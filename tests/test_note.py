from datetime import date

from ytdownloader.core.models import Chapter, VideoInfo
from ytdownloader.core.note import neutralize_markdown, render_note
from ytdownloader.core.subtitles import Paragraph


def make_info(**kw) -> VideoInfo:
    base = dict(
        id="jNQXAC9IVRw",
        title="Me at the zoo",
        channel="jawed",
        url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
        duration=19,
        published=date(2005, 4, 24),
        language="en",
        thumbnail=None,
        description="The first video.",
        chapters=[Chapter(0, "Intro"), Chapter(5, "The cool thing"), Chapter(17, "End")],
        heights=[240],
        subtitles=[],
    )
    base.update(kw)
    return VideoInfo(**base)


def test_render_note_zoo():
    out = render_note(
        make_info(), "Me at the zoo.mp4", "youtube-manual-en",
        [Paragraph(0.4, "All right, so here we are")], date(2026, 10, 18),
    )
    expected = (
        "---\n"
        'title: "Me at the zoo"\n'
        "\n"
        'channel: "jawed"\n'
        "\n"
        "url: https://www.youtube.com/watch?v=jNQXAC9IVRw\n"
        "\n"
        "published: 2005-04-24\n"
        "\n"
        "downloaded: 2026-10-18\n"
        "\n"
        'duration: "00:19"\n'
        "\n"
        'video: "[[Me at the zoo.mp4]]"\n'
        "\n"
        "transcript: youtube-manual-en\n"
        "\n"
        "tags: [video, youtube]\n"
        "\n"
        "---\n"
        "\n"
        "# Me at the zoo\n"
        "\n"
        "![[Me at the zoo.mp4]]\n"
        "\n"
        "## Description\n"
        "\n"
        "The first video.\n"
        "\n"
        "## Chapters\n"
        "\n"
        "- [00:00](https://youtu.be/jNQXAC9IVRw?t=0) Intro\n"
        "- [00:05](https://youtu.be/jNQXAC9IVRw?t=5) The cool thing\n"
        "- [00:17](https://youtu.be/jNQXAC9IVRw?t=17) End\n"
        "\n"
        "## Transcript\n"
        "\n"
        "[00:00](https://youtu.be/jNQXAC9IVRw?t=0) All right, so here we are\n"
    )
    assert out == expected


def test_render_without_transcript_and_chapters():
    out = render_note(make_info(chapters=[]), "a.mp4", "none", None, date(2026, 10, 18))
    assert "## Transcript" not in out
    assert "## Chapters" not in out
    assert "transcript: none\n" in out
    assert out.endswith("The first video.\n")


def test_long_video_uses_hours():
    out = render_note(
        make_info(duration=3935, chapters=[Chapter(266, "X")]), "a.mp4", "none", None,
        date(2026, 10, 18),
    )
    assert 'duration: "1:05:35"' in out
    assert "[0:04:26](https://youtu.be/jNQXAC9IVRw?t=266) X" in out


def test_neutralize():
    assert (
        neutralize_markdown("#AI news\nsee #tag and https://x.io/#frag [[x]]")
        == "\\#AI news\nsee \\#tag and https://x.io/#frag \\[\\[x\\]\\]"
    )


def test_neutralize_blocks_images_links_html_and_code():
    """Text from YouTube must stay text: no remote image, masked link, raw HTML or code block."""
    assert neutralize_markdown("![](https://evil.example/p.png)") == "!\\[\\](https://evil.example/p.png)"
    assert neutralize_markdown("[Site](obsidian://open)") == "\\[Site\\](obsidian://open)"
    assert neutralize_markdown('<img src="https://evil.example/p.png">') == (
        '\\<img src="https://evil.example/p.png">'
    )
    assert neutralize_markdown("```dataviewjs\nx\n```") == "\\`\\`\\`dataviewjs\nx\n\\`\\`\\`"
    assert neutralize_markdown("~~~js") == "\\~\\~\\~js"


def test_neutralize_escapes_backslash_first():
    # An author's own backslash must not cancel the escape added after it.
    assert neutralize_markdown("\\[x](y)") == "\\\\\\[x\\](y)"


def test_neutralize_keeps_bare_urls_intact():
    url = "https://en.wikipedia.org/wiki/Foo_(bar)?a=1&b=2"
    assert neutralize_markdown(f"More: {url}") == f"More: {url}"


def test_title_heading_is_neutralized():
    out = render_note(
        make_info(title="![](https://evil.example/p.png) #1"), "a.mp4", "none", None,
        date(2026, 10, 18),
    )
    assert "\n# !\\[\\](https://evil.example/p.png) \\#1\n" in out
    assert 'title: "![](https://evil.example/p.png) #1"\n' in out


def test_chapters_and_transcript_are_neutralized():
    out = render_note(
        make_info(chapters=[Chapter(0, "#1 Intro [[link]]")]), "a.mp4", "youtube-auto-en",
        [Paragraph(0, "we love #python and [[wiki]]")], date(2026, 10, 18),
    )
    assert "- [00:00](https://youtu.be/jNQXAC9IVRw?t=0) \\#1 Intro \\[\\[link\\]\\]\n" in out
    assert (
        "[00:00](https://youtu.be/jNQXAC9IVRw?t=0) we love \\#python and \\[\\[wiki\\]\\]\n" in out
    )


def test_title_with_quotes_is_valid_yaml_string():
    out = render_note(make_info(title='He said "hi"'), "a.mp4", "none", None, date(2026, 10, 18))
    assert 'title: "He said \\"hi\\""\n' in out


def test_missing_published_omits_line():
    out = render_note(make_info(published=None), "a.mp4", "none", None, date(2026, 10, 18))
    assert "published:" not in out


def test_frontmatter_survives_viewers_without_frontmatter_support():
    """A blank line between fields keeps each one a paragraph of its own, and a blank line
    before the closing `---` keeps it a rule instead of turning the fields into a heading."""
    out = render_note(make_info(), "Me at the zoo.mp4", "none", None, date(2026, 10, 18))
    front = out.split("\n---\n", 1)[0].split("\n")
    assert front[0] == "---"
    fields = front[1:]
    assert fields[-1] == ""
    assert all(line == "" for line in fields[1::2])
    assert all(": " in line for line in fields[0::2])
