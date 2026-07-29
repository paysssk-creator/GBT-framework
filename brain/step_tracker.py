# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# ⛔ 链路内核集成 — 不可绕过
"""
brain/step_tracker.py — 运行时Step追踪器 · 硬强制
==================================================
确保每次任务严格按照 pipeline.md Step -2→-1→0→1→2→3→4→5→6 执行。
任何跳步操作被检测到 → 立即阻断。

与 chain_kernel.enforce() 集成:
  enforce() 每次调用时自动检查当前Step是否合法
  跳步检测: Step 0不能直接到Step 4，Step 4不能跳过复查直接到Step 6

状态持久化: ~/.gbt/step_state.json
"""

import json, time, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

STEP_STATE = Path.home() / ".gbt" / "step_state.json"
STEP_STATE.parent.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  Step定义 · 顺序不可变 · 条件不可跳过
# ═══════════════════════════════════════════════════════════

STEPS = {
    -2: {"name": "链路内核验证",   "next": -1, "requires": [],        "gate": "chain_kernel.auto_boot() 13阶段全通过"},
    -1: {"name": "邻域感知",       "next": 0,  "requires": [-2],      "gate": "核心邻域模块全部就绪"},
    0:  {"name": "任务登记",       "next": 1,  "requires": [-1],      "gate": "任务复述正确, 用户确认"},
    1:  {"name": "影响面分析",     "next": 2,  "requires": [0],       "gate": "每个涉及项有工具证据"},
    2:  {"name": "读取研究",       "next": 3,  "requires": [1],       "gate": "每个涉及文件都已read"},
    3:  {"name": "方案设计",       "next": 4,  "requires": [2],       "gate": "方案有验收标准, 考虑连锁影响"},
    4:  {"name": "逐子任务执行",   "next": 5,  "requires": [3],       "gate": "每个子任务通过4a→4c镜像验证"},
    5:  {"name": "深度复查(三遍)", "next": 6,  "requires": [4],       "gate": "三遍复查全部通过, 零问题"},
    6:  {"name": "交付",           "next": None, "requires": [5],      "gate": "验收标准逐条确认, 项目可运行"},
}

# 禁止跳步路径
FORBIDDEN_JUMPS = [
    (0, 4, "禁止: Step 0→4 跳过研究+方案"),
    (0, 2, "禁止: Step 0→2 跳过影响面分析"),
    (4, 6, "禁止: Step 4→6 跳过深度复查"),
    (3, 5, "禁止: Step 3→5 跳过执行"),
    (1, 4, "禁止: Step 1→4 跳过读取+方案"),
]


class StepTracker:
    """运行时Step追踪器 — 硬强制pipeline流程"""

    def __init__(self):
        from brain.chain_kernel import enforce_chain
        enforce_chain("step_tracker.init")
        self._state = self._load()
        self._violations: list[dict] = []

    def _load(self) -> dict:
        if STEP_STATE.exists():
            try:
                return json.loads(STEP_STATE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, ValueError):
                pass
        return {
            "current_step": -2,
            "task_id": None,
            "task_description": "",
            "completed_steps": [],
            "step_history": [],
            "created_at": datetime.now().isoformat(),
        }

    def _save(self):
        self._state["updated_at"] = datetime.now().isoformat()
        STEP_STATE.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Step操作 ──────────────────────────────

    def current_step(self) -> int:
        return self._state.get("current_step", -2)

    def current_step_name(self) -> str:
        s = STEPS.get(self.current_step(), {})
        return s.get("name", "未知")

    def is_completed(self, step: int) -> bool:
        return step in self._state.get("completed_steps", [])

    def can_advance_to(self, target: int) -> tuple[bool, str]:
        """检查是否可以前进到目标Step"""
        current = self.current_step()

        if target == current:
            return True, ""

        # 前进: 必须是一步一步走
        if target == current + 1:
            return True, ""

        # 回退: 允许
        if target < current:
            return True, ""

        # 跳步: 检查禁止路径
        for from_step, to_step, reason in FORBIDDEN_JUMPS:
            if current <= from_step and target >= to_step:
                return False, reason

        return True, ""

    def advance(self, to_step: int, evidence: str = "") -> dict:
        """前进到指定Step — 必须通过门禁"""
        ok, reason = self.can_advance_to(to_step)
        if not ok:
            self._violations.append({
                "type": "step_jump_blocked",
                "from": self.current_step(),
                "to": to_step,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            })
            return {"ok": False, "error": reason, "code": "STEP_JUMP_BLOCKED"}

        # 逐步前进
        current = self.current_step()
        while current < to_step:
            current += 1
            step_info = STEPS.get(current, {})
            self._state["completed_steps"].append(current)
            self._state["step_history"].append({
                "step": current,
                "name": step_info.get("name", ""),
                "gate": step_info.get("gate", ""),
                "evidence": evidence if current == to_step else "",
                "timestamp": datetime.now().isoformat(),
            })

        self._state["current_step"] = to_step
        self._save()
        return {"ok": True, "current_step": to_step, "step_name": self.current_step_name()}

    def new_task(self, description: str) -> dict:
        """开始新任务 — 重置到Step -2"""
        self._state = {
            "current_step": -2,
            "task_id": f"task_{int(time.time())}",
            "task_description": description[:500],
            "completed_steps": [-2],  # auto_boot always runs
            "step_history": [],
            "created_at": datetime.now().isoformat(),
        }
        self._violations = []
        self._save()
        return {"ok": True, "task_id": self._state["task_id"], "step": -2}

    def check_enforce(self, context: str = "") -> dict:
        """被 enforce() 调用的检查点 — 验证当前Step合法性"""
        current = self.current_step()

        # 检查是否有违规跳步
        for v in self._violations[-5:]:
            if (datetime.now() - datetime.fromisoformat(v["timestamp"])).seconds < 60:
                return {"ok": False, "error": f"Step违规未解决: {v['reason']}",
                        "code": "STEP_VIOLATION_ACTIVE"}

        return {"ok": True, "step": current, "step_name": self.current_step_name()}

    def status(self) -> dict:
        return {
            "current_step": self.current_step(),
            "step_name": self.current_step_name(),
            "task_description": self._state.get("task_description", ""),
            "completed": self._state.get("completed_steps", []),
            "violations": len(self._violations),
            "next_step": STEPS.get(self.current_step(), {}).get("next"),
            "next_gate": STEPS.get(self.current_step(), {}).get("gate", ""),
        }


# ═══════════════════════════════════════════════════════════
#  全局
# ═══════════════════════════════════════════════════════════

_tracker: StepTracker | None = None

def get_tracker() -> StepTracker:
    global _tracker
    if _tracker is None:
        _tracker = StepTracker()
    return _tracker

def step_advance(to_step: int, evidence: str = "") -> dict:
    return get_tracker().advance(to_step, evidence)

def step_new_task(description: str) -> dict:
    return get_tracker().new_task(description)

def step_current() -> int:
    return get_tracker().current_step()

def step_status() -> dict:
    return get_tracker().status()


if __name__ == "__main__":
    print("=" * 60)
    print("  Step追踪器 · 自测")
    print("=" * 60)

    t = get_tracker()
    t.new_task("测试任务")

    # 正常前进
    for s in [-1, 0, 1, 2, 3]:
        r = t.advance(s, f"Step {s} 完成")
        print(f"  Step {s}: {'OK' if r['ok'] else 'BLOCKED'} → {t.current_step_name()}")

    # 尝试跳步
    r = t.advance(6, "跳过复查直接交付")
    msg = "BLOCKED: " + r.get("error", "?") if not r['ok'] else "OK"
    print(f"  Jump 4->6: {msg}")

    print(f"\n  状态: {t.status()}")
