import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""brain/layer_wiring.py — GBT v5.0 14层契约注册
=================================================
由 layer_guard.py 驱动。启动时 verify_topology() 替代旧的"每层打勾"。
"""
from brain.layer_guard import LayerGuard, LayerContract
from brain.nexus import get_nexus
from brain.cognition import get_cognition
from brain.orchestrator import get_orchestrator


def _safe_import_check(module_path: str, attr: str = None) -> bool:
    """安全导入检查 — 替代 lambda: True no-op"""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        if attr:
            return hasattr(mod, attr) or getattr(mod, attr, None) is not None
        return True
    except Exception:
        return False

guard = LayerGuard()

# ═══════════════════════════════════════════════════════
#  14 层契约 — 基于2026-07-22全框架审计
#  依赖链: L0→L1→L2→L3→L4→L5→L6→L7→L8→L9→L10→L11→L12
#          横向: L_translation (L5→翻译⇢L2,L7)
# ═══════════════════════════════════════════════════════

guard.register(LayerContract(
    name="L0_boot", version="5.0",
    exposes=["boot_sequence"],
    health_check=lambda: True
))

guard.register(LayerContract(
    name="L1_caps_execution", version="5.0",
    depends_on=["L0_boot"],
    exposes=["162_capability_modules"],
    health_check=lambda: get_nexus().scan()["ok"]
))

guard.register(LayerContract(
    name="L2_nexus_routes", version="5.0",
    depends_on=["L1_caps_execution", "L_translation"],
    exposes=["55_routes", "7_quantum_connections"],
    health_check=lambda: get_nexus().deep_scan()["connections"]["ok"]
))

guard.register(LayerContract(
    name="L3_topology", version="5.0",
    depends_on=["L2_nexus_routes"],
    exposes=["topology_map", "neighborhood_scan"],
    health_check=lambda: get_nexus().topology() is not None
))

guard.register(LayerContract(
    name="L4_cognition", version="5.0",
    depends_on=["L3_topology"],
    exposes=["identity_check", "who_am_i", "visual_system"],
    health_check=lambda: get_cognition().who_am_i() is not None
))

guard.register(LayerContract(
    name="L5_intent_broker", version="5.0",
    depends_on=["L4_cognition", "L_translation"],
    exposes=["intent_classification", "zh_en_mapping"],
    health_check=lambda: _safe_import_check("brain.intent_broker", "IntentBroker")
))

guard.register(LayerContract(
    name="L6_orchestrator", version="5.0",
    depends_on=["L5_intent_broker", "L2_nexus_routes"],
    min_dependency_versions={"L5_intent_broker": "5.0", "L2_nexus_routes": "5.0"},
    exposes=["submit", "health_check", "run_cycle", "judge", "complete_task"],
    health_check=lambda: get_orchestrator().health_check()["ok"]
))

guard.register(LayerContract(
    name="L7_intent_route", version="5.0",
    depends_on=["L2_nexus_routes", "L5_intent_broker", "L_translation"],
    exposes=["route", "match_intent", "fuzzy_match"],
    health_check=lambda: get_nexus().route("status check")["ok"]
))

guard.register(LayerContract(
    name="L8_deep_reasoner", version="5.0",
    depends_on=["L7_intent_route", "L4_cognition"],
    exposes=["reason", "analyze", "plan"],
    health_check=lambda: _safe_import_check("brain.deep_reasoner", "DeepReasoner")
))

guard.register(LayerContract(
    name="L9_self_evolve", version="5.0",
    depends_on=["L8_deep_reasoner", "L4_cognition"],
    exposes=["evolve", "learn", "absorb", "stats"],
    health_check=lambda: _safe_import_check("brain.self_evolve", "SelfEvolve")
))

guard.register(LayerContract(
    name="L10_executor", version="5.0",
    depends_on=["L6_orchestrator", "L1_caps_execution"],
    exposes=["execute", "plan", "agents", "status"],
    health_check=lambda: _safe_import_check("brain.executor", "AutonomousExecutor")
))

guard.register(LayerContract(
    name="L11_audit_trail", version="5.0",
    depends_on=["L10_executor"],
    exposes=["audit_log", "trace"],
    health_check=lambda: _safe_import_check("brain.audit_trail", "log")
))

guard.register(LayerContract(
    name="L12_mirror_fusion", version="5.0",
    depends_on=["L8_deep_reasoner", "L11_audit_trail"],
    exposes=["mirror_exec", "compare", "ablation_test", "sandbox_exec"],
    health_check=lambda: _safe_import_check("brain.mirror_fusion", "MirrorFusion")
))
# 翻译层 — 独立层，被 L2/L5/L7 显式依赖，无反向依赖
guard.register(LayerContract(
    name="L_translation", version="1.0",
    depends_on=[],
    exposes=["zh_to_en_intent"],
    health_check=lambda: _safe_import_check("caps.translator.run", "do_translate")
))

# ═══════════════════════════════════════════════════════
#  主动技能层 — 不经过 L7 路由，自主触发
#  修改上游必须走: skill → L11_audit_trail → 校验 → 生效
# ═══════════════════════════════════════════════════════

# Devourer 吞噬引擎 — 每日自主扫描→吸收→注入→进化
guard.register(LayerContract(
    name="L_devourer", version="3.0",
    depends_on=["L11_audit_trail"],
    exposes=["scan", "devour", "daily", "gaps", "digest", "auto_create"],
    trigger_mode="proactive",
    change_scope=["L1_caps_execution", "L9_self_evolve"],
    health_check=lambda: True
))