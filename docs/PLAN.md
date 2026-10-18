# PLAN — YouTube Downloader

## Stan

- **Produkcja:** v1.3.0 (GitHub Releases, 2026-05-16) — na Windows nie startuje (log w `C:\tmp`).
- **Na `dev`:** v2.0.0 wdrożona w kodzie, dokumentacji i skillu; czeka na testy akceptacyjne PO
  i pierwszy przebieg CI z budowaniem paczek.

## Etapy

### Etap 1 — v2.0.0: przebudowa (wdrożony, czeka na akceptację PO)

- Projekt: `docs/superpowers/specs/2026-10-18-v2-design.md` (zaakceptowany przez PO)
- Plan wykonawczy: `docs/superpowers/plans/2026-10-18-v2.md`
- Gotowe: rdzeń, CLI, GUI, paczki i CI, dokumentacja (`README.md`, `docs/BUILDING.md`,
  `docs/TECH.md`), skill Claude Code (`integrations/claude-skill/youtube-downloader/`)
- Poprawki po przeglądzie całej gałęzi wykonane (aktualizacja silnika, błędy sieci, CLI,
  okno, CI)
- Otwarte: `docs/TECH.md` → „Known Issues”
- Zamknięcie: testy akceptacyjne PO na Windows i Linux/WSL (spec §11), potem PR `dev` →
  `main` i tag `v2.0.0` (za zgodą PO)

## Bieżący krok

PO: (1) za jego zgodą push `dev`; (2) CI buduje instalator Windows i `.deb` jako artefakty;
(3) PO instaluje wersję na Windows i przechodzi siedem scenariuszy ze spec §11, a na
Linux/WSL scenariusz 2 z zainstalowanym skillem. Uwagi PO → poprawki na `dev`.

## Backlog

- Wtyczka PO Token (`bgutil-ytdlp-pot-provider`) jako plan B na blokady YouTube.
- Playlisty / kolejka (dziś świadomie poza zakresem).
