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
        ("WARNING: [youtube] x: nsig extraction failed: You may experience throttling", "engine_outdated"),
        ("ERROR: [youtube] x: Signature extraction failed: Some formats may be missing", "engine_outdated"),
        ("ERROR: [youtube] x: Unable to extract initial player response", "engine_outdated"),
        ("ERROR: [youtube] x: Requested format is not available", "engine_outdated"),
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
    assert friendly("unknown").hint == "See the details and include them in a bug report."
    assert friendly("engine_outdated").message == "The download engine needs an update."
    assert friendly("engine_outdated").hint == "Update the engine and try again."
    assert friendly("tools_missing").message == "Download tools are missing."


def test_friendly_error_is_exception():
    err = FriendlyError("c", "m", "h", "d")
    assert isinstance(err, Exception)
    assert (err.code, err.message, err.hint, err.details) == ("c", "m", "h", "d")


def test_engine_outdated_order():
    # After bot_check and rate_limit, before unavailable.
    assert classify("Sign in to confirm you're not a bot\nUnable to extract x").code == "bot_check"
    assert classify("HTTP Error 429\nnsig extraction failed").code == "rate_limit"
    assert classify("Unable to extract x\nVideo unavailable").code == "engine_outdated"


def test_http_403_is_forbidden():
    err = classify("ERROR: unable to download video data: HTTP Error 403: Forbidden\n")
    assert err.code == "forbidden"
    assert "try again" in err.hint
