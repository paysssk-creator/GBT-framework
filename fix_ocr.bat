@echo off
chcp 65001 >nul
title GBT · OCR一键修复
echo GBT OCR引擎修复中...
echo.

:: 安装Tesseract
where tesseract >nul 2>&1 || (
    echo 安装 Tesseract-OCR...
    winget install UB-Mannheim.TesseractOCR --silent --accept-package-agreements
)

:: 定位tessdata
set "TD="
for /f "tokens=*" %%d in ('where tesseract 2^>nul') do for %%I in ("%%d") do set "TD=%%~dpItessdata"
if not defined TD (if exist "C:\Program Files\Tesseract-OCR\tessdata" set "TD=C:\Program Files\Tesseract-OCR\tessdata")
if not defined TD (if exist "C:\Program Files (x86)\Tesseract-OCR\tessdata" set "TD=C:\Program Files (x86)\Tesseract-OCR\tessdata")
if not defined TD (echo Tesseract未找到 & pause & exit /b 1)

:: 下载中文包
if exist "%TD%\chi_sim.traineddata" (
    echo 中文包已存在
) else (
    echo 下载中文简体语言包...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata' -OutFile '%TD%\chi_sim.traineddata'"
)

:: 验证
"%TD%\..\tesseract.exe" --list-langs 2>&1 | find "chi_sim" >nul && (
    echo ✅ OCR中文识别已就绪！
) || (
    echo ⚠️ 中文包未成功，检查网络后重试
)
pause
