# gbt_stock.ps1 - GBT A股操盘 PowerShell原生版
# 无需Python，远程机器直接用
param([string]$Action="scan", [string]$Code="600519", [int]$Limit=10)

function Get-StockData {
    param([string[]]$Codes)
    $url = "https://hq.sinajs.cn/list=" + ($Codes -join ",")
    $resp = Invoke-RestMethod -Uri $url -Headers @{Referer="https://finance.sina.com.cn"} -TimeoutSec 10
    $stocks = @()
    foreach ($line in ($resp -split "`n")) {
        if ($line -match "hq_str_") {
            $p = $line -split ","
            $code = ($line -split "=")[0] -replace "var hq_str_", ""
            $stocks += [PSCustomObject]@{
                Code = $code
                Name = ($p[0] -split '"')[-1]
                Price = [double]$p[3]
                Open = [double]$p[1]
                PreClose = [double]$p[2]
                High = [double]$p[4]
                Low = [double]$p[5]
                Volume = [long]$p[8]
                Amount = [double]$p[9]
                Change = [math]::Round(([double]$p[3] - [double]$p[2]), 2)
                ChangePct = [math]::Round((([double]$p[3] - [double]$p[2]) / [double]$p[2] * 100), 2)
                Time = "$($p[30]) $($p[31])"
            }
        }
    }
    return $stocks
}

$POOL = @(
    "sh600519","sz000858","sh601318","sz300750","sh600036",
    "sz002415","sz000333","sh601899","sz002594","sh600900",
    "sh600276","sh600887","sh601012","sz002475","sz300059",
    "sh600030","sh601398","sz000001","sz002230","sz300124",
    "sz000725","sh600050","sh601857","sz002142","sz300498",
    "sh601166","sh600809","sz000651","sh603259","sz002352",
    "sh601088","sh600585","sz000063","sh688981","sz300274",
    "sh600031","sh600690","sz002049","sh600150","sz000776"
)

switch ($Action) {
    "scan" {
        Write-Host "=== GBT A股扫描 Top $Limit ===" -ForegroundColor Green
        $batch = $POOL | Select-Object -First $Limit
        $stocks = Get-StockData -Codes $batch
        $stocks | Sort-Object {[math]::Abs($_.ChangePct)} -Descending | 
            Select-Object -First $Limit |
            Format-Table Code,Name,Price,ChangePct,Volume,High,Low -AutoSize
    }
    "analyze" {
        $codes = @()
        if ($Code -match "^6") { $codes = @("sh$Code") }
        else { $codes = @("sz$Code") }
        $s = Get-StockData -Codes $codes
        if ($s) {
            $s | Format-List Code,Name,Price,Open,PreClose,High,Low,Volume,Amount,Change,ChangePct,Time
        }
    }
    "hot" {
        Write-Host "=== 涨跌幅TOP10 ===" -ForegroundColor Green
        $stocks = Get-StockData -Codes $POOL
        Write-Host "`n🔥 涨幅榜:" -ForegroundColor Red
        $stocks | Where-Object { $_.ChangePct -gt 0 } | Sort-Object ChangePct -Descending | 
            Select-Object -First 5 | Format-Table Name,Price,ChangePct -AutoSize
        Write-Host "❄️ 跌幅榜:" -ForegroundColor Cyan
        $stocks | Where-Object { $_.ChangePct -lt 0 } | Sort-Object ChangePct | 
            Select-Object -First 5 | Format-Table Name,Price,ChangePct -AutoSize
    }
    default {
        Write-Host "GBT A股操盘 PS版 v1.0"
        Write-Host "用法: .\gbt_stock.ps1 scan|analyze|hot [参数]"
    }
}
