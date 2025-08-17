# 🚀 Release Process - Develop → Main 

## Bezpieczny proces przejścia develop → main dla single-repository

### 🎯 Cel procesu
Zapewnienie że na main branch trafiają tylko:
- ✅ Stabilne, przetestowane funkcje
- ✅ Czyste pliki źródłowe bez wrażliwych danych
- ✅ Finalne release builds (.deb tylko dla stable versions)
- ❌ **NIE:** development builds, cursorrules, prywatne skrypty

## 📋 Fazy Release Process

### Phase 1: Pre-Release Validation
```bash
# 1. Sprawdź że develop jest gotowe do merge
git checkout develop
git status  # must be clean
git pull origin develop

# 2. Uruchom pełne testy
make test               # Technical validation
make ci-check          # Full CI pipeline
# Manual UAT testing according to docs/TESTING_CHECKLIST.md

# 3. Security scan develop branch
./scripts/security-check.sh develop
```

### Phase 2: Security Filter Setup
```bash
# Sprawdź które pliki NIE powinny iść na main
echo "🔍 Checking for sensitive files..."

# Files that MUST NOT go to main:
find . -name "cursorrules" -o -name ".cursorrules"
find . -name "*.local" -o -name ".env*" 
find . -name "*secret*" -o -name "*private*"
find . -name "*dev*.deb"  # Development .deb builds
ls -la backup/           # Backup directories
ls -la scripts/          # Private scripts

# Create exclusion list
cat > .release-exclude << 'EOF'
cursorrules
.cursorrules
backup/
scripts/push-to-private.sh
scripts/force-sync-public.sh
youtube-downloader_*_dev*.deb
*.local
.env*
*secret*
*private*
EOF
```

### Phase 3: Clean Merge Strategy

#### Option A: Selective File Merge (Recommended)
```bash
# 1. Checkout main and ensure it's clean
git checkout main
git pull origin main

# 2. Create release branch for safe merge
git checkout -b release/v1.x.x

# 3. Selective merge - only production-ready files
git checkout develop -- src/
git checkout develop -- docs/TESTING_CHECKLIST.md
git checkout develop -- docs/MIGRATION_PLAN.md
git checkout develop -- .github/workflows/ci.yml
git checkout develop -- .gitignore
git checkout develop -- README.md
git checkout develop -- requirements.txt
git checkout develop -- main.py
git checkout develop -- tests/

# 4. Update version to release version (NOT development)
echo '__version__ = "1.x.x"' > version.py  # STABLE VERSION

# 5. Add only stable .deb (if exists)
if [ -f "youtube-downloader_1.x.x_all.deb" ]; then
    git add -f youtube-downloader_1.x.x_all.deb
fi
```

#### Option B: Full Merge with Cleanup (Alternative)
```bash
# 1. Merge develop to release branch
git checkout main
git checkout -b release/v1.x.x
git merge develop --no-commit

# 2. Remove sensitive files before commit
git reset HEAD cursorrules .cursorrules
git reset HEAD backup/
git reset HEAD scripts/push-to-private.sh
git reset HEAD youtube-downloader_*_dev*.deb
rm -f cursorrules .cursorrules
rm -rf backup/

# 3. Clean up .gitignore for main (less restrictive)
# Edit .gitignore to allow stable .deb files but block dev builds
```

### Phase 4: Release Finalization
```bash
# 1. Commit release
git add .
git commit -m "release: v1.x.x - [Brief description of major changes]

- Feature 1: description
- Feature 2: description  
- Security: improvements
- Migration: architecture changes

🔒 Security verified: No sensitive data included
✅ Tests passed: CI/CD pipeline successful
📦 Stable build: Ready for production release"

# 2. Final security check
./scripts/security-check.sh HEAD

# 3. Merge to main
git checkout main
git merge --no-ff release/v1.x.x

# 4. Tag release
git tag -a v1.x.x -m "Release v1.x.x - [Brief description]"

# 5. Push to remote
git push origin main
git push origin v1.x.x

# 6. Create GitHub Release
gh release create v1.x.x \
    --title "YouTube Downloader v1.x.x" \
    --notes "## Release Notes..." \
    youtube-downloader_1.x.x_all.deb
```

### Phase 5: Post-Release Cleanup
```bash
# 1. Update develop branch
git checkout develop
git merge main  # Keep develop in sync

# 2. Increment develop version for next cycle
echo '__version__ = "1.x+1.0-dev"' > version.py
git add version.py
git commit -m "chore: Bump version to next development cycle"
git push origin develop

# 3. Clean up release branch
git branch -d release/v1.x.x
```

## 🛡️ Security Guards

### Automated Pre-Commit Hooks
```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "🔍 Security check before commit..."

if [ "$BRANCH" = "main" ]; then
    # Extra strict checks for main branch
    if find . -name "cursorrules" | grep -q .; then
        echo "❌ BLOCKED: cursorrules found in main branch"
        exit 1
    fi
    
    if find . -name "*dev*.deb" | grep -q .; then
        echo "❌ BLOCKED: Development .deb found in main branch"
        exit 1
    fi
fi
```

### GitHub Actions Protection
```yaml
# .github/workflows/main-protection.yml
name: Main Branch Protection
on:
  push:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Block sensitive files
      run: |
        if find . -name "cursorrules" | grep -q .; then
          echo "❌ Sensitive files detected in main branch"
          exit 1
        fi
```

## 📝 Branch Strategy Summary

### develop branch:
- ✅ Development builds (.deb)
- ✅ cursorrules, private scripts
- ✅ backup/ directories
- ✅ All development tools
- ✅ version.py = "X.Y.Z-dev"

### main branch:
- ✅ Only stable releases (.deb)
- ✅ Clean source code only
- ❌ NO development tools
- ❌ NO cursorrules or private files
- ✅ version.py = "X.Y.Z" (stable)

### release branches:
- 🔄 Temporary branches for safe merge
- 🧹 Security filtering applied
- 🚀 Bridge between develop and main

## 🎯 Quick Reference Commands

```bash
# Start release process
git checkout develop && git pull
make test && make ci-check
git checkout -b release/v1.x.x

# Selective merge (recommended)
git checkout develop -- src/ docs/ .github/ README.md requirements.txt

# Finish release
git checkout main && git merge --no-ff release/v1.x.x
git tag v1.x.x && git push origin main v1.x.x
gh release create v1.x.x youtube-downloader_1.x.x_all.deb
```

---
*Last updated: August 2025 - Single Repository Architecture*