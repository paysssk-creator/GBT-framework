// ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
// browser-mastery.js — 浏览器操控大师工具包
// Puppeteer + CDP 极限操控 · 隐身 · 拟人 · 多标签 · 网络层 · 持久化
// ================================================================

class BrowserMastery {
  constructor(page, browser, opts = {}) {
    this.page = page;
    this.browser = browser;
    this.opts = { stealth: true, humanLike: true, debug: false, ...opts };
    this._delay = [80, 350]; // 拟人延迟范围 ms
    this._sessions = new Map();
    this._networkLog = [];
  }

  // ==================== 隐身引擎 ====================

  async stealthMode() {
    const { page } = this;
    // 隐藏 webdriver 标记
    await page.evaluateOnNewDocument(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => false });
      Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
      Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
      // 伪造 chrome runtime
      window.chrome = { runtime: {} };
      // 伪造权限
      const origQuery = window.navigator.permissions.query;
      window.navigator.permissions.query = (params) =>
        params.name === 'notifications' ?
          Promise.resolve({ state: Notification.permission }) : origQuery(params);
    });
    // CDP 层隐身
    const client = await page.target().createCDPSession();
    await client.send('Page.addScriptToEvaluateOnNewDocument', {
      source: `
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
        Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
        delete window.__nightmare;
        delete window.callPhantom;
        delete window._phantom;
        delete window.__selenium_unwrapped;
        delete window.__webdriver_evaluate;
        delete window.__driver_evaluate;
        delete window.__webdriver_script_function;
        delete window.__webdriver_script_func;
        delete window.__webdriver_script_fn;
        delete window.__fxdriver_evaluate;
        delete window.__driver_unwrapped;
        delete window.__webdriver_unwrapped;
        delete window.__selenium_evaluate;
        delete window.__webdriver_evaluate;
      `
    });
    await client.detach();
    return this;
  }

  // ==================== 拟人交互 ====================

  _rand(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
  _sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  async humanDelay(min, max) {
    const [dMin, dMax] = min ? [min, max || min] : this._delay;
    const d = this._rand(dMin, dMax);
    if (this.opts.humanLike) await this._sleep(d);
    return d;
  }

  // 拟人鼠标移动
  async humanMove(selector) {
    const el = typeof selector === 'string' ? await this.page.$(selector) : selector;
    if (!el) throw new Error(`humanMove: element not found`);
    const box = await el.boundingBox();
    const startX = this._rand(100, 600);
    const startY = this._rand(100, 400);
    const steps = this._rand(8, 20);
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t; // easeInOut
      const x = startX + (box.x + box.width / 2 - startX) * ease + this._rand(-3, 3);
      const y = startY + (box.y + box.height / 2 - startY) * ease + this._rand(-3, 3);
      await this.page.mouse.move(x, y);
      await this._sleep(this._rand(5, 15));
    }
    return box;
  }

  // 拟人点击
  async humanClick(selector) {
    await this.humanDelay();
    await this.humanMove(selector);
    await this.humanDelay(50, 150);
    await this.page.mouse.click(0, 0); // 已在元素上
    await this.humanDelay(100, 300);
    return this;
  }

  // 拟人输入
  async humanType(selector, text) {
    const el = await this.page.$(selector);
    await el.click({ clickCount: 3 }); // 全选
    for (const ch of text) {
      await this.page.keyboard.type(ch);
      await this._sleep(this._rand(30, 120));
    }
    return this;
  }

  // 拟人滚动
  async humanScroll({ distance, duration = 2000, pause = 1500 } = {}) {
    const dist = distance || this._rand(300, 800);
    const steps = Math.floor(duration / 50);
    const stepSize = dist / steps;
    for (let i = 0; i < steps; i++) {
      await this.page.mouse.wheel({ deltaY: stepSize });
      await this._sleep(this._rand(30, 70));
    }
    await this._sleep(pause);
    return this;
  }

  // ==================== 智能等待 ====================

  async waitForStable(ms = 2000) {
    let lastHTML = '';
    let stable = 0;
    const maxChecks = 30;
    for (let i = 0; i < maxChecks; i++) {
      const html = await this.page.evaluate(() => document.body.innerHTML.length);
      if (html === lastHTML) {
        stable++;
        if (stable >= 3) return true;
      } else {
        stable = 0;
      }
      lastHTML = html;
      await this._sleep(ms / maxChecks);
    }
    return false;
  }

  async waitForText(text, { timeout = 10000 } = {}) {
    await this.page.waitForFunction(
      (t) => document.body.innerText.includes(t), { timeout }, text
    );
    return this;
  }

  async waitForNetworkIdle({ timeout = 30000, idleTime = 2000 } = {}) {
    let pending = 0;
    let lastActivity = Date.now();
    const onRequest = () => { pending++; lastActivity = Date.now(); };
    const onResponse = () => { pending--; lastActivity = Date.now(); };
    this.page.on('request', onRequest);
    this.page.on('response', onResponse);
    this.page.on('requestfailed', onResponse);
    const start = Date.now();
    while (Date.now() - start < timeout) {
      if (pending === 0 && Date.now() - lastActivity > idleTime) break;
      await this._sleep(200);
    }
    this.page.off('request', onRequest);
    this.page.off('response', onResponse);
    this.page.off('requestfailed', onResponse);
    return pending === 0;
  }

  // ==================== 多标签编排 ====================

  async newTab(url) {
    const page = await this.browser.newPage();
    if (this.opts.stealth) {
      const bm = new BrowserMastery(page, this.browser, this.opts);
      await bm.stealthMode();
    }
    if (url) await page.goto(url, { waitUntil: 'networkidle2' });
    return { page, id: page.target()._targetId };
  }

  // ==================== 网络层 ====================

  enableNetworkMonitor() {
    this.page.on('request', (req) => {
      this._networkLog.push({
        type: 'request',
        url: req.url(),
        method: req.method(),
        headers: req.headers(),
        timestamp: Date.now()
      });
    });
    this.page.on('response', (res) => {
      this._networkLog.push({
        type: 'response',
        url: res.url(),
        status: res.status(),
        headers: res.headers(),
        timestamp: Date.now()
      });
    });
    return this;
  }

  getNetworkLog(filter) {
    if (!filter) return this._networkLog;
    return this._networkLog.filter(e => e.url.includes(filter) || e.type === filter);
  }

  networkStats() {
    const reqs = this._networkLog.filter(e => e.type === 'request');
    const resps = this._networkLog.filter(e => e.type === 'response');
    const statuses = {};
    resps.forEach(r => { statuses[r.status] = (statuses[r.status] || 0) + 1; });
    const errors = resps.filter(r => r.status >= 400).length;
    return { totalRequests: reqs.length, totalResponses: resps.length, statuses, errors };
  }

  async interceptRequests(rules) {
    await this.page.setRequestInterception(true);
    this.page.on('request', (req) => {
      for (const rule of rules) {
        if (req.url().includes(rule.urlPattern)) {
          if (rule.block) { req.abort(); return; }
          if (rule.mock) {
            req.respond({ status: rule.mock.status || 200, contentType: rule.mock.contentType || 'application/json', body: JSON.stringify(rule.mock.body || {}) });
            return;
          }
          if (rule.redirect) { req.continue({ url: rule.redirect }); return; }
        }
      }
      req.continue();
    });
    return this;
  }

  // ==================== 会话持久化 ====================

  async saveSession(name) {
    const cookies = await this.page.cookies();
    const localStorage = await this.page.evaluate(() => JSON.stringify(window.localStorage));
    const sessionStorage = await this.page.evaluate(() => JSON.stringify(window.sessionStorage));
    const url = this.page.url();
    this._sessions.set(name, { cookies, localStorage, sessionStorage, url, timestamp: Date.now() });
    return { name, cookieCount: cookies.length, url };
  }

  async loadSession(name) {
    const session = this._sessions.get(name);
    if (!session) throw new Error(`Session "${name}" not found`);
    if (session.url) await this.page.goto(session.url, { waitUntil: 'domcontentloaded' });
    if (session.cookies.length) await this.page.setCookie(...session.cookies);
    await this.page.evaluate((ls) => {
      window.localStorage.clear();
      for (const [k, v] of Object.entries(JSON.parse(ls))) window.localStorage.setItem(k, v);
    }, session.localStorage || '{}');
    return this;
  }

  async exportSession(name) {
    const s = this._sessions.get(name);
    if (!s) throw new Error(`Session "${name}" not found`);
    return JSON.stringify(s, null, 2);
  }

  async importSession(json) {
    const s = typeof json === 'string' ? JSON.parse(json) : json;
    this._sessions.set(s.name || 'imported', s);
    return this;
  }

  // ==================== 智能提取 ====================

  async extractTable(selector) {
    return this.page.evaluate((sel) => {
      const table = document.querySelector(sel);
      if (!table) return [];
      const headers = [...table.querySelectorAll('th')].map(th => th.innerText.trim());
      const rows = [...table.querySelectorAll('tr')].slice(headers.length ? 1 : 0).map(tr =>
        [...tr.querySelectorAll('td')].map(td => td.innerText.trim())
      );
      if (headers.length) return rows.map(row => Object.fromEntries(headers.map((h, i) => [h, row[i] || ''])));
      return rows;
    }, selector);
  }

  async extractLinks(selector = 'a') {
    return this.page.evaluate((sel) =>
      [...document.querySelectorAll(sel)].map(a => ({ text: a.innerText.trim(), href: a.href })).filter(l => l.href), selector);
  }

  async extractAllText(selector) {
    return this.page.evaluate((sel) =>
      (document.querySelector(sel) || document.body).innerText, selector);
  }

  async extractStructured(selectors) {
    const result = {};
    for (const [key, sel] of Object.entries(selectors)) {
      try {
        const el = await this.page.$(sel);
        result[key] = el ? await this.page.evaluate(e => e.innerText.trim(), el) : null;
      } catch { result[key] = null; }
    }
    return result;
  }

  // ==================== 智能填表 ====================

  async detectForms() {
    return this.page.evaluate(() =>
      [...document.querySelectorAll('form')].map(form => ({
        action: form.action,
        method: form.method,
        fields: [...form.querySelectorAll('input, select, textarea')].map(el => ({
          tag: el.tagName,
          type: el.type || '',
          name: el.name,
          id: el.id,
          placeholder: el.placeholder,
          required: el.required,
          label: (el.labels && el.labels[0]) ? el.labels[0].innerText.trim() : ''
        }))
      }))
    );
  }

  async fillFormSmart(formSelector, data) {
    const form = await this.page.$(formSelector);
    if (!form) throw new Error(`Form not found: ${formSelector}`);
    for (const [field, value] of Object.entries(data)) {
      const el = await form.$(`[name="${field}"], #${field}, [data-field="${field}"]`);
      if (!el) continue;
      const tag = await el.evaluate(e => e.tagName);
      if (tag === 'SELECT') {
        await el.select(value);
      } else if (tag === 'TEXTAREA' || (await el.evaluate(e => e.type)) === 'text') {
        await el.click({ clickCount: 3 });
        await el.type(String(value));
      } else if ((await el.evaluate(e => e.type)) === 'checkbox') {
        if (value) await el.click();
      } else if ((await el.evaluate(e => e.type)) === 'radio') {
        const radio = await form.$(`input[type="radio"][value="${value}"]`);
        if (radio) await radio.click();
      } else {
        await el.type(String(value));
      }
      await this.humanDelay(50, 150);
    }
    return this;
  }

  // ==================== 视觉操作 ====================

  async screenshot(selector, opts = {}) {
    const el = selector ? await this.page.$(selector) : this.page;
    return el.screenshot({ encoding: 'base64', ...opts });
  }

  async fullPageScreenshot() {
    return this.page.screenshot({ fullPage: true, encoding: 'base64' });
  }

  async elementState(selector) {
    try {
      const el = await this.page.$(selector);
      if (!el) return { exists: false };
      const box = await el.boundingBox();
      const visible = await el.evaluate(e => {
        const style = window.getComputedStyle(e);
        return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
      });
      const text = await el.evaluate(e => e.innerText?.trim() || '');
      return { exists: true, visible, boundingBox: box, text, enabled: !(await el.evaluate(e => e.disabled)) };
    } catch { return { exists: false }; }
  }

  // ==================== CDP 高级能力 ====================

  async cdp(command, params = {}) {
    const client = await this.page.target().createCDPSession();
    const result = await client.send(command, params);
    await client.detach();
    return result;
  }

  // 模拟地理位置
  async setGeolocation(lat, lng, accuracy = 100) {
    const client = await this.page.target().createCDPSession();
    await client.send('Emulation.setGeolocationOverride', { latitude: lat, longitude: lng, accuracy });
    await client.detach();
    return this;
  }

  // 模拟时区
  async setTimezone(timezoneId) {
    const client = await this.page.target().createCDPSession();
    await client.send('Emulation.setTimezoneOverride', { timezoneId });
    await client.detach();
    return this;
  }

  // 模拟设备
  async emulateDevice(device) {
    const devices = {
      'iPhone 14': { width: 390, height: 844, scale: 3, ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1', touch: true },
      'iPad Pro': { width: 1024, height: 1366, scale: 2, ua: 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1', touch: true },
      'Pixel 7': { width: 412, height: 915, scale: 2.625, ua: 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36', touch: true },
    };
    const d = devices[device] || device;
    await this.page.setViewport({ width: d.width, height: d.height, deviceScaleFactor: d.scale || 1, isMobile: !!d.touch, hasTouch: !!d.touch });
    if (d.ua) await this.page.setUserAgent(d.ua);
    return this;
  }

  // 注入 JS 库
  async injectLibrary(name) {
    const libs = {
      jquery: 'https://code.jquery.com/jquery-3.7.1.min.js',
    };
    const url = libs[name];
    if (url) await this.page.addScriptTag({ url });
    return this;
  }

  // 性能追踪
  async tracePerformance(duration = 5000) {
    const client = await this.page.target().createCDPSession();
    await client.send('Performance.enable');
    const startMetrics = await client.send('Performance.getMetrics');
    await this._sleep(duration);
    const endMetrics = await client.send('Performance.getMetrics');
    await client.detach();
    const metrics = {};
    for (let i = 0; i < startMetrics.metrics.length; i++) {
      const name = startMetrics.metrics[i].name;
      const delta = endMetrics.metrics[i].value - startMetrics.metrics[i].value;
      metrics[name] = delta;
    }
    return metrics;
  }

  // 注入自定义 CSS
  async injectCSS(css) {
    await this.page.addStyleTag({ content: css });
    return this;
  }

  // ==================== 高级动作 ====================

  // 右键菜单
  async rightClick(selector) {
    await this.humanMove(selector);
    await this.page.mouse.click(0, 0, { button: 'right' });
    return this;
  }

  // 拖拽
  async dragDrop(fromSelector, toSelector) {
    const from = await this.page.$(fromSelector);
    const to = await this.page.$(toSelector);
    const fromBox = await from.boundingBox();
    const toBox = await to.boundingBox();
    await this.page.mouse.move(fromBox.x + fromBox.width / 2, fromBox.y + fromBox.height / 2);
    await this.page.mouse.down();
    await this._sleep(100);
    const steps = 10;
    for (let i = 1; i <= steps; i++) {
      const x = fromBox.x + fromBox.width / 2 + (toBox.x + toBox.width / 2 - fromBox.x - fromBox.width / 2) * (i / steps);
      const y = fromBox.y + fromBox.height / 2 + (toBox.y + toBox.height / 2 - fromBox.y - fromBox.height / 2) * (i / steps);
      await this.page.mouse.move(x, y);
      await this._sleep(20);
    }
    await this.page.mouse.up();
    return this;
  }

  // 键盘快捷键
  async hotkey(...keys) {
    for (const key of keys) await this.page.keyboard.down(key);
    for (const key of keys.reverse()) await this.page.keyboard.up(key);
    return this;
  }

  // ==================== 工具方法 ====================

  async url() { return this.page.url(); }
  async title() { return this.page.title(); }
  async content() { return this.page.content(); }
  async pdf(opts = {}) { return this.page.pdf({ format: 'A4', ...opts }); }
  async close() { await this.page.close(); return this; }

  debug(msg) { if (this.opts.debug) console.log(`[BrowserMastery] ${msg}`); return this; }
}

// 便捷工厂
BrowserMastery.create = async function(page, browser, opts) {
  const bm = new BrowserMastery(page, browser, opts);
  if (opts.stealth !== false) await bm.stealthMode();
  return bm;
};

// 按名称管理多标签
BrowserMastery.tabs = class TabManager {
  constructor(browser) {
    this.browser = browser;
    this.tabs = new Map();
  }
  async open(name, url, opts) {
    const page = await this.browser.newPage();
    const bm = await BrowserMastery.create(page, this.browser, opts);
    this.tabs.set(name, bm);
    if (url) await page.goto(url, { waitUntil: 'networkidle2' });
    return bm;
  }
  get(name) { return this.tabs.get(name); }
  async close(name) { const bm = this.tabs.get(name); if (bm) { await bm.close(); this.tabs.delete(name); } }
  async closeAll() { for (const [name] of this.tabs) await this.close(name); }
  list() { return [...this.tabs.keys()]; }
};

module.exports = BrowserMastery;
