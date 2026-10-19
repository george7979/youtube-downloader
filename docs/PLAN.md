# PLAN — YouTube Downloader

## Stan

- **Produkcja:** v2.0.0 (GitHub Releases, tag `v2.0.0`) — instalator Windows i paczka `.deb`.
- **`dev` = `main`** po wydaniu; nowe prace zaczynają się na `dev`.

## Etapy

### Etap 1 — v2.0.0: przebudowa (zamknięty — wydany)

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
- Zamknięcie: akceptacja PO na Windows i Linux/WSL (spec §11), PR `dev` → `main`, tag
  `v2.0.0` i wydanie na GitHubie (stary lekki tag `v2.0.0` z 2025 usunięty).

## Bieżący krok

Brak — v2.0.0 wydana. Kolejna praca: pozycja z backlogu albo uwaga użytkownika, na `dev`.

## Backlog

- Podpis cyfrowy instalatora i `.exe` na Windows — certyfikat czeka na aktywację po stronie PO
  (link w mailu PO). Potem: podpis w budowaniu, README bez uwagi „not digitally signed”, wydanie
  v2.0.1.
- Język dokumentów projektowych — otwarte, PO nie jest przekonany. Stała zasada: dokumentacja dla
  użytkownika (README, BUILDING, skill, interfejs) po angielsku. Rozważany wariant: CKM (PRD, PLAN,
  TECH) po angielsku, robocze pliki `docs/superpowers/` po polsku. Do decyzji PO, nie przed podpisem.
- Wtyczka PO Token (`bgutil-ytdlp-pot-provider`) jako plan B na blokady YouTube.
- Przestoje YouTube co ~10 MB (TECH → Known Issues): zbadać przy kolejnym wystąpieniu z `-v`.
- Playlisty / kolejka (dziś świadomie poza zakresem).
