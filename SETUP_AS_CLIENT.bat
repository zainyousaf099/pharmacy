@echo off
title Setup as CLIENT Laptop
color 0B
cd /d "%~dp0"

echo ========================================
echo   CLINIC MANAGEMENT - CLIENT SETUP
echo ========================================
echo.
echo This laptop will be a CLIENT.
echo - It will NOT start Django server
echo - It will connect to the server laptop
echo - It will share the same database
echo.
echo ========================================

set /p SERVER_IP="Enter SERVER laptop IP address: "

if "%SERVER_IP%"=="" (
    echo.
    echo ERROR: You must enter the server IP address!
    pause
    exit /b
)

echo.
echo Creating client configuration...
echo Connecting to server: %SERVER_IP%

REM Create config.json for client mode
(
echo {
echo   "mode": "client",
echo   "serverIP": "%SERVER_IP%"
echo }
) > electron\config.json

echo.
echo ========================================
echo   CLIENT SETUP COMPLETE!
echo ========================================
echo.
echo Configuration saved:
echo - Mode: CLIENT
echo - Server IP: %SERVER_IP%
echo.
echo Now you can:
echo 1. Run the desktop app (Clinic Management.exe)
echo 2. Or use RUN_DESKTOP_APP.bat for testing
echo.
echo This laptop will connect to the server and
echo use the same database as all other laptops.
echo.
pause
