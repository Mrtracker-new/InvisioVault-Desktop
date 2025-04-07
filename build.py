#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build script for InvisioVault

This script builds the InvisioVault application into a standalone executable
using PyInstaller.
"""

import os
import sys
import shutil
import subprocess

# Configuration
APP_NAME = "InvisioVault"
MAIN_SCRIPT = "invisiovault.py"
OUTPUT_DIR = "dist"
ICON_FILE = "InvisioVault.ico"  # Application icon file


def clean_build_dirs():
    """Clean build directories"""
    dirs_to_clean = ["build", "dist", f"{APP_NAME}.spec"]
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
            else:
                os.remove(dir_path)
    print("Cleaned build directories.")


def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependencies installed.")


def build_executable():
    """Build the executable using PyInstaller"""
    print(f"Building {APP_NAME} executable...")
    
    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--clean",
    ]
    
    # Add icon if available
    if ICON_FILE and os.path.exists(ICON_FILE):
        cmd.extend(["--icon", ICON_FILE])
    
    # Add main script
    cmd.append(MAIN_SCRIPT)
    
    # Run PyInstaller
    # Use absolute paths and handle Python executable
    invisivault_path = os.path.abspath('invisiovault.py')
    version_file = os.path.abspath('version_info.txt')
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--onefile',
        '--noconsole',
        '--name', 'InvisioVault',
        '--icon', 'InvisioVault.ico',
        '--version-file', version_file,
        invisivault_path
    ]
    
    try:
        subprocess.check_call(
        [
            sys.executable,
            '-m',
            'PyInstaller',
            '--onefile',
            '--noconsole',
            '--name', 'InvisioVault',
            '--icon', os.path.abspath('InvisioVault.ico'),
            '--version-file', os.path.abspath('version_info.txt'),
            '--add-data', f'{os.path.abspath("history.json")};.',
            '--hidden-import', 'PyQt5.QtCore',
            '--hidden-import', 'PyQt5.QtGui',
            '--hidden-import', 'PyQt5.QtWidgets',
            '--hidden-import', 'sip',
            '--paths', os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages'),
            '--paths', os.path.expanduser('~/.local/lib/python3.12/site-packages'),
            os.path.abspath('invisiovault.py')
        ],
        shell=False
    )
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code {e.returncode}")
        sys.exit(1)
    print(f"Build completed. Executable is in the '{OUTPUT_DIR}' directory.")


def main():
    """Main build function"""
    print(f"=== Building {APP_NAME} ===\n")
    
    # Clean previous builds
    clean_build_dirs()
    
    # Install dependencies
    install_dependencies()
    
    # Build executable
    build_executable()
    
    print(f"\n=== {APP_NAME} build completed successfully ===\n")
    print(f"The executable is located at: {os.path.join(OUTPUT_DIR, APP_NAME)}.exe")


if __name__ == "__main__":
    main()