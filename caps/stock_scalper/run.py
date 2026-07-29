# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
stock_scalper/run.py — A股快进快出操盘引擎
==========================================
行情源: 新浪财经 | AI引擎: DeepSeek | 策略: 涨幅动量快进快出
止盈: +3% | 止损: -1.5% | 持有: 分钟级
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_DIR = Path.home() / ".gbt" / "stock_scalper"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"
TRADES_DIR = DATA_DIR / "trades"
TRADES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
    "deepseek_api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
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
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2),
                           encoding="utf-8")


# ══════════════════════════════════════════════════════════════
#  行情数据 — 新浪接口
# ══════════════════════════════════════════════════════════════

# 活跃股票池（上证50+深证50成分股，确保有行情数据）
ACTIVE_POOL = [
    # 上证
    "sh600519", "sh600036", "sh600030", "sh601318", "sh600276",
    "sh600887", "sh601166", "sh600900", "sh601398", "sh600809",
    "sh601899", "sh600585", "sh601088", "sh600031", "sh600104",
    "sh601857", "sh600028", "sh600050", "sh601628", "sh601688",
    "sh600309", "sh600690", "sh600048", "sh601012", "sh600406",
    # 深证
    "sz000858", "sz000333", "sz000651", "sz002415", "sz000568",
    "sz002594", "sz000725", "sz002230", "sz002475", "sz002304",
    "sz000002", "sz000063", "sz002142", "sz000001", "sz002714",
    "sz002027", "sz300750", "sz300059", "sz300124", "sz300015",
    "sz300274", "sz300394", "sz300502", "sz300433", "sz300760",
]


def _fetch_sina(codes):
    """从新浪获取实时行情"""
    url = "http://hq.sinajs.cn/list=" + ",".join(codes)
    headers = {"Referer": "https://finance.sina.com.cn"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("gbk")
    except Exception as e:
        return None


def _parse_sina_line(code, data):
    """解析单条新浪行情数据"""
    try:
        parts = data.split(",")
        if len(parts) < 32:
            return None
        name = parts[0]
        open_p = float(parts[1]) if parts[1] else 0
        prev_close = float(parts[2]) if parts[2] else 0
        price = float(parts[3]) if parts[3] else 0
        high = float(parts[4]) if parts[4] else 0
        low = float(parts[5]) if parts[5] else 0
        volume = float(parts[8]) if parts[8] else 0
        amount = float(parts[9]) if parts[9] else 0

        if price <= 0:
            return None

        change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0
        return {
            "code": code,
            "name": name,
            "price": price,
            "open": open_p,
            "high": high,
            "low": low,
            "prev_close": prev_close,
            "change_pct": change_pct,
            "volume": volume,
            "amount": amount,
        }
    except (ValueError, IndexError):
        return None


def fetch_market_data(sort="change_pct", limit=30):
    """获取实时行情并排序"""
    codes = ACTIVE_POOL[:min(limit * 2, len(ACTIVE_POOL))]
    raw = _fetch_sina(codes)
    if not raw:
        return {"ok": False, "error": "新浪行情获取失败，请检查网络"}

    results = []
    for line in raw.strip().split("\n"):
        if not line or "=" not in line:
            continue
        try:
            code_raw = line.split("=")[0].strip()
            # hq_str_sh600519 → sh600519
            code = code_raw.replace("var hq_str_", "").strip()
            quote_str = line.split('"')[1] if '"' in line else ""
            if not quote_str or quote_str == "":
                continue
            stock = _parse_sina_line(code, quote_str)
            if stock:
                results.append(stock)
        except Exception:
            continue

    if sort == "change_pct":
        results.sort(key=lambda x: x["change_pct"], reverse=True)
    elif sort == "volume":
        results.sort(key=lambda x: x["volume"], reverse=True)

    return {"ok": True, "total": len(results), "stocks": results[:limit],
            "timestamp": datetime.now().isoformat()}


# ══════════════════════════════════════════════════════════════
#  市场情绪
# ══════════════════════════════════════════════════════════════

def market_sentiment():
    """计算市场情绪指标"""
    data = fetch_market_data(limit=50)
    if not data.get("ok"):
        return {"ok": False, "error": data.get("error")}

    stocks = data["stocks"]
    up_count = sum(1 for s in stocks if s["change_pct"] > 0)
    down_count = sum(1 for s in stocks if s["change_pct"] < 0)
    flat_count = len(stocks) - up_count - down_count

    limit_up = sum(1 for s in stocks if s["change_pct"] >= 9.8)
    limit_down = sum(1 for s in stocks if s["change_pct"] <= -9.8)

    up_ratio = round(up_count / len(stocks) * 100, 1) if stocks else 0
    avg_change = round(sum(s["change_pct"] for s in stocks) / len(stocks), 2) if stocks else 0

    # 情绪打分 0-100
    score = min(100, max(0, int(50 + up_ratio * 0.5 + avg_change * 3)))
    if score >= 70:
        mood = "STRONG_BULL"
    elif score >= 55:
        mood = "BIAS_BULL"
    elif score >= 45:
        mood = "NEUTRAL"
    elif score >= 30:
        mood = "BIAS_BEAR"
    else:
        mood = "STRONG_BEAR"

    return {
        "ok": True,
        "total_stocks": len(stocks),
        "up": up_count,
        "down": down_count,
        "flat": flat_count,
        "up_ratio": up_ratio,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "avg_change": avg_change,
        "mood_score": score,
        "mood": mood,
        "timestamp": datetime.now().isoformat()
    }


# ══════════════════════════════════════════════════════════════
#  AI 分析
# ══════════════════════════════════════════════════════════════

def ai_analyze(prompt):
    """调用DeepSeek分析"""
    config = load_config()
    api_key = config.get("deepseek_api_key", "")

    if not api_key:
        # 无API Key时使用启发式规则
        return _heuristic_analyze(prompt)

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
            {"Authorization": f"Bearer {api_key}",
             "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            json_match = re.search(r'\{[^{}]*\}', content)
            if json_match:
                return json.loads(json_match.group())
            return {"momentum": "中", "buy": False,
                    "hold_minutes": 0, "risk": content[:100]}
    except Exception as e:
        return _heuristic_analyze(prompt)


def _heuristic_analyze(prompt):
    """无API时的启发式分析"""
    # 从prompt提取涨幅
    pct_match = re.search(r'涨幅([\-\d.]+)%', prompt)
    pct = float(pct_match.group(1)) if pct_match else 0

    if pct > 5:
        return {"momentum": "强", "buy": True, "hold_minutes": 5,
                "risk": "高位追涨风险"}
    elif pct > 2:
        return {"momentum": "中", "buy": True, "hold_minutes": 10,
                "risk": "中等风险"}
    elif pct > 0:
        return {"momentum": "弱", "buy": False, "hold_minutes": 0,
                "risk": "动能不足"}
    else:
        return {"momentum": "弱", "buy": False, "hold_minutes": 0,
                "risk": "下跌趋势"}


# ══════════════════════════════════════════════════════════════
#  快进快出策略
# ══════════════════════════════════════════════════════════════

def scalp_trade(max_stocks=5, max_amount=100000, min_change=2.0,
                max_change=8.0, take_profit=3.0, stop_loss=-1.5):
    """快进快出主策略"""
    result = {
        "ok": True,
        "strategy": "scalp",
        "params": {"take_profit": take_profit, "stop_loss": stop_loss},
        "trades": [],
        "timestamp": datetime.now().isoformat()
    }

    market = fetch_market_data(sort="change_pct", limit=50)
    if not market["ok"]:
        return {"ok": False, "error": market.get("error", "行情获取失败")}

    candidates = []
    for stock in market["stocks"]:
        name = stock.get("name", "")
        pct = stock.get("change_pct", 0)
        if "ST" in name or "退" in name or "N" in name:
            continue
        if pct < min_change or pct > max_change:
            continue
        candidates.append(stock)

    candidates = candidates[:max_stocks]

    if not candidates:
        result["message"] = "当前无符合条件的快进快出候选"
        result["total_trades"] = 0
        return result

    for stock in candidates:
        code = stock["code"]
        name = stock["name"]
        pct = stock["change_pct"]

        prompt = (
            f"A股{name}({code})当前涨幅{pct}%。"
            f"请判断是否适合短线快进快出。"
            f'用JSON回答: {{"momentum":"强或中或弱","buy":true或false,'
            f'"hold_minutes":数字,"risk":"一句话风险"}}'
        )

        ai = ai_analyze(prompt)

        if ai.get("buy") and ai.get("momentum") in ("强", "中"):
            qty = min(int(max_amount / stock["price"] / 100), 50)
            if qty > 0:
                trade = {
                    "code": code,
                    "name": name,
                    "action": "BUY",
                    "price": stock["price"],
                    "quantity": qty * 100,
                    "change_pct": pct,
                    "ai_momentum": ai.get("momentum"),
                    "ai_risk": ai.get("risk", ""),
                    "take_profit_pct": take_profit,
                    "stop_loss_pct": stop_loss,
                    "timestamp": datetime.now().isoformat()
                }
                result["trades"].append(trade)
                _log_trade(trade)

    result["total_trades"] = len(result["trades"])
    if result["total_trades"] > 0:
        names = ", ".join(t["name"] for t in result["trades"])
        result["summary"] = (
            f"🔫 快进快出: {result['total_trades']}笔买入({names}), "
            f"止盈+{take_profit}%, 止损{stop_loss}%"
        )
    else:
        result["summary"] = "AI判定当前候选不适合买入"

    return result


def _log_trade(trade):
    """记录交易到日志"""
    today = datetime.now().strftime("%Y%m%d")
    log_file = TRADES_DIR / f"trades_{today}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(trade, ensure_ascii=False) + "\n")


# ══════════════════════════════════════════════════════════════
#  复盘
# ══════════════════════════════════════════════════════════════

def trade_review(days=1):
    """查看近期交易记录"""
    trades = []
    for f in sorted(TRADES_DIR.glob("trades_*.jsonl"), reverse=True)[:days]:
        try:
            for line in f.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    trades.append(json.loads(line))
        except Exception:
            continue

    if not trades:
        return {"ok": True, "total": 0, "trades": [], "message": "暂无交易记录"}

    buy_count = len(trades)
    total_amount = sum(t.get("price", 0) * t.get("quantity", 0) for t in trades)

    return {
        "ok": True,
        "total": buy_count,
        "total_amount": round(total_amount, 2),
        "trades": trades[-20:],
        "period": f"最近{days}天",
        "timestamp": datetime.now().isoformat()
    }


# ══════════════════════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════════════════════

def do_scan(params):
    limit = int(params.get("limit", 30))
    sort = params.get("sort", "change_pct")
    return fetch_market_data(sort=sort, limit=min(limit, 50))


def do_scalp(params):
    config = load_config()
    strategy = config.get("strategy", DEFAULT_CONFIG["strategy"])
    return scalp_trade(
        max_stocks=int(params.get("max_stocks", strategy["max_stocks"])),
        max_amount=int(params.get("max_amount", strategy["max_amount"])),
        min_change=float(params.get("min_change", strategy["min_change"])),
        max_change=float(params.get("max_change", strategy["max_change"])),
        take_profit=float(params.get("take_profit", strategy["take_profit"])),
        stop_loss=float(params.get("stop_loss", strategy["stop_loss"])),
    )


def do_status(params):
    config = load_config()
    return {
        "ok": True,
        "strategy": config.get("strategy", {}),
        "api_configured": bool(config.get("deepseek_api_key")),
        "trading_hours": config.get("trading_hours", {}),
        "data_dir": str(DATA_DIR),
        "active_pool": len(ACTIVE_POOL),
    }


def do_config(params):
    action = params.get("action", "view")
    if action == "set":
        args = params.get("args", [])
        if isinstance(args, str):
            args = [args]
        config = load_config()
        for arg in args:
            if "=" in arg:
                k, v = arg.split("=", 1)
                keys = k.split(".")
                target = config
                for key in keys[:-1]:
                    target = target.setdefault(key, {})
                try:
                    v = json.loads(v)
                except Exception:
                    pass
                target[keys[-1]] = v
        save_config(config)
        return {"ok": True, "message": "配置已保存", "config": config}
    return {"ok": True, "config": load_config()}


def do_sentiment(params):
    return market_sentiment()


def do_review(params):
    days = int(params.get("days", 1))
    return trade_review(days=min(days, 30))


HANDLERS = {
    "scan": do_scan,
    "scalp": do_scalp,
    "status": do_status,
    "config": do_config,
    "sentiment": do_sentiment,
    "review": do_review,
}


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            params = {"raw": sys.argv[2]}

    h = HANDLERS.get(action, do_status)
    try:
        result = h(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)[:200]},
                         ensure_ascii=False))
