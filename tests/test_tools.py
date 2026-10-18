import hashlib
import io
import json
import os
import posixpath
import socket
import stat
import subprocess
import sys
import tarfile
import urllib.error
import zipfile
from pathlib import Path

import pytest

from ytdownloader.core.errors import FriendlyError
from ytdownloader.core.tools import (
    ToolManager,
    ToolSpec,
    should_check_update,
    tool_specs,
)

YTDLP = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/"
FFMPEG = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/"
DENO = "https://github.com/denoland/deno/releases/latest/download/"


def _spec(platform: str, name: str) -> ToolSpec:
    return next(s for s in tool_specs(platform) if s.name == name)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _zip(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return buf.getvalue()


def _tar_xz(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:xz") as tf:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class FakeNet:
    """Serves payloads by URL; sums files are built from the payloads unless overridden."""

    def __init__(self, spec: ToolSpec, payload: bytes, sums_hex: str | None = None, fail_midway=False):
        self.spec = spec
        self.payload = payload
        self.sums_hex = sums_hex if sums_hex is not None else _sha(payload)
        self.fail_midway = fail_midway

    def fetch(self, url, dest, on_bytes):
        assert url == self.spec.url
        dest = Path(dest)
        if self.fail_midway:
            dest.write_bytes(self.payload[: len(self.payload) // 2])
            raise OSError("connection reset")
        dest.write_bytes(self.payload)
        on_bytes(len(self.payload), len(self.payload))

    def fetch_text(self, url):
        if url.startswith("https://api.github.com/"):
            raise urllib.error.URLError("offline")  # ffmpeg falls back to the `latest` URLs
        assert url == self.spec.sums_url
        return f"{'0' * 64}  some-other-asset\n{self.sums_hex}  {self.spec.asset}\n"


class FakeRun:
    """Returns canned results; `script` maps an argv flag to a list of outputs consumed in order.

    An output is the stdout of a successful run, or an int: the exit code of a failed run.
    """

    def __init__(self, script: dict[str, list[str]]):
        self.script = {k: list(v) for k, v in script.items()}
        self.calls: list[list[str]] = []

    def __call__(self, args, **kwargs):
        self.calls.append(list(args))
        assert kwargs["stdin"] is subprocess.DEVNULL
        assert kwargs["encoding"] == "utf-8" and kwargs["errors"] == "replace"
        assert kwargs["timeout"] > 0
        for flag, outputs in self.script.items():
            if flag in args:
                out = outputs.pop(0)
                if isinstance(out, int):
                    return subprocess.CompletedProcess(args, out, "", "ERROR: failed")
                return subprocess.CompletedProcess(args, 0, out, "")
        raise FileNotFoundError(args[0])


def _no_which(_name):
    return None


def _leftovers(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.name.endswith(".part") or ".staging" in p.parts]


def test_specs_windows_and_linux():
    win = {s.name: s for s in tool_specs("win32")}
    lin = {s.name: s for s in tool_specs("linux")}
    assert list(win) == list(lin) == ["yt-dlp", "ffmpeg", "deno"]

    assert win["yt-dlp"] == ToolSpec(
        "yt-dlp", YTDLP + "yt-dlp.exe", YTDLP + "SHA2-256SUMS", "yt-dlp.exe", None, (), "yt-dlp.exe", 18
    )
    assert lin["yt-dlp"] == ToolSpec(
        "yt-dlp", YTDLP + "yt-dlp_linux", YTDLP + "SHA2-256SUMS", "yt-dlp_linux", None, (), "yt-dlp", 18
    )
    assert win["ffmpeg"] == ToolSpec(
        "ffmpeg",
        FFMPEG + "ffmpeg-master-latest-win64-gpl-shared.zip",
        FFMPEG + "checksums.sha256",
        "ffmpeg-master-latest-win64-gpl-shared.zip",
        "zip",
        ("*/bin/*",),
        "ffmpeg.exe",
        90,
    )
    assert lin["ffmpeg"] == ToolSpec(
        "ffmpeg",
        FFMPEG + "ffmpeg-master-latest-linux64-gpl.tar.xz",
        FFMPEG + "checksums.sha256",
        "ffmpeg-master-latest-linux64-gpl.tar.xz",
        "tar.xz",
        ("*/bin/ffmpeg", "*/bin/ffprobe"),
        "ffmpeg",
        149,
    )
    assert win["deno"] == ToolSpec(
        "deno",
        DENO + "deno-x86_64-pc-windows-msvc.zip",
        DENO + "deno-x86_64-pc-windows-msvc.zip.sha256sum",
        "deno-x86_64-pc-windows-msvc.zip",
        "zip",
        ("deno.exe",),
        "deno.exe",
        40,
    )
    assert lin["deno"] == ToolSpec(
        "deno",
        DENO + "deno-x86_64-unknown-linux-gnu.zip",
        DENO + "deno-x86_64-unknown-linux-gnu.zip.sha256sum",
        "deno-x86_64-unknown-linux-gnu.zip",
        "zip",
        ("deno",),
        "deno",
        40,
    )
    assert sum(s.approx_mb for s in win.values()) == 148
    assert sum(s.approx_mb for s in lin.values()) == 207


def test_linux_uses_system_ffmpeg(tmp_path):
    which = {"ffmpeg": "/usr/bin/ffmpeg", "ffprobe": "/usr/bin/ffprobe"}.get
    tm = ToolManager(root=tmp_path, platform="linux", which=which, run=FakeRun({}))
    assert "ffmpeg" not in [s.name for s in tm.missing()]
    assert tm.paths().ffmpeg_dir == Path("/usr/bin")


def test_linux_without_ffprobe_needs_bundled_ffmpeg(tmp_path):
    which = {"ffmpeg": "/usr/bin/ffmpeg"}.get
    tm = ToolManager(root=tmp_path, platform="linux", which=which, run=FakeRun({}))
    assert "ffmpeg" in [s.name for s in tm.missing()]
    assert tm.paths().ffmpeg_dir == tmp_path / "ffmpeg"


def test_paths_layout_windows(tmp_path):
    tm = ToolManager(root=tmp_path, platform="win32", which=_no_which, run=FakeRun({}))
    p = tm.paths()
    assert p.yt_dlp == tmp_path / "yt-dlp" / "yt-dlp.exe"
    assert p.ffmpeg_dir == tmp_path / "ffmpeg"
    assert p.deno == tmp_path / "deno" / "deno.exe"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX exec bit")
def test_install_plain_file_verifies_checksum(tmp_path):
    spec = _spec("linux", "yt-dlp")
    net = FakeNet(spec, b"#!/bin/sh\necho yt-dlp\n")
    tm = ToolManager(root=tmp_path, platform="linux", fetch=net.fetch, fetch_text=net.fetch_text,
                     which=_no_which, run=FakeRun({}))
    progress = []
    tm.install(spec, lambda done, total: progress.append((done, total)))

    installed = tmp_path / "yt-dlp" / "yt-dlp"
    assert installed == tm.paths().yt_dlp
    assert installed.read_bytes() == net.payload
    assert os.stat(installed).st_mode & stat.S_IXUSR
    assert progress and progress[-1] == (len(net.payload), len(net.payload))
    assert "yt-dlp" not in [s.name for s in tm.missing()]
    assert _leftovers(tmp_path) == []


def test_install_zip_flattens_members(tmp_path):
    deno_spec = _spec("linux", "deno")
    deno_net = FakeNet(deno_spec, _zip({"deno": b"deno-binary"}))
    ToolManager(root=tmp_path, platform="linux", fetch=deno_net.fetch, fetch_text=deno_net.fetch_text,
                which=_no_which, run=FakeRun({})).install(deno_spec, lambda d, t: None)
    assert (tmp_path / "deno" / "deno").read_bytes() == b"deno-binary"
    if sys.platform != "win32":
        assert os.stat(tmp_path / "deno" / "deno").st_mode & stat.S_IXUSR

    ff_spec = _spec("win32", "ffmpeg")
    ff_net = FakeNet(ff_spec, _zip({
        "ffmpeg-x/LICENSE.txt": b"license",
        "ffmpeg-x/bin/ffmpeg.exe": b"ffmpeg-exe",
        "ffmpeg-x/bin/ffprobe.exe": b"ffprobe-exe",
        "ffmpeg-x/bin/avcodec.dll": b"avcodec",
    }))
    ToolManager(root=tmp_path, platform="win32", fetch=ff_net.fetch, fetch_text=ff_net.fetch_text,
                which=_no_which, run=FakeRun({})).install(ff_spec, lambda d, t: None)
    assert sorted(p.name for p in (tmp_path / "ffmpeg").iterdir()) == [
        "avcodec.dll", "ffmpeg.exe", "ffprobe.exe"
    ]
    assert (tmp_path / "ffmpeg" / "ffmpeg.exe").read_bytes() == b"ffmpeg-exe"
    assert _leftovers(tmp_path) == []


def test_install_tar_xz_takes_only_listed_members(tmp_path):
    spec = _spec("linux", "ffmpeg")
    net = FakeNet(spec, _tar_xz({
        "ffmpeg-master-latest-linux64-gpl/bin/ffmpeg": b"ffmpeg",
        "ffmpeg-master-latest-linux64-gpl/bin/ffprobe": b"ffprobe",
        "ffmpeg-master-latest-linux64-gpl/bin/ffplay": b"ffplay",
        "ffmpeg-master-latest-linux64-gpl/doc/readme.txt": b"doc",
    }))
    tm = ToolManager(root=tmp_path, platform="linux", fetch=net.fetch, fetch_text=net.fetch_text,
                     which=_no_which, run=FakeRun({}))
    tm.install(spec, lambda d, t: None)
    assert sorted(p.name for p in (tmp_path / "ffmpeg").iterdir()) == ["ffmpeg", "ffprobe"]
    assert "ffmpeg" not in [s.name for s in tm.missing()]
    assert _leftovers(tmp_path) == []


def test_checksum_mismatch_leaves_previous_install(tmp_path):
    (tmp_path / "deno").mkdir()
    (tmp_path / "deno" / "deno").write_text("old")
    spec = _spec("linux", "deno")
    net = FakeNet(spec, _zip({"deno": b"new"}), sums_hex="f" * 64)
    tm = ToolManager(root=tmp_path, platform="linux", fetch=net.fetch, fetch_text=net.fetch_text,
                     which=_no_which, run=FakeRun({}))
    with pytest.raises(FriendlyError) as exc:
        tm.install(spec, lambda d, t: None)
    assert exc.value.code == "tools_missing"
    assert exc.value.details == f"checksum mismatch for {spec.asset}"
    assert (tmp_path / "deno" / "deno").read_text() == "old"
    assert _leftovers(tmp_path) == []


def _files_outside(root: Path) -> list[Path]:
    return [p for p in root.parent.rglob("*") if p.is_file() and root not in p.parents]


@pytest.mark.parametrize("evil", ["x/bin/D:evil.dll", "x/bin/a:b.dll", "x/bin/../evil", "x/bin/ev|il"])
def test_zip_unsafe_member_is_rejected(tmp_path, evil):
    root = tmp_path / "tools"
    (root / "ffmpeg").mkdir(parents=True)
    (root / "ffmpeg" / "ffmpeg.exe").write_text("old")
    spec = _spec("win32", "ffmpeg")
    net = FakeNet(spec, _zip({"x/bin/ffmpeg.exe": b"new", evil: b"evil"}))
    tm = ToolManager(root=root, platform="win32", fetch=net.fetch, fetch_text=net.fetch_text,
                     which=_no_which, run=FakeRun({}))
    with pytest.raises(FriendlyError) as exc:
        tm.install(spec, lambda d, t: None)
    assert exc.value.code == "tools_missing"
    assert "unsafe archive member" in exc.value.details
    assert [p.name for p in (root / "ffmpeg").iterdir()] == ["ffmpeg.exe"]
    assert (root / "ffmpeg" / "ffmpeg.exe").read_text() == "old"
    assert _files_outside(root) == []
    assert _leftovers(root) == []


def test_zip_member_outside_patterns_is_ignored(tmp_path):
    root = tmp_path / "tools"
    spec = _spec("linux", "deno")
    net = FakeNet(spec, _zip({"../evil": b"evil", "deno": b"deno-binary"}))
    ToolManager(root=root, platform="linux", fetch=net.fetch, fetch_text=net.fetch_text,
                which=_no_which, run=FakeRun({})).install(spec, lambda d, t: None)
    assert [p.name for p in (root / "deno").iterdir()] == ["deno"]
    assert _files_outside(root) == []


def test_tar_unsafe_member_is_rejected(tmp_path):
    root = tmp_path / "tools"
    spec = _spec("linux", "ffmpeg")
    net = FakeNet(spec, _tar_xz({"x/bin/ffmpeg": b"ffmpeg", "x/bin/../ffprobe/../bin/ffprobe": b"evil"}))
    tm = ToolManager(root=root, platform="linux", fetch=net.fetch, fetch_text=net.fetch_text,
                     which=_no_which, run=FakeRun({}))
    with pytest.raises(FriendlyError) as exc:
        tm.install(spec, lambda d, t: None)
    assert exc.value.code == "tools_missing"
    assert not (root / "ffmpeg").exists()
    assert _files_outside(root) == []
    assert _leftovers(root) == []


def test_fetch_failure_midway_cleans_up(tmp_path):
    spec = _spec("linux", "yt-dlp")
    net = FakeNet(spec, b"x" * 1000, fail_midway=True)
    tm = ToolManager(root=tmp_path, platform="linux", fetch=net.fetch, fetch_text=net.fetch_text,
                     which=_no_which, run=FakeRun({}))
    with pytest.raises(FriendlyError) as exc:
        tm.install(spec, lambda d, t: None)
    assert exc.value.code == "network"
    assert "connection reset" in exc.value.details
    assert _leftovers(tmp_path) == []
    assert not (tmp_path / "yt-dlp").exists()
    assert "yt-dlp" in [s.name for s in tm.missing()]


@pytest.mark.parametrize(
    ("where", "error"),
    [
        ("fetch", urllib.error.URLError(socket.gaierror(-3, "Temporary failure in name resolution"))),
        ("fetch", TimeoutError("timed out")),
        ("fetch", ConnectionResetError("reset by peer")),
        ("fetch_text", urllib.error.URLError("no route")),
        ("fetch_text", socket.timeout("read timed out")),
        ("fetch_text", OSError("network is unreachable")),
    ],
)
def test_network_failure_is_network_error(tmp_path, where, error):
    spec = _spec("linux", "deno")
    net = FakeNet(spec, _zip({"deno": b"deno-binary"}))

    def failing(*args):
        if where == "fetch":
            Path(args[1]).write_bytes(b"partial")
        raise error

    fetch = failing if where == "fetch" else net.fetch
    fetch_text = failing if where == "fetch_text" else net.fetch_text
    tm = ToolManager(root=tmp_path, platform="linux", fetch=fetch, fetch_text=fetch_text,
                     which=_no_which, run=FakeRun({}))
    with pytest.raises(FriendlyError) as exc:
        tm.install(spec, lambda d, t: None)
    assert exc.value.code == "network"
    assert exc.value.message == "No connection to YouTube."
    assert exc.value.details.startswith("deno: ")
    assert _leftovers(tmp_path) == []
    assert not (tmp_path / "deno").exists()


def test_bad_archive_is_still_tools_missing(tmp_path):
    spec = _spec("linux", "deno")
    net = FakeNet(spec, b"not a zip")
    tm = ToolManager(root=tmp_path, platform="linux", fetch=net.fetch, fetch_text=net.fetch_text,
                     which=_no_which, run=FakeRun({}))
    with pytest.raises(FriendlyError) as exc:
        tm.install(spec, lambda d, t: None)
    assert exc.value.code == "tools_missing"
    assert _leftovers(tmp_path) == []


@pytest.mark.parametrize("platform, exe", [("linux", ""), ("win32", ".exe")])
def test_bundled_ffmpeg_needs_ffprobe(tmp_path, platform, exe):
    tm = ToolManager(root=tmp_path, platform=platform, which=_no_which, run=FakeRun({}))
    (tmp_path / "ffmpeg").mkdir()
    (tmp_path / "ffmpeg" / f"ffmpeg{exe}").write_text("ffmpeg")
    assert "ffmpeg" in [s.name for s in tm.missing()]
    (tmp_path / "ffmpeg" / f"ffprobe{exe}").write_text("ffprobe")
    assert "ffmpeg" not in [s.name for s in tm.missing()]


def test_install_ffmpeg_without_ffprobe_fails(tmp_path):
    spec = _spec("linux", "ffmpeg")
    net = FakeNet(spec, _tar_xz({"x/bin/ffmpeg": b"ffmpeg"}))
    tm = ToolManager(root=tmp_path, platform="linux", fetch=net.fetch, fetch_text=net.fetch_text,
                     which=_no_which, run=FakeRun({}))
    with pytest.raises(FriendlyError) as exc:
        tm.install(spec, lambda d, t: None)
    assert exc.value.code == "tools_missing"
    assert exc.value.details == f"ffprobe not found in {spec.asset}"
    assert not (tmp_path / "ffmpeg").exists()
    assert _leftovers(tmp_path) == []


def test_should_check_update():
    assert should_check_update(0, 86400) is True
    assert should_check_update(100, 86399) is False


def test_deno_version_floor(tmp_path):
    old = ToolManager(root=tmp_path, platform="linux", which=_no_which,
                      run=FakeRun({"--version": ["deno 2.2.9 (stable, release, x86_64-unknown-linux-gnu)\n"]}))
    assert old.deno_ok() is False
    new = ToolManager(root=tmp_path, platform="linux", which=_no_which,
                      run=FakeRun({"--version": ["deno 2.9.7 (stable, release, x86_64-unknown-linux-gnu)\nv8 13\n"]}))
    assert new.deno_ok() is True
    broken = ToolManager(root=tmp_path, platform="linux", which=_no_which, run=FakeRun({}))
    assert broken.deno_ok() is False


def test_missing_includes_outdated_deno(tmp_path):
    (tmp_path / "deno").mkdir()
    (tmp_path / "deno" / "deno").write_text("binary")
    tm = ToolManager(root=tmp_path, platform="linux", which=_no_which,
                     run=FakeRun({"--version": ["deno 2.2.9 (stable)\n"]}))
    assert "deno" in [s.name for s in tm.missing()]


def test_update_ytdlp_reports_versions(tmp_path):
    run = FakeRun({"-U": ["Updated yt-dlp to stable@2026.10.01\n"],
                   "--version": ["2026.08.19\n", "2026.10.01\n"]})
    tm = ToolManager(root=tmp_path, platform="linux", which=_no_which, run=run)
    assert tm.update_ytdlp() == ("2026.08.19", "2026.10.01")
    exe = str(tmp_path / "yt-dlp" / "yt-dlp")
    assert [c[0] for c in run.calls] == [exe, exe, exe]
    assert ["--version" in c for c in run.calls] == [True, False, True]
    assert all("--ignore-config" in c for c in run.calls)


def test_update_ytdlp_failed_run_reports_no_new_version(tmp_path):
    # -U exits non-zero (offline): the old version must not be reported as "up to date".
    failing = FakeRun({"-U": [1], "--version": ["2026.08.19\n", "2026.08.19\n"]})
    tm = ToolManager(root=tmp_path, platform="linux", which=_no_which, run=failing)
    assert tm.update_ytdlp() == ("2026.08.19", None)
    # -U cannot even start.
    missing = FakeRun({"--version": ["2026.08.19\n"]})
    tm = ToolManager(root=tmp_path, platform="linux", which=_no_which, run=missing)
    assert tm.update_ytdlp() == ("2026.08.19", None)


def test_ytdlp_version_none_on_failure(tmp_path):
    tm = ToolManager(root=tmp_path, platform="linux", which=_no_which, run=FakeRun({}))
    assert tm.ytdlp_version() is None


def test_update_all_reinstalls_deno_and_bundled_ffmpeg(tmp_path):
    tm = ToolManager(root=tmp_path, platform="linux", which=_no_which,
                     run=FakeRun({"-U": ["ok\n"], "--version": ["2026.08.19\n", "2026.10.01\n"]}))
    installed, asked = [], []
    tm.install = lambda spec, on_bytes: installed.append(spec.name)

    def on_bytes_for(name):
        asked.append(name)
        return lambda d, t: None

    assert tm.update_all(on_bytes_for) == ("2026.08.19", "2026.10.01")
    assert installed == asked == ["ffmpeg", "deno"]


def test_update_all_skips_system_ffmpeg(tmp_path):
    which = {"ffmpeg": "/usr/bin/ffmpeg", "ffprobe": "/usr/bin/ffprobe"}.get
    tm = ToolManager(root=tmp_path, platform="linux", which=which,
                     run=FakeRun({"-U": ["ok\n"], "--version": ["a\n", "b\n"]}))
    installed = []
    tm.install = lambda spec, on_bytes: installed.append(spec.name)
    tm.update_all(lambda name: (lambda d, t: None))
    assert installed == ["deno"]


def test_update_all_reinstalls_broken_ytdlp(tmp_path):
    # yt-dlp does not answer --version: no -U, a fresh checksum-verified install instead.
    run = FakeRun({"--version": [1, "2026.10.01\n"]})
    tm = ToolManager(root=tmp_path, platform="linux", which=_no_which, run=run)
    installed = []
    tm.install = lambda spec, on_bytes: installed.append(spec.name)
    assert tm.update_all(lambda name: (lambda d, t: None)) == (None, "2026.10.01")
    assert installed == ["yt-dlp", "ffmpeg", "deno"]
    assert not any("-U" in c for c in run.calls)


def test_update_all_reinstalls_ytdlp_broken_by_update(tmp_path):
    run = FakeRun({"-U": ["ok\n"], "--version": ["2026.08.19\n", 1, "2026.10.01\n"]})
    tm = ToolManager(root=tmp_path, platform="linux", which=_no_which, run=run)
    installed = []
    tm.install = lambda spec, on_bytes: installed.append(spec.name)
    assert tm.update_all(lambda name: (lambda d, t: None)) == ("2026.08.19", "2026.10.01")
    assert installed == ["yt-dlp", "ffmpeg", "deno"]


def test_update_all_failed_self_update_keeps_working_ytdlp(tmp_path):
    run = FakeRun({"-U": [1], "--version": ["2026.08.19\n", "2026.08.19\n"]})
    tm = ToolManager(root=tmp_path, platform="linux", which=_no_which, run=run)
    installed = []
    tm.install = lambda spec, on_bytes: installed.append(spec.name)
    assert tm.update_all(lambda name: (lambda d, t: None)) == ("2026.08.19", None)
    assert installed == ["ffmpeg", "deno"]


def test_tar_rejects_traversal_even_if_data_filter_normalizes_name(tmp_path, monkeypatch):
    """Newer tarfile.data_filter releases normalize `a/../b` to `b`; our check must not rely on it."""
    real = tarfile.data_filter

    def normalizing(member, dest_path):
        member = real(member, dest_path)
        return member.replace(name=posixpath.normpath(member.name), deep=False)

    monkeypatch.setattr(tarfile, "data_filter", normalizing)
    root = tmp_path / "tools"
    spec = _spec("linux", "ffmpeg")
    net = FakeNet(spec, _tar_xz({"x/bin/ffmpeg": b"ffmpeg", "x/bin/../ffprobe/../bin/ffprobe": b"evil"}))
    tm = ToolManager(root=root, platform="linux", fetch=net.fetch, fetch_text=net.fetch_text,
                     which=_no_which, run=FakeRun({}))
    with pytest.raises(FriendlyError) as exc:
        tm.install(spec, lambda d, t: None)
    assert exc.value.code == "tools_missing"
    assert "unsafe archive member" in exc.value.details
    assert not (root / "ffmpeg").exists()
    assert _files_outside(root) == []
    assert _leftovers(root) == []


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "fixture, asset, expected",
    [
        # Real Deno release files: Linux uses `<hex>  <name>`, Windows uses PowerShell's
        # Get-FileHash list format (Algorithm / Hash / Path, upper-case hex, CRLF).
        ("deno_linux.sha256sum", "deno-x86_64-unknown-linux-gnu.zip",
         "c6527f24f4b16031d3ae4fa9f658d5f11534c8d84ce7dc8502420280919c3490"),
        ("deno_windows.sha256sum", "deno-x86_64-pc-windows-msvc.zip",
         "a0c3101b4158d1dfb7d6a78a7bf0f3de80c96bb423c152beec8beb22786f2238"),
    ],
)
def test_expected_sha256_reads_real_deno_sums(fixture, asset, expected):
    from ytdownloader.core.tools import _expected_sha256

    text = (FIXTURES / fixture).read_text(encoding="utf-8")
    assert _expected_sha256(text, asset) == expected


def test_expected_sha256_getfilehash_for_other_asset_is_none():
    from ytdownloader.core.tools import _expected_sha256

    text = (FIXTURES / "deno_windows.sha256sum").read_text(encoding="utf-8")
    assert _expected_sha256(text, "something-else.zip") is None


def _release(tag, assets, state="uploaded"):
    base = f"https://github.com/yt-dlp/FFmpeg-Builds/releases/download/{tag}/"
    return {
        "tag_name": tag,
        "draft": False,
        "assets": [
            {"name": n, "state": state, "browser_download_url": base + n} for n in assets
        ],
    }


WIN_ZIP = "ffmpeg-N-127654-g7045cc9b80-win64-gpl-shared.zip"
RELEASES = [
    _release("latest", ["checksums.sha256", "ffmpeg-master-latest-win64-gpl-shared.zip"]),
    _release("autobuild-2026-10-17-20-33", ["checksums.sha256", "ffmpeg-N-127600-gaaaa-win64-gpl-shared.zip"]),
    _release("autobuild-2026-10-18-17-17", [
        "checksums.sha256", WIN_ZIP, "ffmpeg-N-127654-g7045cc9b80-winarm64-gpl-shared.zip",
    ]),
]


def test_ffmpeg_resolves_to_newest_autobuild():
    tm = ToolManager(root=Path("unused"), platform="win32",
                     fetch_text=lambda url: json.dumps(RELEASES), which=_no_which, run=FakeRun({}))
    spec = tm._resolve(_spec("win32", "ffmpeg"))
    assert spec.asset == WIN_ZIP
    assert spec.url.endswith("/autobuild-2026-10-18-17-17/" + WIN_ZIP)
    assert spec.sums_url.endswith("/autobuild-2026-10-18-17-17/checksums.sha256")


def test_ffmpeg_skips_autobuild_still_uploading():
    releases = RELEASES[:2] + [_release("autobuild-2026-10-18-17-17", ["checksums.sha256", WIN_ZIP], state="starter")]
    tm = ToolManager(root=Path("unused"), platform="win32",
                     fetch_text=lambda url: json.dumps(releases), which=_no_which, run=FakeRun({}))
    assert tm._resolve(_spec("win32", "ffmpeg")).asset == "ffmpeg-N-127600-gaaaa-win64-gpl-shared.zip"


@pytest.mark.parametrize("reply", ['{"message": "API rate limit exceeded"}', "not json", "[]"])
def test_ffmpeg_falls_back_to_latest(reply):
    tm = ToolManager(root=Path("unused"), platform="linux",
                     fetch_text=lambda url: reply, which=_no_which, run=FakeRun({}))
    spec = _spec("linux", "ffmpeg")
    assert tm._resolve(spec) == spec


def test_other_tools_are_not_resolved():
    def no_api(url):
        raise AssertionError("no API call for yt-dlp")

    tm = ToolManager(root=Path("unused"), platform="linux", fetch_text=no_api, which=_no_which, run=FakeRun({}))
    spec = _spec("linux", "yt-dlp")
    assert tm._resolve(spec) is spec


def test_ffmpeg_installs_from_resolved_autobuild(tmp_path):
    payload = _zip({
        "ffmpeg-N-127654-g7045cc9b80-win64-gpl-shared/bin/ffmpeg.exe": b"ffmpeg-exe",
        "ffmpeg-N-127654-g7045cc9b80-win64-gpl-shared/bin/ffprobe.exe": b"ffprobe-exe",
    })
    build = RELEASES[2]["assets"]
    urls = {a["name"]: a["browser_download_url"] for a in build}

    def fetch(url, dest, on_bytes):
        assert url == urls[WIN_ZIP]
        Path(dest).write_bytes(payload)

    def fetch_text(url):
        if url.startswith("https://api.github.com/"):
            return json.dumps(RELEASES)
        assert url == urls["checksums.sha256"]
        return f"{'0' * 64}  ffmpeg-master-latest-win64-gpl-shared.zip\n{_sha(payload)}  {WIN_ZIP}\n"

    tm = ToolManager(root=tmp_path, platform="win32", fetch=fetch, fetch_text=fetch_text,
                     which=_no_which, run=FakeRun({}))
    tm.install(_spec("win32", "ffmpeg"), lambda d, t: None)

    assert sorted(p.name for p in (tmp_path / "ffmpeg").iterdir()) == ["ffmpeg.exe", "ffprobe.exe"]
    assert _leftovers(tmp_path) == []
