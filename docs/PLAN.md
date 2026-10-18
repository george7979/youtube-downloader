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

Testy akceptacyjne PO na Windows w toku. Pierwsza próba wywróciła się na sumie kontrolnej Deno
(plik `.sha256sum` dla Windows ma format PowerShell `Get-FileHash`) — naprawione i wypchnięte;
PO instaluje instalator z przebiegu „Build and Release” dla tej poprawki (artefakt
`windows-installer`) na poprzednią wersję i kontynuuje scenariusze ze spec §11 (lista w
spec §11; po przypomnienie z opisem kroków — poprosić Claude). Na Linux/WSL scenariusz 2
przez skill (CLI i skill zainstalowane na thinkpadzie).

CI na Windows bywa czerwone przez losowy błąd startu Tcl/Tk w testach GUI (aplikacji nie
dotyczy); poprawka testów jest w commicie lokalnym, do wypchnięcia razem z poprawkami po
testach PO. Uwagi PO → poprawki na `dev`; po akceptacji PR `dev` → `main` i tag `v2.0.0`
(za zgodą PO).

Otwarte pytanie do PO (bez decyzji): czy deinstalator ma usuwać też ustawienia i logi —
dziś usuwa program i narzędzia, ustawienia i logi zostają celowo, pobrane pliki zawsze zostają.

## Backlog

- Wtyczka PO Token (`bgutil-ytdlp-pot-provider`) jako plan B na blokady YouTube.
- Playlisty / kolejka (dziś świadomie poza zakresem).
