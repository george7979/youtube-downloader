# Additional Transcript Languages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a video and its note are already in the folder and the user picks another subtitle language, write a full note `Title.<lang>.md` in that language without downloading the video again.

**Architecture:** A language note is an ordinary note from `render_note` with one extra frontmatter field `main_note` that marks it. `naming.plan_names` never treats a language note as the main note but uses it to identify the video. `Service.download` decides whether a language can be added, returns that as `addable_lang` on an `already_exists` result, and writes the language note when the request carries `add_transcript=True` (yt-dlp `--skip-download` + subtitles, the existing `note_only` path). The window offers it as a button in "Already downloaded"; the CLI sets `add_transcript` when `--subs <lang>` is explicit.

**Tech Stack:** Python 3.12, CustomTkinter, pytest, yt-dlp as an external binary.

**Spec:** `docs/superpowers/specs/2026-10-19-transcript-languages-design.md` (accepted by the PO). Project rules: `CLAUDE.md`.

## Global Constraints

- `ytdownloader/core/` never imports `tkinter`/`customtkinter`; GUI and CLI call only `Service` and `ToolManager`.
- No hard-coded paths; UI and CLI text in English only.
- Tests never use the network; `FakeRunner` / `NoRunner` in `tests/test_service.py` stand in for yt-dlp.
- An existing note (main or language) is never overwritten, modified or deleted.
- A language note never counts as the main note (`plan_names`, `already_exists`, base name).
- Language codes are compared exactly as the track gives them (`en-US` ≠ `en`); manual vs auto of one language is the same language.
- "Add transcript" requires `save_note=True`; with notes off, behaviour is today's.
- Recent is not changed by adding a language note; "Download again" (`force`) works as today.
- README "How it works", PRD, TECH and the skill describe a changed rule in the same commit (CLAUDE.md).
- Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; work on `dev`, no push.

## Review Focus

1. A video whose title ends in what looks like a language (`Report.pl` → main note `Report.pl.md`) — its main note must still be the main note (Task 1 test).
2. Regional codes (`pt-BR`): file `Title.pt-BR.md`, recognised as a language note (Task 1 test).
3. A user's own `Title.pl.md` that the app did not write (no `main_note`) — never overwritten, no button for `pl` (Task 2 test).
4. Cancel while adding a language — no partial language note; video, main note untouched (Task 2 test).
5. MP3 already there with its note — the language note embeds `Title.mp3` (Task 2 test).

---

### Task 1: Language-note format and recognition

**Files:**
- Modify: `ytdownloader/core/note.py` (`render_note`)
- Modify: `ytdownloader/core/naming.py` (`note_video_id`, `plan_names`, `NamePlan`)
- Test: `tests/test_note.py`, `tests/test_naming.py`

**Interfaces:**
- Produces: `render_note(info, media_filename, transcript_kind, paragraphs, downloaded, main_note: str | None = None) -> str` — when `main_note` is given, the frontmatter gets `main_note: "[[<main_note>]]"` (JSON-quoted like the other fields) right after `transcript:`; nothing else changes.
- Produces: `note_fields(note: Path) -> dict[str, str]` in `naming.py` — frontmatter `key: value` pairs from the file head (same tolerant reading as `note_video_id` today: first line `---`, stop at the closing `---`), values stripped and with surrounding JSON double quotes decoded. `note_video_id` uses it.
- Produces: `is_language_note(note: Path) -> bool` — `"main_note" in note_fields(note)`.
- Produces: `NamePlan.language_note(lang: str) -> Path` — `folder / f"{base}.{lang}.md"` (folder = `media.parent`).
- Produces: `plan_names` — the main-note search skips language notes; if no main note of this video exists but a language note does, `base` = that note's stem with its last `.<suffix>` removed, `existing_media` is looked up with that base, `existing_note` stays `None`, and the `[ID]` collision rule does not fire for that base.

- [ ] **Step 1: Write the failing tests**

`tests/test_note.py`:
```python
def test_language_note_links_its_main_note():
    out = render_note(make_info(), "a.mp4", "youtube-auto-pl", None, date(2026, 10, 19),
                      main_note="a")
    assert 'transcript: youtube-auto-pl\n\nmain_note: "[[a]]"\n' in out

def test_main_note_has_no_main_note_field():
    assert "main_note" not in render_note(make_info(), "a.mp4", "none", None, date(2026, 10, 19))
```

`tests/test_naming.py` (helper: write a note with `url:` of `ID` and optional `main_note`):
```python
def test_language_note_is_not_the_main_note(tmp_path):
    # T.md, T.pl.md (main_note), T.mp4 -> existing_note == T.md, base == "T",
    # language_note("pl") == tmp_path / "T.pl.md"

def test_language_note_alone_identifies_the_video(tmp_path):
    # T.pl.md (main_note) + T.mp4, no T.md -> base == "T", existing_media == T.mp4,
    # existing_note is None, note == tmp_path / "T.md"  (no " [ID]" suffix)

def test_title_ending_like_a_language_stays_main(tmp_path):
    # "Report.pl.md" without main_note, "Report.pl.mp4" -> existing_note == Report.pl.md,
    # base == "Report.pl"

def test_regional_language_note(tmp_path):
    # T.md + T.pt-BR.md (main_note) -> existing_note == T.md; is_language_note(T.pt-BR.md)

def test_note_fields_decodes_quotes(tmp_path):
    # '---\ntitle: "A \\"b\\""\nmain_note: "[[T]]"\n---\n' -> {"title": 'A "b"', "main_note": "[[T]]"}
```

- [ ] **Step 2: Run them — expect failures** (`render_note` has no `main_note`; `note_fields`, `is_language_note`, `language_note` missing)

Run: `uv run pytest -q tests/test_note.py tests/test_naming.py`

- [ ] **Step 3: Implement** the Interfaces above. Keep `note_video_id`'s behaviour (BOM-less UTF-8 head of `_HEAD_BYTES`, `None` on read errors).

- [ ] **Step 4: Run the whole suite — all pass**

Run: `uv run pytest -q`

- [ ] **Step 5: Commit** — `feat(core): language notes carry main_note and never count as the main note`

---

### Task 2: Service — decide and write a language note

**Files:**
- Modify: `ytdownloader/core/models.py` (`DownloadRequest`, `DownloadResult`)
- Modify: `ytdownloader/core/service.py` (`download`, `_write_outputs`)
- Modify: `README.md` ("The note", "File names and downloading again"), `docs/PRD.md` (req. 6), `docs/TECH.md` (`naming.py`, `service.py` rows, "Nazwy i rozpoznawanie istniejących plików")
- Test: `tests/test_service.py`

**Interfaces:**
- Consumes: Task 1 (`render_note(..., main_note=)`, `note_fields`, `NamePlan.language_note`).
- Produces: `DownloadRequest.add_transcript: bool = False`.
- Produces: `DownloadResult.addable_lang: str | None = None` (set only on `already_exists=True` results when a language can be added) and `DownloadResult.note_lang: str | None = None` (language of the main note's transcript on `already_exists` results; `None` when it has none or the field is missing).

Rules (all from the spec): with media + main note present and `not req.force`:
- `track = pick_track(info, req.subs, remembered_lang)[0]`; main language from `note_fields(main)["transcript"]` — missing field → unknown (never addable); `"none"` → no language; `youtube-<kind>-<lang>` → `<lang>` (`value.split("-", 2)[2]`).
- addable when `req.save_note` and `track` and language known-or-none and `track.lang != main_lang` and `not names.language_note(track.lang).exists()`.
- not addable, or addable without `req.add_transcript` → today's `already_exists` result plus `addable_lang` / `note_lang`.
- addable with `req.add_transcript` → engine run with `note_only=True` and that `track`; on a VTT, write `names.language_note(track.lang)` via `render_note(..., main_note=names.base)` embedding the existing media's file name; `.srt` as today when `save_srt`; result `already_exists=False`, `media_path` = existing media, `note_path` = language note, `transcript` = `youtube-<kind>-<lang>`. No VTT → no language note, `note_path=None`, `transcript="none"`, warning `"No subtitles were downloaded."`.

- [ ] **Step 1: Write the failing tests** (in `tests/test_service.py`, using `FakeRunner`/`NoRunner`; main note `T.md` written by `render_note` with `transcript: youtube-auto-en`, media `T.mp4`, the `lecture` fixture has `pl-orig` auto captions)

```python
def test_other_language_is_offered_not_downloaded(tmp_path, lecture):
    # subs="pl", NoRunner -> already_exists True, addable_lang == "pl", note_lang == "en"

def test_add_transcript_writes_language_note_without_video(tmp_path, lecture, vtt):
    # subs="pl", add_transcript=True, FakeRunner files {"T.pl-orig.vtt": vtt}
    # -> "--skip-download" in args; T.pl.md exists with 'main_note: "[[T]]"', "![[T.mp4]]",
    #    "## Transcript"; T.md and T.mp4 bytes unchanged; result.note_path == T.pl.md,
    #    result.transcript == "youtube-auto-pl", already_exists False, no *.vtt left

def test_same_language_is_not_offered(tmp_path, lecture):
    # main note transcript youtube-manual-pl, subs="pl" -> addable_lang is None

def test_existing_language_note_is_not_offered(tmp_path, lecture):
    # T.pl.md already there (any content, even without main_note) -> addable_lang None,
    # and with add_transcript=True NoRunner is never called and T.pl.md is unchanged

def test_note_off_is_not_offered(tmp_path, lecture):
    # save_note=False, save_srt=True, subs="pl" -> addable_lang None (today's result)

def test_main_note_without_transcript_field_is_not_offered(tmp_path, lecture):
    # T.md with url only -> addable_lang None

def test_main_note_without_transcript_offers_any_language(tmp_path, lecture):
    # T.md rendered with transcript "none" -> addable_lang == "pl", note_lang is None

def test_add_transcript_without_subtitles_writes_nothing(tmp_path, lecture):
    # add_transcript=True, FakeRunner without a vtt -> no T.pl.md, note_path None,
    # "No subtitles were downloaded." in warnings

def test_cancel_while_adding_leaves_everything(tmp_path, lecture):
    # FakeRunner rc=-1 -> FriendlyError "cancelled"; T.md, T.mp4 unchanged; no T.pl.md

def test_language_note_for_mp3_embeds_the_mp3(tmp_path, lecture, vtt):
    # T.mp3 + T.md, mode="mp3", add_transcript=True -> "![[T.mp3]]" in T.pl.md

def test_deleted_main_note_is_rebuilt_from_language_note(tmp_path, lecture, vtt):
    # T.mp4 + T.pl.md (main_note) only, subs="pl" -> "--skip-download"; T.md written;
    # no "T [VIw16SXObUQ].mp4" planned; T.pl.md unchanged
```

- [ ] **Step 2: Run them — expect failures**

Run: `uv run pytest -q tests/test_service.py`

- [ ] **Step 3: Implement** the fields and rules. `_write_outputs` gets the note target explicitly (main note when none exists, the language note when adding, nothing otherwise) instead of deciding from `names.existing_note` alone. `_cleanup` must keep the language note's siblings it did not create (it already deletes only partial patterns).

- [ ] **Step 4: Update the docs** listed under Files: README gets one bullet under "The note" (`Title.<lang>.md`: a full note in another language, added without downloading the video again; your existing notes are never changed) and one row in the "In the folder" table; PRD req. 6 one sentence; TECH rows and the naming section describe `main_note` and the rules above.

- [ ] **Step 5: Run the whole suite — all pass**

Run: `uv run pytest -q`

- [ ] **Step 6: Commit** — `feat(core): add a transcript in another language as Title.<lang>.md without the video`

---

### Task 3: CLI — `get --subs <lang>` adds the language note

**Files:**
- Modify: `ytdownloader/cli.py` (`_run_get`)
- Modify: `README.md` (Command line bullets), `integrations/claude-skill/youtube-downloader/SKILL.md` (Reading the result / `already_exists`)
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: Task 2 (`DownloadRequest.add_transcript`).
- Produces: `add_transcript = req.subs not in (SUBS_DEFAULT, SUBS_NONE)`; JSON shape unchanged.

- [ ] **Step 1: Write the failing tests** (follow `test_flags_map_to_request`):

```python
def test_explicit_subs_ask_to_add_a_transcript(tmp_path):
    # get URL --out DIR --subs pl -> captured request.add_transcript is True

@pytest.mark.parametrize("subs", [None, "none"])
def test_default_or_none_subs_do_not_add(tmp_path, subs):
    # -> add_transcript is False
```

- [ ] **Step 2: Run — expect failures.** `uv run pytest -q tests/test_cli.py`
- [ ] **Step 3: Implement** in `_run_get`.
- [ ] **Step 4: Docs:** README CLI bullet for `get` ("`--subs pl` on a video that is already here with its note writes `Title.pl.md` — the JSON's `note` points to it"); skill: same, next to the `already_exists` paragraph. Copy the skill to `~/.claude/skills/youtube-downloader/`.
- [ ] **Step 5: Whole suite passes.** `uv run pytest -q`
- [ ] **Step 6: Commit** — `feat(cli): --subs <lang> adds a transcript note to an existing download`

---

### Task 4: Window — "Add transcript (<lang>)" in "Already downloaded"

**Files:**
- Modify: `ytdownloader/gui/widgets.py` (`ask_already_downloaded`)
- Modify: `ytdownloader/gui/app.py` (`_ask_already`, `_on_download_ok`, `_remember`)
- Modify: `README.md` ("Using the window", one sentence)
- Test: `tests/test_gui_smoke.py`

**Interfaces:**
- Consumes: Task 2 (`DownloadResult.addable_lang`, `.note_lang`, `DownloadRequest.add_transcript`).
- Produces: `ask_already_downloaded(parent, title: str, has_note: bool = True, add_lang: str | None = None, note_lang: str | None = None) -> str` returning `"add" | "show" | "again" | "cancel"`; `dialog.buttons["add"]` exists only when `add_lang`.

Copy (exact): button `f"Add transcript ({add_lang})"`, packed first, the only filled button (`set_primary_enabled`/default `CTkButton` style from `theme.py`); with `note_lang` the line reads `f"The video and its note (transcript: {note_lang}) are already in this folder."`, otherwise as today. Status after adding: `f"Done. Saved {note_path.name}"` + warnings; without a note written: `"No transcript added"` + warnings.

- [ ] **Step 1: Write the failing tests** (follow `test_already_downloaded_choices` / `test_ask_already_downloaded_text`):

```python
def test_dialog_offers_add_transcript(make_window):
    # add_lang="pl", note_lang="en" -> buttons["add"] text "Add transcript (pl)";
    # invoking it returns "add"; description mentions "(transcript: en)"

def test_dialog_without_add_lang_is_unchanged(make_window):
    # no "add" key in buttons

def test_add_choice_runs_add_transcript_request(make_window, tmp_path, monkeypatch):
    # FakeService: first result already_exists with addable_lang "pl"; dialog stubbed to "add"
    # -> second download call has add_transcript True and force False;
    #    status starts with "Done. Saved T.pl.md"; Recent unchanged
```

- [ ] **Step 2: Run — expect failures.** `uv run pytest -q tests/test_gui_smoke.py`
- [ ] **Step 3: Implement.** `_remember` skips `add_recent` for `add_transcript` requests (still saves options and `subs_lang`).
- [ ] **Step 4: README** — under "Using the window": "If the video is already in the folder and you picked another subtitle language, **Add transcript** saves a note in that language without downloading the video again."
- [ ] **Step 5: Whole suite passes.** `uv run pytest -q`
- [ ] **Step 6: Commit** — `feat(gui): Add transcript (<lang>) in the Already downloaded dialog`

---

### Task 5: Close-out

- [ ] Update `docs/PLAN.md` (Etap 1 bullet: additional transcript languages; "Bieżący krok": PO tests the new installer) and the spec's status line ("wdrożony").
- [ ] `uv run pytest -q` all pass; `git status` clean except the PO's uncommitted `pics/main-window.png`.
- [ ] Delete this plan file (executed plans are not kept in the repo; git history has it).
- [ ] Commit — `docs(plan): additional transcript languages implemented`
