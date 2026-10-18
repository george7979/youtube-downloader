# YouTube Downloader

Save a YouTube video as an MP4 file together with a Markdown note and a transcript built from
YouTube's own captions. Made for keeping videos in an Obsidian vault: the note sits next to the
video, embeds it, and carries the description, chapters and a timestamped transcript.

The app has a window (Windows and Linux) and a command line for scripts and for Claude Code
(Linux / WSL). It works with **YouTube only**, one video at a time.

![The main window](pics/main-window.png)

## Contents

- [What you get](#what-you-get)
- [Legal notice](#legal-notice)
- [Installation](#installation)
- [Using the window](#using-the-window)
- [How it works](#how-it-works)
- [Command line (Linux / WSL)](#command-line-linux--wsl)
- [Troubleshooting](#troubleshooting)
- [Files, folders and uninstalling](#files-folders-and-uninstalling)
- [Building from source](#building-from-source)

## What you get

For every video, in the folder you choose:

| File | What it is |
|---|---|
| `Title.mp4` | The video, H.264 + AAC where YouTube offers it (plays everywhere), up to 1080p by default. MP3 audio is available instead. |
| `Title.md` | A note: metadata, the embedded video, the description, chapters and the transcript with clickable timestamps. |
| `Title.<lang>.srt` | Optional subtitles file, when you tick **Also save subtitles (.srt)**. |

A note looks like this (shortened; the values are placeholders):

```markdown
---
title: "Video title"

channel: "Channel name"

url: https://www.youtube.com/watch?v=VIDEO_ID

published: 2026-10-01

downloaded: 2026-10-18

duration: "26:02"

video: "[[Video title.mp4]]"

transcript: youtube-manual-en

tags: [video, youtube]

---

# Video title

![[Video title.mp4]]

## Description
…
## Chapters
- [00:00](https://youtu.be/VIDEO_ID?t=0) Intro
…
## Transcript
[00:00](https://youtu.be/VIDEO_ID?t=0) First paragraph of the transcript…

[00:47](https://youtu.be/VIDEO_ID?t=47) Second paragraph…
```

## Legal notice

**This application is a technical tool. The user is responsible for the legality of downloading
content.**

Allowed use:
- Your own YouTube content (authors can download their own videos)
- Content under Creative Commons licenses, public domain
- Backup of your own materials
- Educational use within fair use

Prohibited use:
- Downloading others' content without the author's consent
- Commercial distribution of downloaded content
- Copyright infringement

Respect copyright and the [YouTube Terms of Service](https://www.youtube.com/t/terms).

## Installation

System requirements: Windows 10 / 11, or Linux (Ubuntu 22.04+ / Debian 12+), 64-bit, and an
internet connection with IPv4.

### Windows — installer

1. Download `youtube-downloader-X.X.X-setup.exe` from
   [Releases](https://github.com/george7979/youtube-downloader/releases).
2. Run it. It creates a Start Menu shortcut and a desktop icon; the last page can start the app
   right away.

> **Windows SmartScreen warning**
>
> The installer is **not digitally signed** (code signing certificates cost about $300 a year).
> Windows may show a "Windows protected your PC" warning. To install anyway, click
> **More info**, then **Run anyway**. The application is open source — you can review the full
> source code in this repository.

Installing a new version over an old one keeps your settings. The Windows app is windowed only;
it has no command line.

### Linux — .deb package

```bash
sudo apt install ./youtube-downloader_X.X.X_amd64.deb
youtube-downloader          # opens the window
```

`ffmpeg` is a recommended package; without it the app downloads its own copy.

### Linux / WSL — from the repository (command line, Claude Code)

```bash
sudo apt install python3-tk     # Tk for the window, with smooth fonts
uv tool install --python /usr/bin/python3 /path/to/youtube-downloader
youtube-downloader tools        # checks the setup, downloads missing tools
```

This needs a system Python 3.12 or newer (Ubuntu 24.04 and later). On older systems use
`uv tool install --managed-python --python 3.12 /path/to/youtube-downloader` instead: everything
works, but uv's own Python draws the window with a plain bitmap font and letters in place of
arrows and check marks. The command line is the same either way.

### First run

The download tools are not bundled with the app (see [Tools and updates](#tools-and-updates)).
On the first start the app downloads them, checks their SHA-256 checksums and shows progress for
each one: about 150 MB on Windows, about 60 MB on Linux with a system ffmpeg (about 210 MB
without). This needs an internet connection once; if it fails, the window shows the error and a
**Retry** button.

![First run](pics/first-run.png)

## Using the window

1. **Paste a YouTube link.** The app checks it right away and shows the title, channel, length,
   publication date, thumbnail and the available subtitles. For a typed link, or to try again,
   click **Check**.
2. **Choose what to save:** **MP4** or **MP3**, the **Quality**, the **Subtitles** track for the
   transcript, and the two boxes — **Save note with transcript (.md)** (it reads "without
   transcript" when Subtitles is set to None) and **Also save subtitles (.srt)**.
3. **Save to** shows the folder — your system Downloads folder at first. Click the path to open
   it; **Change** picks another one. The folder and your choices are remembered.
4. **Click Download.** While it runs, a progress bar and a status line show each step (fetching
   the video, downloading, merging, writing the note); **Cancel** stops it and removes partial
   files. You can paste and check the next link while a download runs.

**Recent** lists the last three downloads; **Show file** shows the file in its folder,
**Clear** empties the list (the files stay on disk). The footer shows the engine version and
whether it is up to date; the **⋯** menu has **Update engine**, **Open log folder** and **About**.


## How it works

### Tools and updates

The app drives three external tools, downloaded from their official releases into your user
profile:

| Tool | What it does |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Reads the video page and downloads the streams — the download engine. |
| [ffmpeg](https://github.com/yt-dlp/FFmpeg-Builds) | Merges the video and audio streams into one MP4, makes MP3s. On Linux a system ffmpeg is used when installed. |
| [Deno](https://deno.com) | Lets yt-dlp solve the JavaScript challenges YouTube puts in front of its streams. |

Every download is verified against the checksum published with the release before it is
installed, and a tool is only replaced once the new copy is complete.

YouTube changes often, and an old yt-dlp stops working. So:

- **At most once a day**, when the window starts (or before a `get` / `info` command), the app
  updates yt-dlp in the background. The footer shows the result: *updated*, *up to date* or
  *update failed*. A download you start meanwhile waits for the update to finish.
- If the update fails (for example offline), the next start tries again; the app keeps working
  with the version it has.
- **Update engine** (in the **⋯** menu, and next to errors an update may fix) updates yt-dlp
  now, reinstalls it if it no longer runs, and refreshes ffmpeg and Deno. It is not available
  while a download runs.

### Video and audio

- **MP4:** the best stream up to the chosen height, preferring H.264 video and AAC audio, which
  play everywhere. If a video has no H.264 at that height (some 4K videos), the app uses VP9/AV1
  and says so — some players cannot play those.
- **Quality is a ceiling.** The app picks the highest height the video has at or below your
  setting. A video that only goes up to 720p is downloaded in 720p without lowering your
  setting for the next one.
- **MP3:** the best audio stream, converted to MP3 at 192 kbit/s.

### Subtitles and the transcript

The transcript comes from captions YouTube already has; nothing is transcribed by the app.

- **Which tracks are offered:** every manual (uploaded) subtitle language, plus the automatic
  captions in the language that is actually spoken in the video. YouTube's machine translations
  of automatic captions into other languages are never offered.
- **Which track is chosen by default:** your last choice of language, if this video has it;
  otherwise manual subtitles in the video's own language; otherwise the first manual track;
  otherwise the automatic captions. Manual subtitles always win over automatic ones in the same
  language. Picking **None** saves the note without a transcript.
- **How the transcript is built:** automatic captions repeat each line as it scrolls; the
  repeats are removed. The text is joined into paragraphs of about 45 seconds that end on a
  full sentence (at most 90 seconds), and a new paragraph starts at every chapter. Each
  paragraph begins with its time as a link to that moment on YouTube (`mm:ss`, or `h:mm:ss` for
  videos of an hour or more).
- The `transcript:` field of the note says where the text came from: `youtube-manual-<lang>`,
  `youtube-auto-<lang>` or `none`.
- The `.srt` file is written from the same track, cleaned the same way.

### The note

- The header (frontmatter) holds the title, channel, link, publication and download dates,
  length, a link to the video file, the transcript source and the tags `video` and `youtube`.
  Obsidian shows it as properties; other Markdown viewers show one field per line.
- `![[Title.mp4]]` embeds the video in Obsidian; the link works by file name, so the video can
  be moved anywhere in the vault.
- `#` and `[[` in the description, chapter titles and transcript are escaped, so YouTube text
  never turns into Obsidian tags or links.
- **An existing note is never overwritten or deleted** — your own edits are safe.

### File names and downloading again

- Files are named after the video title, with characters Windows does not allow replaced and
  long titles shortened.
- If a file with that name belongs to a different video, the new files get the video ID:
  `Title [AbCdEfGhIjK].mp4`. Nothing is ever overwritten.
- The app recognises a video already in the folder by its note (the `url:` field) or by the ID
  in a file name — not by the title alone, so it never attaches a note to someone else's file:

| In the folder | What happens |
|---|---|
| video + note | "Already downloaded" — **Show file** or **Download again** |
| note, no video | downloads the video, keeps your note |
| video with `[ID]`, no note | writes only the note |
| `Title.mp4` without a note | treated as another video: the download goes to `Title [ID].mp4` |

- MP4 and MP3 are separate: having the MP4 does not stop an MP3 download of the same video.

### Connection and reliability

- The app talks to YouTube over IPv4 only. YouTube sometimes flags a home IPv6 address
  ("Sign in to confirm you're not a bot") while the same computer's IPv4 address works fine.
- When YouTube refuses a stream (HTTP 403), the download is retried once automatically with
  fresh stream links; you only see an error if the second try fails too.
- YouTube sometimes holds back each ~10 MB piece of a video for about 20 seconds, so a download
  pauses and resumes in steps. This comes from YouTube and varies with the time of day; the log
  records every pause longer than 15 seconds.
- Downloading many videos in a row can trigger YouTube's limits (about 300 videos an hour);
  the app shows `rate_limit` and you wait a few minutes.

## Command line (Linux / WSL)

The command line never asks questions and never uses the folder saved by the window: you pass
the folder every time. Like the window, `get` and `info` update yt-dlp at most once a day before
they start (a status line on stderr; if the update fails they warn and carry on).

```bash
youtube-downloader get <URL> --out DIR [--quality 1080] [--audio] [--subs LANG|none]
                             [--srt] [--no-note] [--force] [--json]
youtube-downloader info <URL> [--json]
youtube-downloader tools [--update] [--json]
```

- `get` downloads the video and writes the note. `--audio` makes an MP3, `--subs pl` picks a
  caption language (manual before automatic), `--subs none` skips captions, `--force` downloads
  again even if the files exist. Without `--subs` the default track follows the rules above
  (the command line does not remember a language). Without `--force`, an existing video + note
  is reported and nothing is downloaded.
- `info` shows the metadata, available heights and caption tracks, without downloading.
- `tools` shows the tool paths and versions; `--update` updates them like **Update engine**.
- Progress goes to stderr. With `--json` stdout carries exactly one JSON object.

Success from `get --json`:

```json
{"ok": true, "video_id": "AbCdEfGhIjK", "title": "...",
 "media": "/path/Title.mp4", "note": "/path/Title.md", "srt": null,
 "transcript": "youtube-auto-pl", "already_exists": false, "warnings": []}
```

`transcript` is `youtube-manual-<lang>`, `youtube-auto-<lang>` or `none`. `already_exists: true`
means nothing was downloaded and the paths are the existing files; `transcript` is then always
`"none"` because the note was not rebuilt (the existing note may well contain a transcript).
With `--no-note` and the video already in the folder, `note` is `null`.

`info --json`:

```json
{"ok": true, "video_id": "AbCdEfGhIjK", "title": "...", "channel": "...",
 "url": "https://www.youtube.com/watch?v=AbCdEfGhIjK", "duration": 3935,
 "published": "2020-07-01", "heights": [720, 360, 144],
 "subtitles": [{"lang": "pl", "kind": "auto"}]}
```

`duration` is in seconds and `published` an ISO date; both can be `null`. `heights` are the
available video heights, highest first; `kind` is `manual` or `auto`.

`tools --json`:

```json
{"ok": true,
 "tools": {"yt-dlp": {"path": "...", "version": "2026.10.18"},
           "ffmpeg": {"path": "..."}, "deno": {"path": "..."}},
 "updated": null}
```

`ffmpeg.path` is the folder holding `ffmpeg` and `ffprobe`. `updated` is `null` without
`--update`; with it, `{"from": "<old>", "to": "<new>"}`, where `"to": null` means the yt-dlp
update failed.

Failure (any command):

```json
{"ok": false, "error": {"code": "unavailable", "message": "...", "hint": "...", "details": "..."}}
```

Exit codes: `0` success, `1` error, `2` wrong usage (argparse prints to stderr, no JSON),
`130` cancelled with Ctrl+C.

### Claude Code skill

`integrations/claude-skill/youtube-downloader/SKILL.md` teaches Claude Code to use the command
line. Copy that folder to `~/.claude/skills/youtube-downloader/`. The skill always asks you for
the destination folder first.

## Troubleshooting

Every error says what happened and what to do; **Show details** reveals the technical text to
copy into a bug report. The command line returns the same `code`.

| Error code | What it means | What to do |
|---|---|---|
| `invalid_url` | The text is not a YouTube video link. | Paste a link like `https://www.youtube.com/watch?v=...`. Playlists are not supported. |
| `unavailable` | Private, removed, age-restricted, members-only or region-blocked video. | Check the link or try another video. Logging in is not supported. |
| `network` | No connection to YouTube (or, while installing the tools, to GitHub). | Check your internet connection and try again. |
| `bot_check` | YouTube suspects automated access (common on VPNs and office networks). | Click **Update engine** (`youtube-downloader tools --update`) and try again, or try again later. |
| `engine_outdated` | YouTube changed something and yt-dlp can no longer read the video. | Click **Update engine** (`youtube-downloader tools --update`) and try again. |
| `forbidden` | YouTube refused the video stream (HTTP 403). The app already retried once. | Try again; if it keeps happening, click **Update engine**. |
| `rate_limit` | Too many requests. | Wait a few minutes. |
| `write_failed` | The folder is not writable or the disk is full. | Pick another folder or free up space. |
| `tools_missing` | Download tools are missing, or a downloaded tool failed its checksum or was incomplete. | Restart the app while online, or run `youtube-downloader tools`. |
| `cancelled` | You cancelled the download. | Nothing to do; partial files were removed. |
| `unknown` | Anything else. | Use **Show details** (or `error.details` in JSON) in a bug report. |

Other things worth knowing:

- **Log file:** **⋯** menu → **Open log folder**. Each download logs yt-dlp's warnings, every
  pause longer than 15 seconds and the total time — attach it when reporting slow downloads.
- **Application won't start on Linux:** `sudo apt reinstall youtube-downloader`; for dependency
  errors `sudo apt-get install -f`.

## Files, folders and uninstalling

| What | Windows | Linux |
|---|---|---|
| Settings and the recent list | `%APPDATA%\YouTube Downloader\` | `~/.config/youtube-downloader/` |
| Tools (yt-dlp, ffmpeg, Deno) | `%LOCALAPPDATA%\YouTube Downloader\tools\` | `~/.local/share/youtube-downloader/tools/` |
| Log `app.log` | `%LOCALAPPDATA%\YouTube Downloader\Logs\` | `~/.local/state/youtube-downloader/log/` |
| Downloads | the folder you choose (Downloads by default) | the folder you choose (`~/Downloads` by default) |

**Windows:** uninstall in Settings → Apps. The uninstaller removes the program, the tools, the
settings, the recent list and the logs. Your downloaded videos and notes are never removed.

**Linux:**

```bash
sudo dpkg -r youtube-downloader     # keep settings
sudo dpkg -P youtube-downloader     # purge the package
```

Settings, tools and logs stay in your profile (the folders above); delete them by hand to remove
everything.

## Building from source

See [docs/BUILDING.md](docs/BUILDING.md).

## Reporting issues

Found a bug? Have a feature suggestion?
**GitHub Issues:** https://github.com/george7979/youtube-downloader/issues
