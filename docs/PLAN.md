# PLAN — YouTube Downloader

## Stan

- **Produkcja:** v1.3.0 (GitHub Releases) — na Windows nie startuje; zastąpi ją v2.0.0.
- **Na `dev`:** v2.0.0 gotowa w kodzie, dokumentacji i skillu, z poprawkami po pierwszych
  testach PO; CI (Ubuntu, Windows) i budowanie paczek przechodzą.

## Etapy

### Etap 1 — v2.0.0: przebudowa (wdrożony, testy akceptacyjne PO w toku)

- Projekt: `docs/superpowers/specs/2026-10-18-v2-design.md` (decyzje PO D1–D14).
- Gotowe: rdzeń, CLI, GUI, paczki i CI, dokumentacja, skill Claude Code.
- Poprawki po testach PO na Windows (stan opisują PRD, TECH i README): suma Deno w formacie
  `Get-FileHash`, ffmpeg z niezmiennego `autobuild-*`, rozmiar okna liczony z ekranu,
  nagłówek notatki czytelny poza Obsidianem, ponowienie HTTP 403, `--force-ipv4`, log
  przestojów, Recent (3 pozycje, Clear), deinstalator czyszczący dane aplikacji, ikona
  w Ustawieniach Windows, „Run” na końcu instalatora; po skanie bezpieczeństwa tekst od autora
  filmu zostaje w notatce zwykłym tekstem (bez zdalnych obrazków, łączy, HTML i bloków kodu).
- Kolejne języki transkrypcji (spec `docs/superpowers/specs/2026-10-19-transcript-languages-design.md`):
  ten sam film w innym języku napisów daje drugą notatkę `Tytuł.<lang>.md` bez ponownego
  pobierania wideo — usługa, `get --subs <lang>`, przycisk „Add transcript (<lang>)” w dialogu
  „Already downloaded”.
- Samo `.srt` (spec `docs/superpowers/specs/2026-10-19-srt-only-design.md`): przy zaznaczonym
  „Also save subtitles (.srt)” brakujący `Tytuł.<lang>.srt` da się dołożyć bez pobierania wideo
  i bez ruszania notatki — usługa, `get --srt`, przycisk „Add subtitles (<lang>)” w dialogu
  „Already downloaded” (gdy nie ma już czego dodać jako transkrypt).
- Wygląd po analizie UI (makiety zaakceptowane przez PO:
  `docs/superpowers/specs/2026-10-18-ui-polish-mockups/index.html`): jeden wypełniony przycisk
  w akcencie `#C62828`, zwarty układ, auto-Check po wklejeniu, nowe okno pierwszego
  uruchomienia.
- Zamknięcie: akceptacja PO na Windows i Linux/WSL (spec §11), potem PR `dev` → `main` i tag
  `v2.0.0` (za zgodą PO). Na GitHubie wisi stary lekki tag `v2.0.0` (`fc52839`, 2025-08-17,
  bez wydania) — przed nowym tagiem trzeba go usunąć z remote'u (za zgodą PO).

## Bieżący krok

PO testuje na Windows instalator z ostatniego przebiegu „Build and Release” na `dev` (artefakt
`windows-installer`) — scenariusze ze spec §11 oraz nowy wygląd; Linux/WSL zaliczony. „Add
transcript” i „Add subtitles” sprawdzone przez PO; zrzut `pics/main-window.png` z buildu 2.0.0
w repo. Do sprawdzenia przy okazji: zmiana jakości przez „Download again” podmienia `Tytuł.mp4`
pod tą samą nazwą, a link w notatce działa. Uwagi PO → poprawki na `dev`; po akceptacji
zamknięcie etapu (wyżej).

## Backlog

- Wtyczka PO Token (`bgutil-ytdlp-pot-provider`) jako plan B na blokady YouTube.
- Przestoje YouTube co ~10 MB (TECH → Known Issues): zbadać przy kolejnym wystąpieniu z `-v`.
- Playlisty / kolejka (dziś świadomie poza zakresem).
