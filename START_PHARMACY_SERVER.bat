@echo off
title Pharmacy Server - Main Database
color 0A
cls
echo ============================================================
echo              PHARMACY SERVER - MAIN DATABASE
echo ============================================================
echo.
echo Starting Pharmacy as the MAIN SERVER...
echo.
echo Other PCs (OPD, Doctor) will connect to this database.
echo.
echo ============================================================

cd /d "%~dp0"

:: Get IP Address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║  YOUR SERVER IP ADDRESS:  %IP%                    
echo ║                                                          ║
echo ║  Share this IP with OPD and Doctor panels to connect!    ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

:: Activate environment and start server
call .\env\Scripts\activate.bat

echo Checking database...
python manage.py migrate --no-input

echo.
echo ============================================================
echo Server starting on: http://%IP%:8000/pharmacy/
echo ============================================================
echo.
echo KEEP THIS WINDOW OPEN - Closing will stop the server!
echo.

python manage.py runserver 0.0.0.0:8000

pause
