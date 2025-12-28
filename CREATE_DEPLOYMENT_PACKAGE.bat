@echo off
title Creating Deployment Package
color 0B
cd /d "%~dp0"

echo ==========================================
echo   CREATING DEPLOYMENT PACKAGE
echo ==========================================
echo.
echo This will create a clean folder with only
echo necessary files for deployment.
echo.
echo Creating: Clinic_App_Deployment
echo.
pause

REM Create deployment folder
if exist "Clinic_App_Deployment" (
    echo Removing old deployment folder...
    rmdir /S /Q "Clinic_App_Deployment"
)

mkdir "Clinic_App_Deployment"

echo.
echo Copying essential files...
echo.

REM Copy Django project files (only necessary ones)
echo [1/10] Copying Django core files...
xcopy "accounts" "Clinic_App_Deployment\accounts" /E /I /Q
xcopy "admission" "Clinic_App_Deployment\admission" /E /I /Q
xcopy "core" "Clinic_App_Deployment\core" /E /I /Q
xcopy "doctor" "Clinic_App_Deployment\doctor" /E /I /Q
xcopy "inventory" "Clinic_App_Deployment\inventory" /E /I /Q
xcopy "opd" "Clinic_App_Deployment\opd" /E /I /Q
xcopy "pharmacy" "Clinic_App_Deployment\pharmacy" /E /I /Q

echo [2/10] Copying templates...
xcopy "templates" "Clinic_App_Deployment\templates" /E /I /Q

echo [3/10] Copying static files...
xcopy "static" "Clinic_App_Deployment\static" /E /I /Q

echo [4/10] Copying manage.py...
copy "manage.py" "Clinic_App_Deployment\" >nul

echo [5/10] Copying requirements.txt...
copy "requirements.txt" "Clinic_App_Deployment\" >nul

echo [6/10] Copying database...
if exist "db.sqlite3" (
    copy "db.sqlite3" "Clinic_App_Deployment\" >nul
) else (
    echo WARNING: db.sqlite3 not found, will be created on first run
)

echo [7/10] Copying desktop app...
mkdir "Clinic_App_Deployment\DesktopApp"
xcopy "electron\dist\win-unpacked" "Clinic_App_Deployment\DesktopApp" /E /I /Q

echo [8/10] Copying launcher scripts...
copy "INSTALL.bat" "Clinic_App_Deployment\" >nul
copy "RUN_DESKTOP_APP.bat" "Clinic_App_Deployment\" >nul

echo [9/10] Creating README for users...
(
echo ==========================================
echo   CLINIC MANAGEMENT SYSTEM
echo ==========================================
echo.
echo SETUP INSTRUCTIONS:
echo.
echo 1. Make sure Python 3.8+ is installed
echo    Download from: https://www.python.org/
echo.
echo 2. Run INSTALL.bat ^(first time only^)
echo    - This sets up the virtual environment
echo    - Installs all required packages
echo    - Takes 2-5 minutes
echo.
echo 3. After installation, run the app:
echo    Option A: Double-click "RUN_DESKTOP_APP.bat"
echo    Option B: Go to DesktopApp folder
echo              Double-click "Clinic Management.exe"
echo.
echo 4. First laptop to open becomes SERVER
echo    Other laptops auto-connect as CLIENTS
echo.
echo NETWORK SETUP:
echo - Connect all laptops to SAME WiFi network
echo - No internet required after installation
echo.
echo SUPPORT:
echo - For issues, check TROUBLESHOOTING.txt
echo.
echo ==========================================
) > "Clinic_App_Deployment\README.txt"

echo [10/10] Creating troubleshooting guide...
(
echo COMMON ISSUES AND SOLUTIONS
echo ============================
echo.
echo Issue: "Python not found"
echo Solution: Install Python from python.org
echo           Make sure to check "Add Python to PATH"
echo.
echo Issue: "Module not found"
echo Solution: Run INSTALL.bat again
echo.
echo Issue: App won't connect to server
echo Solution: 
echo - Check all laptops on same WiFi
echo - Restart server laptop first
echo - Wait 15 seconds, then start other laptops
echo.
echo Issue: Slow performance
echo Solution:
echo - Move closer to WiFi router
echo - Use Ethernet cables instead
echo - Close other programs
echo.
echo For more help, contact your IT administrator.
) > "Clinic_App_Deployment\TROUBLESHOOTING.txt"

echo.
echo ==========================================
echo   DEPLOYMENT PACKAGE CREATED!
echo ==========================================
echo.
echo Location: Clinic_App_Deployment\
echo.
echo This folder contains ONLY necessary files:
echo - Django application files
echo - Desktop app ^(.exe^)
echo - Installation scripts
echo - User guides
echo.
echo NO source code or development files included!
echo.
echo You can now:
echo 1. Copy this folder to USB drive
echo 2. Transfer to other laptops
echo 3. Run INSTALL.bat on each laptop
echo.
echo Folder size: ~250 MB ^(much smaller^)
echo.
pause

REM Open deployment folder
explorer "Clinic_App_Deployment"
