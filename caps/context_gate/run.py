# 开发者：自由的风
"""context_gate/run.py — 上下文守门人
=======================================
本地读取项目状态/日志/文件结构，生成结构化上下文摘要。
优先使用本地小模型 (节省token)，无本地模型时用纯文本压缩。
"""
import sys, json, os, re, subprocess
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
STATE_DIR = Path.home() / ".gbt" / "state"
EVOLVE_DIR = Path.home() / ".gbt" / "evolve"

def _read_state():
    """读取项目状态"""
    sf = STATE_DIR / PROJECT_ROOT.name / "state.json"
    if sf.exists():
        try:
            return json.loads(sf.read_text(encoding="utf-8"))
        except: pass
    return None

MEMORY_STORE = PROJECT_ROOT / "sandbox" / "memory_store.json"

def _read_memories(limit=5):
    """读取三岛记忆: memory_store.json + self_evolve insights + project_state decisions"""
    items = []

    # 1. memory_store.json (持久记忆)
    if MEMORY_STORE.exists():
        try:
            data = json.loads(MEMORY_STORE.read_text(encoding="utf-8"))
            for k, v in data.items():
                if isinstance(v, dict):
                    items.append({
                        "source": "memory_store",
                        "key": k,
                        "value": str(v.get("value", ""))[:120],
                        "saved": v.get("saved_at", ""),
                    })
        except:
            pass

    # 2. self_evolve insights (最近 3 条)
    insights_file = EVOLVE_DIR / "insights.json"
    if insights_file.exists():
        try:
            data = json.loads(insights_file.read_text(encoding="utf-8"))
            combined = (data.get("patterns", []) + data.get("lessons", []))[-3:]
            for pat in combined:
                items.append({
                    "source": "self_evolve",
                    "key": f"insight_{pat.get('type', 'unknown')}",
                    "value": str(pat.get("task", pat.get("lesson", "")))[:120],
                    "saved": pat.get("ts", ""),
                })
        except:
            pass

    # 3. project_state decisions (最近 3 条)
    state = _read_state()
    if state:
        decisions = state.get("decisions", [])[-3:]
        for d in decisions:
            items.append({
                "source": "project_state",
                "key": "decision",
                "value": str(d.get("text", ""))[:120],
                "saved": d.get("ts", ""),
            })

    return sorted(items, key=lambda x: x.get("saved", ""), reverse=True)[:limit]

def _read_project_tree(max_depth=3, max_files=80):
    """项目文件结构"""
    files = []
    skip = {"__pycache__", ".git", "node_modules", ".venv", "venv", "dist", "build",
            ".GBT", ".claude", ".gbt", "sandbox-logs"}
    for item in sorted(PROJECT_ROOT.iterdir()):
        if item.name.startswith(".") and item.name not in (".env",):
            continue
        if item.name in skip: continue
        if item.is_dir():
            depth = 0
            for p in item.rglob("*"):
                if depth > max_depth: break
                if any(s in p.parts for s in skip): continue
                if p.is_file() and p.suffix in (".py", ".md", ".json", ".yml", ".bat", ".ts", ".js", ".html", ".css"):
                    files.append(str(p.relative_to(PROJECT_ROOT)))
                if len(files) >= max_files: break
        elif item.is_file():
            files.append(item.name)
    return sorted(files)[:max_files]

def _read_recent_logs(n=20):
    """最近日志"""
    logs = []
    # 从 project_state
    state = _read_state()
    if state:
        logs = state.get("log", [])[-n:]
    # 从 llm_audit
    audit = Path.home() / ".gbt" / "sandbox" / "logs" / "llm_audit.jsonl"
    if audit.exists():
        try:
            lines = audit.read_text(encoding="utf-8").strip().split("\n")
            for line in lines[-10:]:
                e = json.loads(line)
                logs.append({"ts": e.get("ts", ""), "action": "llm_call",
                             "detail": f"{e.get('provider')} tokens:{e.get('tokens_in',0)}+{e.get('tokens_out',0)} {e.get('status')}"})
        except: pass
    return logs[-n:]

def _read_git_status():
    """Git 状态摘要"""
    import subprocess
    try:
        r = subprocess.run(["git", "status", "--porcelain"], cwd=str(PROJECT_ROOT),
                          capture_output=True, text=True, timeout=5)
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        staged = len([l for l in lines if not l.startswith("??") and l[1] != " "])
        unstaged = len([l for l in lines if l[0] in " M"])
        untracked = len([l for l in lines if l.startswith("??")])
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=str(PROJECT_ROOT),
                               capture_output=True, text=True, timeout=5).stdout.strip()
        return {"branch": branch, "staged": staged, "unstaged": unstaged, "untracked": untracked, "clean": staged + unstaged == 0}
    except: return None

def _try_local_model(prompt, max_chars=500):
    """尝试用本地小模型生成摘要 (降级: 返回None)"""
    try:
        # 尝试 ollama
        import subprocess
        models = ["qwen3:0.6b", "gemma3:1b", "llama3.2:1b", "phi3:mini"]
        for model in models:
            r = subprocess.run(["ollama", "run", model, prompt],
                             capture_output=True, text=True, timeout=30,
                             encoding="utf-8", errors="replace")
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()[:max_chars]
    except: pass
    return None

def _text_summary(style="full"):
    """纯文本上下文摘要 (无需模型)"""
    state = _read_state()
    git = _read_git_status()
    logs = _read_recent_logs(10)
    files = _read_project_tree(max_depth=2, max_files=40)

    parts = [f"## GBT-JXDWD 上下文摘要 ({datetime.now().strftime('%H:%M')})\n"]

    # 目标
    if state:
        active_goals = [g["title"] for g in state.get("goals", []) if g.get("status") == "active"]
        if active_goals:
            parts.append(f"🎯 当前目标: {active_goals[0]}")
        done = len([g for g in state.get("goals", []) if g.get("status") == "completed"])
        parts.append(f"📊 进度: {done}/{len(state.get('goals',[]))} 目标完成")

    # Git
    if git:
        parts.append(f"🔀 Git: {git['branch']} | 修改:{git.get('staged',0)+git.get('unstaged',0)} 未追踪:{git['untracked']}")

    # 文件
    cap_count = len([f for f in files if "caps/" in f and "/run.py" in f])
    # 记忆
    memories = _read_memories(3)
    if memories:
        parts.append("🧠 关键记忆:")
        for m in memories:
            parts.append(f"  [{m['key']}] {m['value'][:80]}")
    parts.append(f"📦 项目: {len(files)} 文件, ~{cap_count} caps")

    if style == "brief":
        return " | ".join(parts).replace("\n", " ")

    # 最近活动
    if logs:
        parts.append(f"\n📝 最近活动:")
        for l in logs[-5:]:
            parts.append(f"  {l.get('ts','')[-8:] if l.get('ts') else ''} {l.get('action','')}: {l.get('detail','')[:80]}")

    # 文件变更
    if git and not git["clean"]:
        parts.append(f"\n📁 待处理文件: {git['staged']+git['unstaged']} 个")

    return "\n".join(parts)


def do_summary(params=None):
    """生成完整上下文摘要"""
    style = (params or {}).get("style", "full")
    text = _text_summary(style)
    # 尝试用本地模型润色
    if style == "full":
        model_output = _try_local_model(f"用一句话总结以下项目状态:\n{text[:300]}")
        if model_output:
            text = f"🤖 本地模型总结: {model_output}\n\n{text}"
    # HEADROOM 集成：摘要超过 2000 字符时自动压缩
    if len(text) > 2000:
        try:
            hr = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "sandbox" / "caps" / "headroom" / "run.py"), "--action", "compress"],
                input=json.dumps({"text": text}), capture_output=True, text=True, timeout=15
            )
            if hr.returncode == 0:
                compressed = json.loads(hr.stdout)
                if compressed.get("ok"):
                    compressed_text = compressed.get("compressed", "")
                    if compressed_text:
                        text = f"[HEADROOM 压缩] 原 {len(text)} 字 → {len(compressed_text)} 字\n\n{compressed_text}"
        except Exception:
            pass
    return {"ok": True, "summary": text, "chars": len(text),
            "local_model_used": "🤖" in text}

def do_brief(params=None):
    """极简摘要"""
    text = _text_summary("brief")
    return {"ok": True, "brief": text}

def do_inject(params=None):
    """生成可注入主AI的完整系统提示"""
    state = _read_state()
    git = _read_git_status()
    files = _read_project_tree(max_depth=1, max_files=30)
    prompt = []
    prompt.append("你是GBT小土豆，GBT镜像多维度空间的驻场AI。")
    if state:
        goals = [g["title"] for g in state.get("goals", []) if g.get("status") == "active"]
        if goals:
            prompt.append(f"当前首要目标: {goals[0]}")
        decisions = state.get("decisions", [])[-3:]
        if decisions:
            prompt.append("最近决策: " + "; ".join(d["text"][:60] for d in decisions))
    if git:
        prompt.append(f"Git分支: {git['branch']}, 有{git.get('staged',0)+git.get('unstaged',0)}个未提交修改")
    prompt.append(f"项目包含 {len(files)} 个核心文件")
    memories = _read_memories(3)
    if memories:
        prompt.append("关键记忆: " + "; ".join(f"[{m['key']}]{m['value'][:60]}" for m in memories))
    prompt.append("请继续推进当前目标，遵循 GBT 金品标准。")
    system_prompt = "\n".join(prompt)
    if len(system_prompt) > 3000:
        system_prompt = system_prompt[:3000] + "\n[自动截断至 3000 字符]"
    return {"ok": True, "system_prompt": system_prompt,
            "usage": "将此文本注入 GBT编程工具 --append-system-prompt"}

def do_recall(params):
    """关键词搜索上下文历史"""
    query = (params or {}).get("query", params.get("q", "") if params else "")
    if not query:
        return {"ok": False, "error": "缺少 query 参数"}
    state = _read_state()
    if not state:
        return {"ok": True, "matches": [], "query": query}
    matches = []
    q = query.lower()
    for entry in state.get("log", []):
        if q in entry.get("detail", "").lower() or q in entry.get("action", "").lower():
            matches.append(entry)
    for d in state.get("decisions", []):
        if q in d.get("text", "").lower():
            matches.append({"ts": d["ts"], "action": "decision", "detail": d["text"]})
    # 也搜持久记忆
    memories = _read_memories(50)
    for m in memories:
        if q in m["value"].lower() or q in m["key"].lower():
            matches.append({"ts": m.get("saved",""), "action": "memory", "detail": f"[{m['key']}] {m['value']}"})
    return {"ok": True, "query": query, "matches": matches[-20:], "count": len(matches)}

def do_pressure(params=None):
    """压力检测：读取最近5个llm_audit.jsonl条目，累计token使用量，计算使用率。"""
    budget = (params or {}).get("budget", 10000)
    audit_path = Path.home() / ".gbt" / "sandbox" / "logs" / "llm_audit.jsonl"
    entries = []
    if audit_path.exists():
        try:
            lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
            for line in lines[-5:]:
                e = json.loads(line)
                entries.append(e)
        except Exception:
            pass

    total_tokens = sum(e.get("tokens_in", 0) + e.get("tokens_out", 0) for e in entries)
    usage_pct = round((total_tokens / max(budget, 1)) * 100, 1)

    result = {
        "ok": True,
        "entries_count": len(entries),
        "total_tokens": total_tokens,
        "budget": budget,
        "usage_pct": usage_pct,
        "threshold_exceeded": usage_pct > 60,
    }

    if usage_pct > 60:
        result["warning"] = f"Token使用率 {usage_pct}% 超过阈值60%，建议截断或压缩上下文"
        result["suggestion"] = "使用 headroom compress 压缩，或减少注入的记忆/文件数量"

    return result



def _score_sentences(text: str) -> list[tuple[str, float]]:
    """Score sentences by relevance using extractive heuristics (no LLM)."""
    # Split into sentences (handle Chinese + English punctuation)
    raw = re.split(r'(?<=[.!?。！？\n])\s*', text)
    sentences = [s.strip() for s in raw if s.strip() and len(s.strip()) > 2]
    if not sentences:
        return []

    # Word frequency (TF)
    all_words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{3,}', text.lower())
    if not all_words:
        # Fallback: just use position scoring
        total = len(sentences)
        scored = []
        for i, s in enumerate(sentences):
            pos_score = 1.5 if i == 0 else (1.3 if i < 3 else 1.0)
            length_score = min(len(s) / 150, 1.0) if len(s) > 20 else 0.3
            score = pos_score * 0.7 + length_score * 0.3
            scored.append((s, round(score, 4)))
        return scored

    word_freq = {}
    for w in all_words:
        word_freq[w] = word_freq.get(w, 0) + 1
    max_freq = max(word_freq.values()) if word_freq else 1

    total = len(sentences)
    scored = []
    for i, s in enumerate(sentences):
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{3,}', s.lower())
        if not words:
            scored.append((s, 0.1))
            continue
        # TF score
        tf_score = sum(word_freq.get(w, 0) / max_freq for w in words) / len(words)
        # Position score (first sentences matter more)
        pos_score = 1.5 if i == 0 else (1.3 if i < total * 0.2 else 1.0)
        # Length score (penalize too short or too long)
        ln = len(s)
        length_score = 1.0 if 20 < ln < 300 else (0.5 if ln <= 20 else 0.7)
        # Named entity bonus (uppercase words, numbers, dates)
        ne_bonus = 0.0
        if re.search(r'[A-Z]{2,}', s): ne_bonus += 0.15
        if re.search(r'\d{2,}', s): ne_bonus += 0.1
        if re.search(r'\d{4}-\d{2}-\d{2}', s): ne_bonus += 0.1

        score = tf_score * 0.4 + pos_score * 0.3 + length_score * 0.2 + ne_bonus * 0.1
        scored.append((s, round(score, 4)))

    return scored


def do_compress_context(params=None):
    """Extractive summarization: reduce text by >=50% while preserving key facts."""
    p = params or {}
    text = p.get("text", "")
    target_ratio = p.get("ratio", 0.5)  # default: keep 50%, discard 50%

    if not text:
        return {"ok": False, "error": "text is required"}

    original_len = len(text)
    scored = _score_sentences(text)
    if not scored:
        return {"ok": True, "compressed": text, "original_chars": original_len,
                "compressed_chars": original_len, "reduction_pct": 0, "method": "noop"}

    # Sort by score descending, select top N by target ratio
    keep_count = max(1, int(len(scored) * target_ratio))
    # But keep original order for coherence
    indexed = [(i, s, sc) for i, (s, sc) in enumerate(scored)]
    # Get threshold score at position keep_count
    threshold = sorted(scored, key=lambda x: x[1], reverse=True)[keep_count - 1][1] if keep_count <= len(scored) else 0
    # Keep sentences at or above threshold, in original order
    kept = [(s, sc) for s, sc in scored if sc >= threshold]
    # If too many tied at threshold, trim to keep_count
    if len(kept) > keep_count:
        kept = kept[:keep_count]

    compressed = "\n".join(s for s, _ in kept)
    compressed_len = len(compressed)
    reduction_pct = round((1 - compressed_len / max(original_len, 1)) * 100, 1)

    # Ensure at least 50% reduction if possible
    if reduction_pct < 50 and len(kept) > 1:
        # More aggressive: drop lowest-scored until >=50%
        kept_sorted = sorted(kept, key=lambda x: x[1])
        for i in range(len(kept_sorted)):
            trial = "\n".join(s for s, _ in kept_sorted[i+1:])
            if len(trial) / max(original_len, 1) <= 0.5:
                # Re-sort to original order
                kept_set = {s for s, _ in kept_sorted[i+1:]}
                kept = [(s, sc) for s, sc in scored if s in kept_set]
                compressed = "\n".join(s for s, _ in kept)
                compressed_len = len(compressed)
                reduction_pct = round((1 - compressed_len / max(original_len, 1)) * 100, 1)
                break

    return {
        "ok": True,
        "compressed": compressed,
        "original_chars": original_len,
        "compressed_chars": compressed_len,
        "reduction_pct": reduction_pct,
        "sentences_kept": len(kept),
        "sentences_total": len(scored),
        "method": "extractive_tf_position",
    }


AUTO_GATE_STATE = {"total_compressions": 0, "last_size": 0}


def do_auto_gate(params=None):
    """Monitor context size and trigger compression at thresholds."""
    p = params or {}
    text = p.get("text", "")
    threshold = p.get("threshold", 2000)  # chars
    target_ratio = p.get("ratio", 0.5)
    auto = p.get("auto", True)  # if True, auto-compress when over threshold

    if not text:
        return {"ok": False, "error": "text is required"}

    current_size = len(text)
    AUTO_GATE_STATE["last_size"] = current_size

    result = {
        "ok": True,
        "current_size": current_size,
        "threshold": threshold,
        "over_threshold": current_size > threshold,
        "auto_compressed": False,
    }

    if not auto or current_size <= threshold:
        return result

    # Auto-compress
    compressed_result = do_compress_context({"text": text, "ratio": target_ratio})
    if compressed_result.get("ok"):
        AUTO_GATE_STATE["total_compressions"] += 1
        result.update({
            "auto_compressed": True,
            "compressed_text": compressed_result["compressed"],
            "compressed_size": compressed_result["compressed_chars"],
            "reduction_pct": compressed_result["reduction_pct"],
            "total_compressions": AUTO_GATE_STATE["total_compressions"],
            "note": f"Auto-compressed from {current_size} to {compressed_result['compressed_chars']} chars "
                    f"({compressed_result['reduction_pct']}% reduction)",
        })

    return result
HANDLERS = {"summary": do_summary, "brief": do_brief, "inject": do_inject, "recall": do_recall, "pressure": do_pressure, "compress_context": do_compress_context, "auto_gate": do_auto_gate}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "summary"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
