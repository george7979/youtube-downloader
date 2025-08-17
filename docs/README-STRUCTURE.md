# 📁 Struktura Projektu YouTube Downloader

## 🎯 Przegląd Dual-Repository Architecture

Projekt używa **dual-repository workflow** z rozdzieleniem development/production:

```
📂 PRIVATE REPO (george7979/youtube-downloader-private)
├── Development, testing, staging
├── Pełny kod z narzędziami deweloperskimi
└── Wrażliwe pliki (cursorrules, dev configs)

📂 PUBLIC REPO (george7979/youtube-downloader)  
├── Clean production code
├── Official releases i assets
└── Public issues & documentation
```

## 🏗️ Struktura Private Repository

```
youtube-downloader-private/
├── 📁 build-tools/                  # 🔧 BUILD SYSTEM
│   ├── build-deb.sh                # → Główny skrypt budowania
│   └── version-manager.sh           # → Zarządzanie wersjami
│
├── 📁 scripts/                      # 🔄 DUAL-REPO WORKFLOW
│   ├── sync-to-private.sh           # → Local → Private/develop
│   ├── promote-to-main.sh           # → Develop → Main (private)
│   ├── release-to-public.sh         # → Main Private → Main Public
│   ├── sync-releases.sh             # → Sync releases między repos
│   ├── security-check-main.sh       # → Security validation
│   └── demo-safe-merge.sh           # → Safe merge demonstrations
│
├── 📁 docs/                         # 📚 DOCUMENTATION
│   ├── BUILDING.md                  # → Instrukcja budowania
│   ├── WORKFLOW.md                  # → Dual-repo workflow guide
│   ├── RELEASE_PROCESS.md           # → Release management
│   ├── TESTING_CHECKLIST.md         # → QA procedures
│   ├── README-STRUCTURE.md          # → Ten plik
│   └── WORKFLOW-SYNC-PLAN.md        # → Plan implementacji workflow
│
├── 📁 .github/                      # 🤖 GITHUB ACTIONS
│   └── workflows/
│       ├── ci.yml                   # → Continuous Integration
│       ├── build.yml                # → Build & Test
│       └── auto-sync.yml            # → Auto sync to public repo
│
├── 📁 core/                         # 🎯 APPLICATION CORE
│   ├── downloader.py               # → Download logic
│   └── utils.py                    # → Utility functions
│
├── 📁 ui/                           # 🎨 USER INTERFACE
│   └── gui.py                      # → GUI implementation
│
├── 📁 pics/                         # 🖼️ SCREENSHOTS & ASSETS
│   ├── youtube-downloader-120.png  # → App screenshots
│   └── youtube-downloader-2.png    # → Interface previews
│
├── 📋 PROJECT MANAGEMENT:
│   ├── launcher.py                  # → Main application entry point
│   ├── version.py                   # → Version configuration
│   ├── requirements.txt             # → Python dependencies
│   ├── Makefile                     # → Build automation
│   ├── README.md                    # → Main project README
│   ├── CONTRIBUTING.md              # → Contribution guidelines
│   ├── LICENSE                      # → MIT License
│   ├── .gitignore                   # → Git ignore rules
│   ├── cursorrules                  # → 🔒 DEV RULES (private only!)
│   └── .github/                     # → GitHub configuration
│
└── 📁 IGNORED IN PUBLIC:
    ├── .venv/                       # → Python virtual environments
    ├── build/                       # → Build artifacts
    ├── *.deb                        # → Package files
    ├── backup/                      # → Backup directories
    └── dev-tools/                   # → Development utilities
```

## 🏗️ Struktura Public Repository

```
youtube-downloader/
├── 📁 build-tools/                  # ✅ Clean build system
│   ├── build-deb.sh                # → Production build script
│   └── version-manager.sh           # → Version management
│
├── 📁 scripts/                      # ✅ Essential scripts only
│   ├── sync-to-private.sh           # → Development sync
│   ├── promote-to-main.sh           # → Staging promotion
│   ├── release-to-public.sh         # → Production release
│   └── sync-releases.sh             # → Release synchronization
│
├── 📁 docs/                         # ✅ Public documentation
│   ├── BUILDING.md                  # → Build instructions
│   ├── WORKFLOW.md                  # → Development workflow
│   └── README-STRUCTURE.md          # → This file
│
├── 📁 .github/workflows/            # ✅ Public CI/CD
│   ├── ci.yml                       # → Quality checks
│   └── auto-sync.yml                # → Auto synchronization
│
├── 📁 core/                         # ✅ Clean application code
├── 📁 ui/                           # ✅ User interface
├── 📁 pics/                         # ✅ Public screenshots
│
├── launcher.py                      # ✅ Application entry point
├── version.py                       # ✅ Version info
├── requirements.txt                 # ✅ Dependencies
├── Makefile                         # ✅ Build system
├── README.md                        # ✅ User documentation
├── CONTRIBUTING.md                  # ✅ Contribution guide
├── LICENSE                          # ✅ MIT License
└── .gitignore                       # ✅ Clean ignore rules

❌ NEVER IN PUBLIC:
├── cursorrules                      # 🔒 Development rules
├── .venv/                           # 🔒 Virtual environments
├── backup/                          # 🔒 Private backups
├── dev-tools/                       # 🔒 Development utilities
└── *dev*.deb                        # 🔒 Development builds
```

## 🔄 Workflow Synchronization

### 1. Development Flow
```bash
# Private repo - codzienna praca
LOCAL → PRIVATE/develop
  ↓ make sync-develop
PRIVATE/develop (all files, including sensitive)
```

### 2. Staging Flow  
```bash
# Promotion z security check
PRIVATE/develop → PRIVATE/main
  ↓ make promote (+ security scan)
PRIVATE/main (cleaned, staged)
```

### 3. Production Flow
```bash
# Final release do public
PRIVATE/main → PUBLIC/main
  ↓ make release-public (+ final validation)
PUBLIC/main (clean, production-ready)
```

## 🔒 Security & Privacy

### 🚫 Files NEVER synced to public:
- `cursorrules` - Development rules
- `.env*`, `*.local` - Environment configs
- `backup/` - Private backups  
- `dev-tools/` - Development utilities
- `*dev*.deb` - Development builds
- `.venv/` - Virtual environments
- Private scripts i configurations

### ✅ Files always synced:
- Core application code
- Public documentation
- Build system (cleaned)
- Tests and CI configuration
- Official releases and assets

## 📊 File Flow Matrix

| File Type | Private → Public | Comments |
|-----------|------------------|----------|
| `core/`, `ui/` | ✅ Always | Application code |
| `docs/` | ✅ Always | Documentation |
| `build-tools/` | ✅ Always | Build system |
| `scripts/workflow` | ✅ Always | Essential scripts |
| `requirements.txt` | ✅ Always | Dependencies |
| `launcher.py` | ✅ Always | Entry point |
| `cursorrules` | ❌ Never | Development rules |
| `.venv/` | ❌ Never | Virtual env |
| `backup/` | ❌ Never | Private backups |
| `*.deb` (dev) | ❌ Never | Dev builds |
| `.env*` | ❌ Never | Environment configs |

## 🛠️ Development Guidelines

### 📂 Dodawanie nowych plików:
1. **Kod aplikacji** → umieść w `core/` lub `ui/`
2. **Build tools** → dodaj do `build-tools/`  
3. **Dokumentacja** → wrzuć do `docs/`
4. **Dev utilities** → umieść w `dev-tools/` (nie sync do public)

### 🔧 Narzędzia workflow:
- `make workflow-status` - sprawdź status synchronizacji
- `make sync-develop` - wyślij zmiany do private/develop
- `make promote` - przenieś develop → main (private)
- `make release-public` - publikuj main → public repo

### 🎯 Best Practices:
- Testuj zawsze w private/develop przed promocją
- Używaj security checks przed każdą publikacją
- Dokumentuj zmiany w changelog
- Sprawdzaj co zostanie zsynchronizowane z public

---
*Struktura zaktualizowana dla dual-repository workflow v1.2.0*