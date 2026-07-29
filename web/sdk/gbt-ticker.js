/* ═══════════════════════════════════════════════════════════
   GBT 实时行情 — 国际比价表
   数据源: BestChange (600+交易所) + CoinGecko/CoinMarketCap fallback
   ═══════════════════════════════════════════════════════════ */

const TICKER_CONFIG = {
  refreshInterval: 5000,  // 5秒刷新
  pairs: [
    { base: 'BTC',  quote: 'USDT', icon: '₿',  name: 'Bitcoin' },
    { base: 'ETH',  quote: 'USDT', icon: 'Ξ',  name: 'Ethereum' },
    { base: 'SOL',  quote: 'USDT', icon: '◎',  name: 'Solana' },
    { base: 'BNB',  quote: 'USDT', icon: '🔶', name: 'BNB' },
    { base: 'TRX',  quote: 'USDT', icon: '⬡',  name: 'TRON' },
    { base: 'MATIC',quote: 'USDT', icon: '⬢',  name: 'Polygon' },
    { base: 'USDT', quote: 'CNY',  icon: '💲',  name: 'Tether/CNY' },
    { base: 'BTC',  quote: 'CNY',  icon: '₿',  name: 'Bitcoin/CNY' },
  ],
  // 涨跌颜色
  upColor: '#30d158',
  downColor: '#ff4757',
};

class RealtimeTicker {
  constructor() {
    this.data = new Map();
    this.listeners = [];
    this.running = false;
  }

  async start() {
    if (this.running) return;
    this.running = true;
    await this.fetchAll();
    this._interval = setInterval(() => this.fetchAll(), TICKER_CONFIG.refreshInterval);
  }

  stop() {
    this.running = false;
    if (this._interval) clearInterval(this._interval);
  }

  async fetchAll() {
    const results = await Promise.allSettled(
      TICKER_CONFIG.pairs.map(pair => this.fetchPair(pair))
    );

    results.forEach((r, i) => {
      if (r.status === 'fulfilled' && r.value) {
        const pair = TICKER_CONFIG.pairs[i];
        const key = `${pair.base}/${pair.quote}`;
        const prev = this.data.get(key);
        
        // 计算涨跌
        const change24h = prev ? ((r.value.price - prev.price) / prev.price * 100) : 0;
        
        this.data.set(key, {
          ...r.value,
          pair: key,
          base: pair.base,
          quote: pair.quote,
          icon: pair.icon,
          name: pair.name,
          change24h: change24h,
          updated: Date.now(),
        });
      }
    });

    this.notify();
  }

  async fetchPair(pair) {
    // 优先 BestChange
    try {
      const res = await fetch(`/api/rates?from=${pair.base}&to=${pair.quote}`);
      if (res.ok) {
        const d = await res.json();
        if (d.bestchange?.rate) {
          return { price: d.bestchange.rate, source: 'bestchange', depth: d.bestchange.depth };
        }
      }
    } catch(e) {}

    // Fallback: CoinGecko 免费 API
    try {
      const ids = { BTC: 'bitcoin', ETH: 'ethereum', SOL: 'solana', BNB: 'binancecoin', TRX: 'tron', MATIC: 'matic-network', USDT: 'tether' };
      const id = ids[pair.base];
      if (!id) throw new Error('unknown');

      const res = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${id}&vs_currencies=usd,cny&include_24hr_change=true`);
      const d = await res.json();
      
      const quoteCurrency = pair.quote === 'CNY' ? 'cny' : 'usd';
      const price = d[id]?.[quoteCurrency];
      
      if (price) {
        return { price, source: 'coingecko', depth: 0 };
      }
    } catch(e) {}

    // Fallback: 静态汇率
    const rate = CONVERSION_RATES?.[pair.base] || 1;
    return { price: rate, source: 'static', depth: 0 };
  }

  get(key) { return this.data.get(key); }
  getAll() { return Array.from(this.data.values()); }

  onChange(fn) { this.listeners.push(fn); }
  notify() { this.listeners.forEach(fn => fn(this.getAll())); }
}

// ═══════════════════════════════════════════════════════════
// 行情表 UI 组件 (注入钱包)
// ═══════════════════════════════════════════════════════════

function createTickerHTML() {
  return `
    <div class="gbt-ticker" style="
      background: var(--bg2, #08080c);
      border: 1px solid var(--border, rgba(255,255,255,.06));
      border-radius: 14px;
      overflow: hidden;
      margin-bottom: 16px;
    ">
      <div style="
        display: flex; align-items: center; justify-content: space-between;
        padding: 14px 18px;
        border-bottom: 1px solid var(--border);
      ">
        <div style="font-size: 14px; font-weight: 700;">
          📊 实时行情
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="gbt-ticker-status" style="width: 6px; height: 6px; border-radius: 50%; background: #30d158;"></span>
          <span class="gbt-ticker-time" style="font-size: 10px; color: var(--dim);">实时</span>
        </div>
      </div>

      <div class="gbt-ticker-table" style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border);">
              <th style="padding: 10px 14px; text-align: left; color: var(--dim); font-weight: 500; font-size: 10px; text-transform: uppercase; letter-spacing: .5px;">币种</th>
              <th style="padding: 10px 14px; text-align: right; color: var(--dim); font-weight: 500; font-size: 10px; text-transform: uppercase; letter-spacing: .5px;">最新价</th>
              <th style="padding: 10px 14px; text-align: right; color: var(--dim); font-weight: 500; font-size: 10px; text-transform: uppercase; letter-spacing: .5px;">24h 涨跌</th>
              <th style="padding: 10px 14px; text-align: right; color: var(--dim); font-weight: 500; font-size: 10px; text-transform: uppercase; letter-spacing: .5px;">来源</th>
            </tr>
          </thead>
          <tbody class="gbt-ticker-body">
            ${TICKER_CONFIG.pairs.map(p => `
              <tr class="gbt-ticker-row" data-pair="${p.base}/${p.quote}" style="border-bottom: 1px solid rgba(255,255,255,.02); transition: background .15s;">
                <td style="padding: 10px 14px;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">${p.icon}</span>
                    <div>
                      <div style="font-weight: 600;">${p.base}<span style="color:var(--dim);font-weight:400;">/${p.quote}</span></div>
                      <div style="font-size: 10px; color: var(--dim);">${p.name}</div>
                    </div>
                  </div>
                </td>
                <td class="gbt-ticker-price" data-pair="${p.base}/${p.quote}" style="padding: 10px 14px; text-align: right; font-weight: 600; font-family: 'SF Mono','Fira Code',monospace;">—</td>
                <td class="gbt-ticker-change" data-pair="${p.base}/${p.quote}" style="padding: 10px 14px; text-align: right; font-weight: 600;">—</td>
                <td class="gbt-ticker-source" data-pair="${p.base}/${p.quote}" style="padding: 10px 14px; text-align: right; font-size: 10px; color: var(--dim);">—</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      <div style="
        padding: 8px 18px; font-size: 10px; color: var(--dim);
        border-top: 1px solid var(--border);
        display: flex; justify-content: space-between;
      ">
        <span>数据: BestChange · CoinGecko</span>
        <span class="gbt-ticker-updated">更新中...</span>
      </div>
    </div>
  `;
}

// ═══════════════════════════════════════════════════════════
// 行情更新逻辑
// ═══════════════════════════════════════════════════════════

function updateTickerUI(data) {
  data.forEach(item => {
    const pair = item.pair;
    const priceEl = document.querySelector(`.gbt-ticker-price[data-pair="${pair}"]`);
    const changeEl = document.querySelector(`.gbt-ticker-change[data-pair="${pair}"]`);
    const sourceEl = document.querySelector(`.gbt-ticker-source[data-pair="${pair}"]`);
    const row = document.querySelector(`.gbt-ticker-row[data-pair="${pair}"]`);

    if (priceEl) {
      const oldPrice = parseFloat(priceEl.textContent);
      const newPrice = item.price;
      
      // 格式化价格
      if (newPrice > 1000) priceEl.textContent = '$' + newPrice.toLocaleString('en-US', { maximumFractionDigits: 0 });
      else if (newPrice > 1) priceEl.textContent = '$' + newPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      else priceEl.textContent = '$' + newPrice.toFixed(6);

      // 价格变动闪烁
      if (oldPrice && oldPrice !== newPrice) {
        const color = newPrice > oldPrice ? TICKER_CONFIG.upColor : TICKER_CONFIG.downColor;
        priceEl.style.color = color;
        if (row) row.style.background = color === TICKER_CONFIG.upColor ? 'rgba(48,209,88,.04)' : 'rgba(255,71,87,.04)';
        setTimeout(() => {
          priceEl.style.color = '';
          if (row) row.style.background = '';
        }, 800);
      }
    }

    if (changeEl && item.change24h !== undefined) {
      const change = item.change24h;
      const sign = change >= 0 ? '+' : '';
      changeEl.textContent = sign + change.toFixed(2) + '%';
      changeEl.style.color = change >= 0 ? TICKER_CONFIG.upColor : TICKER_CONFIG.downColor;
    }

    if (sourceEl) {
      sourceEl.textContent = item.source === 'bestchange' ? 'BestChange' : 
                             item.source === 'coingecko' ? 'CoinGecko' : '静态';
    }
  });

  // 更新时间
  const timeEl = document.querySelector('.gbt-ticker-updated');
  if (timeEl) {
    timeEl.textContent = '更新于 ' + new Date().toLocaleTimeString();
  }
}

// ═══════════════════════════════════════════════════════════
// 注入钱包
// ═══════════════════════════════════════════════════════════

function injectTickerIntoTarget() {
  // 查找钱包容器
  const wallet = document.querySelector('.gbt-wallet-v2');
  if (!wallet) return;

  // 插入行情表 (在支付宝 banner 之后)
  const banner = wallet.querySelector('.gbt-alipay-banner');
  const tickerHTML = createTickerHTML();
  if (banner) {
    banner.insertAdjacentHTML('afterend', tickerHTML);
  } else {
    const first = wallet.firstElementChild;
    if (first) first.insertAdjacentHTML('beforebegin', tickerHTML);
  }

  // 启动实时行情
  const ticker = new RealtimeTicker();
  ticker.onChange(updateTickerUI);
  ticker.start();
}

// 自动注入
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectTickerIntoTarget);
} else {
  setTimeout(injectTickerIntoTarget, 500);
}

export { RealtimeTicker, TICKER_CONFIG, injectTickerIntoTarget };
