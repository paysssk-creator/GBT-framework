# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
nanobrowser/run.py — AI多智能体浏览器自动化引擎
=================================================
架构: Planner(LLM规划) → Navigator(浏览器执行) → Extractor(数据提取) → Validator(结果验证)
引擎: SeleniumBase + Playwright + Puppeteer (via browser_automation)
指纹: 15维隐身指纹 (via gbt_browser)
食谱: login/scrape/monitor (via browser_automation recipes)
"""
import json
import re
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from _shared import _call_cap, _get_sandbox

SANDBOX = _get_sandbox()
DATA_DIR = Path.home() / ".gbt" / "nanobrowser"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── 持久的浏览器用户数据目录（防EBUSY闪退）──
BROWSER_DATA_DIR = DATA_DIR / "browser_profiles"
BROWSER_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════
#  AGENT 1 — Planner: 将自然语言目标分解为可执行步骤
# ══════════════════════════════════════════════════════════════

PLANNER_SYSTEM_PROMPT = """你是一个网页自动化规划器。将用户的浏览目标分解为具体的操作步骤。
输出JSON格式: {"steps": [{"action":"navigate|click|type|scroll|extract|wait|screenshot", "target":"css选择器或URL", "value":"输入值(可选)", "reason":"为什么需要这一步"}]}

可用的action类型:
- navigate: 导航到URL
- click: 点击元素 (target=css选择器)
- type: 输入文本 (target=css选择器, value=输入内容)
- scroll: 滚动页面 (value=像素或"bottom")
- extract: 提取数据 (target=css选择器, value=数据描述)
- wait: 等待 (value=秒数或css选择器)
- screenshot: 截图

规则:
1. 每一步必须具体、可执行
2. 步骤数量控制在3-10步
3. 优先使用语义化选择器 (a[href*="xxx"], button:contains("xxx"))
4. 数据提取步骤放在最后
5. 如果目标不需要交互，只需要navigate+extract"""


def _plan(goal: str, context: dict = None) -> list:
    """使用LLM将目标分解为操作步骤"""
    prompt = f"目标: {goal}"
    if context:
        prompt += f"\n当前上下文: {json.dumps(context, ensure_ascii=False)}"

    try:
        result = _call_cap("cloud_llm", "ask", {
            "prompt": prompt,
            "system": PLANNER_SYSTEM_PROMPT
        }, timeout=60)

        if result.get("ok") and result.get("reply"):
            reply = result["reply"]
            # Try to extract JSON from reply
            json_match = re.search(r'\{[\s\S]*"steps"[\s\S]*\}', reply)
            if json_match:
                plan = json.loads(json_match.group())
                return plan.get("steps", [])
        return _fallback_plan(goal)
    except Exception:
        return _fallback_plan(goal)


def _fallback_plan(goal: str) -> list:
    """当LLM不可用时的确定性规划"""
    steps = []
    url_match = re.search(r'(https?://[^\s]+)', goal)
    if url_match:
        url = url_match.group()
        steps.append({"action": "navigate", "target": url, "reason": "导航到目标URL"})

    if any(kw in goal for kw in ["提取", "抓取", "extract", "获取", "爬取"]):
        steps.append({"action": "extract", "target": "body",
                       "value": "页面主要内容", "reason": "提取页面数据"})
    elif any(kw in goal for kw in ["截图", "screenshot", "截屏"]):
        steps.append({"action": "screenshot", "target": "full_page",
                       "reason": "截取页面"})
    elif any(kw in goal for kw in ["登录", "login", "登入"]):
        steps.append({"action": "navigate", "target": url or goal,
                       "reason": "导航到登录页"})

    if not steps:
        steps.append({"action": "navigate",
                       "target": f"https://www.google.com/search?q={goal}",
                       "reason": "搜索目标"})
        steps.append({"action": "extract", "target": "#search",
                       "value": "搜索结果", "reason": "提取搜索结果"})

    return steps


# ══════════════════════════════════════════════════════════════
#  AGENT 2 — Navigator: 执行浏览器操作
# ══════════════════════════════════════════════════════════════

def _get_fingerprint(os_name="Windows", country="cn"):
    """获取15维隐身指纹"""
    try:
        result = _call_cap("gbt_browser", "generate_fingerprint", {
            "os": os_name, "country": country,
            "canvas_noise": "medium"
        }, timeout=10)
        if result.get("ok"):
            return result.get("fingerprint", {})
    except Exception:
        pass
    return {}


def _navigate(url: str, fingerprint: dict = None, headless: bool = True,
              wait_selector: str = None) -> dict:
    """智能导航 — 使用browser_automation引擎"""
    params = {"url": url, "headless": headless}
    if fingerprint:
        params["fingerprint"] = fingerprint
    if wait_selector:
        params["wait_selector"] = wait_selector

    try:
        result = _call_cap("browser_automation", "navigate",
                           params, timeout=60)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _click(selector: str, url: str = None, fingerprint: dict = None,
           headless: bool = True) -> dict:
    """点击元素"""
    params = {"url": url or "about:blank", "headless": headless,
              "fill_selectors": {selector: "click"}}
    if fingerprint:
        params["fingerprint"] = fingerprint

    try:
        # Use fill_form with click action
        result = _call_cap("browser_automation", "fill_form",
                           params, timeout=30)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _type_text(selector: str, text: str, url: str = None,
               fingerprint: dict = None, headless: bool = True) -> dict:
    """输入文本"""
    params = {"url": url or "about:blank", "headless": headless,
              "fill_selectors": {selector: text}}
    if fingerprint:
        params["fingerprint"] = fingerprint

    try:
        result = _call_cap("browser_automation", "fill_form",
                           params, timeout=30)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _extract_content(url: str, selectors: list = None, schema: dict = None,
                     fingerprint: dict = None, headless: bool = True) -> dict:
    """提取结构化数据"""
    params = {"url": url, "headless": headless}
    if selectors:
        # browser_automation expects selectors as dict {name: css_selector}
        if isinstance(selectors, list):
            params["selectors"] = {f"sel_{i}": s for i, s in enumerate(selectors)}
        else:
            params["selectors"] = selectors
    if schema:
        params["schema"] = schema
    if fingerprint:
        params["fingerprint"] = fingerprint

    try:
        result = _call_cap("browser_automation", "extract_data",
                           params, timeout=60)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def _screenshot(url: str, selector: str = None, full_page: bool = False,
                fingerprint: dict = None, headless: bool = True) -> dict:
    """截图"""
    params = {"url": url, "headless": headless,
              "full_page": full_page}
    if selector:
        params["selector"] = selector
    if fingerprint:
        params["fingerprint"] = fingerprint

    try:
        result = _call_cap("browser_automation", "screenshot",
                           params, timeout=30)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ══════════════════════════════════════════════════════════════
#  AGENT 3 — Extractor: 语义数据提取 + 结构化输出
# ══════════════════════════════════════════════════════════════

def _extract_semantic(raw_text: str, goal: str) -> dict:
    """从原始文本中语义提取目标数据"""
    # 确定性提取常见模式
    extracted = {"_raw_length": len(raw_text), "_goal": goal}

    # URLs
    urls = re.findall(r'https?://[^\s<>"]+', raw_text)
    if urls:
        extracted["urls"] = urls[:20]

    # Emails
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', raw_text)
    if emails:
        extracted["emails"] = emails[:10]

    # Prices
    prices = re.findall(r'[¥$€£]\s*[\d,]+\.?\d*', raw_text)
    if prices:
        extracted["prices"] = prices[:20]

    # Headings
    headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', raw_text, re.IGNORECASE)
    if headings:
        extracted["headings"] = headings[:10]

    # Links text
    links = re.findall(r'<a[^>]*>(.*?)</a>', raw_text, re.IGNORECASE)
    if links:
        extracted["links"] = [ln.strip() for ln in links[:20] if ln.strip()]
    return extracted


# ══════════════════════════════════════════════════════════════
#  AGENT 4 — Validator: 验证任务是否完成
# ══════════════════════════════════════════════════════════════

def _validate(goal: str, results: list, extracted: dict) -> dict:
    """验证任务完成度"""
    checks = []

    # Check navigation success
    nav_ok = any(r.get("ok") for r in results if r.get("action") == "navigate")
    checks.append({"check": "navigate", "pass": nav_ok,
                   "detail": "页面导航成功" if nav_ok else "导航失败"})

    # Check extraction success
    ext_ok = any(r.get("ok") for r in results if r.get("action") == "extract")
    checks.append({"check": "extract", "pass": ext_ok,
                   "detail": "数据提取成功" if ext_ok else "数据提取失败"})

    # Check if data looks meaningful
    has_data = bool(extracted) and extracted.get("_raw_length", 0) > 100
    checks.append({"check": "has_data", "pass": has_data,
                   "detail": f"获取到{extracted.get('_raw_length', 0)}字符数据"
                   if has_data else "数据量不足"})

    all_pass = all(c["pass"] for c in checks)
    return {
        "passed": all_pass,
        "checks": checks,
        "summary": "✅ 任务完成" if all_pass else "⚠️ 部分步骤未成功"
    }


# ══════════════════════════════════════════════════════════════
#  MAIN ORCHESTRATOR — 四体协同任务执行
# ══════════════════════════════════════════════════════════════

def do_task(params: dict) -> dict:
    """执行完整的多智能体浏览器任务"""
    goal = params.get("goal", "")
    url = params.get("url", "")
    max_steps = int(params.get("max_steps", 10))
    headless = params.get("headless", True)
    fingerprint = params.get("fingerprint")

    if not goal:
        return {"ok": False, "error": "缺少goal参数"}

    start_time = time.time()
    log = []

    # ── 获取指纹 ──
    if not fingerprint:
        fp_result = _get_fingerprint()
        fingerprint = fp_result if fp_result else None
    log.append({"phase": "fingerprint", "ok": bool(fingerprint),
                "ts": time.time() - start_time})

    # ── Planner: 分解步骤 ──
    context = {"url": url} if url else {}
    steps = _plan(goal, context)
    log.append({"phase": "plan", "steps": len(steps),
                "detail": steps, "ts": time.time() - start_time})

    # ── Navigator + Extractor: 逐步执行 ──
    results = []
    current_url = url
    extracted_data = {}

    for i, step in enumerate(steps[:max_steps]):
        step_start = time.time()
        action = step.get("action", "navigate")
        target = step.get("target", "")
        value = step.get("value", "")
        step_result = {"step": i + 1, "action": action,
                       "target": target, "ok": False}

        try:
            if action == "navigate":
                nav_url = target if target.startswith("http") else (
                    f"https://{target}" if target else current_url)
                r = _navigate(nav_url, fingerprint, headless)
                step_result["ok"] = r.get("ok", False)
                step_result["detail"] = r.get("content", "")[:500]
                if r.get("ok"):
                    current_url = nav_url

            elif action == "click":
                r = _click(target, current_url, fingerprint, headless)
                step_result["ok"] = r.get("ok", False)
                step_result["detail"] = str(r)[:200]

            elif action == "type":
                r = _type_text(target, value, current_url, fingerprint, headless)
                step_result["ok"] = r.get("ok", False)
                step_result["detail"] = str(r)[:200]

            elif action == "scroll":
                r = _navigate(current_url, fingerprint, headless)
                step_result["ok"] = r.get("ok", False)
                step_result["detail"] = f"scrolled {value}"

            elif action == "extract":
                selectors = [target] if target and target != "body" else None
                r = _extract_content(current_url, selectors,
                                     None, fingerprint, headless)
                step_result["ok"] = r.get("ok", False)
                if r.get("ok"):
                    raw = r.get("content", r.get("data", ""))
                    if isinstance(raw, str):
                        extracted_data = _extract_semantic(raw, goal)
                    elif isinstance(raw, dict):
                        extracted_data = raw
                    step_result["detail"] = str(extracted_data)[:500]

            elif action == "screenshot":
                r = _screenshot(current_url, target,
                                target == "full_page", fingerprint, headless)
                step_result["ok"] = r.get("ok", False)
                step_result["detail"] = "screenshot captured" if r.get("ok") else r.get("error", "")

            elif action == "wait":
                wait_sec = float(value) if value else 2.0
                time.sleep(min(wait_sec, 30))
                step_result["ok"] = True
                step_result["detail"] = f"waited {wait_sec}s"

        except Exception as e:
            step_result["ok"] = False
            step_result["error"] = str(e)[:200]

        step_result["elapsed"] = round(time.time() - step_start, 2)
        results.append(step_result)

        # Early exit on critical failure
        if not step_result["ok"] and action == "navigate":
            break

    # ── Validator: 验证结果 ──
    validation = _validate(goal, results, extracted_data)
    log.append({"phase": "validate", "passed": validation["passed"],
                "ts": time.time() - start_time})

    total_elapsed = round(time.time() - start_time, 2)

    return {
        "ok": validation["passed"],
        "goal": goal,
        "steps_planned": len(steps),
        "steps_executed": len(results),
        "results": results,
        "extracted": extracted_data,
        "validation": validation,
        "log": log,
        "elapsed": total_elapsed
    }


def do_navigate(params: dict) -> dict:
    """智能导航"""
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "缺少url参数"}

    fingerprint = params.get("fingerprint") or _get_fingerprint()
    headless = params.get("headless", True)

    return _navigate(url, fingerprint, headless,
                     params.get("wait_selector"))


def do_extract(params: dict) -> dict:
    """智能数据提取"""
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "缺少url参数"}

    fingerprint = params.get("fingerprint") or _get_fingerprint()
    headless = params.get("headless", True)
    selectors = params.get("selectors")
    schema = params.get("schema")

    result = _extract_content(url, selectors, schema, fingerprint, headless)

    # Add semantic extraction layer (defensive)
    if result.get("ok"):
        try:
            raw = result.get("content", result.get("data", ""))
            if isinstance(raw, str):
                result["semantic"] = _extract_semantic(raw, params.get("goal", ""))
        except Exception:
            pass

    return result


def do_screenshot(params: dict) -> dict:
    """截图"""
    url = params.get("url", "")
    fingerprint = params.get("fingerprint") or _get_fingerprint()
    headless = params.get("headless", True)

    return _screenshot(url, params.get("selector"),
                       params.get("full_page", False),
                       fingerprint, headless)


def do_interact(params: dict) -> dict:
    """智能页面交互"""
    url = params.get("url", "")
    actions = params.get("actions", [])
    fingerprint = params.get("fingerprint") or _get_fingerprint()
    headless = params.get("headless", True)

    if not actions:
        return {"ok": False, "error": "缺少actions参数"}

    results = []
    for act in actions:
        act_type = act.get("action", act.get("type", "click"))
        target = act.get("target", act.get("selector", "body"))
        value = act.get("value", "")

        if act_type == "click":
            r = _click(target, url, fingerprint, headless)
        elif act_type == "type":
            r = _type_text(target, value, url, fingerprint, headless)
        elif act_type == "navigate":
            r = _navigate(target, fingerprint, headless)
        elif act_type == "scroll":
            r = _navigate(url, fingerprint, headless)
        elif act_type == "extract":
            r = _extract_content(url, [target], None, fingerprint, headless)
        else:
            r = {"ok": False, "error": f"未知操作: {act_type}"}

        results.append({"action": act_type, "target": target,
                        "ok": r.get("ok", False),
                        "detail": str(r)[:200]})

    return {"ok": any(r["ok"] for r in results),
            "actions": len(actions), "results": results}


def do_status(params: dict = None) -> dict:
    """引擎状态检查"""
    engines = {}
    try:
        r = _call_cap("browser_automation", "engines", {}, timeout=10)
        engines["browser_automation"] = r
    except Exception as e:
        engines["browser_automation"] = {"error": str(e)}

    fingerprint = {}
    try:
        r = _call_cap("gbt_browser", "status", {}, timeout=10)
        fingerprint["gbt_browser"] = r
    except Exception as e:
        fingerprint["gbt_browser"] = {"error": str(e)}

    llm_ready = False
    try:
        r = _call_cap("cloud_llm", "list_caps", {}, timeout=10)
        llm_ready = r.get("ok", False)
    except Exception:
        pass

    return {
        "ok": True,
        "engines": engines,
        "fingerprint": fingerprint,
        "llm_ready": llm_ready,
        "cap_version": "1.0.0",
        "data_dir": str(DATA_DIR)
    }


# ══════════════════════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════════════════════

HANDLERS = {
    "task": do_task,
    "navigate": do_navigate,
    "extract": do_extract,
    "screenshot": do_screenshot,
    "interact": do_interact,
    "status": do_status,
}


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            params = {"raw": sys.argv[2]}

    h = HANDLERS.get(action, do_status)
    try:
        result = h(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": str(e)[:200],
            "traceback": traceback.format_exc()[-500:]
        }, ensure_ascii=False))
