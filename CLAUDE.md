# CLAUDE.md — YouTube Downloader

Aplikacja (okno + CLI) pobierająca filmy z YouTube jako MP4 z notatką Markdown i transkryptem,
na silniku yt-dlp pobieranym osobno. Python 3.12, CustomTkinter. Repo publiczne na GitHubie,
interfejs, README, BUILDING i skill po angielsku; dokumentacja projektowa po polsku.

## Dokumentacja (CKM)

- `docs/PRD.md` — co i dlaczego · `docs/PLAN.md` — etapy i bieżący krok · `docs/TECH.md` —
  architektura, narzędzia, fakty o yt-dlp, znane problemy
- `docs/BUILDING.md` — środowisko, paczki, wydanie · `README.md` — dla użytkownika, w tym
  „How it works”: zasady działania (aktualizacje, wybór napisów, transkrypt, nazwy, ponowne
  pobranie) — zmiana tych zasad w kodzie = aktualizacja README w tym samym commicie
- `docs/superpowers/specs/2026-10-18-v2-design.md` — projekt z decyzjami PO (D1–D14);
  `…/2026-10-18-ui-polish-mockups/index.html` — zaakceptowane makiety wyglądu (statyczny HTML)
- Stan projektu trzymaj w PLAN.md, nie tutaj.
- Przykłady w README, makietach i zrzutach: tylko dane zastępcze (`Video title`, `VIDEO_ID`);
  zrzut okna bez filmu i z pustą listą Recent.

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
- FFmpeg-Builds podmienia pliki wydania `latest` w miejscu co dzień — ffmpeg bierzemy z
  niezmiennego `autobuild-*` (`ToolManager._resolve`); `latest` tylko jako zapas.
- Plik `.sha256sum` Deno dla Windows ma format PowerShell `Get-FileHash`, nie `<hex>  <nazwa>` — każdy nowy plik sum sprawdzaj dla obu platform.
- Postęp postprocesorów yt-dlp (scalanie, MP3) idzie na **stderr**, pobierania na stdout.
- `--print` wycisza yt-dlp → zawsze `--progress`.
- „not a bot” tylko w Windows, a w WSL działa → to IPv6 (WSL go nie ma); stąd `--force-ipv4` w `COMMON`.
  Porównując zachowanie Windows i WSL, sprawdź `api64.ipify.org`, nie tylko IPv4.
- `-S res:<q>,vcodec:h264,acodec:m4a` — kolejność kluczy ma znaczenie.
- `%` w `-o` trzeba podwoić; własne `-o` zawsze (yt-dlp zamienia `?` na `？`).
- Zrzutów ekranu okna pod WSLg nie zrobisz; wygląd sprawdza PO na Windows.
- `geometry()`/`minsize()` w CustomTkinter są mnożone przez skalowanie Windows (150% na
  laptopach Full HD) — rozmiar okna licz z obszaru roboczego (`gui/placement.py`), nie na sztywno.
- Testy GUI w CI na Windows: ukryte (`withdraw`) okno zgłasza rozmiar 200×200 — sprawdzaj geometrię,
  o którą okno prosi (`record_geometry`), nie odczytaną.
- `CTkEntry` z tekstem zastępczym zwraca `get() == ""`, dopóki pole nie dostanie `<FocusIn>`.
- Wyłączony `CTkButton` zachowuje `fg_color` — przycisk główny przełączaj przez `set_primary_enabled`.
- Tk usuwa nazwaną czcionkę razem z jej obiektem Pythona — trzymaj referencję (`self._font_menu`).
- Testy, które ruszają schowek, muszą go przywrócić: WSLg dzieli schowek z Windows.
- PyInstaller na Linuksie nie znajduje `libtcl`/`libtk` z Pythona uv — dokłada je `.spec`.
- Windows `.exe` jest okienkowy (`console=False`): `sys.stdout` bywa `None`, CLI tam nie działa.
- Skill z `integrations/claude-skill/` kopiuje do `~/.claude/skills/` użytkownik; repo jest
  źródłem, kopia instalowana to wtórna.

## Git

Praca na `dev`. Commit wolno; `git push`, tag i PR do `main` — za zgodą PO.
