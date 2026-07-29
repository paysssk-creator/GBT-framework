# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/audit_trail.py — 执行审计追踪器
=======================================
第零条执行: 确保每条指令都真实执行，产出可查证据。
三重验证: ①工具调用记录 ②产出物证 ③证据链闭合
"""
import json, time, hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

TRAIL_DIR = Path.home() / ".gbt" / "audit"
TRAIL_DIR.mkdir(parents=True, exist_ok=True)
TRAIL_FILE = TRAIL_DIR / "trail.jsonl"


class AuditTrail:
    """执行审计追踪 — 每一条指令的可查证据链"""

    def __init__(self):
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.records: list[dict] = []
        self.start_time = time.time()

    # ── 记录 ──────────────────────────────────

    def log(self, action: str, evidence: dict, 
            instruction: str = "", phase: str = "") -> dict:
        """记录一次真实执行"""
        record = {
            "session": self.session_id,
            "seq": len(self.records) + 1,
            "timestamp": time.time(),
            "phase": phase,
            "instruction": instruction[:200],
            "action": action,
            "evidence": evidence,
            "verifiable": self._is_verifiable(evidence)
        }
        self.records.append(record)
        self._persist(record)
        return record

    def _is_verifiable(self, evidence: dict) -> bool:
        """判断证据是否可查"""
        # 必须有至少一个可验证字段
        verifiable_fields = ["stdout", "stderr", "output", "result", 
                            "tag", "file", "lines", "status", "returncode",
                            "url", "response", "content"]
        for f in verifiable_fields:
            if f in evidence and evidence[f]:
                return True
        # 如果是工具调用，至少要有工具名
        if evidence.get("tool"):
            return True
        return False

    def _persist(self, record: dict):
        with open(TRAIL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ── 核查 ──────────────────────────────────

    def verify_last(self) -> dict:
        """核查最近一条记录是否真实"""
        if not self.records:
            return {"ok": False, "error": "无记录"}

        last = self.records[-1]
        checks = {
            "has_timestamp": "timestamp" in last,
            "has_evidence": bool(last.get("evidence")),
            "is_verifiable": last.get("verifiable", False),
            "has_action": bool(last.get("action")),
            "evidence_keys": list(last.get("evidence", {}).keys())
        }

        return {
            "ok": all(checks.values()),
            "record_id": last["seq"],
            "action": last["action"],
            "checks": checks,
            "verdict": "✅ 真实执行" if all(checks.values()) else "❌ 证据不足"
        }

    def verify_session(self) -> dict:
        """核查整条会话的执行真实性"""
        total = len(self.records)
        if total == 0:
            return {"ok": False, "error": "空会话，无执行记录"}

        verifiable = sum(1 for r in self.records if r.get("verifiable"))
        unverifiable = total - verifiable
        phases_covered = set(r.get("phase", "") for r in self.records)

        # 检查证据链闭合
        chain_ok = self._check_chain()

        return {
            "ok": verifiable == total and chain_ok,
            "total_actions": total,
            "verifiable": verifiable,
            "unverifiable": unverifiable,
            "verifiability_pct": round(verifiable / total * 100, 1),
            "phases_covered": sorted(phases_covered),
            "chain_closed": chain_ok,
            "fakes_detected": unverifiable,
            "verdict": "✅ 全部可查" if verifiable == total else f"⚠️ {unverifiable}条记录证据不足"
        }

    def _check_chain(self) -> bool:
        """检查证据链是否闭合(简化版: 连续记录之间有无断点)"""
        if len(self.records) < 2:
            return True
        # 相邻记录时间间隔不超过60秒视为连续
        for i in range(1, len(self.records)):
            gap = self.records[i]["timestamp"] - self.records[i-1]["timestamp"]
            if gap > 300:  # 超过5分钟可能是假执行间隙
                return False
        return True

    # ── 假执行检测 ────────────────────────────

    def detect_fakes(self) -> list:
        """检测可能的假执行"""
        fakes = []
        for r in self.records:
            reasons = []
            if not r.get("verifiable"):
                reasons.append("无可验证证据")
            if not r.get("evidence"):
                reasons.append("证据为空")
            if r.get("evidence") == {} or r.get("evidence") == {"ok": True}:
                reasons.append("证据过于简单(可能伪造)")
            if reasons:
                fakes.append({"record_id": r["seq"], "action": r["action"], 
                             "reasons": reasons})
        return fakes

    # ── 报告 ──────────────────────────────────

    def report(self) -> str:
        """生成可读审计报告"""
        v = self.verify_session()
        lines = [
            "=" * 50,
            f"GBT 执行审计报告",
            f"会话: {self.session_id}",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"总操作: {v['total_actions']} | 可查: {v['verifiable']} | 可疑: {v['unverifiable']}",
            f"可查率: {v['verifiability_pct']}% | 证据链: {'闭合' if v['chain_closed'] else '断裂'}",
            "=" * 50,
            "",
            "执行记录:"
        ]
        for r in self.records[-20:]:  # 最近20条
            status = "✅" if r.get("verifiable") else "❌"
            action = r["action"][:50]
            evidence_summary = ", ".join(list(r.get("evidence", {}).keys())[:3])
            lines.append(f"  {status} #{r['seq']} {action} [{evidence_summary}]")

        fakes = self.detect_fakes()
        if fakes:
            lines.append("")
            lines.append("⚠️ 可疑记录:")
            for f in fakes:
                lines.append(f"  ❌ #{f['record_id']} {f['action'][:40]}: {', '.join(f['reasons'])}")

        lines.append("")
        lines.append(f"裁决: {v['verdict']}")
        return "\n".join(lines)


# 全局
_trail: Optional[AuditTrail] = None

def get_trail() -> AuditTrail:
    global _trail
    if _trail is None:
        _trail = AuditTrail()
    return _trail


def log(action: str, evidence: dict, instruction: str = "", phase: str = ""):
    """快捷记录"""
    return get_trail().log(action, evidence, instruction, phase)


def verify() -> dict:
    """快捷核查"""
    return get_trail().verify_session()
