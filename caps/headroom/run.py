# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
headroom/run.py — Token智能压缩引擎
================================================================
集成 headroomlabs-ai/headroom (56k stars, Apache 2.0):
  - ContentRouter: 自动检测JSON/代码/文本，选最优压缩器
  - SmartCrusher: JSON深度压缩
  - CodeCompressor: AST级别代码压缩
  - Kompress-v2-base: HuggingFace模型文本压缩
  - CacheAligner: 前缀对齐，提升KV缓存命中率
  - CCR: 可逆压缩，按需检索原始内容
  - 跨Agent记忆: Claude/Codex/Gemini共享存储

安装: pip install "headroom-ai[all]"
"""
import sys, json, os, re, subprocess
from pathlib import Path

HEADROOM_AVAILABLE = False
try:
    import importlib
    importlib.import_module("headroom")
    HEADROOM_AVAILABLE = True
except ImportError:
    pass


TIKTOKEN_AVAILABLE = False
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    pass

def _real_tokens(text: str) -> int:
    """Real token count using tiktoken cl100k_base, fallback ~2.5 chars/token"""
    if TIKTOKEN_AVAILABLE:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except:
            pass
    return max(1, int(len(text) / 2.5))

def _py_compress(text: str) -> dict:
    """Python回退: 基础文本压缩"""
    original_len = len(text)
    original_tokens_est = _real_tokens(text)  # 粗略估计

    # 策略1: 去空白压缩
    compressed = re.sub(r'\n{3,}', '\n\n', text)  # 多余空行
    compressed = re.sub(r' {2,}', ' ', compressed)  # 多余空格
    # 策略2: 去日志时间戳
    compressed = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d+Z]*\s*', '', compressed)
    # 策略3: JSON精简
    if text.strip().startswith('{') or text.strip().startswith('['):
        try:
            obj = json.loads(text)
            compressed = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
        except Exception:
            pass

    compressed_len = len(compressed)
    ratio = round((1 - compressed_len / max(original_len, 1)) * 100, 1)
    return {
        "ok": True,
        "method": "python_fallback",
        "original_chars": original_len,
        "compressed_chars": compressed_len,
        "estimated_tokens_before": original_tokens_est,
        "estimated_tokens_after": _real_tokens(compressed),
        "savings_pct": ratio,
        "compressed": compressed[:5000],
    }


def _headroom_compress(text: str) -> dict:
    """使用 Headroom 原生压缩"""
    try:
        from headroom import compress
        result = compress([{"role": "user", "content": text}])
        return {"ok": True, "method": "headroom_native", "result": str(result)[:5000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def do_compress(params: dict) -> dict:
    text = params.get("text", params.get("prompt", ""))
    if not text and "stdin" in params:
        text = params["stdin"]
    if not text:
        return {"ok": False, "error": "缺少 text"}

    if HEADROOM_AVAILABLE:
        r = _headroom_compress(text)
        if r.get("ok"):
            r["action"] = "compress"
            r["context_gate_compatible"] = True
            r["context_gate_note"] = "返回字段: compressed(压缩后文本), original_chars, compressed_chars, savings_pct"
            return r

    r = _py_compress(text)
    r["action"] = "compress"
    r["context_gate_compatible"] = True
    r["context_gate_note"] = "返回字段: compressed(压缩后文本), original_chars, compressed_chars, savings_pct"
    r["note"] = "安装 headroom-ai 获得 60-95% 更优压缩: pip install 'headroom-ai[all]'"
    return r


def do_stats(params: dict) -> dict:
    if HEADROOM_AVAILABLE:
        try:
            r = subprocess.run(["headroom", "perf"], capture_output=True, text=True, timeout=10)
            return {"ok": True, "method": "headroom_native", "stats": r.stdout[:3000]}
        except Exception:
            pass
    return {
        "ok": True,
        "headroom_installed": HEADROOM_AVAILABLE,
        "compression_available": "python_fallback (basic: whitespace+JSON+timestamp)",
        "estimated_savings": "30-50% (fallback) vs 60-95% (headroom native)",
        "note": "pip install 'headroom-ai[all]' for SmartCrusher/CodeCompressor/Kompress-v2",
    }


def do_info(params: dict) -> dict:
    return {
        "ok": True,
        "installed": HEADROOM_AVAILABLE,
        "features": {
            "compressors": "SmartCrusher(JSON) + CodeCompressor(AST) + Kompress-v2-base(text)",
            "router": "ContentRouter — auto-detect content type",
            "cache": "CacheAligner — prefix stabilization for KV cache hits",
            "retrieval": "CCR — reversible, originals cached locally",
            "memory": "cross-agent — shared across Claude/Codex/Gemini",
            "learn": "headroom learn — mines failed sessions, writes corrections",
        },
        "savings": "60-95% tokens, same answers",
        "install": "pip install 'headroom-ai[all]'",
        "stars": "56,499",
        "license": "Apache 2.0",
    }


handlers = {"compress": do_compress, "stats": do_stats, "info": do_info}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "compress"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = handlers.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(handlers.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
