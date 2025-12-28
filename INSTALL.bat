@echo off
title Clinic App - Quick Installer
color 0E
cd /d "%~dp0"

echo ==========================================
echo   CLINIC MANAGEMENT SYSTEM - INSTALLER
echo ==========================================
echo.
echo This will set up the Clinic app on this laptop.
echo.
echo Requirements:
echo - Python 3.8 or newer must be installed
echo - Internet connection (for first-time setup)
echo.
pause

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Python found!
python --version
echo.

REM Check if virtual environment exists
if exist "env\Scripts\activate.bat" (
    echo [OK] Virtual environment already exists
) else (
    echo Creating virtual environment...
    python -m venv env
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

echo.
echo Installing dependencies...
echo (This may take 2-5 minutes)
echo.

call env\Scripts\activate.bat

REM Upgrade pip first
python -m pip install --upgrade pip --quiet

REM Install requirements
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
) else (
    echo [WARNING] requirements.txt not found!
    echo Installing essential packages...
    pip install django pillow
)

echo.
echo ==========================================
echo   INSTALLATION COMPLETE!
echo ==========================================
echo.
echo Next steps:
echo 1. Make sure all laptops are on same WiFi network
echo 2. Run "RUN_DESKTOP_APP.bat" to start the app
echo 3. First laptop to start becomes the server
echo 4. Other laptops auto-connect to server
echo.
echo For desktop app (.exe):
echo - Go to: electron\dist\win-unpacked\
echo - Double-click: Clinic Management.exe
echo.
pause
