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
├── (no symlinks) – pliki źródłowe trzymamy w root; `public-src/` jest snapshotem publikacyjnym
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
- **Pracuj w**: root (main.py, gui.py, downloader.py, utils.py)
- **Source of truth**: root
- **Public snapshot**: `make sync-public` przygotowuje `public-src/`
- **Build tools**: `build-tools/`, **Documentation**: `docs/`

### **2. Dual-Repo Sync**
- **Krok 1**: `make sync-public` (root → public-src)
- **Krok 2**: `make push-public` (public-src → public GitHub, z security check i potwierdzeniem)

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
# Praca w repo prywatnym
vim main.py gui.py downloader.py utils.py

# Build
make build

# Wersja
./build-tools/version-manager.sh bump patch  # lub set X.Y.Z

# Publikacja (gdy gotowe)
make sync-public
make push-public
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

### **Publikacja nie zawiera zmian:**
```bash
# Upewnij się, że odświeżyłeś snapshot
make sync-public
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