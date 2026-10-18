# CLAUDE.md — YouTube Downloader

Aplikacja (okno + CLI) pobierająca filmy z YouTube jako MP4 z notatką Markdown i transkryptem,
na silniku yt-dlp pobieranym osobno. Python 3.12, CustomTkinter. Repo publiczne na GitHubie,
interfejs, README, BUILDING i skill po angielsku; dokumentacja projektowa po polsku.

## Dokumentacja (CKM)

- `docs/PRD.md` — co i dlaczego · `docs/PLAN.md` — etapy i bieżący krok · `docs/TECH.md` —
  architektura, narzędzia, fakty o yt-dlp, znane problemy
- `docs/BUILDING.md` — środowisko, paczki, wydanie · `README.md` — dla użytkownika
- `docs/superpowers/specs/2026-10-18-v2-design.md` — projekt z decyzjami PO (D1–D14)
- Stan projektu trzymaj w PLAN.md, nie tutaj.

## Środowisko i uruchamianie

```bash
uv sync --managed-python --python 3.12     # uv-managed Python: systemowy nie ma tkinter
uv run pytest -q                           # testy; GUI wymaga wyświetlacza (WSLg lokalnie, xvfb w CI)
uv run youtube-downloader                  # okno
uv run youtube-downloader info <URL>       # CLI: get / info / tools, --json
uv run pyinstaller youtube-downloader.spec --clean   # paczka; dalej docs/BUILDING.md
```

Bez wyświetlacza testy GUI same się pomijają. Po zmianie `version.py` albo `pyproject.toml`
`uv` odbuduje instalację edytowalną (`cache-keys`); skrypt konsolowy bywa przestarzały po
nietypowej instalacji — `uv sync --reinstall-package youtube-downloader`.

## Zasady kodu

- `ytdownloader/core/` nie importuje `tkinter`/`customtkinter`; GUI i CLI wołają tylko
  `Service` i `ToolManager`.
- Żadnych zakodowanych ścieżek (`/tmp`, `~/Downloads`, `C:\…`) — wszystko z `core/paths.py`.
- Tekst interfejsu i wyjścia CLI wyłącznie po angielsku.
- Podprocesy: `stdin=DEVNULL`, `encoding="utf-8", errors="replace"`, na Windows
  `CREATE_NO_WINDOW`; yt-dlp zawsze z `--ignore-config`.
- W `core` nie ma pakietu `yt-dlp` — silnik to zewnętrzny plik.
- Istniejąca notatka `.md` nigdy nie jest nadpisywana.
- Testy bez sieci; nowe fixtury z prawdziwych odpowiedzi yt-dlp w `tests/fixtures/`.

## Pułapki sprawdzone w tym projekcie

- Systemowy Python bez `tkinter` → zawsze uv-managed (`--managed-python`).
- `zipfile.extractall` gubi bit wykonywalności → `chmod 0o755` po rozpakowaniu.
- Postęp postprocesorów yt-dlp (scalanie, MP3) idzie na **stderr**, pobierania na stdout.
- `--print` wycisza yt-dlp → zawsze `--progress`.
- `-S res:<q>,vcodec:h264,acodec:m4a` — kolejność kluczy ma znaczenie.
- `%` w `-o` trzeba podwoić; własne `-o` zawsze (yt-dlp zamienia `?` na `？`).
- Zrzutów ekranu okna pod WSLg nie zrobisz; wygląd sprawdza PO na Windows.
- PyInstaller na Linuksie nie znajduje `libtcl`/`libtk` z Pythona uv — dokłada je `.spec`.
- Windows `.exe` jest okienkowy (`console=False`): `sys.stdout` bywa `None`, CLI tam nie działa.
- Skill z `integrations/claude-skill/` kopiuje do `~/.claude/skills/` użytkownik; repo jest
  źródłem, kopia instalowana to wtórna.

## Git

Praca na `dev`. Commit wolno; `git push`, tag i PR do `main` — za zgodą PO.
