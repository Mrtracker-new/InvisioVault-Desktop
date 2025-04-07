@echo off
echo Building InvisioVault Installer Package...
echo.

:: First, build the executable using PyInstaller
echo Step 1: Building executable with PyInstaller...
call build.bat

:: Check if the executable was built successfully
if not exist "dist\InvisioVault.exe" (
    echo Error: Failed to build executable. Aborting installer creation.
    pause
    exit /b 1
)

:: Create the installer directory if it doesn't exist
if not exist "installer" mkdir installer

:: Run Inno Setup Compiler to create the installer
echo Step 2: Creating installer with Inno Setup...

:: Check if Inno Setup is installed
set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_COMPILER%" (
    set "INNO_COMPILER=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist "%INNO_COMPILER%" (
    echo Error: Inno Setup not found. Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
    echo After installing, run this script again.
    pause
    exit /b 1
)

:: Compile the installer
"%INNO_COMPILER%" installer_setup.iss

if %ERRORLEVEL% neq 0 (
    echo Error: Failed to create installer.
    pause
    exit /b 1
)

echo.
echo InvisioVault installer package created successfully!
echo You can find the installer in the 'installer' folder.
echo.
pause