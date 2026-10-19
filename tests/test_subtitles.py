from pathlib import Path

from ytdownloader.core.models import Chapter
from ytdownloader.core.subtitles import (
    Cue,
    clean_auto,
    parse_vtt,
    to_paragraphs,
    to_srt,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_manual():
    cues = parse_vtt(_read("manual_en.vtt"))
    assert len(cues) == 6
    assert cues[0] == Cue(1.2, 3.36, "All right, so here we are, in front of the elephants")


def test_parse_handles_short_timestamps_entities_and_notes():
    text = (
        "WEBVTT\n\nNOTE a comment\nsecond line\n\n"
        "STYLE\n::cue { color: red }\n\n"
        "01:02.500 --> 01:04.000 align:start position:0%\n"
        "Tom &amp; Jerry &gt; &lt;b&gt;&nbsp;x<c> y</c>\n"
    )
    cues = parse_vtt(text)
    assert cues == [Cue(62.5, 64.0, "Tom & Jerry > <b> x y")]
    assert parse_vtt("WEBVTT\n\n01:00:01.000 --> 01:00:02.000\nhi\n")[0].start == 3601.0


def test_clean_auto_has_no_repeats():
    cues = clean_auto(parse_vtt(_read("auto_pl.vtt")))
    joined = " ".join(c.text for c in cues)
    phrase = "Zbigniew Trybuła, dyrektor Instytutu Fizyki Molekularnej Polskiej Akademii Nauk"
    assert joined.count(phrase) == 1
    assert cues[0].start == 8.76
    assert cues[0].text == "Witam serdecznie wszystkich państwa."
    expected = (
        "Witam serdecznie wszystkich państwa. Zbigniew Trybuła, dyrektor Instytutu "
        "Fizyki Molekularnej Polskiej Akademii Nauk, a jednocześnie kierownik naukowy "
        "warsztatów Lato z Helen. Proszę państwa, dzisiaj pierwszy dzień"
    ).split()
    assert joined.split()[: len(expected)] == expected
    assert "<c>" not in joined and "00:00" not in joined
    for a, b in zip(cues, cues[1:]):
        assert a.text != b.text


def test_paragraphs_respect_target_and_chapters():
    cues = [Cue(i * 10.0, i * 10.0 + 10, f"Sentence {i}.") for i in range(25)]
    paras = to_paragraphs(cues, [Chapter(0, "A"), Chapter(100, "B")])
    starts = [p.start for p in paras]
    assert starts[:3] == [0.0, 50.0, 100.0]
    for prev, cur in zip(starts, starts[1:]):
        assert cur == 100.0 or cur - prev >= 45.0
    assert "  " not in paras[0].text and paras[0].text.startswith("Sentence 0. Sentence 1.")


def test_paragraphs_hard_limit_without_punctuation():
    cues = [Cue(i * 10.0, i * 10.0 + 10, f"word{i}") for i in range(12)]
    paras = to_paragraphs(cues, [])
    assert [p.start for p in paras] == [0.0, 90.0]


def test_to_srt():
    cues = [Cue(1.2, 3.36, "All right"), Cue(3661.5, 3662.0, "Second")]
    assert to_srt(cues) == (
        "1\n00:00:01,200 --> 00:00:03,360\nAll right\n\n"
        "2\n01:01:01,500 --> 01:01:02,000\nSecond\n\n"
    )


def test_whitespace_only_payload_line_keeps_cue():
    cues = parse_vtt("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n \nhello\n")
    assert cues == [Cue(1.0, 2.0, "hello")]
    assert parse_vtt(_read("auto_pl.vtt"))[0].start == 8.76


def test_first_paragraph_of_auto_captions_starts_at_first_cue():
    paras = to_paragraphs(clean_auto(parse_vtt(_read("auto_pl.vtt"))), [])
    assert paras[0].start == 8.76
