# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
collab_dispatch/run.py — 协作执行智能调度 · 铁律版
=====================================================
铁律:
  ① 每一步必须执行，不许跳过
  ② 失败 → 自动重试1次 → 仍失败 → 标记FAIL并继续
  ③ 每步执行前打印标题，执行后打印结果
  ④ 所有步骤执行完毕才进入汇总
  ⑤ cloud_llm 是唯一出口，必须最后一步执行

执行链:
  [指令] → Phase1:设计大脑分析 → Phase2:思维导图展示
         → Phase3:每步严格执行(无跳过) → Phase4:LLM汇总输出
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
import sys, json, os, subprocess, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

CAPS_DIR = os.path.join(os.path.dirname(__file__), '..')
SANDBOX  = os.path.join(os.path.dirname(__file__), '..', '..')

# ══════════════════════════════════════════════════════
# 底层工具
# ══════════════════════════════════════════════════════

def _call_cap(cap_name: str, action: str, params: dict, timeout: int = 30) -> dict:
    run_py = os.path.join(CAPS_DIR, cap_name, "run.py")
    if not os.path.exists(run_py):
        return {"ok": False, "error": f"能力文件不存在: {cap_name}/run.py"}
    try:
        r = subprocess.run(
            [sys.executable, run_py, action, json.dumps(params, ensure_ascii=False)],
            capture_output=True, text=True, timeout=timeout,
            cwd=SANDBOX, encoding="utf-8", errors="replace"
        )
        raw = (r.stdout or "").strip()
        if raw:
            try:    return json.loads(raw)
            except: return {"ok": True, "raw": raw[:600]}
        err = (r.stderr or "").strip()
        return {"ok": False, "error": err[:300] or "无输出"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"超时({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}

def _retry_call(cap: str, action: str, params: dict, timeout: int = 30) -> dict:
    """执行能力，失败自动重试一次"""
    result = _call_cap(cap, action, params, timeout)
    if not result.get("ok"):
        time.sleep(1)
        result = _call_cap(cap, action, params, timeout)
        result["_retried"] = True
    return result

# ── 能力默认动作表 ──────────────────────────────────────────
DEFAULT_ACTIONS = {
    "design_brain":        ("architect",   30),
    "programming":         ("code",        45),
    "code_exec":           ("run",         20),
    "deep_reasoner":       ("reason",      30),
    "mind_visual":         ("mindmap",     30),
    "gbt_brain":           ("think",       30),
    "cloud_brain":         ("ask",         45),
    "omni_eye":            ("see",         10),
    "screen_ocr":          ("read",        10),
    "auto_fix":            ("fix",         20),
    "git_ops":             ("status",      10),
    "codebase_memory":     ("search",      15),
    "sqli_tester":         ("test",        20),
    "xss_tester":          ("test",        20),
    "port_scanner":        ("scan",        20),
    "dir_buster":          ("bust",        20),
    "deep_scrape":         ("scrape",      30),
    "precision_scrape":    ("scrape",      20),
    "tg_client":           ("status",      10),
    "desktop_master":      ("status",      10),
    "sys_control":         ("list",        10),
    "self_diagnostic":     ("check",       15),
    "video_gen":           ("list",        10),
    "cloud_llm":           ("ask",         60),
    "agent_reach":         ("status",      10),
    "waf_bypass":          ("test",        20),
    "bounty_hunter":       ("hunt",        30),
    "docker":              ("status",      10),
    "auto_pipeline":       ("list",        10),
}

def _get_action(cap: str) -> tuple:
    return DEFAULT_ACTIONS.get(cap, ("run", 25))

# ══════════════════════════════════════════════════════
# 步骤执行器（铁律: 每步必须执行）
# ══════════════════════════════════════════════════════

class StrictExecutor:
    def __init__(self, instruction: str, verbose: bool = True):
        self.instruction = instruction
        self.verbose     = verbose
        self.log         = []
        self.step_log    = []   # 每步详细记录
        self.start_time  = time.time()

    def emit(self, msg: str):
        self.log.append(msg)
        if self.verbose:
            print(msg, flush=True)

    def run_step(self, step_no: int, name: str, cap: str, action: str,
                 params: dict, timeout: int = 30, mandatory: bool = True) -> dict:
        """
        执行单步。铁律: 无论结果如何都执行完，不跳过。
        mandatory=True: 失败后重试一次并记录
        """
        border = "═" * 58
        self.emit(f"\n{border}")
        self.emit(f"  Step {step_no:02d} │ {name}")
        self.emit(f"  能力  │ {cap}")
        self.emit(f"  动作  │ {cap}.{action}()")
        self.emit(f"  参数  │ {str(params)[:80]}")
        self.emit(f"{border}")
        self.emit(f"  ▶ 执行中...")

        t0     = time.time()
        result = _retry_call(cap, action, params, timeout)
        elapsed = round(time.time() - t0, 2)
        ok      = result.get("ok", False)
        retried = result.get("_retried", False)

        status = "✓ 成功" if ok else "✗ 失败"
        retry_note = " (已重试)" if retried else ""
        self.emit(f"  {status}{retry_note} │ 耗时 {elapsed}s")

        if ok:
            # 显示输出摘要
            if result.get("reply"):
                self.emit(f"  输出  │ {result['reply'][:100]}")
            elif result.get("raw"):
                self.emit(f"  输出  │ {result['raw'][:100]}")
            elif result.get("result"):
                self.emit(f"  输出  │ {str(result['result'])[:100]}")
            else:
                keys = [k for k in result if k not in ("ok","_retried")]
                self.emit(f"  输出  │ 字段: {keys[:5]}")
        else:
            err = result.get("error", "未知错误")
            self.emit(f"  错误  │ {err[:120]}")
            if mandatory:
                self.emit(f"  处理  │ 标记FAIL → 继续下一步（不中断流程）")

        record = {
            "step":    step_no,
            "name":    name,
            "cap":     cap,
            "action":  action,
            "ok":      ok,
            "elapsed": elapsed,
            "retried": retried,
            "result":  result,
        }
        self.step_log.append(record)
        return record

# ══════════════════════════════════════════════════════
# 主调度入口
# ══════════════════════════════════════════════════════

def do_run(params: dict) -> dict:
    """
    完整执行链 —— 每步必须执行，不许跳过。
    """
    instruction = params.get("instruction") or params.get("prompt", "")
    verbose     = params.get("verbose", True)
    if not instruction:
        return {"ok": False, "error": "缺少 instruction 参数"}

    ex = StrictExecutor(instruction, verbose)
    ex.emit(f"\n{'▶'*4} 协作调度启动 · 铁律模式 {'◀'*4}")
    ex.emit(f"指令: {instruction[:100]}")
    ex.emit(f"时间: {time.strftime('%H:%M:%S')}")

    step_no = 1

    # ══ Phase 1: 设计大脑分析（必须执行）══════════════════
    ex.emit(f"\n{'━'*58}")
    ex.emit(f"  Phase 1 │ 设计大脑分析")
    ex.emit(f"{'━'*58}")

    brain_rec = ex.run_step(
        step_no=step_no,
        name="设计大脑 · 意图识别 + 思维导图生成",
        cap="design_brain",
        action="analyze",
        params={"instruction": instruction},
        timeout=20,
    )
    step_no += 1

    brain_data = brain_rec["result"] if brain_rec["ok"] else {}
    plan       = brain_data.get("plan", {})
    domains    = brain_data.get("domains", ["AI推理"])
    design_mode = plan.get("design_mode", False)
    caps_ready  = plan.get("caps_ready", [])
    mindmap     = plan.get("mindmap", [])

    # ══ Phase 2: 思维导图展示（必须执行）═════════════════
    ex.emit(f"\n{'━'*58}")
    ex.emit(f"  Phase 2 │ 思维导图 · 执行计划展示")
    ex.emit(f"{'━'*58}")
    ex.emit(f"\n  指令: {instruction[:60]}")
    ex.emit(f"  识别域: {domains}")
    ex.emit(f"  设计模式: {'🎨是' if design_mode else '⚡否'}")
    ex.emit(f"  计划步数: {len(mindmap)}")
    ex.emit(f"  待执行能力: {caps_ready}")
    ex.emit(f"\n  [执行路径]")
    for s in mindmap:
        ex.emit(f"    [{s['step']:02d}] {s['name']} → {s.get('tool','?')}")

    # ══ Phase 3: 设计规范注入（设计任务必须执行）══════════
    design_context = ""
    if design_mode:
        ex.emit(f"\n{'━'*58}")
        ex.emit(f"  Phase 3 │ 设计规范注入（美感强制）")
        ex.emit(f"{'━'*58}")
        std_rec = ex.run_step(
            step_no=step_no,
            name="加载美感设计规范 · 深色玻璃拟态 + 霓虹渐变",
            cap="design_brain",
            action="standards",
            params={"category": "web"},
            timeout=10,
        )
        step_no += 1
        if std_rec["ok"]:
            std = std_rec["result"].get("standards", {})
            design_context = (
                f"\n\n【强制设计规范】\n"
                f"主题: {std.get('theme','')}\n"
                f"配色: {std.get('palette','')}\n"
                f"字体: {std.get('fonts','')}\n"
                f"动效: {std.get('animation','')}\n"
                f"布局: {std.get('layout','')}\n"
                f"必须包含: {std.get('must_have','')}\n"
                f"严禁使用: {std.get('forbidden','')}"
            )

    # ══ Phase 4: 逐步执行所有能力（每步必须执行）══════════
    ex.emit(f"\n{'━'*58}")
    ex.emit(f"  Phase 4 │ 逐步执行 · {len(caps_ready)} 个能力（全部必须执行）")
    ex.emit(f"{'━'*58}")

    # 如果 design_brain 没有给出 caps，用默认推断
    if not caps_ready:
        import re
        if re.search(r"网站|HTML|CSS|前端|UI|界面", instruction):
            caps_ready = ["programming", "code_exec"]
        elif re.search(r"渗透|漏洞|注入|扫描", instruction):
            caps_ready = ["port_scanner", "sqli_tester", "bounty_hunter"]
        elif re.search(r"感知|屏幕|截图|OCR", instruction):
            caps_ready = ["omni_eye", "screen_ocr"]
        else:
            caps_ready = ["deep_reasoner", "gbt_brain"]

    for cap in caps_ready:  # 所有cap全部执行，不截断
        action, timeout = _get_action(cap)
        cap_params = {
            "prompt":      instruction,
            "instruction": instruction,
            "query":       instruction,
        }
        if design_mode and design_context:
            cap_params["design_context"] = design_context

        ex.run_step(
            step_no=step_no,
            name=f"执行能力: {cap}",
            cap=cap,
            action=action,
            params=cap_params,
            timeout=timeout,
            mandatory=True,  # 必须执行
        )
        step_no += 1

    # ══ Phase 5: cloud_llm 汇总（唯一网关，必须最后执行）══
    ex.emit(f"\n{'━'*58}")
    ex.emit(f"  Phase 5 │ cloud_llm · 唯一网关 · 最终汇总输出")
    ex.emit(f"{'━'*58}")

    # 构建汇总 prompt
    ok_steps   = [s for s in ex.step_log if s["ok"]]
    fail_steps = [s for s in ex.step_log if not s["ok"]]

    summary_prompt = (
        f"用户原始指令:\n{instruction}\n\n"
        f"执行摘要:\n"
        f"  总步数: {len(ex.step_log)}  成功: {len(ok_steps)}  失败: {len(fail_steps)}\n\n"
        f"各步骤结果:\n"
        + "\n".join([
            f"  [{s['step']:02d}] {s['name']} [{s['cap']}] → "
            + ("✓成功" if s["ok"] else "✗失败: " + s["result"].get("error","?")[:40])
            for s in ex.step_log
        ])
        + (f"\n\n{design_context}" if design_context else "")
        + f"\n\n请根据以上执行结果，给出完整的最终回答，包括:\n"
        f"1. 任务完成情况\n2. 关键输出或结果\n3. 下一步建议\n"
        f"{'4. 设计决策说明（美感任务）' if design_mode else ''}"
    )

    ex.run_step(
        step_no=step_no,
        name="cloud_llm · DeepSeek · 生成最终回答",
        cap="cloud_llm",
        action="ask",
        params={
            "prompt":     summary_prompt,
            "max_tokens": 4096,
        },
        timeout=60,
        mandatory=True,
    )
    step_no += 1

    # ══ 执行报告 ══════════════════════════════════════════
    total_time = round(time.time() - ex.start_time, 2)
    ok_count   = sum(1 for s in ex.step_log if s["ok"])
    fail_count = len(ex.step_log) - ok_count

    ex.emit(f"\n{'▶'*4} 执行完毕 {'◀'*4}")
    ex.emit(f"  总步数: {len(ex.step_log)}  ✓{ok_count}  ✗{fail_count}  ⏱{total_time}s")
    ex.emit(f"  铁律: 所有步骤已强制执行，零跳过")

    final_llm = next((s["result"] for s in reversed(ex.step_log) if s["cap"] == "cloud_llm"), {})
    return {
        "ok":            True,
        "instruction":   instruction,
        "domains":       domains,
        "design_mode":   design_mode,
        "total_steps":   len(ex.step_log),
        "ok_steps":      ok_count,
        "fail_steps":    fail_count,
        "elapsed_s":     total_time,
        "final_reply":   final_llm.get("reply", ""),
        "step_log":      [{"step":s["step"],"name":s["name"],"cap":s["cap"],
                           "ok":s["ok"],"elapsed":s["elapsed"]} for s in ex.step_log],
    }

def do_preview(params: dict) -> dict:
    """预览执行计划（不执行，只生成思维导图）"""
    instruction = params.get("instruction") or params.get("prompt", "")
    if not instruction:
        return {"ok": False, "error": "缺少 instruction"}
    result = _call_cap("design_brain", "analyze", {"instruction": instruction}, 20)
    return result


# ══════════════════════════════════════════════════════
# 协作调度 · 并行/依赖/合并
# ══════════════════════════════════════════════════════

def do_coordinate_parallel(params: dict) -> dict:
    """并行执行 N 个独立任务，通过子进程并发运行，收集所有输出。

    params:
        tasks: [ {cap, action, params, timeout?}, ... ]  — 至少 3 个
        max_workers: int (默认 min(len(tasks), 8))
    """
    tasks = params.get("tasks", [])
    if not isinstance(tasks, list) or len(tasks) < 1:
        return {"ok": False, "error": "缺少 tasks 列表或为空"}

    max_workers = params.get("max_workers", min(len(tasks), 8))
    results = [None] * len(tasks)
    errors  = []

    def _run_one(idx: int, t: dict):
        cap     = t.get("cap", "")
        action  = t.get("action", "run")
        tparams = t.get("params", {})
        timeout = t.get("timeout", 30)
        if not cap:
            return idx, {"ok": False, "error": "task 缺少 cap"}
        r = _call_cap(cap, action, tparams, timeout)
        return idx, r

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_one, i, t): i for i, t in enumerate(tasks)}
        for fut in as_completed(futures):
            i, r = fut.result()
            results[i] = r
            if not r.get("ok"):
                errors.append({"index": i, "error": r.get("error", "?")})

    ok_count = sum(1 for r in results if r and r.get("ok"))
    return {
        "ok":          len(errors) == 0,
        "total":       len(tasks),
        "ok_count":    ok_count,
        "fail_count":  len(errors),
        "errors":      errors,
        "results":     results,
        "cap":         "collab_dispatch",
        "action":      "coordinate_parallel",
    }


def do_dependency_graph(params: dict) -> dict:
    """解析任务依赖关系，按拓扑顺序执行。

    params:
        tasks: [ {id, cap, action, params, depends_on: [id]?, timeout?}, ... ]
    """
    tasks = params.get("tasks", [])
    if not isinstance(tasks, list) or len(tasks) < 1:
        return {"ok": False, "error": "缺少 tasks 列表或为空"}

    # 建图
    task_map = {}
    in_degree = {}
    adj = {}
    for t in tasks:
        tid = t.get("id", "")
        if not tid:
            return {"ok": False, "error": "每个 task 必须包含 id"}
        task_map[tid] = t
        in_degree[tid] = 0
        adj[tid] = []

    for t in tasks:
        tid = t.get("id")
        for dep in t.get("depends_on", []):
            if dep not in task_map:
                return {"ok": False, "error": f"依赖 '{dep}' 不存在于 tasks 中 (来自 '{tid}')"}
            adj[dep].append(tid)
            in_degree[tid] += 1

    # 拓扑排序
    q = deque([tid for tid, deg in in_degree.items() if deg == 0])
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                q.append(v)

    if len(order) != len(tasks):
        return {"ok": False, "error": "存在循环依赖，无法解析拓扑顺序",
                "resolved": len(order), "total": len(tasks)}

    # 按序执行
    results = []
    timed_order = []
    for tid in order:
        t = task_map[tid]
        cap     = t.get("cap", "")
        action  = t.get("action", "run")
        tparams = t.get("params", {})
        timeout = t.get("timeout", 30)
        t0 = time.time()
        r = _call_cap(cap, action, tparams, timeout) if cap else {"ok": False, "error": "缺少 cap"}
        elapsed = round(time.time() - t0, 3)
        results.append(r)
        timed_order.append({"id": tid, "ok": r.get("ok"), "elapsed": elapsed,
                            "depends_on": t.get("depends_on", [])})

    ok_count = sum(1 for r in results if r.get("ok"))
    return {
        "ok":            ok_count == len(tasks),
        "total":         len(tasks),
        "ok_count":      ok_count,
        "execution_order": order,
        "timed_order":   timed_order,
        "results":       results,
        "cap":           "collab_dispatch",
        "action":        "dependency_graph",
    }


def do_merge_results(params: dict) -> dict:
    """合并多个并行任务输出为一个连贯结果。

    params:
        results:   [dict, ...]               — 各任务输出
        strategy:  "concat" | "pick_best" | "vote"  (默认 "concat")
        key:       str                       — strategy=pick_best/vote 时提取的字段
    """
    results  = params.get("results", [])
    strategy = params.get("strategy", "concat")
    key      = params.get("key", "")

    if not isinstance(results, list):
        return {"ok": False, "error": "results 必须是列表"}
    if not results:
        return {"ok": True, "merged": "", "count": 0, "cap": "collab_dispatch", "action": "merge_results"}

    merged = ""
    if strategy == "concat":
        parts = []
        for i, r in enumerate(results):
            if isinstance(r, dict):
                txt = r.get("reply") or r.get("result") or r.get("raw") or r.get("output") or json.dumps(r, ensure_ascii=False, default=str)
            else:
                txt = str(r)
            parts.append(f"[Task {i+1}]\n{txt}")
        merged = "\n\n".join(parts)

    elif strategy == "pick_best":
        if not key:
            return {"ok": False, "error": "pick_best 策略需要 key 参数"}
        best_val = None
        best_idx = -1
        for i, r in enumerate(results):
            val = r.get(key, 0) if isinstance(r, dict) else 0
            if best_val is None or val > best_val:
                best_val = val
                best_idx = i
        merged = json.dumps(results[best_idx], ensure_ascii=False, default=str) if best_idx >= 0 else ""

    elif strategy == "vote":
        if not key:
            return {"ok": False, "error": "vote 策略需要 key 参数"}
        from collections import Counter
        votes = Counter()
        for r in results:
            val = r.get(key) if isinstance(r, dict) else None
            if val is not None:
                votes[str(val)] += 1
        winner = votes.most_common(1)
        merged = winner[0][0] if winner else ""

    else:
        return {"ok": False, "error": f"未知合并策略: {strategy}"}

    return {
        "ok":       True,
        "merged":   merged,
        "strategy": strategy,
        "count":    len(results),
        "cap":      "collab_dispatch",
        "action":   "merge_results",
    }
handlers = {
    "run":                do_run,
    "preview":            do_preview,
    "coordinate_parallel": do_coordinate_parallel,
    "dependency_graph":   do_dependency_graph,
    "merge_results":      do_merge_results,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "run"
    raw    = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(raw)
    except Exception:
        params = {"instruction": raw}
    h = handlers.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, indent=2))
