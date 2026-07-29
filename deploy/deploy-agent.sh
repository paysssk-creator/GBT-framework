#!/bin/bash
# GBT 远程部署代理 · Unix一键安装
# 客户运行: curl -sSL https://gbtxiaotudou.com/deploy-agent.sh | bash
set -e
echo "🥔 GBT 远程部署代理 v3.0"
echo "================================"
echo ""

# 检测Python
if ! command -v python3 &>/dev/null; then
    echo "[1/4] 安装 Python..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip
    elif command -v brew &>/dev/null; then
        brew install python3
    else
        echo "请手动安装Python3后重试"
        exit 1
    fi
fi

# 下载deploy_me.py
AGENT_DIR="$HOME/.gbt/deploy-agent"
mkdir -p "$AGENT_DIR"
echo "[2/4] 下载部署代理..."
curl -sSL -o "$AGENT_DIR/deploy_me.py" https://gbtxiaotudou.com/deploy_me.py

# 启动
SESSION=$RANDOM$RANDOM
cd "$AGENT_DIR"
echo "[3/4] 启动安全隧道..."
python3 deploy_me.py --session "$SESSION"

echo ""
echo "[4/4] 隧道已建立! GBT正在连接..."
echo "请勿关闭此窗口!"
