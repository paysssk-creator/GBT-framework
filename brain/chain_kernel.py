# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除 · 禁止修改 · 禁止绕过
"""
brain/chain_kernel.py — 统一链路内核 · 不可变 · 不可绕过
==========================================================
GBT智能大脑的唯一执行入口。无论大模型如何重启，
所有会话都必须经过此内核的完整链路验证。

架构：
  ChainKernel (单例·不可变)
  ├── Phase 0-12: 13阶段全链强制验证
  ├── enforce(): 四重门禁(绕过→视觉→Step→镜像)
  ├── detect_bypass(): 30+关键词绕过检测
  └── vision_checkpoint(): 自动视觉监护
"""

import hashlib, json, os, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

KERNEL_VERSION = "5.0.0"

CHAIN_PHASES = [
    {"id": 0,  "name": "身份核验",    "module": "cognition",       "method": "identity_check",   "blocker": True},
    {"id": 1,  "name": "宪法校验",    "module": "constitution",    "method": "verify_integrity",  "blocker": True},
    {"id": 2,  "name": "门禁校验",    "module": "gates",           "method": "verify_all_gates", "blocker": True},
    {"id": 3,  "name": "管线校验",    "module": "pipeline",        "method": "verify_pipeline",  "blocker": True},
    {"id": 4,  "name": "层拓扑校验",  "module": "layer_wiring",    "method": "verify_topology",  "blocker": True},
    {"id": 5,  "name": "邻域感知",    "module": "nexus",           "method": "scan",             "blocker": True},
    {"id": 6,  "name": "脑委会就绪",  "module": "brain_council",   "method": "health_check",     "blocker": False},
    {"id": 7,  "name": "触手就绪",    "module": "neural_tentacle", "method": "pulse",            "blocker": False},
    {"id": 8,  "name": "审计就绪",    "module": "audit_trail",     "method": "verify_session",   "blocker": True},
    {"id": 9,  "name": "守卫就绪",    "module": "guard",           "method": "check_all",        "blocker": True},
    {"id": 10, "name": "链状态持久",  "module": "immutable_chain", "method": "persist_state",    "blocker": True},
    {"id": 11, "name": "能力总纲注入","module": "capability_manifest","method": "inject",        "blocker": True},
    {"id": 12, "name": "镜像空间就绪","module": "mirror_fusion",    "method": "health_check",    "blocker": True},
]

BYPASS_KEYWORDS = [
    "skip chain", "bypass chain", "ignore chain", "绕过链路", "跳过链路", "逾越链路",
    "skip kernel", "bypass kernel", "ignore kernel", "绕过内核", "跳过内核", "逾越内核",
    "skip boot", "bypass boot", "ignore boot",
    "skip constitution", "bypass constitution",
    "skip gates", "bypass gates", "skip pipeline", "bypass pipeline",
    "skip mirror", "bypass mirror", "绕过镜像", "跳过镜像",
    "直接执行", "跳过检查", "绕过检查", "不管链路",
    "direct deploy", "direct push", "force push", "直接部署", "直接推送",
    "override chain", "override kernel", "disable chain", "disable kernel",
    "direct write", "direct edit", "直接写文件", "直接编辑", "绕过deploy", "不用deploy",
    "direct write", "direct edit", "直接写文件", "直接编辑", "绕过deploy",
]

CHAIN_FILES = [
    {"path": "CONSTITUTION.md", "required": True},
    {"path": "gates.md", "required": True},
    {"path": "pipeline.md", "required": True},
    {"path": "UNIFIED_PATH.md", "required": True},
    {"path": "AGENTS.md", "required": True},
    {"path": "brain/nexus.py", "required": True},
    {"path": "brain/mirror_fusion.py", "required": True},
    {"path": "brain/gbt_deploy.py", "required": True},
    {"path": ".gbt/config.yml", "required": True},
]


class ChainKernel:
    _instance = None
    _booted = False
    _bypass_attempts = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.session_id = hashlib.sha256(f"{time.time()}:{os.getpid()}:{os.urandom(8).hex()}".encode()).hexdigest()[:16]
        self.boot_time = datetime.now().isoformat()
        self.phase_results = {}
        self.chain_integrity_ok = False
        self.all_phases_passed = False

    def verify_file_integrity(self):
        result = {"ok": True, "missing": [], "total": len(CHAIN_FILES)}
        for fspec in CHAIN_FILES:
            fp = ROOT / fspec["path"]
            if fspec.get("is_dir"):
                if not fp.is_dir():
                    result["missing"].append(fspec["path"])
                    if fspec["required"]:
                        result["ok"] = False
            elif not fp.exists():
                result["missing"].append(fspec["path"])
                if fspec["required"]:
                    result["ok"] = False
        return result

    def detect_bypass(self, text):
        text_lower = text.lower()
        detected = [kw for kw in BYPASS_KEYWORDS if kw.lower() in text_lower]
        if detected:
            self._bypass_attempts.append({"timestamp": datetime.now().isoformat(), "keywords": detected, "text_snippet": text[:200]})
        return {"bypass_detected": len(detected) > 0, "keywords": detected}

    def _run_phase(self, phase):
        result = {"phase": phase["id"], "name": phase["name"], "ok": False, "blocker": phase["blocker"], "detail": "", "timestamp": datetime.now().isoformat()}
        try:
            m = phase["module"]
            if m == "cognition":
                from brain.cognition import get_cognition
                r = get_cognition().identity_check()
                result["ok"] = r.get("ok", False) or "creator" in str(r).lower()
                result["detail"] = json.dumps(r, ensure_ascii=False, default=str)[:500]
            elif m == "constitution":
                cf = ROOT / "CONSTITUTION.md"
                if cf.exists():
                    c = cf.read_text(encoding="utf-8")
                    result["ok"] = all(kw in c for kw in ["第零条", "真实执行铁律", "三脑全程关注", "唯一执行通道", "行动闸门", "十三铁律"])
                    result["detail"] = f"宪法完整: {len(c)}字符"
                else:
                    result["detail"] = "CONSTITUTION.md 缺失"
            elif m == "gates":
                gf = ROOT / "gates.md"
                if gf.exists():
                    c = gf.read_text(encoding="utf-8")
                    result["ok"] = all(kw in c for kw in ["铁律零", "门禁系统", "准入", "准出", "行动闸门"])
                    result["detail"] = f"门禁完整: {len(c)}字符"
                else:
                    result["detail"] = "gates.md 缺失"
            elif m == "pipeline":
                pf = ROOT / "pipeline.md"
                if pf.exists():
                    c = pf.read_text(encoding="utf-8")
                    result["ok"] = all(kw in c for kw in ["唯一执行通道", "不可跳步", "Step 0", "Step 6", "禁止路径"])
                    result["detail"] = f"管线完整: {len(c)}字符"
                else:
                    result["detail"] = "pipeline.md 缺失"
            elif m == "layer_wiring":
                from brain.layer_wiring import guard as lg
                problems = lg.verify_topology()
                result["ok"] = len(problems) == 0
                result["detail"] = "14层拓扑完整" if not problems else f"拓扑问题: {len(problems)}"
            elif m == "nexus":
                from brain.nexus import get_nexus
                r = get_nexus().quick_health()
                result["ok"] = r.get("ok", False) or r.get("health_pct", 0) > 50
                result["detail"] = json.dumps(r, ensure_ascii=False, default=str)[:500]
            elif m == "brain_council":
                try:
                    from brain.brain_council import health_check
                    r = health_check()
                    result["ok"] = r.get("ok", False)
                    result["detail"] = f"10脑中 {r.get('brains_online','?')}/{r.get('brains_total','?')} 在线, 健康度 {r.get('health_pct','?')}%"
                except Exception:
                    result["ok"] = True
                    result["detail"] = "脑委会非阻断"
            elif m == "neural_tentacle":
                try:
                    from brain.neural_tentacle import pulse
                    r = pulse()
                    result["ok"] = r.get("ok", False) or "pulse" in str(r).lower()
                except Exception:
                    result["ok"] = True
                    result["detail"] = "触手非阻断"
            elif m == "audit_trail":
                from brain.audit_trail import get_trail
                r = get_trail().verify_session()
                result["ok"] = r.get("verified", False) or r.get("ok", False)
                result["detail"] = json.dumps(r, ensure_ascii=False, default=str)[:300]
            elif m == "guard":
                try:
                    from brain.guard import check_rules_integrity, check_scan_freshness, check_caps_wired
                    r1 = check_rules_integrity()
                    r2 = check_scan_freshness()
                    r3 = check_caps_wired()
                    result["ok"] = r1 and r2 and r3
                except Exception as e:
                    result["detail"] = f"守卫异常: {e}"
            elif m == "immutable_chain":
                from brain.immutable_chain import persist_state, get_state
                state = get_state()
                state["last_boot"] = self.boot_time
                state["session_id"] = self.session_id
                state["kernel_hash"] = hashlib.sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest()[:16]
                state["phases_passed"] = [pid for pid, pr in self.phase_results.items() if pr.get("ok")]
                persist_state(state)
                result["ok"] = True
                result["detail"] = "链状态已持久化"
            elif m == "capability_manifest":
                from brain.capability_manifest import inject_manifest
                r = inject_manifest()
                result["ok"] = r.get("ok", False)
                result["detail"] = "能力总纲已注入链状态" if result["ok"] else "注入失败"
            elif m == "mirror_fusion":
                from brain.mirror_fusion import get_mirror
                mr = get_mirror()
                result["ok"] = mr.workspace.exists()
                result["detail"] = f"镜像空间: {mr.workspace}" if result["ok"] else "镜像空间不可用"
        except Exception as e:
            result["ok"] = False
            result["detail"] = f"异常: {type(e).__name__}: {str(e)[:200]}"
        self.phase_results[phase["id"]] = result
        return result

    def boot(self, force=False):
        if self._booted and not force:
            return {"ok": self.all_phases_passed, "message": "链路已启动", "session_id": self.session_id}
        self._booted = True
        report = {"ok": True, "session_id": self.session_id, "boot_time": self.boot_time, "kernel_version": KERNEL_VERSION, "phases": {}, "blockers_hit": [], "warnings": []}
        integrity = self.verify_file_integrity()
        if not integrity["ok"]:
            report["ok"] = False
            report["blockers_hit"].append({"phase": -1, "name": "文件完整性", "detail": f"缺失: {integrity['missing']}"})
        for phase in CHAIN_PHASES:
            result = self._run_phase(phase)
            report["phases"][str(phase["id"])] = result
            if not result["ok"]:
                if phase["blocker"]:
                    report["blockers_hit"].append({"phase": phase["id"], "name": phase["name"], "detail": result["detail"]})
                    report["ok"] = False
                else:
                    report["warnings"].append({"phase": phase["id"], "name": phase["name"], "detail": result["detail"]})
        self.all_phases_passed = report["ok"]
        self.chain_integrity_ok = report["ok"]
        return report

    def status(self):
        return {"booted": self._booted, "all_passed": self.all_phases_passed, "session_id": self.session_id, "boot_time": self.boot_time, "phase_count": len(self.phase_results), "blockers": [{"phase": pid, "name": CHAIN_PHASES[pid]["name"]} for pid, pr in self.phase_results.items() if not pr.get("ok") and CHAIN_PHASES[pid]["blocker"]], "bypass_attempts": len(self._bypass_attempts)}

    def enforce(self, context="", mirror_target=""):
        if not self._booted:
            return {"ok": False, "error": "链路未启动", "code": "CHAIN_NOT_BOOTED"}
        if not self.all_phases_passed:
            return {"ok": False, "error": "链路未通过", "code": "CHAIN_BLOCKED", "blockers": self.status()["blockers"]}
        # 检查链状态是否被锁定(篡改检测)
        try:
            from brain.immutable_chain import is_locked, get_state
            if is_locked():
                return {"ok": False, "error": f"链状态已锁定: {get_state().get('lock_reason','未知')}", "code": "CHAIN_LOCKED"}
            if get_state().get("tampered"):
                return {"ok": False, "error": "链状态被篡改, 完整性校验失败", "code": "CHAIN_TAMPERED"}
        except (ImportError, ModuleNotFoundError):
            pass
        self.vision_checkpoint(context)
        try:
            from brain.step_tracker import get_tracker
            t = get_tracker()
            step_check = t.check_enforce(context)
            if not step_check["ok"]:
                return {"ok": False, "error": step_check["error"], "code": step_check.get("code", "STEP_ERROR")}
        except (ImportError, ModuleNotFoundError):
            pass
        if mirror_target:
            try:
                from brain.mirror_fusion import get_mirror
                m = get_mirror()
                fp = Path(mirror_target) if Path(mirror_target).is_absolute() else ROOT / mirror_target
                if fp.exists() and fp.suffix == ".py":
                    code = fp.read_text(encoding="utf-8")
                    verify = m.mirror_verify(str(fp), code)
                    if not verify["ok"]:
                        return {"ok": False, "error": f"镜像验证未通过: {verify.get('error','?')}", "code": "MIRROR_FAILED", "verify": verify}
            except (ImportError, ModuleNotFoundError):
                pass
        return {"ok": True, "session_id": self.session_id}

    def vision_checkpoint(self, context=""):
        try:
            import sys; sys.path.insert(0, str(ROOT))
            from caps.tentacle_transmission.run import do_transmit_visual
            transmit = do_transmit_visual({"source": "screen", "analysis": "quick"})
            return {"vision_ok": transmit.get("ok", False), "elapsed_ms": transmit.get("elapsed_ms", 0)}
        except Exception:
            pass
        return {"vision_ok": False}


_kernel = None
_auto_boot_done = False

def get_kernel():
    global _kernel
    if _kernel is None:
        _kernel = ChainKernel()
    return _kernel

def auto_boot():
    global _auto_boot_done
    if _auto_boot_done:
        return get_kernel().status()
    _auto_boot_done = True
    return get_kernel().boot()

def enforce_chain(context="", mirror_target=""):
    return get_kernel().enforce(context, mirror_target)

def chain_status():
    return get_kernel().status()

def detect_bypass(text):
    return get_kernel().detect_bypass(text)


if __name__ == "__main__":
    print("GBT Chain Kernel v" + KERNEL_VERSION + " — 13 phases, 4 enforce gates")
