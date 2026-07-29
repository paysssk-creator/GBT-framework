# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""caps/_shared.py — 共享工具模块
=================================
所有cap可复用此模块，避免重复定义 _call_cap / _get_sandbox。
"""
import sys, json, subprocess
from pathlib import Path

_CAPS_ROOT = Path(__file__).parent
_SANDBOX_ROOT = Path(__file__).parent.parent


def _get_sandbox() -> Path:
    """返回沙箱根目录 (GBTxiaotudouV5/)"""
    return _SANDBOX_ROOT


def _call_cap(cap_id: str, action: str, params: dict, timeout: int = 15) -> dict:
    """标准子进程调用cap — 所有cap统一的调用入口（超时时杀子进程防孤儿）"""
    run_py = _CAPS_ROOT / cap_id / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": f"cap {cap_id} 不存在"}
    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, str(run_py), action,
             json.dumps(params, ensure_ascii=False)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=str(_SANDBOX_ROOT),
            encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        raw = (stdout or "").strip()
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"ok": True, "result": raw[:300]}
        return {"ok": False, "error": (stderr or "无输出")[:200]}
    except subprocess.TimeoutExpired:
        if proc:
            proc.kill()
            proc.wait(timeout=3)
        return {"ok": False, "error": f"超时({timeout}s)，已终止子进程"}
    except Exception as e:
        if proc and proc.poll() is None:
            proc.kill()
        return {"ok": False, "error": str(e)[:100]}
