# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/platform.py -- 统一平台 · 能力中枢 v1.0
============================================
所有触手能力集中到一个面板: 扫描/审计/视觉/导航/吞噬/证据/脑委会
"""
import sys, os, json, time
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


class Platform:
    """统一平台 - 所有能力中枢"""

    def status(self) -> dict:
        """全平台状态一览"""
        return {
            "timestamp": datetime.now().isoformat(),
            "systems": {
                "neighborhood": self._nexus_status(),
                "tentacle": self._tentacle_status(),
                "vision": self._vision_status(),
                "audit": self._audit_status(),
                "navigation": self._nav_status(),
                "devour": self._devour_status(),
                "evidence": self._evidence_status(),
                "council": self._council_status(),
                "deploy": self._deploy_status(),
            }
        }

    def _nexus_status(self) -> dict:
        try:
            from brain.nexus import get_nexus
            n = get_nexus()
            s = n.scan(force=True)
            return {"ok": s.get("ok", False), "health": s.get("health_pct", 0),
                    "caps": f"{s.get('found', 0)}/{s.get('total_caps', 0)}", "domain": "19域"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def _tentacle_status(self) -> dict:
        try:
            from brain.neural_tentacle import get_tentacle
            t = get_tentacle()
            return {"ok": True, "scans": t._scan_count,
                    "found": t._issues_found_total, "healed": t._issues_fixed_total}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def _vision_status(self) -> dict:
        try:
            from brain.host_body import eyes
            screen = eyes.see()
            from brain.visual_memory import get_memory
            mem = get_memory()
            return {"ok": screen.get("ok", False),
                    "screen": screen.get("size", [0, 0]) if screen.get("ok") else None,
                    "memory_frames": mem.stats.get("total_frames", 0)}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def _audit_status(self) -> dict:
        try:
            from brain.deploy_audit import get_auditor
            a = get_auditor()
            audits = a._history
            last = audits[-1] if audits else None
            return {"ok": True, "total_audits": len(audits),
                    "last_score": last["overall_score"] if last else None}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def _nav_status(self) -> dict:
        try:
            from brain.navigation_tentacle import get_nav
            n = get_nav()
            return {"ok": True, "navigations": n.state.get("total_navigations", 0),
                    "keys_valid": n.state.get("keys_found", 0)}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def _devour_status(self) -> dict:
        try:
            from brain.devour_tentacle import get_devourer
            d = get_devourer()
            return {"ok": True, "devours": d.state.get("total_devours", 0),
                    "absorbed": d.state.get("total_absorbed", 0),
                    "caps_created": d.state.get("total_caps_created", 0)}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def _evidence_status(self) -> dict:
        try:
            from brain.evidence_tentacle import get_evidence
            e = get_evidence()
            return {"ok": True, "chain": e.stats().get("chain_length", 0)}
        except Exception as ex:
            return {"ok": False, "error": str(ex)[:100]}

    def _council_status(self) -> dict:
        try:
            from brain.brain_council import get_council
            c = get_council()
            return {"ok": True, "brains": "10脑", "history": len(c._history)}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def _deploy_status(self) -> dict:
        try:
            from caps.oneclick_deploy.run import _load_status
            s = _load_status()
            deps = s.get("deployments", {})
            active = sum(1 for d in deps.values() if d.get("status") not in ("failed",))
            return {"ok": True, "total": len(deps), "active": active}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}


def platform_status() -> dict:
    return Platform().status()


if __name__ == "__main__":
    p = Platform()
    s = p.status()
    print("\n" + "=" * 55)
    print("  GBT 统一平台 · 能力中枢")
    print("=" * 55)
    for name, info in s["systems"].items():
        ok = info.get("ok", False)
        icon = "🟢" if ok else "🔴"
        details = ", ".join(f"{k}={v}" for k, v in info.items() if k not in ("ok", "error"))
        print(f"  {icon} {name:15s} {details}")
    print("=" * 55)
