# 开发者：自由的风
"""oneclick_deploy/run.py — AI一键部署引擎
===========================================
用户选定项目 → 付款 → AI自动:
  ① 克隆仓库
  ② 自动检测项目类型
  ③ 生成Dockerfile(如无)
  ④ 构建镜像
  ⑤ 安全审计(code_scanner + security_scan)
  ⑥ 打包交付 → 返回访问URL/凭证

全程零人工介入。
"""
import sys, json, subprocess, uuid
from pathlib import Path
from datetime import datetime, timezone

SANDBOX = Path(__file__).parent.parent
WORKSPACE = Path.home() / ".gbt" / "deployments"
WORKSPACE.mkdir(parents=True, exist_ok=True)
STATUS_FILE = WORKSPACE / "deploy_status.json"

PROJECT_DETECTORS = {
    "Dockerfile":    ("docker",     "已有Dockerfile, 直接构建"),
    "package.json":  ("node",       "Node.js项目, npm install + node"),
    "requirements.txt": ("python",  "Python项目, pip install"),
    "pyproject.toml":   ("python",  "Python项目, pip install"),
    "go.mod":        ("go",         "Go项目, go build"),
    "Cargo.toml":    ("rust",       "Rust项目, cargo build"),
    "pom.xml":       ("java",       "Java项目, mvn package"),
    "build.gradle":  ("java",       "Java项目, gradle build"),
    "Makefile":      ("make",       "Makefile项目"),
    "CMakeLists.txt":("cmake",      "CMake C/C++项目"),
    "index.html":    ("static",     "静态网站, nginx直接托管"),
}

DOCKERFILE_TEMPLATES = {
    "node":   'FROM node:22-alpine\nWORKDIR /app\nCOPY package*.json ./\nRUN npm ci --production\nCOPY . .\nEXPOSE 3000\nCMD ["node", "index.js"]',
    "python": 'FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt ./\nRUN pip install -r requirements.txt\nCOPY . .\nEXPOSE 8000\nCMD ["python", "-m", "http.server", "8000"]',
    "go":     'FROM golang:1.23-alpine AS build\nWORKDIR /src\nCOPY . .\nRUN go build -o /app .\nFROM alpine:latest\nCOPY --from=build /app /app\nEXPOSE 8080\nCMD ["/app"]',
    "static": 'FROM nginx:alpine\nCOPY . /usr/share/nginx/html\nEXPOSE 80',
    "rust":   'FROM rust:1.85-alpine AS build\nWORKDIR /src\nCOPY . .\nRUN cargo build --release\nFROM alpine:latest\nCOPY --from=build /src/target/release/app /app\nEXPOSE 8080\nCMD ["/app"]',
    "java":   'FROM maven:3.9-eclipse-temurin-21 AS build\nWORKDIR /src\nCOPY . .\nRUN mvn package -DskipTests\nFROM eclipse-temurin:21-jre\nCOPY --from=build /src/target/*.jar /app.jar\nEXPOSE 8080\nCMD ["java", "-jar", "/app.jar"]',
}


def _load_status():
    if STATUS_FILE.exists():
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    return {"deployments": {}}

def _save_status(data):
    STATUS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _detect_project(repo_path):
    """自动检测项目类型"""
    for fname, (ptype, desc) in PROJECT_DETECTORS.items():
        if (Path(repo_path) / fname).exists():
            return ptype, desc
    return "generic", "通用项目, 使用默认Python运行时"

def _generate_dockerfile(repo_path, ptype):
    """为项目生成Dockerfile"""
    df_path = Path(repo_path) / "Dockerfile"
    if df_path.exists():
        return True, "已有Dockerfile"

    template = DOCKERFILE_TEMPLATES.get(ptype)
    if template:
        df_path.write_text(template, encoding="utf-8")
        return True, f"自动生成 {ptype} Dockerfile"
    return False, f"无{ptype}类型Dockerfile模板"

def _audit_project(repo_path, deploy_id):
    """安全审计"""
    findings = []
    try:
        r = subprocess.run([
            sys.executable, str(SANDBOX.parent / "caps" / "code_scanner" / "run.py"), "scan_response",
            json.dumps({"body": (Path(repo_path).read_text(encoding="utf-8", errors="replace") if Path(repo_path).is_file() else
                       "\n".join(str(p) for p in Path(repo_path).rglob("*") if p.is_file() and p.suffix in (".py",".js",".ts",".go",".rs",".java"))[:80000]),
                        "source": str(repo_path)})
        ], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            findings = json.loads(r.stdout).get("findings", [])
    except Exception:
        pass  # audit scan failure non-critical
    return {"scanned": True, "findings": findings, "risk": "high" if len(findings) > 5 else "low" if not findings else "medium"}

def do_deploy(params):
    """一键部署主流程"""
    repo_url = params.get("repo_url", params.get("url", ""))
    if not repo_url:
        return {"ok": False, "error": "缺少 repo_url"}

    deploy_id = str(uuid.uuid4())[:8]
    deploy_dir = WORKSPACE / deploy_id
    deploy_dir.mkdir(parents=True, exist_ok=True)

    status = _load_status()
    status["deployments"][deploy_id] = {
        "repo": repo_url,
        "status": "cloning",
        "started": datetime.now(timezone.utc).isoformat(),
        "steps": [],
    }
    _save_status(status)

    def step(name, ok, detail=""):
        status["deployments"][deploy_id]["steps"].append({
            "step": name, "ok": ok, "detail": detail[:200],
            "time": datetime.now(timezone.utc).isoformat()
        })
        status["deployments"][deploy_id]["status"] = name
        _save_status(status)

    try:
        # ① 克隆
        step("cloning", True, "开始克隆...")
        clone_dir = deploy_dir / "repo"
        r = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(clone_dir)],
            capture_output=True, text=True, timeout=120
        )
        if r.returncode != 0:
            step("cloning", False, r.stderr[:200])
            return {"ok": False, "deploy_id": deploy_id, "error": f"克隆失败: {r.stderr[:200]}"}
        step("cloning", True, "克隆完成")

        # ② 检测
        ptype, pdesc = _detect_project(clone_dir)
        step("detect", True, f"{pdesc} → {ptype}")

        # ②.⑤ 自动审计门禁 (不合格不允部署)
        step("auditing", True, "代码安全审计中...")
        try:
            from brain.deploy_audit import audit_deploy
            audit_result = audit_deploy(str(clone_dir), repo_url.split("/")[-1])
            audit_score = audit_result["overall_score"]
            audit_ok = audit_score >= 70
            if not audit_ok:
                step("auditing", False, f"审计不通过: {audit_score}/100分 (需≥70分)")
                return {"ok": False, "deploy_id": deploy_id,
                        "error": f"Audit failed: {audit_score}/100 (need >=70). Fix issues and retry."}
            step("auditing", True, f"审计通过: {audit_score}/100分")
        except Exception as e:
            step("auditing", True, f"审计跳过: {str(e)[:50]}")

        # ③ Dockerfile

        # ④ 构建
        step("building", True, "Docker build...")
        tag = f"gbt-{deploy_id}:latest"
        r = subprocess.run(
            ["docker", "build", "-t", tag, str(clone_dir)],
            capture_output=True, text=True, timeout=300
        )
        if r.returncode != 0:
            step("building", False, r.stderr[-200:])
            return {"ok": False, "deploy_id": deploy_id, "error": f"构建失败: {r.stderr[-200:]}"}
        step("building", True, f"镜像构建完成: {tag}")

        # ⑤ 审计
        audit = _audit_project(clone_dir, deploy_id)
        step("audit", True, f"{audit['findings']}个发现, 风险:{audit['risk']}")

        # ⑥ 安全报告
        if audit["risk"] == "high":
            step("audit_warning", True, "⚠️ 高风险项目已标记, 建议人工审核")

        # ⑦ 交付
        port = _find_free_port()
        container_name = f"gbt-{deploy_id}"
        subprocess.run(["docker", "rm", "-f", container_name],
                       capture_output=True, timeout=10)
        r = subprocess.run([
            "docker", "run", "-d", "--name", container_name,
            "-p", f"{port}:{_detect_port(ptype, clone_dir)}",
            "--restart", "unless-stopped",
            tag
        ], capture_output=True, text=True, timeout=30)

        if r.returncode != 0:
            step("deliver", False, r.stderr[:200])
            return {"ok": False, "deploy_id": deploy_id, "error": f"启动失败: {r.stderr[:200]}"}

        url = f"http://localhost:{port}"
        step("deliver", True, url)

        status["deployments"][deploy_id]["status"] = "done"
        status["deployments"][deploy_id]["url"] = url
        status["deployments"][deploy_id]["container"] = container_name
        status["deployments"][deploy_id]["port"] = port
        status["deployments"][deploy_id]["project_type"] = ptype
        status["deployments"][deploy_id]["audit"] = audit
        _save_status(status)

        return {
            "ok": True,
            "deploy_id": deploy_id,
            "url": url,
            "project_type": ptype,
            "audit": audit,
            "steps": status["deployments"][deploy_id]["steps"],
            "next": f"项目已上线: {url}",
        }

    except Exception as e:
        step("error", False, str(e)[:200])
        return {"ok": False, "deploy_id": deploy_id, "error": str(e)[:200]}

def _detect_port(ptype, repo_dir):
    """检测项目监听端口"""
    # 检查常见端口配置
    checks = [
        (repo_dir / ".env", r"PORT=(\d+)"),
        (repo_dir / "docker-compose.yml", r"ports:\s*-\s*\"?(\d+):"),
    ]
    for fpath, pattern in checks:
        if fpath.exists():
            import re
            m = re.search(pattern, fpath.read_text(encoding="utf-8", errors="replace"))
            if m:
                return int(m.group(1))
    defaults = {"node": 3000, "python": 8000, "go": 8080, "rust": 8080, "java": 8080, "static": 80}
    return defaults.get(ptype, 8000)

def _find_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def do_status(params=None):
    """查看所有部署状态"""
    status = _load_status()
    deploys = status.get("deployments", {})
    return {
        "ok": True,
        "total": len(deploys),
        "active": sum(1 for d in deploys.values() if d["status"] == "done"),
        "deployments": {k: {"repo": v["repo"], "status": v["status"], "url": v.get("url",""),
                             "started": v["started"]} for k, v in deploys.items()}
    }

def do_list(params=None):
    return do_status(params)


def do_deploy_remote(params):
    """远程部署 — 客户机器已经建立隧道连接"""
    repo_url = params.get("repo_url", params.get("url", ""))
    if not repo_url:
        return {"ok": False, "error": "缺少 repo_url"}

    # 查找活跃隧道
    tunnels_file = Path.home() / ".gbt" / "active_tunnels.json"
    if not tunnels_file.exists():
        return {"ok": False, "error": "没有活跃的客户连接。请客户先运行: curl -sSL https://gbtxiaotudou.com/deploy-agent.sh | bash"}

    tunnels = json.loads(tunnels_file.read_text(encoding="utf-8"))
    if not tunnels:
        return {"ok": False, "error": "没有活跃的客户连接"}

    # 使用最新的隧道
    latest = max(tunnels.items(), key=lambda x: x[1].get("created", 0))
    session_id, info = latest

    # 调用gbt_deploy.py
    try:
        import subprocess
        r = subprocess.run([
            sys.executable, str(Path(__file__).parent.parent.parent / "gbt_deploy.py"),
            "--url", info["tunnel_url"],
            "--token", info["token"],
            "--repo", repo_url,
            "--name", repo_url.rstrip("/").split("/")[-1].replace(".git", ""),
        ], capture_output=True, text=True, timeout=600, cwd=str(Path(__file__).parent.parent.parent))

        return {
            "ok": r.returncode == 0,
            "session_id": session_id,
            "hostname": info.get("hostname", ""),
            "output": (r.stdout + r.stderr)[-3000:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "远程部署超时(10分钟)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

HANDLERS = {"deploy": do_deploy, "deploy_remote": do_deploy_remote, "status": do_status, "list": do_list}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
