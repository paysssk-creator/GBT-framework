# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# computer_use/run.py — GBT AI电脑操控执行器
# 集成全网最成熟项目: Open Interpreter (GUI+Code) + Browser Use (Web)
# ============================================================
"""GBT Computer Use v1.0 — AI远程电脑操控

支持的Agent:
  1. Open Interpreter — 全能型: GUI操控 + 代码执行 + 文件管理 + Shell (56k⭐)
  2. Browser Use     — 浏览器专项: DOM+视觉双重定位, 速度最快 (60k⭐)
  3. UI-TARS         — 纯本地视觉模型, 无需云端API (18k⭐)

用法:
  # 浏览器任务
  python run.py --mode browser --task "在GitHub上搜索AI agent项目并star前3个"

  # 桌面任务
  python run.py --mode desktop --task "打开记事本, 输入hello world, 保存到桌面"

  # 代码任务
  python run.py --mode code --task "在当前目录创建一个Flask API服务"

  # 混合全能力(默认)
  python run.py --task "帮我部署GPTxiaotudouV5到新服务器"
"""

import subprocess, sys, os, json
from pathlib import Path

CAPS_DIR = Path(__file__).parent.parent
PROJECT_ROOT = CAPS_DIR.parent

# ===================== 配置 =====================
MODES = {
    "browser": {
        "description": "浏览器任务 — 使用Browser Use (最快最准)",
        "backend": "browser_use",
        "pip_pkg": "browser-use",
    },
    "desktop": {
        "description": "桌面任务 — GUI操控+文件+Shell",
        "backend": "open_interpreter_desktop",
        "pip_pkg": "open-interpreter",
    },
    "code": {
        "description": "代码任务 — 写代码/运行/调试",
        "backend": "open_interpreter_code",
        "pip_pkg": "open-interpreter",
    },
    "mixed": {
        "description": "混合任务 — 浏览器+桌面+代码全能力",
        "backend": "open_interpreter_full",
        "pip_pkg": "open-interpreter",
    },
    "deploy": {
        "description": "自动部署 — 完整的项目部署流程",
        "backend": "open_interpreter_full",
        "pip_pkg": "open-interpreter",
    },
}


def check_backend(mode: str) -> bool:
    """检查依赖是否安装"""
    info = MODES.get(mode)
    if not info:
        return False
    pkg = info["pip_pkg"]
    try:
        if pkg == "open-interpreter":
            import interpreter
        elif pkg == "browser-use":
            pass  # 懒加载
        return True
    except ImportError:
        return False


def install_backend(mode: str) -> bool:
    """安装缺失依赖"""
    info = MODES.get(mode)
    if not info:
        return False
    print(f"[GBT] 安装 {info['pip_pkg']} ...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", info["pip_pkg"]],
        capture_output=True, text=True, timeout=300,
    )
    return result.returncode == 0


def run_browser_task(task: str, api_key: str = None, model: str = "deepseek-chat") -> dict:
    """使用Browser Use执行浏览器任务 — 原生ChatDeepSeek后端"""
    try:
        from browser_use import Agent
        from browser_use.llm.deepseek.chat import ChatDeepSeek

        llm = ChatDeepSeek(
            model=model,
            api_key=api_key or os.environ.get("DEEPSEEK_API_KEY"),
        )
        agent = Agent(task=task, llm=llm)
        import asyncio
        result = asyncio.run(agent.run())
        return {"ok": True, "result": str(result), "mode": "browser"}
    except ImportError as e:
        return {"ok": False, "error": f"browser-use 未安装: {e}", "mode": "browser"}
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "browser"}


def run_desktop_task(task: str, api_key: str = None) -> dict:
    """使用Open Interpreter执行桌面/GUI任务"""
    try:
        from interpreter import interpreter

        interpreter.llm.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        interpreter.llm.model = "deepseek-chat"
        interpreter.llm.api_base = "https://api.deepseek.com/v1"
        interpreter.auto_run = True
        interpreter.offline = False
        interpreter.os = True

        result = interpreter.chat(task)
        return {"ok": True, "result": str(result), "mode": "desktop"}
    except ImportError:
        return {"ok": False, "error": "open-interpreter 未安装", "mode": "desktop"}
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "desktop"}


def run_code_task(task: str, api_key: str = None) -> dict:
    """使用Open Interpreter执行代码任务"""
    try:
        from interpreter import interpreter

        interpreter.llm.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        interpreter.llm.model = "deepseek-chat"
        interpreter.llm.api_base = "https://api.deepseek.com/v1"
        interpreter.auto_run = True
        interpreter.safe_mode = False
        interpreter.loop = True  # 多轮交互

        result = interpreter.chat(f"请完成以下编程任务:\n{task}")
        return {"ok": True, "result": str(result), "mode": "code"}
    except ImportError:
        return {"ok": False, "error": "open-interpreter 未安装", "mode": "code"}
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "code"}


def run_mixed_task(task: str, api_key: str = None) -> dict:
    """使用Open Interpreter执行混合全能力任务"""
    try:
        from interpreter import interpreter

        interpreter.llm.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        interpreter.llm.model = "deepseek-chat"
        interpreter.llm.api_base = "https://api.deepseek.com/v1"
        interpreter.auto_run = True
        interpreter.os = True
        interpreter.loop = True
        interpreter.computer.import_computer_api = True  # 启用完整电脑操控API

        system_msg = (
            "你是一个AI电脑操控助手。你可以:\n"
            "1. 控制鼠标键盘 (PyAutoGUI)\n"
            "2. 操作浏览器 (Browser Use)\n"
            "3. 执行命令行/Shell\n"
            "4. 读写文件\n"
            "5. 安装软件\n"
            "请自动选择最合适的工具完成任务。"
        )
        result = interpreter.custom_instructions = system_msg
        result = interpreter.chat(task)
        return {"ok": True, "result": str(result), "mode": "mixed"}
    except ImportError:
        return {"ok": False, "error": "open-interpreter 未安装", "mode": "mixed"}
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "mixed"}


# ===================== 主入口 =====================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="GBT AI电脑操控")
    parser.add_argument("--mode", choices=list(MODES.keys()), default="mixed",
                        help="操控模式")
    parser.add_argument("--task", required=True, help="任务描述")
    parser.add_argument("--api-key", help="LLM API Key (默认用DEEPSEEK_API_KEY环境变量)")
    parser.add_argument("--install", action="store_true", help="自动安装缺失依赖")

    args = parser.parse_args()

    mode = args.mode
    print(f"[GBT Computer Use] 模式: {mode} | 任务: {args.task[:80]}...")

    # 检查并安装依赖
    if not check_backend(mode):
        if args.install:
            print(f"[GBT] 需要安装 {MODES[mode]['pip_pkg']}，正在安装...")
            if not install_backend(mode):
                print(f"[GBT] 安装失败，请手动执行: pip install {MODES[mode]['pip_pkg']}")
                sys.exit(1)
        else:
            print(f"[GBT] 缺少依赖 {MODES[mode]['pip_pkg']}，加 --install 自动安装")
            sys.exit(1)

    # 执行
    runners = {
        "browser": run_browser_task,
        "desktop": run_desktop_task,
        "code": run_code_task,
        "mixed": run_mixed_task,
        "deploy": run_mixed_task,
    }

    runner = runners.get(mode, run_mixed_task)
    result = runner(args.task, args.api_key)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


handlers = {
    "run": lambda p: _run_wrapper(p),
}

def _run_wrapper(params: dict) -> dict:
    """handlers 兼容层 — 接受 JSON params 转为 CLI 调用"""
    import sys as _sys
    mode = params.get("mode", "auto")
    task = params.get("task", "test")
    _sys.argv = ["run.py", "--mode", mode, "--task", task]
    return main()


if __name__ == "__main__":
    main()
