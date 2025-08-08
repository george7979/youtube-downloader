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

.PHONY: help build clean test install version check deps ci test-dual-repo ci-check push-private sync-public push-public

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
	@echo ""
	@dpkg --contents $(DEB_FILE) | head -15
	@echo ""
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

push-private: ## Wypchnij całe lokalne repo do private (łącznie z ignorowanymi); interaktywne potwierdzenia
	@./scripts/push-to-private.sh

sync-public: ## Przygotuj okrojony kod do publikacji w katalogu public-src/
	@./scripts/sync-to-public.sh

push-public: ## Opublikuj zawartość public-src/ do publicznego repo na GitHub
	@echo "ℹ️  Upewnij się, że masz tag w formacie vX.Y.Z (np. v$$(python3 -c 'ns={};exec(open("version.py").read(),ns);print(ns.get("__version__","0.0.0"))'))"
	@./scripts/sync-to-public-github.sh

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

bump-major: ## Zwiększ wersję major (1.0.3 -> 2.0.0)
	$(call log_info,Zwiększanie wersji major...)
	@./build-tools/version-manager.sh bump major
	$(call log_success,Wersja major zwiększona)

check: ## Sprawdź wymagania systemowe
	$(call log_info,Sprawdzanie wymagań...)
	@command -v dpkg-deb >/dev/null || { echo "❌ Brak dpkg-deb. Zainstaluj: apt-get install dpkg-dev"; exit 1; }
	@command -v fakeroot >/dev/null || { echo "❌ Brak fakeroot. Zainstaluj: apt-get install fakeroot"; exit 1; }
	@command -v python3 >/dev/null || { echo "❌ Brak python3"; exit 1; }
	@test -f main.py || { echo "❌ Brak main.py"; exit 1; }
	@test -f gui.py || { echo "❌ Brak gui.py"; exit 1; }
	@test -f downloader.py || { echo "❌ Brak downloader.py"; exit 1; }
	@test -f utils.py || { echo "❌ Brak utils.py"; exit 1; }
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

test-dual-repo: ## Test dual-repository workflow
	$(call log_info,Testowanie dual-repo workflow...)
	@./scripts/test-dual-repo.sh
	$(call log_success,Dual-repo workflow tests passed)

ci-check: ## Comprehensive CI checks
	$(call log_info,Uruchamianie comprehensive CI checks...)
	@./scripts/ci-check.sh
	$(call log_success,All CI checks passed)

info: ## Pokaż informacje o projekcie
	@echo "YouTube Downloader Build System"
	@echo "================================"
	@echo "Wersja:          $(VERSION)"
	@echo "Pakiet:          $(DEB_FILE)"
	@echo "Build script:    ./build-deb.sh"
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

# Zaawansowane cele
docker-build: ## Zbuduj w kontenerze Docker (wymaga Dockerfile)
	@if [ -f Dockerfile ]; then \
		$(call log_info,Budowanie w Docker...); \
		docker build -t $(PACKAGE_NAME)-builder .; \
		docker run --rm -v $(PWD):/workspace $(PACKAGE_NAME)-builder make build; \
		$(call log_success,Docker build zakończony); \
	else \
		$(call log_warning,Brak Dockerfile - pomijam Docker build); \
	fi

# Debug cele
debug-version: ## Debug version manager
	@echo "=== Debug Version Manager ==="
	@echo "VERSION: $(VERSION)"
	@echo "DEB_FILE: $(DEB_FILE)"
	@echo ""
	@bash -x ./build-tools/version-manager.sh show

debug-build: ## Debug build script
	@echo "=== Debug Build Script ==="
	@DEBUG=1 ./build-deb.sh

# Sprawdź czy wszystkie pliki istnieją przed budowaniem

$(DEB_FILE): main.py gui.py downloader.py utils.py requirements.txt build-tools/build-deb.sh
	@$(MAKE) build

# Aliasy dla wygody
b: build
c: clean
t: test
i: install
v: version