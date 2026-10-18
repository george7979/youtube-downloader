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

Testy akceptacyjne PO na Windows w toku (scenariusze w spec §11; po przypomnienie z opisem
kroków — poprosić Claude). Na Linux/WSL scenariusz 2 przez skill (CLI i skill zainstalowane na
thinkpadzie). Poprawki po dotychczasowych uwagach PO (sprawdzenie w instalatorze z przebiegu
„Build and Release”, artefakt `windows-installer`):

- suma kontrolna Deno na Windows (format `Get-FileHash`) — wypchnięte, CI zielone;
- okno za wysokie na Full HD przy skalowaniu 125–150% — rozmiar liczony z obszaru roboczego
  ekranu;
- nagłówek notatki sklejony w jedną linię w edytorach bez obsługi frontmattera (Notepad++
  z wtyczką Markdown) — pusta linia między polami; PO sprawdza w Notepad++ i w Obsidianie;
- błąd HTTP 403 przy pobieraniu (przeszedł dopiero za drugim razem) — jedna automatyczna
  ponowna próba i własny komunikat `forbidden`;
- lista Recent: przycisk „Clear”; deinstalator usuwa też ustawienia, Recent i logi (decyzja PO);
- większe menu `⋯`;
- „checksum mismatch” ffmpeg przy pierwszym uruchomieniu (trafienie w codzienną podmianę
  wydania `latest` FFmpeg-Builds) — pobieranie z niezmiennego `autobuild-*`; ucięte szczegóły
  błędu w oknie pierwszego uruchomienia — okno rośnie do treści;
- pasek przewijania widoczny zawsze — teraz tylko, gdy treść się nie mieści; „Save note” nie mówił,
  czy będzie transkrypt — etykieta zależna od wybranych napisów;
- przestoje w pobieraniu — przyczyna nieznana (log był pusty); log zapisuje teraz przerwy ≥ 15 s
  i komunikaty yt-dlp, do analizy przy następnym przestoju;
- „chińskie znaczki” w transkrypcie — błąd programu do odczytu, nie aplikacji (pliki są
  poprawnym UTF-8; w innym edytorze i w Obsidianie OK — potwierdził PO).

Uwagi PO → poprawki na `dev`; po akceptacji PR `dev` → `main` i tag `v2.0.0` (za zgodą PO).

## Backlog

- Wtyczka PO Token (`bgutil-ytdlp-pot-provider`) jako plan B na blokady YouTube.
- Playlisty / kolejka (dziś świadomie poza zakresem).
