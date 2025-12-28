@echo off
title Setup as SERVER Laptop
color 0C
cd /d "%~dp0electron"

echo ========================================
echo   CLINIC MANAGEMENT - SERVER SETUP
echo ========================================
echo.
echo This laptop will become the SERVER.
echo - It will start the Django server
echo - It will host the database
echo - Other laptops will connect to this one
echo.

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do set IP=%%a
set IP=%IP:~1%

echo Your Server IP Address: %IP%
echo.
echo Creating server configuration...

REM Create config.json for server mode
(
echo {
echo   "mode": "server",
echo   "serverIP": "localhost"
echo }
) > electron\config.json

echo.
echo ========================================
echo   SERVER SETUP COMPLETE!
echo ========================================
echo.
echo IMPORTANT: Write down this IP address
echo Other laptops will need it: %IP%
echo.
echo Now you can:
echo 1. Run the desktop app (Clinic Management.exe)
echo 2. Or use RUN_DESKTOP_APP.bat for testing
echo.
pause
