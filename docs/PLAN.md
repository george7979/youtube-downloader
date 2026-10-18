# PLAN — YouTube Downloader

## Stan

- **Produkcja:** v1.3.0 (GitHub Releases) — na Windows nie startuje; zastąpi ją v2.0.0.
- **Na `dev`:** v2.0.0 gotowa w kodzie, dokumentacji i skillu, z poprawkami po pierwszych
  testach PO; CI (Ubuntu, Windows) i budowanie paczek przechodzą.

## Etapy

### Etap 1 — v2.0.0: przebudowa (wdrożony, testy akceptacyjne PO w toku)

- Projekt: `docs/superpowers/specs/2026-10-18-v2-design.md` (decyzje PO D1–D14); plan
  wykonawczy: `docs/superpowers/plans/2026-10-18-v2.md` (archiwum).
- Gotowe: rdzeń, CLI, GUI, paczki i CI, dokumentacja, skill Claude Code.
- Poprawki po testach PO na Windows (stan opisują PRD, TECH i README): suma Deno w formacie
  `Get-FileHash`, ffmpeg z niezmiennego `autobuild-*`, rozmiar okna liczony z ekranu,
  nagłówek notatki czytelny poza Obsidianem, ponowienie HTTP 403, `--force-ipv4`, log
  przestojów, Recent (3 pozycje, Clear), deinstalator czyszczący dane aplikacji, ikona
  w Ustawieniach Windows, „Run” na końcu instalatora.
- Wygląd po analizie UI (makiety zaakceptowane przez PO:
  `docs/superpowers/specs/2026-10-18-ui-polish-mockups/index.html`): jeden wypełniony przycisk
  w akcencie `#C62828`, zwarty układ, auto-Check po wklejeniu, nowe okno pierwszego
  uruchomienia.
- Zamknięcie: akceptacja PO na Windows i Linux/WSL (spec §11), potem PR `dev` → `main` i tag
  `v2.0.0` (za zgodą PO).

## Bieżący krok

PO testuje na Windows instalator z ostatniego przebiegu „Build and Release” na `dev` (artefakt
`windows-installer`) — scenariusze ze spec §11 oraz nowy wygląd. Na Linux/WSL scenariusz 2
przez skill. Uwagi PO → poprawki na `dev`.

## Backlog

- Wtyczka PO Token (`bgutil-ytdlp-pot-provider`) jako plan B na blokady YouTube.
- Przestoje YouTube co ~10 MB (TECH → Known Issues): zbadać przy kolejnym wystąpieniu z `-v`.
- Playlisty / kolejka (dziś świadomie poza zakresem).
