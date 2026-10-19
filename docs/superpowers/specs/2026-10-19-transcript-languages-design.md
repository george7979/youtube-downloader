# Kolejne języki transkrypcji — projekt

Status: wdrożony na `dev`, czeka na testy PO; część wydania v2.0.0.

## Po co

Film jest już w folderze razem z notatką `Tytuł.md` z transkrypcją w jednym języku (np. EN).
Użytkownik wybiera z listy napisy w innym języku (np. PL) i klika Download. Dziś aplikacja
pyta „Already downloaded”, a „Download again” pobiera cały film od nowa, napisów nie pobiera
wcale (tryb `media_only`), notatki nie rusza — wybór języka przepada bez śladu, a użytkownik
płaci za ponowne pobranie filmu. Aplikacja ma zamiast tego **dołożyć notatkę w nowym języku**,
nie pobierając filmu.

## Cele

- Dodatkowy język = osobna, **pełna notatka** `Tytuł.<lang>.md` (decyzja PO): ten sam
  frontmatter co notatka główna (z `transcript: youtube-<kind>-<lang>`), osadzony film, opis,
  rozdziały, transkrypcja w tym języku — wynik tej samej funkcji `render_note`.
- Pobierane są **tylko napisy** (`--skip-download`), film zostaje, jak jest.
- Notatka główna `Tytuł.md` i istniejące notatki językowe nigdy nie są nadpisywane ani zmieniane.
- `.srt`, jeśli zaznaczone, powstaje jak dziś: `Tytuł.<lang>.srt`.

## Zakres poza projektem (non-goals)

- „Download again” działa jak dziś (pobiera film ponownie, notatki nie rusza) — poprawka
  „nie pobieraj filmu na darmo” to osobna sprawa, poza tym projektem.
- Brak scalania języków w jednej notatce, brak dopisywania do istniejącej notatki.
- Brak listy „jakie języki już mam” w oknie poza tym, co wynika z reguły niżej.
- Recent bez zmian: dołożenie notatki językowej nie dodaje wiersza (to nadal ten sam plik
  wideo). *(wybór Claude'a)*

## Czego nie wolno zepsuć (anti-goals)

- Notatka językowa nie może zostać uznana za notatkę główną — ani przy rozpoznawaniu „już
  pobrane”, ani przy planowaniu nazw (inaczej `base` zrobiłby się `Tytuł.pl`, a aplikacja
  szukałaby `Tytuł.pl.mp4`). Dotyczy też sytuacji, gdy użytkownik usunął `Tytuł.md`, a
  `Tytuł.pl.md` został.
- Zasada „istniejąca notatka nigdy nie jest nadpisywana” obowiązuje także notatki językowe.
- Przypadki z `Tytuł [ID]` (kolizja tytułów) działają tak samo: `Tytuł [ID].pl.md`.

### Notatka główna usunięta, notatka językowa została *(wybór Claude'a)*

W folderze są `Tytuł.mp4` i `Tytuł.pl.md`, nie ma `Tytuł.md`. Notatka językowa (jej `url:`)
**identyfikuje film**, ale nie jest notatką główną: `base` zostaje `Tytuł` (bez `.pl`), film
jest „już tutaj”, a pobranie idzie istniejącą ścieżką „tylko notatka” — powstaje nowe
`Tytuł.md`, film nie jest pobierany ponownie, `Tytuł.pl.md` zostaje nietknięte. Bez tego film
trafiłby drugi raz do `Tytuł [ID].mp4` — dokładnie to, czego projekt ma unikać.

## Zachowanie

### Kiedy aplikacja dokłada język

Warunki (wszystkie):
1. W folderze jest film w żądanym formacie i notatka główna tego filmu (stan dzisiejszego
   `already_exists`).
2. Wybrana ścieżka napisów istnieje (konkretny język, nie „None”).
3. Język wybranej ścieżki różni się od języka transkrypcji notatki głównej (z jej pola
   `transcript:`; `none` = notatka bez transkrypcji, więc każdy język się różni).
   Porównujemy **sam kod języka** — `en (manual)` przy notatce `youtube-auto-en` to ten sam
   język, przycisku nie ma. *(wybór Claude'a)*
4. `Tytuł.<lang>.md` jeszcze nie istnieje.
5. Zapis notatki jest włączony (okno: „Save note…”, CLI: bez `--no-note`). Gdy notatka jest
   wyłączona, zachowanie jest dzisiejsze — także przy zaznaczonym `.srt`. *(wybór Claude'a:
   „Add transcript” oznacza notatkę; wariant „tylko .srt” wymagałby drugiej wersji
   przycisku, komunikatów i JSON-u)*

Szczegóły warunków *(wybory Claude'a)*:
- Kody języka porównujemy dokładnie, tak jak przychodzą ze ścieżki (`en-US` ≠ `en`).
- Notatka główna bez pola `transcript:` (użytkownik je usunął) = język nieznany → przycisku nie
  ma.
- MP4 i MP3 dzielą notatkę główną; notatka językowa osadza plik w żądanym formacie.

Gdy któryś warunek nie jest spełniony, zachowanie jest dzisiejsze.

### Okno (GUI)

Dialog „Already downloaded” dostaje trzeci przycisk, gdy warunki są spełnione:

```
Already downloaded
Video title
The video and its note (transcript: en) are already in this folder.

[ Add transcript (pl) ]  ( Show file )  ( Download again )   Cancel
```

- „Add transcript (pl)” jest jedynym wypełnionym przyciskiem (zasada jednego wypełnionego
  przycisku z makiet UI); bez niego dialog wygląda jak dziś (bez wypełnionego przycisku).
- Linia opisu podaje język transkrypcji notatki głównej, żeby było widać, co już jest.
  *(wybór Claude'a; dokładne brzmienie — budujący)*
- Po kliknięciu: postęp jak przy zwykłym pobraniu („Downloading subtitles”, „Writing note…”),
  na końcu status „Done. Saved Tytuł.pl.md” plus ostrzeżenia. Cancel działa.
- Język zapamiętuje się jak przy zwykłym pobraniu (`subs_lang`).

### CLI

- `get --subs <lang>` dla filmu, który już jest z notatką główną, przy spełnionych warunkach
  **sam** dokłada notatkę językową (CLI jest nieinteraktywne; użytkownik jawnie poprosił o
  język). *(wybór Claude'a)*
- Wynik JSON bez nowych pól: `already_exists: false` (coś powstało), `media` = istniejący
  plik, `note` = ścieżka nowej notatki językowej, `transcript` = `youtube-<kind>-<lang>`,
  `srt` jak dziś.
- Bez `--subs` (reguła domyślna) albo gdy warunki nie są spełnione — dzisiejsze
  `already_exists: true`.
- `--force` działa jak dziś.

### Gdy napisów nie udało się pobrać

Jeśli YouTube nie odda pliku napisów, notatka językowa **nie powstaje** (pusta notatka
językowa nie ma sensu); użytkownik dostaje ostrzeżenie jak dziś („No subtitles were
downloaded.”), a wynik jest „nic nie zapisano”. *(wybór Claude'a; dokładna forma wyniku —
budujący)*

## Ograniczenia

- Reguły projektu z `CLAUDE.md`: `core` bez Tk, ścieżki tylko z `paths.py`, tekst UI po
  angielsku, testy bez sieci (fixtury z prawdziwych odpowiedzi yt-dlp).
- Silnik: tryb „tylko napisy” już istnieje (`note_only` → `--skip-download` + `--write-subs`/
  `--write-auto-subs`) — do wykorzystania.
- README → „How it works” (sekcje „The note” i „File names and downloading again”) i skill
  opisują nowe zachowanie w tym samym commicie; PRD (wymaganie 6) i TECH też.

## Zostawione budującemu

- Jak rozpoznawać notatkę językową (np. nazwa `<base>.<lang>.md` obok notatki głównej
  i/lub cecha we frontmatterze) — byle spełniała anti-goals.
- Kształt zmian w `NamePlan` / `DownloadResult` / `DownloadRequest` (np. nowe pole w wyniku
  „można dołożyć język X” i flaga żądania „tylko notatka językowa”).
- Brzmienie tekstów w oknie i w CLI (po angielsku).
