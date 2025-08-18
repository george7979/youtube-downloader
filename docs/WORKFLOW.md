# 🔄 Dual-Repository Workflow Guide

## 📋 Przegląd

YouTube Downloader używa **dual-repository workflow** z trzema głównymi etapami:

```
LOCAL DEVELOPMENT
    ↓ (make sync-develop)
PRIVATE/develop
    ↓ (make promote)
PRIVATE/main (staging)
    ↓ (make release-public)  
PUBLIC/main (production)
```

## 🎯 Repozytoria

- **Private**: `george7979/youtube-downloader-private` - rozwój, testing, staging
- **Public**: `george7979/youtube-downloader` - czysta dystrybucja, releases

## 🛠️ Dostępne Komendy

### Podstawowe operacje

```bash
# Status workflow
make workflow-status        # Sprawdź status wszystkich etapów
make w                     # Alias dla workflow-status

# Synchronizacja develop
make sync-develop          # Local → Private/develop
make s                     # Alias
make sync-develop-force    # Force push (nadpisuje konflikty)

# Promocja do main
make promote-check         # Sprawdź czy promocja możliwa (dry run)
make promote              # Develop → Main (private)
make p                    # Alias
make promote-squash       # Promocja z squash commits

# Publikacja
make release-public-verify # Sprawdź czy publikacja możliwa (dry run)
make release-public       # Main private → Main public
make r                    # Alias

# Synchronizacja releases
make sync-releases        # Sync releases między repos
make watch-releases       # Monitoring + auto-sync
```

### Zaawansowane operacje

```bash
# Pełny workflow z potwierdzeniami
make sync-all             # Local → develop → main → public

# Bezpośrednie użycie skryptów
./scripts/sync-to-private.sh --help
./scripts/promote-to-main.sh --help  
./scripts/release-to-public.sh --help
./scripts/sync-releases.sh --help
```

## 📝 Typowy Workflow

### 1. Codzienna Praca

```bash
# Normalna praca nad kodem
git add .
git commit -m "New feature"

# Synchronizacja z private/develop
make sync-develop

# Lub sprawdź status przed sync
make workflow-status
```

### 2. Przygotowanie Release

```bash
# Sprawdź czy wszystko gotowe
make promote-check

# Promuj do main (private) - staging
make promote

# Opcjonalnie: squash commits dla czystszej historii
make promote-squash
```

### 3. Publikacja

```bash
# Sprawdź czy publikacja bezpieczna
make release-public-verify

# Publikuj do public repo
make release-public
```

### 4. Pełny Workflow (pojedyncza komenda)

```bash
# Wszystko w jednym (z potwierdzeniami)
make sync-all
```

## 🔒 Zabezpieczenia

### Automatyczne sprawdzenia na każdym etapie:

#### Promote (develop → main)
- ✅ Sprawdzenie plików wrażliwych
- ✅ Weryfikacja .gitignore  
- ✅ Test CI/CD
- ✅ Analiza różnic między branches

#### Release (main → public)
- ✅ **Podwójna weryfikacja bezpieczeństwa** (strict mode)
- ✅ Sprawdzenie wrażliwych plików
- ✅ Analiza zawartości do publikacji
- ✅ Potwierdzenie użytkownika przed publikacją

### Pliki wrażliwe (automatycznie blokowane):
- `.env`, `*.local`
- `cursorrules`, `.cursorrules`
- `*.key`, `*.pem`, `*.p12`
- `secrets/`, `private/`
- Pliki z hasłami/tokenami w nazwie

### 🔐 Context-Aware Security Filtering (v1.2.0)

System automatycznie filtruje pliki wrażliwe podczas publikacji do public repo:

- **`.gitignore-public`** - definiuje pliki do wykluczenia z public repo
- **Tymczasowy filtered branch** - tworzony automatycznie podczas publikacji
- **Kontekstowe sprawdzenia** - różne reguły dla private-promotion vs public-release

#### Pliki automatycznie usuwane podczas publikacji:
- `CLAUDE.md`, `PRD.md`, `TODO*.md`, `NOTES*.md` - dokumentacja deweloperska
- `cursorrules`, `.cursorrules` - reguły IDE
- Katalogi: `backup/`, `dev/`, `private/`, `security-checks/` - dane deweloperskie
- Development builds: `*_dev*.deb`, `*_alpha*.deb`, `*_beta*.deb`
- Skrypty workflow: `scripts/sync-to-private.sh`, `scripts/promote-to-main.sh`, etc.
- Pliki konfiguracyjne: `.env*`, `*.local`, `config.local.*`

#### Mechanizm działania:
1. **Private-promotion context** - pozwala na dokumentację deweloperską w private/main
2. **Public-release context** - blokuje dokumentację deweloperską w public repo
3. **Automatyczne filtrowanie** - tworzy clean branch bez wrażliwych plików
4. **Bezpieczna publikacja** - push do public repo z przefiltrowanego brancha

## 🚨 Tryby Awaryjne

### Force Operations

```bash
# Force sync (nadpisuje remote conflicts)
make sync-develop-force

# Force promotion (pomija niektóre sprawdzenia)
./scripts/promote-to-main.sh --skip-security --force

# Force publikacja
./scripts/release-to-public.sh --force
```

### Dry Run (bezpieczne testowanie)

```bash
# Test wszystkich operacji bez wykonania
./scripts/sync-to-private.sh --dry-run
./scripts/promote-to-main.sh --dry-run  
./scripts/release-to-public.sh --dry-run
```

## 🤖 GitHub Actions

### Automatyczna synchronizacja

Workflow `.github/workflows/auto-sync.yml` automatycznie:

1. **Przy release** - pełna synchronizacja do public
2. **Manual trigger** - wybór typu synchronizacji
3. **Sprawdzenie bezpieczeństwa** przed każdą publikacją
4. **Utworzenie issue** przy błędach

### Dostępne tryby:
- `full` - kod + releases
- `code-only` - tylko kod
- `releases-only` - tylko releases

## 📊 Monitoring

### Status Workflow

```bash
make workflow-status
```

Pokazuje:
- Current branch i commit
- Liczba zmian lokalnych
- Status względem develop/main
- Najnowsze releases w obu repos
- Dostępne komendy

### Continuous Monitoring

```bash
# Monitoruje releases i auto-sync
make watch-releases
```

## 🔧 Rozwiązywanie Problemów

### Problem: Conflicts podczas sync

```bash
# Sprawdź różnice
git status
git diff

# Force sync (ostateczność)
make sync-develop-force
```

### Problem: Promocja zablokowana przez security

```bash
# Sprawdź co blokuje
./scripts/security-check-main.sh develop

# Usuń problematyczne pliki
git rm cursorrules
git commit -m "Remove sensitive files"
```

### Problem: Publikacja niepowiodła się

```bash
# Sprawdź co jest nie tak
make release-public-verify

# Sprawdź GitHub Actions logi
# https://github.com/george7979/youtube-downloader-private/actions
```

### Problem: Releases nie synchronizują się

```bash
# Manual sync konkretnego release
./scripts/sync-releases.sh \
  --from george7979/youtube-downloader-private \
  --to george7979/youtube-downloader \
  --tag v1.0.3

# Force sync wszystkich
./scripts/sync-releases.sh \
  --from george7979/youtube-downloader-private \
  --to george7979/youtube-downloader \
  --force
```

## 📈 Best Practices

### 1. Regularna synchronizacja
- Codziennie: `make sync-develop`
- Po major changes: `make workflow-status`

### 2. Testowanie przed promocją
- Zawsze: `make promote-check`
- W razie wątpliwości: `--dry-run`

### 3. Bezpieczeństwo
- Nigdy nie commituj `.env`, `cursorrules`
- Sprawdzaj `make release-public-verify` przed publikacją
- Używaj GitHub Actions dla automatyzacji

### 4. Zarządzanie releases
- Tworząc release w private, automatycznie sync do public
- Używaj semantic versioning
- Zawsze dodawaj changelog

## 🔗 Linki

- **Private Repo**: https://github.com/george7979/youtube-downloader-private
- **Public Repo**: https://github.com/george7979/youtube-downloader  
- **Actions (Private)**: https://github.com/george7979/youtube-downloader-private/actions
- **Releases (Public)**: https://github.com/george7979/youtube-downloader/releases

---
*Dokumentacja workflow - ostatnia aktualizacja: 2025-08-17*