# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
GBT小土豆 · 智能大脑 v5.0 · 多脑神经系统
==========================================

核心脑:
  🧠 推理脑 (ReasoningBrain)  — 深度推理、8种模式
  🧠 设计脑 (DesignBrain)     — 技能路由、工具编排、方案消化
  🧠 编程脑 (Executor)        — 思维导图执行、子代理隔离
  🧠 视觉脑 (VisualCortex)    — 屏幕感知、三层视觉分析
  🧠 认知脑 (Cognition)       — 自我认知、身份宣告
  🧠 进化脑 (SelfEvolve)      — 自主学习、上下文管理
  🧠 镜像脑 (MirrorFusion)    — 沙盒验证、方案对比
  🧠 审计脑 (AuditTrail)      — 全链路审计、行为追溯
  🧠 意图脑 (IntentBroker)    — 意图识别、能力路由

触手脑 (Tentacle Brains):
  🧬 神经触手 — 穿透扫描、邻域注入、自愈修复
  👁 视觉触手 — 7通道采集、OCR识别
  🍽 吞噬触手 — 缺口分析、自动创建cap
  🧠 视觉记忆 — 每帧存储、时间线索引

身体:
  👀 眼睛 (Eyes) — 屏幕、OCR、视觉
  ✋ 手 (Hands)  — 键鼠、桌面操控

邻域:
  🌐 NexusHub — 12大AI邻域、意图路由、量子延申
"""
from dotenv import load_dotenv; load_dotenv(override=True)
from brain.boot import boot
from brain.orchestrator import Orchestrator, get_orchestrator
from brain.nexus import NexusHub, get_nexus, scan as nexus_scan, diagnose as nexus_diagnose
from brain.intent_broker import IntentBroker, get_broker
from brain.deep_reasoner import DeepReasoner, get_reasoner
from brain.reasoning_brain import ReasoningBrain, get_reasoning_brain, DesignBrainInterface, get_design_interface
from brain.visual_cortex import VisualCortex, get_cortex, analyze_html, analyze_current_screen
from brain.self_evolve import SelfEvolve, get_evolver
from brain.cognition import Cognition, get_cognition
from brain.audit_trail import AuditTrail, get_trail, log as audit_log, verify as audit_verify
from brain.executor import AutonomousExecutor, get_executor
from brain.mirror_fusion import MirrorFusion, get_mirror

__version__ = "5.0.0"
__all__ = [
    "boot", "Orchestrator", "get_orchestrator",
    "NexusHub", "get_nexus", "nexus_scan", "nexus_diagnose",
    "IntentBroker", "get_broker",
    "DeepReasoner", "get_reasoner",
    "ReasoningBrain", "get_reasoning_brain",
    "DesignBrainInterface", "get_design_interface",
    "SelfEvolve", "get_evolver",
    "Cognition", "get_cognition",
    "MirrorFusion", "get_mirror"
]


# ━━━ 身体 ━━━
from brain.host_body import eyes, hands, Eyes, Hands
from brain.remote_body import connect, connect_from_active_tunnels, RemoteBody, RemoteEyes, RemoteHands, RemoteTerminal
from brain.mind_map import generate_mind_map
from brain.deep_reasoner import RUN_PROTOCOL
