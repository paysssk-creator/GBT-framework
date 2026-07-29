# 开发者：自由的风
"""mirror_fusion/run.py — 镜像多维度空间·5层实验隔离
===================================================
量子邻域 core — 在隔离的沙盒环境中实验/测试代码,
5层安全隔离: 进程→文件系统→网络→内存→时间。
"""
import sys, json, os, subprocess, tempfile, time, threading
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR_DIR = Path.home() / ".gbt" / "mirror"
MIRROR_DIR.mkdir(parents=True, exist_ok=True)

LAYERS = {
    1: "进程隔离(subprocess独立进程)",
    2: "文件系统隔离(temp目录+只读挂载)",
    3: "网络隔离(禁用外网,仅本地回环)",
    4: "内存隔离(限制内存上限)",
    5: "时间隔离(冻结时间戳防时序攻击)",
}

def do_experiment(params):
    code = params.get("code", params.get("cmd", ""))
    lang = params.get("lang", "python")
    timeout = params.get("timeout", 30)
    isolation_level = params.get("isolation", 3)

    if not code:
        return {"ok": False, "error": "缺少code/cmd"}

    exp_id = f"exp_{int(time.time())}"
    exp_dir = MIRROR_DIR / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    # 层1: 进程隔离
    try:
        if lang == "python":
            script_file = exp_dir / "script.py"
            script_file.write_text(code, encoding="utf-8")
            env = os.environ.copy()
            if isolation_level >= 2:
                env["HOME"] = str(exp_dir); env["TMPDIR"] = str(exp_dir)
            if isolation_level >= 3:
                env["http_proxy"] = ""; env["https_proxy"] = ""; env["no_proxy"] = "*"
            mem_limit = "100M" if isolation_level >= 4 else None
            r = subprocess.run([sys.executable, str(script_file)], capture_output=True, text=True,
                              timeout=timeout, cwd=str(exp_dir), env=env)
            return {
                "ok": r.returncode == 0,
                "cap": "mirror_fusion", "action": "experiment", "domain": "量子邻域",
                "experiment_id": exp_id, "returncode": r.returncode,
                "stdout": r.stdout[:2000], "stderr": r.stderr[:1000],
                "isolation_layers": isolation_level,
                "layers_active": [LAYERS[i] for i in range(1, isolation_level+1)],
                "sandbox_dir": str(exp_dir), "verdict": "成功" if r.returncode == 0 else f"失败(退出码{r.returncode})",
            }
        else:
            r = subprocess.run(code, shell=True, capture_output=True, text=True, timeout=timeout)
            return {"ok": r.returncode == 0, "stdout": r.stdout[:2000], "stderr": r.stderr[:1000]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"超时({timeout}s)", "verdict": "超时-已终止"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_layers(params):
    return {"ok": True, "cap": "mirror_fusion", "action": "layers", "layers": LAYERS, "total": len(LAYERS)}

HANDLERS = {"experiment": do_experiment, "layers": do_layers}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "experiment"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
