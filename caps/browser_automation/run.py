# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""browser_automation/run.py — AI浏览器自动化引擎
================================================
SeleniumBase + Playwright双引擎 · Headless模式 · CDP协议 · 视觉定位
"""
import sys, json, os, subprocess, time, base64
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


from _shared import _call_cap, _get_sandbox
SANDBOX = _get_sandbox()

def _get_selenium_driver(headless=True):
    """获取SeleniumBase驱动 (优先)"""
    try:
        from seleniumbase import Driver
        driver = Driver(browser="chrome", headless=headless, uc=True)  # undetected-chrome
        return driver, "seleniumbase"
    except ImportError:
        pass
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=opts)
        return driver, "selenium"
    except:
        return None, "selenium_not_installed"

def _get_playwright_browser(headless=True):
    """获取Playwright浏览器 (备选)"""
    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        return {"pw": pw, "browser": browser, "page": page}, "playwright"
    except:
        return None, "playwright_not_installed"

def do_navigate(params):
    """导航到URL并返回页面内容"""
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "缺少url参数"}
    
    headless = params.get("headless", True)
    engine = params.get("engine", "auto")
    wait = params.get("wait", 3000)
    
    result = {"ok": True, "cap": "browser_automation", "action": "navigate", "url": url}
    
    # 尝试SeleniumBase
    if engine in ("auto", "seleniumbase", "selenium"):
        driver, name = _get_selenium_driver(headless)
        if driver:
            try:
                driver.get(url)
                time.sleep(wait / 1000)
                result["title"] = driver.title
                result["url_final"] = driver.current_url
                result["content_preview"] = driver.page_source[:3000]
                result["engine"] = name
                if not headless:
                    input("按Enter关闭浏览器...")
                driver.quit()
                return result
            except Exception as e:
                driver.quit()
                if engine != "auto":
                    return {"ok": False, "error": str(e)[:200]}
    
    # 尝试Playwright
    if engine in ("auto", "playwright"):
        pw_ctx, name = _get_playwright_browser(headless)
        if pw_ctx:
            try:
                page = pw_ctx["page"]
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(wait / 1000)
                result["title"] = page.title()
                result["url_final"] = page.url
                result["content_preview"] = page.content()[:3000]
                result["engine"] = name
                pw_ctx["browser"].close()
                pw_ctx["pw"].stop()
                return result
            except Exception as e:
                pw_ctx["browser"].close()
                pw_ctx["pw"].stop()
                if engine != "auto":
                    return {"ok": False, "error": str(e)[:200]}
    
    return {"ok": False, "error": "无可用浏览器引擎。pip install seleniumbase 或 pip install playwright",
            "install": ["pip install seleniumbase", "pip install playwright && playwright install chromium"]}

def do_screenshot(params):
    """截取页面截图 (base64)"""
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "缺少url参数"}
    
    driver, name = _get_selenium_driver(headless=True)
    if not driver:
        return {"ok": False, "error": "需要selenium: pip install seleniumbase"}
    
    try:
        driver.get(url)
        time.sleep(2)
        ss = driver.get_screenshot_as_base64()
        driver.quit()
        return {"ok": True, "cap": "browser_automation", "action": "screenshot",
                "url": url, "engine": name, "image_base64": ss, "format": "png"}
    except Exception as e:
        driver.quit()
        return {"ok": False, "error": str(e)[:200]}

def do_fill_form(params):
    """自动填表"""
    url = params.get("url", "")
    fields = params.get("fields", {})
    submit_selector = params.get("submit", "button[type=submit]")
    
    if not url or not fields:
        return {"ok": False, "error": "缺少url/fields参数"}
    
    driver, name = _get_selenium_driver(headless=False)
    if not driver:
        return {"ok": False, "error": "需要selenium: pip install seleniumbase"}
    
    try:
        from selenium.webdriver.common.by import By
        driver.get(url)
        time.sleep(1)
        
        filled = []
        for selector, value in fields.items():
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                el.clear()
                el.send_keys(str(value))
                filled.append(selector)
            except:
                pass
        
        if submit_selector:
            try:
                driver.find_element(By.CSS_SELECTOR, submit_selector).click()
                filled.append(f"submit:{submit_selector}")
            except:
                pass
        
        time.sleep(2)
        driver.quit()
        return {"ok": True, "cap": "browser_automation", "action": "fill_form",
                "url": url, "engine": name, "filled": filled, "count": len(filled)}
    except Exception as e:
        driver.quit()
        return {"ok": False, "error": str(e)[:200]}

def do_extract_data(params):
    """提取页面结构化数据 — 支持CSS选择器 + 分页抓取食谱"""
    url = params.get("url", "")
    selectors = params.get("selectors", {})
    recipe = params.get("recipe", None)  # "paginated", "infinite_scroll", None=css
    
    if not url and not recipe:
        return {"ok": False, "error": "缺少url参数"}
    
    # ── 食谱模式：委托 Node.js recipes ──
    if recipe:
        import tempfile
        recipes_dir = Path(__file__).parent / "recipes"
        mastery_js = Path(__file__).parent / "browser-mastery.js"
        tmp_params = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        tmp_params.write(json.dumps(params, ensure_ascii=False))
        tmp_params.close()
        runner_js = recipes_dir / ".." / "_recipe_runner.js"
        runner_src = f"""
const BrowserMastery = require({json.dumps(str(mastery_js))});
const recipes = require({json.dumps(str(recipes_dir / 'index.js'))});
const params = require({json.dumps(str(Path(tmp_params.name).resolve()))});
(async () => {{
    const puppeteer = require('puppeteer');
    const browser = await puppeteer.launch({{ headless: 'new' }});
    const page = await browser.newPage();
    const bm = await BrowserMastery.create(page, browser);
    await bm.page.goto(params.url, {{ waitUntil: 'networkidle2' }});
    let result;
    if (params.recipe === 'paginated') {{
        result = await recipes.scrape.scrapePaginated(bm, params);
    }} else if (params.recipe === 'infinite_scroll') {{
        result = await recipes.scrape.scrapeInfiniteScroll(bm, params);
    }} else {{
        result = {{ error: 'unknown recipe: ' + params.recipe }};
    }}
    await browser.close();
    console.log(JSON.stringify(result));
}})();
"""
        tmp_runner = tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8")
        tmp_runner.write(runner_src)
        tmp_runner.close()
        try:
            r = subprocess.run(["node", tmp_runner.name], capture_output=True, text=True, timeout=120,
                               cwd=str(SANDBOX), encoding="utf-8", errors="replace")
            out = (r.stdout or r.stderr or "").strip()
            data = json.loads(out) if out.startswith("{") or out.startswith("[") else {"raw": out[:5000]}
            return {"ok": True, "cap": "browser_automation", "action": "extract_data",
                    "url": url, "recipe": recipe, "data": data}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "食谱执行超时(120s)"}
        except Exception as e:
            return {"ok": False, "error": f"食谱执行失败: {e}"}
        finally:
            try: Path(tmp_params.name).unlink()
            except: pass
            try: Path(tmp_runner.name).unlink()
            except: pass
    
    # ── CSS选择器模式 (现有逻辑) ──
    driver, name = _get_selenium_driver(headless=True)
    if not driver:
        return {"ok": False, "error": "需要selenium: pip install seleniumbase"}
    
    try:
        from selenium.webdriver.common.by import By
        driver.get(url)
        time.sleep(2)
        
        data = {}
        for key, css in selectors.items():
            try:
                els = driver.find_elements(By.CSS_SELECTOR, css)
                data[key] = [el.text.strip() for el in els[:20] if el.text.strip()]
            except:
                data[key] = []
        
        driver.quit()
        return {"ok": True, "cap": "browser_automation", "action": "extract_data",
                "url": url, "engine": name, "data": data, "selectors_used": len(selectors)}
    except Exception as e:
        driver.quit()
        return {"ok": False, "error": str(e)[:200]}
def do_autonomous_patrol(params):
    """自主巡逻：按序访问多个URL，每步截图留证"""
    urls = params.get("urls", [])
    if not urls:
        return {"ok": False, "error": "缺少urls参数 (list of {url, wait?, screenshot?, actions?})"}
    
    headless = params.get("headless", True)
    engine = params.get("engine", "auto")
    patrol_log = []
    overall_ok = True
    
    driver, driver_name = _get_selenium_driver(headless)
    if not driver:
        return {"ok": False, "error": "需要selenium: pip install seleniumbase"}
    
    try:
        for idx, step in enumerate(urls):
            step_url = step.get("url", "") if isinstance(step, dict) else str(step)
            if not step_url:
                patrol_log.append({"step": idx, "ok": False, "error": "缺少url"})
                overall_ok = False
                continue
            
            wait_s = (step.get("wait", 3000) if isinstance(step, dict) else 3000) / 1000
            want_screenshot = step.get("screenshot", True) if isinstance(step, dict) else True
            step_actions = step.get("actions", []) if isinstance(step, dict) else []
            
            entry = {"step": idx, "url": step_url, "ok": True}
            try:
                driver.get(step_url)
                time.sleep(wait_s)
                entry["title"] = driver.title
                entry["url_final"] = driver.current_url
                
                if want_screenshot:
                    entry["screenshot_base64"] = driver.get_screenshot_as_base64()
                
                # 执行子动作
                for act in step_actions:
                    act_type = act.get("type", "")
                    sel = act.get("selector", "")
                    if act_type == "click" and sel:
                        from selenium.webdriver.common.by import By
                        el = driver.find_element(By.CSS_SELECTOR, sel)
                        el.click()
                        time.sleep(act.get("wait", 1000) / 1000)
                    elif act_type == "type" and sel:
                        from selenium.webdriver.common.by import By
                        el = driver.find_element(By.CSS_SELECTOR, sel)
                        el.clear()
                        el.send_keys(act.get("text", ""))
                        time.sleep(act.get("wait", 500) / 1000)
                    elif act_type == "scroll":
                        driver.execute_script(f"window.scrollBy(0, {act.get('distance', 500)})")
                        time.sleep(act.get("wait", 500) / 1000)
                    elif act_type == "wait":
                        time.sleep(act.get("ms", 1000) / 1000)
                
            except Exception as e:
                entry["ok"] = False
                entry["error"] = str(e)[:200]
                overall_ok = False
            
            patrol_log.append(entry)
        
        driver.quit()
        return {"ok": overall_ok, "cap": "browser_automation", "action": "autonomous_patrol",
                "total_steps": len(urls), "steps": patrol_log, "engine": driver_name}
    except Exception as e:
        try: driver.quit()
        except: pass
        return {"ok": False, "error": str(e)[:200]}


def do_monitor_page(params):
    """页面监控：轮询URL检测内容变化"""
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "缺少url参数"}
    
    selector = params.get("selector", "body")
    interval_s = float(params.get("interval_seconds", 5))
    max_checks = int(params.get("max_checks", 12))
    headless = params.get("headless", True)
    
    driver, driver_name = _get_selenium_driver(headless)
    if not driver:
        return {"ok": False, "error": "需要selenium: pip install seleniumbase"}
    
    try:
        from selenium.webdriver.common.by import By
        driver.get(url)
        time.sleep(2)
        
        def _extract_text(d, sel):
            try:
                el = d.find_element(By.CSS_SELECTOR, sel)
                return el.text.strip()[:5000]
            except:
                return None
        
        last_value = _extract_text(driver, selector)
        checks = [{"check": 0, "value": last_value[:200] if last_value else None}]
        
        for i in range(1, max_checks):
            time.sleep(interval_s)
            driver.refresh()
            time.sleep(2)
            current = _extract_text(driver, selector)
            checks.append({"check": i, "value": current[:200] if current else None})
            
            if last_value is not None and current is not None and current != last_value:
                driver.quit()
                return {"ok": True, "cap": "browser_automation", "action": "monitor_page",
                        "url": url, "changed": True, "check_index": i,
                        "old_value_preview": last_value[:500],
                        "new_value_preview": current[:500],
                        "total_checks": i + 1, "checks_log": checks,
                        "engine": driver_name}
            last_value = current
        
        driver.quit()
        return {"ok": True, "cap": "browser_automation", "action": "monitor_page",
                "url": url, "changed": False, "total_checks": max_checks,
                "last_value_preview": (last_value or "")[:500],
                "checks_log": checks, "engine": driver_name}
    except Exception as e:
        try: driver.quit()
        except: pass
        return {"ok": False, "error": str(e)[:200]}

def do_engines(params):
    """检测可用浏览器引擎"""
    engines = {}
    d, n = _get_selenium_driver(headless=True)
    if d:
        engines["seleniumbase"] = "ready"
        d.quit()
    else:
        engines["seleniumbase"] = "not_installed"
    
    pw, n = _get_playwright_browser(headless=True)
    if pw:
        engines["playwright"] = "ready"
        pw["browser"].close()
        pw["pw"].stop()
HANDLERS = {
    "navigate": do_navigate, "screenshot": do_screenshot,
    "fill_form": do_fill_form, "extract_data": do_extract_data,
    "engines": do_engines, "run": do_navigate,
    "autonomous_patrol": do_autonomous_patrol,
    "monitor_page": do_monitor_page,
}


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "engines"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
