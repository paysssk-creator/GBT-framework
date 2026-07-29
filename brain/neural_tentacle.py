# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/neural_tentacle.py — 神经触手 · 实时代码健康监控 v1.0
==========================================================
像光纤一样持续传输代码健康数据到邻域神经网络。

架构:
  ┌─────────────────────────────────────────────┐
架构:
  ┌──────────────────────────────────────────────┐
  │  NeuralTentacle (神经触手)                     │
  │  ┌─────────┐ ┌──────────┐ ┌──────────────┐  │
  │  │ 扫描器   │→│ 差分引擎  │→│ 告警/自愈     │  │
  │  │(穿透L0-L7)│ │(变化检测) │ │(auto_fix)    │  │
  │  └─────────┘ └──────────┘ └──────────────┘  │
  │  ┌──────────────────────────────────────┐   │
  │  │ 视觉触手 (VisionTentacle)              │   │
  │  │ 📸屏幕 📋剪贴板 🌐URL 📁文件 📷摄像头  │   │
  │  └──────────────────────────────────────┘   │
  │         ↓                                    │
  │  ┌──────────────────────────────────────┐   │
  │  │  邻域总线 (NexusHub)                   │   │
  │  └──────────────────────────────────────┘   │
  └──────────────────────────────────────────────┘

用法:
  python brain/neural_tentacle.py                # 单次扫描+注入
  python brain/neural_tentacle.py --watch 30     # 每30秒持续监控
  python brain/neural_tentacle.py --auto-heal    # 自动修复模式
"""
import sys, os, json, time, threading
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

TENTACLE_DIR = Path.home() / ".gbt" / "neural_tentacle"
TENTACLE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = TENTACLE_DIR / "tentacle_state.json"
ISSUES_FILE = TENTACLE_DIR / "known_issues.json"
SNAPSHOT_DIR = TENTACLE_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


class NeuralTentacle:
    """神经触手 — 持续监控代码健康，像光纤一样传输数据"""

    def __init__(self, auto_heal: bool = False):
        self.auto_heal = auto_heal
        self.state = self._load_state()
        self.known_issues = self._load_issues()
        self._running = False
        self._last_scan: Optional[dict] = None
        self._scan_count = self.state.get("total_scans", 0)
        self._issues_found_total = self.state.get("total_issues_found", 0)
        self._issues_fixed_total = self.state.get("total_issues_fixed", 0)

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"total_scans": 0, "total_issues_found": 0, "total_issues_fixed": 0,
                "started_at": None, "last_scan_at": None}

    def _save_state(self):
        self.state["total_scans"] = self._scan_count
        self.state["total_issues_found"] = self._issues_found_total
        self.state["total_issues_fixed"] = self._issues_fixed_total
        self.state["last_scan_at"] = datetime.now().isoformat()
        STATE_FILE.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_issues(self) -> dict:
        if ISSUES_FILE.exists():
            try:
                return json.loads(ISSUES_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_issues(self):
        ISSUES_FILE.write_text(json.dumps(self.known_issues, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_snapshot(self, result: dict):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap = SNAPSHOT_DIR / f"scan_{ts}.json"
        snap.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    def scan(self) -> dict:
        """执行一次穿透扫描"""
        from brain.penetration_scan import run_full_scan
        result = run_full_scan(auto_fix_enabled=self.auto_heal)
        self._scan_count += 1
        self._last_scan = result
        return result

    def diff(self, new_result: dict) -> dict:
        """对比新旧扫描结果，检测变化"""
        changes = {"new_issues": [], "fixed_issues": [], "changed_caps": []}

        if not self._last_scan:
            # 首次扫描，所有问题都是新的
            for name, layer in new_result.get("layers", {}).items():
                for issue in layer.get("detail", []):
                    if issue["level"] == "error":
                        changes["new_issues"].append(issue)
            return changes

        # 对比各层
        old_layers = self._last_scan.get("layers", {})
        new_layers = new_result.get("layers", {})

        for name in set(list(old_layers.keys()) + list(new_layers.keys())):
            old_errors = old_layers.get(name, {}).get("errors", 0)
            new_errors = new_layers.get(name, {}).get("errors", 0)

            if new_errors > old_errors:
                changes["changed_caps"].append({
                    "layer": name,
                    "change": f"+{new_errors - old_errors} errors",
                    "direction": "worse"
                })
            elif new_errors < old_errors:
                changes["changed_caps"].append({
                    "layer": name,
                    "change": f"-{old_errors - new_errors} errors",
                    "direction": "better"
                })

            # 追踪具体issue变化
            new_detail = {i.get("msg", ""): i for i in new_layers.get(name, {}).get("detail", [])}
            old_detail = {i.get("msg", ""): i for i in old_layers.get(name, {}).get("detail", [])}
            for msg in set(new_detail.keys()) - set(old_detail.keys()):
                if new_detail[msg].get("level") == "error":
                    changes["new_issues"].append(new_detail[msg])
            for msg in set(old_detail.keys()) - set(new_detail.keys()):
                if old_detail[msg].get("level") == "error":
                    changes["fixed_issues"].append(old_detail[msg])

        return changes

    def inject_to_nexus(self, result: dict):
        """将扫描结果注入邻域神经系统"""
        try:
            from brain.nexus import get_nexus
            nexus = get_nexus()

            # 更新邻域健康数据
            health = 100.0 if result["ok"] else max(0, 100 - result["total_errors"] * 2)
            nexus._scan_cache = {
                "ok": result["ok"],
                "health_pct": health,
                "total_caps": 210,
                "found": 210,
                "tentacle_scan": True,
                "timestamp": time.time(),
                "total_issues": result["total_issues"],
                "total_errors": result["total_errors"],
                "fixes": result.get("fixes_applied", 0),
            }
            nexus._last_scan = time.time()
            return True
        except Exception:
            return False

    def inject_to_memory(self, result: dict):
        """将结果写入持久化记忆"""
        try:
            memory_file = ROOT / "memory_store.json"
            if memory_file.exists():
                memory = json.loads(memory_file.read_text(encoding="utf-8"))
            else:
                memory = {}
            memory["neural_tentacle"] = {
                "last_scan": datetime.now().isoformat(),
                "health": "OK" if result["ok"] else "DEGRADED",
                "total_scans": self._scan_count,
                "total_errors": result["total_errors"],
                "total_issues": result["total_issues"],
            }
            memory_file.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


    def pulse(self) -> dict:
        """一次完整脉冲: 扫描 → 差分 → 注入邻域 → 持久化 → 吞噬"""
        t0 = time.time()

        # 扫描
        result = self.scan()
        changes = self.diff(result)

        # 注入
        nexus_injected = self.inject_to_nexus(result)
        self.inject_to_memory(result)
        self._save_state()

        # 快照
        if changes["new_issues"] or changes["fixed_issues"]:
            self._save_snapshot(result)
            self._issues_found_total += len(changes["new_issues"])
            self._issues_fixed_total += result.get("fixes_applied", 0)

        # 吞噬 - 扫描结果立刻吞噬进化
        devour_result = None
        try:
            from brain.devour_tentacle import get_devourer, devour_pulse
            d = get_devourer()
            # 吞噬扫描结果(学习自身问题)
            devour_result = d.devour_scan_results({"layers": {
                "penetration_scan": {"detail": [
                    {"level": "error", "msg": f"扫描完成, {result['total_errors']}错误", "cap": "system"}
                ]}
            }})
            # 同时吞噬外部(发现新技能)
            ext = devour_pulse()
            if ext.get("ok"):
                devour_result["external"] = ext
        except:
            pass
        nav_result = None
        try:
            from brain.navigation_tentacle import navigate
            nav_result = navigate()
        except:
            pass

        elapsed = time.time() - t0
        return {
            "ok": result["ok"],
            "elapsed_ms": int(elapsed * 1000),
            "scan_count": self._scan_count,
            "total_errors": result["total_errors"],
            "total_issues": result["total_issues"],
            "new_issues": len(changes["new_issues"]),
            "fixed_issues": len(changes["fixed_issues"]),
            "fixes_applied": result.get("fixes_applied", 0),
            "nexus_injected": nexus_injected,
            "devour": devour_result,
            "navigation": nav_result,
            "timestamp": datetime.now().isoformat(),
        }
    def vision_see(self, channel: str = "screen") -> dict:
        """视觉脉冲 - 通过指定通道看 + 存入视觉记忆"""
        try:
            from brain.vision_tentacle import see as vision_see
            r = vision_see(channel)
            if r.get("ok"):
                v = __import__("brain.vision_tentacle", fromlist=["get_vision"]).get_vision()
                v.save(r)
                # 存入视觉记忆(脑海)
                try:
                    from brain.visual_memory import remember
                    remember(r)
                except:
                    pass
            return r
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}


        elapsed = time.time() - t0

        return {
            "ok": result["ok"],
            "elapsed_ms": int(elapsed * 1000),
            "scan_count": self._scan_count,
            "total_errors": result["total_errors"],
            "total_issues": result["total_issues"],
            "new_issues": len(changes["new_issues"]),
            "fixed_issues": len(changes["fixed_issues"]),
            "fixes_applied": result.get("fixes_applied", 0),
            "nexus_injected": nexus_ok,
            "timestamp": datetime.now().isoformat(),
        }

    def watch(self, interval: int = 60):
        """持续监控模式 — 像光纤一样不间断传输"""
        if not self.state.get("started_at"):
            self.state["started_at"] = datetime.now().isoformat()
            self._save_state()

        self._running = True
        print(f"🧬 神经触手已激活 · 每{interval}秒脉冲 · 自动修复={'开' if self.auto_heal else '关'}")
        print(f"   数据目录: {TENTACLE_DIR}")
        print(f"   Ctrl+C 停止")
        print()

        while self._running:
            try:
                pulse = self.pulse()
                status = "🟢" if pulse["ok"] else "🔴"
                print(f"  {status} [{pulse['timestamp'][11:19]}] "
                      f"扫描#{pulse['scan_count']} "
                      f"错误{pulse['total_errors']} "
                      f"新增{pulse['new_issues']} "
                      f"修复{pulse['fixed_issues']} "
                      f"自愈{pulse['fixes_applied']} "
                      f"| {pulse['elapsed_ms']}ms")

                time.sleep(interval)
            except KeyboardInterrupt:
                self._running = False
                print("\n💤 神经触手休眠")
            except Exception as e:
                print(f"  ⚠️ 脉冲异常: {e}")
                time.sleep(interval)

    def stop(self):
        self._running = False


# ═══════════════ 全局单例 ═══════════════
_tentacle: Optional[NeuralTentacle] = None


def get_tentacle(auto_heal: bool = False) -> NeuralTentacle:
    global _tentacle
    if _tentacle is None:
        _tentacle = NeuralTentacle(auto_heal=auto_heal)
    return _tentacle


def pulse() -> dict:
    """快捷脉冲"""
    t = get_tentacle()
    return t.pulse()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="GBT 神经触手 · 实时代码健康监控")
    p.add_argument("--watch", type=int, metavar="SEC", help="持续监控间隔(秒)")
    p.add_argument("--auto-heal", action="store_true", help="自动修复模式")
    p.add_argument("--once", action="store_true", help="单次脉冲")
    args = p.parse_args()

    tentacle = NeuralTentacle(auto_heal=args.auto_heal)

    if args.watch:
        tentacle.watch(interval=args.watch)
    else:
        # 单次脉冲
        result = tentacle.pulse()
        print(f"\n🧬 神经触手脉冲 #{result['scan_count']}")
        print(f"   状态: {'🟢 健康' if result['ok'] else '🔴 异常'}")
        print(f"   错误: {result['total_errors']} | 新增: {result['new_issues']} | 修复: {result['fixed_issues']}")
        print(f"   自愈: {result['fixes_applied']} | 邻域注入: {'✅' if result['nexus_injected'] else '❌'}")
        print(f"   耗时: {result['elapsed_ms']}ms")
