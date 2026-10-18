# PRD — YouTube Downloader

## Problem

Użytkownik buduje w Obsidianie archiwum wiedzy. Ważne filmy z YouTube mają trafiać do vaulta
jako lokalne pliki MP4 — do obejrzenia i jako materiał do transkrypcji robionej osobnym
skillem. Wersja 1.x nie spełnia tego zadania: na Windows nie startuje, nie ma narzędzi do
sklejania obrazu z dźwiękiem, a zamrożony yt-dlp przestaje działać po każdej zmianie
po stronie YouTube.

## Użytkownicy

- **Właściciel archiwum** — pobiera zwykle jeden film na raz, kilka dziennie; Windows i Linux.
- **Claude Code** — wywołuje narzędzie z terminala (WSL/Linux) na prośbę użytkownika.
- Aplikacja jest publiczna (GitHub), więc interfejs po angielsku.

## Wymagania

1. Pobranie filmu jako MP4 zgodnego z odtwarzaczami (H.264 + AAC, domyślnie do 1080p);
   MP3 jako opcja.
2. Notatka `.md` obok pliku, ta sama nazwa: metadane we frontmatterze, osadzony film,
   opis, rozdziały, transkrypt z napisów YouTube (ręcznych przed automatycznymi) jako
   akapity ze znacznikami czasu-linkami do YouTube. Opcjonalnie plik `.srt`. Notatka czytelna
   także poza Obsidianem — w edytorze Markdown bez obsługi frontmattera metadane są osobnymi
   liniami, nie sklejonym nagłówkiem.
3. Folder docelowy wybierany przez użytkownika, domyślnie systemowe Pobrane, pamiętany.
4. Aplikacja sama pobiera i aktualizuje swoje narzędzia (yt-dlp, ffmpeg, Deno) — działa
   dalej po zmianach YouTube bez nowego wydania.
5. Zawsze widać, co się dzieje (pierwsze uruchomienie, aktualizacja, etapy pobierania);
   błędy opisane prostym językiem z podpowiedzią i szczegółami do skopiowania.
6. Ponowne pobranie rozpoznane po plikach w folderze (po notatce tego filmu albo po nazwie
   z `[ID]` — sam `Tytuł.mp4` bez notatki nie jest uznawany za ten film); istniejąca notatka
   nigdy nie jest nadpisywana.
7. Nieinteraktywne CLI z wynikiem JSON dla Claude Code; Claude zawsze pyta o folder.
8. Lista 3 ostatnich pobrań w oknie (zwarta — nie dominuje okna), z ręcznym czyszczeniem (pliki zostają).
9. Chwilowa odmowa YouTube (HTTP 403) jest ponawiana automatycznie raz, bez udziału
   użytkownika.
10. Deinstalacja na Windows usuwa wszystko, co aplikacja trzyma w profilu (narzędzia,
    ustawienia, lista ostatnich pobrań, logi); pobrane filmy i notatki zostają zawsze.
    Aktualizacja nową wersją zachowuje ustawienia.

11. Wygląd: jedna wyraźna główna akcja na ekranie (Download; w oknie pierwszego uruchomienia
    po błędzie — Retry) w kolorze akcentu kojarzącym się z YouTube, ale nie jego markowym
    (`#C62828`); błędy wyróżnione własnym tłem i ikoną, nie samym kolorem. Wklejony link
    sprawdza się sam. Makiety: `docs/superpowers/specs/2026-10-18-ui-polish-mockups/index.html`.

## Poza zakresem

Kolejka i playlisty, logowanie do YouTube, ręczny wybór klientów YouTube, przekodowywanie,
macOS, serwer MCP, tłumaczenia UI, serwisy inne niż YouTube, historia pobrań.

## Kryteria akceptacji

Siedem scenariuszy w `docs/superpowers/specs/2026-10-18-v2-design.md` §11.

## Źródła decyzji

Projekt v2 z decyzjami PO D1–D14: `docs/superpowers/specs/2026-10-18-v2-design.md`.
