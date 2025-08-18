# 🚀 Release Process - Dual-Repository Workflow

## 📋 Przegląd 3-Stage Release Pipeline

YouTube Downloader używa **dual-repository architecture** z trzema głównymi etapami release:

```
🏠 LOCAL DEVELOPMENT
    ↓ (make sync-develop)
🔒 PRIVATE/develop (development & testing)
    ↓ (make promote)
🔒 PRIVATE/main (staging & validation)
    ↓ (make release-public)
🌍 PUBLIC/main (production & releases)
```

## 🎯 Repozytoria i Role

### 🔒 Private Repository (`george7979/youtube-downloader-private`)
- **Development Environment** - codzienne kodowanie
- **Testing & Staging** - weryfikacja funkcji przed publikacją
- **Security Screening** - kontrola wrażliwych plików
- **Release Preparation** - przygotowanie clean builds

### 🌍 Public Repository (`george7979/youtube-downloader`)
- **Production Environment** - tylko stabilny, przetestowany kod
- **Official Releases** - pakiety .deb i GitHub releases
- **Public Issues & Documentation** - wsparcie użytkowników
- **Clean Distribution** - brak development files

## 📋 Stage 1: Development → Private/develop

### 🎯 Cel
Synchronizacja lokalnych zmian z private repository dla codziennej pracy zespołu.

### 📝 Procedura
```bash
# 1. Sprawdź status lokalnego kodu
git status
git log --oneline -5

# 2. Zsynchronizuj zmiany
make sync-develop
# Lub z dodatkowymi opcjami:
make sync-develop-force  # Force push (nadpisuje konflikty)

# 3. Weryfikuj synchronizację
make workflow-status
```

### ✅ Co jest dozwolone na tym etapie:
- 🔧 Development builds (`*_dev.deb`)
- 📝 `cursorrules`, `.cursorrules`
- 🗂️ `backup/` directories
- 🛠️ Development tools i scripts
- 📊 Debug logs i test files
- 🔧 Version format: `"X.Y.Z-dev"`

### 🚨 Automatyczne sprawdzenia:
- Branch sync status
- Local changes detection
- Remote conflict resolution

---

## 📋 Stage 2: Private/develop → Private/main

### 🎯 Cel
Promocja stabilnych funkcji do staging environment z security validation.

### 📝 Procedura
```bash
# 1. Pre-promotion validation
make promote-check        # Dry run - sprawdź czy promocja możliwa
git checkout develop
make test                 # Uruchom testy techniczne
# Manual UAT według docs/TESTING_CHECKLIST.md

# 2. Security scan
./scripts/security-check-main.sh develop

# 3. Promocja
make promote              # Standard promotion
# Lub:
make promote-squash      # Squash commits dla czystszej historii

# 4. Weryfikacja
make workflow-status
```

### 🔒 Security Features na tym etapie:
```bash
# Automatyczne sprawdzenie wrażliwych plików:
- cursorrules, .cursorrules
- *.env, *.local, *secret*, *private*
- *.key, *.pem, *.p12
- backup/, dev-tools/
- Development .deb builds
```

### ✅ Co przechodzi do Private/main:
- ✅ Clean source code
- ✅ Updated documentation
- ✅ Production-ready build scripts
- ✅ CI/CD configurations
- ✅ Version updated to stable format: `"X.Y.Z"`

### ❌ Co jest blokowane:
- ❌ `cursorrules` files
- ❌ Environment configs (`.env*`)
- ❌ Development builds
- ❌ Private backup directories
- ❌ Debug i development tools

---

## 📋 Stage 3: Private/main → Public/main

### 🎯 Cel
Publikacja stabilnego kodu i releases do production environment.

### 📝 Procedura
```bash
# 1. Pre-release validation
make release-public-verify    # Comprehensive security check

# 2. Final testing
git checkout main
make test
make build                   # Create production .deb

# 3. Create release (w private repo)
./build-tools/version-manager.sh bump patch  # lub minor/major
git commit -am "Release v$(./build-tools/version-manager.sh show)"
git tag v$(./build-tools/version-manager.sh show)

# 4. Publikacja do public repo
make release-public

# 5. Weryfikacja
gh release list --repo george7979/youtube-downloader
```

### 🔐 Automatyczne filtrowanie plików (v1.2.0)

Podczas publikacji do public repo system automatycznie:

1. **Tworzy tymczasowy branch** `public-filtered-{timestamp}`
2. **Usuwa pliki zgodnie z `.gitignore-public`**:
   - Dokumentacja deweloperska (CLAUDE.md, PRD.md, TODO*.md)
   - Konfiguracje IDE (cursorrules, .cursorrules)
   - Katalogi deweloperskie (backup/, dev/, private/, security-checks/)
   - Development builds (*_dev*.deb, *_alpha*.deb, *_beta*.deb)
   - Skrypty workflow (scripts/sync-to-private.sh, etc.)
3. **Commituje zmiany** z opisem "Filter files for public release"
4. **Pushuje przefiltrowany branch** do public repo
5. **Usuwa tymczasowy branch** po publikacji

To zapewnia, że wrażliwe pliki deweloperskie **NIGDY** nie trafią do publicznego repo.

### 🔒 Enhanced Security (Strict Mode):
- **Double validation** - sprawdzenie w private i public
- **User confirmation** - wymagane potwierdzenie przed publikacją
- **Content analysis** - analiza różnic między repos
- **Sensitive file detection** - podwójna kontrola wrażliwych danych
- **Automatic filtering** - automatyczne usuwanie plików z .gitignore-public

### ✅ Co jest publikowane:
- ✅ **Core application** (`core/`, `ui/`)
- ✅ **Public documentation** (`docs/`)
- ✅ **Build system** (`build-tools/`, cleaned)
- ✅ **Essential scripts** (workflow, cleaned)
- ✅ **CI/CD configs** (`.github/workflows/`)
- ✅ **Project files** (`README.md`, `requirements.txt`, `LICENSE`)
- ✅ **Production releases** (stable `.deb` packages)

### ❌ Co nigdy nie jest publikowane:
- ❌ `cursorrules` - development rules
- ❌ `.venv/` - virtual environments
- ❌ `backup/` - private backups
- ❌ `dev-tools/` - development utilities
- ❌ `*dev*.deb` - development builds
- ❌ `.env*` - environment configs

---

## 🤖 GitHub Actions Automation

### Auto-Sync Workflow (`.github/workflows/auto-sync.yml`)

#### Triggers:
1. **Release Publication** - automatyczna pełna synchronizacja
2. **Manual Dispatch** - wybór typu synchronizacji
3. **Scheduled** - regularne sprawdzenia

#### Dostępne tryby:
- `full` - kod + releases (default)
- `code-only` - tylko synchronizacja kodu
- `releases-only` - tylko synchronizacja releases

#### Security Features:
- Automatyczny security scan przed publikacją
- Failure notifications via GitHub Issues
- Rollback capability w przypadku problemów

```yaml
# Przykład manual trigger:
workflow_dispatch:
  inputs:
    sync_type:
      description: 'Sync type'
      required: true
      default: 'full'
      type: choice
      options:
        - full
        - code-only
        - releases-only
```

---

## 📊 Quick Reference Commands

### Daily Workflow
```bash
# Codzienna praca
git add . && git commit -m "Feature implementation"
make sync-develop              # Stage 1: Local → Private/develop

# Status monitoring
make workflow-status           # Sprawdź status wszystkich etapów
make w                        # Alias dla workflow-status
```

### Release Preparation
```bash
# Stage 2: Develop → Main (private)
make promote-check            # Sprawdź czy promocja możliwa
make promote                  # Wykonaj promocję z security check
make p                       # Alias dla promote
```

### Production Release
```bash
# Stage 3: Main → Public
make release-public-verify    # Sprawdź czy publikacja bezpieczna
make release-public          # Publikuj do production
make r                      # Alias dla release-public
```

### Full Pipeline
```bash
# Wszystkie etapy w jednej komendzie (z potwierdzeniami)
make sync-all                # Local → develop → main → public
```

### Monitoring & Maintenance
```bash
make watch-releases          # Continuous monitoring releases
./scripts/sync-releases.sh   # Manual release synchronization
```

---

## 🚨 Emergency Procedures

### Force Operations (Ostateczność)
```bash
# Force sync (nadpisuje remote conflicts)
make sync-develop-force

# Force promotion (pomija niektóre sprawdzenia)
./scripts/promote-to-main.sh --skip-security --force

# Force publication (emergency release)
./scripts/release-to-public.sh --force
```

### Dry Run Testing (Bezpieczne)
```bash
# Test wszystkich operacji bez wykonania
./scripts/sync-to-private.sh --dry-run --verbose
./scripts/promote-to-main.sh --dry-run --verbose
./scripts/release-to-public.sh --dry-run --verbose
```

### Rollback Procedures
```bash
# Rollback niepowodzenie promotion
git checkout develop
git branch -D staging/promotion
git reset --hard origin/develop

# Rollback publication (manual)
# 1. Delete problematic release z public repo
gh release delete v1.x.x --repo george7979/youtube-downloader
# 2. Re-run corrected publication
make release-public
```

---

## 🔧 Troubleshooting

### Problem: Promotion blocked by security
```bash
# Sprawdź co blokuje
./scripts/security-check-main.sh develop

# Usuń problematyczne pliki
git rm cursorrules .env.local
git commit -m "Remove sensitive files for promotion"

# Spróbuj ponownie
make promote
```

### Problem: Publication failed
```bash
# Diagnostyka
make release-public-verify
make workflow-status

# Sprawdź GitHub Actions
# https://github.com/george7979/youtube-downloader-private/actions

# Manual recovery
./scripts/release-to-public.sh --force --verbose
```

### Problem: Release sync nie działa
```bash
# Manual sync konkretnego release
./scripts/sync-releases.sh \
  --from george7979/youtube-downloader-private \
  --to george7979/youtube-downloader \
  --tag v1.0.3

# Force sync wszystkich releases
./scripts/sync-releases.sh \
  --from george7979/youtube-downloader-private \
  --to george7979/youtube-downloader \
  --force
```

---

## 📈 Best Practices

### 1. Development
- **Daily sync**: `make sync-develop` po każdej sesji kodowania
- **Feature branches**: używaj feature branches dla większych zmian
- **Testing**: zawsze testuj lokalnie przed sync

### 2. Staging (Private/main)
- **Security first**: zawsze `make promote-check` przed promocją
- **Clean history**: używaj `make promote-squash` dla czystszej historii
- **Documentation**: aktualizuj changelog przy każdej promocji

### 3. Production (Public/main)
- **Verification**: zawsze `make release-public-verify`
- **Semantic versioning**: używaj proper version numbering
- **Release notes**: dołączaj meaningful release notes

### 4. Monitoring
- **Regular checks**: `make workflow-status` codziennie
- **Auto-monitoring**: używaj `make watch-releases` dla continuous monitoring
- **GitHub Actions**: monitoruj automated workflows

---

## 📞 Support & Links

### Repositories
- **Private**: https://github.com/george7979/youtube-downloader-private
- **Public**: https://github.com/george7979/youtube-downloader

### Monitoring
- **Actions (Private)**: https://github.com/george7979/youtube-downloader-private/actions
- **Releases (Public)**: https://github.com/george7979/youtube-downloader/releases

### Documentation
- **Workflow Details**: [docs/WORKFLOW.md](WORKFLOW.md)
- **Build Instructions**: [docs/BUILDING.md](BUILDING.md)
- **Project Structure**: [docs/README-STRUCTURE.md](README-STRUCTURE.md)

---

*Release Process Documentation - Last updated: 2025-08-17*
*Dual-Repository Workflow v1.2.0*