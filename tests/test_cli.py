import json
from pathlib import Path

import pytest

from ytdownloader import __main__ as entry
from ytdownloader import cli
from ytdownloader.core.errors import friendly
from ytdownloader.core.models import (
    SUBS_DEFAULT,
    SUBS_NONE,
    DownloadResult,
    Progress,
    Status,
)
from ytdownloader.core.probe import info_from_json

FIXTURES = Path(__file__).parent / "fixtures"


class FakeTools:
    def missing(self):
        return []


class FakeService:
    def __init__(self, tmp_path, error=None):
        self.tools = FakeTools()
        self.tmp_path = tmp_path
        self.error = error
        self.requests = []
        self.out_existed = None

    def probe(self, url):
        if self.error:
            raise self.error
        return info_from_json(json.loads((FIXTURES / "info_lecture.json").read_text("utf-8")))

    def download(self, req, info, sink, cancel, remembered_lang=None):
        self.requests.append(req)
        self.out_existed = Path(req.output_dir).is_dir()
        if self.error:
            raise self.error
        sink(Status("Downloading…"))
        sink(Progress(0.5, "50%"))
        return DownloadResult(
            video_id="VIw16SXObUQ",
            title="Zażółć T",
            media_path=Path(req.output_dir) / "T.mp4",
            note_path=Path(req.output_dir) / "T.md",
            srt_path=None,
            transcript="youtube-auto-pl",
            warnings=["careful"],
        )


@pytest.fixture(autouse=True)
def _no_real_logging(monkeypatch):
    monkeypatch.setattr(cli, "setup_logging", lambda: None)


def run(argv, service):
    return cli.main(argv, service_factory=lambda: service)


def test_get_requires_out(tmp_path):
    with pytest.raises(SystemExit) as exc:
        run(["get", "https://youtu.be/x"], FakeService(tmp_path))
    assert exc.value.code == 2


def test_get_creates_missing_out_dir(tmp_path):
    service = FakeService(tmp_path)
    out = tmp_path / "a" / "b"
    assert run(["get", "u", "--out", str(out), "--json"], service) == 0
    assert out.is_dir()
    assert service.out_existed is True


def test_get_json_success(tmp_path, capsys):
    code = run(["get", "u", "--out", str(tmp_path), "--json"], FakeService(tmp_path))
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)  # exactly one JSON object, nothing else
    assert captured.out.endswith("\n") and captured.out.count("\n") == 1
    assert payload["ok"] is True
    assert payload["media"].endswith("T.mp4")
    assert payload["note"].endswith("T.md")
    assert payload["srt"] is None
    assert payload["transcript"] == "youtube-auto-pl"
    assert payload["already_exists"] is False
    assert payload["warnings"] == ["careful"]
    assert payload["title"] == "Zażółć T"  # ensure_ascii=False
    assert "Downloading" in captured.err and "Downloading" not in captured.out


def test_get_human_output(tmp_path, capsys):
    assert run(["get", "u", "--out", str(tmp_path)], FakeService(tmp_path)) == 0
    out = capsys.readouterr().out
    assert f"Saved: {tmp_path / 'T.mp4'}" in out
    assert f"Note: {tmp_path / 'T.md'}" in out
    assert "Transcript: youtube-auto-pl" in out
    assert "Warning: careful" in out


def test_get_json_error(tmp_path, capsys):
    service = FakeService(tmp_path, error=friendly("bot_check"))
    code = run(["get", "u", "--out", str(tmp_path), "--json"], service)
    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["ok"] is False
    assert payload["error"]["code"] == "bot_check"
    assert payload["error"]["hint"]


def test_get_error_human_goes_to_stderr(tmp_path, capsys):
    service = FakeService(tmp_path, error=friendly("bot_check"))
    assert run(["get", "u", "--out", str(tmp_path)], service) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("Error: YouTube is blocking this request.\n")


def test_get_cancelled_exits_130(tmp_path, capsys):
    service = FakeService(tmp_path, error=friendly("cancelled"))
    code = run(["get", "u", "--out", str(tmp_path), "--json"], service)
    assert code == 130
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "cancelled"


def test_get_out_not_creatable_is_write_failed(tmp_path, capsys):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    code = run(["get", "u", "--out", str(blocker / "sub"), "--json"], FakeService(tmp_path))
    assert code == 1
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "write_failed"


def test_info_json_lists_subtitles(tmp_path, capsys):
    assert run(["info", "u", "--json"], FakeService(tmp_path)) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["subtitles"] == [{"lang": "pl", "kind": "auto"}]
    assert payload["heights"] == [720, 360, 144]
    assert payload["published"] is None or isinstance(payload["published"], str)
    assert payload["duration"] is None or isinstance(payload["duration"], int)


def test_info_invalid_url_error(tmp_path, capsys):
    service = FakeService(tmp_path, error=friendly("invalid_url"))
    assert run(["info", "x", "--json"], service) == 1
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "invalid_url"


def test_subs_flag_mapping(tmp_path):
    def subs_for(*extra):
        service = FakeService(tmp_path)
        run(["get", "u", "--out", str(tmp_path), *extra], service)
        return service.requests[0].subs

    assert subs_for("--subs", "none") == SUBS_NONE
    assert subs_for() == SUBS_DEFAULT
    assert subs_for("--subs", "pl") == "pl"


def test_flags_map_to_request(tmp_path):
    service = FakeService(tmp_path)
    run(
        ["get", "u", "--out", str(tmp_path), "--audio", "--quality", "720", "--srt",
         "--no-note", "--force"],
        service,
    )
    req = service.requests[0]
    assert (req.mode, req.quality, req.save_srt, req.save_note, req.force) == (
        "mp3", 720, True, False, True,
    )


def test_main_routes_subcommands(monkeypatch):
    seen = []
    monkeypatch.setattr(cli, "main", lambda argv, service_factory=None: seen.append(argv) or 0)
    assert entry.main(["info", "x", "--json"]) == 0
    assert entry.main(["--help"]) == 0
    assert seen == [["info", "x", "--json"], ["--help"]]
