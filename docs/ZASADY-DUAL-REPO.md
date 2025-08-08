# 📋 ZASADY DUAL-REPO WORKFLOW

## 🎯 GŁÓWNE ZASADY

### **1. PODZIAŁ REPOZYTORIÓW**
```
🔒 PRIVATE: github.com/user/youtube-downloader-dev
   - Pełne repozytorium deweloperskie
   - Wszystkie pliki, łącznie z wrażliwymi
   - Główne miejsce pracy developera

🌍 PUBLIC: github.com/user/youtube-downloader  
   - Oczyszczona wersja dla użytkowników końcowych
   - Tylko kod aplikacji i dokumentacja użytkownika
   - Bez plików deweloperskich i sekretów
```

### **2. PLIKI NIGDY NIE DO PUBLIKACJI** ❌

#### **Pliki wrażliwe:**
- `cursorrules` / `.cursorrules`
- `.env.local` / `.env.dev`
- `*.key` / `*.pem` / `secrets.json`
- `.git-credentials` / `.netrc`
- `config-dev.*`

#### **Narzędzia deweloperskie:**
- `build-scripts/`
- `dev-setup.sh`
- `internal-docs/`
- `private-*`
- `TODO-dev.md`
- `debug-*`

#### **Pliki tymczasowe:**
- `*.local`
- `tmp/` / `temp/`
- `*.log` (debug logs)
- `.backup/`

### **3. PLIKI DO SANITYZACJI** 🧹

#### **README.md:**
```markdown
PRIVATE wersja:
- Pełny development setup
- Wewnętrzne workflows
- Wrażliwe konfiguracje
- Kompletne contributor guidelines

PUBLIC wersja:
- Instrukcja instalacji dla użytkowników
- Podstawowe użycie
- Informacje o wsparciu
- Uproszczone contribution guidelines
```

#### **BUILDING.md:**
```markdown
PRIVATE: Kompletny workflow developera
PUBLIC: Tylko informacje dla użytkowników końcowych o instalacji
```

#### **.gitignore:**
```bash
PRIVATE: Wszystkie ignores
PUBLIC: Tylko user-relevant ignores (bez dev-specific)
```

## 🔄 WORKFLOW ZASADY

### **FLEXIBLE DEVELOPMENT WORKFLOW** 🎯

#### **PRIVATE PUSHE** (kiedy chcesz - bez ograniczeń):
```bash
# Work in progress - zapisuj dowolnie często
git add .
git commit -m "WIP: dodaję nową funkcję pobierania playlist"
git push origin main  # → PRIVATE repo

# Daily backup - koniec dnia
git commit -m "EOD: prace nad GUI, jeszcze nie skończone"
git push origin main  # → PRIVATE repo

# Debug session 
git commit -m "debug: testuje różne podejścia do error handling"
git push origin main  # → PRIVATE repo

# Experimental commits
git commit -m "experiment: próbuję nowy sposób validacji URL"
git push origin main  # → PRIVATE repo
```

**Zalety PRIVATE pushes:**
- ✅ **Backup w chmurze** - nigdy nie stracisz pracy
- ✅ **Work from anywhere** - kontynuuj na innym urządzeniu  
- ✅ **Pełna historia** - każdy krok development jest zapisany
- ✅ **No pressure** - commituj nawet niedokończony kod
- ✅ **Częstotliwość:** Nawet kilka razy dziennie

#### **PUBLIC PUSHE** (kiedy kod jest gotowy):
```bash
# Stabilna funkcja
git commit -m "Feature: dodana obsługa playlist YouTube/Spotify"
./scripts/sync-to-public-github.sh  # Sync to public-src/
./scripts/push-to-public.sh         # → PUBLIC repo

# Ważny bugfix
git commit -m "Fix: naprawiony crash przy długich nazwach plików"
./scripts/sync-to-public-github.sh
./scripts/push-to-public.sh

# Zestaw drobnych poprawek
git commit -m "Improvements: lepszy UX + poprawki UI"
./scripts/sync-to-public-github.sh  
./scripts/push-to-public.sh
```

**Kiedy pushować do PUBLIC?** 🚀
- 🎯 **Nowa funkcja działa** i jest przetestowana
- 🐛 **Ważny bug naprawiony** - users powinni mieć fix
- 🚀 **Chcesz żeby users mieli najnowszą wersję**
- 🔧 **Zebrało się kilka drobnych poprawek**
- 🆘 **Emergency hotfix** - krytyczne problemy
- ⚡ **Performance boost** - znaczące ulepszenia

**Częstotliwość PUBLIC:** **Według potrzeb** - może być codziennie, może co tydzień

#### **PRAKTYCZNY PRZYKŁAD TYGODNIA:**
```
Poniedziałek:
├── git commit -m "WIP: rozpocząłem nową funkcję X" → PRIVATE
├── git commit -m "debug: testuje różne podejścia" → PRIVATE

Wtorek:  
├── git commit -m "progress: funkcja X prawie gotowa" → PRIVATE
├── git commit -m "fix: drobny bug w funkcji Y" → PRIVATE

Środa:
├── git commit -m "Feature: funkcja X gotowa i przetestowana" → PRIVATE
└── [SYNC TO PUBLIC] → "Feature: dodana nowa funkcja X" → PUBLIC

Czwartek:
├── git commit -m "WIP: eksperyment z nowym UI" → PRIVATE
├── git commit -m "EOD: zapisuje progres UI" → PRIVATE

Piątek:
├── git commit -m "HOTFIX: krytyczny bug w funkcji Z" → PRIVATE  
└── [EMERGENCY SYNC TO PUBLIC] → "Hotfix: naprawiony krytyczny bug" → PUBLIC
```

### **CODZIENNI DEVELOPMENT:**
1. ✅ Pracuj normalnie w PRIVATE repo - pushuj dowolnie często
2. ✅ Commituj każdy progres do PRIVATE (WIP, debug, experiments)
3. ✅ Kiedy kod jest **gotowy i stabilny**:
   ```bash
   ./scripts/sync-to-public.sh    # Aktualizuj public-src/
   ./scripts/push-to-public.sh    # Publikuj do PUBLIC repo
   ```

### **EXTERNAL CONTRIBUTIONS:**
1. ✅ User tworzy PR w PUBLIC repo
2. ✅ Przejrzyj zmiany w PUBLIC
3. ✅ Importuj do PRIVATE:
   ```bash
   ./scripts/pull-from-public.sh
   ```
4. ✅ Review i merge w PRIVATE
5. ✅ Sync z powrotem do PUBLIC

### **RELEASE PROCESS:**
1. ✅ Sfinalizuj zmiany w PRIVATE
2. ✅ Uruchom testy w PRIVATE
3. ✅ Sync do PUBLIC: `./scripts/sync-to-public.sh`
4. ✅ Przejrzyj `public-src/` - czy wszystko OK?
5. ✅ Publikuj: `./scripts/push-to-public.sh`
6. ✅ Create release w PUBLIC repo
7. ✅ Tag odpowiednią wersję w PRIVATE

## 🛡️ SECURITY CHECKLIST

### **PRZED KAŻDYM PUSH DO PUBLIC:**
```bash
# 1. Sprawdź czy brak sekretów
grep -r "API_KEY\|SECRET\|PASSWORD\|TOKEN" public-src/

# 2. Sprawdź czy brak dev comments
grep -r "TODO-DEV\|FIXME-DEV\|XXX-DEV\|DEBUG" public-src/

# 3. Sprawdź czy brak private files  
find public-src/ -name "cursorrules" -o -name "*.local" -o -name "private-*"

# 4. Sprawdź .gitignore
cat public-src/.gitignore  # Czy zawiera tylko public-relevant ignores?

# 5. Sprawdź README.md
head -20 public-src/README.md  # Czy brzmi jak user documentation?
```

### **AUTOMATED SECURITY HOOK:**
```bash
# .git/hooks/pre-push w PRIVATE repo
#!/bin/bash
if [ -d "public-src" ]; then
    echo "🔍 Security scan of public-src/..."
    
    # Sprawdź sekrety
    if grep -r "API_KEY\|SECRET\|PASSWORD\|TOKEN" public-src/ >/dev/null; then
        echo "❌ BLOCKED: Potential secrets found in public-src/"
        grep -r "API_KEY\|SECRET\|PASSWORD\|TOKEN" public-src/
        exit 1
    fi
    
    # Sprawdź dev comments
    if grep -r "TODO-DEV\|FIXME-DEV\|XXX-DEV" public-src/ >/dev/null; then
        echo "❌ BLOCKED: Dev comments found in public-src/"
        grep -r "TODO-DEV\|FIXME-DEV\|XXX-DEV" public-src/
        exit 1
    fi
    
    # Sprawdź private files
    if find public-src/ -name "cursorrules" -o -name "*.local" -o -name "private-*" | grep -q .; then
        echo "❌ BLOCKED: Private files found in public-src/"
        find public-src/ -name "cursorrules" -o -name "*.local" -o -name "private-*"
        exit 1
    fi
    
    echo "✅ Security scan passed"
fi
```

## 📁 STRUCTURE ZASADY

### **PRIVATE REPO STRUKTURA:**
```
youtube-downloader-dev/
├── 🔒 PRIVATE FILES:
│   ├── cursorrules                 # NIGDY nie publikuj
│   ├── build-scripts/              # Narzędzia dev
│   ├── internal-docs/              # Notatki dev  
│   ├── .env.local                  # Sekrety dev
│   ├── TODO-dev.md                 # Dev todos
│   └── private-configs/            # Wrażliwe konfigi
│
├── 📤 SYNC TOOLS:
│   └── scripts/
│       ├── setup-dual-repo.sh      # Pierwszy setup
│       ├── sync-to-public.sh       # PRIVATE → PUBLIC
│       ├── push-to-public.sh       # Publikowanie
│       └── pull-from-public.sh     # PUBLIC → PRIVATE
│
├── 🌍 PUBLIC SOURCE:
│   └── public-src/                 # ← To idzie do PUBLIC repo
│       ├── main.py                 # Kod aplikacji
│       ├── gui.py                  # Interface
│       ├── README.md               # User docs (sanitized)
│       ├── debian-src/             # Packaging
│       ├── icons/                  # Assets
│       └── .gitignore              # Public ignores
│
└── 📚 DOCUMENTATION:
    ├── DUAL-REPO.md                # Strategy docs
    ├── ZASADY-DUAL-REPO.md         # Te zasady
    └── BUILDING.md                 # Kompletny dev guide
```

### **PUBLIC REPO STRUKTURA:**
```
youtube-downloader/
├── main.py                         # Z private/public-src/
├── gui.py                          # Z private/public-src/
├── README.md                       # Sanitized dla users
├── debian-src/                     # Packaging files
├── icons/                          # Application assets
├── .gitignore                      # Tylko public-relevant
└── LICENSE                         # MIT license
```

## 🔍 MONITORING ZASADY

### **REGULAR CHECKS:**
1. **Tygodniowo:** Sprawdź czy PUBLIC repo nie ma przypadkowych sekretów
2. **Przed release:** Pełny security scan
3. **Po external PR:** Verify czy nie ma malicious code
4. **Miesięcznie:** Review czy structure jest OK

### **ALERTS SETUP:**
```yaml
# GitHub Actions w PUBLIC repo
name: Security Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Scan for secrets
        run: |
          if grep -r "API_KEY\|SECRET\|PASSWORD" .; then
            echo "❌ Potential secrets found"
            exit 1
          fi
```

## ⚠️ CO ROBIĆ GDY...

### **❌ Przypadkowo spushowałeś sekrety do PUBLIC:**
1. **NATYCHMIAST:** Delete PUBLIC repo lub force push clean version
2. **Zmień wszystkie sekrety** które mogły zostać ujawnione
3. **Sprawdź logi dostępu** do PUBLIC repo
4. **Audit:** Jak to się stało i jak zapobiec w przyszłości

### **❌ PUBLIC repo jest out-of-sync:**
1. **Sprawdź:** `git status` w obu repo
2. **Manual sync:** Copy files z PRIVATE public-src/ do PUBLIC
3. **Force push** jeśli konieczne  
4. **Fix workflow** żeby zapobiec w przyszłości

### **❌ External PR wprowadza problematyczny kod:**
1. **NIE merguj** blindly do PRIVATE
2. **Review carefully** w sandbox environment
3. **Test** w PRIVATE przed merge
4. **Document** co zostało zmienione

## 🎯 SUCCESS METRICS

### **SIGNS OF GOOD DUAL-REPO:**
- ✅ PUBLIC repo ma tylko user-relevant files
- ✅ Zero sekretów w PUBLIC repo history  
- ✅ PUBLIC README jest clear dla end users
- ✅ External contributors mogą łatwo contribute
- ✅ PRIVATE repo ma pełną development env
- ✅ Sync process jest automated i reliable

### **RED FLAGS:**
- ❌ Sekrety w PUBLIC repo
- ❌ Dev files w PUBLIC repo
- ❌ Skomplikowany sync process
- ❌ Manual errors podczas sync
- ❌ PUBLIC repo nie ma sensownej dokumentacji dla users

---

## 📞 EMERGENCY CONTACTS

**W przypadku security incident:**
1. Natychmiast usuń sekrety z PUBLIC repo
2. Zmień wszystkie exposed credentials
3. Review GitHub access logs  
4. Document incident dla future prevention

---

**Pamiętaj: PRIVATE repo jest source of truth, PUBLIC repo jest filtered view dla users.**