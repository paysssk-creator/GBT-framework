# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/devour_tentacle.py -- 吞噬触手 · 自主进化 v1.0
====================================================
触手自己找食吃，自己进化。不用人手一根一根造。

吞噬循环:
  扫描平台 → 发现新技能 → 分析缺口 → 
  自动创建cap骨架 → 注入知识 → 注册nexus → 
  通知event_bus → 存入记忆

与 devourer cap 的关系:
  devourer cap = 独立的吞噬引擎(手动/定时触发)
  devour_tentacle = 织入神经触手的自主吞噬(每次脉冲自动触发)
"""
import sys, os, json, time
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

DEVOUR_STATE = Path.home() / ".gbt" / "neural_tentacle" / "devour_state.json"


class DevourTentacle:
    """吞噬触手 — 自动发现、吸收、进化"""

    def __init__(self):
        self.state = self._load_state()
        self._last_devour = None

    def _load_state(self) -> dict:
        if DEVOUR_STATE.exists():
            try:
                return json.loads(DEVOUR_STATE.read_text(encoding="utf-8"))
            except:
                pass
        return {
            "total_devours": 0,
            "total_absorbed": 0,
            "total_caps_created": 0,
            "last_devour_at": None,
            "absorbed_skills": [],
        }

    def _save_state(self):
        DEVOUR_STATE.parent.mkdir(parents=True, exist_ok=True)
        DEVOUR_STATE.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def scan_gaps(self) -> dict:
        """扫描能力缺口"""
        try:
            from caps.devourer.run import analyze_gaps
            return analyze_gaps()
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def quick_devour(self, max_findings: int = 5, timeout: int = 5) -> dict:
        from brain.chain_kernel import enforce_chain
        enforce_chain("devour_tentacle.quick_devour")
        """快速吞噬 - 本地优先，网络可选。非阻塞。"""
        result = {"ok": True, "total_found": 0, "absorbed": 0, "caps_created": 0, "new_skills": [], "mode": "local"}

        try:
            # 先用本地缺口分析
            gaps = self.scan_gaps()
            if gaps.get("ok") and gaps.get("gaps"):
                high_gaps = [g for g in gaps["gaps"] if g.get("priority") == "high"]
                result["gaps_found"] = len(high_gaps)
                result["total_found"] = len(gaps.get("gaps", []))

                # 自动创建高优先级缺口cap
                if high_gaps:
                    try:
                        created = self.auto_create_from_gaps(max_create=min(3, len(high_gaps)))
                        result["caps_created"] = len(created.get("created", []))
                        result["new_caps"] = created.get("created", [])
                    except:
                        pass

            # 更新状态
            self.state["total_devours"] += 1
            self.state["total_caps_created"] += result["caps_created"]
            self.state["total_absorbed"] += result["absorbed"]
            self.state["last_devour_at"] = __import__("datetime").datetime.now().isoformat()
            self._save_state()

            # 有新cap -> 通知nexus
            if result["caps_created"] > 0:
                try:
                    from brain.nexus import get_nexus
                    get_nexus().scan(force=True)
                except:
                    pass

            return result
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def devour_scan_results(self, scan_result: dict) -> dict:
        from brain.chain_kernel import enforce_chain
        enforce_chain("devour_tentacle.devour_scan")

        """吞噬穿透扫描结果 — 从自身问题中学习进化"""
        devoured = []
        fixed = []

        for layer_name, layer in scan_result.get("layers", {}).items():
            for issue in layer.get("detail", []):
                level = issue.get("level", "info")
                if level not in ("error", "warn", "info"):
                    continue
                msg = issue.get("msg", "")
                cap = issue.get("cap", "")
                path = issue.get("path", "")

                # 记录问题到知识库
                knowledge = f"[{layer_name}] {cap}: {msg}"
                devoured.append({"type": "scan_issue", "knowledge": knowledge, "path": path})

                # 尝试自动修复
                fix_type = issue.get("fix_type")
                if fix_type == "remove_action" and issue.get("fix_action"):
                    try:
                        import json
                        with open(path, "r", encoding="utf-8") as f:
                            cap_data = json.load(f)
                        action = issue["fix_action"]
                        if action in cap_data.get("actions", {}):
                            del cap_data["actions"][action]
                            with open(path, "w", encoding="utf-8") as f:
                                json.dump(cap_data, f, ensure_ascii=False, indent=2)
                            fixed.append(f"移除僵尸action: {path}::{action}")
                    except:
                        pass

                elif fix_type == "add_action" and issue.get("fix_action"):
                    try:
                        import json
                        with open(path, "r", encoding="utf-8") as f:
                            cap_data = json.load(f)
                        action = issue["fix_action"]
                        if "actions" not in cap_data:
                            cap_data["actions"] = {}
                        if action not in cap_data["actions"]:
                            cap_data["actions"][action] = {"description": action}
                            with open(path, "w", encoding="utf-8") as f:
                                json.dump(cap_data, f, ensure_ascii=False, indent=2)
                            fixed.append(f"补声明action: {path}::{action}")
                    except:
                        pass

        # 更新状态
        self.state["total_devours"] += 1
        self.state["total_absorbed"] += len(devoured)
        self.state["total_caps_created"] += len(fixed)
        if devoured:
            self.state.setdefault("scan_learnings", [])
            self.state["scan_learnings"].extend(d["knowledge"] for d in devoured)
            self.state["scan_learnings"] = self.state["scan_learnings"][-200:]
        self.state["last_devour_at"] = datetime.now().isoformat()
        self._save_state()

        return {
            "ok": True,
            "devoured": len(devoured),
            "fixed": len(fixed),
            "knowledge": [d["knowledge"][:100] for d in devoured[:5]],
            "fixes": fixed[:5],
        }

    def auto_create_from_gaps(self, max_create: int = 3) -> dict:
        from brain.chain_kernel import enforce_chain
        enforce_chain("devour_tentacle.auto_create")
        """从缺口自动创建cap骨架"""
        try:
            from caps.devourer.run import analyze_gaps, do_auto_create_gaps
            gaps = analyze_gaps()
            if not gaps.get("ok"):
                return gaps

            high_priority = [g for g in gaps.get("gaps", []) if g.get("priority") == "high"]
            if len(high_priority) > max_create:
                high_priority = high_priority[:max_create]

            if not high_priority:
                return {"ok": True, "created": 0, "message": "无高优先级缺口"}

            created = do_auto_create_gaps({"gaps": high_priority})
            self.state["total_caps_created"] += len(created.get("created", []))
            self._save_state()

            # 通知nexus
            try:
                from brain.nexus import get_nexus
                get_nexus().scan(force=True)
            except:
                pass

            return created
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def inject_to_tentacle(self, skill_name: str, knowledge: str) -> dict:
        from brain.chain_kernel import enforce_chain
        enforce_chain("devour_tentacle.inject")
        """将吞噬到的知识注入到触手系统"""
        # 记录到神经触手已知问题中
        try:
            from brain.neural_tentacle import get_tentacle
            t = get_tentacle()
            if not hasattr(t, 'known_issues'):
                t.known_issues = {}
            t.known_issues[f"devoured_{skill_name}"] = {
                "skill": skill_name,
                "knowledge": knowledge[:500],
                "devoured_at": datetime.now().isoformat(),
            }
            t._save_issues()
            return {"ok": True, "skill": skill_name}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}


# ═══════════════ 全局 ═══════════════

_devourer: Optional[DevourTentacle] = None


def get_devourer() -> DevourTentacle:
    global _devourer
    if _devourer is None:
        _devourer = DevourTentacle()
    return _devourer


def devour_pulse() -> dict:
    """快捷吞噬脉冲"""
    return get_devourer().quick_devour()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="吞噬触手 - 自主进化")
    p.add_argument("--pulse", action="store_true", help="快速吞噬脉冲")
    p.add_argument("--gaps", action="store_true", help="查看能力缺口")
    p.add_argument("--auto-create", action="store_true", help="自动创建缺口cap")
    p.add_argument("--state", action="store_true", help="吞噬状态")
    args = p.parse_args()

    d = get_devourer()

    if args.pulse:
        r = d.quick_devour()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.gaps:
        r = d.scan_gaps()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.auto_create:
        r = d.auto_create_from_gaps()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.state:
        print(json.dumps(d.state, ensure_ascii=False, indent=2))
    else:
        print(f"DevourTentacle: {d.state['total_devours']} devours, {d.state['total_absorbed']} absorbed, {d.state['total_caps_created']} caps created")
