# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/orchestrator.py — 任务编排引擎
=====================================
四脑协作的执行层。接收推理脑的方向建议，
拆解为子任务，调度编程脑执行，裁判验证结果。

流程: 任务入队 → 推理脑分析 → 编程脑方案 → GBT执行 → 裁判验证
"""
import json, time, hashlib, threading, logging
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).parent.parent
log = logging.getLogger("Orchestrator")

# 熔断配置
MAX_ATTEMPTS = 5
WATCHDOG_TIMEOUT_S = 300


class TaskGraph:
    """任务图 — 管理任务状态和依赖"""

    def __init__(self):
        self.tasks: list[dict] = []
        self.current_id = 0

    def add(self, description: str, priority: str = "medium",
            depends_on: list | None = None) -> dict:
        self.current_id += 1
        task = {
            "task_id": f"T{self.current_id:04d}",
            "description": description,
            "priority": priority,
            "status": "pending",
            "depends_on": depends_on or [],
            "attempts": 0,
            "created_at": time.time(),
            "fingerprints": []
        }
        self.tasks.append(task)
        return task

    def get_next_pending(self) -> Optional[dict]:
        for t in sorted(self.tasks, key=lambda x: (
            0 if x["priority"] == "high" else 1 if x["priority"] == "medium" else 2,
            x["created_at"]
        )):
            if t["status"] == "pending":
                deps_done = all(
                    any(dt["task_id"] == dep and dt["status"] == "done"
                        for dt in self.tasks)
                    for dep in t["depends_on"]
                )
                if deps_done:
                    return t
        return None

    def update(self, task_id: str, **kwargs):
        for t in self.tasks:
            if t["task_id"] == task_id:
                t.update(kwargs)
                return t
        return None

    def fingerprint(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def detect_stall(self, task: dict, current_state: str) -> bool:
        fp = self.fingerprint(current_state)
        if fp in task.get("fingerprints", []):
            task["fingerprints"].append(fp)
            return len([f for f in task["fingerprints"] if f == fp]) >= 3
        task.setdefault("fingerprints", []).append(fp)
        return False

    def progress(self) -> dict:
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t["status"] == "done")
        failed = sum(1 for t in self.tasks if t["status"] == "failed")
        return {"total": total, "done": done, "failed": failed,
                "pending": total - done - failed}


class Judge:
    """裁判 — 非LLM验证，唯一"完成"判定"""

    @staticmethod
    def verify(task: dict, result: dict, acceptance_criteria: list) -> tuple[bool, str]:
        """验证任务是否完成"""
        if not result.get("ok", False):
            return False, f"执行失败: {result.get('error', '未知错误')}"

        for i, criterion in enumerate(acceptance_criteria):
            if not Judge._check_criterion(criterion, result):
                return False, f"验收标准[{i}]不满足: {criterion}"

        return True, "全部验收标准满足"

    @staticmethod
    def _check_criterion(criterion: str, result: dict) -> bool:
        """检查单个验收标准"""
        c = criterion.lower()
        output = json.dumps(result).lower()
        if "编译" in c or "compile" in c:
            return "error" not in output[:500]
        if "返回" in c or "return" in c or "输出" in c or "output" in c:
            return "output" in result or "result" in result
        if "不报错" in c or "no error" in c:
            return result.get("ok", False)
        return False  # 无法识别的标准 — 需要明确的验收条件

class Orchestrator:
    """任务编排引擎"""

    def __init__(self):
        self.graph = TaskGraph()
        self.judge = Judge()
        self._nexus = None
        self._start_watchdog()

    def _start_watchdog(self):
        """后台看门狗 — 定期检测并清理超时任务"""
        def _watch():
            while True:
                time.sleep(60)
                try:
                    for t in self.graph.tasks:
                        if t.get("status") == "in_progress":
                            elapsed = time.time() - t.get("started_at", 0)
                            if elapsed > WATCHDOG_TIMEOUT_S:
                                t["status"] = "stale"
                                log.warning(f"⏰ Watchdog: {t['task_id']} 超时({int(elapsed)}s)")
                except Exception:
                    pass
        t = threading.Thread(target=_watch, daemon=True, name="orchestrator-watchdog")
        t.start()
    def _on_state_change(self):
        """会话持久化回调 — session_resume 注入后调用"""
        cb = getattr(self, '_session_save_cb', None)
        if cb:
            try:
                cb(self)
            except Exception:
                pass
    @property
    def nexus(self):
        """延迟加载邻域神经系统"""
        if self._nexus is None:
            try:
                from brain.nexus import get_nexus
                self._nexus = get_nexus()
            except Exception:
                self._nexus = None
        return self._nexus

    def health_check(self) -> dict:
        """邻域健康检查 — 执行任务前验证系统状态"""
        if self.nexus:
            return self.nexus.quick_health()
        return {"ok": True, "note": "邻域中枢未加载"}

    def submit(self, description: str, priority: str = "medium",
               acceptance_criteria: list | None = None) -> dict:
        task = self.graph.add(description, priority)
        task["acceptance_criteria"] = acceptance_criteria or []
        log.info(f"📥 任务入队: {task['task_id']} — {description[:80]}")
        self._on_state_change()
        return task

    def run_cycle(self) -> dict:
        """执行一个完整的编排周期"""
        task = self.graph.get_next_pending()
        if not task:
            self._on_state_change()
            return {"status": "idle", "message": "无待处理任务"}

        task_id = task["task_id"]
        task["status"] = "in_progress"
        task["started_at"] = time.time()
        log.info(f"🔧 开始执行: {task_id}")

        # 检测空转
        if self.graph.detect_stall(task, f"running:{task['attempts']}"):
            task["status"] = "blocked"
            log.warning(f"⛔ {task_id} 空转检测触发")
            self._on_state_change()
            return {"status": "blocked", "task_id": task_id, "reason": "空转(停滞)"}

        # 熔断检查
        if task["attempts"] >= MAX_ATTEMPTS:
            task["status"] = "failed"
            log.error(f"❌ {task_id} 超过最大重试次数")
            self._on_state_change()
            return {"status": "failed", "task_id": task_id,
                    "reason": f"重试{MAX_ATTEMPTS}次仍失败"}

        self._on_state_change()
        return {"status": "in_progress", "task_id": task_id, "task": task}

    def complete_task(self, task_id: str, result: dict) -> dict:
        """标记任务完成，裁判验证"""
        task = self.graph.update(task_id, status="verifying")
        if not task:
            return {"ok": False, "error": f"任务{task_id}不存在"}

        criteria = task.get("acceptance_criteria", [])
        passed, detail = self.judge.verify(task, result, criteria)

        if passed:
            self.graph.update(task_id, status="done", completed_at=time.time())
            log.info(f"✅ {task_id} 完成")
        else:
            task["attempts"] = (task.get("attempts", 0) + 1)
            if task["attempts"] >= MAX_ATTEMPTS:
                self.graph.update(task_id, status="failed")
            else:
                self.graph.update(task_id, status="pending")
            log.warning(f"❌ {task_id} 验证失败: {detail}")

        self._on_state_change()
        return {"ok": passed, "task_id": task_id, "detail": detail,
                "progress": self.graph.progress()}

    def status(self) -> dict:
        return {
            "progress": self.graph.progress(),
            "next_task": self.graph.get_next_pending()
        }


# 全局实例
_orchestrator: Orchestrator | None = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    o = Orchestrator()
    o.submit("示例任务: 创建一个Hello World脚本", "medium",
             ["脚本可运行", "输出Hello World", "不报错"])
    cycle = o.run_cycle()
    print(json.dumps(cycle, ensure_ascii=False, indent=2))
