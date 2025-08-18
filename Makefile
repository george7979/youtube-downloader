# YouTube Downloader - Makefile
# Autor: george7979

# Konfiguracja
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

# Zmienne
VERSION := $(shell ./build-tools/version-manager.sh show | grep "Aktualna wersja:" | cut -d: -f2 | xargs)
PACKAGE_NAME := youtube-downloader
DEB_FILE := $(PACKAGE_NAME)_$(VERSION)_all.deb

# Kolory dla output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

define log_info
	@echo -e "$(BLUE)ℹ️  $(1)$(NC)"
endef

define log_success
	@echo -e "$(GREEN)✅ $(1)$(NC)"
endef

define log_warning
	@echo -e "$(YELLOW)⚠️  $(1)$(NC)"
endef

.PHONY: help build clean test install version check deps ci ci-check sync-develop promote release-public sync-releases sync-all workflow-status

help: ## Pokaż tę pomoc
	@printf "$(BLUE)YouTube Downloader Build System$(NC)\n"
	@echo ""
	@printf "$(GREEN)Dostępne cele:$(NC)\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@printf "$(BLUE)Aktualna wersja:$(NC) $(GREEN)$(VERSION)$(NC)\n"

build: check ## Zbuduj pakiet DEB
	$(call log_info,Budowanie pakietu $(DEB_FILE)...)
	@./build-tools/build-deb.sh
	$(call log_success,Pakiet zbudowany: $(DEB_FILE))

clean: ## Wyczyść pliki build (bez usuwania lokalnych .deb)
	$(call log_info,Czyszczenie plików build...)
	@rm -rf build/
	@rm -f *.md5 *.sha256
	@rm -f .version-backup
	$(call log_success,Pliki build usunięte)

test: build ## Przetestuj pakiet
	$(call log_info,Testowanie pakietu...)
	@dpkg --info $(DEB_FILE)
	$(call log_info,Sprawdzanie zawartości pakietu...)
	@FILE_COUNT=$$(dpkg --contents $(DEB_FILE) 2>/dev/null | wc -l); echo "Pakiet zawiera $$FILE_COUNT plikow"
	@if command -v lintian >/dev/null 2>&1; then \
		$(call log_info,Sprawdzanie lintian...); \
		lintian $(DEB_FILE) || true; \
	else \
		$(call log_warning,lintian nie jest dostępny - pomijam sprawdzenie); \
	fi
	$(call log_success,Testy zakończone)

install: test ## Zainstaluj pakiet lokalnie
	$(call log_info,Instalacja pakietu...)
	@sudo dpkg -i $(DEB_FILE)
	@sudo apt-get install -f || true
	$(call log_success,Pakiet zainstalowany)


uninstall: ## Usuń pakiet
	$(call log_info,Usuwanie pakietu...)
	@sudo dpkg -r $(PACKAGE_NAME) || true
	$(call log_success,Pakiet usunięty)

version: ## Pokaż aktualną wersję
	@./build-tools/version-manager.sh show

bump-patch: ## Zwiększ wersję patch (1.0.3 -> 1.0.4)
	$(call log_info,Zwiększanie wersji patch...)
	@./build-tools/version-manager.sh bump patch
	$(call log_success,Wersja patch zwiększona)

bump-minor: ## Zwiększ wersję minor (1.0.3 -> 1.1.0)
	$(call log_info,Zwiększanie wersji minor...)
	@./build-tools/version-manager.sh bump minor
	$(call log_success,Wersja minor zwiększona)

bump-major: ## Zwiększ wersję major (np. 1.0.3 -> 1.1.0)
	$(call log_info,Zwiększanie wersji major...)
	@./build-tools/version-manager.sh bump major
	$(call log_success,Wersja major zwiększona)

check: ## Sprawdź wymagania systemowe
	$(call log_info,Sprawdzanie wymagań...)
	@command -v dpkg-deb >/dev/null || { echo "❌ Brak dpkg-deb. Zainstaluj: apt-get install dpkg-dev"; exit 1; }
	@command -v fakeroot >/dev/null || { echo "❌ Brak fakeroot. Zainstaluj: apt-get install fakeroot"; exit 1; }
	@command -v python3 >/dev/null || { echo "❌ Brak python3"; exit 1; }
	@test -f launcher.py || { echo "❌ Brak launcher.py"; exit 1; }
	@test -f version.py || { echo "❌ Brak version.py"; exit 1; }
	@test -f core/downloader.py || { echo "❌ Brak core/downloader.py"; exit 1; }
	@test -f ui/gui.py || { echo "❌ Brak ui/gui.py"; exit 1; }
	@test -x build-tools/build-deb.sh || { echo "❌ build-tools/build-deb.sh nie jest wykonywalny"; exit 1; }
	@test -x build-tools/version-manager.sh || { echo "❌ build-tools/version-manager.sh nie jest wykonywalny"; exit 1; }
	$(call log_success,Wszystkie wymagania spełnione)

deps: ## Zainstaluj zależności budowania
	$(call log_info,Instalacja zależności budowania...)
	@sudo apt-get update
	@sudo apt-get install -y \
		build-essential \
		debhelper \
		devscripts \
		dh-python \
		dpkg-dev \
		fakeroot \
		python3-all \
		python3-setuptools \
		python3-dev \
		python3-pip \
		python3-venv \
		lintian \
		git
	$(call log_success,Zależności zainstalowane)

release: clean bump-patch build test ## Pełny release (bump patch + build + test)
	$(call log_success,Release gotowy: $(DEB_FILE))
	@echo ""
	@echo "Następne kroki:"
	@echo "1. git commit -am 'Release $(VERSION)'"
	@echo "2. git tag v$(VERSION)"
	@echo "3. git push origin main --tags"
	@echo "4. Wgraj $(DEB_FILE) do GitHub Releases"

ci: clean check build test ## Continuous Integration pipeline
	$(call log_info,CI Pipeline...)
	@./scripts/ci-check.sh
	@sha256sum $(DEB_FILE) > $(DEB_FILE).sha256
	@md5sum $(DEB_FILE) > $(DEB_FILE).md5
	$(call log_success,CI Pipeline zakończone pomyślnie)


ci-check: ## Comprehensive CI checks
	$(call log_info,Uruchamianie comprehensive CI checks...)
	@./scripts/ci-check.sh
	$(call log_success,All CI checks passed)

info: ## Pokaż informacje o projekcie
	@echo "YouTube Downloader Build System"
	@echo "================================"
	@echo "Wersja:          $(VERSION)"
	@echo "Pakiet:          $(DEB_FILE)"
	@echo "Build script:    ./build-tools/build-deb.sh"
	@echo "Version manager: ./build-tools/version-manager.sh"
	@echo "Dokumentacja:    BUILDING.md"
	@echo ""
	@if [ -f "$(DEB_FILE)" ]; then \
		echo "Status pakietu:  ✅ Istnieje ($(shell ls -lh $(DEB_FILE) | awk '{print $$5}'))"; \
	else \
		echo "Status pakietu:  ❌ Nie istnieje"; \
	fi
	@echo ""
	@./build-tools/version-manager.sh show

# Debug cele
debug-version: ## Debug version manager
	@echo "=== Debug Version Manager ==="
	@echo "VERSION: $(VERSION)"
	@echo "DEB_FILE: $(DEB_FILE)"
	@echo ""
	@bash -x ./build-tools/version-manager.sh show

debug-build: ## Debug build script
	@echo "=== Debug Build Script ==="
	@DEBUG=1 ./build-tools/build-deb.sh

# Sprawdź czy wszystkie pliki istnieją przed budowaniem

$(DEB_FILE): launcher.py version.py requirements.txt build-tools/build-deb.sh
	@$(MAKE) build

# === DUAL-REPO WORKFLOW ===

sync-develop: ## Synchronizuj lokalne zmiany do private/develop
	$(call log_info,Synchronizacja local → private/develop...)
	@./scripts/sync-to-private.sh

sync-develop-force: ## Force sync do private/develop (nadpisuje konflikty)
	$(call log_info,Force sync local → private/develop...)
	@./scripts/sync-to-private.sh --force

promote: ## Promuj develop → main (private) z weryfikacją bezpieczeństwa
	$(call log_info,Promocja develop → main (private)...)
	@./scripts/promote-to-main.sh

promote-check: ## Sprawdź czy promocja jest możliwa (dry run)
	$(call log_info,Sprawdzanie możliwości promocji...)
	@./scripts/promote-to-main.sh --check-only

promote-squash: ## Promuj z squash commits
	$(call log_info,Promocja develop → main (squash)...)
	@./scripts/promote-to-main.sh --squash

release-public: ## Publikuj main private → main public (z automatycznym filtrowaniem .gitignore-public)
	$(call log_info,Publikacja main private → main public z filtrowaniem plików wrażliwych...)
	@./scripts/release-to-public.sh

release-public-verify: ## Sprawdź możliwość publikacji (dry run)
	$(call log_info,Weryfikacja publikacji...)
	@./scripts/release-to-public.sh --verify

sync-releases: ## Synchronizuj releases między repozytoriami
	$(call log_info,Synchronizacja releases...)
	@./scripts/sync-releases.sh --from george7979/youtube-downloader-private --to george7979/youtube-downloader

watch-releases: ## Monitoruj i auto-sync releases
	$(call log_info,Monitoring releases dla auto-sync...)
	@./scripts/sync-releases.sh --from george7979/youtube-downloader-private --to george7979/youtube-downloader --watch

sync-all: ## Pełny workflow: local → develop → main → public
	$(call log_info,🚀 PEŁNY WORKFLOW SYNCHRONIZACJI)
	@echo "=================================="
	@echo "1. Local → Private/develop"
	@$(MAKE) sync-develop
	@echo ""
	@echo "2. Develop → Main (private)"
	@$(MAKE) promote-check
	@read -p "Kontynuować promocję? (y/N): " -n 1 -r && echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) promote; \
	else \
		echo "Promocja anulowana"; exit 0; \
	fi
	@echo ""
	@echo "3. Main Private → Main Public"
	@$(MAKE) release-public-verify
	@read -p "Kontynuować publikację? (y/N): " -n 1 -r && echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) release-public; \
	else \
		echo "Publikacja anulowana"; exit 0; \
	fi
	$(call log_success,Pełny workflow zakończony!)

workflow-status: ## Sprawdź status wszystkich etapów workflow
	$(call log_info,Status Dual-Repo Workflow)
	@echo "=========================="
	@echo ""
	@echo "📍 Current branch: $$(git branch --show-current)"
	@echo "📍 Current commit: $$(git log --oneline -1)"
	@echo ""
	@echo "🔄 Repository Status:"
	@echo "   Local changes: $$(git status --porcelain | wc -l) files"
	@if git rev-parse --verify origin/develop >/dev/null 2>&1; then \
		echo "   Behind develop: $$(git rev-list --count HEAD..origin/develop 2>/dev/null || echo '0') commits"; \
		echo "   Ahead of develop: $$(git rev-list --count origin/develop..HEAD 2>/dev/null || echo '0') commits"; \
	else \
		echo "   Develop: not available"; \
	fi
	@if git rev-parse --verify origin/main >/dev/null 2>&1; then \
		echo "   Behind main: $$(git rev-list --count HEAD..origin/main 2>/dev/null || echo '0') commits"; \
		echo "   Ahead of main: $$(git rev-list --count origin/main..HEAD 2>/dev/null || echo '0') commits"; \
	else \
		echo "   Main: not available"; \
	fi
	@echo ""
	@echo "🏷️  Latest releases:"
	@if command -v gh >/dev/null 2>&1; then \
		echo "   Private: $$(gh release list --repo george7979/youtube-downloader-private --limit 1 2>/dev/null | cut -f3 || echo 'none')"; \
		echo "   Public:  $$(gh release list --repo george7979/youtube-downloader --limit 1 2>/dev/null | cut -f3 || echo 'none')"; \
	else \
		echo "   GitHub CLI not available"; \
	fi
	@echo ""
	@echo "🛠️  Available commands:"
	@echo "   make sync-develop      # Local → Private/develop"
	@echo "   make promote          # Develop → Main (private)"
	@echo "   make release-public   # Main → Public"
	@echo "   make sync-all         # Full workflow"

# Aliasy dla wygody
b: build
c: clean
t: test
i: install
v: version
s: sync-develop
p: promote
r: release-public
w: workflow-status