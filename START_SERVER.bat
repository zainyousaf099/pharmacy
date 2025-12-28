@echo off
title Clinic Management System - Server
color 0A
echo ====================================
echo   CLINIC MANAGEMENT SYSTEM SERVER
echo ====================================
echo.
echo Starting Django server...
echo.
echo IMPORTANT: Keep this window open!
echo Close it only at end of day.
echo.
echo Other laptops can access at:
echo http://YOUR-IP:8000/
echo.
echo To find your IP, open another PowerShell and type: ipconfig
echo.
echo ====================================
echo.

cd /d "%~dp0"
call .\env\Scripts\activate.bat

echo Checking database...
python manage.py migrate --no-input

echo.
echo Starting server on ALL network interfaces...
echo.
python manage.py runserver 0.0.0.0:8000

pause
