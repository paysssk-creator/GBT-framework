@echo off
REM GBT 远程部署代理 · Windows一键安装
REM 客户运行此脚本 → 自动建立安全隧道 → GBT接手部署
title GBT Remote Deploy Agent
echo.
echo 🥔 GBT 远程部署代理 v3.0
echo ================================
echo.

REM 检测Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [1/4] 安装 Python 3.12...
    winget install Python.Python.3.12 --accept-package-agreements --silent
    echo 安装完成, 请重新打开终端运行此脚本
    pause
    exit /b
)

REM 下载deploy_me.py
echo [2/4] 下载部署代理...
set AGENT_DIR=%USERPROFILE%\.gbt\deploy-agent
mkdir "%AGENT_DIR%" 2>nul
curl -sSL -o "%AGENT_DIR%\deploy_me.py" https://gbtxiaotudou.com/deploy_me.py

REM 生成会话ID
set SESSION=%RANDOM%%RANDOM%

REM 启动
echo [3/4] 启动安全隧道...
cd /d "%AGENT_DIR%"
python deploy_me.py --session %SESSION%

echo.
echo [4/4] 隧道已建立! GBT正在连接...
echo 请勿关闭此窗口!
pause
