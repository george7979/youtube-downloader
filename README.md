# YouTube Downloader

Simple Python application for downloading videos from YouTube with a graphical interface.

![YouTube Downloader Interface](pics/youtube-downloader-3.png)

## ✨ Features

- 📥 **Download videos** from YouTube and other platforms
- 🎨 **Intuitive graphical** interface
- 📊 **Quality selection** for video and audio
- 📁 **Remember download path** between sessions
- ⚡ **Fast and stable** operation

## ⚠️ Legal Notice

**This application is a technical tool. The user is responsible for the legality of downloading content.**

### ✅ Allowed use:
- Your own YouTube content (authors can download their own videos)
- Content under Creative Commons licenses, public domain
- Backup of your own materials
- Educational use within fair use

### ❌ Prohibited use:
- Downloading others' content without author's consent
- Commercial distribution of downloaded content
- Copyright infringement

**Respect copyright and [YouTube Terms of Service](https://www.youtube.com/t/terms).**

## 🛠️ Installation

### System requirements
- **Linux:** Ubuntu 22.04+ / Debian 12+
- **Windows:** Windows 10 / 11

### Linux — .deb package

1. Download `youtube-downloader_X.X.X_amd64.deb` from [Releases](https://github.com/george7979/youtube-downloader/releases)

2. Install:
   ```bash
   sudo dpkg -i youtube-downloader_*.deb
   ```

3. Run:
   ```bash
   youtube-downloader
   ```

### Windows — installer (.exe)

1. Download `youtube-downloader-X.X.X-setup.exe` from [Releases](https://github.com/george7979/youtube-downloader/releases)

2. Run the installer — it will create a Start Menu shortcut and a desktop icon.

> **⚠️ Windows SmartScreen warning**
>
> The installer is **not digitally signed** (code signing certificates cost ~$300/year).
> Windows may show a "Windows protected your PC" warning.
>
> To install anyway:
> 1. Click **"More info"**
> 2. Click **"Run anyway"**
>
> The application is open source — you can review the full source code in this repository.

## 🚀 Running

**Linux:**
```bash
youtube-downloader
```

**Windows:** Use the Start Menu shortcut or desktop icon.

## 🎮 How to use

### 1. Launch the application
```bash
youtube-downloader
```

### 2. Paste YouTube link
Enter the video URL in the text field.

### 3. Check video
Click "Check" to retrieve video information.

### 4. Select options
- **Audio only**: Check for MP3 download
- **Quality**: Choose resolution from the list
- **Folder**: Click "Select Folder" to choose directory

### 5. Download
Click "Download" to start downloading.

## 🔧 Troubleshooting

### Application won't start:
```bash
sudo apt reinstall youtube-downloader
```

### Installation errors:
```bash
sudo apt-get install -f
sudo dpkg -i youtube-downloader_*.deb
```

### Download errors:
- Check internet connection
- Make sure the link is correct
- Some videos may be regionally blocked

## 🗑️ Uninstallation

```bash
# Standard uninstallation
sudo dpkg -r youtube-downloader

# Complete removal with configuration
sudo dpkg -P youtube-downloader
```

## 🐛 Reporting issues

Found a bug? Have a feature suggestion?

**Report in GitHub Issues:** https://github.com/george7979/youtube-downloader/issues

