# 📁 Struktura Projektu YouTube Downloader

## 🎯 Przegląd Struktury

```
youtube-downloader-dev/              # 🔒 PRIVATE REPOSITORY
├── 📁 public-src/                   # 🌍 SOURCE FOR PUBLIC REPO
│   ├── main.py                      # → Kod aplikacji
│   ├── gui.py                       # → Interface użytkownika
│   ├── downloader.py                # → Logika pobierania
│   ├── utils.py                     # → Narzędzia pomocnicze
│   ├── requirements.txt             # → Zależności Python
│   ├── README.md                    # → Dokumentacja użytkownika
│   ├── LICENSE                      # → Licencja MIT
│   ├── debian-src/                  # → Debian packaging
│   ├── icons/                       # → Ikony aplikacji
│   ├── pics/                        # → Screenshots
│   └── .github/                     # → GitHub Actions
│
├── 📁 build-tools/                  # 🔧 BUILD SYSTEM
│   ├── build-deb.sh                # → Główny skrypt budowania
│   └── version-manager.sh           # → Zarządzanie wersjami
│
├── 📁 scripts/                      # 🔄 DUAL-REPO TOOLS
│   ├── sync-to-public-github.sh     # → Sync do PUBLIC repo
│   ├── force-sync-public.sh         # → Force sync z czyszczeniem
│   ├── security-check.sh            # → Skanowanie bezpieczeństwa
│   ├── install-hooks.sh             # → Instalacja Git hooks
│   ├── setup-dual-repo.sh           # → Pierwszy setup
│   └── pull-from-public.sh          # → Import z PUBLIC repo
│
├── 📁 docs/                         # 📚 DOCUMENTATION
│   ├── BUILDING.md                  # → Instrukcja budowania
│   ├── DUAL-REPO.md                 # → Strategia dual-repo
│   ├── ZASADY-DUAL-REPO.md          # → Zasady workflow
│   └── README-STRUCTURE.md          # → Ten plik
│
├── 📁 dev-tools/                    # 🛠️ DEVELOPMENT UTILITIES
│   └── (reserved for future tools)
│
├── 🔗 SYMLINKS (for development):
│   ├── main.py → public-src/main.py
│   ├── gui.py → public-src/gui.py
│   ├── downloader.py → public-src/downloader.py
│   ├── utils.py → public-src/utils.py
│   ├── requirements.txt → public-src/requirements.txt
│   └── debian-src → public-src/debian-src
│
├── 📋 PROJECT MANAGEMENT:
│   ├── Makefile                     # → Build automation
│   ├── README.md                    # → Main project README
│   ├── plan.md                      # → Development plan
│   ├── cursorrules                  # → 🔒 DEV RULES (private!)
│   ├── .gitignore                   # → Git ignore rules
│   └── LICENSE                      # → MIT License
│
└── 📦 ARTIFACTS:
    └── *.deb                        # → Built packages
```

## 🔄 Workflow Katalogów

### **1. Development Workflow**
- **Pracuj z**: Symlinks w root (main.py, gui.py, etc.)
- **Source of truth**: `public-src/` directory
- **Build tools**: `build-tools/` directory  
- **Documentation**: `docs/` directory

### **2. Dual-Repo Sync**
- **Sync source**: `public-src/` → PUBLIC repository
- **Sync tools**: `scripts/sync-to-public-github.sh`
- **Security**: `scripts/security-check.sh`

### **3. Build Process**
- **Main script**: `build-tools/build-deb.sh`
- **Version management**: `build-tools/version-manager.sh`
- **Automation**: `make build`

## 🎯 Zalety Tej Struktury

### ✅ **Korzyści:**
1. **Clear separation**: Dev tools vs source code vs documentation
2. **No duplication**: Symlinks eliminują duplikację plików
3. **Easy sync**: `public-src/` jest ready-to-sync
4. **Organized**: Każdy typ plików ma swoje miejsce
5. **Scalable**: Łatwo dodać nowe narzędzia

### 🔒 **Security Benefits:**
- Private files nie są przypadkowo w `public-src/`
- Build tools pozostają tylko w private repo
- Documentation wrażliwa w `docs/` nie sync się
- Security scripts w dedykowanym `scripts/`

## 📖 Jak Używać

### **Daily Development:**
```bash
# Edit files through symlinks (normalnie)
vim main.py                    # Edytuje public-src/main.py
vim gui.py                     # Edytuje public-src/gui.py

# Build with organized tools
make build                     # Używa build-tools/build-deb.sh
make version                   # Używa build-tools/version-manager.sh

# Sync to public when ready
./scripts/sync-to-public-github.sh
```

### **New Team Member Setup:**
```bash
git clone <private-repo>
cd youtube-downloader-dev

# Setup hooks
./scripts/install-hooks.sh

# Verify structure
ls -la *.py                    # Should see symlinks
ls -la public-src/             # Should see actual files
ls -la build-tools/            # Should see build scripts
```

### **Add New Tool:**
```bash
# Development tool
cp new-dev-tool.sh dev-tools/

# Build tool
cp new-build-script.sh build-tools/

# Documentation
cp new-doc.md docs/

# Sync script
cp new-sync-tool.sh scripts/
```

## 🔍 Troubleshooting

### **Symlinks not working:**
```bash
# Recreate symlinks
rm main.py gui.py downloader.py utils.py requirements.txt debian-src
ln -s public-src/main.py main.py
ln -s public-src/gui.py gui.py
ln -s public-src/downloader.py downloader.py
ln -s public-src/utils.py utils.py
ln -s public-src/requirements.txt requirements.txt
ln -s public-src/debian-src debian-src
```

### **Build tools not found:**
```bash
# Check paths in Makefile
make debug-version
make debug-build
```

### **Documentation outdated:**
```bash
# Update paths in documentation
find docs/ -name "*.md" -exec sed -i 's|./version-manager.sh|./build-tools/version-manager.sh|g' {} \;
```

---

**This structure provides maximum organization while maintaining the dual-repo workflow efficiency.**