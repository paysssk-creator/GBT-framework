# ⛔ 开发者：自由的风
# gbt_trade_engine.py — A股AI全自动操盘引擎 v2.0
# 纯标准库，零依赖。选股→买入→监控→止盈止损→卖出→复盘。
"""
用法:
  python gbt_trade_engine.py scan          # 扫描选股
  python gbt_trade_engine.py analyze CODE  # 深度分析
  python gbt_trade_engine.py monitor       # 监控持仓
  python gbt_trade_engine.py review        # 今日复盘
  python gbt_trade_engine.py auto          # 全自动模式
"""
import json, time, urllib.request, urllib.error, random
from pathlib import Path
from datetime import datetime

TRADE_DIR = Path.home() / '.gbt' / 'trading'
TRADE_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════ 配置 ═══════════════════
CONFIG = {
    "max_positions": 3,         # 最大持仓数
    "max_capital_per_stock": 0.3, # 单股最大仓位30%
    "stop_loss_pct": -2.0,      # 止损线 -2%
    "take_profit_pct": 5.0,     # 止盈线 +5%
    "trailing_stop_pct": 2.0,   # 移动止损 从高点回落2%
    "max_daily_loss_pct": -3.0, # 单日最大亏损
    "min_volume": 100000,       # 最小成交量(手)
    "min_volatility": 2.0,      # 最低波动率
    "blacklist": ["ST", "*ST", "退市"],
    "trade_hours": {"start": "09:30", "end": "14:50"},
}

# ═══════════════════ 行情API ═══════════════════
STOCK_POOL = [
    "sh600519","sz000858","sh601318","sz300750","sh600036",
    "sz002415","sz000333","sh601899","sz002594","sh600900",
    "sh600276","sh600887","sh601012","sz002475","sz300059",
    "sh600030","sh601398","sz000001","sz002230","sz300124",
    "sz000725","sh600050","sh601857","sz002142","sz300498",
    "sh601166","sh600809","sz000651","sz002352","sz300274",
    "sh601088","sh600585","sz000063","sh688981","sz300433",
    "sh600031","sh600690","sz002049","sz300015","sz000776",
]

def fetch_quotes(codes):
    """批量获取行情"""
    text, err = None, "init"
    for api in [_sina_fetch, _tencent_fetch]:
        text, err = api(codes)
        if text:
            break
    if not text:
        return []
    
    stocks = []
    for line in text.strip().split("\n"):
        if not line.strip() or "=" not in line:
            continue
        q = _parse_sina(line) if "hq_str" in line else _parse_tencent(line)
        if q and q.get("price", 0) > 0:
            # 过滤ST/退市
            name = q.get("name", "")
            if any(b in name for b in CONFIG["blacklist"]):
                continue
            stocks.append(q)
    return stocks

def _sina_fetch(codes):
    if isinstance(codes, list):
        codes = ",".join(codes)
    try:
        req = urllib.request.Request(
            f"https://hq.sinajs.cn/list={codes}",
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.read().decode("gbk"), None
    except Exception as e:
        return None, str(e)[:100]

def _tencent_fetch(codes):
    if isinstance(codes, list):
        codes = ",".join(codes)
    try:
        req = urllib.request.Request(
            f"https://qt.gtimg.cn/q={codes}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.read().decode("gbk"), None
    except Exception as e:
        return None, str(e)[:100]

def _parse_sina(line):
    try:
        _, data = line.split("=", 1)
        data = data.strip().strip('";')
        parts = data.split(",")
        if len(parts) < 32:
            return None
        code = line.split("=")[0].replace("var hq_str_", "")
        price = float(parts[3]) if parts[3] else 0
        pre_close = float(parts[2]) if parts[2] else 0
        return {
            "code": code, "name": parts[0],
            "price": price, "open": float(parts[1]) if parts[1] else 0,
            "pre_close": pre_close,
            "high": float(parts[4]) if parts[4] else 0,
            "low": float(parts[5]) if parts[5] else 0,
            "volume": int(float(parts[8])) if parts[8] else 0,
            "amount": float(parts[9]) if parts[9] else 0,
            "change_pct": round((price - pre_close) / pre_close * 100, 2) if pre_close > 0 else 0,
            "change": round(price - pre_close, 2),
            "amplitude": round((float(parts[4]) - float(parts[5])) / pre_close * 100, 2) if pre_close > 0 and parts[4] and parts[5] else 0,
            "time": f"{parts[30]} {parts[31]}" if len(parts) > 31 else "",
        }
    except:
        return None
def _parse_tencent(line):
    try:
        _, data = line.split("=", 1)
        data = data.strip().strip('\";')
        parts = data.split("~")
        if len(parts) < 40:
            return None
        price = float(parts[3]) if parts[3] else 0
        pre_close = float(parts[4]) if parts[4] else 0
        return {
            "code": parts[2].lower() if parts[2] else "",
            "name": parts[1],
            "price": price, "open": float(parts[5]) if parts[5] else 0,
            "pre_close": pre_close,
            "high": float(parts[33]) if parts[33] else 0,
            "low": float(parts[34]) if parts[34] else 0,
            "volume": int(float(parts[6])) if parts[6] else 0,
            "change_pct": float(parts[32]) if parts[32] else 0,
        }
    except:
        return None
# ═══════════════════ 持仓管理 ═══════════════════
def load_positions():
    f = TRADE_DIR / "positions.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

def save_positions(positions):
    (TRADE_DIR / "positions.json").write_text(json.dumps(positions, ensure_ascii=False, indent=2), encoding="utf-8")

def load_orders():
    f = TRADE_DIR / "orders.jsonl"
    if f.exists():
        return [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
    return []

def save_order(order):
    with open(TRADE_DIR / "orders.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(order, ensure_ascii=False) + "\n")

# ═══════════════════ 选股引擎 ═══════════════════
def scan_stocks(limit=30):
    """多因子选股"""
    stocks = fetch_quotes(STOCK_POOL)
    if not stocks:
        return []
    
    candidates = []
    for s in stocks:
        # 过滤条件
        if s["volume"] < CONFIG["min_volume"]:
            continue
        if abs(s["change_pct"]) > 9.5:  # 排除涨跌停
            continue
        
        # 评分
        score = 0
        
        # 涨跌幅因子 (适中为好, 2-5%最佳)
        pct = abs(s["change_pct"])
        if 1 < pct < 3: score += 2
        elif 3 <= pct < 6: score += 3
        elif 6 <= pct < 8: score += 1
        
        # 成交量因子
        vol = s["volume"]
        if vol > 500000: score += 2
        elif vol > 200000: score += 1
        
        # 振幅因子 (有波动才有利润)
        amp = s.get("amplitude", 0)
        if amp > 3: score += 2
        elif amp > CONFIG["min_volatility"]: score += 1
        
        # 趋势因子 (涨比跌好)
        if s["change_pct"] > 0: score += 1
        
        candidates.append({"stock": s, "score": score})
    
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:limit]

# ═══════════════════ 交易信号 ═══════════════════
def generate_signal(stock, positions):
    """生成交易信号"""
    code = stock["code"]
    price = stock["price"]
    change_pct = stock["change_pct"]
    
    # 检查是否已持仓
    if code in positions:
        pos = positions[code]
        entry_price = pos["entry_price"]
        profit_pct = (price - entry_price) / entry_price * 100
        
        # 止盈
        if profit_pct >= CONFIG["take_profit_pct"]:
            return {"action": "SELL", "reason": f"止盈 +{profit_pct:.1f}%", "confidence": 0.9}
        
        # 止损
        if profit_pct <= CONFIG["stop_loss_pct"]:
            return {"action": "SELL", "reason": f"止损 {profit_pct:.1f}%", "confidence": 0.95}
        
        # 移动止损
        high = pos.get("high_since_entry", entry_price)
        if price < high * (1 - CONFIG["trailing_stop_pct"] / 100):
            return {"action": "SELL", "reason": f"移动止损 从高点{high:.2f}回落", "confidence": 0.85}
        
        return {"action": "HOLD", "reason": f"持仓中 +{profit_pct:.1f}%", "confidence": 0.6}
    
    # 未持仓 → 买入评估
    if change_pct > 0 and change_pct < 7:
        amp = stock.get("amplitude", 0)
        vol = stock["volume"]
        
        if amp > 2 and vol > CONFIG["min_volume"]:
            return {"action": "BUY", "reason": f"放量上涨 amp={amp:.1f}% vol={vol}万", "confidence": 0.7}
    
    if change_pct < -3 and stock.get("amplitude", 0) > 4:
        return {"action": "BUY", "reason": f"超跌反弹机会", "confidence": 0.55}
    
    return {"action": "WAIT", "reason": "无信号", "confidence": 0.3}

# ═══════════════════ 风险控制 ═══════════════════
def risk_check(positions, orders_today):
    """风险评估"""
    total_pnl = 0
    for p in positions.values():
        pnl = p.get("unrealized_pnl", 0)
        total_pnl += pnl
    
    risks = []
    if total_pnl / 100000 < CONFIG["max_daily_loss_pct"] / 100:
        risks.append("日亏损超限")
    
    if len(positions) >= CONFIG["max_positions"]:
        risks.append("持仓已满")
    
    today_losses = sum(o.get("amount", 0) for o in orders_today if o.get("action") == "SELL" and o.get("pnl", 0) < 0)
    risk_level = "HIGH" if risks else ("MEDIUM" if total_pnl < 0 else "LOW")
    
    return {"level": risk_level, "risks": risks, "total_pnl": total_pnl, "positions": len(positions)}

# ═══════════════════ 复盘 ═══════════════════
def daily_review():
    orders = load_orders()
    today = datetime.now().strftime("%Y-%m-%d")
    today_orders = [o for o in orders if o.get("timestamp", "").startswith(today)]
    buys = [o for o in today_orders if o.get("action") == "BUY"]
    sells = [o for o in today_orders if o.get("action") == "SELL"]
    positions = load_positions()
    total_buy = sum(o.get("amount", 0) for o in buys)
    total_sell = sum(o.get("amount", 0) for o in sells)
    total_pnl = sum(o.get("pnl", 0) for o in sells)
    win_trades = [o for o in sells if o.get("pnl", 0) > 0]
    report = {
        "date": today, "total_trades": len(today_orders),
        "buy_count": len(buys), "sell_count": len(sells),
        "total_buy_amount": total_buy, "total_sell_amount": total_sell,
        "total_pnl": total_pnl,
        "win_rate": len(win_trades) / len(sells) if sells else 0,
        "current_positions": len(positions),
        "timestamp": datetime.now().isoformat(),
    }
    return report
def auto_trade_cycle():
    """一次完整的自动交易周期"""
    positions = load_positions()
    orders_today = load_orders()
    today_orders = [o for o in orders_today if o.get("timestamp", "").startswith(datetime.now().strftime("%Y-%m-%d"))]
    
    # 1. 风控检查
    risk = risk_check(positions, today_orders)
    if risk["level"] == "HIGH":
        return {"action": "PAUSE", "reason": f"风控阻止: {risk['risks']}", "risk": risk}
    
    # 2. 更新持仓价格
    if positions:
        codes = list(positions.keys())
        quotes = fetch_quotes(codes)
        quote_map = {q["code"]: q for q in quotes}
        for code, pos in positions.items():
            if code in quote_map:
                q = quote_map[code]
                pos["current_price"] = q["price"]
                pos["unrealized_pnl"] = (q["price"] - pos["entry_price"]) * pos["quantity"] * 100
                pos["high_since_entry"] = max(pos.get("high_since_entry", q["price"]), q.get("high", q["price"]))
        save_positions(positions)
    
    # 3. 检查持仓信号
    actions = []
    for code, pos in list(positions.items()):
        if code in quote_map:
            signal = generate_signal(quote_map[code], positions)
            if signal["action"] in ("SELL",):
                pnl = (quote_map[code]["price"] - pos["entry_price"]) * pos["quantity"] * 100
                order = {
                    "id": f"AUTO{int(time.time())}{random.randint(100,999)}",
                    "action": "SELL", "code": code, "price": quote_map[code]["price"],
                    "quantity": pos["quantity"], "amount": quote_map[code]["price"] * pos["quantity"] * 100,
                    "pnl": pnl, "reason": signal["reason"],
                    "timestamp": datetime.now().isoformat(),
                }
                save_order(order)
                del positions[code]
                actions.append(order)
    
    # 4. 选股买入 (如果仓位未满)
    if len(positions) < CONFIG["max_positions"]:
        candidates = scan_stocks(10)
        for c in candidates:
            if len(positions) >= CONFIG["max_positions"]:
                break
            s = c["stock"]
            code = s["code"]
            if code in positions:
                continue
            
            signal = generate_signal(s, positions)
            if signal["action"] == "BUY" and signal["confidence"] > 0.6:
                qty = random.randint(5, 20)  # 模拟手数
                positions[code] = {
                    "entry_price": s["price"], "quantity": qty,
                    "entry_time": datetime.now().isoformat(),
                    "current_price": s["price"], "unrealized_pnl": 0,
                    "high_since_entry": s.get("high", s["price"]),
                }
                order = {
                    "id": f"AUTO{int(time.time())}{random.randint(100,999)}",
                    "action": "BUY", "code": code, "price": s["price"],
                    "quantity": qty, "amount": s["price"] * qty * 100,
                    "reason": signal["reason"], "confidence": signal["confidence"],
                    "timestamp": datetime.now().isoformat(),
                }
                save_order(order)
                actions.append(order)
    
    save_positions(positions)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "positions": len(positions),
        "actions": len(actions),
        "actions_detail": [{"action": a["action"], "code": a["code"], "reason": a.get("reason", "")} for a in actions],
        "risk": risk,
    }

# ═══════════════════ CLI ═══════════════════
if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "scan"
    
    if action == "scan":
        candidates = scan_stocks(20)
        print(json.dumps({"action": "scan", "candidates": len(candidates), "top5": [
            {"code": c["stock"]["code"], "name": c["stock"]["name"], 
             "price": c["stock"]["price"], "change_pct": c["stock"]["change_pct"], 
             "score": c["score"]} for c in candidates[:5]
        ]}, ensure_ascii=False, indent=2))
    
    elif action == "analyze":
        code = sys.argv[2] if len(sys.argv) > 2 else "600519"
        scode = f"sh{code}" if code.startswith("6") else f"sz{code}"
        quotes = fetch_quotes([scode])
        if quotes:
            q = quotes[0]
            signal = generate_signal(q, load_positions())
            print(json.dumps({"code": code, "quote": q, "signal": signal}, ensure_ascii=False, indent=2))
    
    elif action == "monitor":
        positions = load_positions()
        if positions:
            codes = list(positions.keys())
            quotes = fetch_quotes(codes)
            quote_map = {q["code"]: q for q in quotes}
            for code, pos in positions.items():
                if code in quote_map:
                    q = quote_map[code]
                    pos["current_price"] = q["price"]
                    pos["unrealized_pnl"] = (q["price"] - pos["entry_price"]) * pos["quantity"] * 100
                    profit_pct = (q["price"] - pos["entry_price"]) / pos["entry_price"] * 100
                    pos["profit_pct"] = round(profit_pct, 2)
            save_positions(positions)
        print(json.dumps({"action": "monitor", "positions": positions, "count": len(positions)}, ensure_ascii=False, indent=2))
    
    elif action == "review":
        print(json.dumps(daily_review(), ensure_ascii=False, indent=2))
    
    elif action == "auto":
        # 持续运行模式
        print(json.dumps({"action": "auto", "status": "starting"}, ensure_ascii=False))
        while True:
            try:
                result = auto_trade_cycle()
                print(json.dumps(result, ensure_ascii=False))
                time.sleep(60)
            except KeyboardInterrupt:
                print(json.dumps({"action": "auto", "status": "stopped"}, ensure_ascii=False))
                break
            except Exception as e:
                print(json.dumps({"error": str(e)}, ensure_ascii=False))
                time.sleep(30)
    
    else:
        print(json.dumps({"usage": "scan|analyze CODE|monitor|review|auto"}, ensure_ascii=False))
