// ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
// recipes/monitor.js — 页面监控 & 变化检测
// ==============================================================

/**
 * 轮询监控页面变化
 */
async function monitor(bm, opts = {}) {
  const {
    url,
    checkSelector,      // 要监控的元素
    interval = 5000,     // 轮询间隔 ms
    maxChecks = 60,
    onChange,            // (oldValue, newValue) => void
    extractFn,           // (el) => value, 默认 innerText
  } = opts;

  await bm.page.goto(url, { waitUntil: 'networkidle2' });
  let lastValue;

  for (let i = 0; i < maxChecks; i++) {
    const value = await bm.page.evaluate((sel, fn) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      return fn ? fn(el) : el.innerText.trim();
    }, checkSelector, extractFn?.toString());

    if (lastValue !== undefined && value !== lastValue) {
      bm.debug(`Change detected at check ${i + 1}`);
      if (onChange) onChange(lastValue, value);
      return { changed: true, check: i + 1, oldValue: lastValue, newValue: value };
    }

    lastValue = value;
    await bm._sleep(interval);
  }

  return { changed: false, checks: maxChecks, lastValue };
}

/**
 * 等待特定元素出现后截图
 */
async function captureOnAppear(bm, opts = {}) {
  const { selector, timeout = 30000, savePath } = opts;
  try {
    await bm.page.waitForSelector(selector, { visible: true, timeout });
    const screenshot = await bm.screenshot(selector);
    return { ok: true, appeared: true, screenshot };
  } catch {
    return { ok: true, appeared: false };
  }
}

module.exports = { monitor, captureOnAppear };
