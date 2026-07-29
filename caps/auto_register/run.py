# 开发者：自由的风
"""auto_register/run.py — 批量账号注册(钱包/社交/直播/论坛/电商)
=============================================================
运维域 ready — 自动化账号注册引擎。支持多平台模板。
"""
import sys, json, os, random, string, time, urllib.request, urllib.error, urllib.parse

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_DIR = os.path.join(os.path.dirname(SANDBOX), ".gbt", "profiles")
os.makedirs(PROFILE_DIR, exist_ok=True)

# 账号生成器
def _gen_email(prefix="user"):
    domains = ["gmail.com", "outlook.com", "proton.me", "yahoo.com", "mail.com"]
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}.{suffix}@{random.choice(domains)}"

def _gen_username():
    adjectives = ["swift", "brave", "calm", "dark", "eager", "fierce", "golden", "happy", "icy", "jolly"]
    nouns = ["tiger", "eagle", "wolf", "fox", "bear", "hawk", "lion", "panda", "dragon", "phoenix"]
    return f"{random.choice(adjectives)}_{random.choice(nouns)}_{random.randint(100,999)}"

def _gen_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

def _gen_phone():
    prefixes = ["+8613", "+8615", "+8618", "+8617", "+8529", "+8536"]
    return random.choice(prefixes) + ''.join(random.choices(string.digits, k=8))

def do_register(params):
    """注册账号(生成+记录)"""
    platform = params.get("platform", "generic")
    count = params.get("count", 1)

    accounts = []
    for _ in range(count):
        account = {
            "platform": platform,
            "email": _gen_email(),
            "username": _gen_username(),
            "password": _gen_password(),
            "phone": _gen_phone(),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "registered": False,
        }
        accounts.append(account)

    # 保存到本地
    profile_file = os.path.join(PROFILE_DIR, f"{platform}_{int(time.time())}.json")
    with open(profile_file, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

    masked = []
    for a in accounts:
        masked.append({**a, "password": a["password"][:3] + "***", "email": a["email"].split("@")[0][:4] + "***@" + a["email"].split("@")[1]})

    return {
        "ok": True,
        "cap": "auto_register",
        "action": "register",
        "domain": "运维域",
        "platform": platform,
        "accounts_created": count,
        "accounts": masked,
        "saved": profile_file,
    }

def do_batch(params):
    """批量注册多平台"""
    platforms = params.get("platforms", ["twitter", "reddit", "discord", "github"])
    results = {}
    for p in platforms:
        r = do_register({"platform": p, "count": 1})
        results[p] = {"ok": r["ok"], "count": r.get("accounts_created", 0)}
    return {"ok": True, "cap": "auto_register", "action": "batch",
            "platforms": len(platforms), "results": results}

HANDLERS = {"register": do_register, "batch": do_batch}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "register"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
