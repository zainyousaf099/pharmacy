@echo off
echo ============================================
echo   Clinic Management System - Build Installer
echo ============================================
echo.

cd /d "%~dp0"

echo [1/7] Cleaning up old builds...
if exist "electron\dist" rmdir /s /q "electron\dist"
echo       Done!
echo.

echo [2/7] Cleaning Python cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul
echo       Done!
echo.

echo [3/7] Checking Python portable setup...
if not exist "python-portable\python.exe" (
    echo ERROR: python-portable folder not found!
    echo Please ensure python-portable folder exists with Python and all dependencies.
    pause
    exit /b 1
)
echo       Python portable found!
echo.

echo [4/7] Verifying Django dependencies in portable Python...
"python-portable\python.exe" -c "import django; print('       Django version:', django.__version__)"
if errorlevel 1 (
    echo ERROR: Django not installed in portable Python!
    echo Installing dependencies...
    "python-portable\python.exe" -m pip install -r requirements.txt
)
echo.

echo [5/7] Creating build folder and icon...
if not exist "electron\build" mkdir "electron\build"
"env\Scripts\python.exe" -c "from PIL import Image; img = Image.open('appico.png'); img.save('electron/build/icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])" 2>nul
if not exist "electron\build\icon.ico" (
    echo WARNING: Could not create icon.ico - using default
)
echo       Done!
echo.

echo [6/7] Installing Node.js dependencies...
cd electron
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install npm dependencies!
    pause
    exit /b 1
)
echo       Done!
echo.

echo [7/7] Building installer...
echo       This may take several minutes...
echo.
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

cd ..
echo.
echo ============================================
echo   BUILD SUCCESSFUL!
echo ============================================
echo.
echo Your installer is ready at:
echo   electron\dist\Clinic Management System Setup 1.0.0.exe
echo.
echo You can distribute this file to your clients!
echo.
pause
