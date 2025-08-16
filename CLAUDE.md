# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a Python-based YouTube downloader application with a Tkinter GUI and sophisticated dual-repository architecture.

### Core Components
- **main.py** - Application entry point with logging setup and window initialization
- **gui.py** - Complete Tkinter interface with progress tracking, format selection, and configuration persistence
- **downloader.py** - YouTube download logic using yt-dlp with multiple fallback client configurations (Android TV, Android, iOS)
- **utils.py** - Shared utilities for filename sanitization, URL validation, timestamp extraction, and logging configuration
- **version.py** - Centralized version management (currently 1.0.3)

### Dual-Repository Structure
This project uses a unique dual-repo setup for separating private development from public distribution:

- **Private repo (this one)** - Full development environment with build tools, scripts, and .deb packages
- **Public repo** - Sanitized subset synchronized from `public-src/` directory via `make sync-public`
- **Symlinks** - Root-level Python files are symlinked to `public-src/` versions for consistency
- **Distribution** - `.deb` packages and sensitive development files stay in private repo only

Key dual-repo commands:
- `make sync-public` - Sync sanitized code to `public-src/` for public release
- `make push-public` - Push `public-src/` content to GitHub public repository  
- `make push-private` - Push complete private state (including .deb files) to private repo

## Essential Development Commands

### Setup and Verification
```bash
# First time setup - verify environment and install build dependencies
make check              # Verify all required tools and files exist
make deps               # Install build dependencies (dpkg-dev, fakeroot, etc.)
make info               # Show project status and current version

# Quick project verification
pwd && ls -la           # Always verify you're in the correct project directory
```

### Build and Test Workflow
```bash
# Standard development cycle
make build              # Build .deb package from current code
make test               # Test the built package (dpkg info, lintian check)
make install            # Install package locally for testing
make uninstall          # Remove installed package

# Version management
make version            # Show current version
make bump-patch         # Increment patch version (1.0.3 -> 1.0.4)
make bump-minor         # Increment minor version (1.0.3 -> 1.1.0) 
make bump-major         # Increment major version (1.0.3 -> 2.0.0)

# Full release workflow
make release            # Complete release: clean + bump-patch + build + test
```

### Continuous Integration
```bash
make ci                 # Full CI pipeline: clean + check + build + test + checksums
make ci-check           # Comprehensive CI validation checks
make test-dual-repo     # Validate dual-repository workflow integrity
```

### Testing & Quality Assurance

For comprehensive testing procedures including:
- User Acceptance Testing (UAT) workflows
- Version-specific testing checklists  
- Quality gates and approval criteria
- User feedback templates and issue tracking

See [`docs/TESTING_CHECKLIST.md`](docs/TESTING_CHECKLIST.md)

The `make test` command performs technical package validation (dpkg info, lintian checks).
Full UAT procedures should follow the comprehensive checklist documentation.

### Development Environment
```bash
# Python environment (if developing outside .deb packaging)
python3 -m venv .venv
source .venv/bin/activate
pip install -r public-src/requirements.txt

# Run application directly
python3 public-src/main.py

# Run installed version
youtube-downloader
```

## Technical Implementation Details

### YouTube Download Strategy
The downloader implements a robust fallback system using yt-dlp with multiple client configurations:
1. **Android TV Client** - Primary choice for stability
2. **Android Client** - Fallback with player config skipping  
3. **iOS Client** - Additional fallback option
4. **Web Client** - Last resort fallback

Each configuration includes specific user agents and extractor arguments optimized for bypassing YouTube's anti-bot measures.

### GUI Architecture
- **Threading** - All downloads run in separate threads to prevent UI freezing
- **Progress Tracking** - Real-time download progress with cancel functionality
- **Configuration Persistence** - Automatic saving/loading of last used directory and settings
- **Format Selection** - Dynamic quality sorting from highest to lowest resolution
- **Cross-platform Paths** - Robust file path handling for different Linux distributions

### Packaging System
- **Debian Package** - Self-contained .deb with isolated virtual environment
- **Desktop Integration** - Automatic .desktop file creation for application menu
- **Dependency Management** - Automatic resolution of system dependencies
- **Clean Uninstall** - Complete removal including virtual environment

## Code Style and Conventions

### File Organization
- All source code uses Polish comments and documentation for local development
- Function/variable names in English for code maintainability
- Comprehensive error handling with user-friendly Polish messages
- Logging configured for both console and file output (`/tmp/youtube_downloader.log`)

### Version Management
Version numbers are managed centrally in `version.py` and automatically propagated to:
- `debian-src/changelog` for package metadata
- `README.md` for documentation consistency
- All build scripts and package generation

### Git Workflow
The dual-repo setup requires specific Git patterns:
- Private repo contains full development history and .deb packages
- Public repo receives only sanitized releases via `make push-public`
- Never commit sensitive development files to public repo
- Use version tags consistently: `v1.0.3` format for releases

## Legal and Compliance Framework

This application implements a comprehensive legal compliance structure for YouTube content downloading:

### Built-in Legal Safeguards
- Prominent legal disclaimers in README.md and application interface
- Clear delineation of allowed vs. prohibited usage scenarios
- User responsibility enforcement for copyright compliance
- Reference to YouTube Terms of Service and API guidelines

### Allowed Use Cases (as documented)
- Downloading user's own YouTube content
- Creative Commons and public domain content
- Personal backup of owned materials
- Educational fair use scenarios

The application itself is legally neutral - responsibility lies entirely with the end user for compliance with copyright law and platform terms of service.