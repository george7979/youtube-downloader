import logging
from pathlib import Path

from ytdownloader.core import logsetup, paths


def test_dirs_follow_platformdirs(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.platformdirs, "user_config_dir", lambda *a, **k: str(tmp_path / "cfg"))
    monkeypatch.setattr(paths.platformdirs, "user_data_dir", lambda *a, **k: str(tmp_path / "data"))
    monkeypatch.setattr(paths.platformdirs, "user_log_dir", lambda *a, **k: str(tmp_path / "log"))
    assert paths.config_dir() == tmp_path / "cfg" and (tmp_path / "cfg").is_dir()
    assert paths.tools_dir() == tmp_path / "data" / "tools" and (tmp_path / "data" / "tools").is_dir()
    assert paths.log_dir() == tmp_path / "log"


def test_downloads_dir_falls_back_to_home(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.platformdirs, "user_downloads_dir", lambda: str(tmp_path / "missing"))
    monkeypatch.setattr(paths.Path, "home", lambda: tmp_path)
    assert paths.downloads_dir() == tmp_path / "Downloads"


def test_setup_logging_writes_under_log_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.platformdirs, "user_log_dir", lambda *a, **k: str(tmp_path / "log"))
    f = logsetup.setup_logging()
    logging.getLogger("t").info("hello")
    assert f.parent == tmp_path / "log" and "hello" in f.read_text(encoding="utf-8")


def test_setup_logging_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.platformdirs, "user_log_dir", lambda *a, **k: str(tmp_path / "log"))
    logsetup.setup_logging()
    n = len(logging.getLogger().handlers)
    logsetup.setup_logging()
    assert len(logging.getLogger().handlers) == n


def test_no_tmp_literal_in_sources():
    root = Path(__file__).resolve().parent.parent / "ytdownloader"
    src = "".join(p.read_text(encoding="utf-8") for p in root.rglob("*.py"))
    assert '"/tmp' not in src and "'/tmp" not in src
