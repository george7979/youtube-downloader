from pathlib import Path

import pytest

from ytdownloader.core.naming import note_video_id, plan_names, safe_filename

VID = "dQw4w9WgXcQ"
OTHER = "VIw16SXObUQ"


def make_note(path: Path, video_id: str) -> None:
    path.write_text(
        f"---\ntitle: x\nurl: https://www.youtube.com/watch?v={video_id}\n---\n\nbody\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ('Wykład: czym jest "czas"?', "Wykład - czym jest 'czas'"),
        ("a/b\\c|d", "a-b-c-d"),
        ("a<b>c*d", "a_b_c_d"),
        ("CON", "_CON"),
        ("con", "_con"),
        ("nul.txt", "_nul.txt"),
        ("COM1", "_COM1"),
        ("CONSOLE", "CONSOLE"),
        ("end. . ", "end"),
        ("🚀 Rocket", "🚀 Rocket"),
        ("???", "video"),
        ("", "video"),
        ("tab\there", "tab here"),
        ("many   spaces\n\nhere", "many spaces here"),
        ("bell\x07char\x7f", "bell_char_"),
    ],
)
def test_safe_filename(title, expected):
    assert safe_filename(title) == expected


def test_safe_filename_truncates():
    assert len(safe_filename("x" * 300)) == 150


def test_safe_filename_truncate_restrips():
    out = safe_filename("a" * 9 + " " + "b" * 20, max_len=10)
    assert out == "a" * 9


def test_plan_fresh_folder(tmp_path):
    plan = plan_names(tmp_path, "My: Title", VID, "mp4")
    assert plan.base == "My - Title"
    assert plan.media == tmp_path / "My - Title.mp4"
    assert plan.note == tmp_path / "My - Title.md"
    assert plan.existing_media is None
    assert plan.existing_note is None


def test_plan_collision_other_video_gets_id_suffix(tmp_path):
    make_note(tmp_path / "T.md", OTHER)
    plan = plan_names(tmp_path, "T", VID, "mp4")
    assert plan.base == f"T [{VID}]"
    assert plan.note == tmp_path / f"T [{VID}].md"
    assert plan.existing_note is None


def test_plan_collision_on_media_only(tmp_path):
    (tmp_path / "T.mp4").write_bytes(b"x")
    plan = plan_names(tmp_path, "T", VID, "mp4")
    assert plan.base == f"T [{VID}]"


def test_plan_finds_existing_note_and_media(tmp_path):
    make_note(tmp_path / "T.md", VID)
    (tmp_path / "T.mp4").write_bytes(b"x")
    plan = plan_names(tmp_path, "Different title now", VID, "mp4")
    assert plan.base == "T"
    assert plan.existing_note == tmp_path / "T.md"
    assert plan.existing_media == tmp_path / "T.mp4"
    assert plan.note == tmp_path / "T.md"


def test_plan_note_only(tmp_path):
    make_note(tmp_path / "T.md", VID)
    plan = plan_names(tmp_path, "T", VID, "mp4")
    assert plan.existing_note == tmp_path / "T.md"
    assert plan.existing_media is None


def test_plan_finds_renamed_note_by_id(tmp_path):
    make_note(tmp_path / "Other name.md", VID)
    plan = plan_names(tmp_path, "T", VID, "mp4")
    assert plan.base == "Other name"
    assert plan.existing_note == tmp_path / "Other name.md"


def test_plan_media_with_other_extension_is_not_existing(tmp_path):
    # MP3 after MP4 of the same video is a new download, not "already downloaded".
    make_note(tmp_path / "T.md", VID)
    (tmp_path / "T.mp4").write_bytes(b"x")
    plan = plan_names(tmp_path, "T", VID, "mp3")
    assert plan.existing_media is None
    assert plan.media == tmp_path / "T.mp3"
    assert plan_names(tmp_path, "T", VID, "mp4").existing_media == tmp_path / "T.mp4"


def test_plan_id_suffixed_media_with_other_extension_is_not_existing(tmp_path):
    (tmp_path / f"Whatever [{VID}].mp4").write_bytes(b"x")
    assert plan_names(tmp_path, "T", VID, "mp3").existing_media is None


def test_plan_finds_media_by_id_suffix_without_note(tmp_path):
    (tmp_path / f"Whatever [{VID}].mp4").write_bytes(b"x")
    plan = plan_names(tmp_path, "T", VID, "mp4")
    assert plan.existing_media == tmp_path / f"Whatever [{VID}].mp4"
    assert plan.existing_note is None


def test_note_video_id_reads_frontmatter(tmp_path):
    note = tmp_path / "n.md"
    make_note(note, VID)
    assert note_video_id(note) == VID


def test_note_video_id_reads_rendered_note(tmp_path):
    from datetime import date

    from ytdownloader.core.models import VideoInfo
    from ytdownloader.core.note import render_note

    info = VideoInfo(
        id=VID, url=f"https://www.youtube.com/watch?v={VID}", title="x", channel="c",
        duration=10, published=None, language=None, thumbnail=None, description="",
        chapters=[], heights=[], subtitles=[],
    )
    note = tmp_path / "n.md"
    note.write_text(render_note(info, "x.mp4", "none", None, date(2026, 10, 18)), encoding="utf-8")
    assert note_video_id(note) == VID


def test_note_video_id_ignores_missing_frontmatter(tmp_path):
    note = tmp_path / "n.md"
    note.write_text(f"# Title\n\nurl: https://www.youtube.com/watch?v={VID}\n", encoding="utf-8")
    assert note_video_id(note) is None


def test_note_video_id_ignores_url_after_frontmatter(tmp_path):
    note = tmp_path / "n.md"
    note.write_text(
        f"---\ntitle: x\n---\nurl: https://www.youtube.com/watch?v={VID}\n", encoding="utf-8"
    )
    assert note_video_id(note) is None


def test_note_video_id_non_utf8_and_missing(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"---\nurl: \xff\xfe\n---\n")
    assert note_video_id(bad) is None
    assert note_video_id(tmp_path / "nope.md") is None


def test_note_video_id_huge_file_cut_inside_multibyte(tmp_path):
    note = tmp_path / "n.md"
    head = f"---\nurl: https://www.youtube.com/watch?v={VID}\n---\n"
    note.write_text(head + "ą" * 10000, encoding="utf-8")
    assert note_video_id(note) == VID


@pytest.mark.parametrize("ch", ["Ж", "漢", "🚀", "a"])
def test_safe_filename_byte_cap(ch):
    name = safe_filename(ch * 150 + ".")
    assert len(name.encode("utf-8")) <= 200
    assert len(name) <= 150
    assert not name.endswith((".", " "))


def test_safe_filename_byte_cap_cuts_on_char_boundary_and_restrips():
    name = safe_filename("Ж" * 99 + " " + "Ж" * 20)
    assert name == "Ж" * 99
    emoji = safe_filename("🚀 " * 100)
    assert len(emoji.encode("utf-8")) <= 200
    assert not emoji.endswith(" ")


def test_plan_reports_unrecognised_suffixed_note(tmp_path):
    make_note(tmp_path / "T.md", OTHER)
    unrecognised = tmp_path / f"T [{VID}].md"
    unrecognised.write_text("user text, no frontmatter\n", encoding="utf-8")
    plan = plan_names(tmp_path, "T", VID, "mp4")
    assert plan.note == unrecognised
    assert plan.existing_note == unrecognised


def test_plan_reports_unrecognised_suffixed_media(tmp_path):
    make_note(tmp_path / "T.md", OTHER)
    media = tmp_path / f"T [{VID}].mp4"
    media.write_bytes(b"x")
    plan = plan_names(tmp_path, "T", VID, "mp4")
    assert plan.existing_media == media
