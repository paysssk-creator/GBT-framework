# 开发者：自由的风
"""stock_browser_trader/run.py — 指纹浏览器+A股AI操盘融合引擎
=============================================================
融合 fingerprint_browser + browser_automation + stock_trader
+ deep_reasoner AI决策, 实现全自动A股Web操盘。

支持平台: 东方财富/同花顺/雪球/新浪财经
核心能力: 指纹伪装→自动登录→行情扫描→AI分析→模拟交易→风控
"""
import sys, json, os, time, random, base64, hashlib, urllib.request, urllib.error, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent))
CAPS_DIR = Path(__file__).parent.parent

TRADE_DIR = Path.home() / '.gbt' / 'trading'
BROWSER_PROFILES_DIR = Path.home() / '.gbt' / 'browser_profiles'
TRADE_DIR.mkdir(parents=True, exist_ok=True)
BROWSER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════ A股Web平台配置 ═══════════════════
A_STOCK_PLATFORMS = {
    "eastmoney": {
        "name": "东方财富",
        "base_url": "https://www.eastmoney.com",
        "login_url": "https://passport.eastmoney.com/login",
        "quote_url": "https://quote.eastmoney.com/{code}.html",
        "search_url": "https://search.eastmoney.com/search?kw={keyword}",
        "data_center": "https://data.eastmoney.com/stockdata/",
        "stock_code_prefix": {"sh": "1", "sz": "0"},
    },
    "10jqka": {
        "name": "同花顺",
        "base_url": "https://www.10jqka.com.cn",
        "login_url": "https://passport.10jqka.com.cn/login",
        "quote_url": "https://stockpage.10jqka.com.cn/{code}/",
        "search_url": "https://www.10jqka.com.cn/search?q={keyword}",
        "data_center": "https://data.10jqka.com.cn/",
        "stock_code_prefix": {"sh": "sh", "sz": "sz"},
    },
    "xueqiu": {
        "name": "雪球",
        "base_url": "https://xueqiu.com",
        "login_url": "https://xueqiu.com/login",
        "quote_url": "https://xueqiu.com/S/{code}",
        "search_url": "https://xueqiu.com/search?q={keyword}",
        "data_center": "https://xueqiu.com/hq",
        "stock_code_prefix": {"sh": "SH", "sz": "SZ"},
    },
    "sina": {
        "name": "新浪财经",
        "base_url": "https://finance.sina.com.cn",
        "login_url": "https://passport.weibo.com/sso/login",
        "quote_url": "https://finance.sina.com.cn/realstock/company/{code}/nc.shtml",
        "search_url": "https://search.sina.com.cn/?q={keyword}&c=finance",
        "data_center": "https://vip.stock.finance.sina.com.cn/",
        "stock_code_prefix": {"sh": "sh", "sz": "sz"},
    },
}

# 指纹模板 — 每个平台独立指纹环境
FINGERPRINT_TEMPLATES = {
    "win_chrome_retail": {
        "platform": "Win32", "vendor": "Google Inc.",
        "canvas_noise": 0.15, "webgl_vendor": "Intel Inc.",
        "webgl_renderer": "Intel(R) UHD Graphics 620",
        "timezone": "Asia/Shanghai", "language": "zh-CN",
        "screen": "1920x1080", "fonts": ["SimSun", "Microsoft YaHei", "Arial"],
        "webrtc_ip": "", "geolocation": {"lat": 31.23, "lng": 121.47},
    },
    "mac_safari_retail": {
        "platform": "MacIntel", "vendor": "Apple Computer, Inc.",
        "canvas_noise": 0.12, "webgl_vendor": "Apple Inc.",
        "webgl_renderer": "Apple M1",
        "timezone": "Asia/Shanghai", "language": "zh-CN",
        "screen": "2560x1600", "fonts": ["PingFang SC", "STHeiti", "Helvetica"],
        "webrtc_ip": "", "geolocation": {"lat": 31.23, "lng": 121.47},
    },
}

# ═══════════════════ 反检测引擎 ═══════════════════
def _human_delay(min_ms=200, max_ms=1500):
    """拟人随机延迟"""
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)

def _human_mouse_moves():
    """生成拟人鼠标移动轨迹"""
    moves = []
    x, y = random.randint(100, 800), random.randint(100, 600)
    for _ in range(random.randint(3, 8)):
        x += random.randint(-50, 50)
        y += random.randint(-30, 30)
        moves.append((x, y))
    return moves

def _random_user_agent():
    """随机User-Agent池"""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    ]
    return random.choice(agents)

# ═══════════════════ AI推理 ═══════════════════
def _ai_analyze(topic, context=None, mode="trading"):
    """调用deep_reasoner进行AI分析"""
    try:
        from brain.deep_reasoner import get_reasoner
        reasoner = get_reasoner()
        return reasoner.reason(topic, context=context, mode=mode)
    except Exception as e:
        return {"direction": "无法分析", "rationale": str(e), "risks": [], "confidence": 0.0}


# ═══════════════════ 指纹浏览器引擎 ═══════════════════

def _gen_fingerprint(os_type="Windows"):
    """从fingerprint_engine生成真实浏览器指纹"""
    try:
        fp_path = CAPS_DIR / "fingerprint_engine" / "run.py"
        if not fp_path.exists():
            return _fallback_fingerprint(os_type)
        r = subprocess.run(
            [sys.executable, str(fp_path), "generate", json.dumps({"os_type": os_type})],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout).get("fingerprint", _fallback_fingerprint(os_type))
    except:
        pass
    return _fallback_fingerprint(os_type)


def _fallback_fingerprint(os_type="Windows"):
    """内置备用指纹 — 无fingerprint_engine时使用"""
    fps = {
        "Windows": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "platform": "Win32", "vendor": "Google Inc.",
            "screen": {"width": 1920, "height": 1080, "dpr": 1.0},
            "hardware_concurrency": 8, "device_memory": 8,
            "timezone": "Asia/Shanghai", "language": "zh-CN,zh;q=0.9",
            "webgl_vendor": "Google Inc. (NVIDIA)", "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Direct3D11 vs_5_0 ps_5_0)",
            "canvas_hash": hashlib.md5(os.urandom(16)).hexdigest(),
        },
        "macOS": {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
            "platform": "MacIntel", "vendor": "Apple Computer, Inc.",
            "screen": {"width": 2560, "height": 1600, "dpr": 2.0},
            "hardware_concurrency": 10, "device_memory": 16,
            "timezone": "America/New_York", "language": "en-US,en;q=0.9",
            "webgl_vendor": "Apple Inc.", "webgl_renderer": "Apple M2 Pro",
            "canvas_hash": hashlib.md5(os.urandom(16)).hexdigest(),
        }
    }
    return fps.get(os_type, fps["Windows"])


def _launch_stealth_browser(platform="eastmoney", fingerprint=None, headless=False):
    """启动隐身浏览器 — 指纹伪装 + 反检测"""
    fp = fingerprint or _gen_fingerprint("Windows")
    plat = A_STOCK_PLATFORMS.get(platform, A_STOCK_PLATFORMS["eastmoney"])
    
    try:
        from seleniumbase import Driver
        driver = Driver(
            browser="chrome",
            headless=headless,
            uc=True,  # undetected-chrome mode
            agent=fp.get("user_agent", ""),
        )
        # 注入指纹覆盖
        if not headless:
            driver.execute_script(f"""
                Object.defineProperty(navigator, 'hardwareConcurrency', {{get:()=>{fp.get('hardware_concurrency',8)}}});
                Object.defineProperty(navigator, 'deviceMemory', {{get:()=>{fp.get('device_memory',8)}}});
                Object.defineProperty(navigator, 'platform', {{get:()=>'{fp.get('platform','Win32')}'}});
            """)
        
        driver.get(plat["base_url"])
        _human_delay(500, 1500)
        return {"ok": True, "driver": driver, "platform": plat["name"], 
                "fingerprint": fp.get("canvas_hash","")[:8], "engine": "seleniumbase+uc"}
    except ImportError:
        pass
    
    # Fallback: Playwright
    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(
            viewport={"width": fp["screen"]["width"], "height": fp["screen"]["height"]},
            user_agent=fp["user_agent"],
            timezone_id=fp["timezone"],
            locale=fp["language"].split(",")[0] if "," in fp.get("language","") else fp.get("language","zh-CN"),
        )
        page = ctx.new_page()
        page.goto(plat["base_url"], wait_until="domcontentloaded")
        _human_delay(500, 1500)
        return {"ok": True, "pw": pw, "browser": browser, "context": ctx, "page": page,
                "platform": plat["name"], "fingerprint": fp.get("canvas_hash","")[:8], "engine": "playwright"}
    except ImportError:
        return {"ok": False, "error": "需要安装: pip install seleniumbase 或 playwright"}


def _close_browser(ctx):
    """安全关闭浏览器"""
    try:
        if "driver" in ctx:
            ctx["driver"].quit()
        elif "browser" in ctx:
            ctx["browser"].close()
            if "pw" in ctx:
                ctx["pw"].stop()
    except:
        pass


# ═══════════════════ AI浏览器操盘 ═══════════════════

def do_launch_trading_browser(params):
    """启动隐身浏览器到A股交易平台 — 指纹伪装+反检测"""
    platform = params.get("platform", "eastmoney")
    headless = params.get("headless", False)
    os_type = params.get("os_type", "Windows")
    
    fingerprint = _gen_fingerprint(os_type)
    ctx = _launch_stealth_browser(platform, fingerprint, headless)
    
    if ctx.get("ok"):
        return {
            "ok": True,
            "action": "launch_trading_browser",
            "platform": ctx["platform"],
            "engine": ctx["engine"],
            "fingerprint_id": ctx["fingerprint"],
            "headless": headless,
            "timestamp": datetime.now().isoformat(),
        }
    return ctx


def do_ai_browser_scan(params):
    """AI浏览器扫描行情 — 打开网页→截图→AI分析→提取数据"""
    platform = params.get("platform", "eastmoney")
    code = params.get("code", "")
    
    ctx = _launch_stealth_browser(platform, headless=True)
    if not ctx.get("ok"):
        return ctx
    
    try:
        # 如果有股票代码, 导航到个股页面
        plat_cfg = A_STOCK_PLATFORMS[platform]
        if code and "page" in ctx:
            formatted = _format_stock_code(code, platform)
            ctx["page"].goto(plat_cfg["quote_url"].format(code=formatted), wait_until="domcontentloaded")
            _human_delay(1000, 2500)
        
        # 截图→AI分析
        eyes, _ = _get_eyes()
        frame = eyes.see()
        
        if frame.get("ok"):
            analysis = _ai_analyze(
                f"分析这只股票的交易页面截图: {code if code else '市场概览'}\n"
                "请识别: 当前价格、涨跌幅、成交量、买卖盘口、技术指标信号",
                mode="trading"
            )
            return {"ok": True, "code": code, "platform": platform,
                    "analysis": analysis, "timestamp": datetime.now().isoformat()}
        
        return {"ok": False, "error": "截图失败"}
    finally:
        _close_browser(ctx)


def do_ai_browser_trade(params):
    """AI浏览器自动交易 — 打开页面→分析→决策→模拟下单"""
    code = params.get("code", "")
    platform = params.get("platform", "eastmoney")
    action_type = params.get("action_type", "analyze")  # analyze / buy / sell
    
    if not code:
        return {"ok": False, "error": "缺少股票代码"}
    
    # 1. 获取实时行情
    sina_result, err = _sina_api([code])
    if err:
        print(f"[stock_trader] 新浪API警告: {err}")
    quotes = _parse_sina_result(sina_result) if sina_result else []
    
    # 2. AI深度分析
    analysis = _ai_analyze(
        f"对股票{code}进行A股专业操盘分析:\n"
        f"实时数据: {json.dumps(quotes, ensure_ascii=False)[:500] if quotes else '无实时数据'}\n"
        "请从以下维度分析:\n"
        "1. 技术面: 价格位置(相对高低)、均线排列、MACD/KDJ/RSI信号\n"
        "2. 资金面: 成交量变化、量价关系、主力动向判断\n"
        "3. 市场情绪: 涨跌停家数、板块热度、大盘环境\n"
        "4. 风险控制: 仓位建议、止损位、止盈位\n"
        "5. 操作建议: 买入/卖出/持有/观望, 给出具体价格区间",
        mode="trading"
    )
    
    result = {
        "ok": True,
        "code": code,
        "platform": platform,
        "action_type": action_type,
        "quotes": quotes[:1] if quotes else [],
        "ai_analysis": analysis,
        "timestamp": datetime.now().isoformat(),
    }
    
    # 3. 如果是交易操作, 打开浏览器执行
    if action_type in ("buy", "sell"):
        ctx = _launch_stealth_browser(platform, headless=False)
        if ctx.get("ok"):
            try:
                plat_cfg = A_STOCK_PLATFORMS[platform]
                if "page" in ctx:
                    formatted = _format_stock_code(code, platform)
                    ctx["page"].goto(plat_cfg["base_url"], 
                                    wait_until="domcontentloaded")
                    _human_delay(2000, 4000)
                result["browser_launched"] = True
                result["browser_action"] = f"{action_type} {code} on {platform}"
            finally:
                _close_browser(ctx)
    
    return result


def do_ai_market_sentiment(params):
    """AI市场情绪分析 — 综合多维度判断大盘环境"""
    # 扫描涨跌停/板块/北向资金
    hot_stocks, err = _sina_api(["sh000001", "sz399001", "sz399006"])  # 上证/深证/创业板
    if err:
        print(f"[stock_trader] 市场情绪API警告: {err}")
    
    analysis = _ai_analyze(
        "A股市场情绪综合分析:\n"
        f"大盘指数: {json.dumps(hot_stocks, ensure_ascii=False)[:300] if hot_stocks else '数据获取中'}\n"
        "请判断:\n"
        "1. 当前市场环境: 牛市/熊市/震荡市\n"
        "2. 市场情绪: 贪婪/恐惧/中性, 给出情绪指数(0-100)\n"
        "3. 仓位建议: 激进(80%)/中性(50%)/防御(20%)/空仓(0%)\n"
        "4. 热点板块: 当前哪些板块资金流入最多\n"
        "5. 风险提示: 需要注意的宏观事件或政策风险",
        mode="trading"
    )
    
    return {"ok": True, "action": "market_sentiment", "analysis": analysis,
            "indices": hot_stocks[:3] if hot_stocks else [],
            "timestamp": datetime.now().isoformat()}


def _parse_sina_result(result):
    """解析新浪API返回的行情数据"""
    if not result:
        return []
    quotes = []
    for line in result.strip().split("\n") if isinstance(result, str) else [result]:
        q = _parse_sina_quote(line)
        if q:
            quotes.append(q)
    return quotes

# ═══════════════════ 东方财富API (免费) ═══════════════════
def _sina_api(codes):
    """新浪财经实时行情API — 稳定免费"""
    if isinstance(codes, list):
        codes = ",".join(codes)
    url = f"https://hq.sinajs.cn/list={codes}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://finance.sina.com.cn"
        })
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.read().decode("gbk"), None
    except Exception as e:
        return None, str(e)[:200]

def _tencent_api(codes):
    """腾讯行情API — 备用"""
    if isinstance(codes, list):
        codes = ",".join(codes)
    url = f"https://qt.gtimg.cn/q={codes}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.read().decode("gbk"), None
    except Exception as e:
        return None, str(e)[:200]

def _parse_sina_quote(line):
    """解析新浪行情数据"""
    try:
        if "=" not in line:
            return None
        _, data = line.split("=", 1)
        data = data.strip().strip('";')
        parts = data.split(",")
        if len(parts) < 32:
            return None
        return {
            "name": parts[0],
            "open": float(parts[1]) if parts[1] else 0,
            "pre_close": float(parts[2]) if parts[2] else 0,
            "price": float(parts[3]) if parts[3] else 0,
            "high": float(parts[4]) if parts[4] else 0,
            "low": float(parts[5]) if parts[5] else 0,
            "volume": int(float(parts[8])) if parts[8] else 0,
            "amount": float(parts[9]) if parts[9] else 0,
            "date": parts[30] if len(parts) > 30 else "",
            "time": parts[31] if len(parts) > 31 else "",
        }
    except Exception:
        return None

def _parse_tencent_quote(line):
    """解析腾讯行情数据"""
    try:
        if "=" not in line:
            return None
        _, data = line.split("=", 1)
        data = data.strip().strip('";')
        parts = data.split("~")
        if len(parts) < 40:
            return None
        return {
            "name": parts[1],
            "code": parts[2],
            "price": float(parts[3]) if parts[3] else 0,
            "pre_close": float(parts[4]) if parts[4] else 0,
            "open": float(parts[5]) if parts[5] else 0,
            "volume": int(float(parts[6])) if parts[6] else 0,
            "high": float(parts[33]) if parts[33] else 0,
            "low": float(parts[34]) if parts[34] else 0,
            "change_pct": float(parts[32]) if parts[32] else 0,
            "pe": float(parts[39]) if parts[39] else 0,
            "market_cap": float(parts[45]) if parts[45] else 0,
        }
    except Exception:
        return None

def _format_stock_code(code, platform):
    """格式化股票代码为平台格式"""
    code = code.strip()
    if code.startswith("6"):
        market = "sh"
        prefix = A_STOCK_PLATFORMS[platform]["stock_code_prefix"]["sh"]
    elif code.startswith(("0", "3", "2")):
        market = "sz"
        prefix = A_STOCK_PLATFORMS[platform]["stock_code_prefix"]["sz"]
    else:
        market = "sh"
        prefix = A_STOCK_PLATFORMS[platform]["stock_code_prefix"]["sh"]
    
    # 东方财富用 1.600519 格式
    if platform == "eastmoney":
        em_market = "1" if market == "sh" else "0"
        return f"{em_market}.{code}"
    return f"{prefix}{code}"

# ═══════════════════ 核心操作 ═══════════════════

def do_setup_platform(params):
    """为指定平台创建指纹浏览器配置文件"""
    platform = params.get("platform", "eastmoney")
    template = params.get("template", "win_chrome_retail")
    profile_name = params.get("profile_name", f"trade_{platform}_{int(time.time())}")
    
    if platform not in A_STOCK_PLATFORMS:
        return {"ok": False, "error": f"未知平台: {platform}", "available": list(A_STOCK_PLATFORMS.keys())}
    
    fp = FINGERPRINT_TEMPLATES.get(template, FINGERPRINT_TEMPLATES["win_chrome_retail"])
    profile_dir = BROWSER_PROFILES_DIR / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        "profile_name": profile_name,
        "platform": platform,
        "platform_name": A_STOCK_PLATFORMS[platform]["name"],
        "fingerprint": fp,
        "template": template,
        "user_agent": _random_user_agent(),
        "created": datetime.now().isoformat(),
        "proxy": params.get("proxy", ""),
        "credentials": params.get("credentials", {}),
    }
    
    (profile_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "profile": profile_name, "platform": A_STOCK_PLATFORMS[platform]["name"], "profile_dir": str(profile_dir)}

def do_scan_market(params):
    """全市场扫描 — Sina实时API + AI筛选"""
    platform = params.get("platform", "sina")
    limit = min(params.get("limit", 30), 100)
    
    # A股核心股票池 (沪深300成分股采样)
    stock_pool = [
        "sh600519", "sh600036", "sh601318", "sh600900", "sh601166",
        "sh600276", "sh600887", "sh601012", "sh603259", "sh600809",
        "sh601899", "sh600585", "sh601398", "sh600030", "sh601688",
        "sz000858", "sz002415", "sz300750", "sz000333", "sz002594",
        "sz000651", "sz300059", "sz002475", "sz000001", "sz300124",
        "sz002230", "sz000725", "sz300015", "sz002714", "sz000568",
        "sh600050", "sh601857", "sh600104", "sh601088", "sh600028",
        "sh600031", "sh688981", "sh600690", "sh601390", "sh600150",
        "sz000002", "sz002142", "sz000063", "sz300498", "sz002352",
        "sz000776", "sz300433", "sz002049", "sz000625", "sz300274",
    ]
    
    # 批量获取行情 (每次最多50个)
    stocks = []
    batch_size = 50
    for i in range(0, min(len(stock_pool), limit + 20), batch_size):
        batch = stock_pool[i:i+batch_size]
        text, err = _sina_api(batch)
        if err:
            continue
        for line in text.strip().split("\n"):
            if not line.strip():
                continue
            q = _parse_sina_quote(line)
            if q and q["price"] > 0:
                code = line.split("=")[0].replace("var hq_str_", "")
                change_pct = round((q["price"] - q["pre_close"]) / q["pre_close"] * 100, 2) if q["pre_close"] > 0 else 0
                stocks.append({
                    "code": code,
                    "name": q["name"],
                    "price": q["price"],
                    "open": q["open"],
                    "high": q["high"],
                    "low": q["low"],
                    "pre_close": q["pre_close"],
                    "change_pct": change_pct,
                    "volume": q["volume"],
                    "amount": q["amount"],
                })
    
    # 按涨跌幅排序
    sort_field = params.get("sort", "change_pct")
    reverse = sort_field in ("change_pct", "volume", "amount")
    stocks.sort(key=lambda x: abs(x.get(sort_field, 0)), reverse=reverse)
    stocks = stocks[:limit]
    
    # AI筛选推荐
    if stocks:
        top5 = stocks[:5]
        stock_names = []
        for s in top5:
            stock_names.append("{} ({}) {:+}%".format(s.get("name","?"), s.get("code","?"), s.get("change_pct",0)))
        ai_topic = "A股扫描结果分析: " + ", ".join(stock_names)
        ai_result = _ai_analyze(ai_topic, context={"top_stocks": top5}, mode="trading")
    else:
        ai_result = {"direction": "无数据", "rationale": "未获取到行情"}
    
    return {
        "ok": True,
        "total": len(stocks),
        "stocks": stocks,
        "ai_analysis": ai_result,
        "platform": "新浪财经",
        "timestamp": datetime.now().isoformat(),
    }

def do_analyze_stock(params):
    """个股深度分析 — Sina实时API + AI推理"""
    code = str(params.get("code", "600519"))
    platform = params.get("platform", "sina")
    
    # 构建Sina代码格式
    if code.startswith("6"):
        scode = "sh" + code
    else:
        scode = "sz" + code
    
    text, err = _sina_api([scode])
    if err or not text:
        return {"ok": False, "error": "获取行情失败: " + str(err)}
    
    q = None
    for line in text.strip().split("\n"):
        if line.strip():
            q = _parse_sina_quote(line)
            if q and q["price"] > 0:
                break
    
    if not q:
        return {"ok": False, "error": "解析行情数据失败"}
    
    change_pct = round((q["price"] - q["pre_close"]) / q["pre_close"] * 100, 2) if q["pre_close"] > 0 else 0
    quote = {
        "code": code,
        "name": q["name"],
        "price": q["price"],
        "open": q["open"],
        "high": q["high"],
        "low": q["low"],
        "pre_close": q["pre_close"],
        "change_pct": change_pct,
        "volume": q["volume"],
        "amount": q["amount"],
        "timestamp": datetime.now().isoformat(),
    }
    
    # AI深度分析
    topic = """个股深度分析: {}({})
价格: {}  涨跌幅: {}%
成交量: {}手  成交额: {}万
开盘: {}  最高: {}  最低: {}""".format(
        quote["name"], code, quote["price"], quote["change_pct"],
        quote["volume"], round(quote["amount"]/10000, 2) if quote["amount"] else 0,
        quote["open"], quote["high"], quote["low"])
    
    ai_result = _ai_analyze(topic, context={"quote": quote}, mode="trading")
    
    return {
        "ok": True,
        "quote": quote,
        "ai_analysis": ai_result,
        "platform": "新浪财经",
    }

def do_scan_hot_sectors(params):
    """扫描热门板块 — 基于个股涨跌聚合"""
    # 复用scan_market的股票池，按涨跌幅聚合
    result = do_scan_market({"limit": 30, "sort": "change_pct"})
    stocks = result.get("stocks", [])
    # 简单的"板块"聚合：取涨跌TOP5
    up_stocks = [s for s in stocks if s.get("change_pct", 0) > 0][:5]
    down_stocks = [s for s in stocks if s.get("change_pct", 0) < 0][:5]
    
    sectors = []
    for s in up_stocks:
        sectors.append({"name": s["name"], "code": s["code"], "change_pct": s["change_pct"], "trend": "up"})
    for s in down_stocks:
        sectors.append({"name": s["name"], "code": s["code"], "change_pct": s["change_pct"], "trend": "down"})
    
    if sectors:
        ai_topic = "热门板块分析(基于个股涨跌): " + ", ".join("{} ({}) {:+}%".format(s["name"], s["code"], s["change_pct"]) for s in sectors[:5])
        ai_result = _ai_analyze(ai_topic, context={"hot_sectors": sectors[:5]}, mode="trading")
    else:
        ai_result = {"direction": "无数据"}
    
    return {"ok": True, "sectors": sectors, "ai_analysis": ai_result, "timestamp": datetime.now().isoformat()}

def do_place_order(params):
    """模拟下单 — AI辅助决策"""
    code = str(params.get("code", ""))
    action = params.get("action", "buy")
    price = float(params.get("price", 0))
    quantity = int(params.get("quantity", 100))
    
    if not code or price <= 0 or quantity <= 0:
        return {"ok": False, "error": "缺少code/price/quantity参数"}
    
    # 用Sina API获取实时价验证
    scode = "sh" + code if code.startswith("6") else "sz" + code
    text, err = _sina_api([scode])
    real_price = price
    price_diff = 0
    if not err and text:
        q = _parse_sina_quote(text.split("\n")[0]) if text.strip() else None
        if q and q["price"] > 0:
            real_price = q["price"]
            price_diff = abs(real_price - price) / real_price * 100 if real_price > 0 else 0
    
    trade_amount = price * quantity
    stamp_tax = trade_amount * 0.001
    commission = max(trade_amount * 0.00025, 5)
    
    ai_topic = "交易审核: {} {} {}手@{}元 实时价:{} 价差:{:.2f}% 金额:{:.2f}".format(
        action, code, quantity, price, real_price, price_diff, trade_amount)
    ai_result = _ai_analyze(ai_topic, mode="trading")
    
    order = {
        "id": "ORD{}{:04d}".format(int(time.time()), random.randint(1000, 9999)),
        "code": code, "action": action, "price": price, "quantity": quantity,
        "amount": trade_amount, "commission": commission, "stamp_tax": stamp_tax,
        "real_price": real_price, "price_diff_pct": round(price_diff, 2),
        "status": "pending", "ai_review": ai_result, "timestamp": datetime.now().isoformat(),
    }
    
    orders_file = TRADE_DIR / "orders.jsonl"
    with open(orders_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(order, ensure_ascii=False) + "\n")
    
    return {"ok": True, "order": order}

def do_risk_check(params):
    """风控检查 — AI+规则双引擎"""
    code = params.get("code", "")
    
    # 持仓检查
    positions = _load_positions()
    total_value = sum(p.get("market_value", 0) for p in positions.values())
    position_count = len(positions)
    
    # 订单历史
    orders = _load_orders()
    today = datetime.now().strftime("%Y-%m-%d")
    today_orders = [o for o in orders if o.get("timestamp", "").startswith(today)]
    today_trades = len(today_orders)
    today_amount = sum(o.get("amount", 0) for o in today_orders)
    
    risks = []
    if total_value > 1000000:
        risks.append({"level": "warning", "msg": f"总持仓{total_value:.0f}元超过100万警戒线"})
    if position_count > 10:
        risks.append({"level": "warning", "msg": f"持仓{position_count}只股票，过度分散"})
    if today_trades > 20:
        risks.append({"level": "danger", "msg": f"今日交易{today_trades}笔，频繁交易警告"})
    if today_amount > 500000:
        risks.append({"level": "danger", "msg": f"今日交易额{today_amount:.0f}元超过50万限额"})
    
    # AI 风控评估
    if code:
        ai_topic = f"风控评估: {code} 当前持仓{position_count}只 总市值{total_value:.0f} 今日交易{today_trades}笔"
        ai_result = _ai_analyze(ai_topic, mode="trading")
    else:
        ai_result = {"direction": "持仓正常" if len(risks) == 0 else "需要关注"}
    
    risk_level = "safe"
    if any(r["level"] == "danger" for r in risks):
        risk_level = "danger"
    elif any(r["level"] == "warning" for r in risks):
        risk_level = "warning"
    
    return {
        "ok": True,
        "risk_level": risk_level,
        "risks": risks,
        "positions": {"count": position_count, "total_value": total_value},
        "today": {"trades": today_trades, "amount": today_amount},
        "ai_assessment": ai_result,
        "timestamp": datetime.now().isoformat(),
    }

def do_daily_review(params):
    """每日复盘 — AI生成操盘总结"""
    orders = _load_orders()
    today = datetime.now().strftime("%Y-%m-%d")
    today_orders = [o for o in orders if o.get("timestamp", "").startswith(today)]
    
    positions = _load_positions()
    
    # 今日交易统计
    buy_orders = [o for o in today_orders if o.get("action") == "buy"]
    sell_orders = [o for o in today_orders if o.get("action") == "sell"]
    
    total_buy = sum(o.get("amount", 0) for o in buy_orders)
    total_sell = sum(o.get("amount", 0) for o in sell_orders)
    
    # 当日盈亏概算
    pnl = 0
    for p in positions.values():
        pnl += p.get("unrealized_pnl", 0)
    
    # AI 复盘
    topic = f"""A股今日复盘:
买入{buy_orders.__len__()}笔 {total_buy:.0f}元
卖出{sell_orders.__len__()}笔 {total_sell:.0f}元
当前持仓{positions.__len__()}只 未实现盈亏{pnl:+.0f}元
请分析: 1.交易质量 2.是否需要调整策略 3.明日关注方向"""
    
    ai_result = _ai_analyze(topic, mode="trading")
    
    return {
        "ok": True,
        "date": today,
        "buy_count": len(buy_orders),
        "sell_count": len(sell_orders),
        "total_buy": total_buy,
        "total_sell": total_sell,
        "position_count": len(positions),
        "unrealized_pnl": pnl,
        "ai_review": ai_result,
        "timestamp": datetime.now().isoformat(),
    }

def do_auto_trade_pipeline(params):
    """一键自动操盘流水线: 扫描→分析→AI决策→下单→风控"""
    platform = params.get("platform", "eastmoney")
    max_trades = min(params.get("max_trades", 3), 10)
    max_amount = min(params.get("max_amount", 50000), 500000)
    
    pipeline_result = {"steps": [], "trades": [], "ok": True, "timestamp": datetime.now().isoformat()}
    
    # Step 1: 扫描市场
    scan = do_scan_market({"platform": platform, "limit": 20, "sort": "f3"})
    pipeline_result["steps"].append({"step": "scan", "ok": scan["ok"], "count": scan.get("total", 0)})
    
    if not scan["ok"]:
        pipeline_result["ok"] = False
        pipeline_result["error"] = "扫描失败"
        return pipeline_result
    
    # Step 2: AI筛选候选
    candidates = []
    for stock in scan.get("stocks", []):
        # 排除ST、新股、涨跌停
        name = stock.get("name", "")
        change_pct = stock.get("change_pct", 0)
        if "ST" in name or abs(change_pct) > 9.5:
            continue
        candidates.append(stock)
    
    candidates = candidates[:max_trades]
    pipeline_result["steps"].append({"step": "filter", "candidates": len(candidates)})
    
    # Step 3: 逐个深度分析
    for stock in candidates:
        code = stock.get("code", "")
        if not code:
            continue
        
        analysis = do_analyze_stock({"code": code, "platform": platform})
        pipeline_result["steps"].append({"step": "analyze", "code": code, "ok": analysis["ok"]})
        
        if not analysis["ok"]:
            continue
        
        # AI决策: 是否交易
        ai = analysis.get("ai_analysis", {})
        direction = ai.get("direction", "")
        confidence = ai.get("confidence", 0)
        
        # 风控检查
        risk = do_risk_check({"code": code})
        if risk["risk_level"] == "danger":
            pipeline_result["steps"].append({"step": "risk_blocked", "code": code, "reason": "风控阻止"})
            continue
        
        # AI决策买入信号
        if confidence > 0.6 and any(w in direction for w in ["买入", "建仓", "加仓", "看好", "增持"]):
            qty = min(int(max_amount / stock["price"] / 100), 100)
            if qty > 0:
                order = do_place_order({
                    "code": code,
                    "action": "buy",
                    "price": stock["price"],
                    "quantity": qty,
                })
                pipeline_result["trades"].append(order.get("order", {}))
                pipeline_result["steps"].append({"step": "trade", "code": code, "action": "buy", "qty": qty})
    
    pipeline_result["total_trades"] = len(pipeline_result["trades"])
    
    # Step 4: 最终复盘
    if pipeline_result["trades"]:
        review_topic = f"自动操盘完成: 执行{pipeline_result['total_trades']}笔交易"
        for t in pipeline_result["trades"]:
            review_topic += f"\n{t.get('action','')} {t.get('code','')} {t.get('quantity',0)}手@{t.get('price',0)}"
        pipeline_result["ai_summary"] = _ai_analyze(review_topic, mode="trading")
    
    return pipeline_result

# ═══════════════════ 辅助函数 ═══════════════════
def _load_positions():
    f = TRADE_DIR / "positions.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {}

def _load_orders():
    f = TRADE_DIR / "orders.jsonl"
    if f.exists():
        return [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
    return []

def do_engine_status(params=None):
    """引擎状态检测"""
    try:
        from brain.deep_reasoner import MODEL, BASE_URL
        ai_status = f"{MODEL} @ {BASE_URL}"
    except:
        ai_status = "unknown"
    
    return {
        "ok": True,
        "ai_engine": ai_status,
        "platforms": list(A_STOCK_PLATFORMS.keys()),
        "profiles_dir": str(BROWSER_PROFILES_DIR),
        "trade_dir": str(TRADE_DIR),
        "positions": len(_load_positions()),
        "total_orders": len(_load_orders()),
        "timestamp": datetime.now().isoformat(),
    }

# ═══════════════════ AI视觉 — 原生邻域驱动 ═══════════════════

def _get_eyes():
    """获取原生视觉单例"""
    sys.path.insert(0, str(ROOT))
    from brain.host_body import eyes, hands
    return eyes, hands


def do_capture_screen(params):
    """截取屏幕 — 原生视觉, 零延迟"""
    region = params.get("region")  # None=全屏, {"x":0,"y":0,"w":400,"h":300}
    try:
        eyes, _ = _get_eyes()
        if region and isinstance(region, dict):
            result = eyes.see(region)
        else:
            result = eyes.see()
        if result.get("ok"):
            return {
                "ok": True,
                "size": result.get("size", "unknown"),
                "image_base64": result.get("image", ""),
                "format": "png",
                "mode": result.get("mode", "native"),
                "timestamp": datetime.now().isoformat(),
            }
        return result
    except Exception as e:
        return {"ok": False, "error": f"截图失败: {e}"}


def do_ocr_screen(params):
    """OCR识别屏幕文字 — 原生视觉直连Tesseract"""
    region = params.get("region")
    try:
        eyes, _ = _get_eyes()
        if region and isinstance(region, dict):
            result = eyes.read(region.get("x", 0), region.get("y", 0),
                             region.get("w", 1920), region.get("h", 1080))
        else:
            result = eyes.read_all()
        
        if result.get("ok"):
            text = " ".join(b["text"] for b in result.get("text_blocks", [])[:200])
            return {
                "ok": True,
                "text": text[:3000],
                "text_blocks": len(result.get("text_blocks", [])),
                "timestamp": datetime.now().isoformat(),
            }
        return result
    except Exception as e:
        return {"ok": False, "error": f"OCR失败: {e}"}


def do_analyze_chart(params):
    """分析屏幕上的K线图/分时图 — 原生视觉+AI"""
    code = params.get("code", "")
    try:
        eyes, _ = _get_eyes()
        prompt = params.get("prompt", "")
        if not prompt:
            prompt = """请分析这张股票K线图/分时图:
1. 识别图中股票代码和名称
2. 判断当前K线形态(阳线/阴线/十字星/锤子线等)
3. 分析均线排列(多头/空头/粘合)
4. 识别MACD/KDJ/RSI/BOLL等指标信号
5. 判断成交量变化趋势
6. 给出短期(1-3天)走势预判
7. 指出关键支撑位和压力位
8. 综合评分: 强烈买入/买入/观望/卖出/强烈卖出"""
        if code:
            prompt = f"股票代码: {code}\n" + prompt
        
        return eyes.analyze(prompt)
    except Exception as e:
        return {"ok": False, "error": f"图表分析失败: {e}"}


def do_watch_market(params):
    """持续监控市场 — 后台FrameBuffer + 场景检测"""
    duration = min(params.get("duration", 60), 300)
    fps = params.get("fps", 5)
    alert_keywords = params.get("alert_keywords", ["涨停", "跌停", "暴跌", "暴涨", "异动", "突破"])
    if isinstance(alert_keywords, str):
        alert_keywords = [w.strip() for w in alert_keywords.split(",")]
    
    try:
        eyes, _ = _get_eyes()
        eyes.start_watching(fps=15)
        
        # 用movie模式采集+场景检测
        movie = eyes.movie(duration, fps, detect_scenes=True)
        
        # OCR检查告警关键词
        alerts = []
        all_text = ""
        for i in range(min(movie.get("frames", 0), 20)):
            frame = eyes.latest
            if frame.get("ok"):
                text_result = eyes.read_all()
                if text_result.get("ok"):
                    all_text = " ".join(b["text"] for b in text_result.get("text_blocks", [])[:100])
                    for kw in alert_keywords:
                        if kw in all_text:
                            alerts.append({"keyword": kw, "time": datetime.now().isoformat()})
        
        eyes.stop_watching()
        return {
            "ok": True,
            "duration": movie.get("duration", duration),
            "frames": movie.get("frames", 0),
            "scene_changes": movie.get("scene_count", 1),
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"ok": False, "error": f"市场监控失败: {e}"}


def do_browse_market(params):
    """浏览市场数据 — 原生视觉+手, 自动滚屏查看行情"""
    count = params.get("count", 10)
    question = params.get("question", "这是什么股票? 价格和涨跌幅是多少?")
    
    try:
        eyes, hands = _get_eyes()
        eyes.start_watching(fps=15)
        result = hands.browse_feed(count, "down", question)
        eyes.stop_watching()
        return result
    except Exception as e:
        return {"ok": False, "error": f"市场浏览失败: {e}"}


def do_look_and_trade(params):
    """看→找→交易: 在屏幕上找到股票代码→点击→查看详情"""
    code = params.get("code", "")
    try:
        eyes, hands = _get_eyes()
        eyes.start_watching(fps=15)
        result = hands.look_and_click(code, timeout=10)
        eyes.stop_watching()
        return result
    except Exception as e:
        return {"ok": False, "error": f"交易操作失败: {e}"}

def _extract_context(text, keyword, width=80):
    """提取关键词周围上下文"""
    idx = text.find(keyword)
    if idx < 0:
        return keyword
    start = max(0, idx - width // 2)
    end = min(len(text), idx + len(keyword) + width // 2)
    return text[start:end]

def do_knowledge(params):
    """查询A股操盘知识库"""
    topic = params.get("topic", "")
    kb_path = Path(__file__).parent / "knowledge.json"
    if not kb_path.exists():
        return {"ok": False, "error": "知识库文件不存在"}
    kb = json.loads(kb_path.read_text(encoding="utf-8"))
    
    if not topic:
        return {"ok": True, "topics": list(kb.keys()), "version": kb["version"]}
    
    # 精确匹配
    if topic in kb:
        return {"ok": True, "topic": topic, "content": kb[topic]}
    
    # 模糊搜索
    results = {}
    for key, val in kb.items():
        if isinstance(val, dict):
            for sub_key, sub_val in val.items():
                if topic in sub_key or topic in str(sub_val)[:200]:
                    results[f"{key}.{sub_key}"] = sub_val
    
    if results:
        return {"ok": True, "topic": topic, "matches": results}
    
    return {"ok": True, "topic": topic, "matches": {}, "suggestion": "试试: trading_rules, technical_indicators, risk_management, candlestick_patterns, market_sentiment"}
# ═══════════════════ 自主巡逻 ═══════════════════

def _is_market_hours():
    """判断当前是否在A股交易时段 (9:30-11:30, 13:00-15:00)"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.hour * 60 + now.minute
    return (570 <= t <= 690) or (780 <= t <= 900)

def _publish_to_event_bus(topic, event_type, payload):
    """发布事件到event_bus cap"""
    eb_run = CAPS_DIR / "event_bus" / "run.py"
    if not eb_run.exists():
        return False
    try:
        r = subprocess.run(
            ["python", str(eb_run), "publish",
             f"topic={topic}", f"event_type={event_type}",
             f"payload={json.dumps(payload, default=str, ensure_ascii=False)}"],
            capture_output=True, text=True, timeout=15, cwd=str(CAPS_DIR)
        )
        return r.returncode == 0
    except Exception:
        return False

STOCKS_CONFIG_FILE = TRADE_DIR / "patrol_stocks.json"

def _load_patrol_stocks():
    """加载巡逻股票列表"""
    if STOCKS_CONFIG_FILE.exists():
        try:
            return json.loads(STOCKS_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return ["000001", "000651", "600519", "601318", "000858"]

def do_autonomous_patrol(params):
    """自主巡逻 — 持续监控配置股票, 交易时段内循环扫描

    params:
        stocks: list[str] — 股票代码列表 (可选, 默认从配置加载)
        interval: int   — 扫描间隔秒数 (默认60)
        rounds: int     — 最大轮次 (默认0=无限)
        simulate: bool  — 是否使用模拟数据 (默认False)
        max_duration: int — 最大运行时长秒数 (默认0=无限)
    """
    stocks = params.get("stocks", _load_patrol_stocks())
    interval = params.get("interval", 60)
    max_rounds = params.get("rounds", 0)
    simulate = params.get("simulate", False)
    max_duration = params.get("max_duration", 0)
    signal_threshold = params.get("signal_threshold", 3.0)

    if isinstance(stocks, str):
        stocks = [s.strip() for s in stocks.split(",")]

    results = []
    alerts = []
    round_num = 0
    start_time = time.time()

    is_market = _is_market_hours()

    while True:
        round_num += 1
        if max_rounds > 0 and round_num > max_rounds:
            break
        if max_duration > 0 and (time.time() - start_time) > max_duration:
            break

        now_market = _is_market_hours()
        if not now_market and not simulate:
            if is_market:
                results.append({"ts": datetime.now().isoformat(), "event": "market_closed"})
            is_market = False
            time.sleep(interval)
            continue
        is_market = now_market

        round_result = {"round": round_num, "ts": datetime.now().isoformat(), "market_open": now_market, "stocks": {}}

        for code in stocks:
            try:
                if simulate:
                    price = round(random.uniform(0.95, 1.05) * 10 + random.gauss(0, 0.05), 2)
                    change_pct = round(random.gauss(0, 1.5), 2)
                    volume_ratio = round(random.uniform(0.5, 3.0), 2)
                    quote = {"code": code, "name": f"模拟{code}", "price": price,
                             "change_pct": change_pct, "volume_ratio": volume_ratio,
                             "simulated": True}
                else:
                    raw, err = _sina_api([code])
                    if err or not raw:
                        quote = {"code": code, "error": str(err)[:100]}
                    else:
                        parsed = _parse_sina_quote(raw) if raw else None
                        if parsed:
                            quote = parsed
                        else:
                            quote = {"code": code, "raw": raw[:200] if raw else "无数据"}
            except Exception as e:
                quote = {"code": code, "error": str(e)[:100]}

            round_result["stocks"][code] = quote

            change = quote.get("change_pct", 0) or 0
            try:
                change = float(change)
            except (ValueError, TypeError):
                change = 0

            if abs(change) >= signal_threshold:
                signal = {
                    "code": code,
                    "name": quote.get("name", code),
                    "change_pct": change,
                    "price": quote.get("price", 0),
                    "direction": "up" if change > 0 else "down",
                    "triggered_at": datetime.now().isoformat(),
                    "round": round_num,
                }
                alerts.append(signal)
                _publish_to_event_bus("stock/signal", "price_alert", signal)

        results.append(round_result)

        if simulate:
            time.sleep(min(interval, 5))
        else:
            time.sleep(interval)

    patrol_file = TRADE_DIR / f"patrol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    patrol_file.write_text(json.dumps({"rounds": round_num, "alerts": len(alerts),
                                        "results": results[-50:], "alerts_list": alerts[-20:]},
                                       ensure_ascii=False, default=str, indent=2),
                           encoding="utf-8")

    return {"ok": True, "total_rounds": round_num, "total_alerts": len(alerts),
            "monitored_stocks": stocks, "market_open": _is_market_hours(),
            "patrol_log": str(patrol_file)}

def do_alert_on_signal(params):
    """信号告警 — 当交易信号触发时发布到event_bus

    params:
        signals: list[dict] — 信号列表, 每个信号包含code/name/signal_type/direction/strength
        topic: str — event_bus topic (默认 stock/signal)
    """
    signals = params.get("signals", [])
    topic = params.get("topic", "stock/signal")

    if isinstance(signals, dict):
        signals = [signals]

    published = []
    failed = []

    for sig in signals:
        code = sig.get("code", "unknown")
        signal_type = sig.get("signal_type", "price_alert")
        direction = sig.get("direction", "neutral")
        strength = sig.get("strength", 0)
        name = sig.get("name", code)

        payload = {
            "code": code,
            "name": name,
            "signal_type": signal_type,
            "direction": direction,
            "strength": strength,
            "price": sig.get("price"),
            "change_pct": sig.get("change_pct"),
            "volume": sig.get("volume"),
            "timestamp": datetime.now().isoformat(),
            "source": "stock_browser_trader",
        }

        ok = _publish_to_event_bus(topic, signal_type, payload)
        (published if ok else failed).append({"code": code, "signal_type": signal_type})

        if signal_type == "breakout":
            _publish_to_event_bus("stock/breakout", "breakout_alert", payload)
        elif signal_type == "volume_spike":
            _publish_to_event_bus("stock/volume", "volume_alert", payload)
        elif signal_type == "trend_reversal":
            _publish_to_event_bus("stock/reversal", "reversal_alert", payload)

    return {"ok": True, "published": len(published), "failed": len(failed),
            "details": {"published": published, "failed": failed},
            "topic": topic, "timestamp": datetime.now().isoformat()}

def do_daily_report(params):
    """每日报告 — 生成交易日终摘要到 ~/.gbt/reports/

    params:
        positions: dict — 当前持仓 (可选, 默认加载)
        orders: list    — 当日订单 (可选, 默认加载)
        watchlist: list — 监控列表 (可选)
    """
    REPORT_DIR = Path.home() / '.gbt' / 'reports'
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    positions = params.get("positions", _load_positions())
    orders = params.get("orders", _load_orders())
    watchlist = params.get("watchlist", [])
    date_str = params.get("date", datetime.now().strftime("%Y-%m-%d"))
    author = params.get("author", "GBT小土豆 v5.0")

    watchlist_data = []
    for code in (watchlist if watchlist else []):
        try:
            raw, err = _sina_api([code])
            if raw:
                quote = _parse_sina_quote(raw)
                if quote:
                    watchlist_data.append(quote)
        except Exception:
            pass

    lines = [
        "# GBT A股操盘日报",
        "",
        f"| 项目 | 内容 |",
        f"|---|---|",
        f"| 日期 | {date_str} |",
        f"| 生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
        f"| 生成者 | {author} |",
        f"| 市场状态 | {'交易中' if _is_market_hours() else '已收盘'} |",
        "",
        "## 持仓概览",
        "",
    ]

    if positions:
        lines.append("| 代码 | 名称 | 数量 | 成本 | 现价 | 盈亏 |")
        lines.append("|---|---|---|---|---|---|")
        total_pnl = 0
        for code, pos in positions.items():
            if isinstance(pos, dict):
                qty = pos.get("quantity", pos.get("qty", 0))
                cost = pos.get("cost", 0)
                name = pos.get("name", code)
                lines.append(f"| {code} | {name} | {qty} | {cost} | - | - |")
        lines.append("")
    else:
        lines.extend(["_暂无持仓数据_", ""])

    lines.extend([
        "## 当日订单",
        "",
    ])

    if orders:
        today_prefix = date_str
        today_orders = [o for o in orders if isinstance(o, dict) and
                        o.get("ts", "").startswith(today_prefix)]
        if today_orders:
            lines.append("| 时间 | 代码 | 方向 | 数量 | 价格 | 状态 |")
            lines.append("|---|---|---|---|---|---|")
            for o in today_orders[-30:]:
                ts = o.get("ts", "")[:19]
                code = o.get("code", "-")
                direction = o.get("direction", "-")
                qty = o.get("quantity", o.get("qty", "-"))
                price = o.get("price", "-")
                status = o.get("status", "-")
                lines.append(f"| {ts} | {code} | {direction} | {qty} | {price} | {status} |")
            lines.append("")
        else:
            lines.extend(["_今日无订单_", ""])
    else:
        lines.extend(["_暂无订单数据_", ""])

    if watchlist_data:
        lines.extend([
            "## 监控列表行情",
            "",
            "| 代码 | 名称 | 现价 | 涨跌幅 |",
            "|---|---|---|---|",
        ])
        for q in watchlist_data:
            lines.append(f"| {q.get('code','-')} | {q.get('name','-')} | {q.get('price','-')} | {q.get('change_pct','-')}% |")
        lines.append("")

    lines.extend([
        "## 风险提示",
        "",
        "- 本报告由AI自动生成，仅供参考，不构成投资建议",
        "- 入市有风险，投资需谨慎",
        "",
        "---",
        f"*报告由 {author} 自动生成 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
    ])

    report = "\n".join(lines)
    fname = f"A股日报_{date_str}.md"
    fpath = REPORT_DIR / fname
    fpath.write_text(report, encoding="utf-8")

    return {"ok": True, "file": str(fpath), "date": date_str,
            "positions_count": len(positions), "orders_count": len(orders),
            "watchlist_count": len(watchlist_data), "market_hours": _is_market_hours()}

# ═══════════════════ 命令路由 ═══════════════════
HANDLERS = {
    "setup_platform": do_setup_platform,
    "scan_market": do_scan_market,
    "analyze_stock": do_analyze_stock,
    "scan_hot_sectors": do_scan_hot_sectors,
    "place_order": do_place_order,
    "risk_check": do_risk_check,
    "daily_review": do_daily_review,
    "auto_trade": do_auto_trade_pipeline,
    "engine_status": do_engine_status,
    "capture_screen": do_capture_screen,
    "ocr_screen": do_ocr_screen,
    "analyze_chart": do_analyze_chart,
    "watch_market": do_watch_market,
    "browse_market": do_browse_market,
    "look_and_trade": do_look_and_trade,
    "knowledge": do_knowledge,
    "launch_browser": do_launch_trading_browser,
    "ai_browser_scan": do_ai_browser_scan,
    "ai_browser_trade": do_ai_browser_trade,
    "market_sentiment": do_ai_market_sentiment,
    "autonomous_patrol": do_autonomous_patrol,
    "alert_on_signal": do_alert_on_signal,
    "daily_report": do_daily_report,
}

if __name__ == "__main__":
    import sys as _sys
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    
    action = _sys.argv[1] if len(_sys.argv) > 1 and not _sys.argv[1].startswith("-") else "engine_status"
    
    params = {}
    for arg in _sys.argv[2:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            try:
                v = json.loads(v)
            except (json.JSONDecodeError, ValueError):
                pass
            params[k] = v
    
    h = HANDLERS.get(action)
    if h:
        result = h(params)
        print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
    else:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
