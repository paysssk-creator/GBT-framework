# capability_protocol.py — GBT 能力协议引擎
# 统一能力发现/调用/健康检查层
# 被 gbt_brain, cloud_brain, image_analysis, root_cause_debugger 引用
# ============================================================
import json, os, subprocess, sys
from pathlib import Path
from typing import Optional
ROOT = Path(__file__).parent.parent  # brain/ → project root
CAPS_DIR = ROOT / "caps"
INTEGRATIONS_DIR = ROOT / "integrations"
DEPLOY_DIR = ROOT / "deploy"

class CapabilityEngine:
    """统一能力调用引擎"""

    def __init__(self):
        self._modules = {}
        self.module_count = 0
        self._scan()

    def _scan(self):
        """扫描所有能力模块"""
        search_dirs = [CAPS_DIR, INTEGRATIONS_DIR, DEPLOY_DIR]
        for base in search_dirs:
            if not base.exists():
                continue
            for entry in sorted(base.iterdir()):
                if entry.is_dir() and (entry / "run.py").exists():
                    name = entry.name
                    cap_json = entry / "capability.json"
                    meta = {}
                    if cap_json.exists():
                        try:
                            meta = json.loads(cap_json.read_text(encoding="utf-8"))
                        except:
                            pass
                    self._modules[name] = {
                        "path": str(entry),
                        "run_py": str(entry / "run.py"),
                        "meta": meta,
                    }
        self.module_count = len(self._modules)

    def call(self, cap_name: str, action: str, params: dict = None, timeout: int = 30):
        from brain.chain_kernel import enforce_chain
        enforce_chain(f"capability_protocol.{cap_name}")

        """调用能力模块"""
        mod = self._modules.get(cap_name)
        if not mod:
            return {"ok": False, "error": f"cap {cap_name} 不存在", "available": list(self._modules.keys())}
        try:
            params_json = json.dumps(params or {}, ensure_ascii=False)
            r = subprocess.run(
                [sys.executable, mod["run_py"], action, params_json],
                capture_output=True, text=True, timeout=timeout,
                cwd=str(ROOT), encoding="utf-8", errors="replace"
            )
            if r.stdout.strip():
                return json.loads(r.stdout)
            return {"ok": False, "error": r.stderr[:200] if r.stderr else "无输出"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"{cap_name}.{action} 超时({timeout}s)"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def health(self):
        """快速健康检查(不执行子进程)"""
        return {
            "module_count": self.module_count,
            "modules": sorted(self._modules.keys()),
        }

    def reload(self):
        """重新扫描"""
        self._modules.clear()
        self._scan()
        return self.health()


# 全局单例
_engine: Optional[CapabilityEngine] = None

def get_engine() -> CapabilityEngine:
    global _engine
    if _engine is None:
        _engine = CapabilityEngine()
    return _engine


def call_cap(cap: str, action: str, params: dict = None):
    """快捷调用"""
    return get_engine().call(cap, action, params)
