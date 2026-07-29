# 开发者：自由的风
"""gbt_deploy.py — GBT远程部署编排器 v3.0
========================================
接收隧道URL → 自动连接 → 部署指定项目到客户机器

用法: python gbt_deploy.py --url <tunnel_url> --token <token> [--repo <github_url>]
"""
import json, time, urllib.request, urllib.error
from pathlib import Path

CAPS_DIR = Path(__file__).parent.parent / "caps"


def call_remote(url: str, token: str, method="GET", json_data=None, timeout=300):
    """调用客户机器的API"""
    headers = {"X-GBT-Token": token, "Content-Type": "application/json"}
    try:
        data = json.dumps(json_data).encode() if json_data else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def deploy_project(tunnel_url: str, token: str, repo_url: str, project_name: str = ""):
    """远程部署指定项目到客户机器"""
    BASE = tunnel_url.rstrip("/")

    def cmd(command, timeout=300, cwd=None):
        return call_remote(BASE, token, "POST",
            {"cmd": command, "timeout": timeout, "cwd": cwd}, timeout)

    def step(name):
        print(f"  [{name}]", end=" ", flush=True)

    print(f"\n🥔 开始远程部署: {repo_url}")
    print(f"   目标机器: {call_remote(BASE, token).get('hostname', '?')}")
    print()

    # ① 环境检查
    step("环境检测")
    r = cmd("docker --version 2>&1 && git --version 2>&1 && echo ENV_OK")
    if "ENV_OK" not in r.get("stdout", ""):
        print("⚠️ Docker或Git未安装, 尝试winget安装...")
        cmd("winget install Docker.DockerDesktop --accept-package-agreements 2>nul || echo SKIP", 180)
        cmd("winget install Git.Git --accept-package-agreements 2>nul || echo SKIP", 120)
    print("OK")

    # ② 创建工作目录
    deploy_name = project_name or repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    work_dir = f"%USERPROFILE%\\GBT-deployments\\{deploy_name}"
    step("创建工作区")
    cmd(f'mkdir "{work_dir}" 2>nul', 10)
    cmd('echo DIR_OK', 5)
    print("OK")

    # ③ 克隆仓库
    step("克隆项目")
    r = cmd(f'cd /d "{work_dir}" && git clone --depth 1 {repo_url} repo 2>&1', 180)
    ok = r.get("ok", False)
    print("OK" if ok else f"失败: {r.get('stderr','')[:100]}")

    # ④ Docker化
    step("构建镜像")
    repo_dir = f"{work_dir}\\repo"
    # 检测Dockerfile
    r = cmd(f'cd /d "{repo_dir}" && (if exist Dockerfile (echo HAS_DOCKERFILE) else (echo NO_DOCKERFILE))', 10)
    if "NO_DOCKERFILE" in r.get("stdout", ""):
        # 生成Dockerfile
        df_lines = [
            'FROM python:3.12-slim',
            'WORKDIR /app',
            'COPY requirements*.txt ./',
            'RUN pip install -r requirements.txt 2>nul || echo SKIP_PIP',
            'COPY . .',
            'EXPOSE 8000',
            'CMD ["python", "-m", "http.server", "8000"]',
        ]
        df_content = '\n'.join(df_lines)
        cmd(f'cd /d "{repo_dir}" && echo {df_content} > Dockerfile', 10)
        print("(自动生成)", end=" ")

    img_tag = f"gbt-{deploy_name}:latest"
    r = cmd(f'cd /d "{repo_dir}" && docker build -t {img_tag} . 2>&1', 300)
    print("OK" if r.get("ok") else f"失败: {r.get('stderr','')[:100]}")

    # ⑤ 启动
    step("启动容器")
    port = _find_free_port(tunnel_url, token)
    container = f"gbt-{deploy_name}"
    cmd(f"docker rm -f {container} 2>nul || echo CLEAN", 10)
    r = cmd(f'docker run -d --name {container} -p {port}:8000 --restart unless-stopped {img_tag} 2>&1', 60)
    print("OK" if r.get("ok") else f"失败: {r.get('stderr','')[:100]}")

    # ⑥ 验证
    step("验证")
    time.sleep(3)
    r = cmd(f"docker ps --filter name={container} --format '{{{{.Status}}}}'", 10)
    status = r.get("stdout", "").strip()
    print(f"{'✅ 运行中' if 'Up' in status else '⚠️ ' + status}")
    # ⑦ HTTP健康检查
    health_ok = False
    if "Up" in status:
        for attempt in range(3):
            hr = call_remote(BASE, token, "POST",
                {"cmd": f"curl -s -o NUL -w \"%{{http_code}}\" http://localhost:{port} 2>nul || echo 000"}, 10)
            http_code = hr.get("stdout", "000").strip()
            if http_code in ("200", "301", "302", "403"):
                health_ok = True
                print(f"  🌐 HTTP {http_code} 响应正常")
                break
            time.sleep(2)
        if not health_ok:
            r_alt = call_remote(BASE, token, "POST",
                {"cmd": f"docker logs --tail 20 {container} 2>&1"}, 10)
            print(f"  ⚠️ HTTP无响应, 容器日志: {r_alt.get('stdout','')[:200]}")

    return {
        "ok": "Up" in status,
        "project": deploy_name,
        "container": container,
        "port": port,
        "access": f"http://localhost:{port}",
    }


def _find_free_port(tunnel_url, token):
    """在客户机器上找空闲端口"""
    # 简单方案: 用固定范围
    r = call_remote(tunnel_url, token, "POST",
        {"cmd": "python -c \"import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()\""}, 10)
    try:
        return int(r.get("stdout", "9000").strip().split("\n")[-1])
    except Exception:
        return 9000


# ═══════════════ 主入口 ═══════════════
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--token", required=True)
    p.add_argument("--repo", default="")
    p.add_argument("--name", default="")
    args = p.parse_args()

    if args.repo:
        result = deploy_project(args.url, args.token, args.repo, args.name)
        print(f"\n{'✅ 部署成功!' if result['ok'] else '❌ 部署失败'}")
        print(f"   访问地址: {result.get('access', 'N/A')}")
    else:
        # 兼容旧模式: 部署GBT自己
        print("用法: python gbt_deploy.py --url <tunnel> --token <tok> --repo <github_url>")
