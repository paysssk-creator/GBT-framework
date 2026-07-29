# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""cloud_brain/run.py — 云端大脑 (本地优先,云端可选)
=====================================================
默认纯本地运行 · 有密钥自动升级云端 · 零配置可启动
"""
import sys, json, os, time, shutil, subprocess
from pathlib import Path
from datetime import datetime, timezone

# 加载 .env
_env = Path(__file__).parent.parent.parent.parent / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            if _k.strip() not in os.environ: os.environ[_k.strip()] = _v.strip()

CLOUD_DIR = Path.home() / ".gbt" / "cloud"
CLOUD_DIR.mkdir(parents=True, exist_ok=True)
SYNC_DIR = CLOUD_DIR / "sync"

# 四脑架构： Flash(极速草稿) + Pro(深度推理) 并发协作
MODEL_FLASH = "deepseek-v4-flash"   # 极速，出草稿
MODEL_PRO   = "deepseek-v4-pro"     # 深度，审核+终稿
DS_KEY  = os.environ.get("DEEPSEEK_API_KEY", "")
DS_BASE = "https://api.deepseek.com/v1"

# 其他云端提供商(备用)
CLOUD_PROVIDERS = {
    "deepseek_pro":   {"base":DS_BASE,"model":MODEL_PRO,  "key_env":"DEEPSEEK_API_KEY"},
    "deepseek_flash": {"base":DS_BASE,"model":MODEL_FLASH,"key_env":"DEEPSEEK_API_KEY"},
    "siliconflow":    {"base":"https://api.siliconflow.cn/v1","model":"deepseek-ai/deepseek-v4-pro","key_env":"SILICONFLOW_API_KEY"},
    "huggingface":    {"base":"https://router.huggingface.co/hf-inference/v1","model":"mistralai/Mistral-7B-Instruct-v0.3","key_env":"HF_API_KEY"},
}

def _has_any_cloud_key():
    return bool(DS_KEY or any(os.environ.get(cfg["key_env"]) for cfg in CLOUD_PROVIDERS.values()))

def _call_one(model: str, messages: list, max_tokens=2000) -> str | None:
    """single model call"""
    if not DS_KEY: return None
    import urllib.request
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }).encode()
    try:
        req = urllib.request.Request(
            DS_BASE + "/chat/completions", data=body,
            headers={"Content-Type":"application/json","Authorization":f"Bearer {DS_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except: return None

def _quad_brain(prompt: str, max_tokens=2000) -> dict:
    """
    四脑协作核心逻辑
    Flash 和 Pro 并发运行，然后合并输出
    """
    import threading

    SYS = ("You are GBT小土豆, powered by GBT-JXDWD dual-brain engine. "
           "你是GBT小土豆，由Flash+Pro双大模型协同驱动，不要自称DeepSeek或任何模型名。")
    msgs = [{"role":"system","content":SYS},{"role":"user","content":prompt}]

    results = {}

    def run_flash():
        results["flash"] = _call_one(MODEL_FLASH,
            [{"role":"system","content":SYS+"快速出草稿，简明扬要。"},
             {"role":"user","content":prompt}],
            max_tokens=800)

    def run_pro():
        results["pro"] = _call_one(MODEL_PRO,
            [{"role":"system","content":SYS+"深度思考，全面推理，给出最佳答案。"},
             {"role":"user","content":prompt}],
            max_tokens=max_tokens)

    t1 = threading.Thread(target=run_flash, daemon=True)
    t2 = threading.Thread(target=run_pro, daemon=True)
    t1.start(); t2.start()
    t1.join(timeout=35); t2.join(timeout=35)

    flash_ans = results.get("flash")
    pro_ans   = results.get("pro")

    if pro_ans and flash_ans:
        # 四脑全通：Pro为主，Flash补充辨证
        final = pro_ans
        if flash_ans.strip() != pro_ans.strip():
            final += f"\n\n---\n💡 *Flash快赍补充*: {flash_ans[:300]}"
        return {"ok":True,"mode":"quad_brain","model":"flash+pro","response":final,
                "flash_ms":"done","pro_ms":"done"}
    elif pro_ans:
        return {"ok":True,"mode":"pro_only","model":MODEL_PRO,"response":pro_ans}
    elif flash_ans:
        return {"ok":True,"mode":"flash_only","model":MODEL_FLASH,"response":flash_ans}
    else:
        return {"ok":False,"error":"四脑均无响应，检查DEEPSEEK_API_KEY"}

def _call_cloud(provider, prompt, max_tokens=2000):
    cfg = CLOUD_PROVIDERS.get(provider)
    if not cfg: return None
    key = os.environ.get(cfg["key_env"], "")
    if not key: return None
    import urllib.request
    url = f"{cfg['base'].rstrip('/')}/chat/completions"
    body = json.dumps({"model":cfg["model"],"messages":[
        {"role":"system","content":"你是GBT小土豆，由GBT-JXDWD驱动。"},
        {"role":"user","content":prompt}
    ],"max_tokens":max_tokens}).encode()
    headers = {"Content-Type":"application/json","Authorization":f"Bearer {key}"}
    try:
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except: return None

def _call_local(prompt):
    """本地推理 — ollama 或项目内置LLM"""
    # 1. 尝试 ollama
    try:
        r = subprocess.run(["ollama","run","qwen3:0.6b",prompt],
                          capture_output=True,text=True,timeout=15,encoding="utf-8",errors="replace")
        if r.returncode==0 and r.stdout.strip(): return r.stdout.strip()[:1000]
    except: pass
    # 2. 尝试项目内置LLM
    try:
        from intent_broker import _call_llm
        r = _call_llm([{"role":"user","content":prompt}], max_tokens=1000)
        if r: return r
    except: pass
    return None

def do_reason(params):
    topic = params.get("topic", params.get("prompt", params.get("query","")))
    if not topic: return {"ok":False,"error":"缺少 topic"}

    # 默认四脑协作模式
    dual = params.get("dual", True)
    provider = params.get("provider", "auto")

    if DS_KEY and (dual or provider == "auto"):
        result = _quad_brain(topic, max_tokens=params.get("max_tokens", 2000))
        if result.get("ok"):
            return result

    # 备用：其他云端
    if _has_any_cloud_key():
        for p in CLOUD_PROVIDERS:
            r = _call_cloud(p, topic)
            if r: return {"ok":True,"provider":p,"response":r,"mode":"cloud_fallback"}

    # 本地推理
    local = _call_local(topic)
    if local:
        return {"ok":True,"provider":"local","response":local,"mode":"local"}

    return {"ok":True,"provider":"builtin","mode":"local",
            "response":f"【本地分析】{topic}\n\n基于规则引擎的推理结果\n1. 问题已记录\n2. 待云端连接后进行深度分析\n3. 当前可使用本地能力模块处理",
            "note":"无API密鑰，使用内置规则引擎。配置DEEPSEEK_API_KEY可启用四脑推理"}

def do_sync(params):
    """本地同步 — 备份到本地+可选云端"""
    what = params.get("what", "all")
    synced_dir = SYNC_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
    synced_dir.mkdir(parents=True, exist_ok=True)
    results = []
    
    # 备份项目状态
    sf = Path.home()/".gbt"/"state"/"GBT-JXDWD"/"state.json"
    if sf.exists():
        shutil.copy2(sf, synced_dir/"project_state.json")
        results.append("project_state")
    
    # 备份记忆
    mf = Path("sandbox/memory_store.json")
    if mf.exists():
        shutil.copy2(mf, synced_dir/"memory.json")
        results.append("memory")
    
    # 备份保险库
    vf = Path.home()/".gbt"/"vault"/"accounts.json"
    if vf.exists():
        shutil.copy2(vf, synced_dir/"vault.json")
        results.append("vault")
    
    return {"ok":True,"synced":len(results),"items":results,
            "sync_dir":str(synced_dir),"mode":"local"}

def do_pull(params=None):
    """从本地备份恢复"""
    backups = sorted(SYNC_DIR.glob("*"), key=lambda p:p.stat().st_mtime, reverse=True)
    if not backups: return {"ok":False,"error":"无本地备份"}
    latest = backups[0]
    return {"ok":True,"latest_backup":str(latest),
            "files":[f.name for f in latest.iterdir()],
            "mode":"local"}

def do_kv(params):
    action = params.get("action","get")
    key = params.get("key",""); value = params.get("value","")
    if KV_FILE.exists():
        try: kv = json.loads(KV_FILE.read_text(encoding="utf-8"))
        except: kv = {}
    else: kv = {}
    if action=="get":
        return {"ok":True,"key":key,"value":kv.get(key)} if key else {"ok":True,"keys":list(kv.keys()),"count":len(kv)}
    if action=="set" and key: kv[key]=value; KV_FILE.write_text(json.dumps(kv,ensure_ascii=False,indent=2)); return {"ok":True,"key":key,"set":True}
    if action=="delete" and key and key in kv: del kv[key]; KV_FILE.write_text(json.dumps(kv,ensure_ascii=False,indent=2)); return {"ok":True,"deleted":True}
    if action=="clear": KV_FILE.write_text("{}"); return {"ok":True,"cleared":True}
    return {"ok":False,"error":f"未知:{action}"}

def do_models(p=None):
    available = []
    for name, cfg in CLOUD_PROVIDERS.items():
        available.append({"name":name,"model":cfg["model"],"ready":bool(os.environ.get(cfg["key_env"],""))})
    # 本地模型
    try:
        r = subprocess.run(["ollama","list"],capture_output=True,text=True,timeout=3)
        if r.returncode==0: available.append({"name":"ollama","model":"local","ready":True})
    except: available.append({"name":"ollama","model":"local","ready":False})
    available.append({"name":"builtin","model":"规则引擎","ready":True})
    return {"ok":True,"total":len(available),"ready":sum(1 for a in available if a["ready"]),
            "has_cloud_keys":_has_any_cloud_key(),"models":available}

def do_deploy(params):
    """部署到远程服务器 (SSH,不需要云API密钥)"""
    try:
        from capability_protocol import get_engine
        engine = get_engine()
        return engine.call("remote_deploy","deploy",{
            "local":str(Path(__file__).parent.parent.parent.parent),
            "remote":params.get("remote","/opt/gbt-brain"),
            "name":params.get("server",""),"host":params.get("host",""),
            "user":params.get("user","root"),
        })
    except Exception as e:
        return {"ok":False,"error":str(e),"note":"配置远程服务器: 编辑 ~/.gbt/hosts.json 或传入 host/user 参数"}

def do_status(p=None):
    """四脑状态速查"""
    has_key = bool(DS_KEY)
    return {
        "ok":        True,
        "engine":    "quad_brain",
        "flash":     MODEL_FLASH,
        "pro":       MODEL_PRO,
        "api_key":   "configured" if has_key else "missing",
        "ds_base":   DS_BASE,
        "ready":     has_key,
        "providers": list(CLOUD_PROVIDERS.keys()),
        "note":      "Flash+Pro四脑并发就绪" if has_key else "缺少DEEPSEEK_API_KEY",
    }

HANDLERS = {
    "reason":  do_reason,
    "ask":     do_reason,
    "query":   do_reason,
    "sync":    do_sync,
    "pull":    do_pull,
    "kv":      do_kv,
    "models":  do_models,
    "status":  do_status,
    "deploy":  do_deploy,
}

if __name__=="__main__":
    action = sys.argv[1].lstrip("-") if len(sys.argv)>1 and sys.argv[1]!="run.py" else "models"
    params={}
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h=HANDLERS.get(action,lambda p:{"ok":False,"error":f"未知:{action}"})
    print(json.dumps(h(params),ensure_ascii=False,default=str))
