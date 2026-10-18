import json

from ytdownloader.core import paths, settings
from ytdownloader.core.settings import RecentItem, Settings


def _item(vid: str, title: str = "T") -> RecentItem:
    return RecentItem(video_id=vid, title=title, media_path=f"/m/{vid}.mp4", downloaded="2026-10-18")


def test_roundtrip(tmp_path):
    p = tmp_path / "settings.json"
    s = Settings(
        output_dir="/some/dir",
        mode="mp3",
        quality=720,
        subs_lang="pl",
        save_note=False,
        save_srt=True,
        last_update_check=123.5,
        recent=[_item("a"), _item("b", "Zażółć")],
    )
    settings.save_settings(s, p)
    assert settings.load_settings(p) == s


def test_missing_or_corrupt_file_gives_defaults(tmp_path):
    assert settings.load_settings(tmp_path / "nope.json") == Settings()

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert settings.load_settings(bad) == Settings()

    extra = tmp_path / "extra.json"
    extra.write_text(json.dumps({"quality": 480, "bogus": 1}), encoding="utf-8")
    assert settings.load_settings(extra) == Settings(quality=480)


def test_save_is_atomic(tmp_path):
    p = tmp_path / "settings.json"
    s = Settings(recent=[_item("a", "Zażółć")])
    settings.save_settings(s, p)
    assert list(tmp_path.glob("*.tmp")) == []
    raw = p.read_text(encoding="utf-8")
    assert "Zażółć" in raw
    assert json.loads(raw)["recent"][0]["title"] == "Zażółć"


def test_add_recent_dedupes_and_caps():
    s = Settings()
    for vid in "abcdefg":
        settings.add_recent(s, _item(vid))
    settings.add_recent(s, _item("c"))
    ids = [r.video_id for r in s.recent]
    assert len(ids) == settings.MAX_RECENT == 3
    assert ids[0] == "c"
    assert ids.count("c") == 1


def test_resolve_output_dir(tmp_path, monkeypatch):
    dl = tmp_path / "Downloads"
    monkeypatch.setattr(paths, "downloads_dir", lambda: dl)

    saved = tmp_path / "saved"
    saved.mkdir()
    assert settings.resolve_output_dir(Settings(output_dir=str(saved))) == (saved, None)

    missing = tmp_path / "gone"
    assert settings.resolve_output_dir(Settings(output_dir=str(missing))) == (
        dl,
        f"Saved folder {missing} is not available. Using Downloads instead.",
    )

    assert settings.resolve_output_dir(Settings()) == (dl, None)
    assert settings.resolve_output_dir(Settings(output_dir="")) == (dl, None)


def test_default_path_uses_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "config_dir", lambda: tmp_path)
    settings.save_settings(Settings(quality=360))
    assert (tmp_path / "settings.json").is_file()
    assert settings.load_settings().quality == 360


def _load(tmp_path, data):
    p = tmp_path / "s.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return settings.load_settings(p)


def test_non_dict_top_level_gives_defaults(tmp_path):
    assert _load(tmp_path, []) == Settings()


def test_malformed_recent_entries_are_skipped(tmp_path):
    good = {"video_id": "a", "title": "T", "media_path": "/m", "downloaded": "2026-10-18"}
    for bad in ("abc", 5, {"a": 1}, None):
        assert _load(tmp_path, {"recent": bad}).recent == []
    s = _load(tmp_path, {"recent": [1, "x", None, {"video_id": "z"}, {**good, "title": 3}, good]})
    assert s.recent == [RecentItem(**good)]


def test_wrong_scalar_types_reset_individually(tmp_path):
    s = _load(
        tmp_path,
        {
            "quality": "abc",
            "mode": 5,
            "save_note": "yes",
            "save_srt": 1,
            "output_dir": 7,
            "subs_lang": ["pl"],
            "last_update_check": "x",
        },
    )
    assert s == Settings()
    assert _load(tmp_path, {"mode": "mkv", "quality": -5}) == Settings()
    assert _load(tmp_path, {"quality": True}).quality == 1080
    # valid fields survive next to an invalid one
    s = _load(tmp_path, {"quality": "abc", "mode": "mp3", "last_update_check": 3})
    assert (s.mode, s.quality, s.last_update_check) == ("mp3", 1080, 3.0)
