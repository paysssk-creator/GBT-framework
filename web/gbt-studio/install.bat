@echo off
chcp 65001 >nul
title GBT V5 Studio · 安装

echo ╔══════════════════════════════════╗
echo ║   GBT V5 Studio · 桌面安装       ║
echo ╚══════════════════════════════════╝
echo.

set "INSTALL_DIR=%USERPROFILE%\GBT-Studio"
set "DESKTOP=%USERPROFILE%\Desktop"
set "APP_DIR=%~dp0"

:: 1. Copy app files
echo [1/3] Installing to %INSTALL_DIR%...
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"
mkdir "%INSTALL_DIR%"
xcopy /e /i /q "%APP_DIR%*" "%INSTALL_DIR%" >nul

:: 2. Create desktop shortcut
echo [2/3] Creating desktop shortcut...
set "SHORTCUT=%DESKTOP%\GBT V5 Studio.url"
(
echo [InternetShortcut]
echo URL=http://localhost:9130
echo IconFile=%INSTALL_DIR%\icon.ico
echo IconIndex=0
) > "%SHORTCUT%"

:: Create launcher shortcut
set "LAUNCHER=%DESKTOP%\GBT V5 Studio.lnk"
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%LAUNCHER%');$s.TargetPath='%INSTALL_DIR%\GBT-Studio.bat';$s.WorkingDirectory='%INSTALL_DIR%';$s.IconLocation='%SystemRoot%\System32\imageres.dll,15';$s.Save()" 2>nul

:: 3. Create icon
echo [3/3] Generating icon...
powershell -Command "Add-Type -AssemblyName System.Drawing;$b=New-Object System.Drawing.Bitmap(256,256);$g=[System.Drawing.Graphics]::FromImage($b);$g.Clear([System.Drawing.Color]::FromArgb(26,26,46));$f=New-Object System.Drawing.Font('Segoe UI',120,[System.Drawing.FontStyle]::Bold);$g.DrawString('G', $f, [System.Drawing.Brushes]::White, 60, 30);$b.Save('%INSTALL_DIR%\icon.png');$g.Dispose();$b.Dispose()" 2>nul

echo.
echo ✅ GBT V5 Studio 已安装到桌面！
echo    双击桌面 "GBT V5 Studio" 即可启动
echo.
pause
