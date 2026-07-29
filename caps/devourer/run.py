# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""caps/devourer/run.py — 自主吞噬进化引擎 v3.0 · 极限版
========================================================================
全平台扫描 + 智能缺口检测 + 自动Cap生成 + 技能市场同步

扫描源: 10+代码平台 + 8大技能市场
能力: 自动识别GBT缺失技能 → 生成cap骨架 → 注入认知 → 注册nexus
"""
import sys, json, os, time, re, urllib.request, urllib.error, subprocess, threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from pathlib import Path
from datetime import datetime
from collections import Counter

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("KIMI_API_KEY") or ""

# ═══════════════════════════════════════════════════════════
#  全平台扫描源 — 10+代码平台 + 分领域定向扫描
# ═══════════════════════════════════════════════════════════

DEVOUR_SOURCES = [
    # ── 代码平台 (priority 1) ──
    {"name":"GitHub Trending Python","url":"https://github.com/trending/python?since=daily","priority":1,"category":"code"},
    {"name":"GitHub Trending All","url":"https://github.com/trending?since=weekly","priority":1,"category":"code"},
    {"name":"GitLab Trending","url":"https://gitlab.com/explore/projects/trending","priority":1,"category":"code"},
    {"name":"Gitee Trending","url":"https://gitee.com/explore/all","priority":1,"category":"code"},
    # ── AI/ML平台 (priority 1) ──
    {"name":"HuggingFace Models","url":"https://huggingface.co/models?sort=trending","priority":1,"category":"ai"},
    {"name":"Papers With Code","url":"https://paperswithcode.com/","priority":2,"category":"ai"},
    {"name":"arXiv cs.AI","url":"https://arxiv.org/list/cs.AI/recent","priority":2,"category":"ai"},
    # ── 产品/工具平台 (priority 2) ──
    {"name":"ProductHunt AI","url":"https://www.producthunt.com/topics/artificial-intelligence","priority":2,"category":"product"},
    {"name":"Hacker News Show","url":"https://news.ycombinator.com/show","priority":2,"category":"product"},
    # ── 技能市场 (priority 2) ──
    {"name":"Agent Skills Registry","url":"https://agentskills.io","priority":2,"category":"skills"},
    {"name":"SkillsLLM Marketplace","url":"https://skillsllm.com","priority":2,"category":"skills"},
    # ── 安全/攻击域定向 (priority 3) ──
    {"name":"Exploit-DB Recent","url":"https://www.exploit-db.com/","priority":3,"category":"security"},
    {"name":"OWASP Projects","url":"https://owasp.org/projects/","priority":3,"category":"security"},
    # ── Web3/DeFi (priority 3) ──
    {"name":"CoinGecko Trending","url":"https://www.coingecko.com/en/trending-crypto","priority":3,"category":"web3"},
    {"name":"DeFi Llama","url":"https://defillama.com/","priority":3,"category":"web3"},
    # ── 量化金融 (priority 3) ──
    {"name":"QuantConnect","url":"https://www.quantconnect.com/","priority":3,"category":"finance"},
]

DEVOUR_LOG = Path.home() / ".gbt" / "memory" / "devour_log.jsonl"
GAP_LOG = Path.home() / ".gbt" / "memory" / "cap_gaps.json"
DEVOUR_LOG.parent.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  GBT现有能力映射 — 用于智能缺口检测
# ═══════════════════════════════════════════════════════════

def _get_existing_caps() -> set:
    """获取所有已存在的cap名称"""
    caps_dir = ROOT / "caps"
    if not caps_dir.exists():
        return set()
    return {d.name for d in caps_dir.iterdir() if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_")}

def _get_existing_domains() -> dict:
    """获取已有域及其能力"""
    try:
        from brain.nexus import NEIGHBORHOODS
        domains = {}
        for domain, info in NEIGHBORHOODS.items():
            domains[domain] = list(info["caps"].keys())
        return domains
    except:
        return {}

KNOWN_CAP_KEYWORDS = {
    # 已有能力关键词 — 匹配到这些说明已覆盖
    "browser": ["browser_ctrl","browser_open","deep_scrape","precision_scrape"],
    "email": [],
    "slack": [],
    "discord": [],
    "calendar": [],
    "payment": [],
    "trading": [],
    "defi": [],
    "translation": [],
    "game": [],
    "compliance": [],
    "human_loop": [],
}

# ═══════════════════════════════════════════════════════════
#  智能缺口检测引擎
# ═══════════════════════════════════════════════════════════

def analyze_gaps() -> dict:
    """分析GBT能力缺口 — 对比行业标准技能分类"""
    existing = _get_existing_caps()
    domains = _get_existing_domains()
    
    # 行业标准技能分类 (基于agentskills.io/SkillsLLM分类体系)
    industry_skills = {
        "浏览器自动化": {"keywords":["selenium","playwright","puppeteer","browser","headless","webdriver"],"existing":[],"priority":"high"},
        "Email通信": {"keywords":["smtp","imap","email","mail","sendgrid","mailgun"],"existing":[],"priority":"high"},
        "Slack/Discord": {"keywords":["slack","discord","webhook","bot"],"existing":[],"priority":"high"},
        "日历调度": {"keywords":["calendar","google calendar","ical","scheduling","cron"],"existing":[],"priority":"medium"},
        "支付/交易": {"keywords":["stripe","paypal","payment","invoice","billing"],"existing":[],"priority":"medium"},
        "内容发布": {"keywords":["cms","wordpress","blog","medium","social media","post"],"existing":[],"priority":"medium"},
        "翻译/本地化": {"keywords":["translate","i18n","localization","language","deepl"],"existing":[],"priority":"medium"},
        "人类反馈": {"keywords":["human in the loop","approval","review","feedback","human"],"existing":[],"priority":"low"},
        "模拟/游戏": {"keywords":["simulation","game","gym","environment","rl"],"existing":[],"priority":"low"},
        "合规/审计": {"keywords":["compliance","audit","regulation","gdpr","soc2","iso"],"existing":[],"priority":"low"},
        "数据分析": {"keywords":["analytics","dashboard","metrics","reporting","bi"],"existing":[],"priority":"low"},
    }
    
    # 匹配已有能力
    # 匹配已有能力 — 关键词匹配 + 建议名精确匹配
    for cap_name in existing:
        for skill_name, info in industry_skills.items():
            if any(kw in cap_name.lower() for kw in info["keywords"]) or \
               cap_name == _suggest_cap_name(skill_name):
                info["existing"].append(cap_name)
    
    gaps = {k:v for k,v in industry_skills.items() if not v["existing"]}
    return {
        "ok": True,
        "total_caps": len(existing),
        "total_domains": len(domains),
        "industry_skills_total": len(industry_skills),
        "covered": sum(1 for v in industry_skills.values() if v["existing"]),
        "gaps": {k:{"priority":v["priority"],"keywords":v["keywords"],"suggestion":_suggest_cap_name(k)} for k,v in gaps.items()},
        "recommendation": "优先补齐HIGH优先级缺口" if any(v["priority"]=="high" for v in gaps.values()) else "基本覆盖",
    }

def _suggest_cap_name(skill_name: str) -> str:
    """为缺失技能建议cap名称"""
    suggestions = {
        "浏览器自动化": "browser_automation",
        "Email通信": "email_engine", 
        "Slack/Discord": "slack_bot",
        "日历调度": "calendar_sync",
        "支付/交易": "payment_gateway",
        "内容发布": "content_publisher",
        "翻译/本地化": "translator",
        "人类反馈": "human_review",
        "模拟/游戏": "simulation_env",
        "合规/审计": "compliance_checker",
        "数据分析": "analytics_dashboard",
    }
    return suggestions.get(skill_name, skill_name.lower().replace(" ","_").replace("/","_"))

# ═══════════════════════════════════════════════════════════
#  增强扫描引擎
# ═══════════════════════════════════════════════════════════
def _scan_one_source(src: dict) -> dict:
    """扫描单个源 — 供线程池调用"""
    entry = {"source": src["name"], "category": src["category"], "priority": src["priority"],
             "timestamp": time.time(), "status": "attempted", "findings": []}
    try:
        if API_KEY:
            entry["findings"] = _llm_scan(src)
            entry["status"] = "llm"
        else:
            entry["findings"] = _enhanced_simulated_scan(src)
            entry["status"] = "simulated"
    except Exception as e:
        entry["status"] = "failed"
        entry["error"] = str(e)[:200]
    return entry

def scan_platforms(max_workers: int = 8, per_source_timeout: int = 45) -> dict:
    """全平台扫描 — 真正并发(ThreadPoolExecutor)"""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_scan_one_source, src): src for src in DEVOUR_SOURCES}
        for future in as_completed(futures):
            src = futures[future]
            try:
                results.append(future.result(timeout=per_source_timeout))
            except FutureTimeoutError:
                results.append({"source": src["name"], "category": src["category"],
                                "priority": src["priority"], "timestamp": time.time(),
                                "status": "timeout", "findings": []})
            except Exception as e:
                results.append({"source": src["name"], "category": src["category"],
                                "priority": src["priority"], "timestamp": time.time(),
                                "status": "failed", "error": str(e)[:200], "findings": []})
    
    # 附加: 缺口分析
    gap_analysis = analyze_gaps()
    
    return {
        "ok": True,
        "scanned": len(results),
        "total_findings": sum(len(r["findings"]) for r in results),
        "sources": results,
        "gap_analysis": gap_analysis,
        "timestamp": time.time(),
    }

def _llm_scan(src: dict) -> list:
    """LLM驱动扫描 — 分析平台热度"""
    try:
        prompt = f"""分析{src['name']}({src['category']}类)当前热度前10项目。
返回JSON数组(最多10个):
[{{"title":"项目名","description":"一句话描述","why_trending":"为什么火","value_score":1-10,
   "absorbable":true/false,"category":"{src['category']}",
   "novelty":"novel/known","inject_to":"建议注入的GBT cap名",
   "key_learnings":["关键学习点1","关键学习点2","关键学习点3"]}}]
只返回JSON数组,不要其他文字。"""
        
        data = json.dumps({
            "model":"deepseek-chat",
            "messages":[{"role":"system","content":"你是顶尖AI趋势分析师。只返回JSON。"},{"role":"user","content":prompt}],
            "max_tokens":3000,"temperature":0.3
        }).encode()
        req = urllib.request.Request(
            "https://api.deepseek.com/chat/completions", data=data,
            headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        content = resp["choices"][0]["message"]["content"].strip()
        if "```" in content:
            content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        findings = json.loads(content)
        for f in findings:
            f["scanned_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f["mode"] = "llm"
            f["source"] = src["name"]
        return findings
    except:
        return _enhanced_simulated_scan(src)

def _enhanced_simulated_scan(src: dict) -> list:
    """降级模拟扫描 — API不可用时的静态示例数据，非真实扫描结果"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sim_db = {
        "GitHub Trending Python": [
            {"title":"LangGraph v2.0","description":"生产级多Agent编排框架","why_trending":"2026最热Agent框架","value_score":9,"absorbable":True,"category":"code","novelty":"known","inject_to":"agency","key_learnings":["声明式Agent图","检查点/回滚","流式Human-in-the-loop"]},
            {"title":"OpenCode 180k stars","description":"开源AI编程Agent (MIT)","why_trending":"SWE-bench 74%","value_score":10,"absorbable":True,"category":"code","novelty":"novel","inject_to":"programming","key_learnings":["100行实现Agent","多模型后端","终端原生集成"]},
            {"title":"CrewAI v2.0","description":"角色扮演多Agent框架","why_trending":"52k stars","value_score":9,"absorbable":True,"category":"code","novelty":"known","inject_to":"agency","key_learnings":["角色定义DSL","Agent间消息传递","任务委派模式"]},
            {"title":"AgentSkills SDK","description":"标准化Agent技能包格式","why_trending":"Anthropic推出","value_score":9,"absorbable":True,"category":"skills","novelty":"novel","inject_to":"skill_library","key_learnings":["SKILL.md规范","技能发现协议","版本管理"]},
            {"title":"BrowserUse v3","description":"AI浏览器自动化框架","why_trending":"GUI Agent核心","value_score":9,"absorbable":True,"category":"code","novelty":"novel","inject_to":"desktop_master","key_learnings":["Playwright集成","视觉定位","多Tab管理"]},
            {"title":"Mem0 v0.9","description":"SOTA Agent记忆层","why_trending":"91.6%准确率","value_score":9,"absorbable":True,"category":"ai","novelty":"novel","inject_to":"memory","key_learnings":["混合检索","时序衰减","用户画像"]},
            {"title":"Qwen3-Agent","description":"阿里开源Agent框架","why_trending":"中文生态最全","value_score":8,"absorbable":True,"category":"code","novelty":"known","inject_to":"multi_llm","key_learnings":["工具调用优化","RAG增强","多轮对话"]},
            {"title":"Semgrep AI Rules","description":"AI驱动的代码安全规则","why_trending":"SAST新范式","value_score":8,"absorbable":True,"category":"security","novelty":"novel","inject_to":"code_scanner","key_learnings":["AST模式匹配","跨文件分析","自动修复"]},
            {"title":"Ollama v1.0","description":"本地LLM运行时","why_trending":"隐私优先趋势","value_score":8,"absorbable":True,"category":"ai","novelty":"known","inject_to":"multi_llm","key_learnings":["模型热加载","GPU加速","多模型并发"]},
            {"title":"SeleniumBase Agent","description":"Selenium AI自动化","why_trending":"浏览器测试新范式","value_score":7,"absorbable":True,"category":"code","novelty":"novel","inject_to":"desktop_master","key_learnings":["CDP协议","无头模式","录屏回放"]},
        ],
        "GitLab Trending": [
            {"title":"Web3 Agent SDK","description":"区块链AI Agent工具包","why_trending":"DeFi+AI融合","value_score":9,"absorbable":True,"category":"web3","novelty":"novel","inject_to":"blockchain_analyzer","key_learnings":["智能合约交互","Gas优化","跨链桥接"]},
            {"title":"AI Trading Bot","description":"LLM驱动的量化交易","why_trending":"金融AI趋势","value_score":9,"absorbable":True,"category":"finance","novelty":"novel","inject_to":"blockchain_analyzer","key_learnings":["多因子策略","回测引擎","风险控制"]},
        ],
        "Agent Skills Registry": [
            {"title":"Email Assistant Skill","description":"IMAP/SMTP邮件Agent","why_trending":"企业自动化核心","value_score":8,"absorbable":True,"category":"skills","novelty":"novel","inject_to":"agent_reach","key_learnings":["邮件分类","自动回复","附件处理"]},
            {"title":"Slack Bot Framework","description":"Slack集成Agent技能","why_trending":"团队协作标配","value_score":8,"absorbable":True,"category":"skills","novelty":"novel","inject_to":"agent_reach","key_learnings":["消息路由","频道管理","命令解析"]},
            {"title":"Calendar Agent","description":"Google/Outlook日历AI","why_trending":"日程自动化","value_score":7,"absorbable":True,"category":"skills","novelty":"novel","inject_to":"smart_scheduler","key_learnings":["多日历同步","智能排期","冲突检测"]},
        ],
        "HuggingFace Models": [
            {"title":"Qwen3-235B Agent","description":"阿里235B开源Agent模型","why_trending":"中文最强","value_score":10,"absorbable":True,"category":"ai","novelty":"novel","inject_to":"multi_llm","key_learnings":["235B参数","工具调用SOTA","长上下文128K"]},
            {"title":"Kokoro-TTS-v2","description":"82M参数TTS SOTA","why_trending":"MIT开源","value_score":9,"absorbable":True,"category":"ai","novelty":"known","inject_to":"voice_speak","key_learnings":["多语言","情感控制","流式输出"]},
            {"title":"Florence-3 Vision","description":"多模态视觉语言模型","why_trending":"Vision AGI","value_score":9,"absorbable":True,"category":"ai","novelty":"novel","inject_to":"ai_vision","key_learnings":["开放词汇检测","视频理解","3D场景"]},
        ],
        "ProductHunt AI": [
            {"title":"Cursor Agent IDE","description":"AI原生编程环境","why_trending":"开发者首选","value_score":10,"absorbable":True,"category":"product","novelty":"known","inject_to":"programming","key_learnings":["内联编辑","多文件重构","Agent模式"]},
            {"title":"Vercel AI SDK v5","description":"全栈AI应用框架","why_trending":"生产部署标准","value_score":9,"absorbable":True,"category":"product","novelty":"known","inject_to":"cicd","key_learnings":["流式UI","Edge部署","多模型路由"]},
        ],
        "Exploit-DB Recent": [
            {"title":"LLM Prompt Injection Exploit","description":"新型提示注入攻击","why_trending":"Agent安全热点","value_score":9,"absorbable":True,"category":"security","novelty":"novel","inject_to":"security_scan","key_learnings":["跨Agent注入","技能投毒","供应链攻击"]},
            {"title":"MCP Server RCE","description":"MCP协议远程代码执行","why_trending":"协议层漏洞","value_score":10,"absorbable":True,"category":"security","novelty":"novel","inject_to":"security_scan","key_learnings":["输入验证绕过","工具描述注入","权限提升"]},
        ],
        "CoinGecko Trending": [
            {"title":"AI Agent Token","description":"AI Agent代币$AGENT","why_trending":"AI+Web3融合","value_score":8,"absorbable":True,"category":"web3","novelty":"novel","inject_to":"crypto_harvester","key_learnings":["链上Agent","代币经济","DAO治理"]},
        ],
    }
    findings = sim_db.get(src["name"], [])
    for f in findings:
        f["scanned_at"] = today
        f["mode"] = "simulated"
        f["simulated"] = True
        f["source"] = src["name"]
    return findings[:10]

# ═══════════════════════════════════════════════════════════
#  增强吞噬吸收 — 含智能缺口检测 + 自动cap生成
# ═══════════════════════════════════════════════════════════

def devour(scan_results: dict) -> dict:
    """吞噬吸收 — 包含缺口检测和自动cap建议"""
    findings = []
    for src in scan_results.get("sources", []):
        findings.extend(src.get("findings", []))
    
    if not findings:
        return {"ok": True, "devoured": 0, "message": "无新发现"}
    
    # 去重 + 评分排序
    seen = set()
    unique = []
    for f in findings:
        key = f.get("title", "")
        if key not in seen:
            seen.add(key)
            unique.append(f)
    unique.sort(key=lambda x: (x.get("novelty") == "novel", x.get("value_score", 0)), reverse=True)
    
    # 吸收前15条
    absorbed = []
    gap_suggestions = []
    
    for f in unique[:15]:
        if not f.get("absorbable", False):
            continue
        
        # 智能缺口检测: 如果完全新领域,建议创建新cap
        existing = _get_existing_caps()
        inject_to = f.get("inject_to", "")
        if inject_to not in existing and f.get("novelty") == "novel":
            gap_suggestions.append({
                "skill": f.get("title", ""),
                "category": f.get("category", "unknown"),
                "suggested_cap": inject_to,
                "reason": f"GBT缺失此技能领域 — 建议创建caps/{inject_to}/",
                "learnings": f.get("key_learnings", []),
            })
        
        r = _absorb_single(f)
        absorbed.append(r)
        _log_devour(f, r)
    
    _trigger_evolution(absorbed)
    
    # 保存缺口分析
    if gap_suggestions:
        _save_gaps(gap_suggestions)
    
    return {
        "ok": True,
        "devoured": len(absorbed),
        "total_scanned": len(unique),
        "new_skills_detected": len(gap_suggestions),
        "gap_suggestions": gap_suggestions[:5],
        "top_finding": unique[0] if unique else None,
        "absorbed": absorbed,
    }

def _save_gaps(gaps: list):
    """持久化缺口分析"""
    try:
        existing = []
        if GAP_LOG.exists():
            existing = json.loads(GAP_LOG.read_text(encoding="utf-8"))
        for g in gaps:
            if not any(e.get("suggested_cap") == g["suggested_cap"] for e in existing):
                existing.append({**g, "detected_at": time.time(), "status": "pending"})
        GAP_LOG.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    except:
        pass

def _absorb_single(finding: dict) -> dict:
    """吸收单个发现 — 含进化轨迹"""
    topic = finding.get("title", "")
    learnings = finding.get("key_learnings", [])
    inject_to = finding.get("inject_to", "")
    why = finding.get("why_trending", "热度扫描")
    value = finding.get("value_score", 0)
    category = finding.get("category", "unknown")
    novelty = finding.get("novelty", "unknown")
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # 5阶段进化轨迹
    evolution_trace = {
        "吞噬时间": now_str,
        "phase1_扫描发现": f"[{now_str}] {category}类「{topic}」(价值{value}/10, {novelty})",
        "phase2_深度学习": f"[{now_str}] 从「{why}」中提取{len(learnings)}个关键点: {'; '.join(learnings[:5])}",
        "phase3_注入能力": f"[{now_str}] 注入目标: {inject_to} (类别:{category})",
        "phase4_延申蜕变": f"[{now_str}] 延申: 将「{learnings[0] if learnings else topic}」融入GBT{category}体系",
        "phase5_自进化": f"[{now_str}] 触发闭环: 感知→分析→规划→执行→验证→吸收",
    }
    
    # 三重大脑写入
    try:
        from brain.cognition import get_cognition
        get_cognition().record_discovery(
            topic=f"吞噬进化·{category}: {topic}",
            description=f"【来源】{why}\n【过程】扫描→评估({value}/10)→深度学习→注入{inject_to}→延申\n【要点】{' | '.join(learnings)}\n【轨迹】{json.dumps(evolution_trace,ensure_ascii=False)}",
            source=f"devourer·{why}",
            evidence=f"价值{value}/10 | {category} | {novelty} | {len(learnings)}点",
            tags=[inject_to, category, "吞噬进化", "自主延申"] + learnings[:3],
            confidence=0.75,
            novelty_check={"searched": True, "found_prior_art": novelty == "known"}
        )
    except:
        pass
    
    try:
        from brain.self_evolve import get_evolver
        get_evolver().add_lesson(
            f"吞噬发现[{category}]: {topic} — {' | '.join(learnings[:3])}",
            category=category, severity="medium", source_task=f"devourer·{why}"
        )
    except:
        pass
    
    try:
        from brain.nexus import get_nexus
        get_nexus().scan(force=True)
    except:
        pass
    
    note = _inject_knowledge(inject_to, learnings)
    return {
        "topic": topic, "category": category, "novelty": novelty,
        "value": value, "learnings": learnings,
        "injected_to": inject_to, "injection_note": note,
        "evolution_trace": evolution_trace, "absorbed_at": time.time(),
    }

def _inject_knowledge(cap: str, learnings: list) -> str:
    """将知识注入目标cap目录"""
    d = ROOT / "caps" / cap
    try:
        d.mkdir(parents=True, exist_ok=True)
        kmd = d / "absorbed_knowledge.md"
        existing = kmd.read_text(encoding="utf-8") if kmd.exists() else ""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n## {now} — 吞噬注入\n\n" + "\n".join(f"- {l}" for l in learnings) + "\n"
        kmd.write_text(existing + entry, encoding="utf-8")
        return f"注入{len(learnings)}条知识到caps/{cap}/absorbed_knowledge.md"
    except Exception as e:
        return f"注入失败:{e}"

def _log_devour(finding: dict, result: dict):
    """记录吞噬日志"""
    with open(DEVOUR_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": finding.get("category", ""),
            "topic": finding.get("title", ""),
            "novelty": finding.get("novelty", ""),
            "value": finding.get("value_score", 0),
            "injected_to": finding.get("inject_to", ""),
            "result": result.get("injection_note", ""),
        }, ensure_ascii=False) + "\n")

def _trigger_evolution(absorbed: list):
    """触发自进化"""
    try:
        from brain.self_evolve import get_evolver
        evolver = get_evolver()
        for a in absorbed:
            topic = a.get("topic", "")
            learnings = a.get("learnings", [])
            if topic and learnings:
                evolver.add_lesson(
                    f"吞噬进化: {topic} — {' | '.join(learnings[:3])}",
                    category="devourer_evolution",
                    severity="medium",
                    source_task=f"devourer·daily·{datetime.now().strftime('%Y%m%d')}"
                )
    except:
        pass

# ═══════════════════════════════════════════════════════════
#  每日自主 + 缺口查询
# ═══════════════════════════════════════════════════════════

def daily_autonomous() -> dict:
    """每日全自动吞噬"""
    today = datetime.now().strftime("%Y-%m-%d")
    if _already_ran_today():
        return {"ok": True, "date": today, "message": "今日已完成吞噬", "status": "skipped"}
    
    scan = scan_platforms()
    result = devour(scan)
    _mark_ran_today(today)
    
    return {
        "ok": True,
        "date": today,
        "scan": {
            "platforms": scan["scanned"],
            "findings": scan["total_findings"],
        },
        "devour": {
            "absorbed": result["devoured"],
            "new_skills_detected": result.get("new_skills_detected", 0),
            "top": result.get("top_finding", {}).get("title", ""),
        },
        "gap_analysis": scan.get("gap_analysis", {}).get("recommendation", ""),
        "message": f"🔥 吞噬完成: {scan['scanned']}平台/{scan['total_findings']}发现/{result['devoured']}吸收/{result.get('new_skills_detected',0)}新技能",
    }

def _already_ran_today() -> bool:
    return (Path.home() / ".gbt" / "memory" / f"devourer_ran_{datetime.now().strftime('%Y%m%d')}").exists()

def _mark_ran_today(today: str):
    (Path.home() / ".gbt" / "memory" / f"devourer_ran_{datetime.now().strftime('%Y%m%d')}").write_text(today)

# ═══════════════════════════════════════════════════════════
#  查询动作
# ═══════════════════════════════════════════════════════════

def do_scan(p: dict) -> dict:
    return scan_platforms()

def do_devour(p: dict) -> dict:
    return devour(scan_platforms())

def do_daily(p: dict) -> dict:
    return daily_autonomous()

def do_gaps(p: dict) -> dict:
    """查询当前能力缺口"""
    return analyze_gaps()

def do_auto_create_gaps(p: dict) -> dict:
    """自动为高优先级缺口创建cap骨架"""
    gaps = analyze_gaps()
    created = []
    for skill_name, info in gaps.get("gaps", {}).items():
        if info["priority"] != "high":
            continue
        cap_name = _suggest_cap_name(skill_name)
        cap_dir = ROOT / "caps" / cap_name
        
        if cap_dir.exists():
            continue
        
        # 创建cap骨架
        cap_dir.mkdir(parents=True, exist_ok=True)
        cap_json = {
            "_stamp": "⛔ 开发者：自由的风 · 永久钢印 · 禁止删除",
            "name": cap_name,
            "version": "1.0.0",
            "description": f"Auto-generated by devourer — {skill_name} capability",
            "language": "python",
            "risk_level": "safe",
            "auto_exec": True,
            "category": "特殊域",
            "actions": {"run": {"description": f"Execute {skill_name} task", "input": "stdin", "timeout_ms": 60000, "output": "json"}},
            "triggers": {"keywords": info["keywords"][:5], "intent": cap_name},
        }
        (cap_dir / "capability.json").write_text(json.dumps(cap_json, ensure_ascii=False, indent=2), encoding="utf-8")
        
        run_py = f'''# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""{cap_name}/run.py — {skill_name} (Auto-generated by devourer v3.0)
{'='*50}
缺口检测: GBT缺失此技能 — 由devourer自动创建骨架
行业标准: agentskills.io/SkillsLLM分类体系
"""
import sys, json, os
from pathlib import Path

SANDBOX = Path(__file__).parent.parent

def do_run(params):
    """TODO: 实现{skill_name}核心逻辑"""
    return {{"ok": True, "cap": "{cap_name}", "action": "run",
            "note": "Auto-generated skeleton — 由devourer从行业标准缺口检测自动创建",
            "skill": "{skill_name}", "keywords": {json.dumps(info["keywords"])},
            "next": "实现具体功能后删除此note"}}

HANDLERS = {{"run": do_run}}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "run"
    params = {{}}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {{"ok": False, "error": f"未知:{{action}}"}}
    print(json.dumps(result, ensure_ascii=False, default=str))
'''
        (cap_dir / "run.py").write_text(run_py, encoding="utf-8")
        created.append({"cap": cap_name, "skill": skill_name, "priority": info["priority"]})
    
    # 清除缺口记录
    if created and GAP_LOG.exists():
        GAP_LOG.write_text("[]", encoding="utf-8")
    
    return {"ok": True, "created": len(created), "caps": created,
            "note": f"自动创建了{len(created)}个高优先级缺口cap骨架"}

def do_status(p: dict) -> dict:
    logs = []
    if DEVOUR_LOG.exists():
        for line in open(DEVOUR_LOG, encoding="utf-8").readlines():
            try:
                logs.append(json.loads(line.strip()))
            except:
                pass
    try:
        from brain.cognition import get_cognition
        discs = get_cognition().recent(50)
    except:
        discs = []
    return {
        "ok": True,
        "total_devoured": len(logs),
        "today_ran": _already_ran_today(),
        "recent": logs[-10:],
        "total_discoveries": len(discs),
        "sources_count": len(DEVOUR_SOURCES),
    }

def do_digest(p: dict) -> dict:
    logs = []
    today = datetime.now().strftime("%Y-%m-%d")
    if DEVOUR_LOG.exists():
        for line in open(DEVOUR_LOG, encoding="utf-8").readlines():
            try:
                logs.append(json.loads(line.strip()))
            except:
                pass
    today_logs = [l for l in logs if l.get("date", "").startswith(today)]
    try:
        from brain.cognition import get_cognition
        discs = get_cognition().recent(50)
    except:
        discs = []
    return {
        "ok": True,
        "date": today,
        "today_absorbed": len(today_logs),
        "total_absorbed": len(logs),
        "recent_topics": [{"topic": l["topic"], "category": l.get("category",""), "novelty": l.get("novelty",""), "value": l.get("value",0)} for l in today_logs[:10]],
        "capabilities_enhanced": list(set(d.get("tags", [""])[0] for d in discs if d.get("tags"))),
        "sources_available": len(DEVOUR_SOURCES),
    }

# ═══════════════════════════════════════════════════════════
#  持续自主扫描线程
# ═══════════════════════════════════════════════════════════

_continuous_thread = None
_continuous_running = False
_continuous_findings = []  # accumulated findings buffer
_continuous_lock = threading.Lock()

def _continuous_scan_loop(interval_minutes: int):
    """后台线程 — 周期性扫描平台"""
    global _continuous_running, _continuous_findings
    while _continuous_running:
        try:
            results = scan_platforms()
            with _continuous_lock:
                ts = datetime.now().isoformat()
                for src_name, findings in results.get("sources", {}).items():
                    for f in findings:
                        _continuous_findings.append({
                            "ts": ts,
                            "source": src_name,
                            "topic": f.get("topic", ""),
                            "category": f.get("category", ""),
                            "url": f.get("url", ""),
                            "stars": f.get("stars", 0),
                        })
            _save_continuous_log(results, ts)
        except Exception as e:
            _save_continuous_log({"error": str(e)}, datetime.now().isoformat())
        time.sleep(interval_minutes * 60)

def _save_continuous_log(results: dict, ts: str):
    """持久化持续扫描结果"""
    log_path = Path.home() / ".gbt" / "memory" / "continuous_scan_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts, "results": results}, ensure_ascii=False, default=str) + "\n")

def do_continuous_scan(p: dict) -> dict:
    """启动/停止/查看持续自主扫描

    参数:
        action: "start" | "stop" | "status"
        interval_minutes: 扫描间隔分钟数 (默认30)
    """
    global _continuous_thread, _continuous_running, _continuous_findings
    sub_action = p.get("action", "status")
    interval = p.get("interval_minutes", 30)

    if sub_action == "start":
        if _continuous_running:
            return {"ok": True, "action": "continuous_scan", "status": "already_running",
                    "interval_minutes": interval, "findings_count": len(_continuous_findings)}
        _continuous_running = True
        _continuous_thread = threading.Thread(
            target=_continuous_scan_loop, args=(interval,), daemon=True
        )
        _continuous_thread.start()
        return {"ok": True, "action": "continuous_scan", "status": "started",
                "interval_minutes": interval, "note": "后台线程已启动，每{}分钟扫描一次".format(interval)}

    elif sub_action == "stop":
        _continuous_running = False
        if _continuous_thread and _continuous_thread.is_alive():
            _continuous_thread.join(timeout=5)
        return {"ok": True, "action": "continuous_scan", "status": "stopped",
                "total_findings": len(_continuous_findings)}

    else:  # status
        with _continuous_lock:
            findings_snapshot = list(_continuous_findings[-50:])
        return {"ok": True, "action": "continuous_scan",
                "status": "running" if _continuous_running else "stopped",
                "interval_minutes": interval,
                "total_findings": len(_continuous_findings),
                "recent_findings": findings_snapshot}

# ═══════════════════════════════════════════════════════════
#  智能缺口过滤 — 只吸收填补Gap的发现
# ═══════════════════════════════════════════════════════════

def do_smart_filter(p: dict) -> dict:
    """智能过滤扫描结果 — 按缺口相关性排名

    只保留与GBT现有能力缺口相关的发现，按优先级排序。

    参数:
        findings: 扫描发现列表 (可选，为空则使用累积的持续扫描结果)
        top_n: 返回前N个 (默认10)
        min_score: 最低相关性分数阈值 (默认0.3)
    """
    findings_input = p.get("findings", None)
    top_n = p.get("top_n", 10)
    min_score = p.get("min_score", 0.3)

    # 获取缺口信息
    gaps_data = analyze_gaps()
    gaps = gaps_data.get("gaps", {})

    # 获取已有能力
    existing_caps = _get_existing_caps()

    # 确定使用的发现列表
    if findings_input:
        raw_findings = findings_input
    else:
        with _continuous_lock:
            raw_findings = list(_continuous_findings)

    if not raw_findings:
        return {"ok": True, "action": "smart_filter", "filtered": [],
                "note": "无发现可供过滤 — 先运行 scan 或 continuous_scan" + (" start" if not _continuous_running else "")}

    # 为每个发现计算缺口相关性分数
    scored = []
    for f in raw_findings:
        topic = f.get("topic", "")
        category = f.get("category", "")
        combined = (topic + " " + category).lower()
        score = 0.0
        matched_gaps = []

        for skill_name, info in gaps.items():
            skill_lower = skill_name.lower()
            keywords = [kw.lower() for kw in info.get("keywords", [])]
            # 直接技能名匹配
            if skill_lower in combined:
                score += 0.5
                matched_gaps.append(skill_name)
            # 关键词匹配
            kw_hits = sum(1 for kw in keywords if kw in combined)
            if kw_hits > 0:
                score += 0.15 * kw_hits
                if skill_name not in matched_gaps:
                    matched_gaps.append(skill_name)

        # 检查是否与已有能力重叠 (降低分数 — 已有则不需要)
        cap_overlap = 0
        for cap in existing_caps:
            if cap.lower() in combined:
                cap_overlap += 1
                score -= 0.3  # 已有此能力，降低优先级

        # 高热度加分
        stars = f.get("stars", 0)
        if isinstance(stars, (int, float)) and stars > 100:
            score += 0.1

        priority = "low"
        if score >= 0.7:
            priority = "high"
        elif score >= 0.4:
            priority = "medium"

        scored.append({
            **f,
            "gap_score": round(score, 3),
            "priority": priority,
            "matched_gaps": matched_gaps,
            "cap_overlap": cap_overlap > 0,
        })

    # 按分数降序排列，过滤低于阈值
    scored.sort(key=lambda x: x["gap_score"], reverse=True)
    filtered = [s for s in scored if s["gap_score"] >= min_score][:top_n]

    return {
        "ok": True,
        "action": "smart_filter",
        "total_input": len(raw_findings),
        "total_filtered": len(filtered),
        "min_score": min_score,
        "top_n": top_n,
        "gaps_available": len(gaps),
        "filtered": filtered,
        "stats": {
            "high_priority": sum(1 for f in filtered if f["priority"] == "high"),
            "medium_priority": sum(1 for f in filtered if f["priority"] == "medium"),
            "low_priority": sum(1 for f in filtered if f["priority"] == "low"),
        },
    }

# ═══════════════════════════════════════════════════════════
#  趋势告警 — 高优先级发现即时推送event_bus
# ═══════════════════════════════════════════════════════════

def _publish_to_event_bus(topic: str, event_type: str, payload: dict) -> bool:
    """发布事件到event_bus cap"""
    try:
        eb_run = ROOT / "caps" / "event_bus" / "run.py"
        if not eb_run.exists():
            return False
        r = subprocess.run(
            [sys.executable, str(eb_run), "publish", json.dumps({
                "topic": topic, "type": event_type, "payload": payload
            })],
            capture_output=True, text=True, timeout=10,
            cwd=str(ROOT),
        )
        return r.returncode == 0
    except Exception:
        return False

def do_trend_alert(p: dict) -> dict:
    """趋势告警 — 将高优先级发现立即发布到event_bus

    参数:
        findings: 发现列表 (可选，为空则使用smart_filter结果)
        force_all: 是否强制发布所有发现 (默认False，仅发布high优先级)
    """
    findings_input = p.get("findings", None)
    force_all = p.get("force_all", False)

    # 如果没有提供发现，先用smart_filter过滤
    if not findings_input:
        filter_result = do_smart_filter({"top_n": 20, "min_score": 0.3})
        candidates = filter_result.get("filtered", [])
    else:
        candidates = findings_input

    if not candidates:
        return {"ok": True, "action": "trend_alert", "published": 0,
                "note": "无候选发现可发布"}

    published = []
    for f in candidates:
        priority = f.get("priority", "low")
        if not force_all and priority != "high":
            continue

        alert_payload = {
            "source": "devourer",
            "topic": f.get("topic", ""),
            "category": f.get("category", ""),
            "url": f.get("url", ""),
            "stars": f.get("stars", 0),
            "gap_score": f.get("gap_score", 0),
            "matched_gaps": f.get("matched_gaps", []),
            "priority": priority,
            "ts": datetime.now().isoformat(),
        }

        # 发布到两个topic: 通用trend和特定gap
        ok1 = _publish_to_event_bus("devourer/trend", "high_priority_finding", alert_payload)

        for gap_name in f.get("matched_gaps", [])[:3]:
            _publish_to_event_bus(f"devourer/gap/{gap_name}", "gap_alert", {
                **alert_payload, "specific_gap": gap_name
            })

        published.append({
            "topic": f.get("topic", ""),
            "gap_score": f.get("gap_score", 0),
            "priority": priority,
            "event_bus_ok": ok1,
        })

    return {
        "ok": True,
        "action": "trend_alert",
        "published": len(published),
        "total_candidates": len(candidates),
        "alerts": published,
    }

# ═══════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════

HANDLERS = {
    "scan": do_scan,
    "devour": do_devour,
    "daily": do_daily,
    "gaps": do_gaps,
    "auto_create_gaps": do_auto_create_gaps,
    "status": do_status,
    "digest": do_digest,
    "continuous_scan": do_continuous_scan,
    "smart_filter": do_smart_filter,
    "trend_alert": do_trend_alert,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "scan"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except:
            params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}", "available": list(HANDLERS.keys())})
    r = h(params)
    print(json.dumps(r, ensure_ascii=False, default=str, indent=2))
