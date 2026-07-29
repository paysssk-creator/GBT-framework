# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""human_task/run.py — Human-in-the-Loop 人类任务委托引擎
==========================================================
学习HumanAPI设计模式: AI Agent可编程调用人类劳动力市场。

三通道:
  ① HumanAPI集成 — 调用thehumanapi.com marketplace
  ② 本地任务队列 — 通过Telegram/Slack发送给人类审批者
  ③ 自动审批 — 低风险任务自动流转

设计理念: GBT无法完成的物理世界任务 → 委托给真实人类 → 结果回传
"""
import sys, json, os, time, urllib.request, urllib.error, subprocess
from pathlib import Path
from datetime import datetime, timezone

SANDBOX = Path(__file__).parent.parent
TASK_DIR = Path.home() / ".gbt" / "human_tasks"
TASK_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  HumanAPI 集成 (thehumanapi.com)
# ═══════════════════════════════════════════════════════════

HUMANAPI_KEY = os.environ.get("HUMANAPI_KEY", "")
HUMANAPI_BASE = "https://api.thehumanapi.com/v1"

def _humanapi(endpoint, method="GET", data=None):
    if not HUMANAPI_KEY:
        return None, "HUMANAPI_KEY未设置 (https://thehumanapi.com 注册获取)"
    url = f"{HUMANAPI_BASE}/{endpoint}"
    headers = {"Authorization": f"Bearer {HUMANAPI_KEY}", "Content-Type": "application/json"}
    body = json.dumps(data).encode() if data else None
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        return resp, None
    except Exception as e:
        return None, str(e)[:200]

# ═══════════════════════════════════════════════════════════
#  任务类型定义 (对标HumanAPI use cases)
# ═══════════════════════════════════════════════════════════

TASK_TYPES = {
    "audio_recording": {
        "name": "音频录制", "category": "everyday_audio",
        "description": "需要真人录制多语言/多口音音频",
        "required_skills": ["native speaker", "quiet environment"],
        "estimated_minutes": 5, "base_reward_usd": 2.00,
    },
    "image_capture": {
        "name": "实景拍摄", "category": "physical_observability",
        "description": "需要真人拍摄特定场景/物体照片",
        "required_skills": ["smartphone camera"],
        "estimated_minutes": 3, "base_reward_usd": 1.50,
    },
    "document_review": {
        "name": "文档审核", "category": "human_action",
        "description": "需要人类专家审核文档/合同",
        "required_skills": ["legal/professional knowledge"],
        "estimated_minutes": 15, "base_reward_usd": 5.00,
    },
    "data_labeling": {
        "name": "数据标注", "category": "human_action",
        "description": "需要人工标注训练数据",
        "required_skills": ["attention to detail"],
        "estimated_minutes": 10, "base_reward_usd": 3.00,
    },
    "physical_verification": {
        "name": "实地验证", "category": "human_action",
        "description": "需要真人到特定地点验证信息",
        "required_skills": ["local presence"],
        "estimated_minutes": 30, "base_reward_usd": 10.00,
    },
    "expert_consultation": {
        "name": "专家咨询", "category": "human_action",
        "description": "需要领域专家提供判断/建议",
        "required_skills": ["domain expertise"],
        "estimated_minutes": 20, "base_reward_usd": 8.00,
    },
    "translation_review": {
        "name": "翻译校对", "category": "everyday_audio",
        "description": "需要双语者校对机器翻译质量",
        "required_skills": ["bilingual"],
        "estimated_minutes": 10, "base_reward_usd": 3.00,
    },
    "captcha_solve": {
        "name": "验证码解决", "category": "human_action",
        "description": "需要人类解决AI无法处理的验证码",
        "required_skills": ["none"],
        "estimated_minutes": 1, "base_reward_usd": 0.10,
    },
}

# ═══════════════════════════════════════════════════════════
#  动作处理
# ═══════════════════════════════════════════════════════════

def do_create_task(params):
    """创建人类任务"""
    task_type = params.get("type", "data_labeling")
    title = params.get("title", params.get("description", ""))
    instructions = params.get("instructions", params.get("detail", ""))
    reward = params.get("reward_usd", None)
    deadline_hours = params.get("deadline_hours", 24)
    
    if not title:
        return {"ok": False, "error": "缺少title/description参数"}
    
    ttype = TASK_TYPES.get(task_type, TASK_TYPES["data_labeling"])
    
    task = {
        "task_id": f"ht_{int(time.time())}",
        "type": task_type,
        "category": ttype["category"],
        "title": title[:200],
        "instructions": instructions[:2000],
        "reward_usd": reward or ttype["base_reward_usd"],
        "estimated_minutes": ttype["estimated_minutes"],
        "deadline_hours": deadline_hours,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "required_skills": ttype["required_skills"],
    }
    
    # 持久化
    task_file = TASK_DIR / f"{task['task_id']}.json"
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # 尝试HumanAPI提交
    humanapi_result = None
    if HUMANAPI_KEY:
        resp, err = _humanapi("tasks", "POST", {
            "title": title, "instructions": instructions,
            "category": ttype["category"], "reward_usd": task["reward_usd"],
        })
        if resp:
            task["humanapi_id"] = resp.get("id", "")
            humanapi_result = {"submitted": True, "id": resp.get("id", "")}
    
    # 同时通过沟通渠道通知
    _notify_humans(task)
    
    return {"ok": True, "task": task, "humanapi": humanapi_result,
            "available_types": list(TASK_TYPES.keys()),
            "note": "任务已创建, 等待人类接单"}

def _notify_humans(task):
    """通过Telegram/Slack通知人类审批者"""
    message = f"📋 新任务 #{task['task_id'][-6:]}: {task['title'][:100]}\n💰 ${task['reward_usd']} | ⏱ {task['estimated_minutes']}min"
    try:
        r = subprocess.run(
            [sys.executable, str(SANDBOX / "slack_bot" / "run.py"), "send_slack",
             json.dumps({"channel": os.environ.get("SLACK_REVIEW_CHANNEL", "general"), "text": message})],
            capture_output=True, text=True, timeout=10
        )
    except:
        pass

def do_list_tasks(params):
    """列出任务"""
    status = params.get("status", "all")
    tasks = []
    for f in sorted(TASK_DIR.glob("ht_*.json"), reverse=True):
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
            if status == "all" or t.get("status") == status:
                tasks.append({"task_id": t["task_id"], "title": t["title"][:100],
                             "status": t["status"], "reward": t["reward_usd"]})
        except:
            pass
    return {"ok": True, "tasks": tasks[:20], "total": len(tasks), "dir": str(TASK_DIR)}

def do_complete_task(params):
    """标记任务完成(人类提交结果后)"""
    task_id = params.get("task_id", "")
    result = params.get("result", {})
    
    task_file = TASK_DIR / f"{task_id}.json"
    if not task_file.exists():
        return {"ok": False, "error": f"任务{task_id}不存在"}
    
    task = json.loads(task_file.read_text(encoding="utf-8"))
    task["status"] = "completed"
    task["result"] = result
    task["completed_at"] = datetime.now(timezone.utc).isoformat()
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # 记录到认知库
    try:
        from brain.cognition import get_cognition
        get_cognition().record_discovery(
            topic=f"人类任务完成: {task.get('title','')[:100]}",
            description=f"类型: {task.get('type','')} | 奖励: ${task.get('reward_usd',0)} | 结果: {json.dumps(result,ensure_ascii=False)[:200]}",
            source="human_task", evidence=f"task_id={task_id}",
            tags=["human_in_the_loop", task.get("type",""), "completed"],
            confidence=1.0
        )
    except:
        pass
    
    return {"ok": True, "task_id": task_id, "status": "completed"}

def do_types(params):
    """列出所有支持的任务类型"""
    return {"ok": True, "types": {k: {"name": v["name"], "category": v["category"], "reward": v["base_reward_usd"], "minutes": v["estimated_minutes"]} for k, v in TASK_TYPES.items()}, "count": len(TASK_TYPES)}

def do_status(params):
    """HumanAPI集成状态 + 任务统计"""
    stats = {"pending": 0, "in_progress": 0, "completed": 0}
    for f in TASK_DIR.glob("ht_*.json"):
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
            s = t.get("status", "pending")
            stats[s] = stats.get(s, 0) + 1
        except:
            pass
    
    api_status = "connected" if HUMANAPI_KEY else "not_configured"
    return {"ok": True, "humanapi": api_status, "tasks_dir": str(TASK_DIR), "stats": stats,
            "note": "配置HUMANAPI_KEY接入thehumanapi.com市场" if not HUMANAPI_KEY else "HumanAPI已连接"}

HANDLERS = {
    "create": do_create_task, "list": do_list_tasks,
    "complete": do_complete_task, "types": do_types, "status": do_status,
    "run": do_create_task,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "types"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except:
            params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
