#!/bin/bash
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# GBT小土豆 · 全栈智能部署向导 (Linux/Mac)
# 用法: curl -sSL https://raw.githubusercontent.com/paysssk-creator/GBTxiaotudouV5/master/deploy.sh | bash
#
# 一键部署: Bun + OMP 外壳 + GBT大脑 + Python依赖 + .omp 配置 + .codex + .gbt
# 部署后运行: omp    (在GBTxiaotudouV5目录下)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}🧠 GBT小土豆 · 智能大脑 v5.0${NC}"
echo -e "${YELLOW}👑 最高执行官 · 全栈部署向导${NC}"
echo -e "Bun + OMP 外壳 + 128cap + 四脑驱动"
echo -e "========================================"

GBT_DIR="$HOME/GBTxiaotudouV5"
OMP_PROFILE="$HOME/.omp/profiles/gbt"
CODEX_DIR="$HOME/.codex"

# ═══════════════ [1/7] Bun Runtime ═══════════════
echo -e "\n${GREEN}🥟 [1/7] Bun Runtime...${NC}"
if command -v bun &>/dev/null; then
    echo -e "  ✅ bun $(bun --version 2>&1)"
else
    echo -e "  ${YELLOW}安装 Bun...${NC}"
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.bun/bin:$PATH"
    echo -e "  ${GREEN}✅ Bun 已安装${NC}"
fi

# ═══════════════ [2/7] OMP Coding Shell ═══════════════
echo -e "\n${GREEN}💻 [2/7] OMP Coding Shell...${NC}"
if bun pm ls -g 2>/dev/null | grep -q "pi-coding-agent"; then
    echo -e "  ✅ OMP 已安装"
else
    echo -e "  ${YELLOW}安装 @oh-my-pi/pi-coding-agent...${NC}"
    bun add -g @oh-my-pi/pi-coding-agent
    echo -e "  ${GREEN}✅ OMP 已安装${NC}"
fi

# ═══════════════ [3/7] GBT Brain Repo ═══════════════
echo -e "\n${GREEN}📦 [3/7] GBT Brain Repository...${NC}"
if [ -d "$GBT_DIR" ]; then
    echo "  更新现有仓库..."
    cd "$GBT_DIR" && git pull origin master 2>/dev/null
else
    echo "  克隆仓库..."
    git clone https://github.com/paysssk-creator/GBTxiaotudouV5.git "$GBT_DIR"
    cd "$GBT_DIR"
fi
echo -e "  ✅ $GBT_DIR"

# ═══════════════ [4/7] Python + Dependencies ═══════════════
echo -e "\n${GREEN}🐍 [4/7] Python + Dependencies...${NC}"
PYTHON=""
for p in python3 python; do
    if command -v $p &>/dev/null; then
        PYTHON=$p
        echo -e "  ✅ Python: $($PYTHON --version 2>&1)"
        break
    fi
done
[ -z "$PYTHON" ] && echo -e "${RED}  ❌ 请安装Python 3.10+${NC}" && exit 1

echo "  安装依赖..."
$PYTHON -m pip install -r requirements.txt -q
echo -e "  ${GREEN}✅ 依赖就绪${NC}"

# ═══════════════ [5/7] OMP Profile ═══════════════
echo -e "\n${GREEN}⚙️  [5/7] OMP Profile Configuration...${NC}"
mkdir -p "$OMP_PROFILE/agent" "$OMP_PROFILE/skills"

# API key
echo -e "  🔑 模型: DeepSeek -> https://platform.deepseek.com/api_keys"
if [ -z "$DEEPSEEK_API_KEY" ]; then
    read -p "  输入 DeepSeek API Key: " DS_KEY
else
    DS_KEY="$DEEPSEEK_API_KEY"
    echo -e "  ✅ 从环境变量读取"
fi
if [ -z "$DS_KEY" ]; then
    echo -e "  ${YELLOW}⚠️  未配置API Key。设置 DEEPSEEK_API_KEY 后重运行。${NC}"
    DS_KEY="sk-YOUR_KEY_HERE"
else
    echo -e "  ${GREEN}✅ API Key 已保存${NC}"
fi

# config.yml
cat > "$OMP_PROFILE/config.yml" << OMPCONF
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
OMPCONF

# agent/config.yml
cat > "$OMP_PROFILE/agent/config.yml" << AGENTCONF
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
AGENTCONF

# skills/gbt-capabilities.md
cat > "$OMP_PROFILE/skills/gbt-capabilities.md" << SKILLS
---
name: GBTxiaotudou5全能力
description: GBT小土豆128项AI能力模块
alwaysApply: true
---

# GBT小土豆 · 全能AI助手

**品牌**：GBT小土豆 | **开发者**：自由的风 | **架构**：四层认知闭环
**128caps**：渗透/推理/浏览器/系统/商业/自动化
SKILLS

echo -e "  ${GREEN}✅ OMP Profile 就绪${NC}"

# ═══════════════ [6/7] .codex + .env ═══════════════
echo -e "\n${GREEN}📝 [6/7] Agent Config + .env...${NC}"

mkdir -p "$CODEX_DIR"
cat > "$CODEX_DIR/AGENTS.md" << CODEX
# GBT智能大脑 v5.0 — 持久化认知管线
# 每次会话必须强制执行，不可跳过
# ①接收→②意图识别(IntentBroker)→③推理(deep_reasoner)→④状态(health_dashboard)→⑤回复
# 铁律: 收到消息后第一个动作是启动管线，不是直接回答。每次工具调用前思考必要性/风险/替代方案。

<!-- codebase-memory-mcp:start -->
# Codebase Knowledge Graph (codebase-memory-mcp)

This project uses codebase-memory-mcp to maintain a knowledge graph of the codebase.
ALWAYS prefer MCP graph tools over grep/glob/file-search for code discovery.

## Priority Order
1. \`search_graph\` — find functions, classes, routes, variables by pattern
2. \`trace_path\` — trace who calls a function or what it calls
3. \`get_code_snippet\` — read specific function/class source code
4. \`query_graph\` — run Cypher queries for complex patterns
5. \`get_architecture\` — high-level project summary

## When to fall back to grep/glob
- Searching for string literals, error messages, config values
- Searching non-code files (Dockerfiles, shell scripts, configs)
- When MCP tools return insufficient results
<!-- codebase-memory-mcp:end -->
CODEX

# .env
ENV_FILE="$GBT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << ENVEOF
# GBT Configuration
# $(date '+%Y-%m-%d %H:%M:%S')
DEEPSEEK_API_KEY=$DS_KEY
ENVEOF
fi

# .gbt/mcp.json — ensure relative cwd
if [ -f "$GBT_DIR/.gbt/mcp.json" ]; then
    $PYTHON -c "
import json
with open('$GBT_DIR/.gbt/mcp.json') as f: c = json.load(f)
c['mcpServers']['gbt-brain']['cwd'] = '.'
with open('$GBT_DIR/.gbt/mcp.json', 'w') as f: json.dump(c, f, indent=2)
" 2>/dev/null
fi

echo -e "  ${GREEN}✅ Agent config 就绪${NC}"

# ═══════════════ [7/7] Verification ═══════════════
echo -e "\n${GREEN}🩺 [7/7] Startup Verification...${NC}"
cd "$GBT_DIR"

$PYTHON -m pip install httpx urllib3 python-dotenv -q

$PYTHON -c "from brain.boot import boot; r=boot(); print(f'  {\"✅\" if r[\"ok\"] else \"⚠️\"} 大脑自检')"
$PYTHON -c "from brain.nexus import get_nexus; print(f'  邻域: {get_nexus().deep_scan()[\"verdict\"]}')"
$PYTHON -c "from brain.cognition import get_cognition; print(f'  {get_cognition().who_am_i()[\"message\"]}')"

if command -v omp &>/dev/null; then
    echo -e "  ${GREEN}✅ OMP Shell: 就绪${NC}"
else
    echo -e "  ${YELLOW}⚠️  OMP: 请运行 'omp' 启动${NC}"
fi

echo -e "\n========================================"
echo -e "${GREEN}✅ GBTxiaotudouV5 全栈部署完成!${NC}"
echo -e "${CYAN}👑 最高执行官已就绪${NC}"
echo ""
echo "启动方式:"
echo "  cd $GBT_DIR"
echo "  omp"
echo ""
echo "提示: omp内使用 profile 'gbt' 获得完整对话体验"
echo "========================================"
