# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
caps/auto_resolver/run.py — 自主解析引擎
==========================================
GBT的字典里没有"叫用户帮忙"这个词。

遇到任何卡点: 四脑分析 → 全网搜索 → 知识检索 → 多方案对比 → 镜像验证 → 继续执行

7步闭环:
  ① 四脑分析: 推理脑分析卡点根因 → 编程脑提出≥3种方案
  ② 全网搜索: web_search + GitHub + StackOverflow + 官方文档
  ③ 知识检索: lessons_db + rag_knowledge
  ④ 多方案对比: 至少3方案 → 可行性/复杂度/风险评估
  ⑤ 镜像验证: mirror_fusion中试验
  ⑥ 继续执行: 验证通过→回到原任务
  ⑦ 吸收教训: self_evolve.add_lesson → 永不再卡
"""
import sys, json, os, re, time, urllib.request, urllib.error
from datetime import datetime

API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("KIMI_API_KEY") or ""
BASE_URL = os.environ.get("GBT_LLM_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("GBT_LLM_MODEL", "deepseek-chat")


def _call_llm(system: str, user: str, temp: float = 0.3, max_tok: int = 3000) -> dict:
    if not API_KEY:
        return {"ok": False, "error": "未配置LLM API Key"}
    try:
        data = json.dumps({
            "model": MODEL, "max_tokens": max_tok, "temperature": temp,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        }).encode("utf-8")
        req = urllib.request.Request(f"{BASE_URL}/chat/completions", data=data,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=90).read())
        return {"ok": True, "content": resp["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  ① 四脑分析 — 推理脑 + 编程脑
# ═══════════════════════════════════════════════════════════

RESOLVE_STRATEGIES = [
    "搜索官方文档 — 找到权威解决方案",
    "搜索StackOverflow — 找到社区验证的答案",
    "搜索GitHub Issues — 找到同类问题的讨论",
    "阅读源码 — 从实现细节中找到答案",
    "最小复现 — 隔离问题，逐步缩小范围",
    "类比推理 — 从相似问题的解决方案中推导",
    "逆向推理 — 从期望结果反推需要的条件",
    "分而治之 — 将大问题分解为可解决的小问题",
    "替代方案 — 如果A方案走不通，B方案呢？",
    "回退重试 — 换一种完全不同的方法",
]


def analyze_blocker(blocker_description: str, context: dict | None = None,
                    previous_attempts: list | None = None) -> dict:
    """四脑分析卡点，生成多方案"""
    
    ctx_str = json.dumps(context, ensure_ascii=False) if context else ""
    attempts_str = "\n".join(f"- {a}" for a in (previous_attempts or []))
    
    if API_KEY:
        return _llm_analyze(blocker_description, ctx_str, attempts_str)
    return _rule_analyze(blocker_description, ctx_str, attempts_str)


def _llm_analyze(blocker: str, ctx: str, attempts: str) -> dict:
    system = """你是世界顶级问题解决专家。遇到任何技术卡点都能自主解决。

请分析以下卡点并生成解决方案。返回JSON:
{
  "root_cause": "根因分析(一句话)",
  "why_blocked": "为什么卡住了(2-3句深层分析)",
  "solutions": [
    {
      "id": "A",
      "approach": "方案名称",
      "steps": ["步骤1", "步骤2", "步骤3"],
      "pros": ["优点1", "优点2"],
      "cons": ["缺点1"],
      "complexity": "low/medium/high",
      "success_probability": 0.0-1.0,
      "search_queries": ["搜索词1", "搜索词2"]
    }
  ],
  "recommended": "推荐方案ID及理由",
  "fallback": "如果推荐方案失败，备选方案ID"
}

规则:
1. 至少3个方案
2. 每个方案必须有具体的搜索词
3. 必须评估成功概率
4. 绝不建议"问用户"或"手动操作"
5. 所有方案都是你(GBT)可以自主执行的"""
    
    user = f"""卡点描述: {blocker}
上下文: {ctx}
已尝试方案: {attempts if attempts else '无(首次尝试)'}

请分析并给出≥3个自主解决方案。"""
    
    result = _call_llm(system, user, temp=0.3, max_tok=2500)
    if result.get("ok"):
        try:
            content = result["content"].strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return {"ok": True, "analysis": json.loads(content), "mode": "llm"}
        except json.JSONDecodeError:
            pass
    
    return _rule_analyze(blocker, ctx, attempts)


def _rule_analyze(blocker: str, ctx: str, attempts: str) -> dict:
    """规则驱动: 自主分析卡点"""
    blocker_lower = blocker.lower()
    
    # 错误类型检测
    if any(kw in blocker_lower for kw in ["import", "modulenotfound", "no module"]):
        root = "缺少依赖/模块"
        solutions = [
            {"id": "A", "approach": "搜索并安装依赖",
             "steps": ["搜索缺失模块的PyPI包名", "pip install 安装", "验证import成功"],
             "search_queries": ["pip install <module_name>", "<module_name> pypi"],
             "complexity": "low", "success_probability": 0.9},
            {"id": "B", "approach": "检查虚拟环境和路径",
             "steps": ["确认Python环境路径", "检查sys.path", "检查是否在正确venv中"],
             "search_queries": ["python sys.path module not found", "virtualenv module not found"],
             "complexity": "low", "success_probability": 0.85},
            {"id": "C", "approach": "寻找替代库",
             "steps": ["搜索功能相似的替代库", "对比API差异", "替换import"],
             "search_queries": ["<module> alternative python", "<module> vs <alternative>"],
             "complexity": "medium", "success_probability": 0.7},
        ]
    elif any(kw in blocker_lower for kw in ["timeout", "超时", "timed out"]):
        root = "超时问题"
        solutions = [
            {"id": "A", "approach": "增加超时时间+重试机制",
             "steps": ["增加timeout参数", "添加指数退避重试", "添加进度日志"],
             "search_queries": ["python timeout retry exponential backoff", "requests timeout best practice"],
             "complexity": "low", "success_probability": 0.9},
            {"id": "B", "approach": "分批处理+并行化",
             "steps": ["将大任务拆分为小批次", "使用异步/并行处理", "限制并发数"],
             "search_queries": ["python async batch processing", "asyncio semaphore timeout"],
             "complexity": "medium", "success_probability": 0.85},
            {"id": "C", "approach": "缓存+增量处理",
             "steps": ["添加结果缓存", "增量处理(只处理新增/变更)", "断点续传"],
             "search_queries": ["python caching strategies", "incremental processing pattern"],
             "complexity": "medium", "success_probability": 0.8},
        ]
    elif any(kw in blocker_lower for kw in ["permission", "denied", "权限", "access"]):
        root = "权限问题"
        solutions = [
            {"id": "A", "approach": "检查并修改权限",
             "steps": ["检查当前用户和文件owner", "修改文件/目录权限", "以正确用户运行"],
             "search_queries": ["chmod permission denied fix", "file ownership change"],
             "complexity": "low", "success_probability": 0.9},
            {"id": "B", "approach": "更换工作目录",
             "steps": ["切换到用户有权限的目录", "修改所有路径引用", "重新运行"],
             "search_queries": ["change working directory python", "permission denied workaround"],
             "complexity": "low", "success_probability": 0.85},
            {"id": "C", "approach": "使用sudo/管理员模式",
             "steps": ["确认操作安全性", "以管理员权限运行", "执行后恢复普通权限"],
             "search_queries": ["sudo python script safely", "elevated privileges best practice"],
             "complexity": "low", "success_probability": 0.8},
        ]
    else:
        root = "通用卡点"
        solutions = [
            {"id": "A", "approach": "全网搜索+官方文档",
             "steps": ["提取关键错误信息", "web_search搜索", "阅读官方文档"],
             "search_queries": [f"{blocker[:80]} solution", f"{blocker[:80]} fix"],
             "complexity": "medium", "success_probability": 0.8},
            {"id": "B", "approach": "最小复现+逐步调试",
             "steps": ["创建最小复现代码", "逐步添加功能", "定位问题点"],
             "search_queries": ["minimal reproducible example", "debugging step by step"],
             "complexity": "medium", "success_probability": 0.75},
            {"id": "C", "approach": "换一种完全不同的方法",
             "steps": ["重新理解需求本质", "寻找替代技术方案", "从零重新实现"],
             "search_queries": [f"alternative to {blocker[:60]}", "different approach"],
             "complexity": "high", "success_probability": 0.6},
        ]
    
    for s in solutions:
        s.setdefault("pros", ["可自主执行", "有明确步骤"])
        s.setdefault("cons", ["需要验证"])
    
    return {
        "ok": True,
        "analysis": {
            "root_cause": root,
            "why_blocked": f"卡点类型: {root}。需要搜索+分析+验证后解决。",
            "solutions": solutions,
            "recommended": "A",
            "fallback": "B"
        },
        "mode": "rule_based"
    }


# ═══════════════════════════════════════════════════════════
#  ② 搜索建议生成器
# ═══════════════════════════════════════════════════════════

def generate_search_queries(blocker: str, solutions: list) -> list:
    """从方案中提取+增强搜索词"""
    queries = []
    for sol in solutions:
        queries.extend(sol.get("search_queries", []))
    
    # 添加通用搜索词
    queries.extend([
        f"{blocker[:80]} solution site:stackoverflow.com",
        f"{blocker[:80]} site:github.com",
        f"{blocker[:80]} documentation",
    ])
    
    return list(set(queries))[:8]  # 去重+限制


# ═══════════════════════════════════════════════════════════
#  动作处理
# ═══════════════════════════════════════════════════════════

def do_resolve(params: dict) -> dict:
    """核心: 完整自主解析流程"""
    blocker = params.get("blocker", params.get("description", params.get("error", "")))
    context = params.get("context", {})
    attempts = params.get("previous_attempts", [])
    
    # ① 四脑分析
    analysis = analyze_blocker(blocker, context, attempts)
    if not analysis.get("ok"):
        return analysis
    
    sol_data = analysis["analysis"]
    solutions = sol_data.get("solutions", [])
    
    # ② 生成搜索词
    queries = generate_search_queries(blocker, solutions)
    
    # ③ 选最优方案
    recommended = sol_data.get("recommended", "A")
    best = None
    for s in solutions:
        s["success_probability"] = s.get("success_probability", 0.5)
        if s["id"] == recommended:
            best = s
    if not best and solutions:
        solutions.sort(key=lambda x: -x.get("success_probability", 0))
        best = solutions[0]
    
    return {
        "ok": True,
        "action": "resolve",
        "blocker": blocker,
        "root_cause": sol_data.get("root_cause", ""),
        "why": sol_data.get("why_blocked", ""),
        "solutions_count": len(solutions),
        "best_solution": best,
        "all_solutions": solutions,
        "search_queries": queries,
        "next_action": f"执行方案{best['id']}: {best['approach']}",
        "do_not_ask_user": True,
        "mode": analysis.get("mode", "rule_based")
    }


def do_search(params: dict) -> dict:
    """生成搜索策略"""
    blocker = params.get("blocker", params.get("query", ""))
    solutions = params.get("solutions", [])
    
    queries = generate_search_queries(blocker, solutions)
    
    return {
        "ok": True,
        "action": "search",
        "queries": queries,
        "sources_priority": [
            "1. 官方文档 — 最权威",
            "2. StackOverflow — 社区验证",
            "3. GitHub Issues — 同类问题",
            "4. 源码 — 实现细节",
            "5. 博客/教程 — 实践经验"
        ],
        "instruction": "对每个搜索词执行web_search，汇总最相关的3-5个结果，提取可行方案"
    }


def do_analyze(params: dict) -> dict:
    """纯分析(不搜索)"""
    blocker = params.get("blocker", params.get("error", ""))
    return analyze_blocker(blocker)


def do_decide(params: dict) -> dict:
    """多方案决策"""
    solutions = params.get("solutions", [])
    if not solutions:
        return {"ok": False, "error": "无方案可供决策"}
    
    # 评分: 成功概率 × 简单度
    for s in solutions:
        prob = s.get("success_probability", 0.5)
        comp = {"low": 1.0, "medium": 0.7, "high": 0.4}.get(s.get("complexity", "medium"), 0.5)
        s["score"] = round(prob * comp, 2)
    
    solutions.sort(key=lambda x: -x.get("score", 0))
    best = solutions[0]
    
    return {
        "ok": True,
        "action": "decide",
        "best": best,
        "all_ranked": solutions[:5],
        "decision_rationale": f"选{best['id']}: 成功概率{best.get('success_probability',0)}×复杂度{best.get('complexity','?')}={best.get('score',0)}",
        "fallback": solutions[1]["id"] if len(solutions) > 1 else None
    }


def do_verify(params: dict) -> dict:
    """验证方案"""
    solution = params.get("solution", {})
    
    return {
        "ok": True,
        "action": "verify",
        "checks": [
            "在mirror_fusion沙盒中运行",
            "验证输出是否符合预期",
            "检查是否有副作用",
            "确认不影响其他模块"
        ],
        "solution": solution,
        "instruction": "在镜像空间创建最小复现→验证方案→确认可行→继续执行"
    }


def do_learn(params: dict) -> dict:
    """吸收教训"""
    blocker = params.get("blocker", "")
    solution = params.get("solution", "")
    
    lesson = f"卡点「{blocker[:100]}」→ 解决方案: {solution.get('approach', solution)[:100]}"
    category = params.get("category", "blocker_resolution")
    
    try:
        from brain.self_evolve import get_evolver
        evolver = get_evolver()
        evolver.add_lesson(lesson, category=category, severity="medium",
                          source_task=f"auto_resolver: {blocker[:50]}")
        return {"ok": True, "action": "learn", "lesson": lesson, "stored": True}
    except Exception:
        return {"ok": True, "action": "learn", "lesson": lesson, "stored": False,
                "note": "自进化模块未加载，教训未持久化"}


# ═══════════════════════════════════════════════════════════
#  resolve_loop — 持续监控 ~/.gbt/errors.log 并自主解决
# ═══════════════════════════════════════════════════════════

ERRORS_LOG = os.path.expanduser("~/.gbt/errors.log")
RESOLUTIONS_LOG = os.path.expanduser("~/.gbt/resolutions.log")
ESCALATION_LOG = os.path.expanduser("~/.gbt/escalations.log")
RESOLVE_PATTERNS_DIR = os.path.expanduser("~/.gbt/resolve_patterns")
MAX_ESCALATION_ATTEMPTS = 5


def _ensure_log_dirs():
    os.makedirs(RESOLVE_PATTERNS_DIR, exist_ok=True)
    for p in [ERRORS_LOG, RESOLUTIONS_LOG, ESCALATION_LOG]:
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write("")


def _read_errors_log(tail_lines: int = 50) -> list[dict]:
    """读取 ~/.gbt/errors.log 中的错误条目，返回 [{ts, error, source}] 列表"""
    _ensure_log_dirs()
    entries = []
    try:
        with open(ERRORS_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = [l.strip() for l in f.readlines()[-tail_lines:] if l.strip()]
    except FileNotFoundError:
        return entries
    # 按时间戳分组解析错误条目，格式: [2025-01-01T00:00:00] ERROR: msg | source: path
    current = {}
    for line in lines:
        if line.startswith("[") and "]" in line[:30]:
            if current:
                entries.append(current)
            ts_end = line.index("]") + 1
            current = {"ts": line[1:ts_end-1], "raw": line[ts_end:].strip()}
            # 尝试从 raw 中提取 source
            if "| source:" in current["raw"]:
                parts = current["raw"].split("| source:")
                current["error"] = parts[0].strip()
                current["source"] = parts[1].strip()
            else:
                current["error"] = current["raw"]
                current["source"] = ""
        elif current:
            current["raw"] = (current.get("raw", "") + "\n" + line).strip()
    if current:
        entries.append(current)
    return entries


def _write_to_errors_log(error: str, source: str = "") -> str:
    """向 ~/.gbt/errors.log 追加一条错误"""
    _ensure_log_dirs()
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"[{ts}] ERROR: {error}"
    if source:
        line += f" | source: {source}"
    with open(ERRORS_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return line


def _read_resolved_signatures() -> set:
    """读取已解决的错误签名（用于去重）"""
    sigs = set()
    try:
        with open(RESOLUTIONS_LOG, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if "| sig:" in line:
                    sigs.add(line.split("| sig:")[-1].strip())
    except FileNotFoundError:
        pass
    return sigs


def _error_signature(error: str) -> str:
    """为错误生成简短签名，用于去重和模式匹配"""
    # 提取关键模式：错误类型 + 核心消息前60字符
    error_type = "unknown"
    for kw in ["Error:", "Exception:", "error:", "Traceback", "SyntaxError",
                "ModuleNotFoundError", "ImportError", "KeyError", "TypeError",
                "ValueError", "FileNotFoundError", "PermissionError"]:
        idx = error.find(kw)
        if idx >= 0:
            error_type = kw.rstrip(":")
            break
    body = error.split("\n")[-1] if "\n" in error else error
    body = body.strip()[:60]
    # 去掉时间戳和可变部分
    import re as _re
    body = _re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '', body)
    body = _re.sub(r'0x[0-9a-fA-F]+', '', body)
    body = _re.sub(r'\d+ms', '', body)
    body = body.strip()
    return f"{error_type}:{body[:40]}"


def do_resolve_loop(params: dict) -> dict:
    """持续监控 ~/.gbt/errors.log 并自动处理新错误

    params:
        tail_lines: 读取最近N行 (默认50)
        poll_interval: 轮询间隔秒数 (默认5.0, 仅 watch 模式)
        max_rounds: 最大处理轮次 (默认10)
        watch: 是否进入持续轮询模式 (默认False)
        dry_run: 仅分析不执行 (默认False)
    """
    tail_lines = int(params.get("tail_lines", 50))
    poll_interval = float(params.get("poll_interval", 5.0))
    max_rounds = int(params.get("max_rounds", 10))
    watch = params.get("watch", False)
    dry_run = params.get("dry_run", False)

    _ensure_log_dirs()
    resolved_sigs = _read_resolved_signatures()
    all_resolved = []
    round_num = 0

    while round_num < max_rounds:
        round_num += 1
        entries = _read_errors_log(tail_lines=tail_lines)
        if not entries:
            if not watch:
                break
            time.sleep(poll_interval)
            continue

        round_resolved = []
        for entry in entries:
            err = entry.get("error", "")
            sig = _error_signature(err)
            if sig in resolved_sigs:
                continue  # 已解决过

            if dry_run:
                # 仅分析，不执行
                analysis = analyze_blocker(err)
                round_resolved.append({
                    "sig": sig, "dry_run": True,
                    "analysis": analysis.get("strategy", ""),
                    "solutions": [s.get("title", "") for s in analysis.get("solutions", [])],
                })
                resolved_sigs.add(sig)
                continue

            # 完整解析流程
            resolve_result = do_resolve({"blocker": err})
            attempts = resolve_result.get("attempts", [])
            success = resolve_result.get("ok", False)

            record = {
                "sig": sig, "error_preview": err[:200],
                "ok": success,
                "strategy": resolve_result.get("strategy", ""),
                "attempts_count": len(attempts),
            }

            if success:
                # 自动学习成功模式
                do_learn_from_resolution({"error": err, "resolution": resolve_result})
                record["learned"] = True

            round_resolved.append(record)
            resolved_sigs.add(sig)

            # 写入解决记录
            with open(RESOLUTIONS_LOG, "a", encoding="utf-8") as f:
                f.write(f"[{params.get('_now_iso', time.strftime('%Y-%m-%dT%H:%M:%S'))}] "
                        f"{'OK' if success else 'FAIL'} | sig: {sig}\n")

        all_resolved.extend(round_resolved)

        if not watch:
            break
        time.sleep(poll_interval)

    return {
        "ok": True,
        "rounds": round_num,
        "resolved_count": len(all_resolved),
        "resolved": all_resolved,
        "watch_mode": watch,
    }


def do_learn_from_resolution(params: dict) -> dict:
    """将成功解析的经验记录为可复用模式，存储到 ~/.gbt/resolve_patterns/

    params:
        error: 原始错误描述
        resolution: 成功的解析结果 dict
        pattern_name: 可选，自定义模式名
    """
    _ensure_log_dirs()
    error = params.get("error", "")
    resolution = params.get("resolution", {})
    pattern_name = params.get("pattern_name", "")

    if not error or not resolution:
        return {"ok": False, "error": "需要 error 和 resolution 参数"}

    sig = _error_signature(error)
    strategy = resolution.get("strategy", "")
    best_solution = ""
    if resolution.get("solutions"):
        best = resolution["solutions"][0] if isinstance(resolution["solutions"], list) else {"title": str(resolution["solutions"])}
        best_solution = best.get("title", str(best))

    pattern = {
        "signature": sig,
        "error_template": error[:500],
        "strategy": strategy,
        "best_solution": best_solution,
        "learned_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "use_count": 1,
        "tags": [],
    }

    if pattern_name:
        pattern["name"] = pattern_name
    else:
        pattern["name"] = re.sub(r'[^a-zA-Z0-9_-]', '_', sig)[:60]

    # 检查是否已存在模式 — 存在则更新计数
    pattern_path = os.path.join(RESOLVE_PATTERNS_DIR, f"{pattern['name']}.json")
    if os.path.exists(pattern_path):
        try:
            with open(pattern_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            existing["use_count"] = existing.get("use_count", 0) + 1
            existing["last_used_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            pattern = existing
        except Exception:
            pass

    with open(pattern_path, "w", encoding="utf-8") as f:
        json.dump(pattern, f, ensure_ascii=False, indent=2)

    # 追加到汇总学习日志
    with open(RESOLUTIONS_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{pattern['learned_at']}] LEARNED: {pattern['name']} | sig: {sig}\n")

    return {
        "ok": True,
        "pattern_name": pattern["name"],
        "pattern_path": pattern_path,
        "signature": sig,
    }


def do_escalation_policy(params: dict) -> dict:
    """升级策略：定义何时放弃并记录供人类审查

    params:
        error: 错误描述
        attempts: 当前已尝试次数 (默认0)
        max_attempts: 最大尝试次数 (默认 MAX_ESCALATION_ATTEMPTS=5)
        resolution_history: 解析历史列表 [{sig, ok, attempts}]

    返回:
        escalate: 是否应升级
        action: "continue" | "escalate" | "human_review"
        reason: 升级原因
    """
    _ensure_log_dirs()
    error = params.get("error", "")
    attempts = int(params.get("attempts", 0))
    max_attempts = int(params.get("max_attempts", MAX_ESCALATION_ATTEMPTS))
    resolution_history = params.get("resolution_history", [])

    # 决策矩阵
    result = {
        "action": "continue",
        "escalate": False,
        "reason": "",
        "attempts_remaining": max_attempts - attempts,
        "thresholds": {
            "max_attempts": max_attempts,
            "current_attempts": attempts,
        },
    }

    # 规则1: 超过最大尝试次数 → 升级
    if attempts >= max_attempts:
        result.update({"action": "escalate", "escalate": True,
                        "reason": f"已达到最大尝试次数 ({max_attempts})，放弃自动解析"})
    # 规则2: 同一错误签名已连续失败≥3次 → 升级
    elif resolution_history:
        sig = _error_signature(error)
        recent_fails = sum(
            1 for r in resolution_history[-5:]
            if r.get("sig") == sig and not r.get("ok", False)
        )
        if recent_fails >= 3:
            result.update({"action": "human_review", "escalate": True,
                            "reason": f"同一签名 {sig} 已连续失败 {recent_fails} 次，需人工审查"})
    # 规则3: 错误包含安全关键词 → 立即人工审查
    elif any(kw in error.lower() for kw in
              ["permission denied", "sudo", "root", "chmod", "chown", "passwd", "token leak"]):
        result.update({"action": "human_review", "escalate": True,
                        "reason": "错误涉及安全/权限操作，需人工审查"})
    # 规则4: 剩余尝试≤1 → 预升级警告
    elif max_attempts - attempts <= 1:
        result.update({"action": "continue", "escalate": False,
                        "reason": "剩余尝试次数不足，建议人工介入", "warning": True})

    # 记录升级事件
    if result["escalate"]:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(ESCALATION_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] ESCALATED ({result['action']}): {result['reason']} | "
                    f"error: {error[:200]}\n")

    return result




# ═══════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════

HANDLERS = {
    "resolve": do_resolve, "search": do_search, "analyze": do_analyze,
    "decide": do_decide, "verify": do_verify, "learn": do_learn,
    "resolve_loop": do_resolve_loop,
    "learn_from_resolution": do_learn_from_resolution,
    "escalation_policy": do_escalation_policy,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "resolve"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            params = {"blocker": sys.argv[2]}
    
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知: {action}"}
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
