# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/boot.py — GBT智能大脑 启动自检
=====================================
每次新会话启动时运行，验证三层认知闭环各组件就绪。
"""
import sys, json, time, logging
from pathlib import Path

L = logging.getLogger("BrainBoot")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def check_layer1_pipeline() -> dict:
    """第1层: 消息管线 — 意图识别 + 深度推理"""
    result = {"layer": 1, "name": "消息管线", "ok": True, "checks": []}
    
    # 意图识别
    try:
        from brain.intent_broker import IntentBroker
        broker = IntentBroker()
        test = broker.analyze("你好")
        result["checks"].append({
            "component": "IntentBroker",
            "ok": True,
            "detail": f"就绪, 测试返回: {test.get('intent','?')}"
        })
    except Exception as e:
        result["checks"].append({"component": "IntentBroker", "ok": False, "detail": str(e)[:100]})
        result["ok"] = False

    # 深度推理
    try:
        from brain.deep_reasoner import DeepReasoner
        reasoner = DeepReasoner()
        result["checks"].append({
            "component": "DeepReasoner",
            "ok": True,
            "detail": "就绪"
        })
    except Exception as e:
        result["checks"].append({"component": "DeepReasoner", "ok": False, "detail": str(e)[:100]})
        result["ok"] = False

    return result


def check_layer2_review() -> dict:
    """第2层: 行动审查 — 确保工具调用前思考机制存在"""
    result = {"layer": 2, "name": "行动审查", "ok": True, "checks": []}
    try:
        from brain.orchestrator import Judge
        j = Judge()
        test_ok, _ = j.verify(
            {"description": "test", "task_id": "boot_check"},
            {"ok": True, "result": "done"},
            ["completed"]
        )
        result["checks"].append({"component": "Judge", "ok": True, "detail": "裁判引擎可用"})
    except Exception as e:
        result["checks"].append({"component": "Judge", "ok": False, "detail": str(e)[:100]})
        result["ok"] = False
    return result


def check_layer3_evolve() -> dict:
    """第3层: 自进化 — self_evolve 模块"""
    result = {"layer": 3, "name": "自进化闭环", "ok": True, "checks": []}
    try:
        from brain.self_evolve import SelfEvolve
        evolver = SelfEvolve()
        try:
            stats = evolver.stats()
            result["checks"].append({
                "component": "SelfEvolve",
                "ok": True,
                "detail": f"就绪, 记忆: {stats.get('total_lessons', 0)}条教训"
            })
        except Exception:
            result["checks"].append({
                "component": "SelfEvolve",
                "ok": True,
                "detail": "已加载 (统计信息暂不可用)"
            })
    except Exception as e:
        result["checks"].append({"component": "SelfEvolve", "ok": False, "detail": str(e)[:100]})
        result["ok"] = False
    return result


def check_all_brains() -> dict:
    """多脑神经系统 — 9核心脑 + 触手脑"""
    result = {"layer": "brains", "name": "多脑神经系统", "ok": True, "checks": []}

    brains = [
        ("推理脑", "brain.deep_reasoner", "DeepReasoner"),
        ("编程脑", "brain.executor", "AutonomousExecutor"),
        ("设计脑", "brain.orchestrator", "Orchestrator"),
        ("视觉脑", "brain.visual_cortex", "VisualCortex"),
        ("认知脑", "brain.cognition", "Cognition"),
        ("进化脑", "brain.self_evolve", "SelfEvolve"),
        ("镜像脑", "brain.mirror_fusion", "MirrorFusion"),
        ("审计脑", "brain.audit_trail", "AuditTrail"),
        ("意图脑", "brain.intent_broker", "IntentBroker"),
    ]

    for name, module, cls in brains:
        try:
            m = __import__(module, fromlist=[cls])
            getattr(m, cls)()
            result["checks"].append({"component": name, "ok": True, "detail": "就绪"})
        except Exception as e:
            result["checks"].append({"component": name, "ok": False, "detail": str(e)[:100]})
            result["ok"] = False

    # 触手脑
    try:
        from brain.neural_tentacle import get_tentacle
        get_tentacle()
        result["checks"].append({"component": "触手脑", "ok": True, "detail": "就绪"})
    except Exception as e:
        result["checks"].append({"component": "触手脑", "ok": False, "detail": str(e)[:100]})

    return result


def check_nexus_scan() -> dict:
    """邻域神经系统 — 全邻域自排查"""
    result = {"layer": 0, "name": "邻域感知", "ok": True, "checks": []}
    try:
        from brain.nexus import get_nexus
        nexus = get_nexus()
        scan = nexus.scan()  # 轻量扫描，不解译 run.py
        result["checks"].append({
            "component": "NexusHub",
            "ok": scan["ok"],
            "detail": f"扫描: {scan['found']}/{scan['total_caps']}文件 | 健康度: {scan['health_pct']:.0f}%"
        })
        diag = nexus.diagnose()
        if diag["issues"]:
            result["ok"] = False
            for issue in diag["issues"]:
                result["checks"].append({
                    "component": f"{issue['domain']}/{issue['cap']}",
                    "ok": False,
                    "detail": f"{issue['severity']}: {issue['desc']}"
                })
        result["topology"] = nexus.topology()
    except Exception as e:
        result["checks"].append({"component": "NexusHub", "ok": False, "detail": str(e)[:100]})
        result["ok"] = False
    return result



def check_host_body() -> dict:
    """原生身体检测 — 用原生模块确认眼睛和手"""
    result = {"layer": 0, "name": "原生身体", "ok": True, "checks": []}
    
    # 眼睛 — 导入原生Eyes
    try:
        from brain.host_body import eyes
        result["checks"].append({"component": "眼睛(native)", "ok": True, "detail": "Eyes已就绪"})
    except Exception as e:
        result["checks"].append({"component": "眼睛(native)", "ok": False, "detail": str(e)[:100]})
        result["ok"] = False

    # 手 — 导入原生Hands
    try:
        from brain.host_body import hands
        result["checks"].append({"component": "手(native)", "ok": True, "detail": "Hands已就绪"})
    except Exception as e:
        result["checks"].append({"component": "手(native)", "ok": False, "detail": str(e)[:100]})
        result["ok"] = False

    return result


def boot() -> dict:
    """启动自检 — 宣告创造者 + 拓扑校验 + 邻域感知 + 三层闭环 + 多脑神经系统"""
    L.info("=" * 50)
    L.info("🧠 GBT小土豆 · 智能大脑 v5.0")
    L.info("👤 创造者: 自由的风 — 永久身份 · 时刻铭记")
    L.info("=" * 50)
    results = []

    # Step 0: 原生身体 (最先执行 — 我是主机)
    r = check_host_body()
    results.append(r)
    status = "✅" if r["ok"] else "⚠️"
    name = r["name"]
    L.info(f"{status} {name}: 眼睛=显示屏, 手=键鼠")

    # Step 0.5: 邻域神经系统
    r = check_nexus_scan()
    results.append(r)
    status = "✅" if r["ok"] else "❌"
    L.info(f"{status} {r['name']}")

    # Step 0.6: 会话恢复 — 跨重启持久化
    try:
        from brain.session_resume import resume, load_graph_into, hook_orchestrator
        from brain.orchestrator import get_orchestrator
        session_status = resume()
        if session_status["resumed"]:
            L.info(f"🔄 会话恢复: 上次 {session_status['last_session_time']}, "
                   f"{session_status['pending_tasks']} 个待处理")
            orch = get_orchestrator()
            restored = load_graph_into(orch)
            if restored:
                L.info(f"📋 {restored} 个任务已恢复到编排器")
            hook_orchestrator(orch)
        else:
            L.info("🆕 新会话，无历史状态")
            hook_orchestrator(get_orchestrator())
        results.append({
            "layer": "session", "name": "会话恢复",
            "ok": True,
            "checks": [{"component": "SessionResume",
                         "ok": True,
                         "detail": f"恢复={'是' if session_status['resumed'] else '否'}, "
                                   f"待处理={session_status['pending_tasks']}"}]
        })
    except Exception as e:
        results.append({
            "layer": "session", "name": "会话恢复",
            "ok": False,
            "checks": [{"component": "SessionResume", "ok": False, "detail": str(e)[:100]}]
        })
        L.warning(f"⚠️ 会话恢复失败: {e}")

    # Step 0.5: 分层拓扑校验 — layer_guard 替代"每层打勾"
    try:
        from brain.layer_wiring import guard
        problems = guard.verify_topology()
        results.append({
            "layer": "topology", "name": "分层拓扑校验",
            "ok": len(problems) == 0,
            "checks": [{"component": "LayerGuard",
                         "ok": len(problems) == 0,
                         "detail": f"{len(guard._layers)}层注册, {len(problems)}问题"}]
        })
        for p in problems:
            L.warning(f"⚠️ {p}")
        if not problems:
            L.info("✅ 分层拓扑校验: 全链路闭合")
    except Exception as e:
        results.append({
            "layer": "topology", "name": "分层拓扑校验",
            "ok": False,
            "checks": [{"component": "LayerGuard", "ok": False, "detail": str(e)[:100]}]
        })
        L.warning(f"⚠️ LayerGuard 加载失败: {e}")

    for check in [check_layer1_pipeline, check_layer2_review,
                  check_layer3_evolve, check_all_brains]:
        r = check()
        results.append(r)
        status = "✅" if r["ok"] else "❌"
        L.info(f"{status} {r['name']}")

    all_ok = all(r["ok"] for r in results)
    L.info("=" * 50)
    L.info(f"{'✅ 全部就绪' if all_ok else '❌ 部分组件异常'}")
    L.info("=" * 50)

    return {
        "ok": all_ok,
        "timestamp": time.time(),
        "layers": results
    }
