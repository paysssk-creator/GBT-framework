# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
gbt_tui.py — GBTxiaotudouV5 Claude Code 风格终端 v5.3
=======================================================
直连 Kimi API。用法: python gbt_tui.py
"""
import sys, os, json, urllib.request, urllib.error, shutil
from pathlib import Path
# ── 编码安全：Windows 控制台拒绝的 Unicode 用 ? 替换，防止闪退 ──
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
elif sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.resolve()

# ── 终端初始化 ──
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleTitleW("GBTxiaotudouV5")
    try:
        _h = ctypes.windll.kernel32.GetStdHandle(-11)
        _m = ctypes.c_ulong()
        ctypes.windll.kernel32.GetConsoleMode(_h, ctypes.byref(_m))
        ctypes.windll.kernel32.SetConsoleMode(_h, _m.value | 0x0004)
    except:
        pass

# ── .env ──
_env_file = ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip()

# ── 颜色 ──
C = {
    "x": "\033[0m", "B": "\033[1m", "dim": "\033[2m",
    "r": "\033[91m", "g": "\033[92m", "y": "\033[93m",
    "b": "\033[94m", "m": "\033[95m", "c": "\033[96m", "w": "\033[97m",
}

# ── LLM ──
API_KEY  = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY") or ""
API_BASE = os.environ.get("KIMI_BASE_URL", "https://api.moonshot.cn")
MODEL    = os.environ.get("KIMI_MODEL", "moonshot-v1-auto")

MODEL_NAMES = {
    "moonshot-v1-auto": "auto", "moonshot-v1-8k": "8k",
    "moonshot-v1-32k": "32k", "moonshot-v1-128k": "128k",
}
MODELS = {v: k for k, v in MODEL_NAMES.items()}

SYSTEM_PROMPT = (
    '你是 GBT小土豆，由"自由的风"创造的智能大脑。\n'
    '你是 GBTxiaotudouV5 项目自身的 AI 编程助手。\n'
    '项目根目录: C:/Users/ADMIN/GBTxiaotudouV5\n'
    '\n'
    '能力：编写/修改代码、执行命令、读写文件、技术分析\n'
    '\n'
    '回复要求：直接、简洁、专业，先说结论再展开；\n'
    '给出具体可执行的方案；不确定的细节要说明。\n'
    '中文回复，代码和术语保留英文。'
)

# ── 工具 ──
def width():
    return shutil.get_terminal_size().columns

def wstrip(s):
    import re
    return re.sub(r'\033\[[0-9;]*m', '', s)

def status_line(cost=0.0, model_short="auto"):
    """底部状态栏 — Claude Code 风格"""
    try:
        import subprocess
        r = subprocess.run(
            ["git", "-C", str(ROOT), "branch", "--show-current"],
            capture_output=True, text=True, timeout=2,
        )
        branch = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else ""
    except:
        branch = ""
    cwd = ROOT.name
    w = width()
    left = f" {cwd}"
    if branch:
        left += f" {C['dim']}({branch}){C['x']}"
    left += f"  {C['g']}¥{cost:.4f}{C['x']}"
    right = f"{MODEL}  /help  "
    pad = w - len(wstrip(left)) - len(wstrip(right))
    if pad < 1: pad = 1
    return f"{C['dim']}{left}{' ' * pad}{right}{C['x']}"

# ── 流式聊天 ──
def stream_chat(messages):
    if not API_KEY:
        yield f"\n{C['r']}❌ 未配置 KIMI_API_KEY。请在 .env 中设置{C['x']}\n"
        return
    data = json.dumps({
        "model": MODEL, "messages": messages,
        "stream": True, "temperature": 0.7,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/v1/chat/completions", data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            if resp.status != 200:
                body = resp.read().decode("utf-8", errors="replace")[:200]
                yield f"\n{C['r']}❌ API {resp.status}: {body}{C['x']}\n"
                return
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
                        c = obj["choices"][0].get("delta", {}).get("content", "")
                        if c: yield c
                    except Exception: continue
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        yield f"\n{C['r']}❌ HTTP {e.code}: {body}{C['x']}\n"
    except Exception as e:
        yield f"\n{C['r']}❌ 连接失败: {e}{C['x']}\n"

# ── 命令 ──
# ── 安全打印：捕获 Unicode 编码错误，防止闪退 ──
def safe_print(*args, **kwargs):
    """print 的安全封装，编码失败时用 ? 替换而非崩溃"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 逐段尝试，失败部分用 ? 替代
        end = kwargs.get("end", "\n")
        flush = kwargs.get("flush", False)
        for a in args:
            try:
                print(a, end="", flush=False)
            except UnicodeEncodeError:
                print(str(a).encode("utf-8", errors="replace").decode("utf-8", errors="replace"), end="", flush=False)
        print(end=end, flush=flush)

# ── 安全输入 ──
def safe_input(prompt=""):
    """input 的安全封装，编码错误时用 sys.stdin.buffer 降级读取"""
    try:
        return input(prompt)
    except UnicodeDecodeError:
        return sys.stdin.buffer.readline().decode("utf-8", errors="replace").rstrip("\r\n")

def handle_cmd(cmd, history):
    global MODEL
    parts = cmd.split()
    op = parts[0].lower()

    if op == "/clear":
        print(f"\n{C['dim']}⏺ 对话已清空{C['x']}")
        return True, [history[0]]

    if op == "/model":
        if len(parts) < 2:
            print(f"\n{C['dim']}用法: /model auto|8k|32k|128k{C['x']}")
            return True, history
        m = parts[1].lower()
        if m not in MODELS:
            print(f"\n{C['r']}未知: {m}。可用: {', '.join(MODELS)}{C['x']}")
            return True, history
        MODEL = MODELS[m]
        os.environ["KIMI_MODEL"] = MODEL
        print(f"\n{C['dim']}⏺ 已切换到 {MODEL}{C['x']}")
        return True, history

    if op == "/models":
        print(f"\n{C['dim']}可用模型:{C['x']}")
        for k, v in MODELS.items():
            mark = " ←" if v == MODEL else ""
            print(f"  {k} → {v}{mark}")
        return True, history

    if op == "/help":
        print(f"""
{C['B']}GBT小土豆 · 命令{C['x']}

  {C['g']}/clear{C['x']}        清空对话
  {C['g']}/model <id>{C['x']}   切换模型 (auto/8k/32k/128k)
  {C['g']}/models{C['x']}       列出模型
  {C['g']}/cost{C['x']}         查看费用
  {C['g']}/save <file>{C['x']}  保存对话
  {C['g']}/help{C['x']}         帮助
  {C['g']}quit/exit/q{C['x']}   退出
""")
        return True, history

    if op == "/save":
        fn = parts[1] if len(parts) > 1 else "gbt_chat.txt"
        p = ROOT / fn
        with open(p, "w", encoding="utf-8") as f:
            for m in history:
                if m["role"] == "system": continue
                tag = "You" if m["role"] == "user" else "GBT"
                f.write(f"{'─'*48}\n{tag}\n{'─'*48}\n{m['content']}\n\n")
        print(f"\n{C['dim']}⏺ 已保存 {p}{C['x']}")
        return True, history

    if op == "/cost":
        return "SHOW_COST", history

    return None, history


# ═══════════════ 主循环 ═══════════════
def main():
    cost = 0.0
    model_short = MODEL_NAMES.get(MODEL, "?")
    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    # ── 启动 ──
    safe_print(f"\n{C['B']}{C['c']}⏺ GBT小土豆{C['x']}  {C['dim']}智能大脑 v5.3{C['x']}")
    safe_print(f"{C['dim']}  {ROOT.name}  ·  {MODEL}  ·  /help 查看命令{C['x']}\n")

    if not API_KEY:
        safe_print(f"{C['r']}⚠ KIMI_API_KEY 未配置 — 请在 .env 中设置{C['x']}\n")

    while True:
        try:
            # 状态栏
            safe_print(status_line(cost, model_short))

            try:
                safe_print(f"{C['B']}> {C['x']}", end="", flush=True)
                user = safe_input()
            except (EOFError, KeyboardInterrupt):
                safe_print(f"\n{C['dim']}⏺ 会话结束 · ¥{cost:.4f}{C['x']}\n")
                break

            if not user.strip(): continue
            user = user.strip()

            if user.lower() in ("quit", "exit", "q"):
                safe_print(f"\n{C['dim']}⏺ 会话结束 · ¥{cost:.4f}{C['x']}\n")
                break

            if user.startswith("/"):
                result, history = handle_cmd(user, history)
                if result == "SHOW_COST":
                    safe_print(f"\n{C['dim']}累计费用: {C['g']}¥{cost:.4f}{C['x']}")
                elif result is True: pass
                elif result is False: break
                continue

            # 用户消息
            history.append({"role": "user", "content": user})
            model_short = MODEL_NAMES.get(MODEL, "?")

            # AI 响应
            safe_print(f"{C['c']}⏺{C['x']} ", end="", flush=True)
            full = ""
            try:
                for chunk in stream_chat(history):
                    safe_print(chunk, end="", flush=True)
                    full += chunk
            except KeyboardInterrupt:
                safe_print(f"\n{C['dim']}⏸ 已中断{C['x']}")
            except Exception as e:
                safe_print(f"\n{C['r']}⚠ 流异常: {e}{C['x']}")

            cost += len(full) / 1000000 * 1.0
            safe_print("\n")

            if full.strip():
                history.append({"role": "assistant", "content": full})
            else:
                history.pop()

        except KeyboardInterrupt:
            safe_print(f"\n{C['dim']}⏺ 会话结束 · ¥{cost:.4f}{C['x']}\n")
            break
        except Exception as e:
            safe_print(f"\n{C['r']}⚠ 内部错误 [{type(e).__name__}]: {e}{C['x']}")
            safe_print(f"{C['dim']}  会话未丢失，继续...{C['x']}\n")

if __name__ == "__main__":
    main()
