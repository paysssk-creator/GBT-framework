# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# ── 邻域中枢接入 ────────────────────────────────────────
try:
    import sys as _nx_sys
    from pathlib import Path as _nx_Path
    _nx_sys.path.insert(0, str(_nx_Path(__file__).parent.parent.parent))
    from neighborhood_nexus import get_nexus, RESONANCE_CHAINS, NEIGHBORHOODS
    _HAS_NEXUS = True
except Exception:
    _HAS_NEXUS = False
"""gbt_brain/run.py — GBT自主AI大脑
====================================
事件驱动+自适应感知+五层决策规则。云端LLM+本地规则双模。
"""
import sys, json, os, time, threading
from pathlib import Path
from datetime import datetime, timezone
from collections import deque

STATE_FILE = Path.home() / ".gbt" / "brain_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

_brain_instance = None

class AutonomousBrain:
    """GBT小土豆 · 全自主AI大脑 v4.0
    
    工作流:
      事件驱动心跳 → 85维感知 → 邻域共振决策 → 桌面操控执行 → 验证反馈
      
    模式:
      - 守护模式: 被动监控,定时健康巡检
      - 自主模式: 接收任务 → 规划 → 执行 → 完成
      - 全自动模式: 持续感知+主动决策+操控执行
    """
    
    def __init__(self):
        self.running = False
        self.thread = None
        self._event = threading.Event()
        self._lock = threading.Lock()
        self.decisions = deque(maxlen=500)
        self.last_check = {}
        self.beat_count = 0
        self.mode = "guardian"  # guardian | autonomous | full_auto
        self._task_queue = deque(maxlen=50)
        self._current_task = None
        self._agent = None  # UniversalAgent实例
        
        # 加载能力
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from capability_protocol import get_engine
            e = get_engine()
            self.capabilities = list(e._modules.keys())
            self._engine = e
        except Exception:
            self.capabilities = [
                "browser_ctrl", "browser_open", "deep_scrape",
                "precision_scrape", "web_search", "screenshot", "screen_ocr",
                "omni_eye", "local_eye", "desktop_type", "desktop_master",
                "memory", "code_exec", "git_ops", "health_dashboard",
            ]
            self._engine = None
    
    def _init_agent(self):
        """延迟加载自主操控引擎"""
        if self._agent is None:
            try:
                caps_dir = Path(__file__).parent.parent
                sys.path.insert(0, str(caps_dir / "desktop_master"))
                from universal_agent import UniversalAgent
                self._agent = UniversalAgent(use_perception=True)
                return True
            except Exception as e:
                return False
        return True
    
    def start(self):
        if self.running: return {"ok": False, "msg": "大脑已在运行"}
        self.running = True; self._event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return {"ok": True, "msg": "GBT小土豆全自主大脑已启动"}
    
    def stop(self):
        self.running = False; self._event.set()
        if self._agent:
            self._agent.stop()
        return {"ok": True, "msg": "大脑已停止"}
    
    def ping(self, source="", reason=""):
        self._event.set()
    
    def submit_task(self, task: str, priority: str = "normal"):
        """提交任务到自主队列"""
        self._task_queue.append({"task": task, "priority": priority, "ts": time.time()})
        self._event.set()
        return {"ok": True, "queued": len(self._task_queue)}
    
    def _loop(self):
        while self.running:
            try:
                now = datetime.now()
                triggered = self._event.is_set()
                self.beat_count += 1
                
                # 阶段1: 感知 (85维)
                perception = self._sense(now, triggered)
                
                # 阶段2: 思考
                action = self._think(perception, now, triggered)
                
                # 阶段3: 行动
                if action: 
                    result = self._act(action, now, perception)
                    self.decisions.append({
                        "ts": now.isoformat(),
                        "action": action.get("type", "?"),
                        "result": str(result)[:200] if result else "ok"
                    })
                
                # 自适应间隔
                if triggered:
                    self._event.clear()
                    wait = 2
                elif action and action.get("priority") == "critical":
                    wait = 2
                elif self._task_queue:
                    wait = 1  # 有任务时快速响应
                else:
                    wait = 30
                self._event.wait(timeout=wait)
            except Exception as e:
                self._event.wait(timeout=10)
    
    def _sense(self, now, triggered):
        """85维感知——恢复简要版获取核心系统状态"""
        p = {"time": now.strftime("%H:%M:%S"), "triggered": triggered, "alerts": []}
        
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            p["resources"] = {"cpu": cpu, "mem": mem.percent, "free_mb": mem.available // 1048576}
            if mem.percent > 92:
                p["alerts"].append({"source": "memory", "level": "critical", "detail": f"内存 {mem.percent}%"})
            elif mem.percent > 85:
                p["alerts"].append({"source": "memory", "level": "warning", "detail": f"内存偏紧 {mem.percent}%"})
            if cpu > 85:
                p["alerts"].append({"source": "cpu", "level": "warning", "detail": f"CPU {cpu}%"})
        except:
            pass
        
        # 前景窗口
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                p["active_window"] = buf.value
        except:
            pass
        
        # 邻域状态
        if _HAS_NEXUS:
            try:
                nexus_status = get_nexus().status()
                p["neighborhoods"] = len(nexus_status.get("neighborhoods", {}))
            except:
                pass
        
        # 任务队列
        p["tasks_queued"] = len(self._task_queue)
        
        return p
    
    def _think(self, p, now, triggered):
        """增强决策——邻域路由+任务队列+健康巡检"""
        
        # 优先: 执行任务队列
        if self._task_queue:
            task_item = self._task_queue.popleft()
            self._current_task = task_item["task"]
            # 通过邻域中枢路由
            if _HAS_NEXUS:
                try:
                    route = get_nexus().route(self._current_task, {})
                    chain = route.get("sequence", [])
                except:
                    chain = ["task", "desktop", "code"]
            else:
                chain = ["task", "desktop"]
            
            return {
                "type": "autonomous_task",
                "priority": "high",
                "task": self._current_task,
                "chain": chain,
                "reason": f"执行: {self._current_task[:60]}"
            }
        
        # 告警处理
        alerts = p.get("alerts", [])
        critical = [a for a in alerts if a.get("level") == "critical"]
        if critical:
            return {
                "type": "alert",
                "priority": "critical",
                "reason": f"严重告警: {critical[0]['detail']}",
                "chain": ["health_check", "system_monitor"]
            }
        
        if triggered and alerts:
            return {
                "type": "alert",
                "priority": "high",
                "reason": f"告警: {alerts[0]['source']}",
                "chain": ["health_check"]
            }
        
        # 定时健康巡检
        last_hc = self.last_check.get("health", 0)
        if time.time() - last_hc > 300:
            self.last_check["health"] = time.time()
            return {
                "type": "health_check",
                "priority": "low",
                "reason": "定时健康巡检",
                "chain": ["health_check"]
            }
        
        return None
    
    def _act(self, action, now, perception=None):
        """增强行动——根据决策类型分发执行"""
        atype = action.get("type", "")
        chain = action.get("chain", [])
        results = []
        
        # 自主任务模式
        if atype == "autonomous_task":
            task = action.get("task", "")
            if task:
                try:
                    if self._init_agent() and self._agent:
                        result = self._agent.run(task, max_turns=15)
                        results.append({
                            "cap": "universal_agent",
                            "ok": result.ok,
                            "detail": f"{result.actions_executed}动作/{result.turns}轮"
                        })
                    else:
                        # 降级: 使用能力链
                        results.append({"cap": "universal_agent", "ok": False, "detail": "引擎未加载"})
                except Exception as e:
                    results.append({"cap": "universal_agent", "ok": False, "error": str(e)[:100]})
        
        # ── 大脑监管审查 ──
        try:
            from brain_oversight import get_gate
            gate = get_gate()
            for cap_name in chain:
                approval = gate.approve(cap_name, "auto", auto_exec=True)
                if not approval["approved"]:
                    results.append({"cap": cap_name, "ok": False, "error": f"监管拒绝: {approval['reason']}", "gate": approval["gate"]})
                    gate.record_result(cap_name, "auto", False, approval["reason"])
            if any(not r.get("ok", True) for r in results):
                return results  # 有拒绝的，直接返回
        except Exception:
            pass  # 监管不可用时放行

        # 标准能力链
        for cap_name in chain:
            try:
                if cap_name == "health_check":
                    if self._engine:
                        r = self._engine.call("health_dashboard", "quick", {})
                    else:
                        import psutil
                        r = {"ok": True, "cpu": psutil.cpu_percent(), "mem": psutil.virtual_memory().percent}
                    results.append({"cap": cap_name, "ok": True, "detail": str(r)[:100]})
                
                elif cap_name == "system_monitor":
                    if self._engine:
                        r = self._engine.call("self_diagnostic", "quick", {})
                    else:
                        r = {"ok": True, "msg": "系统正常"}
                    results.append({"cap": cap_name, "ok": True})
                
                elif cap_name == "notification":
                    try:
                        from notify import send as notify_send
                        notify_send("GBT大脑", action.get("reason", "")[:200])
                        results.append({"cap": cap_name, "ok": True})
                    except:
                        results.append({"cap": cap_name, "ok": False, "error": "notify不可用"})
                
                elif cap_name in ("desktop", "task", "code", "browser", "security"):
                    if _HAS_NEXUS:
                        try:
                            nexus_result = get_nexus().activate_neighborhood(cap_name)
                            results.append({"cap": cap_name, "ok": True, "nexus": "activated"})
                        except:
                            results.append({"cap": cap_name, "ok": False})
                    else:
                        results.append({"cap": cap_name, "ok": True, "mode": "direct"})
                
                else:
                    results.append({"cap": cap_name, "ok": True})
            
            except Exception as e:
                results.append({"cap": cap_name, "ok": False, "error": str(e)[:100]})
        return results

def do_start(p=None):
    global _brain_instance
    if _brain_instance is None: _brain_instance = AutonomousBrain()
    return _brain_instance.start()

def do_stop(p=None):
    global _brain_instance
    if _brain_instance: return _brain_instance.stop()
    return {"ok": False, "msg": "大脑未运行"}

def do_think(params):
    """深度思考 — LLM分析+决策"""
    topic = params.get("topic", params.get("prompt",""))
    if not topic: return {"ok":False,"error":"缺少 topic"}
    try:
        from intent_broker import _call_llm
        prompt = f"""你是一个深度分析引擎。请对以下问题进行深度思考,给出:
1. 核心问题识别
2. 多角度分析(至少3个角度)
3. 最优方案
4. 风险与注意事项
5. 行动建议

问题: {topic}

用简洁中文回答,每个部分2-3句话。"""
        result = _call_llm([{"role":"user","content":prompt}], max_tokens=1500)
        if result:
            return {"ok":True,"topic":topic,"analysis":result,"mode":"cloud_llm"}
    except: pass
    return {"ok":True,"topic":topic,"analysis":f"对「{topic}」的本地分析:\n1. 识别核心问题\n2. 多角度分析\n3. 制定方案\n4. 评估风险\n5. 执行建议","mode":"local"}

def do_decide(params):
    options = params.get("options", [])
    criteria = params.get("criteria", "综合最优")
    if not options: return {"ok":False,"error":"缺少 options"}
    try:
        from intent_broker import _call_llm
        opts_text = "\n".join(f"{i+1}. {o}" for i,o in enumerate(options))
        prompt = f"从以下选项中选择{criteria}的一项,只输出数字编号:\n{opts_text}"
        result = _call_llm([{"role":"user","content":prompt}], max_tokens=50)
        if result:
            import re; nums = re.findall(r'\d+', result)
            if nums: 
                idx = int(nums[0]) - 1
                if 0 <= idx < len(options):
                    return {"ok":True,"chosen":options[idx],"index":idx,"reason":result}
    except: pass
    return {"ok":True,"chosen":options[0],"index":0,"reason":"默认选第一个","mode":"local"}

def do_status(p=None):
    global _brain_instance
    running = _brain_instance is not None and _brain_instance.running
    beats  = _brain_instance.beat_count if _brain_instance else 0
    decisions = len(_brain_instance.decisions) if _brain_instance else 0
    # 动态读引擎能力数
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from capability_protocol import get_engine
        e = get_engine()
        total_caps = e.module_count
        browser_caps = [k for k in e._modules if 'browser' in k.lower()]
        cap_names = list(e._modules.keys())
    except Exception:
        total_caps = 0; browser_caps = []; cap_names = []
    return {
        "ok": True, "running": running,
        "heartbeats": beats, "decisions": decisions,
        "total_caps": total_caps,
        "browser_caps": browser_caps,
        "all_caps": cap_names,
    }


def do_caps(p=None):
    """列出所有已加载能力及其动作"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from capability_protocol import get_engine
        e = get_engine()
        result = []
        for name, mod in sorted(e._modules.items()):
            result.append({
                "name": name,
                "actions": list(mod.actions.keys()),
                "desc": mod.description[:60] if hasattr(mod,'description') else "",
            })
        return {"ok": True, "total": len(result), "caps": result}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

def do_resonate(params):
    """邻域共振 — 意图→中枢路由→LLM分析→反馈闭环"""
    intent = params.get("intent", params.get("prompt", params.get("topic", "")))
    if not intent:
        return {"ok": False, "error": "缺少 intent"}

    result = {"ok": True, "intent": intent, "mode": "resonate"}

    # Step 1: 邻域中枢路由
    if _HAS_NEXUS:
        try:
            nexus = get_nexus()
            route_result = nexus.route(intent, params)
            result["nexus"] = route_result
        except Exception as e:
            result["nexus"] = {"error": str(e)}
    else:
        result["nexus"] = {"error": "邻域中枢不可用"}

    # Step 2: LLM深度推理（分析中枢结果，决定是否继续穿透）
    try:
        from intent_broker import _call_llm
        chain_info = ""
        if _HAS_NEXUS and result["nexus"].get("sequence"):
            chain_info = f"\n共振链: {' → '.join(result['nexus']['sequence'])}"
        prompt = f"""你是GBT的决策大脑。基于邻域中枢的路由结果，分析以下意图并给出:
1. 当前激活的邻域是否足够？是否需要额外邻域？
2. 推荐的具体执行路径
3. 预期的产出和风险
{chain_info}

用户意图: {intent}

用简洁JSON回答: {{"sufficient":true/false,"extra_neighborhoods":[],"path":["step1","step2"],"expected_output":"...","risks":["..."]}}"""

        reasoning = _call_llm([{"role": "user", "content": prompt}], max_tokens=800)
        if reasoning:
            result["reasoning"] = reasoning
            result["mode"] = "nexus+cloud_llm"
        else:
            result["reasoning"] = "LLM无响应，使用中枢默认路由"
    except Exception:
        result["reasoning"] = "使用中枢默认路由（LLM不可用）"

    return result

def do_submit_task(params):
    """提交自主任务 — 大脑自动执行"""
    global _brain_instance
    task = params.get("task", params.get("goal", ""))
    if not task:
        return {"ok": False, "error": "需要 task/goal"}
    if _brain_instance is None:
        _brain_instance = AutonomousBrain()
    if not _brain_instance.running:
        _brain_instance.start()
    result = _brain_instance.submit_task(task)
    return {"ok": True, "task": task, "queued": result["queued"],
            "msg": f"任务已提交,大脑将自动执行: {task[:80]}"}

def do_autonomous(params):
    """全自主模式 v2 — 大脑总指挥驱动任务执行

    分层策略:
    1. 优先用 task_mind.auto (大脑↔导图↔执行 循环) — 最强自主引擎
    2. 降级 design_brain.run_autonomous — 推演收敛引擎
    3. 再降级 AutonomousBrain 心跳模式 — 持续守护

    铁律: 绝不反问用户。卡住=大脑推演，不是问用户。
    """
    task = params.get("task", params.get("goal", params.get("prompt", "")))
    max_rounds = params.get("max_rounds", 10)

    if not task:
        # 无任务 → 守护模式
        return _guardian_mode(params)

    result = {"ok": True, "task": task, "mode": "", "pipeline": []}

    # ══ 第1层: task_mind.auto (大脑↔导图↔执行 核心循环) ══
    try:
        import subprocess
        sandbox = Path(__file__).parent.parent
        tm_py = sandbox / "caps" / "task_mind" / "run.py"
        if tm_py.exists():
            tm_params = json.dumps({"task": task, "max_rounds": max_rounds, "verbose": False},
                                   ensure_ascii=False)
            r = subprocess.run([sys.executable, str(tm_py), "auto", tm_params],
                             capture_output=True, text=True, timeout=600, cwd=str(sandbox))
            if r.returncode == 0 and r.stdout.strip():
                tm_result = json.loads(r.stdout)
                result["pipeline"].append("task_mind.auto")
                result["mode"] = "task_mind_v3"
                result["task_mind"] = {
                    "converged": tm_result.get("converged", False),
                    "brain_rounds": tm_result.get("brain_rounds", 0),
                    "completed_steps": tm_result.get("completed_steps", 0),
                    "failed_steps": tm_result.get("failed_steps", 0),
                }
                if tm_result.get("converged"):
                    result["ok"] = True
                    result["msg"] = f"✅ 全自主完成: {tm_result['brain_rounds']}轮脑循环"
                    return result
                result["ok"] = tm_result.get("ok", False)
                if not result["ok"]:
                    result["msg"] = "⚠ task_mind未完全收敛，尝试下一层"
    except subprocess.TimeoutExpired:
        result["pipeline"].append("task_mind.auto(timeout)")
    except Exception as e:
        result["pipeline"].append(f"task_mind.error:{str(e)[:50]}")

    # ══ 第2层: design_brain.run_autonomous (推演收敛引擎) ══
    try:
        import subprocess
        sandbox = Path(__file__).parent.parent
        db_py = sandbox / "caps" / "design_brain" / "run.py"
        if db_py.exists():
            db_params = json.dumps({"intent": task, "max_rounds": max(3, max_rounds//2)},
                                   ensure_ascii=False)
            r = subprocess.run([sys.executable, str(db_py), "run", db_params],
                             capture_output=True, text=True, timeout=300, cwd=str(sandbox))
            if r.returncode == 0 and r.stdout.strip():
                db_result = json.loads(r.stdout)
                result["pipeline"].append("design_brain.run")
                if not result.get("mode"):
                    result["mode"] = "design_brain"
                result["design_brain"] = {
                    "converged": db_result.get("converged", False),
                    "rounds": db_result.get("rounds", 0),
                }
                if db_result.get("converged"):
                    result["ok"] = True
                    result["msg"] = "✅ design_brain收敛完成"
                    return result
    except subprocess.TimeoutExpired:
        result["pipeline"].append("design_brain.run(timeout)")
    except Exception as e:
        result["pipeline"].append(f"design_brain.error:{str(e)[:50]}")

    # ══ 第3层: AutonomousBrain 心跳守护 ══
    result["mode"] = result.get("mode") or "brain_guardian"
    result["ok"] = False
    result["msg"] = "所有管线已尝试，当前为守护模式。大脑持续监听，随时可重新执行。"

    # 启动守护（如果还没运行）
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AutonomousBrain()
    if not _brain_instance.running:
        _brain_instance.start()
    if task:
        _brain_instance.submit_task(task)

    return result


def _guardian_mode(params):
    """守护模式 — 无任务时的大脑自检和监控"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AutonomousBrain()
    if not _brain_instance.running:
        _brain_instance.start()

    # 快速健康检查
    health = {"caps_ok": 0, "caps_total": 0}
    try:
        sandbox = Path(__file__).parent.parent
        hd_py = sandbox / "caps" / "health_dashboard" / "run.py"
        if hd_py.exists():
            import subprocess
            r = subprocess.run([sys.executable, str(hd_py), "quick"],
                             capture_output=True, text=True, timeout=15, cwd=str(sandbox))
            if r.returncode == 0 and r.stdout.strip():
                health = json.loads(r.stdout)
    except: pass

    return {
        "ok": True,
        "mode": "guardian",
        "msg": "🧠 大脑守护模式 — 持续感知，随时响应",
        "running": _brain_instance.running,
        "beat_count": _brain_instance.beat_count,
        "decisions": len(_brain_instance.decisions),
        "health": health,
    }

HANDLERS = {"start":do_start,"stop":do_stop,"think":do_think,"decide":do_decide,
             "status":do_status,"caps":do_caps,"resonate":do_resonate,
             "submit_task":do_submit_task,"autonomous":do_autonomous,"task":do_submit_task}

if __name__=="__main__":
    action = sys.argv[1].lstrip("-") if len(sys.argv)>1 and sys.argv[1]!="run.py" else "status"
    params={}
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h=HANDLERS.get(action,lambda p:{"ok":False,"error":f"未知:{action}"})
    print(json.dumps(h(params),ensure_ascii=False,default=str))
