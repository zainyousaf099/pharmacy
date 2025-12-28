@echo off
title Clinic Management - Desktop App (Development Mode)
color 0A

REM Check if electron folder exists (development environment)
if exist "%~dp0electron" (
    cd /d "%~dp0electron"
    echo ====================================
    echo   CLINIC MANAGEMENT DESKTOP APP
    echo   Development Mode
    echo ====================================
    echo.
    echo Installing dependencies (if needed)...
    call npm install
    
    echo.
    echo Starting Desktop Application...
    echo.
    echo NOTE: This runs in development mode.
    echo For production build, run as Administrator.
    echo.
    
    npm start
) else (
    REM Production environment (DesktopApp folder)
    if exist "%~dp0DesktopApp\Clinic Management.exe" (
        echo ====================================
        echo   CLINIC MANAGEMENT SYSTEM
        echo ====================================
        echo.
        echo Starting application...
        echo.
        
        cd /d "%~dp0DesktopApp"
        start "" "Clinic Management.exe"
        
        echo.
        echo Application started!
        echo.
        echo If you see a splash screen saying
        echo "Searching for server..." - that's normal!
        echo.
        echo Wait a few seconds for the app to open.
        echo.
    ) else (
        echo ====================================
        echo   ERROR
        echo ====================================
        echo.
        echo Desktop app not found!
        echo.
        echo Please make sure you have:
        echo 1. Installed using INSTALL.bat
        echo 2. Or build the app using npm run build-win
        echo.
    )
)

pause
