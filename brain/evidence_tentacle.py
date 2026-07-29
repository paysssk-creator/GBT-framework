# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/evidence_tentacle.py -- 证据触手 · 铁证链 v1.0
====================================================
铁律: 没看 → 没证据 → 禁止下结论。

证据链:
  ① 看(see)     → 触手采集现场数据
  ② 记(record)   → 证据存入铁证链
  ③ 判(judge)    → 基于证据推理
  ④ 行(act)      → 执行并记录结果
  ⑤ 验(verify)   → 触手回传验证证据

每步操作前后必须采集证据，形成闭环铁证链。
"""
import sys, os, json, time, base64, io
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = Path.home() / ".gbt" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
CHAIN_FILE = EVIDENCE_DIR / "evidence_chain.jsonl"
SNAPSHOTS_DIR = EVIDENCE_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


class EvidenceTentacle:
    """证据触手 — 没看不许判，没证据不许行"""

    def __init__(self):
        self._chain = []
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def see(self, context: str = "") -> dict:
        """看 — 采集当前现场证据"""
        evidence = {
            "id": f"ev_{int(time.time()*1000)}",
            "session": self._session_id,
            "phase": "see",
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "sources": {}
        }

        # 屏幕证据
        try:
            from brain.host_body import eyes
            screen = eyes.see()
            if screen.get("ok"):
                evidence["sources"]["screen"] = {
                    "size": screen.get("size"),
                    "captured": True
                }
                # 保存截图证据
                snap = SNAPSHOTS_DIR / f"{evidence['id']}_screen.png"
                img_bytes = base64.b64decode(screen["image"])
                snap.write_bytes(img_bytes)
                evidence["sources"]["screen"]["file"] = str(snap)
        except:
            evidence["sources"]["screen"] = {"captured": False}

        # 代码证据 - 穿透扫描
        try:
            from brain.penetration_scan import scan_L1_syntax, scan_L2_load
            syntax = scan_L1_syntax()
            evidence["sources"]["code_syntax"] = {
                "ok": syntax.get("ok"),
                "issues": len(syntax.get("issues", []))
            }
        except:
            evidence["sources"]["code_syntax"] = {"ok": False}

        # 邻域证据
        try:
            from brain.nexus import get_nexus
            n = get_nexus()
            s = n.scan(force=True)
            evidence["sources"]["nexus"] = {
                "health": s.get("health_pct"),
                "found": s.get("found"),
                "total": s.get("total_caps")
            }
        except:
            evidence["sources"]["nexus"] = {"health": 0}

        # 触手状态证据
        try:
            from brain.neural_tentacle import get_tentacle
            t = get_tentacle()
            evidence["sources"]["tentacle"] = {
                "scans": t._scan_count,
                "issues_found": t._issues_found_total,
                "issues_fixed": t._issues_fixed_total
            }
        except:
            evidence["sources"]["tentacle"] = {"scans": 0}

        # 导航证据
        try:
            from brain.navigation_tentacle import navigate
            nav = navigate()
            evidence["sources"]["navigation"] = {
                "keys_valid": nav.get("keys_valid", 0),
                "payments_ready": nav.get("payments_ready", 0),
                "apis_total": nav.get("apis_total", 0),
                "routes_ok": nav.get("routes_ok", False),
            }
        except:
            evidence["sources"]["navigation"] = {"ok": False}

        self._chain.append(evidence)
        self._persist(evidence)
        return evidence

    def record(self, action: str, details: dict = None) -> dict:
        """记 — 记录操作证据"""
        record = {
            "id": f"rc_{int(time.time()*1000)}",
            "session": self._session_id,
            "phase": "record",
            "action": action,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._chain.append(record)
        self._persist(record)
        return record

    def judge(self, evidence: dict, question: str = "") -> dict:
        """判 — 基于证据推理，不是猜"""
        # 收集所有证据源
        sources = evidence.get("sources", {})
        has_screen = sources.get("screen", {}).get("captured", False)
        has_code = sources.get("code_syntax", {}).get("ok", False)
        nexus_health = sources.get("nexus", {}).get("health", 0)
        tentacle_scans = sources.get("tentacle", {}).get("scans", 0)

        # 证据充分性判定
        evidence_score = 0
        evidence_items = []

        if has_screen:
            evidence_score += 30
            evidence_items.append("屏幕证据:已采集")
        else:
            evidence_items.append("屏幕证据:缺失")

        if has_code:
            evidence_score += 30
            evidence_items.append("代码证据:通过")
        else:
            evidence_items.append("代码证据:缺失")

        if nexus_health and nexus_health > 90:
            evidence_score += 20
            evidence_items.append(f"邻域健康:{nexus_health}%")
        else:
            evidence_items.append("邻域健康:异常")

        if tentacle_scans > 0:
            evidence_score += 20
            evidence_items.append(f"触手扫描:{tentacle_scans}次")
        else:
            evidence_items.append("触手扫描:未运行")

        can_judge = evidence_score >= 50

        judgment = {
            "id": f"jd_{int(time.time()*1000)}",
            "session": self._session_id,
            "phase": "judge",
            "question": question,
            "can_judge": can_judge,
            "evidence_score": evidence_score,
            "evidence_items": evidence_items,
            "verdict": "证据充分,可以下结论" if can_judge else "证据不足,禁止下结论,必须先看",
            "timestamp": datetime.now().isoformat(),
        }

        self._chain.append(judgment)
        self._persist(judgment)
        return judgment

    def act(self, action: str, result: dict = None) -> dict:
        """行 — 执行并记录结果"""
        act_record = {
            "id": f"ac_{int(time.time()*1000)}",
            "session": self._session_id,
            "phase": "act",
            "action": action,
            "result": result or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._chain.append(act_record)
        self._persist(act_record)
        return act_record

    def verify(self, action: str, expected: dict = None) -> dict:
        """验 — 触手回传验证证据"""
        # 重新采集证据验证
        new_evidence = self.see(context=f"verify:{action}")

        verification = {
            "id": f"vr_{int(time.time()*1000)}",
            "session": self._session_id,
            "phase": "verify",
            "action": action,
            "expected": expected or {},
            "actual": {
                "nexus_health": new_evidence.get("sources", {}).get("nexus", {}).get("health"),
                "code_ok": new_evidence.get("sources", {}).get("code_syntax", {}).get("ok"),
                "screen_captured": new_evidence.get("sources", {}).get("screen", {}).get("captured"),
            },
            "timestamp": datetime.now().isoformat(),
        }

        self._chain.append(verification)
        self._persist(verification)
        return verification

    def full_chain(self, context: str, action: str = None) -> dict:
        """完整铁证链: 看→判→行→验"""
        # ① 必须先看
        evidence = self.see(context=context)

        # ② 基于证据判
        judgment = self.judge(evidence, question=context)

        if not judgment["can_judge"]:
            return {
                "ok": False,
                "phase": "judge_blocked",
                "message": "证据不足,禁止下结论。必须先采集更多证据。",
                "evidence": evidence,
                "judgment": judgment,
                "required": [e for e in judgment["evidence_items"] if "缺失" in e or "异常" in e],
            }

        # ③ 执行
        act_result = {}
        if action:
            act_result = self.act(action)

        # ④ 验证
        verification = self.verify(action or context)

        return {
            "ok": True,
            "evidence": evidence,
            "judgment": judgment,
            "action": act_result,
            "verification": verification,
            "chain_length": len(self._chain),
        }

    def _persist(self, entry: dict):
        """持久化证据到铁证链文件"""
        try:
            with open(CHAIN_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except:
            pass

    def stats(self) -> dict:
        return {
            "session": self._session_id,
            "chain_length": len(self._chain),
            "evidence_dir": str(EVIDENCE_DIR),
        }


# ═══════════════ 全局 ═══════════════

_evidence: Optional[EvidenceTentacle] = None


def get_evidence() -> EvidenceTentacle:
    global _evidence
    if _evidence is None:
        _evidence = EvidenceTentacle()
    return _evidence


def see_and_judge(context: str, action: str = None) -> dict:
    """快捷: 看→判→行→验 完整铁证链"""
    return get_evidence().full_chain(context, action)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="证据触手 - 铁证链")
    p.add_argument("--context", default="系统状态检查", help="上下文")
    p.add_argument("--action", help="执行动作")
    args = p.parse_args()

    e = get_evidence()
    result = e.full_chain(args.context, args.action)
    print(json.dumps(result, ensure_ascii=False, indent=2))
