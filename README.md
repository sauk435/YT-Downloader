<div align="center">
  <img src="icon.png" alt="YouTube Downloader Icon" width="160"/>
  <h1>YouTube Downloader for Windows</h1>
  <p align="center">
    <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue?logo=windows" alt="Windows Support">
    <img src="https://img.shields.io/badge/Version-1.0.0-red" alt="Version">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python Version">
    <img src="https://img.shields.io/badge/UI-CustomTkinter-blueviolet" alt="CustomTkinter">
    <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  </p>
  <p>A modern, fast, and feature-packed desktop application to search, trim, and download YouTube videos and music on Windows.</p>
</div>

---

## 🌟 Features

- 🎬 **High-Quality Video & Audio:** Download in up to 4K resolution (MP4) or extract crystal-clear 192 kbps audio (MP3) powered by `yt-dlp` and `ffmpeg`.
- ✂️ **Built-in Trimmer:** Crop videos directly before downloading with an interactive dual-handle timeline slider.
- 🔍 **Integrated Search & Playlists:** Search YouTube directly from the app or paste any video, Short, or full playlist URL.
- 👶 **YouTube Kids & Restricted Video Support:** Optimized extraction engine using Android client APIs to reliably bypass format restrictions on children's videos.
- 📁 **Direct Destination Folder Selection:** Choose or change your target download folder at any time right from the main window.
- 📜 **Download History:** Review past downloads with exact file locations, direct buttons to open files or folders, and file deletion controls.
- 🖥️ **Background Downloads (Installed):** Minimizes smoothly to the Windows System Tray so long downloads can finish while you work.
- 🚀 **Zero-Traces Portable Mode:** A fully self-contained portable executable that closes immediately when you exit, without leaving background processes.
- 🌐 **Multilingual & Themed:** Full Spanish and English support, complete with dark and light themes built on CustomTkinter.

---

## 📥 Download & Usage (For Users)

You can find both editions ready to use in the **`Release/`** folder:

### 1. Standalone Portable (`YT Downloader Portable.exe`)
* **No installation required.** Double-click and use immediately.
* Completely terminates when closed (no tray or background services).

### 2. Full Installer (`YT Downloader Instalador.exe`)
* Setup wizard with desktop shortcut and start menu options.
* Supports **background downloading** via the Windows System Tray.
* Clean uninstaller that automatically terminates active tasks and removes all installed components.

> **Note:** If Windows SmartScreen displays an unrecognized app warning on the first run, click **"More info" (Más información)** > **"Run anyway" (Ejecutar de todas formas)**.

---

## 💻 Development & Building (For Developers)

### 1. Requirements
* Windows 10 or 11
* Python 3.10+
* Inno Setup 6 (optional, for compiling the installer wizard)

### 2. Local Setup
```bash
# 1. Clone the repository
git clone https://github.com/sauk435/youtube-downloader.git
cd youtube-downloader

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the application
python YouTubeDownloader.pyw
```

### 3. Build Executables

#### Build Portable Edition
```bash
pyinstaller -y --name "YT Downloader Portable" --icon=icon.ico --add-data "icon.ico;." --noconsole --onefile --distpath "Release" --collect-all customtkinter --collect-all yt_dlp --collect-all imageio_ffmpeg YouTubeDownloader.pyw
```

#### Build Installer Edition
1. Package source files:
   ```bash
   pyinstaller -y --name "YT Downloader" --icon=icon.ico --add-data "icon.ico;." --noconsole --onedir --distpath "TempSource" --collect-all customtkinter --collect-all yt_dlp --collect-all imageio_ffmpeg YouTubeDownloader.pyw
   ```
2. Compile setup wizard with Inno Setup:
   ```bash
   ISCC.exe installer.iss
   ```

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
