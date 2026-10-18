"""GUI smoke tests: build the main window and drive the Check flow without network."""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("tkinter")

if sys.platform.startswith("linux") and not (
    os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
):
    pytest.skip("no display available", allow_module_level=True)

from ytdownloader.core.errors import friendly  # noqa: E402
from ytdownloader.core.probe import info_from_json  # noqa: E402
from ytdownloader.core.settings import RecentItem, Settings  # noqa: E402
from ytdownloader.gui import app as app_mod  # noqa: E402
from ytdownloader.gui.app import MainWindow  # noqa: E402
from ytdownloader.gui.worker import UiQueue  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def lecture():
    return info_from_json(json.loads((FIXTURES / "info_lecture.json").read_text(encoding="utf-8")))


class FakeService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.gate: threading.Event | None = None  # when set, probe blocks until released
        self.urls: list[str] = []

    def probe(self, url):
        self.urls.append(url)
        if self.gate is not None:
            assert self.gate.wait(5), "test never released the probe"
        if self.error is not None:
            raise self.error
        return self.result


class FakeTools:
    pass


@pytest.fixture(autouse=True)
def _no_side_effects(monkeypatch):
    saved: list[Settings] = []
    monkeypatch.setattr(app_mod, "save_settings", lambda s, path=None: saved.append(s))
    # Thumbnail fetch must never touch the network in tests.
    monkeypatch.setattr(app_mod, "fetch_thumbnail", lambda url: None)
    return saved


@pytest.fixture
def make_window(tmp_path):
    windows: list[MainWindow] = []

    def build(service=None, settings=None):
        settings = settings or Settings(output_dir=str(tmp_path))
        w = MainWindow(service or FakeService(), FakeTools(), settings)
        w.withdraw()
        windows.append(w)
        return w

    yield build
    for w in windows:
        w.destroy()


def pump(root, until, timeout=5.0):
    deadline = time.monotonic() + timeout
    while not until():
        if time.monotonic() > deadline:
            raise AssertionError("condition not reached in time")
        root.update()
        time.sleep(0.01)


def test_window_builds_and_applies_info(make_window):
    w = make_window()
    w.apply_info(lecture())

    assert w.quality_menu.cget("values") == ["720p", "360p", "144p"]
    assert w.quality_menu.get() == "720p"
    assert w.subs_menu.get() == "pl (auto)"
    assert w.download_button.cget("state") == "normal"

    req = w.selected_request()
    assert req.quality == 720
    assert req.subs == "pl"
    assert req.mode == "mp4"
    assert req.url == "https://www.youtube.com/watch?v=VIw16SXObUQ"


def test_meta_and_subtitle_lines(make_window):
    w = make_window()
    w.apply_info(lecture())
    assert w.meta_label.cget("text") == "Science 5.0 · 1:05:35 · 2020-07-01"
    assert w.subs_line_label.cget("text") == "Subtitles: pl (auto)"


def test_subtitles_none_maps_to_subs_none(make_window):
    w = make_window()
    w.apply_info(lecture())
    w.subs_menu.set("None")
    assert w.selected_request().subs == "none"


def test_mp3_mode_disables_quality(make_window):
    w = make_window()
    w.apply_info(lecture())
    w.mode_switch.set("MP3")
    w._on_mode_change("MP3")
    assert w.quality_menu.cget("state") == "disabled"
    assert w.selected_request().mode == "mp3"


def test_download_disabled_before_check(make_window):
    w = make_window()
    assert w.download_button.cget("state") == "disabled"


def test_fresh_window_shows_options_but_not_card(make_window):
    w = make_window(settings=Settings(quality=1080))
    assert w.options.winfo_manager() == "pack"
    assert w.card.winfo_manager() == ""
    assert w.quality_menu.cget("values") == ["1080p"]
    assert w.quality_menu.get() == "1080p"
    assert w.subs_menu.cget("values") == ["None"]
    assert w.subs_menu.get() == "None"
    w.apply_info(lecture())
    assert w.card.winfo_manager() == "pack"


def check_and_wait(w, url):
    w.url_entry.delete(0, "end")
    w.url_entry.insert(0, url)
    w.check()
    pump(w, lambda: w.status_label.cget("text") != "Fetching video info…")


def test_failed_check_disarms_previous_video(make_window):
    service = FakeService(result=lecture())
    w = make_window(service=service)
    check_and_wait(w, "https://youtu.be/VIw16SXObUQ")
    assert w.download_button.cget("state") == "normal"

    service.error = friendly("unavailable")
    check_and_wait(w, "https://youtu.be/otherVideo1")

    assert w.status_label.cget("text") == "This video is not publicly available."
    assert w.download_button.cget("state") == "disabled"
    assert w.card.winfo_manager() == ""
    assert w.selected_request().url != lecture().url
    assert w.url_entry.cget("state") == "normal"
    assert w.check_button.cget("state") == "normal"


def test_download_disabled_while_check_in_flight(make_window):
    service = FakeService(result=lecture())
    w = make_window(service=service)
    check_and_wait(w, "https://youtu.be/VIw16SXObUQ")
    assert w.download_button.cget("state") == "normal"

    service.gate = threading.Event()
    w.check()
    for _ in range(10):
        w.update()
        time.sleep(0.01)
    assert w.download_button.cget("state") == "disabled"
    assert w.card.winfo_manager() == ""
    assert w.selected_request().url == "https://youtu.be/VIw16SXObUQ"  # entry text, not old info
    assert w.check_button.cget("state") == "normal"

    service.gate.set()
    pump(w, lambda: w.status_label.cget("text") == "Ready.")
    assert w.download_button.cget("state") == "normal"


def test_download_stays_disabled_while_downloading(make_window):
    w = make_window()
    w.downloading = True
    w.apply_info(lecture())
    assert w.download_button.cget("state") == "disabled"
    w.downloading = False
    w.update_download_button()
    assert w.download_button.cget("state") == "normal"


def test_recent_missing_file_greyed(make_window, tmp_path):
    present = tmp_path / "present.mp4"
    present.write_bytes(b"x")
    settings = Settings(
        output_dir=str(tmp_path),
        recent=[
            RecentItem("aaa", "Gone video", str(tmp_path / "gone.mp4"), "2026-10-18"),
            RecentItem("bbb", "Here video", str(present), "2026-10-18"),
        ],
    )
    w = make_window(settings=settings)
    texts = [label.cget("text") for label in w.recent_labels]
    assert "(file missing)" in texts[0]
    assert "Gone video" in texts[0]
    assert "(file missing)" not in texts[1]


def test_check_success_fills_card(make_window):
    service = FakeService(result=lecture())
    w = make_window(service=service)
    w.url_entry.insert(0, "https://youtu.be/VIw16SXObUQ")
    w.check()
    assert w.status_label.cget("text") == "Fetching video info…"
    pump(w, lambda: w.status_label.cget("text") == "Ready.")
    assert service.urls == ["https://youtu.be/VIw16SXObUQ"]
    assert w.title_label.cget("text") == lecture().title
    assert w.download_button.cget("state") == "normal"


def test_check_error_shows_friendly_message(make_window):
    w = make_window(service=FakeService(error=friendly("invalid_url")))
    w.url_entry.insert(0, "not a link")
    w.check()
    pump(w, lambda: w.status_label.cget("text") != "Fetching video info…")
    assert w.status_label.cget("text") == "This doesn't look like a YouTube video link."
    assert w.download_button.cget("state") == "disabled"


def test_folder_change_saves_settings(make_window, monkeypatch, tmp_path, _no_side_effects):
    new_dir = tmp_path / "videos"
    new_dir.mkdir()
    monkeypatch.setattr(app_mod.filedialog, "askdirectory", lambda **kw: str(new_dir))
    w = make_window()
    w.change_folder()
    assert w.selected_request().output_dir == new_dir
    assert w.settings.output_dir == str(new_dir)
    assert _no_side_effects and _no_side_effects[-1].output_dir == str(new_dir)


def test_unavailable_saved_folder_warns_in_status(make_window, tmp_path):
    w = make_window(settings=Settings(output_dir=str(tmp_path / "nope")))
    assert "is not available" in w.status_label.cget("text")


def test_uiqueue_runs_callbacks_on_main_thread(make_window):
    w = make_window()
    q = UiQueue(w, interval_ms=10)
    main = threading.get_ident()
    seen: dict[str, int] = {}

    def work():
        seen["work"] = threading.get_ident()
        return 42

    def on_ok(value):
        seen["ok"] = threading.get_ident()
        seen["value"] = value

    def on_err(exc):
        seen["err_thread"] = threading.get_ident()
        seen["err"] = exc

    def boom():
        raise ValueError("bad")

    q.run_bg(work, on_ok, lambda e: None)
    q.run_bg(boom, lambda v: None, on_err)
    pump(w, lambda: "ok" in seen and "err" in seen)
    q.close()

    assert seen["value"] == 42
    assert seen["work"] != main
    assert seen["ok"] == main
    assert seen["err_thread"] == main
    assert isinstance(seen["err"], ValueError)
