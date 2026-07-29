# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""captcha_solver/run.py — 2Captcha验证码求解能力模块 · 16种验证码"""
import sys, json, os
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

SOLVER_READY = False
solver = None
try:
    from caps._2captcha.client import CaptchaSolver
    solver = CaptchaSolver()
    SOLVER_READY = True
except Exception as e:
    SOLVER_ERROR = str(e)

METHOD_MAP = {
    "solve_recaptcha_v2":    {"params": ["website_url", "website_key", "proxy", "is_invisible"], "desc": "reCAPTCHA v2 人机验证"},
    "solve_recaptcha_v3":    {"params": ["website_url", "website_key", "min_score", "action"], "desc": "reCAPTCHA v3 无感验证"},
    "solve_turnstile":       {"params": ["website_url", "website_key", "proxy"], "desc": "Cloudflare Turnstile"},
    "solve_funcaptcha":      {"params": ["website_url", "website_public_key", "proxy"], "desc": "Funcaptcha (Arkose Labs)"},
    "solve_geetest":         {"params": ["website_url", "gt", "challenge", "api_server", "proxy"], "desc": "极验 v3"},
    "solve_geetest_v4":      {"params": ["website_url", "captcha_id", "proxy"], "desc": "极验 v4"},
    "solve_hcaptcha":        {"params": ["website_url", "website_key", "proxy"], "desc": "hCaptcha"},
    "solve_image":           {"params": ["image_path", "image_base64", "case_sensitive", "numeric", "min_len", "max_len", "phrase", "calc", "lang", "hint"], "desc": "图片验证码识别"},
    "solve_audio":           {"params": ["audio_path", "audio_base64", "lang"], "desc": "音频验证码识别"},
    "solve_coordinates":     {"params": ["image_path", "image_base64", "comment"], "desc": "坐标点击验证码"},
    "solve_tencent":         {"params": ["website_url", "app_id", "proxy"], "desc": "腾讯验证码"},
    "solve_binance":         {"params": ["website_url", "website_key", "proxy"], "desc": "币安验证码"},
    "solve_imperva":         {"params": ["website_url", "website_key", "proxy", "user_agent"], "desc": "Imperva/Incapsula"},
    "solve_yandex":          {"params": ["website_url", "website_key", "proxy"], "desc": "Yandex SmartCaptcha"},
    "solve_amazon_waf":      {"params": ["website_url", "website_key", "proxy"], "desc": "Amazon WAF"},
    "solve_datadome":        {"params": ["website_url", "captcha_url", "proxy", "user_agent"], "desc": "DataDome"},
}

def do_list(params=None):
    """列出所有可用验证码类型及所需参数"""
    return {
        "ok": True,
        "ready": SOLVER_READY,
        "total": len(METHOD_MAP),
        "methods": [
            {"name": k, "desc": v["desc"], "params": v["params"]}
            for k, v in METHOD_MAP.items()
        ]
    }

def do_self_test(params=None):
    """自检: 2Captcha API Key 是否配置"""
    if not SOLVER_READY:
        api_key = os.environ.get("CAPTCHA_API_KEY", os.environ.get("TWOCAPTCHA_API_KEY", ""))
        return {
            "ok": False,
            "ready": False,
            "error": SOLVER_ERROR if 'SOLVER_ERROR' in dir() else "未知错误",
            "fix": "设置环境变量 CAPTCHA_API_KEY 或 TWOCAPTCHA_API_KEY"
        }
    try:
        balance = solver.get_balance()
        return {"ok": True, "ready": True, "balance": balance}
    except Exception as e:
        return {"ok": False, "ready": True, "error": f"连接失败: {e}", "fix": "检查 API Key 是否有效"}

def do_run(params):
    """执行验证码求解"""
    if not SOLVER_READY:
        return do_self_test(params)
    action = params.get("action") or params.get("_action") or "solve_recaptcha_v2"
    if action not in METHOD_MAP and action not in ("get_balance", "report_correct", "report_incorrect"):
        return {"ok": False, "error": f"未知方法: {action}", "available": list(METHOD_MAP.keys()) + ["get_balance", "report_correct", "report_incorrect"]}
    if action in METHOD_MAP:
        valid = METHOD_MAP[action]["params"]
        kwargs = {k: params[k] for k in valid if k in params}
        try:
            method = getattr(solver, action)
            return method(**kwargs)
        except Exception as e:
            return {"ok": False, "error": str(e), "required_params": valid}
    try:
        method = getattr(solver, action)
        if action in ("get_balance",):
            return method()
        if action in ("report_correct", "report_incorrect"):
            return method(params.get("task_id", params.get("taskId", "")))
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Handlers
handlers = {
    "run":         do_run,
    "list":        do_list,
    "self_test":   do_self_test,
    "help":        do_list,
    "recaptcha":   lambda p: do_run({**p, "action": "solve_recaptcha_v2"}),
    "hcaptcha":    lambda p: do_run({**p, "action": "solve_hcaptcha"}),
}
HANDLERS = handlers

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # 支持 argv 和 stdin 两种方式
    action = "run"
    params = {}
    if len(sys.argv) > 1 and not sys.argv[1].startswith("{"):
        action = sys.argv[1]
    if len(sys.argv) > 2:
        raw = sys.argv[2]
    elif len(sys.argv) > 1 and sys.argv[1].startswith("{"):
        raw = sys.argv[1]
    else:
        try:
            raw = sys.stdin.read()
        except:
            raw = "{}"
    try:
        params = json.loads(raw) if raw.strip() else {}
    except:
        params = {}
    h = handlers.get(action, do_run)
    result = h(params) if action == "run" else h(params)
    print(json.dumps(result, ensure_ascii=False, default=str))
