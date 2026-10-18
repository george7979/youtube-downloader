import pytest

from ytdownloader.core.errors import FriendlyError, classify, friendly


@pytest.mark.parametrize(
    "line, code",
    [
        ("OSError: [Errno 13] Permission denied: 'x'", "write_failed"),
        ("ERROR: No space left on device", "write_failed"),
        ("OSError: [Errno 28] whatever", "write_failed"),
        ("OSError: Read-only file system", "write_failed"),
        ("ERROR: [youtube] x: Sign in to confirm you’re not a bot", "bot_check"),
        ("ERROR: This content isn't available, try again later", "rate_limit"),
        ("HTTP Error 429: Too Many Requests", "rate_limit"),
        ("ERROR: [youtube] x: Private video", "unavailable"),
        ("ERROR: Video unavailable", "unavailable"),
        ("This video has been removed by the uploader", "unavailable"),
        ("The uploader says it is not available in your country", "unavailable"),
        ("Sign in to confirm your age", "unavailable"),
        ("Join this channel to get access: members-only content", "unavailable"),
        ("ERROR: Unable to download webpage: boom", "network"),
        ("getaddrinfo failed", "network"),
        ("Temporary failure in name resolution", "network"),
        ("Connection refused", "network"),
        ("The read operation timed out", "network"),
        ("Network is unreachable", "network"),
        ("<urlopen error foo>", "network"),
        ("something totally different", "unknown"),
        ("", "unknown"),
    ],
)
def test_classify(line, code):
    err = classify(line)
    assert isinstance(err, FriendlyError)
    assert err.code == code


def test_classify_details_keeps_last_40_lines():
    text = "\n".join(f"line {i}" for i in range(100))
    err = classify(text)
    lines = err.details.splitlines()
    assert len(lines) == 40
    assert lines[0] == "line 60" and lines[-1] == "line 99"


def test_friendly_table():
    err = friendly("invalid_url")
    assert str(err) == "This doesn't look like a YouTube video link."
    assert err.message == str(err)
    assert err.hint == "Paste a link like https://www.youtube.com/watch?v=…"
    assert friendly("cancelled").hint == ""
    assert friendly("unknown", "d").details == "d"
    assert friendly("unknown").hint == 'Open "Show details" and copy them into a bug report.'
    assert friendly("tools_missing").message == "Download tools are missing."


def test_friendly_error_is_exception():
    err = FriendlyError("c", "m", "h", "d")
    assert isinstance(err, Exception)
    assert (err.code, err.message, err.hint, err.details) == ("c", "m", "h", "d")
