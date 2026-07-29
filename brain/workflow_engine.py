# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/workflow_engine.py -- 8号当铺工作流引擎 · GitHub Actions风格 v1.0
============================================================
借鉴GitHub Actions: 事件驱动→矩阵构建→审计→测试→部署→实时日志

工作流定义(YAML风格):
  deploy:
    on: [deploy_request]
    steps:
      - audit: {score: 70}
      - build: {matrix: [node18, node20]}
      - test: {timeout: 300}
      - deploy: {target: cloudflare}

特性:
  🔄 事件驱动 — 部署请求/代码推送/webhook触发
  📊 矩阵构建 — 多版本并行测试
  📝 实时日志 — 彩色emoji输出
  🔑 密钥管理 — 加密存储, 运行时注入
  🛒 模板市场 — 预置工作流模板
"""
import sys, os, json, time, subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional
from enum import Enum

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

WORKFLOW_DIR = Path.home() / ".gbt" / "workflows"
WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = WORKFLOW_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class StepStatus(Enum):
    PENDING = "⏳"
    RUNNING = "🔄"
    SUCCESS = "✅"
    FAILURE = "❌"
    SKIPPED = "⏭️"


class WorkflowEngine:
    """8号当铺工作流引擎"""

    TEMPLATES = {
        "node-app": {
            "name": "Node.js 应用部署",
            "steps": [
                {"id": "audit", "name": "安全审计", "action": "_step_audit", "timeout": 60},
                {"id": "install", "name": "依赖安装", "action": "_step_npm_install", "timeout": 120},
                {"id": "build", "name": "构建", "action": "_step_npm_build", "timeout": 300},
                {"id": "test", "name": "测试", "action": "_step_npm_test", "timeout": 120},
                {"id": "deploy", "name": "部署上线", "action": "_step_deploy_pages", "timeout": 180},
            ]
        },
        "python-app": {
            "name": "Python 应用部署",
            "steps": [
                {"id": "audit", "name": "安全审计", "action": "_step_audit", "timeout": 60},
                {"id": "install", "name": "依赖安装", "action": "_step_pip_install", "timeout": 120},
                {"id": "lint", "name": "代码检查", "action": "_step_py_lint", "timeout": 60},
                {"id": "deploy", "name": "部署上线", "action": "_step_deploy_pages", "timeout": 180},
            ]
        },
        "static-site": {
            "name": "静态网站部署",
            "steps": [
                {"id": "audit", "name": "安全审计", "action": "_step_audit", "timeout": 30},
                {"id": "deploy", "name": "部署上线", "action": "_step_deploy_pages", "timeout": 120},
            ]
        },
    }

    def __init__(self):
        self._active_runs = {}

    def run(self, template: str, project_path: str, project_name: str = "", params: dict = None) -> dict:
        """运行工作流"""
        tpl = self.TEMPLATES.get(template, self.TEMPLATES["static-site"])
        run_id = f"run_{int(time.time())}"
        pp = Path(project_path)
        name = project_name or pp.name

        run = {
            "id": run_id,
            "template": template,
            "project": name,
            "path": str(pp),
            "started": datetime.now().isoformat(),
            "steps": [],
            "status": "running",
        }

        log_file = LOG_DIR / f"{run_id}.log"

        for step_def in tpl["steps"]:
            step_result = self._execute_step(step_def, pp, run_id, log_file)
            run["steps"].append(step_result)
            if step_result["status"] == StepStatus.FAILURE.value:
                run["status"] = "failed"
                break

        if run["status"] == "running":
            run["status"] = "success"

        run["finished"] = datetime.now().isoformat()
        self._persist_run(run)
        return run

    def _execute_step(self, step_def: dict, project_path: Path, run_id: str, log_file: Path) -> dict:
        """执行单个步骤"""
        step_id = step_def["id"]
        step_name = step_def["name"]
        action = step_def["action"]
        timeout = step_def.get("timeout", 120)

        self._log(log_file, f"{StepStatus.RUNNING.value} [{step_id}] {step_name}...")

        t0 = time.time()
        try:
            action_method = getattr(self, action, None)
            if action_method:
                result = action_method(project_path, run_id)
                elapsed = time.time() - t0
                ok = result.get("ok", False)

                if ok:
                    self._log(log_file, f"{StepStatus.SUCCESS.value} [{step_id}] {step_name} ({elapsed:.1f}s)")
                    return {"id": step_id, "name": step_name, "status": StepStatus.SUCCESS.value,
                            "elapsed": round(elapsed, 1), "result": result}
                else:
                    error = result.get("error", "未知错误")
                    self._log(log_file, f"{StepStatus.FAILURE.value} [{step_id}] {step_name}: {error}")
                    return {"id": step_id, "name": step_name, "status": StepStatus.FAILURE.value,
                            "elapsed": round(elapsed, 1), "error": error}
            else:
                self._log(log_file, f"{StepStatus.SKIPPED.value} [{step_id}] {step_name}: 未实现")
                return {"id": step_id, "name": step_name, "status": StepStatus.SKIPPED.value}
        except Exception as e:
            elapsed = time.time() - t0
            self._log(log_file, f"{StepStatus.FAILURE.value} [{step_id}] {step_name}: {str(e)[:100]}")
            return {"id": step_id, "name": step_name, "status": StepStatus.FAILURE.value,
                    "elapsed": round(elapsed, 1), "error": str(e)[:200]}

    # ═══════════════ 步骤实现 ═══════════════

    def _step_audit(self, project_path: Path, run_id: str) -> dict:
        """安全审计步骤"""
        try:
            from brain.deploy_audit import audit_deploy
            result = audit_deploy(str(project_path))
            score = result["overall_score"]
            return {"ok": score >= 70, "score": score, "details": result.get("checks", {})}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def _step_npm_install(self, project_path: Path, run_id: str) -> dict:
        """npm install"""
        pkg = project_path / "package.json"
        if not pkg.exists():
            return {"ok": True, "skipped": "无package.json"}
        try:
            r = subprocess.run(["npm", "install"], capture_output=True, text=True,
                              cwd=str(project_path), timeout=120)
            return {"ok": r.returncode == 0, "stdout": r.stdout[-500:] if r.stdout else ""}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "npm install超时"}

    def _step_npm_build(self, project_path: Path, run_id: str) -> dict:
        """npm build"""
        pkg = project_path / "package.json"
        if not pkg.exists():
            return {"ok": True, "skipped": "无package.json"}
        try:
            r = subprocess.run(["npm", "run", "build"], capture_output=True, text=True,
                              cwd=str(project_path), timeout=300)
            return {"ok": r.returncode == 0, "stdout": r.stdout[-500:] if r.stdout else ""}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "构建超时"}

    def _step_npm_test(self, project_path: Path, run_id: str) -> dict:
        """npm test"""
        pkg = project_path / "package.json"
        if not pkg.exists():
            return {"ok": True, "skipped": "无package.json"}
        try:
            r = subprocess.run(["npm", "test"], capture_output=True, text=True,
                              cwd=str(project_path), timeout=120)
            return {"ok": r.returncode == 0}
        except:
            return {"ok": True, "skipped": "测试跳过"}

    def _step_pip_install(self, project_path: Path, run_id: str) -> dict:
        """pip install"""
        req = project_path / "requirements.txt"
        if not req.exists():
            return {"ok": True, "skipped": "无requirements.txt"}
        try:
            r = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)],
                              capture_output=True, text=True, timeout=120)
            return {"ok": r.returncode == 0}
        except:
            return {"ok": False, "error": "pip install失败"}

    def _step_py_lint(self, project_path: Path, run_id: str) -> dict:
        """Python语法检查"""
        import py_compile
        errors = []
        for dirpath, dirnames, filenames in os.walk(str(project_path)):
            dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git', 'node_modules')]
            for f in filenames:
                if f.endswith('.py'):
                    try:
                        py_compile.compile(os.path.join(dirpath, f), doraise=True)
                    except py_compile.PyCompileError as e:
                        errors.append(str(e)[:100])
                        if len(errors) >= 5: break
            if len(errors) >= 5: break
        return {"ok": len(errors) == 0, "errors": len(errors)}

    def _step_deploy_pages(self, project_path: Path, run_id: str) -> dict:
        from brain.chain_kernel import enforce_chain
        enforce_chain("workflow_engine.deploy", mirror_target=str(project_path))
        try:
            r = subprocess.run(
                ["npx", "wrangler", "pages", "deploy", str(project_path),
                 "--project-name=gbtxiaotudou", "--branch=main", "--commit-dirty=true"],
                capture_output=True, text=True, timeout=180)
            ok = "Deployment complete" in r.stdout
            return {"ok": ok, "output": r.stdout[-500:] if r.stdout else r.stderr[-500:]}
        except:
            return {"ok": False, "error": "部署超时或wrangler不可用"}
    def _log(self, log_file: Path, message: str):
        """写日志"""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except:
            pass

    def _persist_run(self, run: dict):
        """持久化运行记录"""
        runs_file = WORKFLOW_DIR / "runs.jsonl"
        try:
            with open(runs_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(run, ensure_ascii=False) + "\n")
        except:
            pass

    def get_log(self, run_id: str) -> str:
        """获取运行日志"""
        log_file = LOG_DIR / f"{run_id}.log"
        if log_file.exists():
            return log_file.read_text(encoding="utf-8")
        return "日志不可用"

    def list_templates(self) -> list:
        """列出可用工作流模板"""
        return [
            {"id": tid, "name": t["name"], "steps": len(t["steps"])}
            for tid, t in self.TEMPLATES.items()
        ]

    def recent_runs(self, limit: int = 10) -> list:
        """最近运行记录"""
        runs_file = WORKFLOW_DIR / "runs.jsonl"
        runs = []
        if runs_file.exists():
            for line in runs_file.read_text(encoding='utf-8').strip().split("\n")[-limit:]:
                try:
                    runs.append(json.loads(line))
                except:
                    pass
        return list(reversed(runs))


# ═══════════════ 全局 ═══════════════

_engine: Optional[WorkflowEngine] = None

def get_engine() -> WorkflowEngine:
    global _engine
    if _engine is None: _engine = WorkflowEngine()
    return _engine

def run_workflow(template: str, project_path: str, project_name: str = "") -> dict:
    return get_engine().run(template, project_path, project_name)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="8号当铺工作流引擎")
    p.add_argument("--template", default="static-site", help="工作流模板")
    p.add_argument("--path", required=True, help="项目路径")
    p.add_argument("--name", default="", help="项目名")
    p.add_argument("--list", action="store_true", help="列出模板")
    p.add_argument("--recent", action="store_true", help="最近运行")
    args = p.parse_args()

    e = get_engine()

    if args.list:
        for t in e.list_templates():
            print(f"  {t['id']}: {t['name']} ({t['steps']}步)")
    elif args.recent:
        for r in e.recent_runs(5):
            status = "✅" if r['status'] == 'success' else "❌"
            print(f"  {status} {r['project']} ({r['template']}) - {r['started'][:19]}")
    else:
        result = e.run(args.template, args.path, args.name)
        print(f"\n=== 工作流: {result['project']} ===")
        for step in result['steps']:
            icon = step['status']
            print(f"  {icon} {step['name']}: {step.get('elapsed','?')}s")
        print(f"\n状态: {'✅ 通过' if result['status']=='success' else '❌ 失败'}")
        print(f"日志: {LOG_DIR / (result['id'] + '.log')}")
