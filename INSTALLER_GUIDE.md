# InvisioVault Installer Guide

## Overview
This guide explains how to build and use the InvisioVault installer package that includes proper metadata and publisher information. The installer is created using Inno Setup, which produces a professional Windows installer with all necessary application information.

## Prerequisites

1. **Python Environment**: Ensure you have Python 3.8+ installed with all dependencies listed in `requirements.txt`
2. **Inno Setup**: Download and install Inno Setup 6 from [https://jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)
3. **PyInstaller**: Already included in the requirements.txt file

## Files Created for the Installer

1. **installer_setup.iss**: The Inno Setup script that defines how the installer is built
2. **LICENSE.txt**: MIT license file included in the installer
3. **version_info.txt**: Contains Windows version information metadata
4. **build_installer.bat**: Batch script to automate the build process

## Building the Installer

### Method 1: Using the Automated Script

1. Simply run the `build_installer.bat` script:
   ```
   build_installer.bat
   ```

   This script will:
   - Build the executable using PyInstaller
   - Create the installer using Inno Setup
   - Place the final installer in the `installer` folder

### Method 2: Manual Process

1. First, build the executable:
   ```
   build.bat
   ```

2. Then compile the installer with Inno Setup:
   ```
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_setup.iss
   ```

## Installer Features

- **Professional Appearance**: Modern wizard interface with InvisioVault branding
- **Proper Metadata**: Includes version information, publisher details, and file descriptions
- **Start Menu Integration**: Creates program group with application shortcut
- **Desktop Shortcut**: Optional desktop icon creation
- **Uninstaller**: Proper uninstallation support
- **Documentation**: Includes all documentation files

## Customizing the Installer

### Changing Version Information

1. Update the version number in `invisiovault.py` (APP_VERSION variable)
2. Update the version in `installer_setup.iss` (#define MyAppVersion)
3. Update the version in `version_info.txt` (filevers, prodvers, and version strings)

### Changing Publisher Information

1. Modify the publisher name in `installer_setup.iss` (#define MyAppPublisher)
2. Update the company name in `version_info.txt` (CompanyName and LegalCopyright)

### Adding Additional Files

To include additional files in the installer:

1. Open `installer_setup.iss`
2. Add new entries to the [Files] section:
   ```
   Source: "path\to\file"; DestDir: "{app}"; Flags: ignoreversion
   ```

## Distribution

After building, you'll find the installer at:
```
installer\InvisioVault_Setup_v1.0.0.exe
```

This installer can be distributed to users and includes:
- The InvisioVault application
- All necessary documentation
- Proper Windows metadata and publisher information

## Troubleshooting

### Common Issues

1. **Inno Setup Not Found**: Ensure Inno Setup is installed in the default location or update the path in `build_installer.bat`

2. **PyInstaller Errors**: Check that all dependencies are installed with `pip install -r requirements.txt`

3. **Missing Files**: Verify that all required files (InvisioVault.ico, history.json, etc.) exist in the project directory

### Getting Help

If you encounter issues with the installer, check the Inno Setup documentation or seek assistance from the developer.