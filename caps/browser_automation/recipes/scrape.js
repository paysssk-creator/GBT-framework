// ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
// recipes/scrape.js — 智能数据抓取
// ==============================================================

/**
 * 分页抓取列表数据
 */
async function scrapePaginated(bm, opts = {}) {
  const {
    listSelector,      // 列表项选择器
    itemSelectors,     // { title, link, price, ... }
    nextPageSelector,  // "下一页" 按钮
    maxPages = 10,
    waitBetween = 2000,
  } = opts;

  const allItems = [];

  for (let page = 0; page < maxPages; page++) {
    await bm.waitForStable();
    const items = await bm.page.evaluate((listSel, itemSel) => {
      const rows = [...document.querySelectorAll(listSel)];
      return rows.map(row => {
        const item = {};
        for (const [key, sel] of Object.entries(itemSel)) {
          const el = row.querySelector(sel);
          item[key] = el ? el.innerText.trim() : null;
        }
        return item;
      });
    }, listSelector, itemSelectors);

    allItems.push(...items);
    bm.debug(`Page ${page + 1}: scraped ${items.length} items (total: ${allItems.length})`);

    // 下一页
    const nextBtn = await bm.page.$(nextPageSelector);
    if (!nextBtn) break;
    const disabled = await nextBtn.evaluate(el => el.disabled || el.classList.contains('disabled'));
    if (disabled) break;

    await bm.humanClick(nextPageSelector);
    await bm._sleep(waitBetween);
  }

  return { total: allItems.length, items: allItems };
}

/**
 * 无限滚动抓取
 */
async function scrapeInfiniteScroll(bm, opts = {}) {
  const {
    itemSelector,
    extractFn, // (el) => data 或选择器映射
    maxScrolls = 50,
    scrollDistance = 800,
    waitBetween = 1500,
    stopWhen = null, // (items) => boolean
  } = opts;

  const items = new Set();
  let noNewCount = 0;

  for (let i = 0; i < maxScrolls; i++) {
    const newItems = await bm.page.evaluate((sel, fn) => {
      const els = [...document.querySelectorAll(sel)];
      if (typeof fn === 'function') return els.map(fn);
      if (typeof fn === 'object') {
        return els.map(el => {
          const item = {};
          for (const [k, s] of Object.entries(fn)) {
            const child = el.querySelector(s);
            item[k] = child ? child.innerText.trim() : null;
          }
          return item;
        });
      }
      return els.map(el => el.innerText.trim());
    }, itemSelector, extractFn);

    const before = items.size;
    newItems.forEach(item => items.add(JSON.stringify(item)));
    const added = items.size - before;

    if (added === 0) {
      noNewCount++;
      if (noNewCount >= 3) break;
    } else {
      noNewCount = 0;
    }

    if (stopWhen && stopWhen([...items].map(s => JSON.parse(s)))) break;

    await bm.humanScroll({ distance: scrollDistance, pause: waitBetween });
  }

  return { total: items.size, items: [...items].map(s => JSON.parse(s)) };
}

module.exports = { scrapePaginated, scrapeInfiniteScroll };
