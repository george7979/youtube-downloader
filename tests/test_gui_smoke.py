"""GUI smoke tests: build the main window and drive the Check flow without network."""

from __future__ import annotations

import json
import os
import sys
import threading
import tkinter
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("tkinter")

if sys.platform.startswith("linux") and not (
    os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
):
    pytest.skip("no display available", allow_module_level=True)

import tkinter as tk  # noqa: E402

import customtkinter as ctk  # noqa: E402

from ytdownloader import gui as gui_mod  # noqa: E402
from ytdownloader.core.errors import friendly  # noqa: E402
from ytdownloader.core.models import DownloadResult, Progress, Status  # noqa: E402
from ytdownloader.core.probe import info_from_json  # noqa: E402
from ytdownloader.core.settings import RecentItem, Settings  # noqa: E402
from ytdownloader.core.settings import save_settings as real_save_settings  # noqa: E402
from ytdownloader.core.tools import tool_specs  # noqa: E402
from ytdownloader.gui import app as app_mod  # noqa: E402
from ytdownloader.gui import widgets  # noqa: E402
from ytdownloader.gui.app import MainWindow  # noqa: E402
from ytdownloader.gui.first_run import FirstRunWindow  # noqa: E402
from ytdownloader.gui.worker import UiQueue  # noqa: E402

# Creating many Tk roots in one process occasionally fails on the Windows CI runner while
# Tcl/Tk read their library scripts ("Can't find a usable init.tcl" / "tk.tcl", "invalid command
# name tcl_findLibrary") — an environmental flake, not an app defect (the app creates a single
# root). Retry only Tcl/Tk initialisation failures.
_TCL_INIT_ERRORS = ("Can't find a usable", "tcl_findLibrary")


def create_root(factory):
    for attempt in range(3):
        try:
            return factory()
        except tkinter.TclError as exc:
            if not any(m in str(exc) for m in _TCL_INIT_ERRORS) or attempt == 2:
                raise
            time.sleep(0.2)


real_fetch_thumbnail = app_mod.fetch_thumbnail  # the autouse fixture replaces it in app_mod

FIXTURES = Path(__file__).parent / "fixtures"


def lecture():
    return info_from_json(json.loads((FIXTURES / "info_lecture.json").read_text(encoding="utf-8")))


def zoo():
    return info_from_json(json.loads((FIXTURES / "info_zoo.json").read_text(encoding="utf-8")))


class FakeService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.gate: threading.Event | None = None  # when set, probe blocks until released
        self.urls: list[str] = []
        # download(): emits `events`, optionally blocks on `download_gate` (or cancel), then
        # returns `download_results` in order (an Exception in the list is raised instead).
        self.events: list = []
        self.download_gate: threading.Event | None = None
        self.download_results: list = []
        self.download_calls: list = []

    def probe(self, url):
        self.urls.append(url)
        if self.gate is not None:
            assert self.gate.wait(5), "test never released the probe"
        if self.error is not None:
            raise self.error
        return self.result

    def download(self, req, info, sink, cancel, remembered_lang=None):
        self.download_calls.append((req, info, remembered_lang))
        for event in self.events:
            sink(event)
        if self.download_gate is not None:
            deadline = time.monotonic() + 5
            while not (self.download_gate.is_set() or cancel.is_set()):
                assert time.monotonic() < deadline, "test never released the download"
                time.sleep(0.01)
        if cancel.is_set():
            raise friendly("cancelled")
        outcome = self.download_results.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeTools:
    """Only what the engine-status tests need; `gate` holds update_ytdlp until released."""

    def __init__(self, old="2026.09.01", new="2026.10.18"):
        self.old = old
        self.new = new
        self.gate: threading.Event | None = None
        self.updates = 0

    def ytdlp_version(self):
        return self.old

    def update_ytdlp(self):
        self.updates += 1
        if self.gate is not None:
            assert self.gate.wait(5), "test never released the update"
        return self.old, self.new

    def update_all(self, on_bytes_for):
        on_bytes_for("deno")(1_000_000, 2_000_000)
        return self.update_ytdlp()


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

    def build(service=None, settings=None, tools=None):
        settings = settings or Settings(output_dir=str(tmp_path))
        w = create_root(lambda: MainWindow(service or FakeService(), tools or FakeTools(), settings))
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

    assert w.error_panel.winfo_manager() == "pack"
    assert w.error_panel.message_label.cget("text") == "This video is not publicly available."
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
    assert w.error_panel.message_label.cget("text") == (
        "This doesn't look like a YouTube video link."
    )
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


# --- download flow, error panel, first run, engine status --------------------------------


def status(w):
    return w.status_label.cget("text")


def idle_ticks(w, n=10):
    for _ in range(n):
        w.update()
        time.sleep(0.01)


def done_result(tmp_path, already=False, warnings=()):
    info = zoo()
    media = tmp_path / f"{info.title} [{info.id}].mp4"
    media.write_bytes(b"x")
    return DownloadResult(
        video_id=info.id,
        title=info.title,
        media_path=media,
        note_path=tmp_path / f"{info.title} [{info.id}].md",
        srt_path=None,
        transcript="none",
        already_exists=already,
        warnings=list(warnings),
    )


def test_download_success_updates_recent_and_status(make_window, tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(
        app_mod, "save_settings", lambda s, path=None: real_save_settings(s, settings_file)
    )
    service = FakeService()
    service.events = [
        Progress(None, "Downloading video"),
        Progress(0.5, "Downloading video 50% · 2.0 MB/s"),
        Status("Merging into MP4…"),
        Status("Writing note…"),
    ]
    result = done_result(tmp_path, warnings=["No subtitles were downloaded."])
    service.download_results = [result]
    w = make_window(service=service, settings=Settings(output_dir=str(tmp_path), subs_lang="pl"))
    w.apply_info(zoo())
    w.subs_menu.set("de (manual)")
    w.srt_var.set(True)

    w.download_button.invoke()
    assert w.download_button.cget("state") == "disabled"
    assert w.cancel_button.cget("state") == "normal"
    pump(w, lambda: status(w).startswith("Done."), timeout=3)

    assert status(w) == f"Done. Saved {result.media_path.name} · No subtitles were downloaded."
    assert w.recent_labels[0].cget("text") == "Me at the zoo"
    assert w.download_button.cget("state") == "normal"
    assert w.cancel_button.cget("state") == "disabled"
    assert w.error_panel.winfo_manager() == ""
    req, info, remembered = service.download_calls[0]
    assert (req.url, req.subs, info.id, remembered) == (zoo().url, "de", "jNQXAC9IVRw", "pl")

    saved = json.loads(settings_file.read_text(encoding="utf-8"))
    assert saved["recent"][0]["video_id"] == "jNQXAC9IVRw"
    assert saved["recent"][0]["title"] == "Me at the zoo"
    assert saved["recent"][0]["media_path"] == str(result.media_path)
    # 240p was only this video's best: the 1080p preference stays for the next videos.
    assert (saved["mode"], saved["quality"], saved["subs_lang"]) == ("mp4", 1080, "de")
    assert (saved["save_note"], saved["save_srt"]) == (True, True)


@pytest.mark.parametrize(("picked", "stored"), [(None, 1080), ("144p", 144)])
def test_quality_preference_changes_only_when_picked(make_window, tmp_path, picked, stored):
    service = FakeService()
    service.download_results = [done_result(tmp_path)]
    w = make_window(service=service, settings=Settings(output_dir=str(tmp_path), quality=1080))
    w.apply_info(zoo())  # best is 240p, so the default selection is 240p
    if picked:
        w.quality_menu.set(picked)
    w.download_button.invoke()
    pump(w, lambda: status(w).startswith("Done."), timeout=3)
    assert w.settings.quality == stored


def test_download_error_shows_panel_with_details(make_window, tmp_path):
    service = FakeService()
    service.download_results = [friendly("bot_check", details="ERR LINE"), done_result(tmp_path)]
    w = make_window(service=service)
    w.apply_info(zoo())
    w.download_button.invoke()
    pump(w, lambda: w.error_panel.winfo_manager() == "pack", timeout=3)

    panel = w.error_panel
    assert panel.message_label.cget("text") == "YouTube is blocking this request."
    assert "VPN" in panel.hint_label.cget("text")
    assert "ERR LINE" in panel.details_text.get("1.0", "end")
    assert panel.details_box.winfo_manager() == ""
    panel.details_button.invoke()
    assert panel.details_box.winfo_manager() == "pack"
    panel.copy_button.invoke()
    assert w.clipboard_get() == "ERR LINE"
    assert w.download_button.cget("state") == "normal"

    w.download_button.invoke()
    assert panel.winfo_manager() == ""  # a new attempt clears the old error
    pump(w, lambda: status(w).startswith("Done."), timeout=3)


@pytest.mark.parametrize(
    ("code", "offered"),
    [("engine_outdated", True), ("bot_check", True), ("forbidden", True), ("unavailable", False)],
)
def test_error_panel_offers_engine_update(make_window, code, offered):
    tools = FakeTools()
    service = FakeService()
    service.download_results = [friendly(code, details="ERR")]
    w = make_window(service=service, tools=tools)
    w.apply_info(zoo())
    w.download_button.invoke()
    pump(w, lambda: w.error_panel.winfo_manager() == "pack", timeout=3)
    button = w.error_panel.update_button
    assert (button.winfo_manager() == "pack") is offered
    if offered:
        button.invoke()
        pump(w, lambda: w.engine_label.cget("text") == "yt-dlp 2026.10.18", timeout=3)
        assert tools.updates == 1


def test_cancel_shows_cancelled_without_panel(make_window):
    service = FakeService()
    service.events = [Progress(0.1, "Downloading video 10%")]
    service.download_gate = threading.Event()
    w = make_window(service=service)
    w.apply_info(zoo())
    w.download_button.invoke()
    pump(w, lambda: status(w) == "Downloading video 10%", timeout=3)

    w.cancel_button.invoke()
    assert status(w) == "Cancelling…"
    pump(w, lambda: status(w) == "Cancelled.", timeout=3)
    assert w.error_panel.winfo_manager() == ""
    assert w.download_button.cget("state") == "normal"
    assert w.cancel_button.cget("state") == "disabled"


def test_unexpected_worker_exception_reaches_panel(make_window):
    service = FakeService()
    service.download_results = [RuntimeError("kaboom")]
    w = make_window(service=service)
    w.apply_info(zoo())
    w.download_button.invoke()
    pump(w, lambda: w.error_panel.winfo_manager() == "pack", timeout=3)
    assert w.error_panel.message_label.cget("text") == "Something went wrong."
    details = w.error_panel.details_text.get("1.0", "end")
    assert "Traceback" in details
    assert "RuntimeError: kaboom" in details


@pytest.mark.parametrize("choice", ["again", "show", "cancel"])
def test_already_downloaded_choices(make_window, tmp_path, monkeypatch, choice):
    asked: list[str] = []
    shown: list[Path] = []
    monkeypatch.setattr(
        app_mod,
        "ask_already_downloaded",
        lambda parent, title, has_note=True: asked.append(title) or choice,
    )
    monkeypatch.setattr(app_mod.system, "show_file", shown.append)
    service = FakeService()
    existing = done_result(tmp_path, already=True)
    service.download_results = [existing, done_result(tmp_path)]
    w = make_window(service=service, settings=Settings(output_dir=str(tmp_path), subs_lang="pl"))
    w.apply_info(zoo())
    w.subs_menu.set("None")
    w.download_button.invoke()

    if choice == "again":
        pump(w, lambda: status(w).startswith("Done."), timeout=3)
        assert [call[0].force for call in service.download_calls] == [False, True]
        assert w.settings.subs_lang == "pl"  # "None" keeps the remembered language
    else:
        pump(w, lambda: status(w) == "Already downloaded.", timeout=3)
        assert len(service.download_calls) == 1
        assert shown == ([existing.media_path] if choice == "show" else [])
    assert asked == ["Me at the zoo"]
    assert w.download_button.cget("state") == "normal"


def test_check_during_download_keeps_the_running_request(make_window, tmp_path):
    service = FakeService(result=lecture())
    service.events = [Status("Merging into MP4…")]
    service.download_gate = threading.Event()
    service.download_results = [done_result(tmp_path)]
    w = make_window(service=service)
    w.apply_info(zoo())
    w.download_button.invoke()
    pump(w, lambda: status(w) == "Merging into MP4…", timeout=3)

    w.url_entry.delete(0, "end")
    w.url_entry.insert(0, "https://youtu.be/VIw16SXObUQ")
    w.check()
    assert status(w) == "Merging into MP4…"  # the download owns the status line
    pump(w, lambda: w.title_label.cget("text") == lecture().title, timeout=3)
    idle_ticks(w)
    assert status(w) == "Merging into MP4…"
    assert w.download_button.cget("state") == "disabled"
    assert w.url_entry.cget("state") == "normal"

    service.download_gate.set()
    pump(w, lambda: status(w).startswith("Done."), timeout=3)
    req, info, _ = service.download_calls[0]
    assert (req.url, info.id) == (zoo().url, "jNQXAC9IVRw")
    assert w.settings.recent[0].video_id == "jNQXAC9IVRw"
    assert w.download_button.cget("state") == "normal"  # the lecture is checked and ready


def test_download_waits_for_startup_engine_update(make_window, tmp_path, _no_side_effects):
    tools = FakeTools()
    tools.gate = threading.Event()
    service = FakeService()
    service.download_results = [done_result(tmp_path)]
    w = make_window(service=service, tools=tools)
    w.start_engine_status(now=1_000_000.0)
    pump(w, lambda: w.engine_label.cget("text") == "yt-dlp 2026.09.01 · checking for updates…")

    w.apply_info(zoo())
    w.download_button.invoke()
    assert status(w) == "Waiting for engine update to finish…"
    idle_ticks(w)
    assert service.download_calls == []

    tools.gate.set()
    pump(w, lambda: status(w).startswith("Done."), timeout=3)
    assert w.engine_label.cget("text") == "yt-dlp 2026.10.18 · updated"
    assert w.settings.last_update_check == 1_000_000.0
    assert any(s.last_update_check == 1_000_000.0 for s in _no_side_effects)


@pytest.mark.parametrize(
    ("new", "footer"),
    [("2026.09.01", "yt-dlp 2026.09.01 · up to date"), (None, "yt-dlp 2026.09.01 · update failed")],
)
def test_startup_update_outcomes(make_window, _no_side_effects, new, footer):
    w = make_window(tools=FakeTools(new=new))
    w.start_engine_status(now=1_000_000.0)
    pump(w, lambda: w.engine_label.cget("text") == footer)
    # A failed update (e.g. offline) is retried at the next start, not a day later.
    expected = 0.0 if new is None else 1_000_000.0
    assert w.settings.last_update_check == expected
    assert any(s.last_update_check == 1_000_000.0 for s in _no_side_effects) is (new is not None)


def test_engine_status_skips_recent_check(make_window, tmp_path):
    tools = FakeTools()
    settings = Settings(output_dir=str(tmp_path), last_update_check=100.0)
    w = make_window(tools=tools, settings=settings)
    w.start_engine_status(now=200.0)
    pump(w, lambda: w.engine_label.cget("text") == "yt-dlp 2026.09.01")
    idle_ticks(w)
    assert tools.updates == 0


def test_update_engine_refused_while_downloading(make_window, tmp_path):
    tools = FakeTools()
    service = FakeService()
    service.download_gate = threading.Event()
    service.download_results = [done_result(tmp_path)]
    w = make_window(service=service, tools=tools)
    w.apply_info(zoo())
    w.download_button.invoke()
    assert w.engine_menu.entrycget(0, "state") == "disabled"
    w.update_engine()
    assert status(w) == "Can't update the engine while a download is running."
    idle_ticks(w)
    assert tools.updates == 0

    service.download_gate.set()
    pump(w, lambda: status(w).startswith("Done."), timeout=3)
    assert w.engine_menu.entrycget(0, "state") == "normal"
    w.update_engine()
    assert w.engine_label.cget("text").startswith("Updating engine…")
    assert w.download_button.cget("state") == "normal"
    pump(w, lambda: w.engine_label.cget("text") == "yt-dlp 2026.10.18", timeout=3)
    assert tools.updates == 1


def test_update_engine_without_version_reports_failure(make_window):
    w = make_window(tools=FakeTools(new=None))
    w._ytdlp_version = "2026.09.01"
    w.update_engine()
    failed = "yt-dlp 2026.09.01 · update failed"
    pump(w, lambda: w.engine_label.cget("text") == failed, timeout=3)
    assert w.engine_menu.entrycget(0, "state") == "normal"
    assert w.settings.last_update_check == 0.0


def test_windows_icon_error_is_not_fatal(make_window, monkeypatch):
    w = make_window()
    monkeypatch.setattr(widgets, "sys", SimpleNamespace(platform="win32"))

    def broken_iconbitmap(*args):
        raise tk.TclError('bitmap "x.ico" not defined')

    monkeypatch.setattr(w, "iconbitmap", broken_iconbitmap)
    widgets.set_window_icon(w)  # must not raise


def test_first_run_window_sets_app_icon(monkeypatch):
    import ytdownloader.gui.first_run as first_run_mod

    calls = []
    monkeypatch.setattr(first_run_mod, "set_window_icon", lambda root: calls.append(root))
    w = create_root(lambda: FirstRunWindow(FakeInstaller(), tool_specs("linux")))
    w.withdraw()
    try:
        assert calls == [w]
    finally:
        w.destroy()


def test_fetch_thumbnail_rejects_non_http_urls(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("must not open the URL")

    monkeypatch.setattr(app_mod.urllib.request, "urlopen", no_network)
    for url in ("file:///etc/passwd", "ftp://example.com/x.jpg", "data:image/png;base64,AA=="):
        with pytest.raises(ValueError):
            real_fetch_thumbnail(url)


def test_fetch_thumbnail_reads_at_most_5_mb(monkeypatch):
    asked: list[int] = []

    class Huge:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, size=-1):
            asked.append(size)
            return b"x" * size

    monkeypatch.setattr(app_mod.urllib.request, "urlopen", lambda url, timeout: Huge())
    with pytest.raises(ValueError):
        real_fetch_thumbnail("https://i.ytimg.com/vi/x/hq.jpg")
    assert asked == [5 * 1024 * 1024 + 1]


class SlowCancelService(FakeService):
    """download() blocks until cancelled, then takes a while to stop (kill tree, delete partials)."""

    def __init__(self):
        super().__init__()
        self.cleaned_up = False

    def download(self, req, info, sink, cancel, remembered_lang=None):
        self.download_calls.append((req, info, remembered_lang))
        sink(Progress(0.1, "Downloading video 10%"))
        assert cancel.wait(5), "download was never cancelled"
        time.sleep(0.5)
        self.cleaned_up = True
        raise friendly("cancelled")


def test_closing_mid_download_waits_for_cleanup(monkeypatch, tmp_path):
    from ytdownloader.core import logsetup
    from ytdownloader.core import service as service_mod
    from ytdownloader.core import settings as settings_mod
    from ytdownloader.core import tools as tools_mod

    service = SlowCancelService()
    fake_tools = FakeTools()
    fake_tools.missing = lambda: []
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)  # run() installs its own hooks
    monkeypatch.setattr(threading, "excepthook", threading.excepthook)
    monkeypatch.setattr(logsetup, "setup_logging", lambda: tmp_path / "app.log")
    monkeypatch.setattr(tools_mod, "ToolManager", lambda: fake_tools)
    monkeypatch.setattr(service_mod, "Service", lambda tools: service)
    monkeypatch.setattr(
        settings_mod,
        "load_settings",
        lambda path=None: Settings(output_dir=str(tmp_path), last_update_check=time.time()),
    )

    def mainloop(self):
        def start():
            self.apply_info(zoo())
            self.download_button.invoke()
            wait_for_progress()

        def wait_for_progress():
            if self.status_label.cget("text") == "Downloading video 10%":
                self.destroy()  # the user closes the window mid-download
            else:
                self.after(20, wait_for_progress)

        self.after(50, start)
        ctk.CTk.mainloop(self)

    monkeypatch.setattr(MainWindow, "mainloop", mainloop)

    assert gui_mod.run() == 0
    assert len(service.download_calls) == 1
    assert service.cleaned_up  # run() waited for the cancelled download to finish


def test_ask_already_downloaded_returns_choice(make_window):
    w = make_window()

    def click():
        dialog = next(c for c in w.winfo_children() if isinstance(c, ctk.CTkToplevel))
        dialog.buttons["again"].invoke()

    w.after(200, click)
    assert widgets.ask_already_downloaded(w, "Me at the zoo") == "again"


@pytest.mark.parametrize(
    ("has_note", "text"),
    [
        (True, "The video and its note are already in this folder."),
        (False, "The video is already in this folder."),
    ],
)
def test_ask_already_downloaded_text(make_window, has_note, text):
    w = make_window()
    seen: list[str] = []

    def read_and_cancel():
        dialog = next(c for c in w.winfo_children() if isinstance(c, ctk.CTkToplevel))
        seen.extend(c.cget("text") for c in dialog.winfo_children() if isinstance(c, ctk.CTkLabel))
        dialog.buttons["cancel"].invoke()

    w.after(200, read_and_cancel)
    assert widgets.ask_already_downloaded(w, "Me at the zoo", has_note=has_note) == "cancel"
    assert text in seen


class FakeInstaller:
    """ToolManager stand-in: the first install raises, every later one succeeds."""

    def __init__(self):
        self.calls: list[str] = []
        self.fail_next = True

    def install(self, spec, on_bytes):
        self.calls.append(spec.name)
        on_bytes(0, 2_000_000)
        on_bytes(1_000_000, 2_000_000)
        if self.fail_next:
            self.fail_next = False
            raise friendly("network", details="connection reset")
        on_bytes(2_000_000, 2_000_000)


def test_first_run_retry_after_failure():
    tools = FakeInstaller()
    w = create_root(lambda: FirstRunWindow(tools, tool_specs("linux")))
    w.withdraw()
    try:
        assert w.header_label.cget("text") == (
            "First run: downloading tools (yt-dlp, ffmpeg, Deno), about 207 MB"
        )
        pump(w, lambda: w.retry_button.winfo_manager() == "pack", timeout=3)
        assert w.error_panel.message_label.cget("text") == "No connection to YouTube."
        assert w.size_labels["yt-dlp"].cget("text") == "1.0 / 2.0 MB"
        assert w.ok is False

        w.retry_button.invoke()
        pump(w, lambda: w.ok, timeout=3)
        assert tools.calls == ["yt-dlp", "yt-dlp", "ffmpeg", "deno"]
        assert w.retry_button.winfo_manager() == ""
        assert w.error_panel.winfo_manager() == ""
    finally:
        w.destroy()


def test_crash_reporter_shows_log_path(make_window, monkeypatch, tmp_path):
    shown: list[tuple[str, str]] = []
    monkeypatch.setattr(
        gui_mod.messagebox, "showerror", lambda title, message, **kw: shown.append((title, message))
    )
    reporter = gui_mod.CrashReporter(tmp_path / "app.log")
    w = make_window()
    reporter.attach(w)
    try:
        raise ValueError("boom")
    except ValueError:
        w.report_callback_exception(*sys.exc_info())
    assert shown[0][0] == "Something went wrong"
    assert str(tmp_path / "app.log") in shown[0][1]

    no_log = gui_mod.CrashReporter(None, "Permission denied")
    assert "could not be created" in no_log.message()
    assert "Permission denied" in no_log.message()


def record_geometry(monkeypatch, cls) -> list[str]:
    """Geometry strings the window asks for. Reading geometry() back is useless here: a withdrawn
    window on Windows reports Tk's default 200x200 until it is mapped."""
    asked: list[str] = []

    def geometry(self, geometry_string=None):
        if geometry_string is not None:
            asked.append(geometry_string)
        return ctk.CTk.geometry(self, geometry_string)

    monkeypatch.setattr(cls, "geometry", geometry)
    return asked


def asked_size(asked: list[str]) -> tuple[int, int]:
    width, height = asked[-1].split("+")[0].split("x")
    return int(width), int(height)


def test_window_height_fits_small_work_area(make_window, monkeypatch):
    import ytdownloader.gui.app as app_module
    from ytdownloader.gui.placement import FRAME

    monkeypatch.setattr(app_module, "work_area", lambda root: (0, 0, 1280, 600))
    asked = record_geometry(monkeypatch, MainWindow)
    w = make_window()
    width, height = asked_size(asked)
    assert width == 540
    assert (height + FRAME) * w._get_window_scaling() <= 600
    assert height == int(600 / w._get_window_scaling()) - FRAME


def test_clear_recent_empties_list_and_saves(make_window, tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(
        app_mod, "save_settings", lambda s, path=None: real_save_settings(s, settings_file)
    )
    present = tmp_path / "present.mp4"
    present.write_bytes(b"x")
    settings = Settings(
        output_dir=str(tmp_path),
        recent=[RecentItem("bbb", "Here video", str(present), "2026-10-18")],
    )
    w = make_window(settings=settings)
    assert w.clear_recent_button.cget("state") == "normal"

    w.clear_recent_button.invoke()

    assert w.recent_labels == []
    assert w.clear_recent_button.cget("state") == "disabled"
    assert json.loads(settings_file.read_text(encoding="utf-8"))["recent"] == []
    assert present.exists()  # history only — files stay


def test_clear_recent_disabled_when_empty(make_window):
    w = make_window()
    assert w.clear_recent_button.cget("state") == "disabled"


def test_footer_menu_uses_larger_font(make_window):
    import tkinter.font as tkfont

    w = make_window()
    # The configured size: X servers without scalable fonts (WSLg's "fixed") round the actual one.
    font = tkfont.nametofont(str(w.engine_menu.cget("font")), root=w)
    assert font.cget("size") == app_mod.MENU_FONT_SIZE >= 12
    labels = [w.engine_menu.entrycget(i, "label").strip() for i in range(3)]
    assert labels == ["Update engine", "Open log folder", "About"]


def test_first_run_grows_to_show_error_details(monkeypatch):
    import ytdownloader.gui.first_run as first_run_mod

    monkeypatch.setattr(first_run_mod, "work_area", lambda root: (0, 0, 1920, 1040))
    asked = record_geometry(monkeypatch, FirstRunWindow)
    tools = FakeInstaller()
    w = create_root(lambda: FirstRunWindow(tools, tool_specs("linux")))
    w.withdraw()
    try:
        assert asked_size(asked) == (480, 360)
        pump(w, lambda: w.retry_button.winfo_manager() == "pack", timeout=3)
        w.error_panel.details_button.invoke()
        w.update_idletasks()
        width, height = asked_size(asked)
        assert width == 480
        assert height * w._get_window_scaling() >= w.winfo_reqheight() - 1
        assert height > 360
    finally:
        w.destroy()


def test_note_label_says_whether_transcript_is_included(make_window):
    w = make_window()
    assert w.note_check.cget("text") == "Save note without transcript (.md)"
    w.apply_info(lecture())
    assert w.subs_menu.get() != app_mod.NO_SUBS
    assert w.note_check.cget("text") == "Save note with transcript (.md)"
    w.subs_menu._dropdown_callback(app_mod.NO_SUBS)  # what picking from the list does
    assert w.note_check.cget("text") == "Save note without transcript (.md)"


def test_scrollbar_only_when_content_overflows(make_window):
    w = make_window()
    bar = w.body._scrollbar
    w._on_body_scroll("0.0", "1.0")
    assert bar.winfo_manager() == ""
    w._on_body_scroll("0.0", "0.6")
    assert bar.winfo_manager() == "grid"
    w._on_body_scroll("0.0", "1.0")
    assert bar.winfo_manager() == ""
