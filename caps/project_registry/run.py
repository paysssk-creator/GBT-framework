# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""project_registry/run.py — 项目注册中心
=============================================
平台项目全生命周期管理: 注册·部署·上下架·状态跟踪
"""
import sys, json, os, time, subprocess
from pathlib import Path
from datetime import datetime, timezone

SANDBOX = Path(__file__).parent.parent
REGISTRY_FILE = Path.home() / ".gbt" / "project_registry.json"
REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)

# 默认种子项目
SEED_PROJECTS = [
    {"id":"n8n","name":"N8N · 自动化工作流","stars":"58K","price":0.50,"category":"automation","status":"active","tags":["自动化","低代码"],"icon":"n8n","color":"#ff6d00"},
    {"id":"supabase","name":"Supabase · 开源Firebase","stars":"78K","price":1.00,"category":"backend","status":"active","tags":["后端"],"icon":"supabase","color":"#3ecf8e"},
    {"id":"lobechat","name":"LobeChat · AI对话","stars":"65K","price":1.00,"category":"ai","status":"active","tags":["AI","SaaS"],"icon":"lobechat","color":"#4da6ff"},
    {"id":"calcom","name":"Cal.com · 日程调度","stars":"42K","price":0.60,"category":"saas","status":"active","tags":["SaaS"],"icon":"cal","color":"#292929"},
    {"id":"appwrite","name":"Appwrite · BaaS后端","stars":"47K","price":1.20,"category":"backend","status":"active","tags":["后端"],"icon":"appwrite","color":"#fd366e"},
    {"id":"ghost","name":"Ghost · 独立博客","stars":"48K","price":0.80,"category":"cms","status":"active","tags":["CMS"],"icon":"ghost","color":"#15171a"},
    {"id":"langgraph","name":"LangGraph · Agent框架","stars":"68K","price":2.00,"category":"ai","status":"active","tags":["AI","Agent"],"icon":"langgraph","color":"#1a1a2e"},
    {"id":"opencode","name":"OpenCode · AI编程","stars":"180K","price":3.00,"category":"dev","status":"active","tags":["AI","Dev"],"icon":"opencode","color":"#0d1117"},
    {"id":"devopsgpt","name":"DevOpsGPT · AI运维","stars":"8K","price":1.50,"category":"devops","status":"active","tags":["DevOps"],"icon":"devopsgpt","color":"#fc6d26"},
    {"id":"qwen3","name":"Qwen3-235B · Agent模型","stars":"12K","price":5.00,"category":"ai","status":"active","tags":["AI","Model"],"icon":"qwen","color":"#615eed"},
    {"id":"kokoro","name":"Kokoro-TTS · 语音合成","stars":"8K","price":2.50,"category":"ai","status":"active","tags":["AI","Audio"],"icon":"kokoro","color":"#ffd24c"},
    {"id":"ruoyi","name":"RuoYi-Vue · 企业后台","stars":"42K","price":0.80,"category":"admin","status":"active","tags":["Admin"],"icon":"ruoyi","color":"#c71d23"},
    {"id":"pentestai","name":"PentestAI · 渗透测试","stars":"6K","price":4.00,"category":"security","status":"active","tags":["Security"],"icon":"pentestai","color":"#00ff41"},
]

def _load():
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return {"projects": SEED_PROJECTS, "updated": datetime.now(timezone.utc).isoformat()}

def _save(data):
    REGISTRY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def do_list(params=None):
    """列出所有项目"""
    data = _load()
    projects = data["projects"]
    # 过滤
    status = (params or {}).get("status","active")
    category = (params or {}).get("category","")
    limit = (params or {}).get("limit",50)
    if status != "all": projects = [p for p in projects if p.get("status")==status]
    if category: projects = [p for p in projects if p.get("category")==category]
    return {"ok":True,"projects":projects[:limit],"total":len(projects),"categories":list(set(p.get("category","") for p in data["projects"]))}

def do_register(params):
    """注册新项目"""
    name = params.get("name",""); repo = params.get("repo","")
    stars = params.get("stars","?"); price = float(params.get("price",0.50))
    category = params.get("category","other"); tags = params.get("tags",[])
    if not name: return {"ok":False,"error":"需要name参数"}
    data = _load()
    pid = repo.split("/")[-1].replace(".git","").lower() if repo else name.lower().replace(" ","-")[:20]
    # 去重
    if any(p["id"]==pid for p in data["projects"]): return {"ok":False,"error":f"项目{pid}已存在"}
    new = {"id":pid,"name":name,"stars":stars,"price":price,"category":category,"status":"pending","tags":tags,"icon":pid[:2],"color":"#4da6ff","repo":repo,"created":datetime.now(timezone.utc).isoformat()}
    data["projects"].append(new)
    data["updated"]=datetime.now(timezone.utc).isoformat()
    _save(data)
    return {"ok":True,"project":new}

def do_deploy(params):
    """部署/上下架项目"""
    pid = params.get("id",""); status = params.get("status","active")
    if not pid: return {"ok":False,"error":"需要id参数"}
    data = _load()
    for p in data["projects"]:
        if p["id"]==pid: p["status"]=status; p["updated"]=datetime.now(timezone.utc).isoformat(); data["updated"]=datetime.now(timezone.utc).isoformat(); _save(data); return {"ok":True,"id":pid,"status":status}
    return {"ok":False,"error":f"项目{pid}不存在"}

def do_stats(params=None):
    """项目统计"""
    data = _load()
    projects = data["projects"]
    total = len(projects); active = sum(1 for p in projects if p.get("status")=="active")
    cats = {}; [cats.update({p.get("category","other"):cats.get(p.get("category","other"),0)+1}) for p in projects]
    return {"ok":True,"total":total,"active":active,"pending":total-active,"categories":cats,"avg_price":round(sum(p["price"] for p in projects)/max(total,1),2)}

HANDLERS={"list":do_list,"register":do_register,"deploy":do_deploy,"stats":do_stats,"run":do_list}
if __name__=="__main__":
    a=sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith("-") else "list"
    p={}
    if len(sys.argv)>2:
        try:p=json.loads(sys.argv[2])
        except:p={}
    h=HANDLERS.get(a,lambda x:{"ok":False,"error":f"未知:{a}"})
    print(json.dumps(h(p),ensure_ascii=False,default=str))
