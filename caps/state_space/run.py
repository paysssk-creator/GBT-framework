# 开发者：自由的风 · 融合自 VulnClaw solver.py 的架构思想
"""
state_space/run.py — 状态空间搜索引擎 v1.0

融合 VulnClaw 的核心架构：把任务执行建模为从 origin → goal 的状态空间搜索。
用两个原语驱动：Fact（已确认事实）+ Intent（探索方向），结构上杜绝原地打转。

核心动作:
  init     — 初始化状态空间（设置origin和goal）
  add_fact — 添加已确认的事实到黑板
  propose  — 大脑提出新的探索方向(Intent)
  execute  — 执行一个Intent，产出新的Fact
  status   — 查看当前状态空间（已确认/探索中/已放弃）
  converge — 判断是否已达到目标
"""

import sys, json, os, time
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

STATE_DIR = Path.home() / ".gbt" / "state_space"
STATE_DIR.mkdir(parents=True, exist_ok=True)

class IntentStatus(Enum):
    PROPOSED = "proposed"     # 大脑提出，尚未执行
    EXPLORING = "exploring"   # 正在执行
    CONCLUDED = "concluded"   # 执行完成，产出Fact
    ABANDONED = "abandoned"   # 放弃（失败/不可行）

class FactConfidence(Enum):
    HIGH = "high"       # 工具输出直接证实
    MEDIUM = "medium"   # 推理得出
    LOW = "low"         # 推测

@dataclass
class Fact:
    id: str
    content: str                    # 事实内容
    confidence: str = "medium"      # high/medium/low
    source: str = ""                # 来源工具/tool
    evidence: str = ""              # 工具原始输出作为证据
    timestamp: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id, "content": self.content,
            "confidence": self.confidence, "source": self.source,
            "evidence": self.evidence[:500], "timestamp": self.timestamp,
            "tags": self.tags
        }

@dataclass
class Intent:
    id: str
    direction: str                  # 探索方向描述
    from_facts: List[str]           # 基于哪些Fact提出
    status: str = "proposed"        # proposed/exploring/concluded/abandoned
    result_fact_id: str = ""        # 执行后产出的Fact ID
    error: str = ""                 # 失败原因
    proposed_at: str = ""
    executed_at: str = ""

    def to_dict(self):
        return {
            "id": self.id, "direction": self.direction,
            "from_facts": self.from_facts, "status": self.status,
            "result_fact_id": self.result_fact_id, "error": self.error,
            "proposed_at": self.proposed_at, "executed_at": self.executed_at
        }

class StateSpace:
    """黑板图状态空间 — 任务执行的导航地图"""

    def __init__(self, task_id: str = "", origin: str = "", goal: str = ""):
        self.task_id = task_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.origin = origin        # 起点：初始状态/目标
        self.goal = goal            # 终点：拿到flag/确认漏洞/完成任务
        self.facts: Dict[str, Fact] = {}
        self.intents: Dict[str, Intent] = {}
        self.fact_counter = 0
        self.intent_counter = 0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self._load()

    def _next_fact_id(self):
        self.fact_counter += 1
        return f"F{self.fact_counter:04d}"

    def _next_intent_id(self):
        self.intent_counter += 1
        return f"I{self.intent_counter:04d}"

    def add_fact(self, content: str, confidence: str = "medium",
                 source: str = "", evidence: str = "", tags: list = None) -> Fact:
        """添加已确认的事实到黑板 — 防重复"""
        # 检查是否已存在相似事实（防原地打转）
        content_lower = content.lower().strip()
        for existing in self.facts.values():
            if content_lower == existing.content.lower().strip():
                existing.confidence = confidence  # 更新置信度
                existing.evidence = evidence or existing.evidence
                return existing

        fid = self._next_fact_id()
        fact = Fact(id=fid, content=content, confidence=confidence,
                    source=source, evidence=evidence or "",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    tags=tags or [])
        self.facts[fid] = fact
        self._save()
        return fact

    def propose_intent(self, direction: str, from_fact_ids: List[str] = None) -> Intent:
        """大脑提出新的探索方向 — 防重复"""
        direction_lower = direction.lower().strip()
        # 检查是否已提出过相同方向
        for existing in self.intents.values():
            if direction_lower == existing.direction.lower().strip():
                if existing.status in ("concluded", "abandoned"):
                    # 已探索过且已结束，不允许重复
                    return None
                return existing  # 仍在进行中

        iid = self._next_intent_id()
        intent = Intent(id=iid, direction=direction,
                       from_facts=from_fact_ids or [],
                       status="proposed",
                       proposed_at=datetime.now(timezone.utc).isoformat())
        self.intents[iid] = intent
        self._save()
        return intent

    def execute_intent(self, intent_id: str, success: bool,
                       result_content: str = "", evidence: str = "",
                       error: str = "") -> Optional[Fact]:
        """执行一个Intent → 成功则产出Fact"""
        if intent_id not in self.intents:
            return None

        intent = self.intents[intent_id]
        intent.status = "concluded" if success else "abandoned"
        intent.executed_at = datetime.now(timezone.utc).isoformat()
        intent.error = error

        if success and result_content:
            fact = self.add_fact(
                content=result_content,
                confidence="high" if evidence else "medium",
                source=f"intent:{intent_id}",
                evidence=evidence,
                tags=["explored"]
            )
            intent.result_fact_id = fact.id
            self._save()
            return fact

        self._save()
        return None

    def has_converged(self) -> dict:
        """判断是否已达成目标"""
        goal_lower = self.goal.lower().strip() if self.goal else ""
        if not goal_lower:
            # 无明确目标 → 检查是否有待探索方向
            pending = [i for i in self.intents.values() if i.status == "proposed"]
            return {"converged": len(pending) == 0 and len(self.facts) > 0,
                    "reason": "探索前沿耗尽" if not pending else "仍有探索方向",
                    "pending_intents": len(pending)}

        # 检查goal关键词是否在任何Fact中出现
        goal_keywords = [w for w in goal_lower.split() if len(w) > 2]
        for fact in self.facts.values():
            fact_lower = fact.content.lower()
            # 关键检查：目标关键词是否在事实中
            if all(kw in fact_lower for kw in goal_keywords[:3]):
                # 证据级验证：如果是flag类目标，必须在证据中逐字符出现
                if "flag" in goal_lower or "密码" in goal_lower or "key" in goal_lower:
                    if fact.evidence and all(kw in fact.evidence.lower() for kw in goal_keywords[:3]):
                        return {"converged": True, "reason": f"目标已达成(证据验证): {fact.content[:100]}",
                                "fact_id": fact.id}
                    return {"converged": False, "reason": "声称达成但无证据验证",
                            "fact_id": fact.id, "warning": "证据反幻觉闸门触发"}
                return {"converged": True, "reason": f"目标已达成: {fact.content[:100]}",
                        "fact_id": fact.id}

        # 还有待探索方向
        pending = [i for i in self.intents.values() if i.status == "proposed"]
        return {"converged": False, "pending_intents": len(pending),
                "reason": "目标未达成" + (f"，{len(pending)}个方向待探索" if pending else "，无待探索方向")}

    def get_frontier(self) -> List[Intent]:
        """获取探索前沿 — 所有待执行的Intent"""
        return [i for i in self.intents.values() if i.status == "proposed"]

    def get_summary(self) -> dict:
        """状态空间摘要"""
        facts_list = [f.to_dict() for f in self.facts.values()]
        intents_list = [i.to_dict() for i in self.intents.values()]
        return {
            "task_id": self.task_id,
            "origin": self.origin,
            "goal": self.goal,
            "facts_count": len(self.facts),
            "intents_count": len(self.intents),
            "proposed": len([i for i in self.intents.values() if i.status == "proposed"]),
            "concluded": len([i for i in self.intents.values() if i.status == "concluded"]),
            "abandoned": len([i for i in self.intents.values() if i.status == "abandoned"]),
            "convergence": self.has_converged(),
            "facts": facts_list,
            "intents": intents_list,
        }

    def _save(self):
        sf = STATE_DIR / f"{self.task_id}.json"
        sf.write_text(json.dumps({
            "task_id": self.task_id, "origin": self.origin, "goal": self.goal,
            "facts": {k: v.to_dict() for k, v in self.facts.items()},
            "intents": {k: v.to_dict() for k, v in self.intents.items()},
            "fact_counter": self.fact_counter, "intent_counter": self.intent_counter,
            "created_at": self.created_at,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }, ensure_ascii=False, indent=2), encoding='utf-8')

    def _load(self):
        sf = STATE_DIR / f"{self.task_id}.json"
        if sf.exists():
            try:
                data = json.loads(sf.read_text(encoding='utf-8'))
                self.origin = data.get("origin", self.origin)
                self.goal = data.get("goal", self.goal)
                self.fact_counter = data.get("fact_counter", 0)
                self.intent_counter = data.get("intent_counter", 0)
                for k, v in data.get("facts", {}).items():
                    self.facts[k] = Fact(**{kk: vv for kk, vv in v.items()
                                            if kk in Fact.__dataclass_fields__})
                for k, v in data.get("intents", {}).items():
                    self.intents[k] = Intent(**{kk: vv for kk, vv in v.items()
                                                if kk in Intent.__dataclass_fields__})
            except: pass


# ══════════════════════════════════════════════════════════
# Actions
# ══════════════════════════════════════════════════════════

_active_spaces: Dict[str, StateSpace] = {}

def _get_space(task_id: str = "", origin: str = "", goal: str = "") -> StateSpace:
    if task_id and task_id in _active_spaces:
        return _active_spaces[task_id]
    space = StateSpace(task_id=task_id, origin=origin, goal=goal)
    if task_id:
        _active_spaces[task_id] = space
    return space

def do_init(params: dict) -> dict:
    """初始化状态空间 — origin(起点)和goal(终点)"""
    task_id = params.get("task_id", "")
    origin = params.get("origin", params.get("task", ""))
    goal = params.get("goal", params.get("target", ""))
    space = _get_space(task_id, origin, goal)
    return {"ok": True, "task_id": space.task_id, "origin": space.origin,
            "goal": space.goal, "summary": space.get_summary()}

def do_add_fact(params: dict) -> dict:
    """添加已确认事实"""
    task_id = params.get("task_id", "")
    space = _get_space(task_id)
    fact = space.add_fact(
        content=params.get("content", ""),
        confidence=params.get("confidence", "medium"),
        source=params.get("source", ""),
        evidence=params.get("evidence", ""),
        tags=params.get("tags", [])
    )
    return {"ok": True, "fact": fact.to_dict(), "total_facts": len(space.facts)}

def do_propose(params: dict) -> dict:
    """大脑提出探索方向 — 防重复"""
    task_id = params.get("task_id", "")
    space = _get_space(task_id)
    intent = space.propose_intent(
        direction=params.get("direction", ""),
        from_fact_ids=params.get("from_facts", [])
    )
    if intent is None:
        return {"ok": False, "error": "该方向已探索过(防原地打转)", "duplicate": True}
    return {"ok": True, "intent": intent.to_dict(), "total_intents": len(space.intents)}

def do_execute(params: dict) -> dict:
    """执行探索方向"""
    task_id = params.get("task_id", "")
    space = _get_space(task_id)
    result = space.execute_intent(
        intent_id=params.get("intent_id", ""),
        success=params.get("success", False),
        result_content=params.get("result_content", ""),
        evidence=params.get("evidence", ""),
        error=params.get("error", "")
    )
    if result:
        return {"ok": True, "executed": True,
                "new_fact": result.to_dict(), "convergence": space.has_converged()}
    return {"ok": False, "error": "执行失败或Intent不存在"}

def do_status(params: dict) -> dict:
    """查看状态空间"""
    task_id = params.get("task_id", "")
    space = _get_space(task_id)
    return {"ok": True, **space.get_summary()}

def do_converge(params: dict) -> dict:
    """判断是否已达成目标"""
    task_id = params.get("task_id", "")
    space = _get_space(task_id)
    return {"ok": True, **space.has_converged()}

def do_anti_hallucination(params: dict) -> dict:
    """证据级反幻觉闸门 — 验证声称的结论是否在工具输出中逐字符出现"""
    claim = params.get("claim", "")         # 声称的结论
    evidence = params.get("evidence", "")   # 工具原始输出
    mode = params.get("mode", "strict")     # strict:逐字符 / fuzzy:关键词

    if not claim or not evidence:
        return {"ok": False, "error": "需要 claim 和 evidence", "hallucination": True}

    if mode == "strict":
        # 逐字符匹配（VulnClaw风格）
        verified = claim.strip() in evidence
    else:
        # 关键词匹配
        keywords = [w for w in claim.split() if len(w) > 2]
        verified = all(kw.lower() in evidence.lower() for kw in keywords[:5]) if keywords else False

    return {
        "ok": True,
        "verified": verified,
        "hallucination": not verified,
        "mode": mode,
        "claim_preview": claim[:100],
        "evidence_preview": evidence[:200],
        "recommendation": "证据验证通过" if verified else "⚠ 声称的结论未在工具输出中找到 → 标记为幻觉，丢弃"
    }

def do_detect_loop(params: dict) -> dict:
    """检测循环 — 对比最近的 Intent/Fact 序列判断 GBT 是否陷入重复"""
    task_id = params.get("task_id", "")
    space = _get_space(task_id)
    window = params.get("window", 5)  # 检测窗口大小
    min_repeat = params.get("min_repeat", 2)  # 最小重复次数

    intents = sorted(space.intents.values(), key=lambda i: i.proposed_at if i.proposed_at else "")
    facts = list(space.facts.values())

    if len(intents) < min_repeat * 2:
        return {"ok": True, "looping": False, "reason": "不足够的历史数据检测循环",
                "intent_count": len(intents)}

    # 提取最近的 direction 序列
    recent_directions = [i.direction.lower().strip() for i in intents[-window:]]

    # 检测重复模式：检查连续 window 内是否有重复 direction
    seen = {}
    repeats = []
    for idx, d in enumerate(recent_directions):
        if d in seen:
            seen[d].append(idx)
        else:
            seen[d] = [idx]

    for direction, indices in seen.items():
        if len(indices) >= min_repeat:
            repeats.append({"direction": direction, "count": len(indices),
                            "positions": indices})

    # 检测相邻重复序列 (A→B→A→B 模式)
    adjacent_loops = []
    for seq_len in range(2, min(4, len(recent_directions) // 2 + 1)):
        for start in range(len(recent_directions) - seq_len * 2 + 1):
            seq_a = recent_directions[start:start + seq_len]
            seq_b = recent_directions[start + seq_len:start + seq_len * 2]
            if seq_a == seq_b and any(d.strip() for d in seq_a):
                adjacent_loops.append({
                    "pattern": seq_a,
                    "length": seq_len,
                    "start_pos": start,
                    "repeat_start": start + seq_len,
                })

    # 检测 abandoned → proposed 循环（提出→放弃→再提出相同方向）
    abandon_retry = []
    abandoned_dirs = {}
    for i in intents:
        if i.status == "abandoned":
            d = i.direction.lower().strip()
            if d not in abandoned_dirs:
                abandoned_dirs[d] = []
            abandoned_dirs[d].append(i.id)
    for i in intents:
        if i.status in ("proposed", "exploring"):
            d = i.direction.lower().strip()
            if d in abandoned_dirs:
                abandon_retry.append({"direction": d,
                                      "abandoned_ids": abandoned_dirs[d],
                                      "retry_id": i.id})

    # 事实停滞检测 — 最近 N 个 intent 没有产出新 fact
    fact_stagnation = False
    if len(intents) >= window:
        recent_intents = intents[-window:]
        recent_concluded = [i for i in recent_intents if i.status == "concluded" and i.result_fact_id]
        if len(recent_concluded) == 0 and len(recent_intents) >= window:
            fact_stagnation = True

    looping = len(repeats) > 0 or len(adjacent_loops) > 0 or len(abandon_retry) > 0 or fact_stagnation
    confidence = "high" if len(adjacent_loops) > 0 else ("medium" if len(repeats) > 0 else "low")

    return {
        "ok": True,
        "looping": looping,
        "confidence": confidence,
        "repeated_directions": repeats,
        "adjacent_loops": adjacent_loops,
        "abandon_retry_loops": abandon_retry,
        "fact_stagnation": fact_stagnation,
        "total_intents": len(intents),
        "total_facts": len(facts),
        "window": window,
    }


def do_escape_loop(params: dict) -> dict:
    """逃逸循环 — 检测到循环后建议替代路径"""
    task_id = params.get("task_id", "")
    space = _get_space(task_id)

    # 先运行循环检测
    loop_result = do_detect_loop({"task_id": task_id, **params})

    if not loop_result.get("looping"):
        return {"ok": True, "escaping": False,
                "message": "未检测到循环，无需逃逸",
                "loop_check": loop_result}

    intents = list(space.intents.values())
    facts = list(space.facts.values())

    # 收集已尝试的方向
    tried_directions = set()
    for i in intents:
        if i.status in ("abandoned", "concluded"):
            tried_directions.add(i.direction.lower().strip())

    # 收集已确认的事实作为跳板
    fact_contents = [f.content for f in facts if f.confidence in ("high", "medium")]

    # 建议策略
    suggestions = []

    # 策略1: 从不同事实出发
    if fact_contents:
        unused_facts = fact_contents[-3:] if len(fact_contents) > 3 else fact_contents
        suggestions.append({
            "strategy": "change_origin",
            "label": "更换出发点",
            "description": "从不同的事实/发现重新出发，而非重复已尝试方向",
            "suggested_starting_points": unused_facts[:3],
        })

    # 策略2: 逆向着手
    if space.goal:
        suggestions.append({
            "strategy": "reverse_approach",
            "label": "逆向着手",
            "description": f"从目标「{space.goal[:80]}」反向推导，而非继续当前探索方向",
        })

    # 策略3: 横向探索
    if len(tried_directions) >= 2:
        directions_sample = list(tried_directions)[-3:]
        suggestions.append({
            "strategy": "lateral_explore",
            "label": "横向探索",
            "description": "避免重复已有方向，尝试正交的、尚未探索的角度",
            "exhausted_directions": directions_sample,
        })

    # 策略4: 降维/简化
    suggestions.append({
        "strategy": "simplify",
        "label": "降维简化",
        "description": "将当前问题拆解为更小的子问题，逐个击破而非一次性解决",
        "hint": "尝试修改攻击面 / 变更工具 / 降低复杂度",
    })

    # 策略5: 外部视角
    suggestions.append({
        "strategy": "external_perspective",
        "label": "外部视角",
        "description": "暂停当前方向，查阅文档/社区/历史案例寻找灵感",
    })

    # 识别最严重的循环模式
    worst_loop = None
    if loop_result.get("adjacent_loops"):
        worst_loop = loop_result["adjacent_loops"][0]
    elif loop_result.get("repeated_directions"):
        worst_loop = loop_result["repeated_directions"][0]

    return {
        "ok": True,
        "escaping": True,
        "loop_detected": loop_result,
        "suggestions": suggestions,
        "suggestion_count": len(suggestions),
        "worst_loop": worst_loop,
        "tried_directions_count": len(tried_directions),
        "recommended_action": "选择一个建议策略，用 add_fact 记录新事实，用 propose 提出新方向",
    }


def do_explore_branch(params: dict) -> dict:
    """分叉探索 — 将当前状态空间克隆出多个并行假设路径"""
    task_id = params.get("task_id", "")
    space = _get_space(task_id)
    branches = params.get("branches", 2)  # 分支数
    hypotheses = params.get("hypotheses", [])  # 各分支的假设

    if branches < 1 or branches > 6:
        return {"ok": False, "error": "分支数需在 1-6 之间", "branches_requested": branches}

    current_summary = space.get_summary()
    base_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    created_branches = []
    for idx in range(branches):
        branch_id = f"{space.task_id}_branch{idx + 1}_{base_timestamp}"
        branch_space = StateSpace(task_id=branch_id, origin=space.origin, goal=space.goal)

        # 克隆当前的事实和意图
        for fact in space.facts.values():
            branch_space.add_fact(
                content=f"[fork] {fact.content}",
                confidence=fact.confidence,
                source=f"fork_from:{space.task_id}",
                evidence=fact.evidence,
                tags=fact.tags + ["forked"],
            )

        # 为每个分支设置假设方向
        hypothesis = hypotheses[idx] if idx < len(hypotheses) else f"分支 {idx + 1} — 探索路径 {chr(65 + idx)}"
        branch_space.add_fact(
            content=f"[假设] {hypothesis}",
            confidence="low",
            source=f"explore_branch:{space.task_id}",
            evidence="",
            tags=["hypothesis", f"branch_{idx + 1}"],
        )

        _active_spaces[branch_id] = branch_space
        created_branches.append({
            "branch_index": idx + 1,
            "task_id": branch_id,
            "hypothesis": hypothesis,
            "facts_count": len(branch_space.facts),
            "intents_count": len(branch_space.intents),
        })

    return {
        "ok": True,
        "explored": True,
        "parent_task_id": space.task_id,
        "branches_created": len(created_branches),
        "branches": created_branches,
        "origin": space.origin,
        "goal": space.goal,
        "parent_facts": len(space.facts),
        "parent_intents": len(space.intents),
        "instruction": "每个分支有独立 task_id，用 task_id 参数分别探索。收敛时合并最佳路径的发现。",
    }


# ══════════════════════════════════════════════════════════
# L0-L4 渐进升级策略 (融合自 VulnClaw reflexion.py)
# ══════════════════════════════════════════════════════════

L0_L4_ESCALATION = {
    "L0": {"name": "原始载荷", "desc": "直接使用原始payload，不做任何编码",
           "operations": ["raw"]},
    "L1": {"name": "基础编码", "desc": "URL编码/HTML实体编码",
           "operations": ["url_encode", "html_entity"]},
    "L2": {"name": "双写注释绕过", "desc": "双写关键字/注释插入/大小写变换",
           "operations": ["double_write", "comment_insert", "case_vary"]},
    "L3": {"name": "Unicode/Hex编码", "desc": "Unicode编码/十六进制编码/UTF-7",
           "operations": ["unicode_encode", "hex_encode", "utf7_encode"]},
    "L4": {"name": "多层混淆/换攻击面", "desc": "多层编码组合/换用不同攻击向量/协议降级",
           "operations": ["multi_layer", "attack_surface_switch", "protocol_downgrade"]},
}

def do_escalate(params: dict) -> dict:
    """L0-L4渐进升级策略 — 失败后自动升级绕过等级"""
    current_level = params.get("current_level", "L0")
    failure_reason = params.get("failure_reason", "")
    payload = params.get("payload", "")

    levels = list(L0_L4_ESCALATION.keys())
    try:
        current_idx = levels.index(current_level)
    except ValueError:
        current_idx = 0

    if current_idx >= len(levels) - 1:
        return {"ok": False, "error": f"已到最高等级 {current_level}，建议更换攻击面",
                "max_level_reached": True}

    next_level = levels[current_idx + 1]
    next_info = L0_L4_ESCALATION[next_level]

    # 构建升级指令
    instruction = f"""
【L0-L4 渐进升级】
当前等级: {current_level} ({L0_L4_ESCALATION[current_level]['name']})
失败原因: {failure_reason}
原始载荷: {payload}

→ 升级到 {next_level}: {next_info['name']}
→ 描述: {next_info['desc']}
→ 可选操作: {next_info['operations']}

请使用以上操作对载荷进行编码/改造后重试。
"""

    return {
        "ok": True,
        "escalated": True,
        "previous_level": current_level,
        "new_level": next_level,
        "new_level_name": next_info["name"],
        "new_level_desc": next_info["desc"],
        "available_operations": next_info["operations"],
        "instruction": instruction,
        "level_progress": f"{current_idx + 2}/{len(levels)}",
    }


# ══════════════════════════════════════════════════════════

HANDLERS = {
    "init": do_init,
    "add_fact": do_add_fact,
    "propose": do_propose,
    "execute": do_execute,
    "status": do_status,
    "converge": do_converge,
    "anti_hallucination": do_anti_hallucination,
    "escalate": do_escalate,
    "detect_loop": do_detect_loop,
    "escape_loop": do_escape_loop,
    "explore_branch": do_explore_branch,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知: {action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
