# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/session_resume.py — 会话状态持久化
=========================================
跨进程重启的会话恢复机制。每次编排器任务状态变更时
自动保存 TaskGraph 到 ~/.gbt/sessions/，重启时恢复。

用法:
  from brain.session_resume import resume, save_session
  status = resume()              # 启动时检查
  save_session(orchestrator)     # 状态变更时保存
"""
import json, time, logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

L = logging.getLogger("SessionResume")

SESSION_DIR = Path.home() / ".gbt" / "sessions"
SESSION_FILE = SESSION_DIR / "last_session.json"

def _serialize_value(obj):
    """安全序列化 — 处理 datetime/Path 等非基本类型"""
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, (Path,)):
        return str(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return repr(obj)[:200]  # 最后兜底，不静默丢失


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
def save_session(orchestrator, project_state: Optional[dict] = None):
    """持久化当前编排器 TaskGraph + 项目状态到磁盘。

    在每次 submit / run_cycle / complete_task 后自动调用。
    """
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    # 提取 TaskGraph 可序列化状态
    graph = None
    if hasattr(orchestrator, 'graph'):
        graph = orchestrator.graph

    tasks_data = []
    current_id = 0
    if graph is not None:
        tasks_data = list(graph.tasks)
        current_id = graph.current_id

    payload = {
        "version": 1,
        "last_session_time": _now_iso(),
        "orchestrator": {
            "tasks": tasks_data,
            "current_id": current_id,
        },
        "project_state": project_state or {},
    }
    try:
        SESSION_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=_serialize_value),
            encoding="utf-8"
        )
    except Exception as e:
        L.warning(f"保存会话状态失败: {e}")


def resume() -> dict:
    """检查并加载上一次会话状态。

    返回:
      {resumed: bool, last_task: str|None,
       pending_tasks: int, last_session_time: str|None}
    """
    if not SESSION_FILE.exists():
        return {
            "resumed": False,
            "last_task": None,
            "pending_tasks": 0,
            "last_session_time": None,
        }

    try:
        raw = SESSION_FILE.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError) as e:
        L.warning(f"会话文件损坏，将重建: {e}")
        return {
            "resumed": False,
            "last_task": None,
            "pending_tasks": 0,
            "last_session_time": None,
        }

    orch = data.get("orchestrator", {})
    tasks = orch.get("tasks", [])

    pending = sum(1 for t in tasks if t.get("status") == "pending")
    in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")

    last_task = None
    if tasks:
        sorted_tasks = sorted(tasks, key=lambda t: t.get("created_at", 0),
                              reverse=True)
        last_task = sorted_tasks[0].get("task_id")

    return {
        "resumed": True,
        "last_task": last_task,
        "pending_tasks": pending + in_progress,
        "last_session_time": data.get("last_session_time"),
    }


def load_graph_into(orchestrator) -> bool:
    """将上次持久化的 TaskGraph 恢复到编排器中。

    仅在 resume() 发现残留待处理任务时调用。
    返回 True 表示有任务被恢复。
    """
    if not SESSION_FILE.exists():
        return False

    try:
        raw = SESSION_FILE.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return False

    orch_data = data.get("orchestrator", {})
    saved_tasks = orch_data.get("tasks", [])
    saved_cur_id = orch_data.get("current_id", 0)

    active_statuses = {"pending", "in_progress"}
    restorable = [t for t in saved_tasks if t.get("status") in active_statuses]

    if not restorable:
        return False

    graph = orchestrator.graph
    existing_ids = {t["task_id"] for t in graph.tasks}

    restored_count = 0
    for task in restorable:
        tid = task.get("task_id", "")
        if tid in existing_ids:
            continue
        # 重置为 pending（放弃 in_progress 状态 — 进程已重启）
        task["status"] = "pending"
        task.pop("started_at", None)
        task["fingerprints"] = task.get("fingerprints", [])
        graph.tasks.append(task)
        restored_count += 1

    graph.current_id = max(graph.current_id, saved_cur_id)
    L.info(f"🔄 恢复 {restored_count} 个未完成任务到编排器")
    return True


# ━━━ 编排器钩子 ━━━
# 在 Orchestrator 的 submit/run_cycle/complete_task 之后调用

_patched_orchestrator = False


def hook_orchestrator(orchestrator):
    """注入会话持久化钩子到编排器。

    包装 submit / run_cycle / complete_task，使每次状态变更后自动保存。
    """
    global _patched_orchestrator
    if _patched_orchestrator:
        return
    _patched_orchestrator = True

    orig_submit = orchestrator.submit
    orig_run_cycle = orchestrator.run_cycle
    orig_complete_task = orchestrator.complete_task

    def _submit(*args, **kwargs):
        result = orig_submit(*args, **kwargs)
        try:
            save_session(orchestrator)
        except Exception:
            pass
        return result

    def _run_cycle(*args, **kwargs):
        result = orig_run_cycle(*args, **kwargs)
        status = result.get("status", "")
        if status in ("in_progress", "blocked", "failed"):
            try:
                save_session(orchestrator)
            except Exception:
                pass
        return result

    def _complete_task(*args, **kwargs):
        result = orig_complete_task(*args, **kwargs)
        try:
            save_session(orchestrator)
        except Exception:
            pass
        return result

    orchestrator.submit = _submit
    orchestrator.run_cycle = _run_cycle
    orchestrator.complete_task = _complete_task


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] %(message)s",
                        datefmt="%H:%M:%S")
    status = resume()
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if status["resumed"]:
        L.info(f"上次会话: {status['last_session_time']}, "
               f"{status['pending_tasks']} 个待处理任务")
