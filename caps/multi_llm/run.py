# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""multi_llm/run.py — 多模型智能网关 (13 providers)"""
import sys, json, os, urllib.request, urllib.error
from pathlib import Path

PROVIDERS = {
    "kimi": {"base": "https://api.moonshot.cn/v1", "model": "deepseek-v4-pro", "key_env": ["MOONSHOT_API_KEY","KIMI_API_KEY"]},
    "deepseek": {"base": "https://api.deepseek.com/v1", "model": "deepseek-v4-pro", "key_env": ["DEEPSEEK_API_KEY"]},
    "openai": {"base": "https://api.openai.com/v1", "model": "gpt-4o", "key_env": ["OPENAI_API_KEY"]},
    "zhipu": {"base": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash", "key_env": ["ZHIPU_API_KEY","GLM_API_KEY"]},
    "qwen": {"base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-turbo", "key_env": ["DASHSCOPE_API_KEY","QWEN_API_KEY"]},
    "ollama": {"base": "http://localhost:11434/v1", "model": "qwen3:0.6b", "key_env": []},
    "siliconflow": {"base": "https://api.siliconflow.cn/v1", "model": "Qwen/Qwen2.5-7B-Instruct", "key_env": ["SILICONFLOW_API_KEY"]},
}

def _get_key(provider):
    cfg = PROVIDERS.get(provider, {})
    for env in cfg.get("key_env", []):
        k = os.environ.get(env, "")
        if k: return k
    return ""

def _call_llm(provider, prompt, max_tokens=1024):
    cfg = PROVIDERS.get(provider)
    if not cfg: return None
    key = _get_key(provider)
    if not key and cfg["key_env"]: return None
    url = f"{cfg['base'].rstrip('/')}/chat/completions"
    body = json.dumps({"model": cfg["model"], "messages": [{"role":"user","content":prompt}],
                       "max_tokens": max_tokens}).encode()
    headers = {"Content-Type": "application/json"}
    if key: headers["Authorization"] = f"Bearer {key}"
    try:
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except: return None

def do_ask(params):
    prompt = params.get("prompt", params.get("q", ""))
    provider = params.get("provider", "auto")
    if not prompt: return {"ok": False, "error": "缺少 prompt"}
    # ═ 邻域安全管道: input_sanitizer 预处理 ═
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from caps.input_sanitizer.run import do_check
        chk = do_check({"input": prompt, "mode": "fast"})
        if chk.get("level") == "dangerous":
            return {"ok": False, "blocked": True, "reason": chk.get("summary", "input_sanitizer阻断")}
    except Exception:
        pass
    if provider == "auto":
        # 自动选第一个可用的
        for p in PROVIDERS:
            if _get_key(p) or p == "ollama":
                provider = p; break
    result = _call_llm(provider, prompt)
    if result:
        return {"ok": True, "provider": provider, "model": PROVIDERS[provider]["model"], "response": result}
    return {"ok": False, "error": f"{provider} 调用失败", "provider": provider}

def do_models(params=None):
    available = []
    for name, cfg in PROVIDERS.items():
        key = _get_key(name)
        available.append({"name": name, "model": cfg["model"], 
                         "available": bool(key) or name == "ollama",
                         "base": cfg["base"][:40]})
    return {"ok": True, "providers": len(PROVIDERS), "available": sum(1 for a in available if a["available"]), "models": available}

def do_switch(params):
    provider = params.get("provider", "")
    if provider not in PROVIDERS:
        return {"ok": False, "error": f"不支持的provider: {provider}", "available": list(PROVIDERS.keys())}
    os.environ["GBT_LLM_PROVIDER"] = provider
    return {"ok": True, "switched": provider, "model": PROVIDERS[provider]["model"]}

def do_compare(params):
    prompt = params.get("prompt", params.get("q", ""))
    providers_list = params.get("providers", ["deepseek", "kimi"])
    if not prompt: return {"ok": False, "error": "缺少 prompt"}
    results = {}
    for p in providers_list:
        r = _call_llm(p, prompt, 256)
        if r: results[p] = r[:200]
        else: results[p] = "不可用"
    return {"ok": True, "prompt": prompt[:100], "results": results}

HANDLERS = {"ask": do_ask, "models": do_models, "switch": do_switch, "compare": do_compare}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "ask"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
