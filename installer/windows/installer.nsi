; YouTube Downloader NSIS Installer
; Usage: makensis /DAPP_VERSION=2.0.0 installer\windows\installer.nsi
; Run from project root after PyInstaller build

; Change compiler working directory to repo root (script lives in installer\windows\)
!cd "..\.."

!ifndef APP_VERSION
  !define APP_VERSION "2.0.0"
!endif

!define APP_NAME      "YouTube Downloader"
!define APP_EXE       "youtube-downloader.exe"
!define PUBLISHER     "Jerzy Maczewski"
!define WEBSITE       "https://github.com/george7979/youtube-downloader"
!define INSTALL_DIR   "$PROGRAMFILES64\YouTube Downloader"
!define REG_KEY       "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeDownloader"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "installer\windows\youtube-downloader-${APP_VERSION}-setup.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "${REG_KEY}" "InstallLocation"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_ICON   "icons\youtube-downloader.ico"
!define MUI_UNICON "icons\youtube-downloader.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
; "Run YouTube Downloader" on the finish page, ticked by default. The installer runs elevated;
; starting the app through Explorer runs it as the signed-in user, so its settings and tools
; land in that user's profile instead of an elevated one.
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Run ${APP_NAME}"
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchApp
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function LaunchApp
  Exec '"$WINDIR\explorer.exe" "$INSTDIR\${APP_EXE}"'
FunctionEnd

Section "Main" SecMain
  SetOutPath "$INSTDIR"
  File "dist\youtube-downloader.exe"

  CreateDirectory "$SMPROGRAMS\YouTube Downloader"
  CreateShortcut "$SMPROGRAMS\YouTube Downloader\YouTube Downloader.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\YouTube Downloader\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\YouTube Downloader.lnk" "$INSTDIR\${APP_EXE}"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr   HKLM "${REG_KEY}" "DisplayName"     "${APP_NAME}"
  WriteRegStr   HKLM "${REG_KEY}" "DisplayVersion"  "${APP_VERSION}"
  ; Settings > Apps shows a blank icon without this.
  WriteRegStr   HKLM "${REG_KEY}" "DisplayIcon"     "$INSTDIR\${APP_EXE},0"
  WriteRegStr   HKLM "${REG_KEY}" "Publisher"       "${PUBLISHER}"
  WriteRegStr   HKLM "${REG_KEY}" "URLInfoAbout"    "${WEBSITE}"
  WriteRegStr   HKLM "${REG_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr   HKLM "${REG_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegDWORD HKLM "${REG_KEY}" "NoModify"        1
  WriteRegDWORD HKLM "${REG_KEY}" "NoRepair"        1
SectionEnd

Section "Uninstall"
  ; RMDir cannot remove the uninstaller's own working directory.
  SetOutPath "$TEMP"
  Delete "$INSTDIR\${APP_EXE}"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir  "$INSTDIR"

  Delete "$SMPROGRAMS\YouTube Downloader\YouTube Downloader.lnk"
  Delete "$SMPROGRAMS\YouTube Downloader\Uninstall.lnk"
  RMDir  "$SMPROGRAMS\YouTube Downloader"
  Delete "$DESKTOP\YouTube Downloader.lnk"

  DeleteRegKey HKLM "${REG_KEY}"

  ; Remove everything the app keeps per user: tools (yt-dlp, ffmpeg, Deno) and logs in
  ; Local, settings and the recent list in Roaming. Downloaded videos and notes live in the
  ; folder the user chose and are never touched. Installing a new version over an old one
  ; does not run this section, so upgrades keep the settings.
  ; The uninstaller runs elevated, so these are the folders of the account it runs as;
  ; if a standard user elevated with another account's credentials, their own data stays.
  SetShellVarContext current
  RMDir /r "$LOCALAPPDATA\YouTube Downloader"
  RMDir /r "$APPDATA\YouTube Downloader"
SectionEnd
