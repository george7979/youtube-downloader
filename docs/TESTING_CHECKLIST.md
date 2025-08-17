# Testing Checklist & User Acceptance Workflow

## Overview

This document provides comprehensive testing procedures for YouTube Downloader releases, with specific focus on user acceptance testing (UAT) and quality validation workflows.

## 📋 Version-Specific Testing

### v1.1.0 English Internationalization Testing Checklist

#### **Pre-Installation Setup**
- [ ] **Backup current version**: Note current version with `youtube-downloader --help` or check installed packages
- [ ] **Clean environment**: Remove previous version if testing clean install
- [ ] **Document baseline**: Screenshot current Polish UI (if available)

#### **Installation Testing**
- [ ] **Package integrity**: `dpkg --info youtube-downloader_1.1.0_all.deb`
- [ ] **Install package**: `sudo dpkg -i youtube-downloader_1.1.0_all.deb`
- [ ] **Dependency resolution**: `sudo apt-get install -f` (should report no additional packages)
- [ ] **Binary availability**: `which youtube-downloader` returns `/usr/bin/youtube-downloader`
- [ ] **Version verification**: Application shows v1.1.0 in title or about dialog

#### **UI Translation Testing**

##### **Main Interface Elements**
- [ ] **Window title**: Shows "YouTube Downloader" (English/unchanged)
- [ ] **URL input section**: All labels in English
- [ ] **Check button**: Says "Check" (not "Sprawdź")
- [ ] **Video info panel**: Headers show "Title:", "Duration:", "Available formats:" in English
- [ ] **Resolution dropdown**: Label shows "Resolution:" in English
- [ ] **Audio checkbox**: Shows "Audio only (MP3)" in English
- [ ] **Folder selection**: Button shows "Select Folder" in English
- [ ] **Download button**: Shows "Start Download" in English
- [ ] **Cancel button**: Shows "Cancel" in English
- [ ] **Progress section**: "Download" header in English

##### **Status Messages Testing**
Test each status message by triggering appropriate actions:

- [ ] **Video checking**: Status shows "Video checked" after successful URL validation
- [ ] **Download progress**: Shows "Downloading... X%" during download
- [ ] **Download complete**: Shows "Download complete" when finished
- [ ] **Download cancelled**: Shows "Download cancelled" when stopped mid-download

##### **Error Messages Testing**
Trigger error conditions to verify English error messages:

- [ ] **Invalid URL**: Enter invalid URL → Error shows in English
- [ ] **No folder selected**: Try download without folder → "Select destination folder"
- [ ] **No video checked**: Try download without checking → "Check the video first"
- [ ] **Network error**: Disconnect internet → Network error in English
- [ ] **Application startup error**: Test startup error dialog in English

##### **Dialog Boxes Testing**
- [ ] **Success dialog**: Complete download → "Success" title with English message
- [ ] **Folder selector**: "Select Folder" dialog opens with standard system dialog
- [ ] **Error dialogs**: All error popups show English titles and messages

##### **Default Text Testing**
- [ ] **No folder selected**: Initially shows "No folder selected" in English
- [ ] **Empty info panel**: Before video check, info area shows appropriate English placeholders
- [ ] **Unknown values**: When video info unavailable, shows "Unknown" in English

#### **Functional Regression Testing**
Verify v1.1.0 maintains all v1.0.3 functionality:

##### **Core Download Features**
- [ ] **URL validation**: Paste YouTube URL → Check button validates correctly
- [ ] **Video info retrieval**: Get title, duration, formats in English
- [ ] **Resolution selection**: Dropdown populates with available resolutions
- [ ] **Audio-only download**: Checkbox enables MP3-only download
- [ ] **Folder persistence**: Selected folder remembered between sessions
- [ ] **Download progress**: Progress bar updates correctly during download
- [ ] **Download cancellation**: Cancel button stops download mid-process

##### **File Operations**
- [ ] **Video download**: MP4 files download with correct names
- [ ] **Audio download**: MP3 files extract correctly with good quality
- [ ] **File naming**: Sanitized filenames work correctly
- [ ] **Destination folders**: Files save to selected directories
- [ ] **Timestamp extraction**: If applicable, timestamps save correctly

##### **Error Handling**
- [ ] **Invalid URLs**: Graceful error handling for bad URLs
- [ ] **Network issues**: Proper timeout and retry behavior
- [ ] **Disk space**: Appropriate error if insufficient space
- [ ] **Permission errors**: Clear message for folder permission issues

#### **Cross-Platform Testing** (if applicable)
- [ ] **Ubuntu 20.04**: Test on Ubuntu 20.04 LTS
- [ ] **Ubuntu 22.04**: Test on Ubuntu 22.04 LTS  
- [ ] **Debian**: Test on latest Debian stable
- [ ] **Different desktop environments**: Test on GNOME, KDE, XFCE

#### **Performance & Stability Testing**
- [ ] **Startup time**: Application launches within 3 seconds
- [ ] **Memory usage**: No significant memory leaks during downloads
- [ ] **UI responsiveness**: Interface remains responsive during downloads
- [ ] **Multiple downloads**: Handle multiple sequential downloads correctly
- [ ] **Long URLs**: Handle very long YouTube URLs correctly
- [ ] **Special characters**: Handle videos with special characters in titles

#### **Uninstallation Testing**
- [ ] **Clean removal**: `sudo dpkg -r youtube-downloader`
- [ ] **Files cleanup**: Verify installed files removed
- [ ] **Configuration**: User config files appropriately handled
- [ ] **Dependencies**: System dependencies left in clean state

---

## 🔄 General Release Testing Workflow

### Phase 1: Pre-Release Validation (Developer)
1. **Code Review**: All code changes reviewed and approved
2. **Automated Testing**: CI pipeline passes completely
3. **Build Verification**: Package builds successfully
4. **Static Analysis**: No critical linting or security issues

### Phase 2: Technical Testing (Developer/QA)
1. **Installation Testing**: Clean install/uninstall cycle
2. **Functional Testing**: All features work as specified
3. **Regression Testing**: Previous functionality unaffected
4. **Documentation**: README and docs updated appropriately

### Phase 3: User Acceptance Testing (Product Owner/Users)
1. **Feature Validation**: New features work as specified
2. **User Experience**: Interface changes meet usability standards
3. **Performance**: Application meets performance requirements
4. **Compatibility**: Works on target platforms and configurations

### Phase 4: Release Approval
1. **Sign-off Criteria**:
   - All critical and high-priority issues resolved
   - User acceptance testing passes with 4.0/5.0 rating minimum
   - No regressions from previous version
   - Documentation complete and accurate

2. **Approval Matrix**:
   - **Developer**: Technical implementation complete
   - **Product Owner**: Feature requirements met
   - **QA**: Testing criteria satisfied
   - **Community**: Feedback incorporated (for major releases)

### Phase 5: Release Deployment
1. **Final Package**: Create final release package
2. **Release Notes**: Document all changes and known issues
3. **Distribution**: Deploy to repositories and GitHub releases
4. **Communication**: Announce release to users

---

## 📊 Testing Templates

### User Feedback Form Template
```
**Version Tested**: v1.1.0
**System**: Ubuntu XX.XX / Debian XX
**Installation Method**: .deb package / other

**Overall Rating**: [1-5 stars]

**Translation Quality**:
- Accuracy: [1-5]
- Consistency: [1-5] 
- Completeness: [1-5]

**Functionality**:
- Download features: [Working/Issues]
- User interface: [Working/Issues]
- Error handling: [Working/Issues]

**Issues Found**:
- [ ] Critical (prevents use)
- [ ] Major (significant impact)
- [ ] Minor (cosmetic/small)
- [ ] Enhancement (suggestion)

**Detailed Feedback**:
[Free text for specific issues, suggestions, or praise]

**Recommendation**: 
- [ ] Approve for release
- [ ] Approve with minor fixes
- [ ] Requires major fixes before release
- [ ] Not ready for release
```

### Issue Tracking Template
```
**Issue ID**: YTDL-XXXX
**Severity**: Critical/Major/Minor/Enhancement
**Component**: UI/Download/Installation/Documentation
**Version**: v1.1.0
**Environment**: Ubuntu XX.XX

**Description**:
[Clear description of the issue]

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Result**:
[What should happen]

**Actual Result**:
[What actually happened]

**Workaround**: 
[If any workaround exists]

**Status**: Open/In Progress/Resolved/Verified
```

---

## 🎯 Quality Gates

### Release Readiness Criteria

#### **v1.1.0 Specific Gates**
- [ ] **Translation Completeness**: 100% of UI strings translated
- [ ] **Translation Accuracy**: No grammatical errors or mistranslations
- [ ] **Functional Regression**: Zero functionality lost from v1.0.3
- [ ] **Performance**: No performance degradation >10%
- [ ] **User Testing**: Minimum 3 users complete testing checklist
- [ ] **Average Rating**: 4.0/5.0 minimum from user testing
- [ ] **Critical Issues**: Zero critical bugs open
- [ ] **Documentation**: All docs updated for English UI

#### **General Release Gates**
- [ ] **Build Quality**: Package builds cleanly without warnings
- [ ] **Installation**: Installs/uninstalls cleanly on target platforms
- [ ] **Dependencies**: All dependencies properly declared and available
- [ ] **Security**: No security vulnerabilities introduced
- [ ] **Legal**: All licensing and legal requirements met

### Post-Release Monitoring

#### **Success Metrics (30 days post-release)**
- Download success rate: >95%
- User satisfaction: >4.0/5.0 average
- Support ticket volume: <5% increase
- Adoption rate: >25% of active users upgrade

#### **Rollback Triggers**
- Critical security vulnerability discovered
- >10% regression in core functionality
- User satisfaction drops below 3.0/5.0
- Support ticket volume increases >50%

---

## 📝 Documentation Updates

When using this checklist, ensure:

1. **Version Documentation**: Update version-specific sections for each release
2. **Feedback Integration**: Incorporate user feedback into next release planning
3. **Process Improvement**: Update procedures based on lessons learned
4. **Metric Tracking**: Maintain records of testing results and user feedback

---

*This checklist should be completed for every release. Mark items with ✅ when verified and ❌ when issues are found. Document all issues in the project issue tracker with appropriate severity levels.*

**Document Version**: 1.2  
**Last Updated**: August 2025  
**Next Review**: Before v1.2.0 release