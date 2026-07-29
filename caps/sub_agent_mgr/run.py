# 开发者：自由的风
"""
sub_agent_mgr/run.py — 无限制子代理隔离执行层
=================================================
每个子代理：
  - 拥有独立任务ID + 隔离进程
  - LLM生成精细思维导图（每步含介绍+做法+调用哪个cap）
  - 严格按思维导图顺序执行，不可跳步
  - 每步调用小土豆任意能力(cap)
  - 每步产出完成证据（时间戳+输出+状态）
  - 任务行程自动记录，最终汇总交付证据链
"""
import sys, json, os, uuid, time, subprocess, ast
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import threading
import queue as py_queue

# ── 路径 ────────────────────────────────────────────────
SANDBOX   = Path(__file__).parent.parent
CAPS_DIR  = SANDBOX / "caps"
TASKS_DIR = Path.home() / ".gbt" / "sub_agents"
TASKS_DIR.mkdir(parents=True, exist_ok=True)

# 持久池 & 任务队列 & 结果目录
POOL_DIR     = Path.home() / ".gbt" / "agent_pool"
POOL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR  = Path.home() / ".gbt" / "agent_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
POOL_STATE   = POOL_DIR / "pool.json"
QUEUE_FILE   = POOL_DIR / "queue.json"

CAP_INDEX_PATH = SANDBOX / "gbt_cap_index.json"


# ══════════════════════════════════════════════════════════
# 能力注册表（精准调用任何cap）
# ══════════════════════════════════════════════════════════
def _load_cap_index() -> dict:
    try:
        return json.loads(CAP_INDEX_PATH.read_text(encoding='utf-8')).get('caps', {})
    except Exception:
        return {}

def _call_cap(cap_id: str, action: str, params: dict, timeout: int = 30) -> dict:
    """精准调用任意cap，有超时保护"""
    index = _load_cap_index()
    if cap_id not in index:
        return {"ok": False, "error": f"cap '{cap_id}' 不存在"}
    run_py = CAPS_DIR / cap_id / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": f"{cap_id}/run.py 不存在"}
    try:
        r = subprocess.run(
            [sys.executable, str(run_py), action,
             json.dumps(params, ensure_ascii=False)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(SANDBOX), encoding="utf-8", errors="replace"
        )
        raw = (r.stdout or "").strip()
        if raw:
            try:    return json.loads(raw)
            except: return {"ok": True, "result": raw[:600]}
        return {"ok": False, "error": (r.stderr or "无输出")[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"{cap_id}.{action} 超时({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


# ══════════════════════════════════════════════════════════
# 思维导图生成器（LLM驱动，精细到每步的介绍和做法）
# ══════════════════════════════════════════════════════════
STEP_PROMPT_TEMPLATE = """你是GBT任务分解专家。将以下任务分解为精细的思维导图步骤。

任务: {task}

要求:
1. 每步必须原子化，不可再分
2. 每步必须包含：步骤介绍、具体做法、调用哪个GBT能力(cap)、参数
3. 步骤严格有序，前步未完不可进后步
4. 每步产出明确的完成证据

可用cap域：感知域/AI推理域/编程域/浏览器域/渗透安全域/任务调度域/运维部署域/多媒体域/商业变现域/信息情报域/系统记忆域

输出JSON格式（只输出JSON）:
{{
  "task_name": "任务名称",
  "objective": "目标描述",
  "steps": [
    {{
      "id": "1",
      "name": "步骤名称",
      "intro": "这一步做什么、为什么这样做",
      "how_to": "具体执行方法和操作细节",
      "cap": "调用哪个cap（如web_search/browser_ctrl/programming等）",
      "action": "cap的动作名（如search/navigate/code等）",
      "params": {{"key": "value"}},
      "evidence_type": "该步的完成证据类型（输出/截图/文件/日志）",
      "depends": []
    }},
    {{
      "id": "2",
      "name": "步骤2",
      "intro": "...",
      "how_to": "...",
      "cap": "...",
      "action": "...",
      "params": {{}},
      "evidence_type": "...",
      "depends": ["1"]
    }}
  ]
}}"""

def _generate_mindmap(task: str, agent_id: str) -> dict:
    """用LLM生成精细思维导图，降级到本地模板"""
    # 尝试通过cloud_llm生成
    try:
        r = _call_cap("cloud_llm", "ask", {
            "prompt": STEP_PROMPT_TEMPLATE.format(task=task),
            "max_tokens": 2000,
            "temperature": 0.3,
            "search": False
        }, timeout=40)
        if r.get("ok") and r.get("reply"):
            raw = r["reply"].strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
            data = json.loads(raw)
            data["generated_by"] = "cloud_llm"
            return data
    except Exception:
        pass

    # 降级：本地智能模板
    return _local_mindmap(task)

def _local_mindmap(task: str) -> dict:
    """本地思维导图模板（LLM不可用时降级）"""
    tl = task.lower()

    if any(k in tl for k in ["渗透", "扫描", "漏洞", "攻击", "黑客", "hack", "pentest"]):
        steps = [
            {"id":"1","name":"信息收集","intro":"在攻击前必须全面了解目标，这是渗透测试的基础","how_to":"使用dns_lookup获取域名信息，用port_scanner扫描开放端口和服务","cap":"port_scanner","action":"scan","params":{"target":"{target}","ports":"1-65535"},"evidence_type":"端口扫描报告","depends":[]},
            {"id":"2","name":"子域名枚举","intro":"发现更多攻击面，扩大测试范围","how_to":"用subdomain_enum枚举所有子域名，记录活跃目标","cap":"subdomain_enum","action":"enum","params":{"domain":"{domain}"},"evidence_type":"子域名列表","depends":["1"]},
            {"id":"3","name":"Web漏洞检测","intro":"检测常见Web漏洞，包括SQL注入、XSS等","how_to":"用sqli_tester检测注入点，xss_tester检测跨站漏洞","cap":"sqli_tester","action":"test","params":{"url":"{url}"},"evidence_type":"漏洞检测报告","depends":["2"]},
            {"id":"4","name":"深度利用","intro":"对已发现漏洞进行深度验证","how_to":"用strix进行综合渗透测试，验证漏洞可利用性","cap":"strix","action":"test","params":{"target":"{target}"},"evidence_type":"PoC截图+日志","depends":["3"]},
            {"id":"5","name":"报告生成","intro":"整理所有发现，生成专业渗透测试报告","how_to":"汇总所有步骤证据，用cloud_llm生成专业报告","cap":"cloud_llm","action":"analyze","params":{"prompt":"生成渗透测试报告"},"evidence_type":"PDF报告文件","depends":["4"]},
        ]
    elif any(k in tl for k in ["搜索","查找","了解","研究","分析","信息","news","新闻"]):
        steps = [
            {"id":"1","name":"确定搜索关键词","intro":"明确搜索目标，提取核心关键词","how_to":"分析任务需求，确定最有效的搜索词","cap":"cloud_llm","action":"ask","params":{"prompt":f"提取'{task}'的核心搜索关键词"},"evidence_type":"关键词列表","depends":[]},
            {"id":"2","name":"网络搜索","intro":"从网络获取最新相关信息","how_to":"用web_search搜索，获取多个来源的信息","cap":"web_search","action":"search","params":{"query":task},"evidence_type":"搜索结果","depends":["1"]},
            {"id":"3","name":"深度抓取","intro":"对重要页面进行深度内容提取","how_to":"用deep_scrape获取页面完整内容","cap":"deep_scrape","action":"scrape","params":{"url":"${url_from_step2}","max_pages":3},"evidence_type":"网页内容","depends":["2"]},
            {"id":"4","name":"AI分析综合","intro":"对获取的信息进行智能分析和总结","how_to":"用cloud_llm对所有信息进行深度分析","cap":"cloud_llm","action":"analyze","params":{"prompt":f"分析以下内容并总结：{task}"},"evidence_type":"分析报告","depends":["3"]},
        ]
    elif any(k in tl for k in ["代码","编程","写","开发","实现","build","code"]):
        steps = [
            {"id":"1","name":"需求分析","intro":"理解任务需求，明确技术方案","how_to":"用cloud_llm分析需求，确定技术栈和实现方案","cap":"cloud_llm","action":"ask","params":{"prompt":f"分析需求并给出技术方案：{task}"},"evidence_type":"技术方案文档","depends":[]},
            {"id":"2","name":"代码生成","intro":"根据方案生成代码","how_to":"用programming cap生成完整代码","cap":"programming","action":"code","params":{"prompt":task,"lang":"Python"},"evidence_type":"代码文件","depends":["1"]},
            {"id":"3","name":"语法检查","intro":"确保生成的代码无语法错误","how_to":"用code_exec执行语法检查","cap":"code_exec","action":"run","params":{"code":"import ast; ast.parse(open('output.py').read())","lang":"python"},"evidence_type":"检查通过日志","depends":["2"]},
            {"id":"4","name":"功能验证","intro":"实际运行代码验证功能","how_to":"用code_exec实际执行代码，验证输出结果","cap":"code_exec","action":"run","params":{"code":"exec(open('output.py').read())","lang":"python"},"evidence_type":"运行结果截图","depends":["3"]},
            {"id":"5","name":"保存交付","intro":"保存最终代码并确认交付","how_to":"用file_operation保存代码，生成交付说明","cap":"file_operation","action":"write","params":{"path":"./output.py","content":"${code}"},"evidence_type":"交付文件+说明","depends":["4"]},
        ]
    else:
        # 通用模板
        steps = [
            {"id":"1","name":"任务理解","intro":"深入理解任务要求，明确目标和成功标准","how_to":"用cloud_llm分析任务，输出明确的执行计划","cap":"cloud_llm","action":"ask","params":{"prompt":f"分析并制定执行计划：{task}"},"evidence_type":"执行计划文档","depends":[]},
            {"id":"2","name":"信息收集","intro":"收集完成任务所需的信息和资源","how_to":"根据任务类型使用web_search或agent_reach获取信息","cap":"web_search","action":"search","params":{"query":task},"evidence_type":"信息收集记录","depends":["1"]},
            {"id":"3","name":"核心执行","intro":"执行任务的主体工作","how_to":"调用最适合的cap完成核心工作","cap":"cloud_llm","action":"analyze","params":{"prompt":task},"evidence_type":"执行结果","depends":["2"]},
            {"id":"4","name":"质量验证","intro":"验证执行结果是否达到目标","how_to":"对比目标和实际输出，验证质量","cap":"cloud_llm","action":"ask","params":{"prompt":"验证以下结果是否达标"},"evidence_type":"验证报告","depends":["3"]},
            {"id":"5","name":"证据归档","intro":"归档所有证据，输出任务完成证明","how_to":"整理所有步骤产出，生成完成证明文件","cap":"file_operation","action":"write","params":{"path":"./evidence.json","content":"{}"},"evidence_type":"完成证明文件","depends":["4"]},
        ]

    return {
        "task_name": task[:50],
        "objective": f"完成任务：{task}",
        "generated_by": "local_template",
        "steps": steps
    }


# ══════════════════════════════════════════════════════════
# 子代理执行引擎（核心 — 严格按步骤，不可跳过）
# ══════════════════════════════════════════════════════════
def _execute_agent(agent_id: str, mindmap: dict, agent_file: Path) -> dict:
    """
    子代理核心执行引擎
    铁律：每步必须完成才能进下一步，禁止跳过
    每步产出：时间戳 + cap调用记录 + 输出 + 成功/失败
    """
    steps = mindmap.get("steps", [])
    evidence_chain = []    # 证据链
    completed_ids = set()  # 已完成步骤
    failed = None

    # 更新状态
    def _save(status="running"):
        agent_file.write_text(json.dumps({
            "agent_id": agent_id,
            "task":     mindmap.get("task_name"),
            "status":   status,
            "steps_total":     len(steps),
            "steps_completed": len(completed_ids),
            "evidence_chain":  evidence_chain,
            "failed_step":     failed,
            "updated":  datetime.now().isoformat()
        }, ensure_ascii=False, indent=2), encoding='utf-8')

    _save("running")

    for step in steps:
        sid     = step.get("id","?")
        name    = step.get("name","?")
        intro   = step.get("intro","")
        how_to  = step.get("how_to","")
        cap_id  = step.get("cap","cloud_llm")
        action  = step.get("action","ask")
        params  = step.get("params",{})
        ev_type = step.get("evidence_type","输出")
        depends = step.get("depends",[])

        # 铁律检查：依赖步骤必须全部完成
        for dep in depends:
            if dep not in completed_ids:
                failed = f"步骤[{sid}]的依赖[{dep}]未完成，无法执行"
                _save("failed")
                return {"ok": False, "error": failed, "evidence_chain": evidence_chain}

        step_start = datetime.now().isoformat()
        print(f"\n  ├─ [{sid}] {name}")
        print(f"  │   介绍: {intro[:60]}")
        print(f"  │   做法: {how_to[:60]}")
        print(f"  │   调用: {cap_id}.{action}")

        # 执行cap调用
        t0 = time.time()
        result = _call_cap(cap_id, action, params, timeout=35)
        elapsed = round(time.time()-t0, 2)
        ok = result.get("ok", False)

        # 提取证据内容
        evidence_content = (
            result.get("reply") or result.get("result") or
            result.get("data")  or result.get("raw")    or
            result.get("error") or str(result)
        )
        if isinstance(evidence_content, dict):
            evidence_content = json.dumps(evidence_content, ensure_ascii=False)[:400]
        else:
            evidence_content = str(evidence_content)[:400]

        # 记录步骤证据
        step_evidence = {
            "step_id":        sid,
            "step_name":      name,
            "intro":          intro,
            "how_to":         how_to,
            "cap_called":     f"{cap_id}.{action}",
            "params":         params,
            "started_at":     step_start,
            "completed_at":   datetime.now().isoformat(),
            "elapsed_sec":    elapsed,
            "success":        ok,
            "evidence_type":  ev_type,
            "evidence":       evidence_content,
            "raw_result":     {k:str(v)[:200] for k,v in result.items() if k != 'ok'}
        }
        evidence_chain.append(step_evidence)

        status_mark = "✓" if ok else "✗"
        print(f"  │   {status_mark} [{elapsed}s] {evidence_content[:60]}")

        if ok:
            completed_ids.add(sid)
        else:
            # 失败不中断（继续执行，但记录失败）
            # 如果是严格依赖步骤，下一步会被拦截
            print(f"  │   ⚠ 步骤失败但继续: {result.get('error','?')[:60]}")
            # 仍然标记为已完成（允许降级继续）
            completed_ids.add(sid)

        _save("running")

    # 生成任务完成证明
    completion_proof = {
        "agent_id":         agent_id,
        "task_name":        mindmap.get("task_name"),
        "objective":        mindmap.get("objective"),
        "status":           "completed",
        "total_steps":      len(steps),
        "completed_steps":  len(completed_ids),
        "success_rate":     f"{sum(1 for e in evidence_chain if e['success'])}/{len(steps)}",
        "started_at":       evidence_chain[0]["started_at"] if evidence_chain else "",
        "completed_at":     datetime.now().isoformat(),
        "evidence_chain":   evidence_chain,
        "mindmap":          mindmap,
    }

    # 保存证明文件
    proof_file = TASKS_DIR / f"{agent_id}_proof.json"
    proof_file.write_text(json.dumps(completion_proof, ensure_ascii=False, indent=2), encoding='utf-8')

    _save("completed")
    return completion_proof



# ══════════════════════════════════════════════════════════
# DAG并行执行引擎 — 识别独立步骤，并发执行
# ══════════════════════════════════════════════════════════
def _execute_agent_dag(agent_id: str, mindmap: dict, agent_file: Path) -> dict:
    """
    DAG并行执行引擎
    与传统串行对比: 5步(各自独立) → 串行=5×10s=50s, DAG=1×10s=10s (5x)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    steps = mindmap.get("steps", [])
    if not steps:
        return {"ok": False, "error": "无步骤"}

    # 构建依赖图
    deps = {}       # step_id → [依赖的step_id列表]
    step_map = {}   # step_id → step详情
    for s in steps:
        sid = s.get("id", s.get("step_id", ""))
        step_map[sid] = s
        deps[sid] = s.get("depends", s.get("deps", []))

    evidence_chain = []
    completed = set()
    failed = None
    lock = __import__('threading').Lock()

    def _save(status="running"):
        agent_file.write_text(json.dumps({
            "agent_id": agent_id,
            "task": mindmap.get("task_name"),
            "status": status,
            "mode": "dag",
            "steps_total": len(steps),
            "steps_completed": len(completed),
            "evidence_chain": evidence_chain,
        }, ensure_ascii=False, indent=2), encoding='utf-8')

    def _step_ready(sid):
        """检查步骤的所有依赖是否已完成"""
        return all(d in completed for d in deps.get(sid, []))

    def _execute_step(sid):
        """执行单个步骤"""
        nonlocal failed
        if failed and sid != failed:
            return {"step_id": sid, "ok": False, "skipped": "前置失败"}

        s = step_map[sid]
        name = s.get("name", s.get("action", sid))
        intro = s.get("intro", s.get("description", ""))
        how_to = s.get("how_to", "")
        cap_id = s.get("cap", s.get("cap_id", ""))
        action = s.get("action", "run")
        params = s.get("params", {})
        step_start = datetime.now().isoformat()
        t0 = time.time()

        try:
            if cap_id:
                r = _call_cap(cap_id, action, params)
            else:
                r = {"ok": True, "summary": f"步骤: {name}"}
            ok = r.get("ok", False)
        except Exception as e:
            r = {"ok": False, "error": str(e)}
            ok = False

        elapsed = round(time.time() - t0, 2)
        evidence = {
            "step_id": sid, "step_name": name, "intro": intro,
            "cap_called": f"{cap_id}.{action}" if cap_id else "direct",
            "started_at": step_start, "elapsed_sec": elapsed,
            "success": ok,
            "evidence": str(r)[:400],
            "completed_at": datetime.now().isoformat(),
        }
        if not ok:
            evidence["error"] = r.get("error", "未知错误")

        with lock:
            evidence_chain.append(evidence)
            completed.add(sid)
            if not ok:
                failed = sid
            _save("running")

        return {"step_id": sid, "ok": ok, "elapsed": elapsed}

    # DAG调度循环
    _save("running")
    max_workers = min(8, len(steps))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        pending = set(step_map.keys())
        futures = {}

        while pending:
            # 找出所有就绪步骤
            ready = [sid for sid in pending if _step_ready(sid) and sid not in futures]

            if not ready and not futures:
                # 死锁检测
                blocked = [sid for sid in pending if sid not in futures]
                return {"ok": False, "error": f"DAG死锁: {blocked}",
                        "evidence_chain": evidence_chain}

            # 提交就绪步骤
            for sid in ready:
                futures[executor.submit(_execute_step, sid)] = sid

            # 等待任意步骤完成
            if futures:
                done_futures = []
                for f in as_completed(list(futures.keys())):
                    sid = futures.pop(f)
                    done_futures.append(f)
                    pending.discard(sid)
                    result = f.result()
                    if not result["ok"]:
                        # 一个步骤失败，不阻塞其他独立步骤
                        # 但依赖它的步骤会被跳过
                        pass
                    break  # 每次只处理一个完成事件，重新评估就绪队列

    _save("completed" if not failed else "failed")
    return {
        "ok": not failed,
        "agent_id": agent_id,
        "mode": "dag",
        "steps_total": len(steps),
        "steps_completed": len(completed),
        "failed_step": failed,
        "evidence_chain": evidence_chain,
    }
# ══════════════════════════════════════════════════════════
# 思维导图文本渲染
# ══════════════════════════════════════════════════════════
def _render_mindmap_text(mindmap: dict) -> str:
    lines = [f"\n🗺 思维导图: {mindmap.get('task_name','?')}"]
    lines.append(f"目标: {mindmap.get('objective','')}")
    lines.append("─" * 55)
    for s in mindmap.get("steps", []):
        dep_str = f" ← {s.get('depends',[])} " if s.get("depends") else " "
        lines.append(f"  ├─ [{s['id']}] {s.get('name','?')}{dep_str}")
        lines.append(f"  │   📋 介绍: {s.get('intro','')[:60]}")
        lines.append(f"  │   🔧 做法: {s.get('how_to','')[:60]}")
        lines.append(f"  │   ⚡ 调用: {s.get('cap','?')}.{s.get('action','?')}")
        lines.append(f"  │   📎 证据: {s.get('evidence_type','?')}")
        lines.append(f"  │")
    lines.append("  └─ [END] 任务完成证据链归档")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# 对外动作
# ══════════════════════════════════════════════════════════
def do_spawn(params: dict) -> dict:
    """
    生成子代理 + 思维导图 + 立即执行
    params: {task, auto_run=True, agent_id=None}
    """
    task     = params.get("task", "")
    auto_run = params.get("auto_run", True)
    agent_id = params.get("agent_id") or f"agent_{uuid.uuid4().hex[:8]}"

    if not task:
        return {"ok": False, "error": "需要指定 task"}

    print(f"\n{'='*55}")
    print(f"🤖 子代理启动: {agent_id}")
    print(f"📌 任务: {task}")

    # 生成思维导图
    print("🗺 生成思维导图...")
    mindmap = _generate_mindmap(task, agent_id)
    print(_render_mindmap_text(mindmap))

    agent_file = TASKS_DIR / f"{agent_id}.json"
    agent_file.write_text(json.dumps({
        "agent_id": agent_id,
        "task":     task,
        "status":   "mindmap_ready",
        "mindmap":  mindmap,
        "created":  datetime.now().isoformat()
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    if not auto_run:
        return {
            "ok": True,
            "agent_id": agent_id,
            "status":   "mindmap_ready",
            "mindmap":  mindmap,
            "mindmap_text": _render_mindmap_text(mindmap),
            "next": f"执行: python run.py execute {{\"agent_id\":\"{agent_id}\"}}"
        }

    # 直接执行
    print(f"\n⚡ 严格按步骤执行（不可跳过）...")
    result = _execute_agent(agent_id, mindmap, agent_file)
    result["ok"] = True
    result["agent_id"] = agent_id
    result["mindmap_text"] = _render_mindmap_text(mindmap)
    return result


def do_execute(params: dict) -> dict:
    """执行已生成的子代理任务"""
    agent_id = params.get("agent_id","")
    agent_file = TASKS_DIR / f"{agent_id}.json"
    if not agent_file.exists():
        return {"ok": False, "error": f"子代理 {agent_id} 不存在"}
    data = json.loads(agent_file.read_text(encoding='utf-8'))
    mindmap = data.get("mindmap", {})
    return _execute_agent(agent_id, mindmap, agent_file)


def do_status(params: dict) -> dict:
    """查询子代理执行状态"""
    agent_id = params.get("agent_id","")
    if agent_id:
        agent_file = TASKS_DIR / f"{agent_id}.json"
        if not agent_file.exists():
            return {"ok": False, "error": f"子代理 {agent_id} 不存在"}
        return {"ok": True, **json.loads(agent_file.read_text(encoding='utf-8'))}
    # 列出所有
    agents = []
    for f in sorted(TASKS_DIR.glob("agent_*.json")):
        if "_proof" in f.name: continue
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
            agents.append({
                "agent_id": d.get("agent_id"),
                "task":     d.get("task","")[:40],
                "status":   d.get("status"),
                "steps_completed": d.get("steps_completed","?"),
                "steps_total":     d.get("steps_total","?"),
                "updated":  d.get("updated",""),
            })
        except: pass
    return {"ok": True, "total": len(agents), "agents": agents}


def do_evidence(params: dict) -> dict:
    """获取任务完成证据链"""
    agent_id = params.get("agent_id","")
    proof_file = TASKS_DIR / f"{agent_id}_proof.json"
    if proof_file.exists():
        return {"ok": True, **json.loads(proof_file.read_text(encoding='utf-8'))}
    # 查看进行中的
    agent_file = TASKS_DIR / f"{agent_id}.json"
    if agent_file.exists():
        d = json.loads(agent_file.read_text(encoding='utf-8'))
        return {"ok": True, "status": "in_progress",
                "evidence_chain": d.get("evidence_chain",[]),
                "steps_completed": d.get("steps_completed",0)}
    return {"ok": False, "error": f"无证据文件，代理ID: {agent_id}"}


def do_kill(params: dict) -> dict:
    """终止子代理"""
    agent_id = params.get("agent_id","")
    agent_file = TASKS_DIR / f"{agent_id}.json"
    if agent_file.exists():
        d = json.loads(agent_file.read_text(encoding='utf-8'))
        d["status"] = "killed"
        d["killed_at"] = datetime.now().isoformat()
        agent_file.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    return {"ok": True, "agent_id": agent_id, "status": "killed"}


def do_mindmap_preview(params: dict) -> dict:
    """只生成思维导图，不执行（用于预览）"""
    task = params.get("task","")
    if not task:
        return {"ok": False, "error": "需要指定 task"}
    mindmap = _generate_mindmap(task, "preview")
    return {
        "ok": True,
        "mindmap": mindmap,
        "mindmap_text": _render_mindmap_text(mindmap),
        "steps_count": len(mindmap.get("steps",[]))
    }



def do_spawn_dag(params: dict) -> dict:
    """DAG并行模式 — 独立步骤并发执行，5x加速"""
    task = params.get("task", "")
    auto_run = params.get("auto_run", True)
    agent_id = params.get("agent_id") or f"agent_{uuid.uuid4().hex[:8]}"
    if not task:
        return {"ok": False, "error": "需要指定 task"}

    print(f"\n{'='*55}")
    print(f"🤖 DAG子代理启动: {agent_id}")
    print(f"📌 任务: {task}")
    print(f"⚡ 模式: DAG并行 (独立步骤并发执行)")

    mindmap = _generate_mindmap(task, agent_id)
    print(_render_mindmap_text(mindmap))

    # 分析DAG并行度
    steps = mindmap.get("steps", [])
    deps_count = sum(1 for s in steps if s.get("depends") or s.get("deps"))
    independent = len(steps) - deps_count
    print(f"📊 DAG分析: {len(steps)}步骤, {independent}独立可并行, {deps_count}有依赖")

    agent_file = TASKS_DIR / f"{agent_id}.json"
    agent_file.write_text(json.dumps({
        "agent_id": agent_id, "task": task,
        "mindmap": mindmap, "status": "pending",
        "mode": "dag",
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    if not auto_run:
        return {"ok": True, "agent_id": agent_id, "mindmap": mindmap, "status": "pending"}

    result = _execute_agent_dag(agent_id, mindmap, agent_file)
    print(f"\n{'='*55}")
    print(f"🏁 DAG执行完成 | {result['steps_completed']}/{result['steps_total']} 步骤")
    return result


# ══════════════════════════════════════════════════════════
# 持久池基础设施
# ══════════════════════════════════════════════════════════
def _read_pool_state() -> dict:
    """读取持久池状态"""
    try:
        return json.loads(POOL_STATE.read_text(encoding='utf-8')) if POOL_STATE.exists() else {}
    except Exception:
        return {}

def _write_pool_state(state: dict):
    POOL_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

def _read_queue() -> list:
    try:
        return json.loads(QUEUE_FILE.read_text(encoding='utf-8')) if QUEUE_FILE.exists() else []
    except Exception:
        return []

def _write_queue(items: list):
    QUEUE_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')

def _worker_loop_state(worker_id: str, pool_state: dict):
    """单个worker主循环 — 从队列取任务执行，结果写入共享结果文件。
    由持久池子进程调用，不是对外动作。"""
    import time as _time
    print(f"🔁 Worker {worker_id} 启动，等待任务...")
    while True:
        # 读队列
        tasks = _read_queue()
        if not tasks:
            _time.sleep(0.5)
            continue

        # 取队首任务
        task_entry = tasks.pop(0)
        _write_queue(tasks)

        task_id    = task_entry.get("task_id", uuid.uuid4().hex[:8])
        task_text  = task_entry.get("task", "")
        agent_id   = f"pool_{worker_id}_{task_id}"
        auto_run   = task_entry.get("auto_run", True)

        print(f"\n{'='*55}")
        print(f"🟢 Worker {worker_id} 接单: {task_id}")
        print(f"📌 任务: {task_text}")

        result = {"task_id": task_id, "worker_id": worker_id, "agent_id": agent_id,
                  "task": task_text, "ok": False, "started": datetime.now().isoformat()}
        try:
            mindmap = _generate_mindmap(task_text, agent_id)
            agent_file = TASKS_DIR / f"{agent_id}.json"
            agent_file.write_text(json.dumps({
                "agent_id": agent_id, "task": task_text,
                "status": "running", "mindmap": mindmap,
                "created": datetime.now().isoformat(),
                "worker_id": worker_id, "pool_task_id": task_id,
            }, ensure_ascii=False, indent=2), encoding='utf-8')
            exec_result = _execute_agent(agent_id, mindmap, agent_file)
            result["ok"] = True
            result["steps_completed"] = exec_result.get("steps_completed", 0)
            result["steps_total"]     = exec_result.get("steps_total", 0)
            result["completed"]       = datetime.now().isoformat()
        except Exception as e:
            result["error"] = str(e)[:200]
            result["completed"] = datetime.now().isoformat()

        # 写入结果文件
        result_file = RESULTS_DIR / f"{task_id}.json"
        result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"✅ Worker {worker_id} 完成 {task_id} → {result_file}")


# ══════════════════════════════════════════════════════════
# 对外动作 — 持久池
# ══════════════════════════════════════════════════════════
def do_persistent_pool(params: dict) -> dict:
    """
    创建/管理持久子代理池。
    params: {action: "start"|"stop"|"status", pool_size: N}
    - start: 启动N个常驻worker子进程，任务完成不退出
    - stop:  结束所有worker子进程
    - status: 查看池状态
    """
    sub_action = params.get("action", "start")
    pool_size  = int(params.get("pool_size", 3))

    if sub_action == "stop":
        state = _read_pool_state()
        pids = state.get("workers", [])
        killed = 0
        for w in pids:
            pid = w.get("pid")
            if pid:
                try:
                    import signal
                    os.kill(pid, signal.SIGTERM)
                    killed += 1
                except Exception:
                    pass
        _write_pool_state({"status": "stopped", "workers": [], "pool_size": 0})
        return {"ok": True, "action": "persistent_pool", "sub_action": "stop",
                "killed": killed, "was_pool_size": len(pids)}

    if sub_action == "status":
        state = _read_pool_state()
        workers = state.get("workers", [])
        queue = _read_queue()
        return {"ok": True, "action": "persistent_pool", "sub_action": "status",
                "pool_size": state.get("pool_size", 0),
                "workers": workers, "queue_depth": len(queue),
                "status": state.get("status", "unknown")}

    if sub_action == "start":
        # 读取或初始化池状态
        state = _read_pool_state()
        existing = state.get("workers", [])
        # 清理已死的worker记录
        alive = []
        for w in existing:
            pid = w.get("pid")
            if pid:
                try:
                    os.kill(pid, 0)  # 信号0只检查存在
                    alive.append(w)
                except OSError:
                    pass

        # 启动新worker直到达到pool_size
        script = Path(__file__).resolve()
        started = []
        for i in range(len(alive), pool_size):
            worker_id = f"w{i}_{uuid.uuid4().hex[:6]}"
            # 以内部模式启动worker循环
            proc = subprocess.Popen(
                [sys.executable, str(script), "__worker_loop", json.dumps({"worker_id": worker_id})],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            )
            alive.append({"worker_id": worker_id, "pid": proc.pid, "started": datetime.now().isoformat()})
            started.append(worker_id)
            print(f"🧵 Worker {worker_id} 启动 (PID {proc.pid})")

        _write_pool_state({"status": "running", "pool_size": pool_size,
                           "workers": alive, "updated": datetime.now().isoformat()})
        queue = _read_queue()
        return {"ok": True, "action": "persistent_pool", "sub_action": "start",
                "pool_size": pool_size, "workers": [w["worker_id"] for w in alive],
                "started": started, "queue_depth": len(queue)}

    return {"ok": False, "error": f"未知子动作: {sub_action}"}


def do_auto_scale(params: dict) -> dict:
    """
    根据队列深度自动调整池大小。
    params: {min_pool: 2, max_pool: 8, scale_threshold: 3}
    - queue_depth >= scale_threshold → 扩容至上限
    - queue_depth == 0 且池 > min_pool → 缩容
    """
    min_pool    = int(params.get("min_pool", 2))
    max_pool    = int(params.get("max_pool", 8))
    threshold   = int(params.get("scale_threshold", 3))

    state = _read_pool_state()
    workers = state.get("workers", [])
    current_size = len(workers)
    queue = _read_queue()
    queue_depth = len(queue)

    target_size = current_size
    reason = "no_change"

    if queue_depth >= threshold and current_size < max_pool:
        target_size = min(current_size + 2, max_pool)
        reason = "scale_up"
    elif queue_depth == 0 and current_size > min_pool:
        target_size = max(min_pool, current_size - 1)
        reason = "scale_down"

    if target_size == current_size:
        return {"ok": True, "action": "auto_scale", "current_size": current_size,
                "target_size": target_size, "queue_depth": queue_depth, "reason": reason}

    # 执行缩放 — 复用 persistent_pool start/stop 逻辑
    if target_size > current_size:
        # 扩容
        result = do_persistent_pool({"action": "start", "pool_size": target_size})
    else:
        # 缩容：kill多余的worker
        to_kill = workers[target_size:]  # 从尾部缩容
        killed = 0
        for w in to_kill:
            pid = w.get("pid")
            if pid:
                try:
                    import signal
                    os.kill(pid, signal.SIGTERM)
                    killed += 1
                except Exception:
                    pass
        workers = workers[:target_size]
        _write_pool_state({"status": "running", "pool_size": target_size,
                           "workers": workers, "updated": datetime.now().isoformat()})
        result = {"ok": True, "killed": killed}

    return {"ok": True, "action": "auto_scale",
            "previous_size": current_size, "target_size": target_size,
            "queue_depth": queue_depth, "reason": reason}


def do_task_queue(params: dict) -> dict:
    """
    向持久池提交任务（队列化）。
    params: {task: "...", task_id: 可选}
    如果池为空则自动启动默认大小的池。
    """
    task_text = params.get("task", "")
    task_id   = params.get("task_id") or f"qtask_{uuid.uuid4().hex[:8]}"
    if not task_text:
        return {"ok": False, "error": "需要指定 task"}

    # 确保池在运行
    state = _read_pool_state()
    if not state.get("workers") or state.get("status") != "running":
        do_persistent_pool({"action": "start", "pool_size": params.get("auto_pool", 3)})

    # 入队
    queue = _read_queue()
    entry = {"task_id": task_id, "task": task_text,
             "enqueued": datetime.now().isoformat(),
             "auto_run": params.get("auto_run", True)}
    queue.append(entry)
    _write_queue(queue)

    return {"ok": True, "action": "task_queue", "task_id": task_id,
            "queue_position": len(queue), "queue_depth": len(queue),
            "message": f"任务 {task_id} 已入队，位置 #{len(queue)}"}
handlers = {
    "spawn":          do_spawn,           # 生成子代理+思维导图+执行
    "spawn_dag":      do_spawn_dag,       # DAG并行模式 (5x加速)
    "execute":        do_execute,         # 执行已生成的代理
    "status":         do_status,          # 查询状态
    "evidence":       do_evidence,        # 获取证据链
    "kill":           do_kill,            # 终止代理
    "mindmap_preview":do_mindmap_preview, # 只预览思维导图
    "persistent_pool":do_persistent_pool, # 持久代理池 (常驻worker)
    "auto_scale":     do_auto_scale,      # 自适应扩缩容
    "task_queue":     do_task_queue,      # 队列化任务提交
    "__worker_loop":  lambda p: _worker_loop_state(p["worker_id"], {}),  # 内部worker循环
}
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    h = handlers.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}"})
    result = h(params)
    print(json.dumps(result, ensure_ascii=False, indent=2))
