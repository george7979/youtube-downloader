# Dołożenie samego `.srt` — projekt

Status: wdrożony na `dev`, sprawdzony przez PO na Windows; część wydania v2.0.0. Rozszerza `2026-10-19-transcript-languages-design.md`.

## Po co

Film (i zwykle notatka) są już w folderze, ale bez `Tytuł.<lang>.srt`. Użytkownik zaznacza
„Also save subtitles (.srt)” i klika Download. Dziś okno „Already downloaded” daje tylko
„Show file” i „Download again”, które pobiera cały film od nowa. Aplikacja ma zamiast tego
**dołożyć sam plik `.srt`**, pobierając tylko napisy.

## Zachowanie

### Kiedy proponujemy `.srt`

Warunki (wszystkie), w stanie dzisiejszego `already_exists` (film w żądanym formacie jest w
folderze; notatka główna jest albo zapis notatki jest wyłączony):
1. `.srt` jest zaznaczone (`save_srt`, CLI: `--srt`).
2. Wybrana ścieżka napisów istnieje (konkretny język, nie „None”).
3. `Tytuł.<lang>.srt` dla języka tej ścieżki jeszcze nie istnieje.
4. Nie da się dołożyć notatki językowej („Add transcript”) — tamta ścieżka i tak zapisuje
   `.srt`, gdy jest zaznaczone, więc dwa przyciski naraz się nie pojawiają.

### Okno

Dialog „Already downloaded” dostaje wypełniony przycisk **„Add subtitles (<lang>)”** na tym
samym miejscu co „Add transcript” (jeden wypełniony przycisk). Po kliknięciu: pobranie tylko
napisów, zapis `Tytuł.<lang>.srt`, status „Done. Saved Tytuł.<lang>.srt” plus ostrzeżenia.
Recent bez zmian; film i notatki nietknięte.

### CLI

`get --srt` dla filmu, który już jest, **sam** dopisuje brakujący `.srt` — przy warunkach 1–3;
warunek 4 dotyczy tylko okna (w CLI `.srt` dochodzi zawsze, chyba że ta sama komenda dokłada
notatkę językową, która zapisuje go razem z nią) (jak `--subs <lang>` dopisuje notatkę językową). JSON bez nowych pól:
`already_exists: false`, `media` = istniejący film, `note` = istniejąca notatka główna albo
`null`, `srt` = nowy plik, `transcript: "none"`. Bez spełnionych warunków — jak dziś.

### Napisów nie udało się pobrać

Brak pliku napisów albo napisy bez tekstu → `.srt` nie powstaje, `srt: null`, ostrzeżenie
„No subtitles were downloaded.”; okno: status „No subtitles added” plus ostrzeżenie.

## Czego nie wolno zepsuć

- Istniejący `.srt` i istniejące notatki nigdy nie są nadpisywane ani zmieniane.
- „Download again” (`force`) i „Add transcript” działają jak dotąd.
- Przypadek „film `Tytuł [ID]` bez notatki + `.srt`” działa jak dziś (już pobiera tylko napisy).

## Zostawione budującemu

Nazwy pól (`DownloadRequest`/`DownloadResult`), kształt warunku w serwisie, brzmienie
ostrzeżeń poza podanymi wyżej.
