@echo off
title Clinic Management System - Server
color 0A
cd /d "%~dp0"

echo ====================================
echo   CLINIC MANAGEMENT SYSTEM
echo ====================================
echo.
echo Starting Django server...
echo.

REM Activate virtual environment
call .\env\Scripts\activate.bat

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%a
)
set IP=%IP:~1%

REM Start Django server
echo.
echo ====================================
echo   SERVER STARTED!
echo ====================================
echo.
echo Your Server IP: %IP%
echo.
echo Share this with other laptops:
echo http://%IP%:8000/
echo.
echo Doctor Panel:  http://%IP%:8000/accounts/doctor-login/
echo OPD Panel:     http://%IP%:8000/accounts/opd-login/
echo Pharmacy:      http://%IP%:8000/accounts/pharmacy-login/
echo.
echo ====================================
echo.
echo Press Ctrl+C to stop server
echo.

python manage.py runserver 0.0.0.0:8000

pause
