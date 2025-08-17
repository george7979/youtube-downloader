# 📋 Plan Migracji: Dual-Repo → Single-Repo z Branch Strategy

## 📊 Executive Summary

**Status**: Planowana migracja z architektury dual-repo na single-repo  
**Powód**: Uproszczenie workflow, zgodność ze standardami 2024, eliminacja redundancji  
**Metoda**: Trunk-based development z main/develop branches  
**Timeline**: Q1 2025  

---

## 🎯 Cele Migracji

### Główne cele:
1. **Uproszczenie architektury** - jeden repository zamiast dwóch
2. **Zgodność ze standardami** - trunk-based development (industry standard 2024)
3. **Eliminacja problemów** - koniec z false positives w security hooks
4. **Łatwiejsze zarządzanie** - jeden .gitignore, jedna historia commitów
5. **Lepszy CI/CD** - prostsze GitHub Actions workflows

### Co zachowujemy:
- ✅ Separacja kodu deweloperskiego od produkcyjnego
- ✅ Ochrona wrażliwych plików (cursorrules, .env)
- ✅ Clean releases dla użytkowników
- ✅ Możliwość szybkich hotfixów

---

## 📚 Analiza Obecnej Architektury

### Struktura Dual-Repo (OBECNA)
```
🔒 youtube-downloader-private/     (DEV - wszystkie pliki)
├── cursorrules                     ❌ Nigdy nie publikowane
├── scripts/                        ❌ Narzędzia deweloperskie
├── public-src/                     ✅ Synchronizowane do public
└── .git/hooks/pre-push            🔍 Security check (false positives!)

🌍 youtube-downloader/             (PUBLIC - clean code)
└── [tylko pliki z public-src/]    ✅ Dla użytkowników końcowych
```

### Problemy z obecnym podejściem:
1. **Duplikacja pracy** - sync między repozytoriami
2. **Security hooks false positives** - blokują push przez znajdowanie "password" w samych skryptach
3. **Skomplikowany workflow** - multiple remotes, sync scripts
4. **Trudne zarządzanie** - dwa miejsca do monitorowania
5. **Niezgodność ze standardami** - dual-repo to edge case, nie standard

---

## 🚀 Docelowa Architektura (Single-Repo)

### Struktura Branch (NOWA)
```
📦 youtube-downloader/              (JEDNO REPO)
├── main                           (production-ready, releases)
├── develop                        (integration, pre-release)
└── feature/*                      (active development)

📁 Struktura plików:
├── src/                           ✅ Kod aplikacji
├── docs/                          ✅ Dokumentacja
├── tests/                         ✅ Testy
├── .github/workflows/             ✅ CI/CD
├── .gitignore                     🔒 Ignoruje wszystkie sensitive files
├── cursorrules                    🔒 W .gitignore (lokalnie tylko)
├── .env                           🔒 W .gitignore (lokalnie tylko)
└── README.md                      ✅ User documentation
```

### Strategia .gitignore (KLUCZOWA!)
```gitignore
# Sensitive - ZAWSZE ignorowane
cursorrules
.cursorrules
*.local
.env*
!.env.example
secrets/
private/

# Development - ignorowane
*.log
.vscode/
.idea/
__pycache__/
*.pyc
.DS_Store

# Build artifacts - ignorowane  
dist/
build/
*.egg-info/
```

---

## 🔄 Zgodność ze Standardami Branżowymi (2024)

### ✅ Co jest zgodne ze standardami:

#### **Trunk-Based Development** (Obecny Standard)
- **main → develop → feature/** - prosty, liniowy flow
- **Short-lived feature branches** - max 1-2 dni
- **Continuous Integration** - częste merge do develop
- **Single source of truth** - jeden .gitignore dla wszystkich

#### **GitHub Flow** (Alternatywa)
- **main → feature/** - jeszcze prostszy
- **Pull Requests** - code review przed merge
- **Deploy from main** - każdy commit to potencjalny release

### ❌ Anti-Patterns do uniknięcia:

#### **Git Flow** (Legacy - NIE UŻYWAĆ!)
- ~~main/develop/release/hotfix~~ - zbyt skomplikowane
- ~~Long-lived branches~~ - prowadzą do merge conflicts
- ~~Ceremonial releases~~ - spowalniają delivery

#### **Branch-per-Environment** (Anti-Pattern!)
- ~~dev/uat/staging/prod branches~~ - NIE ROBIĆ TEGO!
- **Problem**: Ten sam kod powinien działać wszędzie
- **Rozwiązanie**: Environment variables, nie różne branches

### 📊 Potwierdzenie ze źródeł (2024):

**Atlassian Git Tutorial**:
> "Gitflow is now considered legacy. Modern teams should consider GitHub flow and trunk-based development"

**Google Engineering Practices**:
> "We use trunk-based development. Feature branches live less than 24 hours"

**ThoughtWorks Technology Radar**:
> "Branch-per-environment is an anti-pattern. Use the same code with different configurations"

---

## 📝 Plan Migracji Krok po Kroku

### Phase 1: Przygotowanie (Tydzień 1)

#### 1.1 Backup obecnego stanu
```bash
# Backup private repo
git clone https://github.com/george7979/youtube-downloader-private.git backup-private/
cd backup-private/
git bundle create ../youtube-downloader-private-backup.bundle --all

# Backup public repo  
git clone https://github.com/george7979/youtube-downloader.git backup-public/
cd backup-public/
git bundle create ../youtube-downloader-public-backup.bundle --all
```

#### 1.2 Utworzenie comprehensive .gitignore
```bash
# W private repo
cat > .gitignore << 'EOF'
# === SENSITIVE FILES === 
# Nigdy nie commituj tych plików!
cursorrules
.cursorrules
*.local
.env
.env.*
!.env.example
secrets/
private/
credentials/
*.key
*.pem
*.p12
*.pfx

# === DEVELOPMENT ===
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# === PYTHON ===
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# === BUILD ARTIFACTS ===
dist/
build/
*.egg-info/
.eggs/
*.egg

# === TESTING ===
.coverage
.pytest_cache/
.tox/
htmlcov/

# === LOGS ===
*.log
logs/
*.pid

# === TEMPORARY ===
tmp/
temp/
.tmp/
EOF
```

#### 1.3 Cleanup private repo
```bash
# Usuń stare sync scripts (nie będą potrzebne)
rm -rf scripts/sync-to-public*.sh
rm -rf scripts/push-to-public.sh
rm -rf scripts/pull-from-public.sh
rm -rf scripts/force-sync-public.sh

# Usuń public-src/ (wszystko będzie w głównym katalogu)
mv public-src/* .
rm -rf public-src/

# Usuń dual-repo dokumentację (zastąpimy nową)
rm docs/DUAL-REPO.md
rm docs/ZASADY-DUAL-REPO.md
```

### Phase 2: Konfiguracja Branches (Tydzień 1-2)

#### 2.1 Utworzenie develop branch
```bash
# W private repo (które stanie się głównym)
git checkout -b develop
git push -u origin develop

# Ustaw develop jako default branch w GitHub UI
# Settings → Branches → Default branch → develop
```

#### 2.2 Branch protection rules
```bash
# GitHub UI: Settings → Branches → Add rule

# Dla 'main':
✅ Require pull request reviews (1 approval)
✅ Dismiss stale PR approvals
✅ Require status checks (CI/CD)
✅ Require branches to be up to date
✅ Include administrators

# Dla 'develop':  
✅ Require status checks (tests, linting)
✅ Require branches to be up to date
```

#### 2.3 Update GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest flake8
      - name: Lint
        run: flake8 .
      - name: Test
        run: pytest
      
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Security scan
        run: |
          # Sprawdź czy nie ma przypadkowych commitów sensitive files
          if git ls-files | grep -E "(cursorrules|\.env|\.local|private-)" ; then
            echo "❌ Sensitive files found in repository!"
            exit 1
          fi
```

### Phase 3: Migracja Zawartości (Tydzień 2)

#### 3.1 Finalna struktura katalogów
```bash
youtube-downloader/
├── src/                    # Kod źródłowy
│   ├── main.py
│   ├── gui.py  
│   ├── downloader.py
│   └── utils.py
├── tests/                  # Testy jednostkowe
│   ├── test_downloader.py
│   └── test_utils.py
├── docs/                   # Dokumentacja
│   ├── ARCHITECTURE.md
│   ├── CONTRIBUTING.md
│   └── DEVELOPMENT.md
├── debian/                 # Packaging (jeśli potrzebne)
├── .github/               
│   └── workflows/
│       ├── ci.yml
│       ├── release.yml
│       └── security.yml
├── requirements.txt        # Dependencies
├── requirements-dev.txt    # Dev dependencies  
├── setup.py               # Package setup
├── README.md              # User documentation
├── LICENSE                # MIT License
├── .gitignore             # Comprehensive ignore rules
└── .env.example           # Example environment variables
```

#### 3.2 Przeniesienie historii z public repo
```bash
# Dodaj public jako remote
git remote add old-public https://github.com/george7979/youtube-downloader.git

# Fetch historia
git fetch old-public

# Cherry-pick ważne commity (opcjonalnie)
# git cherry-pick <commit-hash>

# Usuń remote
git remote remove old-public
```

### Phase 4: Workflow Development (Tydzień 2-3)

#### 4.1 Nowy Development Workflow
```bash
# 1. Nowa funkcja
git checkout develop
git pull origin develop
git checkout -b feature/nowa-funkcja

# 2. Development
# ... edycja plików ...
git add .
git commit -m "feat: dodaj nową funkcję"

# 3. Update z develop
git checkout develop
git pull origin develop
git checkout feature/nowa-funkcja
git rebase develop

# 4. Push i PR
git push -u origin feature/nowa-funkcja
# Utwórz PR w GitHub: feature/nowa-funkcja → develop

# 5. Po review i merge
git checkout develop
git pull origin develop
git branch -d feature/nowa-funkcja
```

#### 4.2 Release Workflow
```bash
# 1. Przygotowanie release z develop
git checkout develop
git pull origin develop

# 2. Utwórz PR do main
# GitHub: Create PR develop → main
# Title: "Release v1.2.3"

# 3. Po aprobacie i merge
git checkout main
git pull origin main
git tag v1.2.3
git push origin v1.2.3

# 4. GitHub automatycznie tworzy release
```

#### 4.3 Hotfix Workflow
```bash
# 1. Hotfix z main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# 2. Fix
# ... napraw bug ...
git commit -m "fix: napraw krytyczny bug"

# 3. PR do main
git push -u origin hotfix/critical-bug
# PR: hotfix/critical-bug → main

# 4. Backport do develop
git checkout develop
git pull origin develop
git cherry-pick <hotfix-commit>
git push origin develop
```

### Phase 5: Czyszczenie i Finalizacja (Tydzień 3)

#### 5.1 Update dokumentacji
```markdown
# README.md
## Development

### Quick Start
1. Clone: `git clone https://github.com/george7979/youtube-downloader.git`
2. Branch: `git checkout develop`
3. Install: `pip install -r requirements-dev.txt`
4. Test: `pytest`

### Contributing
- Create feature branch from `develop`
- Make changes with tests
- Submit PR to `develop`
- After review, we'll merge and eventually release to `main`
```

#### 5.2 Archiwizacja starego public repo
```bash
# W GitHub UI dla youtube-downloader (public)
Settings → Options → Archive this repository
✅ "Archive this repository"

# Dodaj README z przekierowaniem
echo "# ⚠️ ARCHIVED - Moved to main repository" > README.md
echo "This repository has been archived. " >> README.md  
echo "Please use: https://github.com/george7979/youtube-downloader-private" >> README.md
git add README.md
git commit -m "docs: add archive notice"
git push origin main
```

#### 5.3 Rename private repo (usuń "-private")
```bash
# GitHub UI: Settings → Options → Repository name
# Zmień z: youtube-downloader-private
# Na: youtube-downloader

# Update local remote
git remote set-url origin https://github.com/george7979/youtube-downloader.git
```

---

## ✅ Checklist Przed Usunięciem Private Repo

### Krytyczne sprawdzenia:
- [ ] Backup obu repozytoriów (bundle files)
- [ ] Wszystkie ważne commity przeniesione
- [ ] CI/CD działa na nowych branches
- [ ] .gitignore kompletny i przetestowany
- [ ] Dokumentacja zaktualizowana
- [ ] Team poinformowany o zmianach
- [ ] External links zaktualizowane
- [ ] Issues/PRs przeniesione lub zamknięte

### Test końcowy:
```bash
# Clone fresh i sprawdź
git clone https://github.com/george7979/youtube-downloader.git test-repo/
cd test-repo/
git checkout develop

# Sprawdź brak sensitive files
ls -la | grep -E "(cursorrules|\.env|private-)"  # Powinno być puste

# Sprawdź czy działa
python3 -m venv .venv
source .venv/bin/activate  
pip install -r requirements.txt
python src/main.py  # Test podstawowy
```

---

## 🎯 Rezultaty Po Migracji

### Co zyskujemy:
✅ **Prostsza architektura** - jeden repo, jasne branches  
✅ **Zgodność ze standardami** - trunk-based development  
✅ **Łatwiejszy workflow** - bez sync scripts  
✅ **Lepsza historia** - jedna timeline commitów  
✅ **Mniej błędów** - brak false positives w hooks  
✅ **Szybszy development** - mniej kroków do release  
✅ **Industry standard** - każdy developer zna ten workflow  

### Porównanie workflow:

#### PRZED (Dual-Repo):
```
Edit → Commit → Push to Private → Sync Script → Security Check → Push to Public → Issues!
```

#### PO (Single-Repo):
```
Edit → Commit → Push to feature → PR to develop → Merge → PR to main → Release!
```

---

## 📚 Referencje i Best Practices

### Oficjalne źródła:
1. **[Atlassian Git Tutorials](https://www.atlassian.com/git/tutorials/comparing-workflows)** - "Gitflow is now considered legacy"
2. **[GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)** - Prosty, efektywny workflow
3. **[Google Engineering](https://abseil.io/resources/swe-book/html/ch16.html)** - Trunk-based w praktyce
4. **[Martin Fowler](https://martinfowler.com/articles/branching-patterns.html)** - Branching patterns analysis

### Kluczowe zasady 2024:
- 🎯 **Trunk-based > Git Flow** - prostota wygrywa
- 🎯 **Short-lived branches** - max 1-2 dni życia
- 🎯 **Continuous Integration** - częste merge
- 🎯 **Same code everywhere** - config różni environments
- 🎯 **Simple > Complex** - mniej moving parts

---

## 🚀 Timeline Wykonania

### Tydzień 1 (Przygotowanie)
- ✅ Backup repozytoriów
- ✅ Utworzenie .gitignore  
- ✅ Cleanup struktur
- ✅ Setup develop branch

### Tydzień 2 (Migracja)
- ⏳ Przeniesienie contentu
- ⏳ Konfiguracja CI/CD
- ⏳ Branch protection rules
- ⏳ Test workflows

### Tydzień 3 (Finalizacja)  
- ⏳ Update dokumentacji
- ⏳ Archiwizacja old public
- ⏳ Rename repository
- ⏳ Team training

### Tydzień 4 (Monitoring)
- ⏳ Obserwacja nowego workflow
- ⏳ Zbieranie feedback
- ⏳ Drobne poprawki
- ⏳ Finalna dokumentacja

---

## 📞 Kontakt i Wsparcie

**Owner**: Jerzy Maczewski  
**Repository**: https://github.com/george7979/youtube-downloader  
**Status**: 🔄 W trakcie migracji  

---

*Ostatnia aktualizacja: Sierpień 2025*  
*Wersja dokumentu: 1.0*  
*Status: DRAFT - Do zatwierdzenia przed wykonaniem*