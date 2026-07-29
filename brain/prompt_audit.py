# GBT小土豆 v5.0 · 提示词吞噬引擎
# 精准审计系统提示词 token 消耗，定位膨胀源

import os, re, json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SOURCES = {
    "AGENTS.md":           ROOT / "AGENTS.md",
    "HOST_BODY.md":        ROOT / "HOST_BODY.md",
    "user_AGENTS.md":      Path.home() / ".codex" / "AGENTS.md",
}

# 项目文档——存在但未被 omp 注入，仅供参考
DOCS_ONLY = {
    "CONSTITUTION.md":     ROOT / "CONSTITUTION.md",
    "pipeline.md":         ROOT / "pipeline.md",
    "dual_brain.md":       ROOT / "dual_brain.md",
    "gates.md":            ROOT / "gates.md",
    "STAMP.md":            ROOT / "STAMP.md",
}


def count_chars(text: str) -> int:
    return len(text)


def estimate_tokens(text: str) -> int:
    """粗略估算: 中文 ~1.5 char/token, 英文 ~4 char/token"""
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
    other = len(text) - chinese
    return int(chinese / 1.5 + other / 4)


def estimate_tokens_tiktoken(text: str) -> int:
    """精确计数（如果 tiktoken 可用）"""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return estimate_tokens(text)


def analyze_file(path: Path, label: str) -> dict:
    """分析单个文件"""
    if not path.exists():
        return {"label": label, "path": str(path), "exists": False, "chars": 0, "tokens": 0, "lines": 0}

    text = path.read_text(encoding="utf-8", errors="replace")
    chars = count_chars(text)
    tokens = estimate_tokens_tiktoken(text)
    lines = text.count('\n') + 1
    return {
        "label": label,
        "path": str(path),
        "exists": True,
        "chars": chars,
        "tokens": tokens,
        "lines": lines,
    }


def estimate_omp_system_prompt() -> dict:
    """从最近 collab 会话 API usage 数据估算 omp 系统提示词 token 量"""
    import json, glob as _glob
    collab_dir = Path.home() / ".omp" / "collab"
    if collab_dir.exists():
        files = sorted(collab_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
        for f in files[:3]:
            try:
                first_msg = None
                for line in f.read_text(encoding="utf-8").splitlines():
                    entry = json.loads(line)
                    if entry.get("type") == "message" and entry.get("message", {}).get("usage"):
                        u = entry["message"]["usage"]
                        first_msg = u
                        break
                if first_msg:
                    # 第一条消息的 input tokens ≈ omp 系统提示词 + GBT 上下文 + 用户消息
                    input_tokens = first_msg.get("input", 0)
                    # 后续消息的 cacheRead ≈ 系统提示词 + 上下文（不含用户消息）
                    cache_reads = []
                    for line in f.read_text(encoding="utf-8").splitlines():
                        entry = json.loads(line)
                        if entry.get("type") == "message" and entry.get("message", {}).get("usage"):
                            cr = entry["message"]["usage"].get("cacheRead", 0)
                            if cr > 10000:
                                cache_reads.append(cr)
                    avg_cache = sum(cache_reads) / len(cache_reads) if cache_reads else input_tokens
                    return {
                        "label": "omp_system_prompt",
                        "path": f"<API 估算: {f.name}>",
                        "exists": True,
                        "chars": 0,
                        "tokens": int(avg_cache),
                        "lines": 0,
                        "note": f"从 collab 会话 API usage 提取: input={input_tokens}, avg_cache={avg_cache:,.0f}"
                    }
            except Exception:
                continue
    return {
        "label": "omp_system_prompt",
        "path": "<无法提取>",
        "exists": False,
        "chars": 0,
        "tokens": 0,
        "lines": 0,
        "note": "无 collab 会话数据"
    }


def aggregate(results: list[dict]) -> dict:
    """汇总所有来源"""
    existing = [r for r in results if r.get("exists", False)]
    total_context_tokens = sum(r["tokens"] for r in existing)
    total_context_chars = sum(r["chars"] for r in existing)

    # 典型上下文窗口
    windows = {
        "deepseek-v4": 131072,
        "deepseek-v3": 65536,
        "deepseek-r1": 131072,
        "gpt-4o": 128000,
        "claude-3.5": 200000,
    }

    return {
        "sources": sorted(existing, key=lambda r: r["tokens"], reverse=True),
        "missing": [r for r in results if not r.get("exists", False)],
        "total_chars": total_context_chars,
        "total_tokens": total_context_tokens,
        "context_windows": {k: {
            "total": v,
            "used_pct": round(total_context_tokens / v * 100, 1),
            "remaining": v - total_context_tokens,
        } for k, v in windows.items()},
    }


def report(summary: dict) -> str:
    """生成人类可读报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("  GBT 系统提示词吞噬审计")
    lines.append("=" * 60)
    lines.append("")

    total = summary["total_tokens"]
    lines.append(f"  总计注入: {total:,} tokens ({summary['total_chars']:,} 字符)")
    lines.append("")

    lines.append("  ─── 各来源 token 消耗 ───")
    for i, src in enumerate(summary["sources"]):
        pct = round(src["tokens"] / total * 100, 1) if total > 0 else 0
        bar = "█" * int(pct / 2)
        lines.append(f"  {i+1}. {src['label']:<20s} {src['tokens']:>6,} tokens ({pct:>5.1f}%) {bar}")
        lines.append(f"     {src['path']} ({src['lines']} 行)")

    if summary["missing"]:
        lines.append("")
        lines.append("  ─── 缺失文件 ───")
        for m in summary["missing"]:
            lines.append(f"  ✗ {m['label']}: {m['path']}")

    lines.append("")
    lines.append("  ─── 上下文窗口占用 ───")
    for model, info in summary["context_windows"].items():
        status = "🚨 危险" if info["used_pct"] > 30 else ("⚠️ 偏高" if info["used_pct"] > 15 else "✅ 健康")
        lines.append(f"  {model:<18s} {info['used_pct']:>5.1f}% 占用 {status} ({info['remaining']:,} tokens 剩余)")

    lines.append("")
    lines.append("  ─── 铁律来源 (高认知负载来源) ───")
    cognitive_sources = ["AGENTS.md", "HOST_BODY.md", "user_AGENTS.md",
                         "pipeline.md", "CONSTITUTION.md", "gates.md"]
    cognitive_tokens = 0
    for src in summary["sources"]:
        if src["label"] in cognitive_sources:
            cognitive_tokens += src["tokens"]
    lines.append(f"  铁律/管线/契约类: {cognitive_tokens:,} tokens ({round(cognitive_tokens/total*100,1)}%)")
    lines.append(f"  功能类(文档):      {total - cognitive_tokens:,} tokens")

    lines.append("")
    lines.append("  ─── 建议 ───")
    if cognitive_tokens > 2000:
        lines.append("  🔴 铁律/管线类占比过高，严重挤占有效推理空间")
        lines.append("  🔴 建议: 将 AGENTS.md/HOST_BODY.md 从上下文注入中移除")
        lines.append("  🔴 或精简为 5 行以内的核心规则")
    elif cognitive_tokens > 1000:
        lines.append("  🟡 认知负载偏高，可考虑精简")
    else:
        lines.append("  🟢 认知负载合理")

    return "\n".join(lines)


def main():
    print("🧠 GBT 提示词吞噬引擎 v1.0")
    print("   正在审计系统提示词 token 消耗...")
    print()

    results = []
    for label, path in SOURCES.items():
        results.append(analyze_file(path, label))

    # omp 内置系统提示词（从 API usage 数据提取）
    omp_result = estimate_omp_system_prompt()
    results.append(omp_result)

    summary = aggregate(results)
    print(report(summary))

    # 保存 JSON
    out_path = ROOT / ".gbt" / "prompt_audit.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    print(f"\n📄 审计报告已保存: {out_path}")

    return summary


if __name__ == "__main__":
    main()
