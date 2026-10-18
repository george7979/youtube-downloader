"""External tools (yt-dlp, ffmpeg, Deno): download, checksum-verify, atomic install, update."""

from __future__ import annotations

import fnmatch
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable

from ytdownloader import __version__
from ytdownloader.core import paths
from ytdownloader.core.errors import FriendlyError, friendly

OnBytes = Callable[[int, int | None], None]
Fetch = Callable[[str, Path, OnBytes], None]  # url, dest, on_bytes(done, total)
FetchText = Callable[[str], str]

DENO_MIN_VERSION = (2, 3, 0)
UPDATE_CHECK_INTERVAL = 86400  # seconds
VERSION_TIMEOUT = 60
UPDATE_TIMEOUT = 300
HTTP_TIMEOUT = 60
CHUNK = 64 * 1024

_YTDLP = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/"
_FFMPEG = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/"
_DENO = "https://github.com/denoland/deno/releases/latest/download/"


@dataclass(frozen=True)
class ToolSpec:
    name: str  # "yt-dlp" | "ffmpeg" | "deno"
    url: str
    sums_url: str
    asset: str  # name looked up in the sums file
    archive: str | None  # None | "zip" | "tar.xz"
    members: tuple[str, ...]  # glob(s) inside the archive to install flat; () for a plain file
    target: str  # installed main executable name
    approx_mb: int  # for the first-run text


@dataclass(frozen=True)
class ToolPaths:
    yt_dlp: Path
    ffmpeg_dir: Path
    deno: Path


def tool_specs(platform: str) -> list[ToolSpec]:
    if platform == "win32":
        ytdlp_asset, exe = "yt-dlp.exe", ".exe"
        ffmpeg_asset = "ffmpeg-master-latest-win64-gpl-shared.zip"
        ffmpeg_archive, ffmpeg_members, ffmpeg_mb = "zip", ("*/bin/*",), 84
        deno_asset = "deno-x86_64-pc-windows-msvc.zip"
    else:
        ytdlp_asset, exe = "yt-dlp_linux", ""
        ffmpeg_asset = "ffmpeg-master-latest-linux64-gpl.tar.xz"
        ffmpeg_archive, ffmpeg_members, ffmpeg_mb = "tar.xz", ("*/bin/ffmpeg", "*/bin/ffprobe"), 149
        deno_asset = "deno-x86_64-unknown-linux-gnu.zip"
    return [
        ToolSpec("yt-dlp", _YTDLP + ytdlp_asset, _YTDLP + "SHA2-256SUMS", ytdlp_asset,
                 None, (), "yt-dlp" + exe, 18),
        ToolSpec("ffmpeg", _FFMPEG + ffmpeg_asset, _FFMPEG + "checksums.sha256", ffmpeg_asset,
                 ffmpeg_archive, ffmpeg_members, "ffmpeg" + exe, ffmpeg_mb),
        ToolSpec("deno", _DENO + deno_asset, _DENO + deno_asset + ".sha256sum", deno_asset,
                 "zip", ("deno" + exe,), "deno" + exe, 40),
    ]


def should_check_update(last_check: float, now: float) -> bool:
    return now - last_check >= UPDATE_CHECK_INTERVAL


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": f"youtube-downloader/{__version__}"})


def http_fetch(url: str, dest: Path, on_bytes: OnBytes) -> None:
    with urllib.request.urlopen(_request(url), timeout=HTTP_TIMEOUT) as resp:
        length = resp.headers.get("Content-Length")
        total = int(length) if length and length.isdigit() else None
        done = 0
        on_bytes(done, total)
        with open(dest, "wb") as out:
            while chunk := resp.read(CHUNK):
                out.write(chunk)
                done += len(chunk)
                on_bytes(done, total)


def http_fetch_text(url: str) -> str:
    with urllib.request.urlopen(_request(url), timeout=HTTP_TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _expected_sha256(sums_text: str, asset: str) -> str | None:
    for line in sums_text.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[1].strip().lstrip("*") == asset:
            return parts[0].lower()
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _matches(member: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(member, p) for p in patterns)


_UNSAFE_CHARS = frozenset('<>:"/\\|?*') | frozenset(chr(c) for c in range(32))


def _flat_target(member: str, dest: Path) -> Path:
    """Flattened install path for an archive member; rejects anything that could escape `dest`."""
    parts = member.replace("\\", "/").split("/")
    name = parts[-1]
    if (
        ".." in parts
        or name in ("", ".")
        or any(ch in _UNSAFE_CHARS for ch in name)
        or PureWindowsPath(name).name != name
        or PurePosixPath(name).name != name
    ):
        raise ValueError(f"unsafe archive member: {member!r}")
    target = dest / name
    if target.parent != dest:
        raise ValueError(f"unsafe archive member: {member!r}")
    return target


def _extract_zip(archive: Path, patterns: tuple[str, ...], dest: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir() or not _matches(info.filename, patterns):
                continue
            with zf.open(info) as src, open(_flat_target(info.filename, dest), "wb") as out:
                shutil.copyfileobj(src, out, CHUNK)


def _extract_tar(archive: Path, patterns: tuple[str, ...], dest: Path) -> None:
    with tarfile.open(archive, "r:xz") as tf:
        for member in tf:
            if not _matches(member.name, patterns):
                continue
            member = tarfile.data_filter(member, str(dest))  # rejects unsafe members
            if not member.isfile():
                continue
            src = tf.extractfile(member)
            assert src is not None
            with src, open(_flat_target(member.name, dest), "wb") as out:
                shutil.copyfileobj(src, out, CHUNK)


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def _rmdir_if_empty(path: Path) -> None:
    try:
        path.rmdir()
    except OSError:
        pass


class ToolManager:
    def __init__(
        self,
        root: Path | None = None,
        platform: str = sys.platform,
        fetch: Fetch = http_fetch,
        fetch_text: FetchText = http_fetch_text,
        which: Callable[[str], str | None] = shutil.which,
        run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ):
        self.root = Path(root) if root is not None else paths.tools_dir()
        self.platform = platform
        self.specs = tool_specs(platform)
        self._fetch = fetch
        self._fetch_text = fetch_text
        self._which = which
        self._run = run

    def _spec(self, name: str) -> ToolSpec:
        return next(s for s in self.specs if s.name == name)

    def _system_ffmpeg_dir(self) -> Path | None:
        if self.platform != "linux":
            return None
        ffmpeg = self._which("ffmpeg")
        if ffmpeg and self._which("ffprobe"):
            return Path(ffmpeg).parent
        return None

    def paths(self) -> ToolPaths:
        return ToolPaths(
            yt_dlp=self.root / "yt-dlp" / self._spec("yt-dlp").target,
            ffmpeg_dir=self._system_ffmpeg_dir() or self.root / "ffmpeg",
            deno=self.root / "deno" / self._spec("deno").target,
        )

    def missing(self) -> list[ToolSpec]:
        p = self.paths()
        result = []
        for spec in self.specs:
            if spec.name == "yt-dlp":
                ok = p.yt_dlp.is_file()
            elif spec.name == "ffmpeg":
                ok = self._system_ffmpeg_dir() is not None or (p.ffmpeg_dir / spec.target).is_file()
            else:
                ok = p.deno.is_file() and self.deno_ok()
            if not ok:
                result.append(spec)
        return result

    # --- subprocess helpers -------------------------------------------------

    def _output(self, args: list[str], timeout: int) -> str | None:
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        try:
            proc = self._run(
                args,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                **kwargs,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if proc.returncode != 0:
            return None
        return proc.stdout or ""

    def ytdlp_version(self) -> str | None:
        out = self._output([str(self.paths().yt_dlp), "--ignore-config", "--version"], VERSION_TIMEOUT)
        if not out or not out.strip():
            return None
        return out.strip().splitlines()[0].strip()

    def deno_ok(self) -> bool:
        out = self._output([str(self.paths().deno), "--version"], VERSION_TIMEOUT)
        if not out or not out.strip():
            return False
        words = out.strip().splitlines()[0].split()
        if len(words) < 2 or words[0] != "deno":
            return False
        try:
            version = tuple(int(x) for x in words[1].split(".")[:3])
        except ValueError:
            return False
        return version >= DENO_MIN_VERSION

    def update_ytdlp(self) -> tuple[str | None, str | None]:
        old = self.ytdlp_version()
        self._output([str(self.paths().yt_dlp), "--ignore-config", "-U"], UPDATE_TIMEOUT)
        return old, self.ytdlp_version()

    def update_all(self, on_bytes_for: Callable[[str], OnBytes]) -> tuple[str | None, str | None]:
        versions = self.update_ytdlp()
        if self._system_ffmpeg_dir() is None:
            self.install(self._spec("ffmpeg"), on_bytes_for("ffmpeg"))
        self.install(self._spec("deno"), on_bytes_for("deno"))
        return versions

    # --- install ------------------------------------------------------------

    def install(self, spec: ToolSpec, on_bytes: OnBytes) -> None:
        download_dir = self.root / ".download"
        staging_root = self.root / ".staging"
        part = download_dir / f"{spec.asset}.part"
        staging = staging_root / spec.name
        try:
            download_dir.mkdir(parents=True, exist_ok=True)
            _remove(part)
            _remove(staging)
            staging.mkdir(parents=True)

            self._fetch(spec.url, part, on_bytes)
            expected = _expected_sha256(self._fetch_text(spec.sums_url), spec.asset)
            if expected is None:
                raise friendly("tools_missing", details=f"no checksum listed for {spec.asset}")
            if _sha256(part) != expected:
                raise friendly("tools_missing", details=f"checksum mismatch for {spec.asset}")

            if spec.archive is None:
                os.replace(part, staging / spec.target)
            elif spec.archive == "zip":
                _extract_zip(part, spec.members, staging)
            elif spec.archive == "tar.xz":
                _extract_tar(part, spec.members, staging)
            else:
                raise ValueError(f"unsupported archive type {spec.archive!r}")
            if not (staging / spec.target).is_file():
                raise friendly("tools_missing", details=f"{spec.target} not found in {spec.asset}")

            if self.platform != "win32":
                for f in staging.iterdir():
                    f.chmod(0o755)
            self._swap_in(staging, self.root / spec.name)
        except FriendlyError:
            raise
        except Exception as exc:
            raise friendly("tools_missing", details=f"{spec.name}: {exc}") from exc
        finally:
            _remove(part)
            _remove(staging)
            _rmdir_if_empty(download_dir)
            _rmdir_if_empty(staging_root)

    def _swap_in(self, staging: Path, final: Path) -> None:
        old = final.with_name(f".{final.name}.old")
        _remove(old)
        had_previous = final.exists()
        if had_previous:
            os.replace(final, old)
        try:
            os.replace(staging, final)
        except BaseException:
            if had_previous:
                os.replace(old, final)
            raise
        if had_previous:
            _remove(old)
