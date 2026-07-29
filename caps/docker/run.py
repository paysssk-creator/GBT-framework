# 开发者：自由的风
"""docker/run.py — 容器管理(Docker)
===================================
运维域 ready — Docker镜像/容器/构建全生命周期管理
"""
import sys, json, os, subprocess

def _docker(args, timeout=30):
    try:
        r = subprocess.run(["docker"] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or r.stderr)[:1000]
    except FileNotFoundError:
        return False, "docker未安装或不在PATH中"
    except subprocess.TimeoutExpired:
        return False, f"超时({timeout}s)"
    except Exception as e:
        return False, str(e)[:100]

def do_ps(params):
    ok, out = _docker(["ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"])
    containers = []
    if ok:
        for line in out.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                containers.append({"id": parts[0][:12], "name": parts[1], "status": parts[2] if len(parts) > 2 else ""})
    return {"ok": True, "cap": "docker", "action": "ps", "domain": "运维域", "containers": containers, "count": len(containers)}

def do_run(params):
    image = params.get("image", "")
    name = params.get("name", "")
    ports = params.get("ports", "")
    args = ["run", "-d"]
    if name: args += ["--name", name]
    if ports: args += ["-p", ports]
    args.append(image)
    ok, out = _docker(args)
    return {"ok": ok, "cap": "docker", "action": "run", "image": image, "output": out[:200]}

def do_build(params):
    path = params.get("path", ".")
    tag = params.get("tag", "gbt-build:latest")
    ok, out = _docker(["build", "-t", tag, path], timeout=120)
    return {"ok": ok, "cap": "docker", "action": "build", "tag": tag, "output": out[:500]}

def do_stop(params):
    container = params.get("container", params.get("name", ""))
    ok, out = _docker(["stop", container])
    return {"ok": ok, "container": container, "stopped": ok}

def do_compose_up(params):
    file = params.get("file", "_deploy/docker-compose.yml")
    project_name = params.get("project", "gbt")
    # prefer "docker compose" (v2 plugin), fall back to "docker-compose" (v1 standalone)
    for cmd in (["docker", "compose"], ["docker-compose"]):
        try:
            subprocess.run(cmd, capture_output=True, timeout=5)
            break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            cmd = None
    if cmd is None:
        return {"ok": False, "cap": "docker", "action": "compose_up", "error": "docker compose 未安装"}
    args = cmd + ["-f", file, "-p", project_name, "up", "-d"]
    ok, out = _docker(args, timeout=120)
    return {"ok": ok, "cap": "docker", "action": "compose_up", "domain": "运维域",
            "file": file, "project": project_name, "output": out[:500]}

def do_health_check(params):
    names = params.get("containers", [])
    ok, out = _docker(["ps", "-a", "--format", "{{.Names}}\t{{.State}}\t{{.Status}}"])
    all_containers = {}
    if ok:
        for line in out.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                all_containers[parts[0]] = {"state": parts[1], "status": parts[2] if len(parts) > 2 else ""}
    if names:
        # filter to specified containers
        results = {n: all_containers.get(n, {"state": "not_found", "status": "container not found"}) for n in names}
    else:
        results = all_containers
    healthy = all(v.get("state") == "running" for v in results.values())
    return {"ok": True, "cap": "docker", "action": "health_check", "domain": "运维域",
            "containers": results, "healthy": healthy, "total": len(results)}

def do_auto_orchestrate(params):
    action = params.get("op", "status")
    names = params.get("containers", [])
    results = {}
    for name in names:
        if action == "start":
            ok, out = _docker(["start", name])
            results[name] = {"ok": ok, "action": "start", "output": out[:200]}
        elif action == "stop":
            ok, out = _docker(["stop", name])
            results[name] = {"ok": ok, "action": "stop", "output": out[:200]}
        elif action == "restart":
            ok, out = _docker(["restart", name])
            results[name] = {"ok": ok, "action": "restart", "output": out[:200]}
        elif action == "status":
            ok, out = _docker(["inspect", "--format", "{{.State.Status}}", name])
            results[name] = {"ok": ok, "state": out.strip()}
        else:
            results[name] = {"ok": False, "error": f"unknown op: {action}"}
    all_ok = all(v.get("ok", False) for v in results.values()) if results else True
    return {"ok": all_ok, "cap": "docker", "action": "auto_orchestrate", "domain": "运维域",
            "op": action, "results": results, "managed_count": len(names)}

HANDLERS = {"ps": do_ps, "run": do_run, "build": do_build, "stop": do_stop,
            "compose_up": do_compose_up, "health_check": do_health_check,
            "auto_orchestrate": do_auto_orchestrate}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "ps"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
