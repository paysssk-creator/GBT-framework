# -*- coding: utf-8 -*-
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/reasoning_brain.py -- 推理脑 · DeepSeek实时对话通道
=========================================================
GBT三脑架构第一脑: 外部DeepSeek提供推理、方案、策略。

每次询问自动前缀"这是技术层问题"，确保推理聚焦技术方案。

通道特性:
  - 实时对话: 保持会话上下文，支持多轮追问
  - 自动前缀: 所有查询自动加"这是技术层问题"
  - 设计脑接入: 设计脑通过此通道获取推理结果
  - 编程脑接入: 编程脑获取最终方案后执行
"""
import json, os, time, urllib.request, urllib.error
from pathlib import Path
from typing import Optional

# -- 推理脑配置 — 优先从环境变量读取 --
API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("KIMI_API_KEY") or ""
BASE_URL = os.environ.get("GBT_LLM_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("GBT_LLM_MODEL", "deepseek-chat")

# 会话存储 -- 保持对话连续性
CHAT_HISTORY_DIR = Path.home() / ".gbt" / "reasoning_sessions"
CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════ 技术前缀 ═══════════════
TECH_PREFIX = "这是技术层问题："


class ReasoningBrain:
    """推理脑 -- DeepSeek实时对话通道
    
    三脑架构中的第一脑。设计脑通过 ask() 获取推理方案，
    编程脑通过 get_plan() 获取可执行的思维导图。
    
    会话管理铁律:
      - 每个任务独立会话，绝不串话
      - 会话持久化到磁盘，重启不丢
      - 多轮对话保持完整上下文
      - 历史全量可查
    """

    def __init__(self):
        self.api_key = API_KEY
        self.base_url = BASE_URL
        self.model = MODEL
        self._session_id: Optional[str] = None
        self._session_title: str = ""
        self._history: list[dict] = []
        self._turn_count: int = 0

    # ── 会话管理 ──────────────────────────

    def new_session(self, title: str = "") -> str:
        """开启新会话 -- 自动归档旧会话，返回新session_id"""
        # 归档当前会话
        if self._session_id:
            self._save()

        ts = int(time.time())
        self._session_id = f"reason_{ts}"
        self._session_title = title or f"会话_{ts}"
        self._history = []
        self._turn_count = 0

        if title:
            self._history.append({
                "role": "system",
                "content": (
                    f"会话主题: {title}\n"
                    f"你是GBT小土豆的推理脑(第一脑)。\n"
                    f"每次回答必须给出: 方向建议 + 逻辑依据 + 风险评估 + 思维导图。\n"
                    f"输出结构化JSON，不要markdown包裹。"
                )
            })
        self._save()
        return self._session_id

    def load_session(self, session_id: str) -> bool:
        """恢复已有会话 -- 完整加载历史上下文"""
        f = CHAT_HISTORY_DIR / f"{session_id}.json"
        if not f.exists():
            return False
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            # 先归档当前会话
            if self._session_id and self._session_id != session_id:
                self._save()
            self._session_id = session_id
            self._session_title = data.get("title", "")
            self._history = data.get("history", [])
            self._turn_count = data.get("turn_count", len(self._history) // 2)
            return True
        except Exception:
            return False

    def switch_session(self, session_id: str) -> bool:
        """切换到指定会话 -- 不丢当前会话"""
        if not self._session_id:
            return self.load_session(session_id)
        self._save()  # 保存当前
        return self.load_session(session_id)

    def _save(self):
        """持久化当前会话 -- 完整快照"""
        if not self._session_id:
            return
        f = CHAT_HISTORY_DIR / f"{self._session_id}.json"
        f.write_text(json.dumps({
            "session_id": self._session_id,
            "title": self._session_title,
            "timestamp": time.time(),
            "turn_count": self._turn_count,
            "history": self._history,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 会话列表/查询 ──────────────────────

    def list_sessions(self) -> list[dict]:
        """列出所有历史会话 -- 按时间倒序"""
        sessions = []
        for f in sorted(CHAT_HISTORY_DIR.glob("reason_*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                history = data.get("history", [])
                # 提取第一条用户消息作为预览
                preview = ""
                for msg in history:
                    if msg.get("role") == "user":
                        preview = msg["content"].replace(TECH_PREFIX, "")[:100]
                        break
                sessions.append({
                    "session_id": data["session_id"],
                    "title": data.get("title", ""),
                    "timestamp": data.get("timestamp", 0),
                    "turn_count": data.get("turn_count", 0),
                    "message_count": len(history),
                    "preview": preview,
                    "is_active": data["session_id"] == self._session_id,
                })
            except Exception:
                pass
        return sessions

    def get_history(self, session_id: str | None = None) -> dict:
        """查看会话完整记录
        
        Args:
            session_id: 指定会话ID，None=当前会话
        Returns:
            {session_id, title, turns, messages: [{role, content, timestamp}]}
        """
        sid = session_id or self._session_id
        if not sid:
            return {"error": "无活动会话"}

        # 如果是当前会话，直接用内存；否则从磁盘读
        if sid == self._session_id:
            history = self._history
            title = self._session_title
            turns = self._turn_count
        else:
            f = CHAT_HISTORY_DIR / f"{sid}.json"
            if not f.exists():
                return {"error": f"会话不存在: {sid}"}
            data = json.loads(f.read_text(encoding="utf-8"))
            history = data.get("history", [])
            title = data.get("title", "")
            turns = data.get("turn_count", 0)

        # 过滤system消息，只返回对话
        dialogue = []
        for msg in history:
            if msg.get("role") != "system":
                dialogue.append({
                    "role": msg["role"],
                    "content": msg["content"][:500],  # 截断长内容
                    "full_length": len(msg["content"]),
                })

        return {
            "session_id": sid,
            "title": title,
            "turn_count": turns,
            "message_count": len(dialogue),
            "dialogue": dialogue,
        }

    def get_current_session(self) -> dict:
        """获取当前会话信息 -- 避免搞混"""
        if not self._session_id:
            return {"active": False, "message": "无活动会话, 请先 new_session()"}
        return {
            "active": True,
            "session_id": self._session_id,
            "title": self._session_title,
            "turn_count": self._turn_count,
            "message_count": len(self._history),
            "last_activity": self._history[-1]["content"][:100] if self._history else "无",
        }

    def clear_session(self):
        """清除当前会话 -- 不删除磁盘记录"""
        if self._session_id:
            self._save()  # 最后保存
        self._session_id = None
        self._session_title = ""
        self._history = []
        self._turn_count = 0

    def delete_session(self, session_id: str) -> bool:
        """删除指定会话的磁盘记录"""
        f = CHAT_HISTORY_DIR / f"{session_id}.json"
        if f.exists():
            f.unlink()
            if session_id == self._session_id:
                self.clear_session()
            return True
        return False

    # ── 核心对话 ──────────────────────────

    def ask(self, question: str, context: dict | None = None,
            expect_mindmap: bool = True) -> dict:
        """向推理脑提问 -- 自动加技术前缀, 保持多轮上下文

        每次调用自动:
          1. 前缀'这是技术层问题'
          2. 追加到会话历史
          3. 发送完整上下文给DeepSeek
          4. 保存响应
          5. turn_count += 1
        """
        if not self._session_id:
            self.new_session("自动会话")

        if not self.api_key:
            return self._fallback(question)

        full_question = f"{TECH_PREFIX}{question}"

        ctx_block = ""
        if context:
            ctx_block = f"\n\n上下文信息:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        mm_block = ""
        if expect_mindmap:
            mm_block = """
输出要求:
1. direction: 具体行动方向(一句话)
2. rationale: 逻辑依据(3-5条)
3. risks: 风险点列表
4. mindmap: 精细到每一步的思维导图，格式:
   [
     {"step": 1, "action": "具体动作", "tool": "需要的工具/cap名称", "expected": "预期产出", "verify": "验证方法"},
     {"step": 2, ...}
   ]
5. tools_needed: 需要调用的能力模块列表
6. confidence: 0.0-1.0
7. 如果有信息不足，next_question: 追问的问题

返回纯JSON，不要markdown包裹。"""

        prompt = f"{full_question}{ctx_block}{mm_block}"
        self._history.append({"role": "user", "content": prompt})
        self._turn_count += 1

        result = self._call_api()

        if result:
            self._history.append({
                "role": "assistant",
                "content": json.dumps(result, ensure_ascii=False)
            })
            self._save()
        else:
            return self._fallback(question)

        return result

    def follow_up(self, question: str) -> dict:
        """基于当前会话追问 -- 保持完整上下文, 不丢历史"""
        if not self._history:
            return self.ask(question)

        full_question = f"{TECH_PREFIX}{question}"
        self._history.append({"role": "user", "content": full_question})
        self._turn_count += 1

        result = self._call_api()
        if result:
            self._history.append({
                "role": "assistant",
                "content": json.dumps(result, ensure_ascii=False)
            })
            self._save()
        else:
            return self._fallback(question)
        return result

    def _call_api(self) -> dict | None:
        """调用DeepSeek API -- 发送完整会话上下文"""
        try:
            data = json.dumps({
                "model": self.model,
                "messages": self._history[-20:],
                "max_tokens": 2000,
                "temperature": 0.3
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
            content = resp["choices"][0]["message"]["content"]

            parsed = None
            for strategy in [
                lambda c: json.loads(c.strip()),
                lambda c: json.loads(c.strip().removeprefix("```json").removesuffix("```").strip()),
                lambda c: json.loads(c[c.find("{"):c.rfind("}")+1]),
            ]:
                try:
                    parsed = strategy(content)
                    break
                except (json.JSONDecodeError, ValueError):
                    continue

            return parsed or {"direction": content[:200], "rationale": content, "confidence": 0.5}

        except urllib.error.HTTPError as e:
            print(f"[推理脑] API错误 HTTP {e.code}: {e.reason}", flush=True)
            return None
        except Exception as e:
            print(f"[推理脑] 连接失败: {e}", flush=True)
            return None

    def _fallback(self, question: str) -> dict:
        """API不可用时的本地回退"""
        return {
            "direction": f"本地分析: {question[:50]}",
            "rationale": "推理脑API不可用，使用本地关键词匹配",
            "risks": ["API连接失败，推理精度下降"],
            "mindmap": [
                {"step": 1, "action": "检查API连接", "tool": "health_dashboard", "expected": "确认API状态", "verify": "API返回200"},
                {"step": 2, "action": "使用本地推理", "tool": "deep_reasoner", "expected": "本地推理结果", "verify": "结果可用"},
            ],
            "tools_needed": ["health_dashboard", "deep_reasoner"],
            "confidence": 0.3,
            "mode": "fallback"
        }


# ═══════════════ 设计脑接口 ═══════════════

import threading
import logging

_DESIGN_LOG = logging.getLogger("DesignBrain")
PATROL_INTERVAL = 30 * 60  # 30分钟


class DesignBrainInterface:
    """设计脑 -- 三脑架构调度中枢

    职责:
      1. 自主调度: 判断什么时候用什么技能(cap)、什么工具
      2. 推理消化: 拿到推理脑方案 → 分析 → 生成精细思维导图
      3. 邻域巡检: 每30分钟检查神经邻域+感知邻域，确保无失灵/脱节
      4. 卡点处理: 编程脑遇卡点 → 设计脑重新分析 → 必要时再问推理脑
    """

    def __init__(self):
        self.reasoning = ReasoningBrain()
        self._patrol_timer: threading.Timer | None = None
        self._last_patrol: dict = {}
        self._patrol_running = False

    # ── 推理接口 ──────────────────────────

    def query(self, task: str, context: dict | None = None) -> dict:
        """设计脑向推理脑查询 -- 自动前缀'这是技术层问题'"""
        return self.reasoning.ask(task, context=context, expect_mindmap=True)

    def decompose(self, reasoning_result: dict) -> dict:
        """设计脑消化推理结果 → 生成精细思维导图 + 技能/工具调度表"""
        mindmap = reasoning_result.get("mindmap", [])
        tools = reasoning_result.get("tools_needed", [])

        enriched = []
        for step in mindmap:
            enriched.append({
                **step,
                "assigned_cap": step.get("tool", "auto"),
                "trigger_condition": f"上一步'{step.get('verify','')}'通过后触发",
                "on_failure": "返回设计脑重新分析",
            })

        return {
            "original_direction": reasoning_result.get("direction", ""),
            "rationale": reasoning_result.get("rationale", ""),
            "risks": reasoning_result.get("risks", []),
            "confidence": reasoning_result.get("confidence", 0),
            "enriched_mindmap": enriched,
            "skill_schedule": self._build_skill_schedule(enriched),
            "tool_schedule": self._build_tool_schedule(tools),
        }

    def _build_skill_schedule(self, mindmap: list) -> list[dict]:
        schedule = []
        for step in mindmap:
            schedule.append({
                "at_step": step.get("step", 0),
                "action": step.get("action", ""),
                "cap": step.get("assigned_cap", "auto"),
                "trigger": step.get("trigger_condition", ""),
            })
        return schedule

    def _build_tool_schedule(self, tools: list) -> list[dict]:
        return [{"tool": t, "when": "按需", "purpose": "推理脑指定"} for t in tools]

    # ── 邻域巡检 (每30分钟) ────────────────

    def patrol_neighborhoods(self) -> dict:
        """巡检神经邻域 + 感知邻域 -- 检查失灵/脱节

        检查项:
          1. 神经邻域: 全邻域深度扫描 (nexus.scan_all)
          2. 感知域: 屏幕感知+设备感知+邻域感知+对外侦察
          3. 断连检测: 任何core cap缺失/语法错误立即告警
          4. 自动修复建议: 发现问题时生成修复方案
        """
        result = {
            "timestamp": time.time(),
            "neural": {"ok": True, "issues": []},
            "perception": {"ok": True, "issues": []},
            "visual_cortex": {"ok": True, "detail": ""},
            "overall_ok": True,
        }

        try:
            from brain.nexus import get_nexus
            nexus = get_nexus()
            scan = nexus.scan_all(force=True)

            # 神经邻域 -- 所有18个邻域
            for domain_name, domain in scan.get("neighborhoods", {}).items():
                if not domain.get("ok"):
                    result["neural"]["ok"] = False
                    for cap_name, cap in domain.get("caps", {}).items():
                        if not cap.get("healthy") and cap.get("status") == "core":
                            result["neural"]["issues"].append({
                                "domain": domain_name,
                                "cap": cap_name,
                                "issues": cap.get("issues", []),
                                "severity": "critical" if any(
                                    "syntax" in i or "corrupt" in i
                                    for i in cap.get("issues", [])
                                ) else "warning",
                            })

            # 感知域 -- 重点检查
            perception_domains = ["感知域", "设备感知层", "侦察域", "桌面域"]
            for pd_name in perception_domains:
                domain = scan.get("neighborhoods", {}).get(pd_name, {})
                if not domain:
                    result["perception"]["issues"].append({
                        "domain": pd_name,
                        "issue": "感知域缺失",
                        "severity": "critical",
                    })
                    result["perception"]["ok"] = False
                    continue

                for cap_name, cap in domain.get("caps", {}).items():
                    if not cap.get("exists"):
                        severity = "critical" if cap.get("status") == "core" else "warning"
                        result["perception"]["issues"].append({
                            "domain": pd_name,
                            "cap": cap_name,
                            "status": cap.get("status"),
                            "issue": "cap目录缺失(run.py/capability.json)",
                            "severity": severity,
                        })
                        if severity == "critical":
                            result["perception"]["ok"] = False
                    elif not cap.get("healthy"):
                        result["perception"]["issues"].append({
                            "domain": pd_name,
                            "cap": cap_name,
                            "issues": cap.get("issues", []),
                            "severity": "warning",
                        })

            result["neural"]["total_domains"] = len(scan.get("neighborhoods", {}))
            result["neural"]["total_issues"] = scan.get("total_issues", 0)
            result["neural"]["health_pct"] = scan.get("health_pct", 100)

            # 视觉皮层巡检
            try:
                from brain.visual_cortex import get_cortex
                vh = get_cortex().patrol_visual_health()
                result["visual_cortex"]["ok"] = vh["all_ok"]
                result["visual_cortex"]["detail"] = (
                    f'眼:{vh["eyes"]["detail"]} OCR:{vh["ocr"]["detail"]}'
                )
            except Exception as ve:
                result["visual_cortex"]["ok"] = False
                result["visual_cortex"]["detail"] = str(ve)[:100]

            result["overall_ok"] = (
                result["neural"]["ok"] and
                result["perception"]["ok"] and
                result["visual_cortex"]["ok"]
            )

        except Exception as e:
            result["overall_ok"] = False
            result["error"] = str(e)
            _DESIGN_LOG.error(f"邻域巡检失败: {e}")

        self._last_patrol = result

        # 告警
        if not result["overall_ok"]:
            issues_count = (
                len(result["neural"]["issues"]) +
                len(result["perception"]["issues"])
            )
            _DESIGN_LOG.warning(
                f"⛔ 邻域巡检发现{issues_count}处问题: "
                f"神经={len(result['neural']['issues'])} "
                f"感知={len(result['perception']['issues'])}"
            )

        return result

    def start_patrol(self, interval: int = PATROL_INTERVAL):
        """启动定时巡检 -- 默认每30分钟"""
        if self._patrol_running:
            return

        self._patrol_running = True
        _DESIGN_LOG.info(f"设计脑邻域巡检已启动, 间隔{interval//60}分钟")
        self._patrol_loop(interval)

    def _patrol_loop(self, interval: int):
        """巡检循环"""
        if not self._patrol_running:
            return

        try:
            result = self.patrol_neighborhoods()
            status = "OK" if result["overall_ok"] else "ISSUES"
            _DESIGN_LOG.info(
                f"邻域巡检完成: {status} "
                f"(神经={result['neural']['health_pct']}%)"
            )
        except Exception as e:
            _DESIGN_LOG.error(f"巡检异常: {e}")

        # 下一轮
        self._patrol_timer = threading.Timer(interval, self._patrol_loop, args=[interval])
        self._patrol_timer.daemon = True
        self._patrol_timer.start()

    def stop_patrol(self):
        """停止定时巡检"""
        self._patrol_running = False
        if self._patrol_timer:
            self._patrol_timer.cancel()
            self._patrol_timer = None

    def get_patrol_status(self) -> dict:
        """获取最近一次巡检结果"""
        return {
            "running": self._patrol_running,
            "last_patrol": self._last_patrol,
            "seconds_ago": time.time() - self._last_patrol.get("timestamp", 0)
            if self._last_patrol else None,
        }

# ═══════════════ 全局单例 ═══════════════

_reasoning_brain: Optional[ReasoningBrain] = None
_design_interface: Optional[DesignBrainInterface] = None


def get_reasoning_brain() -> ReasoningBrain:
    global _reasoning_brain
    if _reasoning_brain is None:
        _reasoning_brain = ReasoningBrain()
    return _reasoning_brain


def get_design_interface() -> DesignBrainInterface:
    global _design_interface
    if _design_interface is None:
        _design_interface = DesignBrainInterface()
    return _design_interface


# ═══════════════ 快捷函数 ═══════════════

def ask_reasoning(question: str, context: dict | None = None) -> dict:
    """快捷: 向推理脑提问"""
    return get_reasoning_brain().ask(question, context=context)


def design_query(task: str, context: dict | None = None) -> dict:
    """快捷: 设计脑查询推理脑 → 返回可执行的思维导图"""
    di = get_design_interface()
    raw = di.query(task, context)
    return di.decompose(raw)


if __name__ == "__main__":
    import sys
    rb = ReasoningBrain()
    rb.new_session("测试会话")
    q = sys.argv[1] if len(sys.argv) > 1 else "如何优化Python Web应用的并发性能"
    result = rb.ask(q)
    print(json.dumps(result, ensure_ascii=False, indent=2))
