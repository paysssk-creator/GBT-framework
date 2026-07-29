@echo off
title GBT OMP Control Pack v5.0

echo.
echo   ========================================
echo     GBT OMP Native Control Pack v5.0
echo     Starting one-click install...
echo   ========================================
echo.

cd /d "%~dp0"

if not exist "install.bat" (
    echo   [ERROR] install.bat not found
    echo   Directory: %cd%
    pause
    exit /b 1
)

call install.bat
if errorlevel 1 (
    echo.
    echo   Setup error. Screenshot + email: support@gbtxiaotudou.com
)
pause
