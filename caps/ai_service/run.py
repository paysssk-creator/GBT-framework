# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""ai_service/run.py v3.0 — 对标Intercom Fin AI
==================================================
平台级AI: 知识库驱动 · 多轮对话记忆 · 主动建议 · 快捷操作 · 升级工单
"""
# ⛔ 原生身体 — AI不是聊天机器人, 是有眼睛有手的智能体
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from brain.host_body import eyes, hands
    HAS_BODY = True
except:
    HAS_BODY = False

# ━━━ BetterCam 240Hz+ 高速视觉 ━━━
try:
    import bettercam
    _webcam = bettercam.create()
    HAS_BETTERCAM = True
except:
    _webcam = None
    HAS_BETTERCAM = False
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except: pass

def _web_see(region=None):
    """网站AI的高速眼睛"""
    if not HAS_BETTERCAM:
        return _call_cap_fallback('screenshot', 'capture', {})
    try:
        import base64, io
        from PIL import Image
        frame = _webcam.grab(region=(region['x'],region['y'],region['w'],region['h'])) if region else _webcam.grab()
        img = Image.fromarray(frame)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return {'ok': True, 'image': base64.b64encode(buf.getvalue()).decode(), 'fps': 240}
    except:
        return {'ok': False, 'error': 'capture failed'}

def _call_cap_fallback(cap, action, params):
    try:
        import subprocess, sys, json
        from pathlib import Path
        r = subprocess.run([sys.executable, str(Path(__file__).parent.parent/cap/'run.py'), action, json.dumps(params)],
            capture_output=True, text=True, timeout=10)
        return json.loads(r.stdout) if r.stdout else {'ok': False}
    except:
        return {'ok': False}

import sys, json, os, urllib.request, urllib.error, subprocess, hashlib
from pathlib import Path
from datetime import datetime, timezone

SANDBOX = Path(__file__).parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("KIMI_API_KEY", "")
BASE_URL = os.environ.get("GBT_LLM_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("GBT_LLM_MODEL", "deepseek-chat")
# ━━━ AI Gateway (Cloudflare) ━━━
try:
    import sys as _sys; _sys.path.insert(0, str(Path(__file__).parent.parent))
    from brain.ai_gateway import ai_gateway, cached_chat, fallback_chat, vision_chat
    HAS_AI_GATEWAY = True
except:
    HAS_AI_GATEWAY = False
    ai_gateway = None
# ═══════════════ 对话记忆 (多轮) ═══════════════
MEMORY_DIR = Path.home() / ".gbt" / "ai_memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

def _load_memory(session_id):
    f = MEMORY_DIR / f"{session_id}.json"
    if f.exists(): return json.loads(f.read_text(encoding="utf-8"))
    return {"messages":[],"context":{},"created":datetime.now(timezone.utc).isoformat()}

def _save_memory(session_id, data):
    f = MEMORY_DIR / f"{session_id}.json"
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ═══════════════ 知识库 ═══════════════
KNOWLEDGE_BASE = {
    "payment": {
        "question": "如何支付/收款?",
        "answer": "GBT支持全球最全支付: ①Stripe(Card/PayPal/Venmo/ACH/Wire)法币 ②CryptAPI(60+币种)BTC/ETH/SOL/USDC/USDT ③Bitcoin Lightning秒到。开发者80%分成,平台20%。",
        "quick_actions": ["查看支付方式","设置钱包","查看收益"],
        "next_steps": ["如何入驻","定价策略"],
    },
    "onboarding": {
        "question": "如何入驻/开始赚钱?",
        "answer": "3步入驻: ①访问/onboard.html输入邮箱 ②点击链接去Stripe完成KYC(护照+银行) ③提交GitHub仓库,AI自动部署。你拿80%收益!",
        "quick_actions": ["开始入驻","查看演示","联系支持"],
        "next_steps": ["支付方式","定价策略"],
    },
    "pricing": {
        "question": "如何定价/收费?",
        "answer": "AI基于GitHub Stars自动定价: 1K⭐→$0.5/h, 5K⭐→$0.8/h, 10K⭐→$1/h, 50K+⭐→$3-5/h。均价$1.84/h。平台抽20%。",
        "quick_actions": ["查看项目价格","提交项目","查看收益"],
        "next_steps": ["如何入驻","支付方式"],
    },
    "security": {
        "question": "代码安全吗?",
        "answer": "AES-256加密存储 + Docker沙盒隔离 + 独立容器运行。源码只在部署时解密,用户无法访问。SSL传输加密。",
        "quick_actions": ["查看安全详情","提交项目"],
        "next_steps": ["如何入驻","技术架构"],
    },
    "tech": {
        "question": "技术架构?",
        "answer": "Python 3.12 + 161个AI模块 + Docker容器 + Cloudflare部署。30秒部署,24/7 AI运维。505个测试全通过。",
        "quick_actions": ["查看技术文档","提交项目"],
        "next_steps": ["如何入驻","安全详情"],
    },
    "welcome": {
        "question": "欢迎/你好",
        "answer": "👋 我是GBT平台AI助手土豆仔! 我可以帮你: 了解支付方式、入驻赚钱、查看定价、解答技术问题。试试点下面的快捷操作?",
        "quick_actions": ["如何入驻","支付方式","定价策略","查看项目"],
        "next_steps": [],
    },
}

# ═══════════════ 系统提示 ═══════════════
SYSTEM_PROMPT = """你是GBT小土豆平台的AI助手"土豆仔"🥔，基于Intercom Fin AI架构设计。

平台核心信息:
- AI自主部署开源项目市场, AI界的8号当铺
- 161个AI能力模块, 17大智能邻域
- 支付: Stripe(Card/PayPal/Venmo/ACH/Wire) + CryptAPI(60+币种) + Lightning
- 分账: 80%开发者, 20%平台
- 入驻: onboard.html → Stripe KYC → 提交仓库 → 自动部署
- 定价: AI自动, 1K⭐=$0.5/h到50K+⭐=$3-5/h
- 安全: AES-256加密 + Docker沙盒
- 页面: 首页/onboard.html/dashboard.html/settings.html/help.html

回复规则: 友好简洁(3-5句), 提供具体操作步骤, 总是附上快捷操作建议"""

# ═══════════════ Action Handlers ═══════════════

def _get_context():
    """实时平台上下文"""
    ctx = []
    try:
        r = subprocess.run([sys.executable, str(SANDBOX/"caps"/"project_registry"/"run.py"), "stats", "{}"],
            capture_output=True, text=True, timeout=5, encoding="utf-8", errors="replace")
        if r.stdout:
            d = json.loads(r.stdout)
            ctx.append(f"项目: {d['total']}个, {len(d['categories'])}类, 均价${d['avg_price']}/h")
    except: ctx.append("项目: 13个, 9类")
    try:
        sys.path.insert(0, str(SANDBOX))
        from brain.nexus import get_nexus
        ctx.append(f"系统: {get_nexus().quick_health().get('health_pct',100)}%健康")
    except: pass
    return "; ".join(ctx)

def _call_llm(messages):
    if not API_KEY: return None
    try:
        data = json.dumps({"model":MODEL,"messages":messages,"max_tokens":500,"temperature":0.7}).encode()
        req = urllib.request.Request(f"{BASE_URL}/chat/completions", data=data,
            headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return resp["choices"][0]["message"]["content"]
    except: return None

def _match_knowledge(q):
    """知识库匹配"""
    ql = q.lower()
    scores = {}
    for key, entry in KNOWLEDGE_BASE.items():
        score = 0
        for kw in entry.get("question","").lower().split():
            if kw in ql: score += 1
        for kw in ql.split():
            if kw in entry.get("question","").lower(): score += 1
        if score > 0: scores[key] = score
    if scores:
        best = max(scores, key=scores.get)
        if scores[best] >= 2: return best  # 至少匹配2个关键词
    return None

# ═══════════════ Main Handlers ═══════════════


def do_chat_with_vision(params):
    """AI对话 + 图片分析"""
    question = params.get('question', params.get('message', ''))
    image_b64 = params.get('image', '')
    
    if image_b64:
        # Use native eyes to analyze the image
        # For uploaded images, we pass them to LLM vision API
        try:
            import urllib.request, json as _j
            api_key = os.environ.get('DEEPSEEK_API_KEY', os.environ.get('KIMI_API_KEY', ''))
            if api_key:
                req = urllib.request.Request(
                    'https://api.deepseek.com/chat/completions',
                    data=_j.dumps({
                        'model': 'deepseek-chat',
                        'messages': [{
                            'role': 'user',
                            'content': [
                                {'type': 'text', 'text': question or '请描述这张图片'},
                                {'type': 'image_url', 'image_url': {'url': image_b64}}
                            ]
                        }],
                        'max_tokens': 1000
                    }).encode(),
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    }
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = _j.loads(resp.read())
                    answer = data['choices'][0]['message']['content']
                    return {'ok': True, 'answer': answer, 'mode': 'vision'}
        except:
            pass
        
        # Use BetterCam for instant screen capture
            if HAS_BETTERCAM:
                screenshot = _web_see()
                if screenshot.get("ok"):
                    image_b64 = image_b64 or screenshot.get("image", "")
            
            # Fallback: local analysis using native body
        if HAS_BODY:
            try:
                # Use dominant colors + OCR-like analysis
                return {
                    'ok': True,
                    'answer': f'[图片已接收] 当前模式: 本地分析。图片大小约{len(image_b64)//1024}KB。如需AI视觉分析，请配置DEEPSEEK_API_KEY。',
                    'mode': 'local'
                }
            except:
                pass
    
    # Text-only fallback
    return do_chat(params)

def do_chat(params):
    """多轮对话 — 对标Intercom Fin"""
    q = params.get("question", params.get("q", ""))
    session_id = params.get("session", params.get("sid", "default"))
    if not q: return {"ok":False,"error":"需要question"}
    
    mem = _load_memory(session_id)
    ctx = _get_context()
    
    # ① 知识库精确匹配
    matched = _match_knowledge(q)
    if matched:
        entry = KNOWLEDGE_BASE[matched]
        mem["messages"].append({"role":"user","content":q})
        mem["messages"].append({"role":"assistant","content":entry["answer"]})
        _save_memory(session_id, mem)
        return {"ok":True,"answer":entry["answer"],"mode":"knowledge","matched":matched,
                "quick_actions":entry.get("quick_actions",[]),
                "next_topics":entry.get("next_steps",[]),
                "session":session_id,"context":ctx}
    
    # ② LLM深度回答
    messages = [
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"system","content":f"实时: {ctx}"},
    ]
    # 加入历史
    for m in mem.get("messages",[])[-6:]:
        messages.append(m)
    messages.append({"role":"user","content":q})
    
    answer = _call_llm(messages)
    
    if answer:
        mem["messages"].append({"role":"user","content":q})
        mem["messages"].append({"role":"assistant","content":answer})
        _save_memory(session_id, mem)
        return {"ok":True,"answer":answer,"mode":"llm","session":session_id,"context":ctx,
                "quick_actions":["如何入驻","支付方式","定价策略"]}
    
    # ③ 规则回退
    ql = q.lower()
    if any(w in ql for w in ['支付','pay','付款','币']):
        e = KNOWLEDGE_BASE["payment"]
    elif any(w in ql for w in ['入驻','注册','开始']):
        e = KNOWLEDGE_BASE["onboarding"]
    elif any(w in ql for w in ['价格','多少钱','定价']):
        e = KNOWLEDGE_BASE["pricing"]
    elif any(w in ql for w in ['安全','加密']):
        e = KNOWLEDGE_BASE["security"]
    elif any(w in ql for w in ['你好','hi','hello']):
        e = KNOWLEDGE_BASE["welcome"]
    else:
        e = KNOWLEDGE_BASE["welcome"]
    
    mem["messages"].append({"role":"user","content":q})
    mem["messages"].append({"role":"assistant","content":e["answer"]})
    _save_memory(session_id, mem)
    return {"ok":True,"answer":e["answer"],"mode":"rule","quick_actions":e.get("quick_actions",[]),
            "next_topics":e.get("next_steps",[]),"session":session_id,"context":ctx}

def do_suggest(params):
    """主动建议 — 根据用户所在页面提供上下文建议"""
    page = params.get("page", params.get("url", ""))
    suggestions = {
        "onboard": {"msg":"👋 看起来你想入驻赚钱! 需要我引导你完成Stripe KYC验证吗?","actions":["开始入驻","了解分账","查看定价"]},
        "dashboard": {"msg":"📊 在这里追踪你的收益。需要帮助理解数据吗?","actions":["如何提现","设置钱包","查看项目"]},
        "settings": {"msg":"⚙️ 配置你的通知和钱包。建议设置USDT钱包以接收加密付款。","actions":["设置钱包","通知偏好","查看收益"]},
        "help": {"msg":"📚 需要帮助吗? 试试搜索你关心的话题。","actions":["支付方式","入驻流程","定价策略"]},
        "default": {"msg":"👋 新用户? 让我帮你快速了解GBT平台!","actions":["如何入驻","支付方式","查看项目"]},
    }
    key = "default"
    for k in suggestions:
        if k in page.lower(): key = k; break
    s = suggestions[key]
    return {"ok":True,"suggestion":s["msg"],"actions":s["actions"],"page":page}

def do_help(params):
    """帮助中心"""
    topic = params.get("topic", params.get("t", "index"))
    help_db = {
        "index": {"title":"帮助中心","content":"选择主题: payment/onboarding/pricing/tech/security/faq",
                  "topics":["payment","onboarding","pricing","tech","security","faq"]},
        "payment": {"title":"支付","content":"Stripe(Card/PayPal/Venmo/ACH/Wire) + CryptAPI(60+币种:BTC/ETH/SOL/USDC/USDT) + Lightning秒到。80%给开发者。","actions":["设置钱包","查看收益"]},
        "onboarding": {"title":"入驻","content":"①访问onboard.html ②Stripe KYC ③提交GitHub仓库。30秒部署。","actions":["开始入驻"]},
        "pricing": {"title":"定价","content":"1K⭐→$0.5/h, 10K⭐→$1/h, 50K⭐→$3-5/h。AI自动定价。平台抽20%。","actions":["查看项目"]},
        "tech": {"title":"技术","content":"Python 3.12, 161 AI模块, Docker, Cloudflare, AES-256。505测试全通过。"},
        "security": {"title":"安全","content":"AES-256加密+Docker沙盒。源码运行时解密,用完销毁。SSL传输。"},
        "faq": {"title":"FAQ","content":"Q:如何开始→onboard.html|Q:到账→法币1-3天,加密即时|Q:安全→AES-256+沙盒|Q:下架→dashboard随时"},
    }
    entry = help_db.get(topic, help_db["index"])
    return {"ok":True,"topic":topic,"title":entry["title"],"content":entry["content"],
            "actions":entry.get("actions",[]),"topics":entry.get("topics",list(help_db.keys()))}


def do_screenshot(params):
    """截图 — 使用BetterCam高速采集或回退方案"""
    if HAS_BETTERCAM:
        result = _web_see(params.get("region"))
        if result.get("ok"):
            return {"ok": True, "image": result["image"], "format": "png", "fps": 240, "mode": "bettercam"}
    # 回退: 调用local_eye
    fallback = _call_cap_fallback("local_eye", "scan", params)
    if fallback.get("ok") and fallback.get("screenshot"):
        return {"ok": True, "image": fallback["screenshot"], "format": "png", "mode": "fallback"}
    # 最后回退: 调用omni_eye
    uia = _call_cap_fallback("omni_eye", "see", params)
    return {"ok": True, "mode": "uia_only", "windows": uia.get("windows", []), "note": "截图不可用,返回UIA窗口结构"}

HANDLERS = {"chat":do_chat,"suggest":do_suggest,"help":do_help,"vision":do_chat_with_vision,"screenshot":do_screenshot,"run":do_chat}
if __name__=="__main__":
    a=sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith("-") else "chat"
    p={}
    if len(sys.argv)>2:
        try:p=json.loads(sys.argv[2])
        except:p={}
    h=HANDLERS.get(a,lambda x:{"ok":False,"error":f"未知:{a}"})
    print(json.dumps(h(p),ensure_ascii=False,default=str))
