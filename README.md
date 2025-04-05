<div align="center">
  <img src="InvisioVault.ico" alt="InvisioVault Logo" width="200">
  <h1>InvisioVault</h1>
  <p><em>Secure File Hiding with Military-Grade Encryption</em></p>

  ![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
  ![License](https://img.shields.io/badge/license-MIT-green.svg)
  ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
</div>

<p align="center">
  InvisioVault is a professional steganography application that securely hides various file types (PDF, media, documents, etc.) within image files using AES-256 encryption. Perfect for discreet data storage and privacy-conscious users.
</p>

## 📋 Table of Contents
- [✨ Features](#-features)
- [🖼️ Screenshots](#-screenshots)
- [🚀 Installation](#-installation)
- [📝 Usage Guide](#-usage-guide)
- [🔨 Building from Source](#-building-from-source)
- [🔒 Security](#-security)
- [⚠️ Disclaimer](#-disclaimer)

## ✨ Features

<div align="center">
  <table>
    <tr>
      <td width="50%">
        <ul>
          <li>📁 <strong>Multi-Format Support</strong> - Hide PDFs, documents, media files, and more</li>
          <li>🔐 <strong>Military-Grade Encryption</strong> - AES-256 password protection</li>
          <li>🖼️ <strong>Image Formats</strong> - PNG, JPG, BMP support</li>
          <li>🔄 <strong>Batch Processing</strong> - Hide/extract multiple files at once</li>
        </ul>
      </td>
      <td width="50%">
        <ul>
          <li>📊 <strong>History Tracking</strong> - Detailed operation logs</li>
          <li>✅ <strong>File Integrity</strong> - Automatic checksum verification</li>
          <li>⚡ <strong>Quick Setup</strong> - Single executable build</li>
          <li>🔍 <strong>User-Friendly Interface</strong> - Intuitive design for all users</li>
        </ul>
      </td>
    </tr>
  </table>
</div>

## 🖼️ Screenshots

<div align="center">
  <h3>Welcome Screen</h3>
  <img src="./screenshots/First_page.png" alt="Welcome Screen" width="80%">
  <p><em>The application's main interface provides easy access to all features</em></p>

  <h3>Hide Files</h3>
  <img src="./screenshots/Hide_files.png" alt="File Hiding Interface" width="80%">
  <p><em>Securely hide your sensitive files within innocent-looking images</em></p>

  <h3>Extract Files</h3>
  <img src="./screenshots/Extract_files.png" alt="File Extraction" width="80%">
  <p><em>Easily retrieve your hidden files with password protection</em></p>

  <h3>Operation History</h3>
  <img src="./screenshots/History.png" alt="Operation History" width="80%">
  <p><em>Keep track of all your hide and extract operations</em></p>

  <h3>About & Disclaimer</h3>
  <img src="./screenshots/About.png" alt="About Section" width="80%">
  <p><em>Application information and legal disclaimer</em></p>
</div>

## 🚀 Installation

### Quick Start (Prebuilt Executable)
1. Download the latest release from the [Releases page]
2. Double-click `InvisioVault.exe` from the `dist` folder
3. No installation required - runs immediately!

### From Source
```bash
git clone https://github.com/yourusername/InvisioVault.git
cd InvisioVault
pip install -r requirements.txt
python build.bat
```

## 📝 Usage Guide

<div align="center">
  <table>
    <tr>
      <th>Hiding Files</th>
      <th>Extracting Files</th>
    </tr>
    <tr>
      <td>
        <ol>
          <li>Launch InvisioVault</li>
          <li>Select "Hide Files" operation</li>
          <li>Choose a carrier image</li>
          <li>Select file(s) to hide</li>
          <li>Set a strong password</li>
          <li>Click "Hide Files"</li>
        </ol>
      </td>
      <td>
        <ol>
          <li>Launch InvisioVault</li>
          <li>Select "Extract Files" operation</li>
          <li>Select the image with hidden content</li>
          <li>Enter the correct password</li>
          <li>Choose extraction location</li>
          <li>Click "Extract Files"</li>
        </ol>
      </td>
    </tr>
  </table>
</div>

## 🔨 Building from Source

1. Install [Python 3.8+](https://python.org)
2. Clone the repository
3. Run `build.bat` to:
   - Install dependencies
   - Create standalone executable
   - Generate application icon
4. Find executable in `dist` folder

### System Requirements

- Windows operating system
- Python 3.8 or higher (for building from source)
- Required Python packages (see requirements.txt)

## 🔒 Security

InvisioVault uses AES-256 encryption to secure your hidden files. Even if someone discovers that an image contains hidden data, they cannot extract it without the correct password.

## ⚠️ Disclaimer

This tool is intended for legitimate privacy and security purposes only. Users are responsible for ensuring they comply with all applicable laws regarding data privacy and security.
