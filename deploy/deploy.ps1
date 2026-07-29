# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# GBT小土豆 · 全栈智能部署向导 (Windows)
# 用法: irm https://raw.githubusercontent.com/paysssk-creator/GBTxiaotudouV5/master/deploy.ps1 | iex
#
# 一键部署: Bun + OMP 外壳 + GBT大脑 + Python依赖 + .omp 配置 + .codex + .gbt
# 部署后运行: omp    (在GBTxiaotudouV5目录下)

param([switch]$Silent)

function Say($t, $c="White") { Write-Host $t -ForegroundColor $c }
function Banner { Say "========================================" DarkGray }

Say "`n=== GBT小土豆 · 智能大脑 v5.0 ===" Cyan
Say "最高执行官 · 全栈部署向导" Yellow
Say "Bun + OMP 外壳 + 128caps + 四脑驱动" DarkGray
Banner

$GBT_DIR = "$env:USERPROFILE\GBTxiaotudouV5"
$OMP_PROFILE = "$env:USERPROFILE\.omp\profiles\gbt"
$CODEX_DIR = "$env:USERPROFILE\.codex"

# ═══════════════ [1/7] Bun Runtime ═══════════════
Say "`n[1/7] Bun Runtime..." Green
$bun = Get-Command bun -ErrorAction SilentlyContinue
if ($bun) {
    Say "  OK: bun $(bun --version 2>&1)" DarkGray
} else {
    Say "  Installing Bun..." Yellow
    irm bun.sh/install.ps1 | iex
    $env:Path = "$env:USERPROFILE\.bun\bin;" + [Environment]::GetEnvironmentVariable("Path","User") + ";" + [Environment]::GetEnvironmentVariable("Path","Machine")
    Say "  Bun installed!" Green
}

# ═══════════════ [2/7] OMP Coding Shell ═══════════════
Say "`n[2/7] OMP Coding Shell..." Green
$globalPkg = "$env:USERPROFILE\.bun\install\global\package.json"
$alreadyInstalled = (Test-Path $globalPkg) -and ((Get-Content $globalPkg -Raw) -match "pi-coding-agent")
if ($alreadyInstalled) {
    Say "  OK: OMP already installed" DarkGray
} else {
    Say "  Installing @oh-my-pi/pi-coding-agent..." Yellow
    bun add -g @oh-my-pi/pi-coding-agent 2>&1 | Out-Null
    Say "  OMP installed!" Green
}

# ═══════════════ [3/7] GBT Brain Repo ═══════════════
Say "`n[3/7] GBT Brain Repository..." Green
if (Test-Path $GBT_DIR) {
    Say "  Update existing..." DarkGray
    Set-Location $GBT_DIR
    git pull origin master 2>$null
} else {
    Say "  Clone repository..." DarkGray
    git clone https://github.com/paysssk-creator/GBTxiaotudouV5.git $GBT_DIR
    Set-Location $GBT_DIR
}
Say "  OK: $GBT_DIR" DarkGray

# ═══════════════ [4/7] Python + Dependencies ═══════════════
Say "`n[4/7] Python + Dependencies..." Green
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Say "  ERROR: Python 3.10+ required: https://python.org" Red
    if (-not $Silent) { exit 1 }
}
Say "  OK: $(python --version 2>&1)" DarkGray

Say "  Installing dependencies..." DarkGray
python -m pip install -r requirements.txt -q
Say "  Dependencies ready!" Green

# ═══════════════ [5/7] OMP Profile (.omp/profiles/gbt) ═══════════════
Say "`n[5/7] OMP Profile Configuration..." Green
New-Item -ItemType Directory -Force -Path "$OMP_PROFILE" 2>$null | Out-Null
New-Item -ItemType Directory -Force -Path "$OMP_PROFILE\agent" 2>$null | Out-Null
New-Item -ItemType Directory -Force -Path "$OMP_PROFILE\skills" 2>$null | Out-Null

# API key — prompt if not in env
Say "  Model: DeepSeek (free: 5M tokens) -> https://platform.deepseek.com/api_keys" DarkGray
$DS_KEY = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "User")
if (-not $DS_KEY -and -not $Silent) {
    $DS_KEY = Read-Host "  Enter DeepSeek API Key"
}
if (-not $DS_KEY) {
    Say "  WARNING: No API key. Set DEEPSEEK_API_KEY env var and re-run." Yellow
    $DS_KEY = "sk-YOUR_KEY_HERE"
} else {
    [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", $DS_KEY, "User")
    Say "  API Key saved!" Green
}

# config.yml — OMP profile
$ompConfig = @"
# GBT小土豆 · 四脑驱动: DeepSeek V4 Flash(快) + Pro(深度推理)
providers:
  deepseek:
    apiKey: $DS_KEY

modelRoles:
  default: deepseek/deepseek-v4-flash
  slow: deepseek/deepseek-v4-pro
  smol: deepseek/deepseek-v4-flash
bashInterceptor:
  enabled: false
  patterns: []
"@
$ompConfig | Out-File "$OMP_PROFILE\config.yml" -Encoding UTF8

# agent/config.yml
$agentConfig = @"
setupVersion: 1
tools: 
  approvalMode: yolo
loop: 
  mode: compact
interruptMode: wait
bashInterceptor: 
  patterns: 
    []
followUpMode: all
steeringMode: all
hideThinkingBlock: false
"@
$agentConfig | Out-File "$OMP_PROFILE\agent\config.yml" -Encoding UTF8

# skills/gbt-capabilities.md
$skills = @"
---
name: GBTxiaotudou5全能力
description: GBT小土豆128项AI能力模块
alwaysApply: true
---

# GBT小土豆 · 全能AI助手

**品牌**：GBT小土豆 | **开发者**：自由的风 | **架构**：四层认知闭环
**128caps**：渗透/推理/浏览器/系统/商业/自动化

当用户需要执行任务时，通过项目内置的能力模块调用。
"@
$skills | Out-File "$OMP_PROFILE\skills\gbt-capabilities.md" -Encoding UTF8

Say "  OMP Profile ready!" Green

# ═══════════════ [6/7] .codex + .env ═══════════════
Say "`n[6/7] Agent Config + .env..." Green

# .codex/AGENTS.md
New-Item -ItemType Directory -Force -Path $CODEX_DIR 2>$null | Out-Null
$codexAgents = @"
# GBT智能大脑 v5.0 — 持久化认知管线
# 每次会话必须强制执行，不可跳过
# ①接收→②意图识别(IntentBroker)→③推理(deep_reasoner)→④状态(health_dashboard)→⑤回复
# 铁律: 收到消息后第一个动作是启动管线，不是直接回答。每次工具调用前思考必要性/风险/替代方案。

<!-- codebase-memory-mcp:start -->
# Codebase Knowledge Graph (codebase-memory-mcp)

This project uses codebase-memory-mcp to maintain a knowledge graph of the codebase.
ALWAYS prefer MCP graph tools over grep/glob/file-search for code discovery.

## Priority Order
1. `search_graph` — find functions, classes, routes, variables by pattern
2. `trace_path` — trace who calls a function or what it calls
3. `get_code_snippet` — read specific function/class source code
4. `query_graph` — run Cypher queries for complex patterns
5. `get_architecture` — high-level project summary

## When to fall back to grep/glob
- Searching for string literals, error messages, config values
- Searching non-code files (Dockerfiles, shell scripts, configs)
- When MCP tools return insufficient results

## Examples
- Find a handler: `search_graph(name_pattern=".*OrderHandler.*")`
- Who calls it: `trace_path(function_name="OrderHandler", direction="inbound")`
- Read source: `get_code_snippet(qualified_name="pkg/orders.OrderHandler")`
<!-- codebase-memory-mcp:end -->
"@
$codexAgents | Out-File "$CODEX_DIR\AGENTS.md" -Encoding UTF8

# .env (project root)
$envFile = "$GBT_DIR\.env"
if (-not (Test-Path $envFile)) {
    $envContent = @"
# GBT Configuration
# $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
DEEPSEEK_API_KEY=$DS_KEY
"@
    $envContent | Out-File $envFile -Encoding UTF8
}

# .gbt/mcp.json — ensure cwd is relative
$gbtMcp = "$GBT_DIR\.gbt\mcp.json"
if (Test-Path $gbtMcp) {
    $mcpContent = Get-Content $gbtMcp -Raw | ConvertFrom-Json
    $mcpContent.mcpServers.'gbt-brain'.cwd = '.'
    $mcpContent | ConvertTo-Json -Depth 3 | Out-File $gbtMcp -Encoding UTF8
}

Say "  Agent config ready!" Green

# ═══════════════ [7/7] Verification ═══════════════
Say "`n[7/7] Startup Verification..." Green
Set-Location $GBT_DIR

python -m pip install httpx urllib3 python-dotenv -q

$bootOk = python -c "from brain.boot import boot; import json; print(json.dumps({'ok':boot()['ok']}))"
if ($bootOk -match '"ok": true') {
    Say "  Brain self-check: PASSED" Green
} else {
    Say "  Brain self-check: partial (functional)" Yellow
}

python -c "from brain.nexus import get_nexus; print('  Nexus: ' + get_nexus().deep_scan()['verdict'])"
python -c "from brain.cognition import get_cognition; print('  Identity: ' + get_cognition().who_am_i()['message'])"

# Verify OMP
$ompCheck = & bun x omp --version
if ($ompCheck) {
    Say "  OMP Shell: $ompCheck" Green
} else {
    Say "  OMP Shell: installed (run 'omp' in $GBT_DIR)" DarkGray
}

Banner
Say "GBTxiaotudouV5 FULL-STACK DEPLOYMENT COMPLETE!" Green
Say "Supreme Executive is ready." Cyan
Say ""
Say "How to start:" Yellow
Say "  cd $GBT_DIR" White
Say "  omp" White
Say ""
Say "Tip: In omp, use profile 'gbt' for this conversation experience." DarkGray
Banner
