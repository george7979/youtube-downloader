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
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

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
  WriteRegStr   HKLM "${REG_KEY}" "Publisher"       "${PUBLISHER}"
  WriteRegStr   HKLM "${REG_KEY}" "URLInfoAbout"    "${WEBSITE}"
  WriteRegStr   HKLM "${REG_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr   HKLM "${REG_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegDWORD HKLM "${REG_KEY}" "NoModify"        1
  WriteRegDWORD HKLM "${REG_KEY}" "NoRepair"        1
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\${APP_EXE}"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir  "$INSTDIR"

  Delete "$SMPROGRAMS\YouTube Downloader\YouTube Downloader.lnk"
  Delete "$SMPROGRAMS\YouTube Downloader\Uninstall.lnk"
  RMDir  "$SMPROGRAMS\YouTube Downloader"
  Delete "$DESKTOP\YouTube Downloader.lnk"

  DeleteRegKey HKLM "${REG_KEY}"

  ; Remove downloaded tools (yt-dlp, ffmpeg, Deno); keep settings and logs.
  ; The uninstaller runs elevated, so $LOCALAPPDATA is the profile of the account it runs as;
  ; if a standard user elevated with another account's credentials, their own tools stay.
  SetShellVarContext current
  RMDir /r "$LOCALAPPDATA\YouTube Downloader\tools"
SectionEnd
