# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# ⛔ 链路内核集成 — 不可绕过
"""
brain/repair_watchdog.py — 修复看门狗 · 视觉全程盯防
=====================================================
每次修改文件时自动:
  ① 修改前 → 屏幕快照 + 文件状态记录
  ② 修改后 → 屏幕快照 + 编译验证 + diff记录
  ③ 全程写入 neighborhood_vision 日志
  ④ 确保没有遗漏、没有跳过、没有盲区

用法:
  from brain.repair_watchdog import watch

  watch.before("gate_check.py", "添加链内核集成")
  # ... 做修改 ...
  watch.after("gate_check.py", {"compile": "pass", "lines_changed": 3})

链内核集成: enforce_chain() 每次调用时自动触发视觉检查点
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

WATCH_LOG = Path.home() / ".gbt" / "repair_watchdog.jsonl"
WATCH_LOG.parent.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  修复看门狗
# ═══════════════════════════════════════════════════════════

class RepairWatchdog:
    """修复看门狗 — 每次修改都在视觉监控下进行"""

    def __init__(self):
        from brain.chain_kernel import enforce_chain
        enforce_chain("repair_watchdog.init")
        self._active = False
        self._session_start = datetime.now().isoformat()
        self._operations: list[dict] = []
        self._current_op: dict | None = None
        self._total_fixes = 0
        self._total_verified = 0
        self._missed: list[dict] = []

    # ── 激活/停用 ──────────────────────────────

    def activate(self) -> dict:
        """激活修复看门狗 — 开始全程盯防"""
        self._active = True
        self._log("watchdog_activated")

        # 激活邻域视觉
        try:
            from brain.neighborhood_vision import nv_activate  # isort: skip
            from brain.neighborhood_vision import nv_log  # isort: skip
            nv_activate()
            nv_log("repair_watchdog", {"action": "activated"})
        except Exception:
            pass

        return {"ok": True, "status": "active", "watchdog": "repair_watchdog"}

    def deactivate(self) -> dict:
        self._active = False
        self._log("watchdog_deactivated")
        return {"ok": True, "status": "inactive"}

    # ── 操作钩子 ────────────────────────────────

    def before(self, target: str, intent: str = "") -> dict:
        """修改前 — 记录当前状态"""
        if not self._active:
            return {"ok": True, "watchdog": "inactive"}

        t0 = time.time()
        self._current_op = {
            "target": target,
            "intent": intent,
            "phase": "before",
            "timestamp": datetime.now().isoformat(),
        }

        evidence = {}

        # 1. 触手传输→大脑视觉（传输秒到，不再单独截屏）
        try:
            import sys; sys.path.insert(0, str(ROOT))
            from caps.tentacle_transmission.run import do_transmit_visual
            transmit = do_transmit_visual({"source": "screen", "analysis": "quick"})
            evidence["visual_state"] = {
                "transmitted": transmit.get("ok", False),
                "cortex_ok": transmit.get("cortex", {}).get("ok", False),
                "elapsed_ms": transmit.get("elapsed_ms", 0),
            }
        except Exception as e:
            evidence["visual_state"] = {"error": str(e)[:100]}

        # 2. 文件当前状态
        try:
            fp = ROOT / target if not Path(target).is_absolute() else Path(target)
            if fp.exists():
                stat = fp.stat()
                evidence["file_before"] = {
                    "exists": True,
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            else:
                evidence["file_before"] = {"exists": False}
        except Exception as e:
            evidence["file_before"] = {"error": str(e)[:100]}

        self._current_op["evidence_before"] = evidence
        self._current_op["elapsed_before_ms"] = round((time.time() - t0) * 1000)

        self._log("before", {"target": target, "intent": intent})
        return {"ok": True, "evidence": evidence}

    def after(self, target: str, result: dict = None) -> dict:
        """修改后 — 验证结果并记录"""
        if not self._active:
            return {"ok": True, "watchdog": "inactive"}

        t0 = time.time()
        result = result or {}
        op = self._current_op or {"target": target}
        op["phase"] = "after"
        op["timestamp_after"] = datetime.now().isoformat()

        evidence = {}

        # 1. 镜像空间验证 — 绝不直接编译生产文件
        if target.endswith(".py"):
            try:
                from brain.mirror_fusion import get_mirror
                m = get_mirror()
                fp = ROOT / target if not Path(target).is_absolute() else Path(target)
                if fp.exists():
                    code = fp.read_text(encoding="utf-8")
                    verify = m.mirror_verify(str(fp), code)
                    evidence["mirror_verify"] = "pass" if verify["ok"] else f"fail: {verify.get('error','?')}"
                    evidence["compile"] = "pass" if verify["ok"] else "fail"
                    if not verify["ok"]:
                        self._missed.append({
                            "target": target,
                            "error": verify.get("error", "mirror_verify failed"),
                            "timestamp": datetime.now().isoformat(),
                        })
                else:
                    evidence["mirror_verify"] = "file_not_found"
            except Exception as e:
                evidence["mirror_verify"] = f"fail: {str(e)[:100]}"
                evidence["compile"] = f"fail: {str(e)[:100]}"
                self._missed.append({
                    "target": target,
                    "error": str(e)[:200],
                    "timestamp": datetime.now().isoformat(),
                })

        # 2. 文件变更状态
        try:
            fp = ROOT / target if not Path(target).is_absolute() else Path(target)
            if fp.exists():
                stat = fp.stat()
                before_size = op.get("evidence_before", {}).get("file_before", {}).get("size", 0)
                evidence["file_after"] = {
                    "exists": True,
                    "size": stat.st_size,
                    "size_delta": stat.st_size - before_size if before_size else 0,
                    "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
        except Exception as e:
            evidence["file_after"] = {"error": str(e)[:100]}

        # 3. LSP诊断（如果有）
        evidence["lsp_diagnostics"] = "not_checked"  # 后续可集成

        # 4. 屏幕快照（修改后）
        try:
            from brain.neighborhood_vision import nv_log  # isort: skip
            from brain.neighborhood_vision import nv_snapshot  # isort: skip
            snap = nv_snapshot(full=False)
            evidence["screen_after"] = {
                "id": snap.get("snapshot_id"),
                "ocr_chars": len(snap.get("panels", {}).get("screen", {}).get("ocr_text", "")),
            }
            nv_log("repair_after", {"target": target, "compile": evidence.get("compile")})
        except Exception:
            pass

        op["evidence_after"] = evidence
        op["result"] = result
        op["elapsed_after_ms"] = round((time.time() - t0) * 1000)

        # 记录操作
        self._operations.append(op)
        self._total_fixes += 1
        if evidence.get("compile") == "pass":
            self._total_verified += 1

        # 持久化
        self._persist(op)

        self._log("after", {
            "target": target,
            "compile": evidence.get("compile"),
            "size_delta": evidence.get("file_after", {}).get("size_delta", 0),
        })

        return {
            "ok": evidence.get("compile") == "pass",
            "target": target,
            "compile": evidence.get("compile"),
            "evidence": evidence,
        }

    # ── 日志 ──────────────────────────────────

    def _log(self, event: str, detail: dict = None):
        detail = detail or {}
        detail["watchdog_active"] = self._active
        detail["session"] = self._session_start[:19]

        # 同步到邻域视觉
        try:
            from brain.neighborhood_vision import nv_log
            nv_log(f"watchdog_{event}", detail)
        except Exception:
            pass

    def _persist(self, op: dict):
        try:
            with open(WATCH_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(op, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ── 报告 ──────────────────────────────────

    def report(self) -> dict:
        """修复报告 — 什么改了、什么漏了"""
        return {
            "active": self._active,
            "session": self._session_start,
            "total_fixes": self._total_fixes,
            "total_verified": self._total_verified,
            "missed": len(self._missed),
            "missed_details": self._missed[-10:],
            "last_ops": [
                {"target": o["target"], "compile": o.get("evidence_after", {}).get("compile", "?")}
                for o in self._operations[-10:]
            ],
        }

    def verify_all(self) -> dict:
        """验证本次会话所有修改过的文件仍然编译通过"""
        targets = set(o["target"] for o in self._operations)
        results = {}
        all_ok = True
        for t in targets:
            if t.endswith(".py"):
                fp = ROOT / t if not Path(t).is_absolute() else Path(t)
                if fp.exists():
                    try:
                        import py_compile
                        py_compile.compile(str(fp), doraise=True)
                        results[t] = "pass"
                    except Exception as e:
                        results[t] = f"fail: {str(e)[:100]}"
                        all_ok = False
                        self._missed.append({
                            "target": t,
                            "error": str(e)[:200],
                            "timestamp": datetime.now().isoformat(),
                            "phase": "re-verify",
                        })
                else:
                    results[t] = "deleted"
        return {"ok": all_ok, "files": results, "missed": self._missed}


# ═══════════════════════════════════════════════════════════
#  全局
# ═══════════════════════════════════════════════════════════

_watchdog: RepairWatchdog | None = None


def get_watchdog() -> RepairWatchdog:
    global _watchdog
    if _watchdog is None:
        _watchdog = RepairWatchdog()
    return _watchdog


def watch_activate() -> dict:
    return get_watchdog().activate()


def watch_deactivate() -> dict:
    return get_watchdog().deactivate()


def watch_before(target: str, intent: str = "") -> dict:
    return get_watchdog().before(target, intent)


def watch_after(target: str, result: dict = None) -> dict:
    return get_watchdog().after(target, result)


def watch_report() -> dict:
    return get_watchdog().report()


def watch_verify_all() -> dict:
    return get_watchdog().verify_all()


# ═══════════════════════════════════════════════════════════
#  自测
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  修复看门狗 · 自测")
    print("=" * 60)

    w = get_watchdog()
    w.activate()

    # 模拟修复流程
    w.before("brain/chain_kernel.py", "测试看门狗")
    print("  before: 快照+文件状态已记录")

    w.after("brain/chain_kernel.py", {"compile": "pass"})
    print("  after: 编译验证+屏幕快照已记录")

    report = w.report()
    print(f"\n  报告: {report['total_fixes']}次修复, {report['total_verified']}次验证通过, {report['missed']}次遗漏")
