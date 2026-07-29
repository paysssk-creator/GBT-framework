@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   GBT A股操盘系统 v5.0 — 一键部署
echo ============================================
echo.

set "DST=%USERPROFILE%\GBTxiaotudouV5"
if not exist "%DST%" set "DST=C:\Users\Administrator\GBTxiaotudouV5"

echo 📦 1/4 Python操盘引擎...
if not exist "%DST%\caps\stock_browser_trader" mkdir "%DST%\caps\stock_browser_trader"
copy /Y "caps\stock_browser_trader\run.py"           "%DST%\caps\stock_browser_trader\run.py"           >nul 2>&1 || echo    ⚠️ run.py failed
copy /Y "caps\stock_browser_trader\knowledge.json"    "%DST%\caps\stock_browser_trader\knowledge.json"    >nul 2>&1 || echo    ⚠️ knowledge.json failed
copy /Y "caps\stock_browser_trader\capability.json"   "%DST%\caps\stock_browser_trader\capability.json"   >nul 2>&1 || echo    ⚠️ capability.json failed
echo # GBT Stock Browser Trader > "%DST%\caps\stock_browser_trader\__init__.py"
echo    ✅ Python引擎

echo 📦 2/4 PS原生引擎...
copy /Y "gbt_stock.ps1"  "%DST%\gbt_stock.ps1"  >nul 2>&1 || echo    ⚠️ gbt_stock.ps1 failed
echo    ✅ PS引擎

echo 📦 3/4 AI推理引擎...
if not exist "%DST%\brain" mkdir "%DST%\brain"
copy /Y "brain\deep_reasoner.py"  "%DST%\brain\deep_reasoner.py"  >nul 2>&1 || echo    ⚠️ deep_reasoner.py failed
echo    ✅ AI引擎 (DeepSeek V4 Pro)

echo 📦 4/4 远程代理...
copy /Y "gbt_agent.ps1"  "%DST%\gbt_agent.ps1"  >nul 2>&1 || echo    ⚠️ gbt_agent.ps1 failed
echo    ✅ 远程代理

echo.
echo ============================================
echo  ✅ 部署完成!
echo ============================================
echo.
echo  使用方法:
echo    PS原生: powershell -File gbt_stock.ps1 scan
echo    PS原生: powershell -File gbt_stock.ps1 hot
echo    PS原生: powershell -File gbt_stock.ps1 analyze 600519
echo    Python:  python caps/stock_browser_trader/run.py scan_market
echo.
pause
