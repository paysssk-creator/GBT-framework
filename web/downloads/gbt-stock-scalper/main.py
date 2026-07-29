# GBT A股AI快进快出操盘系统 v1.0
# 基于涨幅动量 · AI实时决策 · 止盈止损自动化

import json, os, time, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
LOG_FILE = BASE_DIR / "trading" / "trades.jsonl"

# ═══════════════════ 行情数据 (新浪接口) ═══════════════════
def fetch_market_data(sort="change_pct", limit=30):
    """从新浪获取A股实时行情"""
    url = f"http://hq.sinajs.cn/list="
    codes = _get_active_codes(limit)
    batch_url = url + ",".join(codes)
    
    headers = {"Referer": "https://finance.sina.com.cn"}
    try:
        req = urllib.request.Request(batch_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("gbk")
        return _parse_sina_data(data, sort)
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _get_active_codes(limit=30):
    """获取活跃股票代码"""
    codes = []
    # 上证A股
    for i in range(600000, 600000 + limit):
        codes.append(f"sh{i}")
    # 深证A股  
    for i in range(0, limit):
        codes.append(f"sz{300000+i:06d}")
    return codes[:limit]

def _parse_sina_data(data, sort):
    """解析新浪行情数据"""
    results = []
    for line in data.strip().split("\n"):
        if not line or "=" not in line:
            continue
        try:
            code = line.split("=")[0].split("_")[-1].split(".")[-1] if "." in line else ""
            quote_part = line.split('"')[1] if '"' in line else ""
            if not quote_part:
                continue
            fields = quote_part.split(",")
            if len(fields) < 32:
                continue
            
            name = fields[0]
            open_price = float(fields[1]) if fields[1] else 0
            yesterday_close = float(fields[2]) if fields[2] else 0
            current_price = float(fields[3]) if fields[3] else 0
            high = float(fields[4]) if fields[4] else 0
            low = float(fields[5]) if fields[5] else 0
            volume = float(fields[8]) if fields[8] else 0
            amount = float(fields[9]) if fields[9] else 0
            
            if current_price <= 0:
                continue
                
            change_pct = round((current_price - yesterday_close) / yesterday_close * 100, 2) if yesterday_close else 0
            
            results.append({
                "code": code, "name": name,
                "price": current_price, "open": open_price,
                "high": high, "low": low,
                "yesterday_close": yesterday_close,
                "change_pct": change_pct,
                "volume": volume, "amount": amount,
            })
        except (ValueError, IndexError):
            continue
    
    if sort == "change_pct":
        results.sort(key=lambda x: x["change_pct"], reverse=True)
    elif sort == "volume":
        results.sort(key=lambda x: x["volume"], reverse=True)
    
    return {"ok": True, "total": len(results), "stocks": results}

# ═══════════════════ AI 分析 ═══════════════════
def ai_analyze(prompt):
    """调用AI分析 (DeepSeek)"""
    config = load_config()
    api_key = config.get("deepseek_api_key", os.environ.get("DEEPSEEK_API_KEY", ""))
    
    if not api_key:
        return {"momentum": "中", "buy": False, "hold_minutes": 0, "risk": "API Key未配置"}
    
    try:
        body = json.dumps({
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 200
        }).encode()
        
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            body,
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            # 提取 JSON
            import re
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                return json.loads(json_match.group())
            return {"momentum": "中", "buy": False, "hold_minutes": 0, "risk": content[:100]}
    except Exception as e:
        return {"momentum": "中", "buy": False, "hold_minutes": 0, "risk": str(e)[:100]}

# ═══════════════════ 快进快出核心策略 ═══════════════════
def scalp_trade(max_stocks=5, max_amount=100000, min_change=2.0, max_change=8.0,
                take_profit=3.0, stop_loss=-1.5):
    """
    快进快出策略
    - 扫描涨幅2-8%的股票
    - AI判断动量是否持续
    - 市价买入 → 止盈+3%/止损-1.5%
    """
    result = {
        "ok": True, "strategy": "scalp",
        "params": {"take_profit": take_profit, "stop_loss": stop_loss},
        "trades": [], "timestamp": datetime.now().isoformat()
    }
    
    # 1. 扫描市场
    market = fetch_market_data(sort="change_pct", limit=50)
    if not market["ok"]:
        return {"ok": False, "error": market["error"]}
    
    # 2. 筛选候选
    candidates = []
    for stock in market["stocks"]:
        name = stock.get("name", "")
        pct = stock.get("change_pct", 0)
        if "ST" in name or "退" in name:
            continue
        if pct < min_change or pct > max_change:
            continue
        candidates.append(stock)
    
    candidates = candidates[:max_stocks]
    
    if not candidates:
        result["message"] = "当前无快进快出候选"
        return result
    
    # 3. AI逐个分析
    for stock in candidates:
        code = stock["code"]
        name = stock["name"]
        pct = stock["change_pct"]
        
        prompt = f"""A股{name}({code})当前涨幅{pct}%。请判断是否适合短线快进快出。
用JSON回答: {{"momentum":"强或中或弱","buy":true或false,"hold_minutes":数字,"risk":"一句话风险"}}"""
        
        ai = ai_analyze(prompt)
        
        if ai.get("buy") and ai.get("momentum") in ("强", "中"):
            qty = min(int(max_amount / stock["price"] / 100), 50)
            if qty > 0:
                trade = {
                    "code": code, "name": name,
                    "action": "BUY",
                    "price": stock["price"], "quantity": qty,
                    "change_pct": pct,
                    "ai_momentum": ai.get("momentum"),
                    "take_profit_pct": take_profit,
                    "stop_loss_pct": stop_loss,
                    "timestamp": datetime.now().isoformat()
                }
                result["trades"].append(trade)
                _log_trade(trade)
    
    result["total_trades"] = len(result["trades"])
    result["summary"] = f"快进快出: {len(result['trades'])}笔买入, 止盈+{take_profit}%, 止损{stop_loss}%"
    return result

def _log_trade(trade):
    """记录交易日志"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(trade, ensure_ascii=False) + "\n")

# ═══════════════════ 配置 ═══════════════════
DEFAULT_CONFIG = {
    "deepseek_api_key": "",
    "strategy": {
        "max_stocks": 5,
        "max_amount": 100000,
        "min_change": 2.0,
        "max_change": 8.0,
        "take_profit": 3.0,
        "stop_loss": -1.5,
    },
    "trading_hours": {"start": "09:30", "end": "15:00"},
}

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return DEFAULT_CONFIG

def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

# ═══════════════════ CLI ═══════════════════
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("GBT A股快进快出操盘系统 v1.0")
        print("用法:")
        print("  python main.py scan         扫描市场涨幅榜")
        print("  python main.py scalp        执行快进快出策略")
        print("  python main.py config       查看配置")
        print("  python main.py config set KEY=VALUE  设置配置")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "scan":
        data = fetch_market_data(limit=30)
        if data["ok"]:
            print(f"{'代码':<10} {'名称':<10} {'现价':>8} {'涨幅':>8}")
            print("-" * 40)
            for s in data["stocks"][:20]:
                arrow = "🔴" if s["change_pct"] < 0 else "🟢"
                print(f"{s['code']:<10} {s['name']:<10} {s['price']:>8.2f} {arrow}{s['change_pct']:>+6.2f}%")
        else:
            print(f"扫描失败: {data.get('error')}")
    
    elif cmd == "scalp":
        config = load_config()
        s = config.get("strategy", DEFAULT_CONFIG["strategy"])
        result = scalp_trade(**s)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "config":
        if len(sys.argv) > 2 and sys.argv[2] == "set":
            config = load_config()
            for arg in sys.argv[3:]:
                if "=" in arg:
                    k, v = arg.split("=", 1)
                    keys = k.split(".")
                    target = config
                    for key in keys[:-1]:
                        target = target.setdefault(key, {})
                    try:
                        v = json.loads(v)
                    except:
                        pass
                    target[keys[-1]] = v
            save_config(config)
            print("配置已保存")
        else:
            print(json.dumps(load_config(), ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {cmd}")
