@echo off
chcp 65001 >nul
cd /d "%~dp0"
title GBTxiaotudouV5

REM 自动检测OMP路径
if exist "%USERPROFILE%\.bun\bin\omp.exe" (
    start "GBTxiaotudouV5" "%USERPROFILE%\.bun\bin\omp.exe"
) else if exist "C:\Users\ADMIN\.bun\bin\omp.exe" (
    start "GBTxiaotudouV5" "C:\Users\ADMIN\.bun\bin\omp.exe"
) else (
    echo OMP未安装, 请先运行部署脚本: deploy.bat
    pause
)
