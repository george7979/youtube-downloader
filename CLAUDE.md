# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture v1.2.0

This is a Python-based YouTube downloader application with intelligent launcher, modular architecture, and enhanced cross-platform support.

### Intelligent Launcher System
- **launcher.py** - Smart entry point with automatic GUI/CLI detection and environment diagnostics
- **Environment Detection** - Automatic detection of WSL, DISPLAY availability, and Tkinter support
- **Graceful Fallback** - Seamless transition from GUI to CLI when GUI is unavailable

### Modular Architecture
- **core/** - Business logic separation
  - **downloader.py** - YouTube download engine with multiple fallback client configurations (Android TV, Android, iOS)
  - **utils.py** - Shared utilities for filename sanitization, URL validation, timestamp extraction
  - **translations.py** - Internationalization support
- **ui/** - User interface modules
  - **gui.py** - Complete Tkinter interface with progress tracking and configuration persistence
  - **cli.py** - Command-line interface with interactive prompts and safe input handling
- **version.py** - Centralized version management (currently 1.2.0)

### Dual-Repository Architecture (v1.2.0)
This project uses a dual-repository approach with staged deployment workflow:

- **Private Repository** - Complete development environment with all source code
  - **Develop branch** - Active development and testing (current v1.2.0 work)
  - **Main branch** - Stable releases ready for public distribution
  - **Feature branches** - Individual feature development
- **Public Repository** - Clean distribution version for end users
  - Synchronized from private/main branch
  - Contains only user-essential files
  - No development artifacts or sensitive configuration

## Intelligent Launcher Architecture

### Entry Point Flow
1. **launcher.py** - Main entry point for all execution
2. **Environment Detection** - Checks DISPLAY, Tkinter, WSL status
3. **Interface Selection** - Chooses GUI or CLI automatically
4. **Graceful Fallback** - Seamless degradation when GUI unavailable

### Diagnostic Capabilities
```bash
python3 launcher.py --test  # Environment diagnostics
youtube-downloader --test   # Post-installation diagnostics
```

### Cross-Platform Support
- **Native Linux** - Full GUI experience with Tkinter
- **WSL/WSL2** - Intelligent GUI support with automatic DISPLAY configuration and CLI fallback
- **Headless** - Pure CLI mode for server environments
- **SSH/Remote** - Intelligent detection of terminal-only environments

### WSL GUI Support (v1.2.0)
The launcher includes specialized WSL support:
- **Auto DISPLAY detection** - Automatically sets `DISPLAY=:0` if not configured
- **WSL-optimized window handling** - Uses visibility forcing for GUI windows
- **Graceful fallback** - Seamless transition to CLI if GUI fails
- **Process protection** - Timeout mechanisms prevent hanging processes

For detailed WSL troubleshooting, see [`docs/WSL_TROUBLESHOOTING.md`](docs/WSL_TROUBLESHOOTING.md)

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

### Build and Test Workflow (v1.2.0)
```bash
# Modern build system
./build-tools/build-deb.sh     # Build .deb package with dual-repo architecture
python3 launcher.py --test     # Test intelligent launcher diagnostics

# Testing different modes
youtube-downloader --test      # Environment diagnostics (after install)
youtube-downloader --cli       # Force CLI mode
youtube-downloader             # Auto-detect mode

# Version management (via version.py)
echo "Current: $(python3 -c 'from version import __version__; print(__version__)')"

# Package validation
dpkg --info youtube-downloader_1.2.0_all.deb
dpkg --contents youtube-downloader_1.2.0_all.deb
```

### Continuous Integration
```bash
make ci                 # Full CI pipeline: clean + check + build + test + checksums
make ci-check           # Comprehensive CI validation checks
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
pip install -r requirements.txt

# Run application directly
python3 launcher.py

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
- Source code uses English comments and documentation
- Function/variable names in English for maintainability
- Comprehensive error handling with user-friendly messages
- Logging configured for both console and file output (`/tmp/youtube_downloader.log`)

### Version Management
Version numbers are managed centrally in `version.py` and automatically propagated to:
- `debian-src/changelog` for package metadata
- `README.md` for documentation consistency
- All build scripts and package generation

### Git Workflow (Dual-Repository v1.2.0)
The dual-repository approach follows a staged deployment pattern:

#### Development Workflow
- **Private/develop** - Active development and feature work
- **Private/main** - Stable releases before public distribution
- **Feature branches** - Individual enhancements merged to develop
- **Public/main** - Synchronized from private/main for end users

#### Workflow Scripts
- `scripts/sync-to-private.sh` - Sync local changes to private/develop
- `scripts/promote-to-main.sh` - Promote develop to main (with security validation)
- `scripts/release-to-public.sh` - Release main to public repository
- `scripts/sync-releases.sh` - Synchronize GitHub releases between repositories

#### Deployment Pipeline
1. **Local → Private/develop** - Daily development synchronization
2. **Private/develop → Private/main** - Promotion after testing and validation
3. **Private/main → Public/main** - Clean release distribution

## Documentation Principles

### User-Focused Documentation Strategy
This project follows strict documentation principles to ensure optimal user experience:

#### README.md Guidelines
- **User-Only Content** - README.md contains ONLY information essential for end users
- **No Technical Details** - Development, testing, and contribution information excluded
- **Simple Language** - Clear, straightforward instructions without technical jargon
- **Focus Areas** - Installation, usage, troubleshooting, legal compliance

#### Technical Documentation Separation
- **CLAUDE.md** - Development guidance for Claude Code (this file)
- **docs/BUILDING.md** - Build and deployment procedures
- **docs/TESTING_CHECKLIST.md** - Quality assurance workflows
- **docs/WORKFLOW.md** - Dual-repository workflow details
- **PRD.md** - Product requirements and specifications

#### Implementation Rule
**CRITICAL**: When updating documentation, always ensure README.md remains user-focused. Technical implementation details, development workflows, and contribution guidelines belong in separate technical documentation files, never in README.md.

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