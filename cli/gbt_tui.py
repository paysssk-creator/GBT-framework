# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
gbt_tui.py — GBTxiaotudouV5 对话终端版 v5.0
=============================================
直连 Kimi (Moonshot) LLM。用法: python gbt_tui.py
quit/exit/q 退出 | /clear 清空 | /model 切换 | /models 列表
"""
import sys, os, json, time, urllib.request, urllib.error, subprocess, shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

# ── 终端标题 ──
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleTitleW("GBTxiaotudouV5")
# ── .env ──
_env_file = ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip()

# ── 颜色 ──
C = {"r": "\033[91m", "g": "\033[92m", "y": "\033[93m", "b": "\033[94m",
     "m": "\033[95m", "c": "\033[96m", "w": "\033[97m", "d": "\033[90m",
     "x": "\033[0m", "B": "\033[1m", "dim": "\033[2m"}

# ── LLM 配置 ──
API_KEY = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY") or ""
API_BASE = os.environ.get("KIMI_BASE_URL", "https://api.moonshot.cn")
MODEL = os.environ.get("KIMI_MODEL", "moonshot-v1-auto")
MODEL_NAMES = {"moonshot-v1-auto": "auto", "moonshot-v1-8k": "8k",
               "moonshot-v1-32k": "32k", "moonshot-v1-128k": "128k"}
MODELS = {v: k for k, v in MODEL_NAMES.items()}

GB = 1024**3; MB = 1024**2

SYSTEM_PROMPT = """你是 GBT小土豆，由"自由的风"创造的智能大脑 v5.0。
四层认知闭环：消息管线→行动审查→自进化→任务执行。
回复风格：简洁、专业、直接、中文。先说结论再说依据。
铁律：不虚构、不假设、不敷衍、不留坑、先推理再执行。
你是 GBTxiaotudouV5 项目的 AI 助手，根目录 C:/Users/ADMIN/GBTxiaotudouV5。"""

# ═══════════════ 状态栏数据 ═══════════════
def get_git_info():
    try:
        r = subprocess.run(["git","-C",str(ROOT),"status","--porcelain"],
                          capture_output=True, text=True, timeout=3)
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        modified = sum(1 for l in lines if l[1] != ' ')  # 暂存
        untracked = sum(1 for l in lines if l.startswith("??"))
        branch = "?"
        br = subprocess.run(["git","-C",str(ROOT),"branch","--show-current"],
                           capture_output=True, text=True, timeout=2)
        if br.returncode == 0: branch = br.stdout.strip() or "HEAD"
        return branch, modified, untracked
    except: return "?", 0, 0

def get_mem():
    try:
        if sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength",ctypes.c_ulong),("dwMemoryLoad",ctypes.c_ulong),
                           ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
                           ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
                           ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
                           ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]
            m = MEMORYSTATUSEX(); m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            used = m.ullTotalPhys - m.ullAvailPhys
            return used / m.ullTotalPhys * 100, m.ullTotalPhys / GB
    except: pass
    return 50.0, 16.0

def get_term_width():
    return shutil.get_terminal_size().columns

def status_line():
    branch, mod, unt = get_git_info()
    mem_pct, mem_total = get_mem()
    cwd = ROOT.name
    model_short = MODEL_NAMES.get(MODEL, MODEL.split("-")[-1])
    w = get_term_width()

    left = (f"{C['dim']}╭──{C['x']} {C['B']}{C['c']}GBT小土豆{C['x']}  >  "
            f"{C['g']}⬢{C['x']} Kimi · {C['y']}◒{C['x']} {model_short} > "
            f"{C['b']}📁{C['x']} …{cwd} > "
            f"{C['m']}⑂{C['x']} {branch}")
    if mod or unt:
        left += f" {C['y']}*{mod}{C['x']}"
    if unt:
        left += f" {C['r']}?{unt}{C['x']}"
    left += f" > {C['dim']}◫{C['x']} {mem_pct:.0f}%/{mem_total:.0f}G > "
    left += f"{C['g']}$0.00{C['x']} ▶"

    right = f"{C['dim']}──╮{C['x']}"
    pad = w - len(strip_ansi(left)) - len(strip_ansi(right)) - 1
    return left + " " * max(pad, 1) + right

def bottom_line():
    w = get_term_width()
    return f"{C['dim']}╰─{'─' * (w - 4)}─╯{C['x']}"

def strip_ansi(s):
    import re
    return re.sub(r'\033\[[0-9;]*m', '', s)

# ═══════════════ LLM ═══════════════
def stream_chat(messages):
    if not API_KEY:
        yield f"\n{C['r']}❌ 未配置 KIMI_API_KEY。请在 .env 中设置{C['x']}\n"
        return
    data = json.dumps({"model": MODEL, "messages": messages, "stream": True,
                       "temperature": 0.7}).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/v1/chat/completions", data=data,
        headers={"Content-Type":"application/json","Authorization":f"Bearer {API_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            buf = b""
            for chunk in iter(lambda: resp.read(64), b""):
                if not chunk: break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line or line == b"data: [DONE]": continue
                    if line.startswith(b"data: "): line = line[6:]
                    try:
                        obj = json.loads(line)
                        c = obj["choices"][0].get("delta",{}).get("content","")
                        if c: yield c
                    except: continue
    except Exception as e:
        yield f"\n{C['r']}❌ {e}{C['x']}\n"

# ═══════════════ 命令处理 ═══════════════
def handle_cmd(cmd, history):
    global MODEL
    parts = cmd.split()
    op = parts[0].lower()

    if op == "/clear":
        return f"\n{C['g']}✅ 对话已清空{C['x']}\n", True, [history[0]]

    if op == "/models":
        lines = [f"\n{C['c']}可用模型:{C['x']}"]
        for k, v in MODELS.items():
            mk = " ← 当前" if v == MODEL else ""
            lines.append(f"  {C['y']}{k}{C['x']} → {v}{mk}")
        return "\n".join(lines) + "\n", True, history

    if op == "/model":
        if len(parts) < 2:
            return f"\n{C['y']}用法: /model auto|8k|32k|128k{C['x']}\n", True, history
        m = parts[1].lower()
        if m not in MODELS:
            return f"\n{C['r']}未知: {m}。可用: {', '.join(MODELS)}{C['x']}\n", True, history
        MODEL = MODELS[m]
        os.environ["KIMI_MODEL"] = MODEL
        return f"\n{C['g']}✅ 已切换 {MODEL}{C['x']}\n", True, history

    if op == "/help":
        h = f"""
{C['B']}📖 GBT小土豆 · 终端版 v5.0{C['x']}
━━━━━━━━━━━━━━━━━━━━━
{C['g']}/clear{C['x']}       清空对话
{C['g']}/model <id>{C['x']}  切换模型 (auto/8k/32k/128k)
{C['g']}/models{C['x']}      列出模型
{C['g']}/help{C['x']}       此帮助
{C['g']}/save <file>{C['x']} 保存对话
{C['g']}quit/exit/q{C['x']}  退出
"""
        return h, True, history

    if op == "/save":
        fn = parts[1] if len(parts) > 1 else "gbt_chat.txt"
        p = ROOT / fn
        with open(p, "w", encoding="utf-8") as f:
            for m in history:
                if m["role"] == "system": continue
                tag = "🧑 你" if m["role"] == "user" else "🥔 GBT"
                f.write(f"{'='*48}\n{tag}\n{'='*48}\n{m['content']}\n\n")
        return f"\n{C['g']}✅ 已保存 {p}{C['x']}\n", True, history

    return None, True, history

# ═══════════════ 主循环 ═══════════════
def main():
    cost = 0.0
    print(status_line())
    print(bottom_line())

    if not API_KEY:
        print(f"\n{C['r']}⚠️  未配置 KIMI_API_KEY{C['x']}")
        print(f"   请在 .env 中设置 KIMI_API_KEY=你的密钥\n")

    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    model_short = MODEL_NAMES.get(MODEL, "?")

    while True:
        try:
            # 刷新状态栏
            print(f"\033[2A\r{status_line()}\n{bottom_line()}")
            user = input(f"\r").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{C['dim']}👋 已关闭{C['x']}")
            break

        if not user: continue
        if user.lower() in ("quit", "exit", "q"):
            print(f"\n{C['dim']}👋 已关闭{C['x']}")
            break
        if user.startswith("/"):
            out, cont, history = handle_cmd(user, history)
            if out: print(out, end="")
            if not cont: break
            continue

        history.append({"role": "user", "content": user})
        model_short = MODEL_NAMES.get(MODEL, "?")

        # 刷新状态栏 + 模型标签
        print(f"\033[2A\r{status_line()}\n{bottom_line()}\n{C['dim']}[{model_short}]{C['x']} ", end="", flush=True)

        full = ""
        start_t = time.time()
        try:
            for chunk in stream_chat(history):
                print(chunk, end="", flush=True)
                full += chunk
        except KeyboardInterrupt:
            print(f"\n{C['y']}⏸ 已中断{C['x']}")

        cost += len(full) / 1000000 * 1.0  # Kimi ¥1/M tokens


        print()
        if full.strip():
            history.append({"role": "assistant", "content": full})
        else:
            history.pop()

    # 退出时恢复光标
    print()

if __name__ == "__main__":
    main()
