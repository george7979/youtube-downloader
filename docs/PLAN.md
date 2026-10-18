# PLAN — YouTube Downloader

## Stan

- **Produkcja:** v1.3.0 (GitHub Releases, 2026-05-16) — na Windows nie startuje (log w `C:\tmp`).
- **W toku:** v2.0.0 na gałęzi `dev`.

## Etapy

### Etap 1 — v2.0.0: przebudowa (w toku)

- Projekt: `docs/superpowers/specs/2026-10-18-v2-design.md` (zaakceptowany przez PO 2026-10-18)
- Plan wykonawczy: `docs/superpowers/plans/2026-10-18-v2.md` (15 zadań, SDD)
- Kamienie: rdzeń (zadania 1–10) → CLI (11) → GUI (12–13) → paczki i CI (14) → dokumentacja, skill, 2.0.0 (15)
- Zamknięcie: testy akceptacyjne PO na Windows i Linux/WSL (spec §11), potem PR `dev` → `main` i tag `v2.0.0` (za zgodą PO)

## Bieżący krok

Wykonanie planu `2026-10-18-v2.md` metodą SDD — start od zadania 1.

## Backlog

- Wtyczka PO Token (`bgutil-ytdlp-pot-provider`) jako plan B na blokady YouTube.
- Playlisty / kolejka (dziś świadomie poza zakresem).
