---
name: youtube-downloader
description: Download a YouTube video as an MP4 (or MP3) together with a Markdown note and a transcript built from YouTube captions, ready for a notes folder such as an Obsidian vault. Use when the user gives a YouTube link and wants the video saved, downloaded, archived, or turned into a note with a transcript.
---

# YouTube Downloader

Wraps the `youtube-downloader` command line. It saves `Title.mp4`, a note `Title.md` (metadata,
embedded video, description, chapters, timestamped transcript) and optionally `Title.<lang>.srt`.
YouTube links only. Linux / WSL.

Requires `youtube-downloader` on `PATH`. If `command -v youtube-downloader` finds nothing, tell
the user to install it (`uv tool install --managed-python --python 3.12 <path-to-repo>`, see the
repo README) instead of trying to work around it. The first run downloads yt-dlp, Deno and,
without a system ffmpeg, ffmpeg; it can take a few minutes.

## Always ask for the destination folder first

Before every download, ask the user which folder to save to, and wait for the answer. Do not
guess, do not reuse an earlier folder without asking, do not default to the current directory.
For a Windows vault under WSL the path looks like `/mnt/c/Users/<name>/Vault/Videos`. The folder
is created if it does not exist.

## Commands

```bash
# Download (video + note). Always JSON, always an explicit folder.
youtube-downloader get "<URL>" --out "<DIR>" --json

# Options
#   --quality 720      max height (default 1080)
#   --audio            MP3 only
#   --subs pl          caption language; --subs none = no captions
#   --srt              also write an .srt file
#   --no-note          skip the Markdown note
#   --force            download again even if the files already exist (only on request)

# Look first, without downloading (title, channel, length, heights, caption tracks)
youtube-downloader info "<URL>" --json

# Tool status / update (yt-dlp is updated when YouTube changes)
youtube-downloader tools --json
youtube-downloader tools --update --json
```

Quote the URL. Progress is printed on stderr; the result is one JSON object on stdout. Downloads
can take minutes; run them to completion and do not interrupt. Once a day `get` and `info` first
update yt-dlp themselves ("Checking for engine updates…" on stderr); a warning that the update
failed is not an error — the command carries on.

`info --json` returns `video_id`, `title`, `channel`, `url` (canonical watch link), `duration`
(seconds or `null`), `published` (ISO date or `null`), `heights` (available video heights,
highest first) and `subtitles` (a list of `{"lang", "kind"}`, `kind` = `manual` or `auto`). Use
it to pick `--quality` or `--subs`.

`tools --json` returns `tools` with `yt-dlp` (`path`, `version`), `ffmpeg` (`path`: the folder
with `ffmpeg` and `ffprobe`) and `deno` (`path`), plus `updated`: `null` without `--update`,
otherwise `{"from", "to"}` — `"to": null` means the yt-dlp update failed.

## Reading the result

Success:

```json
{"ok": true, "video_id": "...", "title": "...", "media": "/dir/Title.mp4",
 "note": "/dir/Title.md", "srt": null, "transcript": "youtube-auto-pl",
 "already_exists": false, "warnings": []}
```

Tell the user: the title, the `media` and `note` paths, and the transcript kind:

- `youtube-manual-<lang>` — human-made captions, reliable.
- `youtube-auto-<lang>` — YouTube's speech recognition; may contain recognition errors.
- `none` — no transcript in the note (no captions, or `--subs none`). Offer to try another
  language (`info` lists the tracks) only if one exists.

Report every entry in `warnings` (for example a missing caption language, "Kept your existing
note.", or "No H.264 at this quality — downloading VP9/AV1 instead").

`already_exists: true`: the video and its note were already in that folder and nothing was
downloaded; `media` and `note` are the existing files (`transcript` then shows `none` because
the note was not rebuilt - do not read it as "no transcript"; with `--no-note` `note` can be
`null`). Say so and give the paths. Run
again with `--force` only if the user explicitly asks to download again; a note that exists is
never overwritten.

## Errors

Failure: `{"ok": false, "error": {"code", "message", "hint", "details"}}`, exit code 1.
Give the user `message` and `hint` in plain words; keep `details` for when they ask or for a
bug report.

| code | Tell the user |
|---|---|
| `invalid_url` | That is not a YouTube video link. Ask for a link like `https://www.youtube.com/watch?v=...` (playlists are not supported). |
| `unavailable` | The video is private, removed, age-restricted, members-only or region-blocked. Logging in is not supported. |
| `network` | No connection to YouTube. Check the internet and retry. |
| `bot_check` | YouTube is blocking the request (often a VPN). Update the engine and retry once (below); if it still fails, suggest trying later or without the VPN. |
| `engine_outdated` | YouTube changed something and the download engine needs an update. Update the engine and retry once (below). |
| `rate_limit` | Too many requests. Wait a few minutes. |
| `forbidden` | YouTube refused the video stream (HTTP 403); the app already retried once. Update the engine and retry once (below). |
| `write_failed` | The folder is not writable or the disk is full. Ask for another folder. |
| `tools_missing` | Tools could not be downloaded. Run `youtube-downloader tools` while online and retry. |
| `cancelled` | The download was cancelled (exit code 130); partial files were removed. |
| `unknown` | Something unexpected. Show `details` and suggest a bug report. |

On `engine_outdated`, `bot_check` or `forbidden`: run `youtube-downloader tools --update --json` once, tell
the user the yt-dlp version change (`updated.from` → `updated.to`), then run the failed command
again exactly once. Retry at most once in total (also after a `network` fix); do not loop. If
the retry fails the same way, report it with `message` and `hint`.

Exit code 2 means a usage error (wrong or missing arguments, for example no `--out`): there is
no JSON, the explanation is on stderr. Fix the command and run it again.
