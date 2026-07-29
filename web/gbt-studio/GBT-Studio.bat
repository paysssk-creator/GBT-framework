@echo off
chcp 65001 >nul
title GBT V5 Studio

:: ══════════════════════════════════════════
:: GBT V5 Studio · Desktop App Launcher
:: ══════════════════════════════════════════

set "APP_DIR=%~dp0"
set "PORT=9130"
set "APP_URL=http://localhost:%PORT%"

echo ╔══════════════════════════════════╗
echo ║    GBT V5 Studio · Desktop App   ║
echo ║    开发者: 自由的风               ║
echo ╚══════════════════════════════════╝
echo.

:: Kill any existing instance on the port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Start HTTP server in background
echo [1/3] Starting server on port %PORT%...
start /B "" python -m http.server %PORT% --directory "%APP_DIR%" >nul 2>&1

:: Wait for server to be ready
:wait
timeout /t 1 /nobreak >nul
curl -s -o nul %APP_URL% 2>nul
if errorlevel 1 goto wait

echo [2/3] Server ready

:: Detect Chrome path
set "CHROME="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe"
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

:: Try Edge as fallback
if "%CHROME%"=="" (
    if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" set "CHROME=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)
if "%CHROME%"=="" (
    if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" set "CHROME=C:\Program Files\Microsoft\Edge\Application\msedge.exe"
)

if "%CHROME%"=="" (
    echo [3/3] Opening in default browser...
    start "" %APP_URL%
) else (
    echo [3/3] Launching desktop window...
    start "" "%CHROME%" --app=%APP_URL% --window-size=1280,820 --window-position=center --disable-extensions --disable-sync --no-first-run
)

echo.
echo GBT V5 Studio is running at %APP_URL%
echo Close this window to stop the server.
echo.

:: Wait for user to close
pause >nul

:: Cleanup: kill server
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo Server stopped.
