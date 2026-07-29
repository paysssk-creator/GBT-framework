#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
#  GBT小土豆 OMP原生控制包 — Linux/Mac 全自动安装器
#  开发者：自由的风  ·  一键下载→安装→连接控制
# ═══════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="$HOME/GBTxiaotudouV5"
STAMP="$INSTALL_DIR/.omp_control_installed"

echo ""
echo -e "${CYAN}  ╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}  ║   🧠 GBT小土豆 · OMP原生控制包 v5.0          ║${NC}"
echo -e "${CYAN}  ║   最高执行官 · 一键远程操控部署             ║${NC}"
echo -e "${CYAN}  ╚══════════════════════════════════════════════╝${NC}"
echo ""

if [ -f "$STAMP" ]; then
    echo -e "${GREEN}  ✅ OMP 控制包已安装${NC}"
    echo "  启动: cd $INSTALL_DIR && omp"
    exit 0
fi

# [1/5] Python
echo -e "${GREEN}  [1/5] 检查 Python 3.10+ ...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${YELLOW}  📥 安装 Python3...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install python@3.12
    else
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    fi
fi
echo -e "${GREEN}  ✅ $(python3 --version)${NC}"

# [2/5] Dependencies
echo -e "${GREEN}  [2/5] 安装桌面操控依赖...${NC}"
python3 -m pip install --quiet Pillow mss pyautogui pytesseract easyocr numpy opencv-python 2>/dev/null || true
echo -e "${GREEN}  ✅ 视觉+操控引擎就绪${NC}"

# [3/5] Tesseract
echo -e "${GREEN}  [3/5] 检查 Tesseract-OCR...${NC}"
if ! command -v tesseract &>/dev/null; then
    echo -e "${YELLOW}  📥 安装 Tesseract-OCR...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install tesseract tesseract-lang
    else
        sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra
    fi
fi
echo -e "${GREEN}  ✅ Tesseract-OCR 就绪${NC}"

# [4/5] OMP
echo -e "${GREEN}  [4/5] 安装 OMP 命令行外壳...${NC}"
if ! command -v omp &>/dev/null; then
    echo -e "${YELLOW}  📥 安装 OMP...${NC}"
    curl -fsSL https://omp.sh/install.sh | bash
fi
echo -e "${GREEN}  ✅ OMP $(omp --version 2>&1)${NC}"

# [5/5] GBT Brain
echo -e "${GREEN}  [5/5] 克隆 GBT 大脑 + 配置...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}  📥 更新已有仓库...${NC}"
    cd "$INSTALL_DIR" && git pull origin master 2>/dev/null || true
else
    echo -e "${YELLOW}  📥 克隆 GBT 大脑仓库...${NC}"
    git clone https://github.com/paysssk-creator/GBTxiaotudouV5.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
python3 -m pip install -r requirements.txt -q 2>/dev/null || true

# API Key
echo ""
echo -e "${YELLOW}  🔑 配置 DeepSeek API Key${NC}"
echo "  获取: https://platform.deepseek.com/api_keys"
read -p "  粘贴 API Key (回车跳过): " DS_KEY
if [ -n "$DS_KEY" ]; then
    export DEEPSEEK_API_KEY="$DS_KEY"
    echo "export DEEPSEEK_API_KEY='$DS_KEY'" >> "$HOME/.bashrc"
    echo "export DEEPSEEK_API_KEY='$DS_KEY'" >> "$HOME/.zshrc" 2>/dev/null || true
    echo -e "${GREEN}  ✅ API Key 已保存${NC}"
fi

date > "$STAMP"

# Self-check
echo ""
echo -e "${CYAN}  ─── 运行自检...${NC}"
cd "$INSTALL_DIR"
python3 -c "from brain.boot import boot; boot()" 2>/dev/null || true
python3 -c "from brain.nexus import get_nexus; print(get_nexus().deep_scan()['verdict'])" 2>/dev/null || true

echo ""
echo -e "${CYAN}  ╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}  ║   ✅ GBT小土豆 OMP 原生控制包 部署完成！    ║${NC}"
echo -e "${CYAN}  ║                                              ║${NC}"
echo -e "${CYAN}  ║   启动: cd $INSTALL_DIR && omp              ║${NC}"
echo -e "${CYAN}  ║   远程: omp --mode rpc  |  omp --collab     ║${NC}"
echo -e "${CYAN}  ╚══════════════════════════════════════════════╝${NC}"
echo ""
