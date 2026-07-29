@echo off
chcp 65001 >nul
title GBT小土豆 · 一键部署 v5.0

:: ═══ 自动提权 (UAC) ═══
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs -Wait"
    exit /b
)

echo ========================================
echo   GBT小土豆 智能大脑 v5.0
echo   远程操控客户端 — 一键部署
echo ========================================
echo.

:: ═══ 1. 检查/安装 Python ═══
echo [1/6] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Python 未安装，正在下载安装（约2分钟）...
    winget install Python.Python.3.12 --silent --accept-package-agreements
    if %errorlevel% neq 0 (
        echo   ⚠️ 自动安装失败
        echo   请手动安装: https://python.org
        pause
        exit /b 1
    )
    :: 刷新 PATH
    call :refresh_env
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   ✅ Python %%v

:: ═══ 2. 安装 Python 依赖 ═══
echo [2/6] 安装 Python 桌面操控库...
python -m pip install --quiet --disable-pip-version-check Pillow mss pyautogui pytesseract 2>&1
if %errorlevel% neq 0 (
    echo   ⚠️ pip 安装失败，请检查网络后重试
    pause
    exit /b 1
)
echo   ✅ Pillow + mss + pyautogui + pytesseract

:: ═══ 3. 检查/安装 Tesseract-OCR ═══
echo [3/6] 检查 Tesseract-OCR...
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo   Tesseract-OCR 未安装，正在下载安装（约1分钟）...
    winget install UB-Mannheim.TesseractOCR --silent --accept-package-agreements
    if %errorlevel% neq 0 (
        echo   ⚠️ winget 安装失败，尝试直接下载...
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe' -OutFile '%TEMP%\tesseract-installer.exe'" && "%TEMP%\tesseract-installer.exe" /S
    )
)
where tesseract >nul 2>&1 && (echo   ✅ Tesseract-OCR 已就绪) || (
    echo   ⚠️ Tesseract 未检测到，跳过OCR语言包
    goto :skip_tess
)

:: ═══ 4. 安装中文OCR语言包 ═══
echo [4/6] 安装中文OCR语言包...
:: 定位 tessdata 目录
set "TESSDATA="
for /f "tokens=*" %%d in ('where tesseract 2^>nul') do (
    for %%I in ("%%d") do set "TESSDATA=%%~dpItessdata"
    goto :found_tess
)
:found_tess
if not defined TESSDATA (
    if exist "C:\Program Files\Tesseract-OCR\tessdata" set "TESSDATA=C:\Program Files\Tesseract-OCR\tessdata"
)
if not defined TESSDATA (
    if exist "C:\Program Files (x86)\Tesseract-OCR\tessdata" set "TESSDATA=C:\Program Files (x86)\Tesseract-OCR\tessdata"
)
if not defined TESSDATA (
    echo   ⚠️ 找不到 Tesseract 安装目录
    goto :skip_tess
)
if not exist "%TESSDATA%" mkdir "%TESSDATA%" 2>nul

:: 下载 chi_sim
if not exist "%TESSDATA%\chi_sim.traineddata" (
    echo   下载中文简体语言包 (约15MB)...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata' -OutFile '%TESSDATA%\chi_sim.traineddata' } catch { exit 1 }"
    if exist "%TESSDATA%\chi_sim.traineddata" (echo   ✅ 中文简体语言包安装完成) else (echo   ⚠️ 下载失败，可稍后重试)
) else (
    echo   ✅ 中文简体语言包已存在
)
:skip_tess

:: ═══ 5. 检查/安装 OMP ═══
echo [5/6] 检查 OMP...
where omp >nul 2>&1
if %errorlevel% neq 0 (
    echo   OMP 未安装，正在安装...
    powershell -Command "irm https://omp.sh/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo   ⚠️ OMP 安装失败，请检查网络后重试
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%v in ('omp --version 2^>^&1') do echo   ✅ OMP %%v

:: ═══ 6. 配置 API Key ═══
echo [6/6] 配置 API Key...
echo.
echo   请选择模型提供商:
echo   [1] DeepSeek ^(推荐，便宜^)
echo   [2] OpenAI
echo   [3] 自定义 / 已配置，跳过
echo.
set /p choice="   选择 [1-3]: "

if "%choice%"=="1" (
    set /p apikey="   DeepSeek API Key: "
    setx DEEPSEEK_API_KEY "%apikey%" >nul
    echo   ✅ DeepSeek 已配置
)
if "%choice%"=="2" (
    set /p apikey="   OpenAI API Key: "
    setx OPENAI_API_KEY "%apikey%" >nul
    echo   ✅ OpenAI 已配置
)
if "%choice%"=="3" (
    echo   跳过 API Key 配置
)

:: ═══ 自检 OCR ═══
echo.
echo ─── 自检 OCR 引擎...
where tesseract >nul 2>&1 && (
    for /f "tokens=*" %%d in ('where tesseract 2^>nul') do (
        "%%d" --list-langs 2>&1 | find "chi_sim" >nul && echo   ✅ OCR 中英文识别就绪 || echo   ⚠️ 中文包未检测到，OCR限于英文
        goto :check_done
    )
) || echo   ⚠️ Tesseract 未安装，OCR不可用
:check_done
:: ═══ 7. 部署后自检 ═══
echo [7/7] 部署后自检...
echo   校验大脑启动...
python -c "from brain.boot import boot; r=boot(); print(f'  大脑自检: {\"PASS\" if r[\"ok\"] else \"FAIL\"}')" 2>&1
if %errorlevel% neq 0 (
    echo   ⚠️ 大脑自检失败
    goto :skip_verify
)
python -c "from brain.nexus import get_nexus; r=get_nexus().scan(); print(f'  邻域扫描: {r.get(\"total_caps\",\"?\")} caps, 损坏{r.get(\"integrity\",{}).get(\"broken_count\",\"?\")}个')" 2>&1
python -c "from brain.cognition import get_cognition; print(get_cognition().who_am_i()['message'])" 2>&1
if %errorlevel% equ 0 (
    echo   ✅ 自检全部通过
) else (
    echo   ⚠️ 部分检查失败，但不影响使用
)
::skip_verify

echo.
echo ========================================
echo   部署完成！
echo.
echo   启动方式:
echo     omp                  # 交互模式，输入 /collab 分享链接
echo     omp --mode rpc       # RPC 模式，供外部程序接入
echo ========================================
echo.
pause
exit /b

:: ═══ 子程序: 刷新环境变量 ═══
:refresh_env
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SysPath=%%b"
    if defined SysPath set "PATH=%SysPath%;%PATH%"
    goto :eof
