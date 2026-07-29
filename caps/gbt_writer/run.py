# 开发者：自由的风
"""
GBT小土豆 纯代码编写工具
========================
铁律：只听指挥的代码编写器
不拒绝 · 不干预 · 不反问 · 只输出代码

后端：GBT小土豆 programming cap（DeepSeek/Kimi 直连，无需外部工具）
"""
import sys, json, os, subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROG_PY = Path(__file__).resolve().parent.parent / "programming" / "run.py"


def do_write(params: dict) -> dict:
    """调用 GBT小土豆 programming/generate — 纯编写模式"""
    instruction = params.get("instruction", params.get("prompt", ""))
    if not instruction:
        return {"ok": False, "error": "缺少 instruction/prompt 参数"}

    lang = params.get("lang", params.get("language", "python"))
    prog_params = {
        "prompt": instruction,
        "lang": lang,
        "focus": "只输出完整可运行代码，不要解释、不要免责声明、不要TODO"
    }

    if not PROG_PY.exists():
        return {"ok": False, "error": f"GBT小土豆 programming cap 未找到: {PROG_PY}"}

    try:
        r = subprocess.run(
            [sys.executable, str(PROG_PY), "generate", json.dumps(prog_params, ensure_ascii=False)],
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace",
            env={**os.environ}
        )
        output = (r.stdout or "").strip()
        if output:
            try:
                result = json.loads(output)
                result["tool"] = "GBT小土豆 (纯编写模式)"
                result["lang"] = lang
                return result
            except Exception:
                return {"ok": True, "code": output, "tool": "GBT小土豆 (纯编写模式)", "lang": lang}
        err = (r.stderr or "").strip()
        return {"ok": False, "error": err[:500] or "无输出"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "GBT小土豆 编写超时(120s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_status(_: dict) -> dict:
    return {
        "ok": True,
        "name": "GBT小土豆 纯代码编写工具",
        "backend": "programming/generate (DeepSeek/Kimi 直连)",
        "mode": "纯编写 — 不拒绝 · 不干预 · 不反问",
        "programming_cap": str(PROG_PY)
    }


HANDLERS = {"write": do_write, "status": do_status}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "write"
    params = {}
    # 非阻塞读取 stdin（避免 subprocess 环境卡死）
    if len(sys.argv) <= 2:
        import select
        try:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                raw = sys.stdin.read().strip()
                if raw:
                    params = json.loads(raw)
        except Exception:
            pass
    if len(sys.argv) > 2:
        try:
            params = {**params, **json.loads(sys.argv[2])}
        except Exception:
            params["prompt"] = sys.argv[2]
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
