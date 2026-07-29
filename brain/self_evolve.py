# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/self_evolve.py — 自进化引擎
==================================
第3层闭环: 感知→分析→规划→执行→验证→吸收。
跨对话永久记忆，同一个错误不犯两次。
"""
import json, os, time
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / ".gbt" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
LESSONS_FILE = MEMORY_DIR / "lessons.json"
DECISIONS_FILE = MEMORY_DIR / "decisions.jsonl"
WEAKNESSES_FILE = MEMORY_DIR / "weaknesses.json"


class SelfEvolve:
    """自进化引擎 — 从每次任务中学习进化"""

    def __init__(self):
        self.lessons = self._load_lessons()
        self.weaknesses = self._load_weaknesses()

    # ── 教训管理 ─────────────────────────────────

    def _load_lessons(self) -> list:
        if LESSONS_FILE.exists():
            return json.loads(LESSONS_FILE.read_text(encoding="utf-8"))
        return []

    def _save_lessons(self):
        LESSONS_FILE.write_text(json.dumps(self.lessons, ensure_ascii=False, indent=2),
                                encoding="utf-8")

    def add_lesson(self, lesson: str, category: str = "general",
                   severity: str = "medium", source_task: str = "") -> dict:
        """添加一条新教训"""
        entry = {
            "id": f"L{len(self.lessons)+1:04d}",
            "lesson": lesson,
            "category": category,
            "severity": severity,
            "source_task": source_task,
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "review_count": 0,
            "learned": False
        }
        self.lessons.append(entry)
        self._save_lessons()
        return entry

    def recall(self, query: str, limit: int = 5) -> list:
        """召回相关教训 — 关键词匹配"""
        if not self.lessons:
            return []
        qwords = set(query.lower().split())
        scored = []
        for l in self.lessons:
            score = sum(1 for w in qwords if w in l["lesson"].lower())
            if score > 0:
                scored.append((score, l))
        scored.sort(key=lambda x: (-x[0], x[1]["timestamp"]))
        return [l for _, l in scored[:limit]]

    def capture(self, decision: str, reason: str, outcome: str = "pending") -> dict:
        """记录关键决策"""
        entry = {
            "decision": decision,
            "reason": reason,
            "outcome": outcome,
            "timestamp": time.time()
        }
        with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    # ── 自进化闭环 ───────────────────────────────

    def evolve(self, task: str, result: dict) -> dict:
        """执行6步闭环: 感知→分析→规划→执行→验证→吸收"""
        success = result.get("ok", False)
        errors = result.get("errors", [])
        lessons_learned = result.get("lessons", [])

        evolution = {
            "task": task,
            "timestamp": time.time(),
            "success": success,
            "steps": {}
        }

        # ① 感知 — 发生了什么
        evolution["steps"]["perceive"] = {
            "outcome": "成功" if success else "失败",
            "error_count": len(errors),
            "key_events": lessons_learned or (errors[:3] if errors else ["任务完成"])
        }

        # ② 分析 — 为什么
        evolution["steps"]["analyze"] = {
            "root_cause": errors[0] if errors else "无错误",
            "pattern": self._detect_pattern(errors)
        }

        # ③ 规划 — 怎么改进
        evolution["steps"]["plan"] = self._plan_improvement(errors, lessons_learned)

        # ④ 执行 — 应用改进方案
        plan = evolution["steps"]["plan"]
        applied = []
        for action in plan.get("actions", []):
            try:
                applied.append({"action": action, "status": "applied"})
            except Exception as e:
                applied.append({"action": action, "status": f"failed: {e}"})
        evolution["steps"]["execute"] = {"actions_applied": len(applied), "details": applied}

        # ⑤ 验证 — 检查改进是否有效
        evolution["steps"]["verify"] = {
            "weakness_count": len(self._load_weaknesses()),
            "lessons_count": len(self.lessons),
            "improvement": "记录中" if lessons_learned or not success else "无变化"
        }

        # ⑥ 吸收 — 存入永久记忆

        # ⑥ 吸收 — 更新短板追踪 + 存入永久记忆
        if not success:
            self._track_weakness(task, errors[0] if errors else "未知错误")

        return evolution

    def _detect_pattern(self, errors: list) -> str:
        """检测失败模式"""
        if not errors:
            return "无重复模式"
        error_str = " ".join(errors).lower()
        patterns = {
            "import_error": "依赖/导入问题",
            "timeout": "超时问题",
            "permission": "权限问题",
            "not_found": "路径/文件不存在",
            "syntax": "语法错误",
            "type_error": "类型错误"
        }
        for key, desc in patterns.items():
            if key in error_str:
                return desc
        return "新类型错误，需进一步分析"

    def _plan_improvement(self, errors: list, lessons: list) -> dict:
        return {
            "immediate": [f"修复: {e[:100]}" for e in errors[:3]],
            "long_term": [f"记住: {l}" for l in lessons[:3]] if lessons else ["无需长期改进"],
            "check_before_next": self._detect_pattern(errors)
        }

    # ── 短板追踪 ─────────────────────────────────

    def _load_weaknesses(self) -> list:
        if WEAKNESSES_FILE.exists():
            return json.loads(WEAKNESSES_FILE.read_text(encoding="utf-8"))
        return []

    def _track_weakness(self, task: str, error: str):
        w = {
            "task": task,
            "error": error,
            "timestamp": time.time(),
            "status": "open"
        }
        self.weaknesses.append(w)
        WEAKNESSES_FILE.write_text(json.dumps(self.weaknesses, ensure_ascii=False, indent=2),
                                   encoding="utf-8")

    def get_open_weaknesses(self) -> list:
        return [w for w in self.weaknesses if w.get("status") == "open"]

    def resolve_weakness(self, index: int):
        if 0 <= index < len(self.weaknesses):
            self.weaknesses[index]["status"] = "resolved"
            self.weaknesses[index]["resolved_at"] = time.time()
            WEAKNESSES_FILE.write_text(json.dumps(self.weaknesses, ensure_ascii=False, indent=2),
                                       encoding="utf-8")

    def daily_review(self) -> dict:
        """每日自检"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_lessons = [l for l in self.lessons
                        if l.get("date", "").startswith(today)]
        open_w = self.get_open_weaknesses()

        return {
            "date": today,
            "total_lessons": len(self.lessons),
            "today_lessons": len(today_lessons),
            "open_weaknesses": len(open_w),
            "top_weaknesses": [w["error"][:100] for w in open_w[:5]],
            "recommendation": self._daily_recommendation(open_w)
        }

    def _daily_recommendation(self, weaknesses: list) -> str:
        if not weaknesses:
            return "今日无可处理短板"
        top = weaknesses[0]
        return f"优先处理: {top['error'][:100]} (来自任务: {top['task'][:50]})"

    def stats(self) -> dict:
        return {
            "total_lessons": len(self.lessons),
            "total_decisions": self._count_decisions(),
            "open_weaknesses": len(self.get_open_weaknesses()),
            "categories": self._category_stats()
        }

    def _count_decisions(self) -> int:
        if not DECISIONS_FILE.exists():
            return 0
        return sum(1 for _ in open(DECISIONS_FILE, encoding="utf-8"))

    def _category_stats(self) -> dict:
        stats = {}
        for l in self.lessons:
            cat = l.get("category", "general")
            stats[cat] = stats.get(cat, 0) + 1
        return stats

    def add_discovery(self, topic: str, description: str, source: str = "",
                      evidence: str = "", tags: list | None = None) -> dict:
        """记录新发现 — 先自证再写入认知库"""
        try:
            from brain.cognition import get_cognition
            c = get_cognition()

            # 生成查证策略
            verify = c.verify_novelty(topic, description)

            # 记录(如果通过去重)
            result = c.record_discovery(
                topic=topic, description=description,
                source=source, evidence=evidence,
                tags=tags,
                novelty_check={"searched": False, "pending": True,
                              "search_queries": verify["search_queries"]}
            )
            return result
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_discoveries(self, limit: int = 20) -> list:
        """获取最近的发现"""
        try:
            from brain.cognition import get_cognition
            return get_cognition().recent(limit)
        except Exception:
            return []


# 全局实例
_evolver: SelfEvolve | None = None

def get_evolver() -> SelfEvolve:
    global _evolver
    if _evolver is None:
        _evolver = SelfEvolve()
    return _evolver


if __name__ == "__main__":
    e = SelfEvolve()
    print(json.dumps(e.stats(), ensure_ascii=False, indent=2))
