@echo off
title GBT Nano Browser Pro v1.0 — 一键安装
echo.
echo   ╔══════════════════════════════════════════╗
echo   ║   GBT Nano Browser Pro v1.0              ║
echo   ║   AI全控 · 指纹隐身 · 2Captcha · 股票    ║
echo   ╚══════════════════════════════════════════╝
echo.
echo   [1/3] 安装依赖...
cd /d "%~dp0"
call npm install --production 2>nul
if errorlevel 1 (
    echo   [!] npm install 失败，尝试安装 Node.js...
    echo   请先安装 Node.js: https://nodejs.org
    pause
    exit /b 1
)
echo   [2/3] 配置环境...
if not exist "%USERPROFILE%\.gbt" mkdir "%USERPROFILE%\.gbt"
echo   [3/3] 创建桌面快捷方式...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\GBT Nano Browser Pro.lnk');$s.TargetPath='%~dp0node_modules\.bin\electron.cmd';$s.WorkingDirectory='%~dp0';$s.IconLocation='%~dp0src\icon.ico';$s.Save()" 2>nul
echo.
echo   ✅ 安装完成！
echo   🚀 双击桌面 "GBT Nano Browser Pro" 启动
echo.
start "" /min cmd /c "%~dp0node_modules\.bin\electron.cmd" "%~dp0"
echo   浏览器正在启动...
pause
