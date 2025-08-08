# Dual Repository Strategy

## 🎯 Cel

Zarządzanie dwoma repozytoriami:
- **🔒 PRIVATE**: Pełne repozytorium deweloperskie z wszystkimi plikami
- **🌍 PUBLIC**: Oczyszczona wersja dla użytkowników końcowych

## 📊 Porównanie strategii

| Strategia | Zalety | Wady | Użycie |
|-----------|--------|------|--------|
| **Git Subtree** | Wbudowany w Git | Skomplikowany workflow | Duże projekty |
| **Git Submodule** | Popularne rozwiązanie | Problemy z synchronizacją | Zewnętrzne zależności |
| **Git Subrepo** ⭐ | Prosty workflow | Beta software | Nasze zastosowanie |
| **Manual Sync** | Pełna kontrola | Ryzyko błędów | Proste projekty |

## 🏗️ Architektura

```
🔒 PRIVATE REPO (youtube-downloader-dev)
├── cursorrules                     ❌ SENSITIVE
├── build-scripts/                  ❌ INTERNAL TOOLS  
├── internal-docs/                  ❌ DEV NOTES
├── .env.dev                        ❌ DEV SECRETS
├── public-src/                     ✅ → SYNC TO PUBLIC
│   ├── main.py                     ✅ APPLICATION CODE
│   ├── gui.py                      ✅ USER INTERFACE
│   ├── README.md                   ✅ USER DOCS
│   ├── debian-src/                 ✅ PACKAGING
│   └── icons/                      ✅ ASSETS
└── scripts/
    ├── sync-to-public.sh           🔄 SYNC WORKFLOW
    ├── push-to-public.sh           📤 PUBLISH WORKFLOW
    └── pull-from-public.sh         📥 PULL WORKFLOW

🌍 PUBLIC REPO (youtube-downloader)  
├── main.py                         ✅ FROM private/public-src/
├── gui.py                          ✅ FROM private/public-src/
├── README.md                       ✅ FROM private/public-src/
├── debian-src/                     ✅ FROM private/public-src/
└── icons/                          ✅ FROM private/public-src/
```

## 🔄 Workflow

### **Daily Development (Private)**
```bash
# 1. Normal development in private repo
git add .
git commit -m "Feature: Add new functionality"
git push origin main

# 2. When ready to publish
./scripts/sync-to-public.sh        # Update public-src/
./scripts/push-to-public.sh        # Publish to public repo
```

### **Public User Contributions**
```bash
# 1. User creates PR in public repo
# 2. Pull changes back to private
./scripts/pull-from-public.sh

# 3. Review and merge in private
git merge public-changes
git push origin main

# 4. Sync back to public
./scripts/sync-to-public.sh
./scripts/push-to-public.sh
```

## 📋 Implementation Options

### **Option 1: Git-Subrepo (Recommended)**
```bash
# Setup
git subrepo init public-src -r https://github.com/user/youtube-downloader.git

# Daily workflow
git subrepo push public-src         # Private -> Public
git subrepo pull public-src         # Public -> Private
```

**Zalety:**
- ✅ Prosty workflow
- ✅ Automatyczna synchronizacja
- ✅ Historia zachowana w obu repozytoriach
- ✅ Jeden projekt, dwa widoki

### **Option 2: Manual Sync Scripts**
```bash
# Created scripts handle:
./scripts/sync-to-public.sh         # Copy files
./scripts/push-to-public.sh         # Manual git operations
./scripts/pull-from-public.sh       # Import external changes
```

**Zalety:**
- ✅ Pełna kontrola
- ✅ Możliwość customizacji każdego pliku
- ✅ Żadnych dodatkowych narzędzi

### **Option 3: GitHub Actions**
```yaml
# .github/workflows/sync-public.yml
name: Sync to Public
on:
  push:
    paths: ['public-src/**']
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Sync to public repo
        run: |
          # Push public-src/ to public repository
```

**Zalety:**
- ✅ Automatyczny workflow
- ✅ CI/CD integration
- ✅ Zero manual steps

## 🔒 Security Guidelines

### **Pliki do NIGDY nie publikowania:**
```bash
# Development files
cursorrules
.cursorrules
*.local
.env.dev
.env.local

# Internal tools
build-scripts/
dev-setup.sh
internal-docs/
private-*
TODO-dev.md

# Sensitive data
*.key
*.pem
secrets.json
config-dev.*

# Personal info
.git-credentials
.netrc
```

### **Files requiring sanitization:**
```bash
README.md           # Remove dev sections
BUILDING.md         # Keep user-relevant parts only
.gitignore          # Remove dev-specific ignores
package.json        # Remove dev dependencies
```

## 🎯 Best Practices

### **1. Automated Checks**
```bash
# Pre-push hook
#!/bin/bash
if grep -r "TODO-DEV\|FIXME-DEV\|XXX-DEV" public-src/; then
    echo "❌ Dev comments found in public-src/"
    exit 1
fi

if grep -r "API_KEY\|SECRET\|PASSWORD" public-src/; then
    echo "❌ Potential secrets found in public-src/"
    exit 1
fi
```

### **2. Documentation Strategy**
```
Private README.md:
- Complete development setup
- Internal workflows  
- Sensitive configurations
- Full contributor guidelines

Public README.md:
- User installation guide
- Basic usage
- Support information
- Contribution guidelines for users
```

### **3. Branch Strategy**
```
Private repo branches:
- main (development)
- feature/* (development)
- release/* (pre-public)

Public repo branches:  
- main (stable releases)
- patches/* (hotfixes)
- community/* (external contributions)
```

## 🚀 Migration Path

### **Phase 1: Setup (Now)**
1. ✅ Create scripts/setup-dual-repo.sh
2. ✅ Run setup script
3. ✅ Review public-src/ content
4. ✅ Create public GitHub repository

### **Phase 2: Implementation (Next)**
1. Choose sync strategy (git-subrepo recommended)
2. Setup initial sync
3. Test bidirectional workflow
4. Document process

### **Phase 3: Automation (Future)**
1. Add GitHub Actions
2. Setup automated testing
3. Add security scanning
4. Monitor both repositories

## 💡 Recommendations

**For YouTube Downloader project:**

1. **Use git-subrepo** - Perfect for our use case
2. **Keep cursorrules private** - Contains internal workflows
3. **Sanitize README.md** - Remove development sections
4. **Separate user docs** - Create public-friendly documentation
5. **Automate security** - Scan for secrets before publishing

## 📞 Support

If issues arise:
1. Check both repositories are in sync
2. Verify .gitignore rules
3. Run security scans
4. Test with clean clone

---

**Next Steps:** Run `./scripts/setup-dual-repo.sh` to begin setup.