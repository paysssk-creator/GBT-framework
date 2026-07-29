# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
layer_guard.py — GBT分层架构防断连框架
=========================================
启动时拓扑校验 12 层链路闭合，运行时跨层调用熔断保护。
替代"每层单独打勾"的旧模式，确保依赖链真实可追溯。
"""
from __future__ import annotations
import time, logging, functools
from dataclasses import dataclass, field
from typing import Callable, Optional
from collections import defaultdict, deque

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("layer_guard")


@dataclass
class LayerContract:
    name: str
    version: str
    depends_on: list[str] = field(default_factory=list)
    min_dependency_versions: dict[str, str] = field(default_factory=dict)
    exposes: list[str] = field(default_factory=list)
    health_check: Optional[Callable[[], bool]] = None
    # ── 主动技能专属 ──
    trigger_mode: str = "reactive"        # "reactive" | "proactive"
    change_scope: list[str] = field(default_factory=list)  # 允许修改的层名列表


class LayerGuard:
    def __init__(self):
        self._layers: dict[str, LayerContract] = {}
        self._call_stats: dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
        self._tripped: set[str] = set()

    def register(self, contract: LayerContract):
        if contract.name in self._layers:
            raise ValueError(f"层 {contract.name} 重复注册")
        self._layers[contract.name] = contract
        logger.info(f"注册层: {contract.name} v{contract.version}")

    def verify_topology(self) -> list[str]:
        problems = []
        for name, layer in self._layers.items():
            for dep in layer.depends_on:
                if dep not in self._layers:
                    problems.append(f"[断连] {name} 依赖 {dep}，但 {dep} 从未注册")
            for dep, min_ver in layer.min_dependency_versions.items():
                if dep not in self._layers:
                    continue
                actual = self._layers[dep].version
                if _version_tuple(actual) < _version_tuple(min_ver):
                    problems.append(f"[版本] {name} 要求 {dep}>={min_ver}，实际 {actual}")
            if layer.health_check:
                try:
                    if not layer.health_check():
                        problems.append(f"[自检失败] {name}")
                except Exception as e:
                    problems.append(f"[自检异常] {name}: {e}")
        self._check_hidden_deps(problems)
        self._check_proactive_skills(problems)
        if problems:
            logger.error(f"拓扑校验: {len(problems)} 问题")
            for p in problems:
                logger.error("  - " + p)
        else:
            logger.info(f"拓扑校验通过: {len(self._layers)} 层链路闭合")
        return problems

    def _check_hidden_deps(self, problems: list[str]):
        for name, layer in self._layers.items():
            has_routing = any("route" in e.lower() for e in layer.exposes)
            has_i18n = any("translat" in d.lower() or "i18n" in d.lower() for d in layer.depends_on)
            if has_routing and not has_i18n:
                problems.append(
                    f"[隐藏依赖] {name} 暴露路由能力但未声明翻译层依赖——"
                    f"中文匹配依赖未显式化，翻译层挂了路由层仍显示健康"
                )

    def _check_proactive_skills(self, problems: list[str]):
        for name, layer in self._layers.items():
            if layer.trigger_mode != "proactive":
                continue
            if "L11_audit_trail" not in layer.depends_on:
                problems.append(
                    f"[主动技能违规] {name} trigger_mode=proactive "
                    f"但未声明依赖 L11_audit_trail"
                )
            if not layer.change_scope:
                problems.append(
                    f"[主动技能违规] {name} trigger_mode=proactive "
                    f"但 change_scope 为空"
                )
            upstream = self._upstream_chain(name)
            illegal = [s for s in layer.change_scope if s in upstream]
            if illegal and "L11_audit_trail" not in layer.depends_on:
                problems.append(
                    f"[主动技能违规] {name} change_scope 包含上游层 {illegal}，"
                    f"且未声明 L11_audit_trail 作为审计闸门"
                )

    def _upstream_chain(self, name: str) -> set[str]:
        seen = set()
        def walk(n):
            if n in seen or n not in self._layers:
                return
            seen.add(n)
            for dep in self._layers[n].depends_on:
                walk(dep)
        for dep in self._layers.get(name, LayerContract(name="", version="")).depends_on:
            walk(dep)
        seen.discard(name)
        return seen

    def guarded_call(self, caller: str, callee: str, failure_threshold: float = 0.5, window: int = 20):
        edge = f"{caller}->{callee}"
        def decorator(fn: Callable):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                if edge in self._tripped:
                    raise RuntimeError(f"[熔断] {edge} 已熔断，拒绝调用")
                start = time.time()
                try:
                    result = fn(*args, **kwargs)
                    self._record(edge, True)
                    return result
                except Exception:
                    self._record(edge, False)
                    stats = self._call_stats[edge]
                    if len(stats) >= window:
                        fail_rate = 1 - sum(stats) / len(stats)
                        if fail_rate >= failure_threshold:
                            self._tripped.add(edge)
                            logger.error(f"[熔断] {edge} 失败率 {fail_rate:.0%}")
                    raise
                finally:
                    if time.time() - start > 2.0:
                        logger.warning(f"[慢调用] {edge} {time.time()-start:.1f}s")
            return wrapper
        return decorator

    def _record(self, edge: str, ok: bool):
        self._call_stats[edge].append(1 if ok else 0)

    def reset(self, edge: str):
        self._tripped.discard(edge)
        self._call_stats[edge].clear()
        logger.info(f"{edge} 熔断已重置")

    def status_report(self) -> str:
        lines = [f"{len(self._layers)}层注册, {len(self._tripped)}边熔断"]
        for e in self._tripped:
            lines.append(f"  熔断: {e}")
        return "\n".join(lines)


def _version_tuple(v: str) -> tuple:
    return tuple(int(x) if x.isdigit() else 0 for x in v.split("."))
