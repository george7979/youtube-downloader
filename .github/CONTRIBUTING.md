# Contributing

Thanks for helping. Bug reports, ideas and pull requests are all welcome.

## Reporting a bug or an idea

Use [Issues](https://github.com/george7979/youtube-downloader/issues/new/choose) and pick a
form. For a bug, include the app version (footer of the window), your system, the error code
and the text from **Show details**; for slow or stuck downloads also attach `app.log`
(⋯ → **Open log folder**).

Security problems go through a private report instead — see [SECURITY.md](SECURITY.md).

## Scope

The app downloads single YouTube videos with a Markdown note. Out of scope on purpose: other
sites, playlists and queues, logging in to YouTube (cookies), transcoding, macOS. Ideas in these
areas are fine to discuss, but please open an issue before writing code.

## Pull requests

1. For anything bigger than a small fix, open an issue first so we can agree on the approach.
2. Branch from `dev` and open the pull request against `dev` (`main` only takes releases).
3. Set up the environment and run the tests as described in
   [docs/BUILDING.md](../docs/BUILDING.md):

   ```bash
   uv sync --managed-python --python 3.12
   uv run pytest -q
   ```

4. Keep to the project rules:
   - `ytdownloader/core/` never imports `tkinter` / `customtkinter`; the window and the command
     line talk to the core only through `Service` and `ToolManager`.
   - No hard-coded paths — everything comes from `core/paths.py`.
   - Interface text and command-line output are in English.
   - Tests use no network; new fixtures come from real yt-dlp output in `tests/fixtures/`.
   - An existing note is never overwritten.
   - A change to how the app behaves (updates, subtitles, transcript, file names, downloading
     again) updates `README.md` → "How it works" in the same pull request.
5. Write commit messages in English, in the style of the existing history
   (`feat(core): …`, `fix(gui): …`, `docs: …`).

The maintainer reviews and merges; a release (version bump and tag) is made separately.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
