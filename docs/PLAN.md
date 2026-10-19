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
- Wygląd po analizie UI (makiety zaakceptowane przez PO:
  `docs/superpowers/specs/2026-10-18-ui-polish-mockups/index.html`): jeden wypełniony przycisk
  w akcencie `#C62828`, zwarty układ, auto-Check po wklejeniu, nowe okno pierwszego
  uruchomienia.
- Zamknięcie: akceptacja PO na Windows i Linux/WSL (spec §11), potem PR `dev` → `main` i tag
  `v2.0.0` (za zgodą PO). Na GitHubie wisi stary lekki tag `v2.0.0` (`fc52839`, 2025-08-17,
  bez wydania) — przed nowym tagiem trzeba go usunąć z remote'u (za zgodą PO).

## Bieżący krok

PO testuje na Windows instalator z ostatniego przebiegu „Build and Release” na `dev` (artefakt
`windows-installer`) — scenariusze ze spec §11 oraz nowy wygląd. Na Linux/WSL scenariusz 2
przez skill. Uwagi PO → poprawki na `dev`.

Uwaga PO z Linux/WSL: okno z liter „Y”/„Z” i postrzępionych rogów, menu „⋯” nie znika.
Poprawione na `dev`: menu (X11), paczka Linux na Pythonie z systemowym Tk z Xft (TECH
„Pakowanie”); CI i budowanie zielone (przebieg 39162447294: 20 rodzin fontów w Tk, okno żyje
10 s w kontenerach 22.04 i 24.04); retest PO na Linuksie zaliczony (ikony i czcionki dobre).

## Backlog

- Wtyczka PO Token (`bgutil-ytdlp-pot-provider`) jako plan B na blokady YouTube.
- Przestoje YouTube co ~10 MB (TECH → Known Issues): zbadać przy kolejnym wystąpieniu z `-v`.
- Playlisty / kolejka (dziś świadomie poza zakresem).
