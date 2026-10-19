# TECH — YouTube Downloader

Stan faktyczny kodu. Co i dlaczego: `PRD.md`; kiedy i na jakim etapie: `PLAN.md`; decyzje
projektowe z uzasadnieniem: `docs/superpowers/specs/2026-10-18-v2-design.md`; budowanie
paczek i wydania: `BUILDING.md`. Logikę działania opisaną dla użytkownika (narzędzia i
aktualizacje, wybór napisów, transkrypt, nazwy i ponowne pobranie) trzyma `README.md` → „How it
works” — przy zmianie tych zasad w kodzie aktualizuj oba dokumenty.

## Architektura

Program to pakiet `ytdownloader/` w trzech warstwach:

| Warstwa | Rola | Ograniczenie |
|---|---|---|
| `core/` | cała logika: narzędzia, silnik yt-dlp, napisy, notatka, nazwy, ustawienia | **nie importuje `tkinter` ani `customtkinter`** |
| `gui/` | okno CustomTkinter | tylko wywołuje `core.service.Service` i `ToolManager` |
| `cli.py` | podpolecenia `get`, `info`, `tools` z wynikiem JSON | te same wywołania co GUI |

`__main__.main` kieruje: pierwszy argument `get`/`info`/`tools`/`--help` → `cli.main`, w
przeciwnym razie `gui.run`. Gdy podpolecenie CLI trafi do okienkowego `.exe` (brak
`sys.stdout`), pokazuje okno komunikatu „The command line is available on Linux/WSL…” i
kończy kodem 2. `launcher.py` to wejście dla PyInstallera i `python launcher.py`.
Zależności uruchomieniowe: `customtkinter`, `pillow`, `platformdirs`. **Pakietu `yt-dlp` w
Pythonie nie ma nigdzie** — silnikiem jest zewnętrzny plik wykonywalny.

### Przepływ zdarzeń

`Service.download(req, info, sink, cancel, remembered_lang)` jest jedynym punktem wejścia dla
GUI i CLI: sprawdza narzędzia i folder, planuje nazwy (`naming.plan_names`), wybiera ścieżkę
napisów (`probe.pick_track`), uruchamia silnik, potem zapisuje `.srt` i notatkę. Postęp
wychodzi przez `sink(Status | Progress)`; anulowanie przez `threading.Event`.

```
UI/CLI --Service.download--> engine.download_args --> Runner.run (yt-dlp, nowa sesja/grupa procesów)
                                  ^                         | linie stdout+stderr
                                  |                         v
                          ProgressParser.feed  <-- on_line (wątek wywołujący)
                                  | Status / Progress / FileDone
                                  v
                               sink(...)  --> GUI: UiQueue.post / CLI: stderr
```

### Wątki

- **GUI:** praca w tle przez `UiQueue.run_bg(work, on_ok, on_err)`; wyniki wracają do pętli Tk
  przez kolejkę opróżnianą co 80 ms (`after`). Widżetów nie dotyka nic poza wątkiem Tk.
  `Check`, pobieranie, aktualizacje i miniatura (tylko `http`/`https`, najwyżej 5 MB) działają
  w wątkach demonów; stare wyniki są odrzucane (numer kolejny sprawdzenia, tożsamość
  miniatury). Pobierające żądanie i `info` są przechwycone przy starcie pobierania, więc
  kolejne `Check` go nie psuje. Zamknięcie okna anuluje pobieranie i czeka na sprzątnięcie
  (`DOWNLOAD_STOP_TIMEOUT`).
- **Pierwsze uruchomienie** ma własny korzeń Tk (`FirstRunWindow`), niszczony przed oknem
  głównym — dwa żywe korzenie CTk rozdzielałyby stan Tk.
- **CLI:** `get` działa w wątku roboczym, główny wątek czeka z `join(0.2)`; Ctrl+C ustawia
  `cancel`, czeka na sprzątanie i kończy kodem 130.
- **Runner:** dwa wątki czytają stdout i stderr do jednej kolejki; `on_line` wywoływany jest
  szeregowo w wątku wywołującym. Trzeci wątek pilnuje `cancel` i zabija drzewo procesów —
  tylko gdy proces jeszcze działa. Kod `-1` („anulowano”) zapada wyłącznie po takim
  zabiciu: Cancel wciśnięty, gdy yt-dlp właśnie skończył, zostawia udane pobranie.

### Rozmiar okna

CustomTkinter mnoży szerokość i wysokość z `geometry()` przez skalowanie Windows (150% →
600 px to 900 px fizycznych), a pozycję `+x+y` podaje w pikselach fizycznych.
`gui/placement.py` liczy rozmiar startowy z obszaru roboczego ekranu głównego (Windows:
`SystemParametersInfoW(SPI_GETWORKAREA)`, czyli bez paska zadań; Linux: ekran minus 48 px na
panele): preferowane 540×600 logicznych (cały układ w trakcie pobierania: karta filmu, postęp,
trzy ostatnie pobrania), wysokość przycięta tak, żeby okno z paskiem tytułu
(40 px logicznych) się zmieściło, okno wyśrodkowane. Minimum 480×420 maleje razem z oknem.
Treść jest w `CTkScrollableFrame`, więc niższe okno przewija się zamiast ucinać; pasek
przewijania jest ukryty, dopóki wszystko się mieści (`_on_body_scroll`). Okno
pierwszego uruchomienia startuje tak samo (480×360) i rośnie (`_fit_content`, nigdy nie maleje),
gdy panel błędu się pojawi albo rozwinie szczegóły — do granicy obszaru roboczego.

### Wygląd i zachowanie okna

- **Motyw** (`gui/theme.py`): `apply_theme()` nadpisuje domyślny niebieski CustomTkinter, zanim
  powstanie jakikolwiek widżet (woła je `MainWindow` i `FirstRunWindow`). Akcent `#C62828`
  (przycisk główny, pola wyboru, postęp), listy i przełącznik MP4/MP3 neutralne. Kolory to pary
  (jasny, ciemny), bo okno idzie za trybem systemu.
- **Hierarchia:** na ekranie jeden wypełniony przycisk — Download (w oknie pierwszego
  uruchomienia po błędzie: Retry). Wyjątek: dialog „Already downloaded” może mieć jeden
  wypełniony przycisk, „Add transcript (<lang>)” (tylko gdy da się dodać język); Download
  okna głównego jest wtedy wyłączony, więc aktywny jest zawsze jeden wypełniony przycisk.
  Drugorzędne obrysowane (`OUTLINE_BUTTON`: Check, Change,
  Cancel, Quit, Update engine, pozostałe przyciski dialogu „Already downloaded”, Close w About),
  pomocnicze tekstowe (`TEXT_BUTTON`: Show file, Clear, ⋯, Show details, Copy). Wyłączony
  CTkButton zachowuje `fg_color`, więc `set_primary_enabled` przełącza go na wyciszony kolor.
- **Układ:** folder to wiersz „Save to <ścieżka> (Change)” na dole opcji; kliknięcie ścieżki
  otwiera folder. Cancel i pasek postępu są spakowane tylko w trakcie pobierania
  (`_sync_controls`), linia stanu tylko gdy ma tekst (`set_status`), panel błędu ma własne tło,
  obramowanie i ikonę (`ERROR_BG`, `ERROR_BORDER`).
- **Auto-Check:** `<<Paste>>` w polu linku woła `_check_pasted` przez `after_idle` (wiązanie
  widżetu działa przed wstawieniem tekstu przez klasę `Entry`); sprawdza tylko tekst, z którego
  `parse_video_id` wyciąga ID, i pomija film już pokazany w karcie.
- **Pierwsze uruchomienie:** nagłówek „Setting up” z jednym zdaniem; pasek narzędzia, które
  jeszcze czeka, nie ma wypełnienia (`progress_color` = kolor tła paska — przy 0 CTk rysuje
  okrągłą kropkę akcentu).

## Moduły `gui/`

| Moduł | Odpowiedzialność |
|---|---|
| `__init__.py` | `run()`: logi, `CrashReporter` (hooki wyjątków → okno ze ścieżką logu), okno pierwszego uruchomienia, potem główne; przy zamknięciu czeka do 5 s na anulowane pobieranie |
| `app.py` | `MainWindow`: link → karta filmu → opcje (z „Save to”) → Download → Recent → stopka z menu `⋯` |
| `first_run.py` | `FirstRunWindow`: instalacja narzędzi z paskiem na narzędzie, Retry, rośnie do panelu błędu |
| `widgets.py` | `ErrorPanel`, dialog „Already downloaded”, About, `set_window_icon` |
| `theme.py` | kolory i style przycisków, `apply_theme`, `set_primary_enabled` |
| `placement.py` | rozmiar i położenie okna z obszaru roboczego ekranu |
| `worker.py` | `UiQueue`: praca w tle, wyniki do wątku Tk przez `after` |
| `system.py` | otwarcie folderu, pokazanie pliku w Eksploratorze |

## Moduły `core/`

| Moduł | Odpowiedzialność |
|---|---|
| `paths.py` | **jedyne** źródło lokalizacji: konfiguracja, dane, logi, narzędzia, Pobrane, katalog roboczy yt-dlp, zasoby (`sys._MEIPASS` w paczce) |
| `settings.py` | `settings.json` (folder, tryb, jakość, język napisów, notatka/srt, czas ostatniej aktualizacji) i lista 3 ostatnich pobrań (`MAX_RECENT`, jeden wpis na plik — `add_recent` usuwa duplikat po `media_path`, nie po ID filmu; okno dopisuje format z rozszerzenia); walidacja typów, zapis atomowy; `resolve_output_dir` wraca do Pobrane z komunikatem, gdy zapisany folder zniknął (pusty `output_dir` = nie wybrano). Jakość to pułap: okno domyślnie wybiera najwyższą wysokość filmu ≤ zapisanej i zapisuje jakość tylko wtedy, gdy użytkownik wybrał inną niż ta domyślna (film z maks. 720p nie obniża ustawienia 1080) |
| `logsetup.py` | rotujący `app.log` (1 MB × 3), a gdy jest `stderr` — także na konsolę. `Service` loguje na INFO każde uruchomienie silnika (adres, tryb, jakość, próba), linie yt-dlp poza postępem (`--print` wycisza resztę, więc to ostrzeżenia, błędy, `CODEC`, `FILE`), każdą przerwę bez wyjścia ≥ 15 s (`STALL_LOG_S`) z linią sprzed niej oraz kod wyjścia i czas |
| `urls.py` | ID filmu z linku (`watch`, `youtu.be`, `shorts`, `embed`, `live`); inne → `invalid_url`; playlisty ignorowane |
| `errors.py` | `FriendlyError(code, message, hint, details)`; tabela 10 kodów (niżej); `classify(stderr)` dopasowuje podciągi (kolejność ma znaczenie) |
| `models.py` | typy danych wspólne dla warstw (`VideoInfo`, `DownloadRequest`, `DownloadResult`, `Status`, `Progress`) |
| `tools.py` | `ToolManager`: pobranie, weryfikacja SHA-256, atomowa instalacja i aktualizacja yt-dlp / ffmpeg / Deno |
| `engine.py` | argumenty yt-dlp (`base_args`, `probe_args`, `download_args`), `ProgressParser`, `Runner` (zabija całe drzewo procesów) |
| `probe.py` | `yt-dlp -J` → `VideoInfo`; `pick_track` — wybór napisów wg reguły: wskazany język, zapamiętany, oryginalny ręczny, pierwszy ręczny, automatyczny |
| `subtitles.py` | VTT → cue; odszumianie napisów automatycznych (powtarzane linie „przewijanego” tekstu); akapity ~45 s (twardo 90 s, koniec na kropce, granice rozdziałów); SRT |
| `naming.py` | bezpieczna nazwa pliku (znaki Windows, nazwy zastrzeżone, do 150 znaków i 200 bajtów UTF-8); rozpoznanie istniejących plików filmu; `note_fields` (frontmatter notatki), `is_language_note` (pole `main_note:`), `NamePlan.language_note(lang)` → `<base>.<lang>.md` |
| `note.py` | notatka Markdown: frontmatter z pustą linią między polami (poprawny YAML; podgląd bez obsługi frontmattera pokazuje pola jako osobne akapity między kreskami, a nie jako jeden nagłówek), osadzone wideo, opis, rozdziały, transkrypt ze znacznikami `[mm:ss](https://youtu.be/ID?t=N)` (przy filmach ≥ 1 h `h:mm:ss`); tekst od autora filmu (tytuł w nagłówku, opis, tytuły rozdziałów, transkrypt) zostaje zwykłym tekstem: `neutralize_markdown` ucieka `\`, `[`, `]`, `<`, grawis i `~` oraz `#` na początku słowa — bez tagów, zdalnych obrazków (ujawniłyby IP przy otwarciu notatki), zamaskowanych łączy, HTML i bloków kodu (Dataview); gołe adresy zostają klikalne |
| `service.py` | scala wszystko; silnikowi podaje kanoniczny `info.url`, nie wklejony adres; sprząta pliki częściowe po błędzie i anulowaniu; przy filmie z notatką ocenia, czy można dołożyć notatkę językową (`DownloadResult.addable_lang`, `note_lang`), a na `DownloadRequest.add_transcript` pobiera same napisy i ją zapisuje |

### Kody błędów

`classify` sprawdza wzorce (podciągi, bez wielkości liter) w tej kolejności; pierwszy trafiony
wygrywa. Wiadomość i wskazówka idą do panelu błędu w oknie i do `error` w JSON-ie CLI, więc
nie odwołują się do elementów okna.

| Kod | Kiedy |
|---|---|
| `write_failed` | `permission denied`, `no space left on device`, `[errno 28]`, `[errno 13]`, `read-only file system`; także błąd zapisu notatki/`.srt` i niezapisywalny folder |
| `bot_check` | `not a bot` |
| `rate_limit` | `this content isn't available, try again later`, `http error 429` |
| `forbidden` | `http error 403` — YouTube odrzucił adres strumienia; `Service` sam ponawia uruchomienie silnika raz (`FORBIDDEN_RETRIES`, nowy przebieg dostaje nowe adresy), z komunikatem „YouTube refused the stream — retrying…”; kod trafia do użytkownika dopiero po drugiej porażce |
| `engine_outdated` | `nsig extraction failed`, `signature extraction failed`, `unable to extract`, `requested format is not available` — typowe objawy zmiany po stronie YouTube |
| `unavailable` | prywatny, usunięty, blokada regionu, wiek, tylko dla członków |
| `network` | `unable to download webpage`, błędy DNS i połączenia, `timed out`, `urlopen error`; także nieudane pobranie narzędzi |
| `invalid_url` | link nie jest filmem YouTube (`urls.py`) |
| `tools_missing` | brak narzędzi przy pobieraniu; zła suma kontrolna, uszkodzone archiwum, brak pliku w archiwum |
| `cancelled` | Cancel / Ctrl+C |
| `unknown` | wszystko inne; `details` = ostatnie 40 linii stderr albo traceback |

Okno przy `bot_check`, `forbidden` i `engine_outdated` pokazuje w panelu błędu przycisk „Update engine”
(to samo co w menu `⋯`).

## Narzędzia zewnętrzne

| Narzędzie | Źródło (`releases/latest`) | Suma kontrolna |
|---|---|---|
| yt-dlp | `github.com/yt-dlp/yt-dlp` — `yt-dlp.exe` / `yt-dlp_linux` (kanał stabilny) | `SHA2-256SUMS` |
| ffmpeg (Windows) | `yt-dlp/FFmpeg-Builds`, najnowsze kompletne wydanie `autobuild-*` — `ffmpeg-N-…-win64-gpl-shared.zip` (ok. 90 MB; cały katalog `bin/`) | `checksums.sha256` z tego samego wydania |
| ffmpeg (Linux) | `ffmpeg` i `ffprobe` z `PATH`, jeśli oba są; inaczej `ffmpeg-N-…-linux64-gpl.tar.xz` z `autobuild-*` (149 MB; `bin/ffmpeg`, `bin/ffprobe`) | `checksums.sha256` z tego samego wydania |
| Deno | `github.com/denoland/deno` — `deno-x86_64-{pc-windows-msvc\|unknown-linux-gnu}.zip` (min. **2.3.0**) | `<plik>.sha256sum` — Linux: `<hex>  <nazwa>`, Windows: format PowerShell `Get-FileHash` (`Hash : …` / `Path : …`) |

FFmpeg-Builds co dzień przebudowuje wydanie `latest`, podmieniając pliki w miejscu — przez kilka
minut archiwum i `checksums.sha256` pochodzą z różnych kompilacji (404, „checksum mismatch”).
Dlatego `ToolManager._resolve` pyta API GitHuba (`/releases?per_page=10`) o najnowsze wydanie
`autobuild-*` (niezmienne), w którym archiwum pasujące do `ffmpeg-N-<nr>-g<hash><przyrostek>`
i plik sum mają stan `uploaded`. Gdy API zawiedzie (offline, limit 60 zapytań/h, inna
odpowiedź), instalacja idzie ze starych adresów `latest`. yt-dlp i Deno mają niezmienne
wydania pod tagiem, więc pobierają się przez `releases/latest`.

Pliki sum to linie `<sha256>  <nazwa-zasobu>`. Deno jest potrzebny yt-dlp do rozwiązywania
wyzwań YouTube (`--js-runtimes deno:<ścieżka>`).

### Instalacja

`ToolManager.install` pobiera archiwum do `tools/.download/`, sprawdza SHA-256 względem pliku
sum, rozpakowuje do `tools/.staging/<narzędzie>/` (spłaszczone; odrzuca ścieżki wychodzące
poza katalog, także z literą dysku), nadaje `0755` (`zipfile` gubi bit wykonywalności) i
dopiero wtedy podmienia `tools/<narzędzie>/` przez `os.replace` (poprzednia wersja jest
odtwarzana, gdy podmiana się nie uda). Błąd sieci przy pobieraniu archiwum albo pliku sum
(`URLError`, przekroczony czas, zerwane połączenie, inny `OSError` z pobierania) → `network`,
więc pierwsze uruchomienie offline pokazuje „No connection…” i przycisk Retry; zła suma,
uszkodzone archiwum albo brak wymaganego pliku → `tools_missing`. W obu przypadkach pliki
częściowe i katalog roboczy są sprzątane. `missing()` uznaje narzędzie za brakujące, gdy brak
pliku yt-dlp, gdy dołączony ffmpeg nie ma obok siebie `ffprobe` (instalacja też wymaga obu),
albo gdy Deno nie odpowiada wersją ≥ 2.3.0.

### Polityka aktualizacji

- **Kanał stabilny** yt-dlp (`-U` bez przełączania na nightly).
- **Co najwyżej raz na 24 h** (`UPDATE_CHECK_INTERVAL`), przy starcie GUI, w tle:
  `yt-dlp -U`, wynik w stopce („updated” / „up to date” / „update failed”). Czas ostatniego
  sprawdzenia siedzi w `settings.json` i jest zapisywany **tylko po udanej aktualizacji** —
  po porażce (np. offline) następny start próbuje znowu.
- `update_ytdlp()` zwraca `(stara, nowa)`; gdy `-U` nie da się uruchomić albo kończy się
  kodem ≠ 0, zwraca `(stara, None)` — to jest „update failed”, nigdy „up to date”.
- **Przycisk „Update engine”** (menu `⋯` oraz panel błędu przy `bot_check`/`forbidden`/`engine_outdated`):
  `update_all` — `yt-dlp -U`; gdy yt-dlp nie odpowiada na `--version` przed albo po `-U`,
  instaluje go od nowa ścieżką z sumą kontrolną; potem ponowna instalacja ffmpeg (poza
  systemowym) i Deno. Zablokowany w trakcie pobierania.
- **CLI:** `get` i `info` po doinstalowaniu brakujących narzędzi robią tę samą dobową
  aktualizację co okno (komunikaty na stderr, wspólny `last_update_check` w `settings.json`);
  porażka to tylko ostrzeżenie na stderr i praca na obecnej wersji. `tools --update` wywołuje
  `update_all`; `updated.to` = `null` oznacza nieudaną aktualizację yt-dlp. Czas sprawdzenia
  zapisują tylko udane aktualizacje.

## Lokalizacje na dysku

| Co | Windows | Linux |
|---|---|---|
| ustawienia `settings.json` | `%APPDATA%\YouTube Downloader\` | `~/.config/youtube-downloader/` |
| narzędzia `tools/{yt-dlp,ffmpeg,deno}/` | `%LOCALAPPDATA%\YouTube Downloader\tools\` | `~/.local/share/youtube-downloader/tools/` |
| log `app.log` | `%LOCALAPPDATA%\YouTube Downloader\Logs\` | `~/.local/state/youtube-downloader/log/` |
| katalog roboczy yt-dlp (pliki próbne, kasowane przez yt-dlp) | `%LOCALAPPDATA%\YouTube Downloader\Cache\work\` | `~/.cache/youtube-downloader/work/` |
| domyślny folder pobierania | systemowy „Pobrane” | `~/Downloads` (wg XDG) |

Deinstalator Windows usuwa całe `%LOCALAPPDATA%\YouTube Downloader\` (narzędzia, logi) i
`%APPDATA%\YouTube Downloader\` (ustawienia, lista Recent); instalacja nowej wersji na starą
deinstalatora nie uruchamia, więc aktualizacja ustawienia zachowuje. Pobrane pliki leżą w
folderze wybranym przez użytkownika i nie są ruszane. `.deb` niczego w profilu nie
zakłada ani nie usuwa. CLI na Linuksie/WSL ma własną konfigurację, osobną od Windows; z
`settings.json` czyta i zapisuje wyłącznie `last_update_check` (wspólny z oknem na tym samym
systemie) — folder zawsze podaje `--out`.

## yt-dlp — fakty, które mają znaczenie

Zweryfikowane na prawdziwych uruchomieniach (fixtury w `tests/fixtures/`).

- **Postęp pobierania idzie na stdout, postęp postprocesorów (scalanie, MP3) na stderr.**
  `Runner` karmi `on_line` liniami obu strumieni; stderr jest też zachowany dla
  `classify`. Bez tego status „Merging…” nigdy się nie pojawi.
- **`--print` wycisza yt-dlp** — zawsze dodajemy `--progress` (i `--newline`).
- **`--force-ipv4` zawsze** (w `COMMON`): YouTube potrafi oznaczyć adres IPv6 („Sign in to
  confirm you're not a bot” dla każdego filmu), podczas gdy IPv4 tej samej maszyny działa —
  ten sam `yt-dlp.exe` i to samo łącze: bez `-4` blokada, z `-4` pobiera. Świadomie: sieć bez
  IPv4 nie połączy się z YouTube (błąd `network`).
- **Własne szablony postępu:** `--progress-template "download:YTDL %(progress)j"` i
  `"postprocess:YTPP %(progress)j"`; wartości z `--print`: `before_dl:CODEC %(vcodec)s`
  (ostrzeżenie „No H.264…”, gdy kodek nie zaczyna się od `avc1`) i `after_move:FILE
  %(filepath)s` (ścieżka gotowego pliku).
- **Format MP4:** `-S res:<q>,vcodec:h264,acodec:m4a` — **kolejność kluczy ma znaczenie**:
  najpierw wysokość, potem kodek; odwrotnie yt-dlp wybrałby niższą rozdzielczość dla H.264.
  Do tego `--merge-output-format mp4`. Gdy H.264 przy danej jakości nie istnieje (np. 4K),
  yt-dlp bierze VP9/AV1 i app to sygnalizuje. MP3: `-f bestaudio -x --audio-format mp3
  --audio-quality 192K`.
- **`%` w `-o`:** nazwa jest naszym literałem, więc `%` zamieniamy na `%%`; własne `-o`
  podajemy zawsze (yt-dlp zamieniłby `?` na `？`).
- **`--encoding utf-8`** — zamrożony `yt-dlp.exe` pisałby w rurę w stronie kodowej ANSI i
  psuł ścieżki z polskimi znakami. Subprocesy dostają też `PYTHONUTF8=1`, a czytamy je
  `encoding="utf-8", errors="replace"`.
- **`--` przed URL** — adres zaczynający się od `-` nigdy nie stanie się opcją.
- **Katalog roboczy = `paths.work_dir()` (prywatny katalog cache użytkownika, nie wspólny
  `/tmp` — Deno czyta konfigurację z katalogu roboczego).** Gdy YouTube wymusza
  SABR, yt-dlp sprawdza formaty HLS próbnym pobraniem do pliku `tmp*.tmp` w bieżącym katalogu.
  Aplikacja ze skrótu w menu Start ma bieżący katalog w Program Files, gdzie zapis jest
  zabroniony — yt-dlp wisiał wtedy na „Testing format” bez końca („Fetching video info…”).
  Dotyczy tylko części filmów, dlatego zwykłe pobrania działały.
- **Zawsze** `--ignore-config --no-playlist --no-mtime`; `stdin=DEVNULL`; na Windows
  `CREATE_NO_WINDOW`, na POSIX proces w nowej sesji (`killpg` zabija całe drzewo; Windows:
  `taskkill /F /T`).
- **Napisy automatyczne:** klucze `<lang>-orig` (oryginalny język mowy) w
  `automatic_captions`; bez nich tylko język filmu. Sama tablica `automatic_captions` ma
  setki tłumaczeń — nigdy nie oferujemy ich jako napisów. Pobieranie:
  `--write-subs` / `--write-auto-subs --sub-langs <klucz> --sub-format vtt`; plik
  `<base>.<klucz>.vtt` jest po przetworzeniu usuwany.
- **Pobranie przez `--skip-download`** służy do zapisania samej notatki, gdy plik wideo już
  jest.

## Nazwy i rozpoznawanie istniejących plików

Film jest „ten sam” tylko wtedy, gdy zgadza się ID: z pola `url:` frontmattera notatki `.md`
albo z końcówki nazwy pliku `… [ID].<format>`. Liczy się tylko **żądany format**: MP4 nie
czyni MP3 „już pobranym” (i odwrotnie). Stany: [plik + notatka] → `already_exists`;
[notatka bez pliku] → dociąga plik, notatki nie rusza; [plik `[ID]` bez notatki] → sama
notatka; [plik `[ID]` bez notatki, notatka niechciana i bez `.srt` do zapisania] →
`already_exists` bez uruchamiania yt-dlp (`note` = `null`).
Kolizja nazwy z innym filmem → oba pliki dostają ` [ID]`. Istniejąca notatka nigdy nie jest
nadpisywana ani kasowana (także przy sprzątaniu po błędzie); zapis notatki idzie przez
`write_failed` i usuwa niedokończony plik, żeby nie został uznany za „istniejącą”.

**Notatki językowe.** `<base>.<lang>.md` to pełna notatka z `render_note` (ten sam
frontmatter, `transcript: youtube-<kind>-<lang>`, osadzony plik w żądanym formacie) z dodatkowym
polem `main_note: "[[<base>]]"`. Notatka z polem `main_note:` nigdy nie jest notatką główną: ani
przy `already_exists`, ani przy wyznaczaniu `base`. Gdy została tylko ona (użytkownik usunął
`Tytuł.md`), `base` to jej nazwa bez ostatniego sufiksu, film jest „już tutaj”, a pobranie
idzie ścieżką „sama notatka” — powstaje nowe `Tytuł.md`. Przy [plik + notatka główna], bez
`force`, `service` bierze ścieżkę z `pick_track` i język notatki głównej z jej pola
`transcript:` (`youtube-<kind>-<lang>` → `<lang>`, `none` → bez języka, brak pola lub inna
wartość → język nieznany). Notatkę językową można dołożyć (`addable_lang`), gdy zapis notatki
jest włączony, ścieżka istnieje, język notatki głównej jest znany, kody języka różnią się
(porównanie dokładne: `en-US` ≠ `en`; ręczne i automatyczne napisy jednego języka to ten sam
język) i `<base>.<lang>.md` jeszcze nie istnieje. Bez `add_transcript` wynik to dzisiejsze
`already_exists` z `addable_lang` i `note_lang`; z nim silnik idzie z `--skip-download` dla tej
ścieżki, a notatka językowa powstaje tylko z napisów dających choć jeden akapit — bez nich (brak VTT albo pusty VTT) nic nie jest zapisywane
(`note` = `null`, `transcript` = `none`, ostrzeżenie „No subtitles were downloaded.”). `.srt`
jak zwykle. Wynik: `already_exists` = `false`, `media` = istniejący plik, `note` = notatka
językowa. `force` działa jak dotąd (pobiera film, notatek nie rusza).

Świadomie: goły `Tytuł.mp4` bez notatki **nie** jest uznawany za ten film — identyfikacja po
samym tytule mogłaby dopiąć notatkę do cudzego pliku. Ponowne pobranie trafia wtedy do
`Tytuł [ID].mp4`.

## Pakowanie

- **PyInstaller, tryb onefile, bez yt-dlp** (`youtube-downloader.spec`); dane: `icons/` i
  zasoby `customtkinter`. Wersja pochodzi tylko z `version.py` (hatch `only-include` +
  `cache-keys` w `uv`, żeby edytowalna instalacja nie trzymała starej kopii).
- **Linux: Python z systemowym Tk (Xft).** Tk z Pythona uv (python-build-standalone) jest
  zbudowany bez Xft — widzi tylko bitmapowy font X11 `fixed`, nie wczyta fontu kształtów
  CustomTkinter, więc zamiast strzałek list i ptaszków pól wyboru są litery „Y” i „Z”, rogi
  bez wygładzania. Dlatego paczkę Linux buduje Python z `actions/setup-python` (linkuje
  `libtk8.6` runnera, z Xft) na Ubuntu 22.04 — najstarszym wspieranym, bo plik dziedziczy
  glibc runnera. Krok CI sprawdza `tkinter.font.families()` (więcej niż `fixed`). Windows
  i testy CI zostają na Pythonie uv. `.deb` zależy od bibliotek, które PyInstaller zostawia
  systemowi (`libx11-6`, `libxft2`, `libfontconfig1`, `libxss1`), poleca `fonts-dejavu-core`.
- **Lokalny build na Pythonie uv:** `.spec` dokłada `libtcl*`/`libtk*` ręcznie (blok
  `tcltk_binaries`) — Python uv trzyma je obok `libpython`, a `_tkinter` nie ma RPATH. Taki plik
  działa, ale bez Xft; przy systemowym Pythonie blok nic nie znajduje.
- **Windows: `console=False`** — plik okienkowy, bez konsoli; stąd CLI tylko na Linuksie/WSL
  (podpolecenie w `.exe` → okno komunikatu i kod 2). Ikona `.ico` (błąd jej wczytania tylko
  trafia do logu), zasoby przez `sys._MEIPASS`.
- **NSIS** (`installer/windows/installer.nsi`): instalacja do Program Files, skróty, wpis
  odinstalowania z `DisplayIcon` (bez niego Ustawienia → Aplikacje pokazują pustą ikonę), ikona
  aplikacji także na instalatorze i deinstalatorze; na ostatniej stronie zaznaczone pole „Run
  YouTube Downloader” — start przez `explorer.exe`, czyli bez uprawnień administratora instalatora.
  Wersja z `/DAPP_VERSION`: CI podaje ją z `version.py`; domyślna w skrypcie służy tylko
  budowaniu ręcznemu.
- **`.deb`** (`installer/linux/build-deb.sh`): jeden plik `/usr/bin/youtube-downloader`, ikony,
  plik `.desktop`; `Recommends: ffmpeg`; wersja z `version.py`.
- **CI:** `ci.yml` — lint (tylko błędy składni), testy na Ubuntu (przez `xvfb-run`) i Windows,
  prosty skan plików wrażliwych (`.env`, `*.pem`, `*.key`);
  `build.yml` — paczki na obu systemach, test instalacji `.deb` na Ubuntu 22.04/24.04 (po
  `dpkg -i` zamrożony plik uruchamia `youtube-downloader tools --json` i musi zwrócić
  `"ok": true` — to pobiera narzędzia, więc wymaga sieci; potem okno musi żyć 10 s pod
  `xvfb-run` — CLI nie ładuje Tk, więc tylko to łapie brak bibliotek X11), na tagu `v*` wydanie GitHub. Oba
  workflow robią `uv sync --locked`. Akcje przypięte do SHA.

## Testy

`uv run pytest -q`; sieć nigdy nie jest używana — `ToolManager` dostaje podstawione `fetch`,
`Runner` zastępuje `tests/fake_ytdlp.py`, JSON-y i VTT pochodzą z prawdziwych odpowiedzi
(`tests/fixtures/`). Testy GUI (`test_gui_smoke.py`) wymagają wyświetlacza (WSLg lokalnie,
`xvfb-run` w CI) i same się pomijają bez niego. Zrzutów ekranu pod WSLg zrobić się nie da.
Testy CLI podmieniają ścieżkę `settings.json` na plik tymczasowy (dobowa aktualizacja silnika
czyta i zapisuje `last_update_check`), więc nigdy nie dotykają prawdziwych ustawień.

## Known Issues

Znane, jeszcze niepoprawione; najpierw te widoczne dla użytkownika.

**Pobieranie z YouTube**
- Przestoje: YouTube co pewien czas wstrzymuje wydanie każdego 10-MB kawałka strumienia
  (yt-dlp pobiera YouTube w kawałkach `http_chunk_size`) na ok. 20 s — film 60 MB schodzi wtedy
  w 2–4 min zamiast kilkunastu sekund. Na tym samym łączu i z tymi samymi argumentami raz
  9–33 s, raz 220 s — zależy od chwili (serwer/klient YouTube), nie od aplikacji ani łącza. W `app.log` widać to jako serię „no output for ~20 s” co ~10 MB. Bez
  obejścia; do zbadania przy kolejnym wystąpieniu z `-v` (który klient YouTube i serwer `rr…`).

**Aktualizacja narzędzi**
- `missing()` sprawdza yt-dlp tylko po istnieniu pliku: uszkodzony plik naprawia dopiero
  „Update engine” / `tools --update`, nie start aplikacji.
- Windows: aktualizacja narzędzia, które właśnie działa, kończy się mylącym `tools_missing`;
  brak ponowienia przy `PermissionError`; zostawiony katalog `.old` blokuje kolejne
  aktualizacje; awaria między dwoma `rename` może zgubić ostatnią dobrą kopię; sumy pobierane
  są dopiero po całym archiwum.
- „Check” podczas „Update engine” nie jest serializowane.
- Błąd zapisu na dysk albo zmieniona nazwa pliku w wydaniu (HTTP 404) podczas instalacji
  narzędzi jest pokazywany jako `network` („No connection…”).
- `tools --update` bez `--json` przy nieudanej aktualizacji wypisuje `… -> None`.

**Klasyfikacja błędów**
- `engine_outdated` dopasowuje też ostrzeżenia (`WARNING: … nsig extraction failed`), więc
  przy jednoczesnym prawdziwym błędzie (zerwane połączenie, prywatny film) podpowiedź może
  wskazywać aktualizację silnika zamiast właściwej przyczyny.

**Anulowanie i CLI**
- Ctrl+C w trakcie instalacji narzędzi i dobowej aktualizacji yt-dlp w CLI nie jest
  honorowane; na Windows `lines.get()` bez limitu czasu opóźnia Ctrl+C.
- `already_exists` zwraca `transcript: "none"`, choć notatka może mieć transkrypt (README i
  skill to opisują).
- Wywołanie `probe` nie da się anulować.

**Okno**
- Zamknięcie okna przy otwartym dialogu „Already downloaded” może zgłosić `TclError`;
  anulowanie w momencie zwrotu `already_exists` bywa pokazane jako dialog.
- Przycisk „Update engine” w panelu błędu nie jest wyłączany w trakcie pobierania; kliknięcie
  jest odrzucane, ale komunikat nadpisuje linię statusu pobierania.
- „Download again” dla filmu zapisanego jako `Tytuł [ID].mp4` bez notatki zapisuje drugi plik
  `Tytuł.mp4`.

**Notatka i nazwy**
- Pusty opis daje trzy puste linie.
- Rozpoznanie notatki: BOM UTF-8 uniemożliwia odczyt pola `url:`; pole dopasowywane luźno
  (wcięte, w cudzysłowie); rozszerzenie `.MD` wielkimi literami nie jest rozpoznawane;
  katalog o nazwie `base.md` koliduje, ale nie jest zgłaszany.
- Nazwy zastrzeżone `COM¹`/`LPT¹` (indeksy górne) i rozcięcie sekwencji ZWJ przy skracaniu.
- `info.language` dopasowywany dokładnie (`pl-PL` ≠ `pl`); `nocookie` w adresach `/v/` nieobsługiwane.
- Pusty plik `.vtt` daje pusty `.srt`.

**Ustawienia i logi**
- `last_update_check` z absurdalną liczbą może rzucić `OverflowError`, `NaN`/`inf` są
  przyjmowane.
- `setup_logging` przy ponownym wywołaniu ignoruje zmienioną ścieżkę i poziom.
- Uszkodzony `settings.json`: CLI zapisując czas sprawdzenia aktualizacji nadpisuje go
  ustawieniami domyślnymi (wybrany folder i preferencje okna przepadają).

**CI i testy**
- Lint tylko błędów składni; `RMDir` w NSIS bez warunku; zamrożony plik Windows nie jest
  uruchamiany w CI.
- Gałąź systemu Windows w `paths` jest wyliczana przy imporcie, więc nie da się jej
  przetestować na Linuksie.
- Niepokryte testami: ścieżki cofania instalacji narzędzi, archiwum tar z podatnymi
  ścieżkami, strażnicy przestarzałych wyników GUI, `gui/system.py`.

## Świadome decyzje

- Świadomie: bez logowania do YouTube i bez cookies — filmy wymagające konta kończą się
  `unavailable`.
- Świadomie: bez kolejki i playlist — jedno pobranie naraz, `--no-playlist` zawsze.
- Świadomie: CLI tylko na Linuksie/WSL; plik Windows jest okienkowy.
- Świadomie: CLI nie korzysta z ustawień GUI (poza wspólnym czasem ostatniej aktualizacji
  yt-dlp); `--out` jest wymagane, a skill pyta o folder.
- Świadomie: kod wyjścia 2 (błąd użycia, `argparse`) nie wypisuje JSON-a — wyjaśnienie idzie
  na stderr; skill i README to opisują.
- Świadomie: goły `Tytuł.mp4` bez notatki nie jest uznawany za ten sam film (patrz wyżej).
- Świadomie: yt-dlp z kanału stabilnego, nie nightly.
- Świadomie: aplikacja nie prowadzi historii pobrań — „Recent” to trzy ostatnie
  pozycje w ustawieniach, a stan „już pobrano” wynika z plików w folderze.
