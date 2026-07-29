@echo off
echo ╔══════════════════════════════════════════╗
echo ║  GBT Nano Browser Pro — Build & Package  ║
echo ╚══════════════════════════════════════════╝
cd /d "%~dp0"

echo [1/3] Installing dependencies...
call npm install 2>&1
if errorlevel 1 (echo ERROR: npm install failed & pause & exit /b 1)

echo [2/3] Building portable executable...
call npx electron-builder --win portable 2>&1
if errorlevel 1 (
    echo [!] electron-builder failed, creating manual package...
    goto manual_package
)

echo [3/3] Build complete!
echo Output: dist\*.exe
goto done

:manual_package
echo [2/3 alt] Creating manual package...
if not exist "dist" mkdir dist
powershell -Command "Compress-Archive -Path 'electron','src','server','node_modules','package.json','install.bat' -DestinationPath 'dist\GBT-Nano-Browser-Pro-v1.0.zip' -Force"
echo [3/3] Manual package created: dist\GBT-Nano-Browser-Pro-v1.0.zip

:done
echo.
echo ✅ Build finished
dir dist\ /b 2>nul
pause
