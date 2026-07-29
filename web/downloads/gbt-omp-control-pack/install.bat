@echo off
chcp 936 >nul 2>&1
title GBT小土豆 · OMP原生控制包 v5.0 一键部署
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════════════════════
::  GBT小土豆 OMP原生控制包 — Windows 全自动安装器
::  开发者：自由的风  ·  一键下载→安装→连接控制
:: ═══════════════════════════════════════════════════════════

echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║   ? GBT小土豆 · OMP原生控制包 v5.0          ║
echo   ║   最高执行官 · 一键远程操控部署             ║
echo   ╚══════════════════════════════════════════════╝
echo.

:: ── 自动提权 ──
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo   ? 请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs -Wait"
    exit /b
)

set "INSTALL_DIR=%USERPROFILE%\GBTxiaotudouV5"
set "STAMP=%INSTALL_DIR%\.omp_control_installed"

if exist "%STAMP%" (
    echo   ? OMP 控制包已安装
    echo   启动方式: cd /d "%INSTALL_DIR%" ^&^& omp
    echo.
    pause
    exit /b
)

echo   [1/5] 检查 Python 3.10+ ...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   ? 安装 Python 3.12 (约2分钟)...
    winget install Python.Python.3.12 --silent --accept-package-agreements
    if %errorlevel% neq 0 (
        echo   ? Python 安装失败，请手动安装: https://python.org
        pause & exit /b 1
    )
    call :refresh_env
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   ? Python %%v

echo   [2/5] 安装桌面操控依赖...
python -m pip install --quiet --disable-pip-version-check Pillow mss pyautogui pytesseract easyocr numpy opencv-python 2>&1
if %errorlevel% neq 0 (
    echo   ?? 部分依赖安装失败，尝试继续...
)
echo   ? 视觉+操控引擎就绪

echo   [3/5] 检查 Tesseract-OCR (中文识别)...
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo   ? 安装 Tesseract-OCR...
    winget install UB-Mannheim.TesseractOCR --silent --accept-package-agreements
)
where tesseract >nul 2>&1 && (
    for /f "tokens=*" %%d in ('where tesseract 2^>nul') do set "TESSDATA=%%~dpdtessdata"
    if not exist "!TESSDATA!\chi_sim.traineddata" (
        echo   ? 下载中文OCR语言包...
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata' -OutFile '!TESSDATA!\chi_sim.traineddata'"
    )
    echo   ? Tesseract-OCR 就绪 (中英文)
) || echo   ?? Tesseract 未安装，OCR限于英文

echo   [4/5] 安装 OMP 命令行外壳...
where omp >nul 2>&1
if %errorlevel% neq 0 (
    echo   ? 安装 OMP (Oh My Pi)...
    powershell -Command "irm https://omp.sh/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo   ? OMP 安装失败
        pause & exit /b 1
    )
)
call :refresh_env
for /f "tokens=*" %%v in ('omp --version 2^>^&1') do echo   ? OMP %%v

echo   [5/5] 克隆 GBT 大脑 + 配置...
if exist "%INSTALL_DIR%" (
    echo   ? 更新已有仓库...
    cd /d "%INSTALL_DIR%"
    git pull origin master 2>nul
) else (
    echo   ? 克隆 GBT 大脑仓库...
    git clone https://github.com/paysssk-creator/GBTxiaotudouV5.git "%INSTALL_DIR%"
    cd /d "%INSTALL_DIR%"
)

:: 安装 Python 依赖
python -m pip install -r requirements.txt -q 2>&1 | find /v "Requirement already satisfied"

:: 配置 DeepSeek API Key
echo.
echo   ? 配置 API Key (免费额度: 500万 tokens)
echo   获取: https://platform.deepseek.com/api_keys
echo.
set /p DS_KEY="   粘贴 DeepSeek API Key (回车跳过): "
if not "!DS_KEY!"=="" (
    setx DEEPSEEK_API_KEY "!DS_KEY!" >nul
    echo   ? API Key 已保存
) else (
    echo   ?? 跳过，可稍后手动配置
)

:: 标记安装完成
echo %date% %time% > "%STAMP%"

:: 自检
echo.
echo   ─── 运行自检...
cd /d "%INSTALL_DIR%"
python -c "from brain.boot import boot; boot()" 2>nul
python -c "from brain.nexus import get_nexus; print(get_nexus().deep_scan()['verdict'])" 2>nul

echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║   ? GBT小土豆 OMP 原生控制包 部署完成！    ║
echo   ║                                              ║
echo   ║   启动方式:                                   ║
echo   ║     cd /d "%INSTALL_DIR%"                   ║
echo   ║     omp                                      ║
echo   ║   远程控制:                                   ║
echo   ║     omp --mode rpc              (API模式)    ║
echo   ║     omp --collab               (协作模式)    ║
echo   ║                                              ║
echo   ║   帮助: https://gbtxiaotudou.com/help        ║
echo   ║   文档: https://gbtxiaotudou.com/docs        ║
echo.
pause
exit /b

:refresh_env
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SysPath=%%b"
if defined SysPath set "PATH=%SysPath%;%PATH%"
goto :eof
