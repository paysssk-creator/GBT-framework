# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""git_ops/run.py — Git原生操作"""
import sys, json, os, subprocess
from pathlib import Path

def _git(args, cwd=None, timeout=30):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd or os.getcwd(),
                          capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")
        return {"ok": r.returncode == 0, "output": r.stdout.strip(),
                "stderr": r.stderr.strip()[:300], "exit_code": r.returncode}
    except FileNotFoundError:
        return {"ok": False, "error": "Git 未安装"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"超时"}

def do_status(params=None):
    r = _git(["status", "--porcelain"])
    if r["ok"]:
        lines = [l for l in r["output"].split("\n") if l.strip()]
        staged = len([l for l in lines if not l.startswith("??") and l[1] != " "])
        unstaged = len([l for l in lines if l[0] in " M" and l[1] != "?"])
        untracked = len([l for l in lines if l.startswith("??")])
        r["staged"] = staged; r["unstaged"] = unstaged; r["untracked"] = untracked
        r["clean"] = len(lines) == 0
    return r

def do_commit(params):
    msg = params.get("message", "")
    files = params.get("files", ".")
    if not msg: return {"ok": False, "error": "缺少 message 参数"}
    if isinstance(files, list): files = " ".join(files)
    _git(["add", files])
    return _git(["commit", "-m", msg])

def do_push(params):
    remote = params.get("remote", "origin")
    branch = params.get("branch", "")
    tags = params.get("tags", False)
    args = ["push", remote]
    if branch: args.append(branch)
    if tags: args.append("--tags")
    return _git(args, timeout=60)

def do_pull(params):
    remote = params.get("remote", "origin")
    branch = params.get("branch", "")
    args = ["pull", remote]
    if branch: args.append(branch)
    return _git(args, timeout=60)

def do_branch(params):
    action = params.get("action", "list")
    name = params.get("name", "")
    if action == "create" and name:
        return _git(["checkout", "-b", name])
    elif action == "switch" and name:
        return _git(["checkout", name])
    elif action == "delete" and name:
        return _git(["branch", "-d", name])
    else:
        r = _git(["branch", "-a"])
        if r["ok"]:
            lines = [l.strip().lstrip("*").strip() for l in r["output"].split("\n") if l.strip()]
            r["branches"] = lines
        return r

def do_tag(params):
    action = params.get("action", "list")
    name = params.get("name", "")
    msg = params.get("message", "")
    if action == "create" and name:
        args = ["tag", "-a", name]
        if msg: args.extend(["-m", msg])
        return _git(args)
    else:
        r = _git(["tag", "-l", "--sort=-creatordate"])
        if r["ok"]:
            r["tags"] = [t for t in r["output"].split("\n") if t.strip()][:20]
        return r

def do_log(params):
    n = params.get("n", params.get("count", 10))
    oneline = params.get("oneline", True)
    args = ["log", f"-{n}"]
    if oneline: args.append("--oneline")
    return _git(args)

def do_diff(params):
    file_path = params.get("file", "")
    staged = params.get("staged", False)
    args = ["diff"]
    if staged: args.append("--staged")
    if file_path: args.append("--"); args.append(file_path)
    return _git(args, timeout=15)

def do_merge(params):
    branch = params.get("branch", "")
    if not branch: return {"ok": False, "error": "缺少 branch 参数"}
    return _git(["merge", branch])

def do_clone(params):
    url = params.get("url", "")
    dest = params.get("dest", "")
    if not url: return {"ok": False, "error": "缺少 url 参数"}
    args = ["clone", url]
    if dest: args.append(dest)
    return _git(args, timeout=300)

HANDLERS = {"status": do_status, "commit": do_commit, "push": do_push,
            "pull": do_pull, "branch": do_branch, "tag": do_tag,
            "log": do_log, "diff": do_diff, "merge": do_merge, "clone": do_clone}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, do_status)
    print(json.dumps(h(params), ensure_ascii=False, default=str))
