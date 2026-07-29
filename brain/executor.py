# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/executor.py — 统一自主执行引擎
======================================
无限制子代理 + 思维导图驱动 + 卡点自主解析 + 完美交付循环

循环:
  思维导图分解 → 隔离子代理执行 → 卡点检测 →
  四脑分析 → 全网搜索 → 更精细思维导图 →
  继续执行 → 反复循环 → 完美交付

铁律:
  - 无限子代理，全隔离执行
  - 卡点绝不跳过，必须返回四脑
  - 每次卡点生成更精细的思维导图
  - 反复循环直到完美
  - 拒绝残次品交付
"""
import json, time, threading, subprocess, traceback, shlex, sys, os
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from brain.audit_trail import log as audit_log
# ═ 邻域接入: circuit_breaker → 包裹 cap 执行
def _with_circuit_breaker(cap_name, fn, *args, **kwargs):
    from brain.chain_kernel import enforce_chain
    enforce_chain(f"executor.call_{cap_name}")

    """熔断器包裹: 调用前检查 → 执行 → 上报结果"""
    try:
        sys.path.insert(0, str(ROOT))
        from caps.circuit_breaker.run import do_enforce_before_call, do_report_result
        check = do_enforce_before_call({"cap": cap_name})
        if check.get("state") == "open":
            print(f"[CircuitBreaker] ⚡ {cap_name} 熔断中 — 跳过调用", flush=True)
            return {"ok": False, "blocked": "circuit_breaker_open", "cap": cap_name}
        result = fn(*args, **kwargs)
        ok = result.get("ok", False) if isinstance(result, dict) else bool(result)
        do_report_result({"cap": cap_name, "success": ok})
        return result
    except Exception as e:
        print(f"[CircuitBreaker] 跳过(故障): {e}", flush=True)
        return fn(*args, **kwargs)  # 熔断器自身故障不阻塞


ROOT = Path(__file__).parent.parent
SANDBOX_DIR = ROOT / "sandbox" / "executor_sandboxes"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


class SubAgent:
    """隔离子代理 — 独立沙盒中执行单个子任务"""

    def __init__(self, agent_id: str, task: dict, sandbox_path: Path):
        self.agent_id = agent_id
        self.task = task
        self.sandbox = sandbox_path
        self.status = "created"
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None

    def execute(self) -> dict:
        """在隔离沙盒中执行子任务"""
        self.status = "running"
        self.start_time = time.time()
        self.sandbox.mkdir(parents=True, exist_ok=True)

        try:
            # 写入任务文件
            task_file = self.sandbox / "task.json"
            task_file.write_text(json.dumps(self.task, ensure_ascii=False), encoding="utf-8")

            # 在隔离目录中执行
            action = self.task.get("action", "")
            code = self.task.get("code", "")
            command = self.task.get("command", "")
            audit_log("agent_start", {"agent_id": self.agent_id, "action": action or command or code[:60]}, 
                      instruction=action or command or code[:60], phase="executing")

            if code:
                script = self.sandbox / "script.py"
                script.write_text(code, encoding="utf-8")
                result = subprocess.run(
                    ["python", str(script)],
                    capture_output=True, text=True,
                    timeout=self.task.get("timeout", 60),
                    cwd=str(self.sandbox)
                )
                self.result = {
                    "ok": result.returncode == 0,
                    "stdout": result.stdout[:5000],
                    "stderr": result.stderr[:2000],
                    "returncode": result.returncode
                }
            elif command:
                # 安全: 不使用 shell=True, 用 shlex 解析命令为列表
                if isinstance(command, str):
                    cmd_parts = shlex.split(command)
                else:
                    cmd_parts = list(command)
                result = subprocess.run(
                    cmd_parts, shell=False,
                    capture_output=True, text=True,
                    timeout=self.task.get("timeout", 60),
                    cwd=str(self.sandbox)
                )
                self.result = {
                    "ok": result.returncode == 0,
                    "stdout": result.stdout[:5000],
                    "stderr": result.stderr[:2000],
                    "returncode": result.returncode
                }
            else:
                self.result = {"ok": True, "output": f"Agent {self.agent_id} 完成: {action}"}

            self.status = "completed" if self.result.get("ok") else "failed"
            audit_log("agent_done", {"agent_id": self.agent_id, "ok": self.result.get("ok"), 
                      "returncode": self.result.get("returncode")}, phase="completed")
        except subprocess.TimeoutExpired:
            self.result = {"ok": False, "error": "执行超时"}
            self.status = "failed"
            audit_log("agent_timeout", {"agent_id": self.agent_id, "action": action or command}, phase="timeout")
        except Exception as e:
            self.result = {"ok": False, "error": str(e)}
            self.status = "failed"
            self.error = traceback.format_exc()
            audit_log("agent_error", {"agent_id": self.agent_id, "error": str(e)[:200]}, phase="error")

        self.end_time = time.time()
        return self.to_dict()

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "task": self.task.get("step_id", ""),
            "result": self.result,
            "duration": round((self.end_time or time.time()) - (self.start_time or time.time()), 2)
        }


class PerfectionGate:
    """完美门禁 — 拒绝残次品"""

    @staticmethod
    def verify(plan: dict, results: list[dict]) -> tuple[bool, list[str]]:
        """验证所有子任务是否完美完成"""
        issues = []
        total_steps = 0
        completed_steps = 0

        for phase in plan.get("phases", []):
            for step in phase.get("steps", []):
                total_steps += 1
                sid = step["step_id"]
                agent_result = next((r for r in results if r.get("task") == sid), None)

                if not agent_result:
                    issues.append(f"{sid}: 未执行")
                    continue

                if agent_result.get("status") != "completed":
                    issues.append(f"{sid}: 状态={agent_result.get('status')}")
                    continue

                if not agent_result.get("result", {}).get("ok"):
                    issues.append(f"{sid}: 执行失败 - {agent_result.get('result', {}).get('error', '?')}")
                    continue

                completed_steps += 1

        perfect = len(issues) == 0 and completed_steps == total_steps
        return perfect, issues


class AutonomousExecutor:
    """统一自主执行引擎

    循环:
      mind_map → spawn_agents → monitor → 
      stuck? → quad_brain_analyze → web_search → 
      refine_mind_map → spawn_agents → ...
      → perfection_gate → deliver
    """

    def __init__(self, max_agents: int = 50):
        self.max_agents = max_agents
        self.agents: list[SubAgent] = []
        self.plan: dict = {}
        self.iteration = 0
        self.history: list[dict] = []

    # ── 主循环 ────────────────────────────────

    def execute(self, task_description: str, task_type: str = "coding") -> dict:
        """主入口: 自主执行直到完美交付

        单层重试架构（非嵌套）:
          while True:                     ← 唯一的重试循环
            _spawn_and_execute(plan)      ← 单次遍历所有agent, 遇错即停(无内部重试)
            PerfectionGate.verify()       ← 检查结果
            if perfect: return            ← 成功退出
            _refine_mind_map()            ← 分析卡点 → 生成更精细计划 → 回到循环头
        """
        self.iteration = 0

        # ① 生成初始思维导图
        plan = self._generate_mind_map(task_description, task_type)
        self.plan = plan

        while True:
            self.iteration += 1
            entry = {
                "iteration": self.iteration,
                "timestamp": time.time(),
                "phase": "executing",
                "plan_summary": f"{len(plan.get('phases',[]))}阶段/{self._count_steps(plan)}步骤"
            }

            # ② 隔离子代理执行
            results = self._spawn_and_execute(plan)

            # ③ 完美门禁检查
            perfect, issues = PerfectionGate.verify(plan, results)



            if perfect:
                entry["phase"] = "perfect"
                entry["result"] = "全部通过"
                self.history.append(entry)
                audit_log("executor_done", {"iterations": self.iteration, "status": "perfect_delivery"}, phase="complete")
                self._sync_orchestrator(task_description, results, status="perfect")
                return {
                    "ok": True,
                    "status": "perfect_delivery",
                    "iterations": self.iteration,
                    "plan": plan,
                    "results": results,
                    "history": self.history
                }

            # ④ 卡点检测 → 四脑分析 → 全网搜索 → 更精细思维导图
            entry["phase"] = "stuck"
            entry["issues"] = issues
            self.history.append(entry)

            if self.iteration >= 10:
                audit_log("executor_maxed", {"iterations": self.iteration, "max_reached": True}, 
                          instruction=task_description, phase="max_iterations")
                return {
                    "ok": False,
                    "status": "max_iterations",
                    "iterations": self.iteration,
                    "remaining_issues": issues,
                    "plan": plan
                }

            # 生成更精细的思维导图
            plan = self._refine_mind_map(plan, issues, task_description)
            self.plan = plan

    # ── 思维导图生成 ──────────────────────────

    def _generate_mind_map(self, task: str, task_type: str) -> dict:
        """生成初始思维导图"""
        try:
            from brain.nexus import get_nexus
            nexus = get_nexus()
            nexus.scan()  # 邻域感知
        except Exception:
            pass

        # 使用task_mind生成
        try:
            sys.path.insert(0, str(ROOT))
            from caps.task_mind.run import decompose_task
            result = decompose_task(task, task_type)
            if result.get("ok"):
                return result
        except Exception:
            pass

        # 回退: 规则生成
        return self._rule_based_plan(task)

    def _refine_mind_map(self, old_plan: dict, issues: list, task: str) -> dict:
        """卡点后生成更精细的思维导图"""
        # 四脑分析卡点
        analysis = self._quad_brain_analyze(issues, task)

        # 生成更精细版本
        issue_steps = []
        for issue in issues:
            issue_steps.append({
                "step_id": f"FIX.{len(issue_steps)+1}",
                "action": f"修复: {issue}",
                "how": f"根据四脑分析建议: {analysis.get('direction','自主分析')[:100]}",
                "tool": analysis.get("recommended_tool", "auto"),
                "expected_output": "卡点解决，验证通过",
                "verify": f"原问题'{issue}'不再出现",
                "estimated_minutes": 5,
                "depends_on": [],
                "sub_steps": [
                    {"micro_id": f"FIX.{len(issue_steps)}.1", "micro_action": "分析根因",
                     "micro_how": analysis.get("root_cause", "自主分析"), "micro_time": 2},
                    {"micro_id": f"FIX.{len(issue_steps)}.2", "micro_action": "搜索方案",
                     "micro_how": f"web_search: {issue}", "micro_time": 3},
                    {"micro_id": f"FIX.{len(issue_steps)}.3", "micro_action": "实施修复",
                     "micro_how": "按最佳方案修改", "micro_time": 5},
                    {"micro_id": f"FIX.{len(issue_steps)}.4", "micro_action": "验证修复",
                     "micro_how": "运行测试+断言", "micro_time": 2},
                ]
            })

        new_plan = dict(old_plan)
        new_plan["phases"] = list(old_plan.get("phases", []))
        new_plan["phases"].append({
            "phase": f"卡点修复(第{self.iteration}轮)",
            "objective": f"解决{len(issues)}个卡点: {', '.join(issues[:3])}",
            "estimated_minutes": len(issues) * 12,
            "steps": issue_steps
        })
        new_plan["total_estimated_minutes"] = old_plan.get("total_estimated_minutes", 0) + len(issues) * 12
        new_plan["refined_at_iteration"] = self.iteration
        new_plan["quad_brain_analysis"] = analysis

        return new_plan

    # ── 四脑分析 ──────────────────────────────

    def _quad_brain_analyze(self, issues: list, task: str) -> dict:
        """四脑分析卡点"""
        try:
            from brain.deep_reasoner import get_reasoner
            reasoner = get_reasoner()
            return reasoner.reason(
                f"任务「{task[:100]}」遇到卡点: {'; '.join(issues[:5])}",
                mode="chain"
            )
        except Exception:
            pass

        # 回退分析
        return {
            "direction": f"自主分析{len(issues)}个卡点，逐一解决",
            "root_cause": "需要进一步调试",
            "recommended_tool": "web_search + auto_resolver",
            "risks": ["可能反复卡在同一问题"],
            "confidence": 0.6
        }

    # ── 子代理执行 ────────────────────────────
    def _spawn_and_execute(self, plan: dict) -> list[dict]:
        """批量生成隔离子代理并执行（单次遍历, 无内部重试）

        设计: 每个agent只执行一次, 遇错立即停止。
        重试由外层 execute() 的 while True 循环统一管理,
        每次迭代生成更精细的思维导图后再次调用本方法。
        """

        results = []
        agent_id = 0
        for phase in plan.get("phases", []):
            for step in phase.get("steps", []):
                if agent_id >= self.max_agents:
                    break
                agent_id += 1
                sandbox = SANDBOX_DIR / f"agent_{self.iteration}_{agent_id}"
                agent = SubAgent(f"A{agent_id:03d}", {
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "how": step["how"],
                    "verify": step["verify"],
                    "tool": step["tool"],
                    "code": step.get("code", ""),
                    "command": step.get("command", ""),
                    "timeout": step.get("estimated_minutes", 5) * 60
                }, sandbox)
                
                self.agents.append(agent)
                result = _with_circuit_breaker(step.get("tool", "auto_resolver"), agent.execute)

                if not result.get("result", {}).get("ok"):
                    # 卡点: 立即停止当前阶段，返回四脑
                    break
            else:
                continue
            break

        return results

    # ── 辅助 ──────────────────────────────────

    def _rule_based_plan(self, task: str) -> dict:
        return {
            "ok": True, "task": task,
            "type": "general",
            "total_estimated_minutes": 30,
            "phases": [{
                "phase": "执行",
                "objective": f"完成: {task[:80]}",
                "estimated_minutes": 30,
                "steps": [{
                    "step_id": "1.1",
                    "action": f"执行: {task[:50]}",
                    "how": "自主分析+全网搜索+逐步执行",
                    "tool": "auto",
                    "expected_output": "任务完成",
                    "verify": "验收标准满足",
                    "estimated_minutes": 30,
                    "depends_on": [],
                    "sub_steps": [
                        {"micro_id": "1.1.1", "micro_action": "分析需求", "micro_how": "理解任务目标", "micro_time": 5},
                        {"micro_id": "1.1.2", "micro_action": "设计方案", "micro_how": "多方案对比", "micro_time": 5},
                        {"micro_id": "1.1.3", "micro_action": "逐步执行", "micro_how": "每步验证", "micro_time": 15},
                        {"micro_id": "1.1.4", "micro_action": "最终验证", "micro_how": "三遍复查", "micro_time": 5},
                    ]
                }]
            }]
        }

    def _count_steps(self, plan: dict) -> int:
        return sum(len(p.get("steps", [])) for p in plan.get("phases", []))

    def status(self) -> dict:
        return {
            "iteration": self.iteration,
            "agents_spawned": len(self.agents),
            "plan_phases": len(self.plan.get("phases", [])),
            "history": self.history[-3:]
        }


    def _sync_orchestrator(self, task_description: str, results: list[dict], status: str = "running"):
        """同步编排器状态 — 双向: run_cycle + complete_task on perfect"""
        try:
            from brain.orchestrator import get_orchestrator
            orch = get_orchestrator()
            if status == "perfect":
                orch.complete_task(task_description, results)
            else:
                orch.run_cycle()
        except Exception:
            pass


# 全局
_executor: Optional[AutonomousExecutor] = None

def get_executor() -> AutonomousExecutor:
    global _executor
    if _executor is None:
        _executor = AutonomousExecutor()
    return _executor
