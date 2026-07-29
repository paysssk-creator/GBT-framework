// ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
// recipes/login.js — 通用登录自动化
// 用法: browser.run → require('./caps/browser_automation/browser-mastery') → recipes.login(...)
// ==============================================================

/**
 * 通用登录自动化
 * @param {BrowserMastery} bm
 * @param {object} opts
 * @param {string} opts.url - 登录页 URL
 * @param {object} opts.selectors - { username, password, submit }
 * @param {object} opts.credentials - { username, password }
 * @param {string} opts.successIndicator - 登录成功后页面包含的文本
 */
async function login(bm, opts) {
  const { url, selectors, credentials, successIndicator } = opts;

  await bm.page.goto(url, { waitUntil: 'networkidle2' });
  await bm.waitForStable();

  // 检测是否已登录
  if (successIndicator) {
    const html = await bm.page.content();
    if (html.includes(successIndicator)) {
      bm.debug('Already logged in');
      return { ok: true, alreadyLoggedIn: true };
    }
  }

  // 填表
  await bm.humanType(selectors.username, credentials.username);
  await bm.humanDelay();
  await bm.humanType(selectors.password, credentials.password);
  await bm.humanDelay();

  // 提交
  await bm.humanClick(selectors.submit);

  // 等待跳转
  try {
    await bm.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 });
  } catch {
    // 可能没跳转 (SPA)
    await bm.waitForStable(3000);
  }

  // 验证
  if (successIndicator) {
    const content = await bm.page.content();
    if (!content.includes(successIndicator)) {
      return { ok: false, error: 'Login failed: success indicator not found', url: bm.page.url() };
    }
  }

  await bm.saveSession('login');
  return { ok: true, url: bm.page.url(), session: 'login' };
}

// 常见站点登录预设
const presets = {
  github: {
    url: 'https://github.com/login',
    selectors: { username: '#login_field', password: '#password', submit: 'input[type="submit"]' },
    successIndicator: 'Dashboard',
  },
  gmail: {
    url: 'https://accounts.google.com/signin',
    selectors: { username: 'input[type="email"]', password: 'input[type="password"]', submit: '#identifierNext' },
    successIndicator: 'inbox',
  },
};

module.exports = { login, presets };
