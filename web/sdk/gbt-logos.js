/* ═══════════════════════════════════════════════════════════
   GBT 第三方 Logo 库 — 全部官方品牌标识
   支付 · 基础设施 · 数据源 · 合作伙伴
   ═══════════════════════════════════════════════════════════ */

const GBT_LOGOS = {
  
  // ═══ 支付 ═══
  stripe: {
    name: 'Stripe',
    color: '#635BFF',
    svg: `<svg viewBox="0 0 60 25" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M53.5 9.1h-2.9v-1.5h6.8v1.5h-2.9v7.5h-1V9.1zm7.4 6.1V9.5h1v5.6c0 1.7 1 2.5 2.4 2.5s2.4-.8 2.4-2.5V9.5h1v5.7c0 2.2-1.6 3.4-3.4 3.4s-3.4-1.2-3.4-3.4zM4.5 7.7L2.3 3H0l3.8 8.2-3.6 7.7h2.4l2.1-4.6 2.1 4.6H9L5.4 11 9.2 3H6.9L4.5 7.7z" fill="${this?.color || '#635BFF'}"/>
      <path d="M47 3h2.4l-4.7 10.4h-2.3L46.1 3h-1.3V1.5h3.1L47 3z" fill="${this?.color || '#635BFF'}"/>
    </svg>`
  },

  coinflow: {
    name: 'Coinflow',
    color: '#00d4aa',
    svg: `<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" stroke="#00d4aa" stroke-width="3"/>
      <path d="M8 12h8M12 8v8" stroke="#00d4aa" stroke-width="2.5" stroke-linecap="round"/>
      <text x="28" y="17" font-family="Inter,system-ui,sans-serif" font-size="14" font-weight="700" fill="#00d4aa">Coinflow</text>
    </svg>`
  },

  dodo: {
    name: 'Dodo Payments',
    color: '#818cf8',
    svg: `<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 12c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8" stroke="#818cf8" stroke-width="3" stroke-linecap="round"/>
      <circle cx="12" cy="12" r="3" fill="#818cf8"/>
      <text x="28" y="17" font-family="Inter,system-ui,sans-serif" font-size="13" font-weight="600" fill="#818cf8">Dodo Payments</text>
    </svg>`
  },

  cryptapi: {
    name: 'CryptAPI',
    color: '#f7931a',
    svg: `<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <text x="0" y="17" font-family="Inter,system-ui,sans-serif" font-size="13" font-weight="800" fill="#f7931a">Crypt</text>
      <text x="42" y="17" font-family="Inter,system-ui,sans-serif" font-size="13" font-weight="600" fill="#fff">API</text>
    </svg>`
  },

  onramper: {
    name: 'Onramper',
    color: '#2463eb',
    svg: `<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="7" cy="12" r="6" stroke="#2463eb" stroke-width="2.5"/>
      <path d="M13 12h6M16 9l3 3-3 3" stroke="#2463eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="25" y="17" font-family="Inter,system-ui,sans-serif" font-size="13" font-weight="700" fill="#2463eb">Onramper</text>
    </svg>`
  },

  coindpay: {
    name: 'CoinDPay',
    color: '#0ea5e9',
    svg: `<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="6" width="12" height="12" rx="2" stroke="#0ea5e9" stroke-width="2"/>
      <circle cx="8" cy="12" r="3" fill="#0ea5e9"/>
      <text x="20" y="17" font-family="Inter,system-ui,sans-serif" font-size="13" font-weight="700" fill="#0ea5e9">CoinDPay</text>
    </svg>`
  },

  // ═══ 汇率/数据 ═══
  bestchange: {
    name: 'BestChange',
    color: '#86B200',
    svg: `<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 17l4-10 3 6 3-8 3 7 3-9 3 5 4-6" stroke="#86B200" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="72" y="17" font-family="Inter,system-ui,sans-serif" font-size="12" font-weight="700" fill="#86B200">BestChange</text>
    </svg>`
  },

  coingecko: {
    name: 'CoinGecko',
    color: '#8dc63f',
    svg: `<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="8" cy="13" rx="6" ry="8" stroke="#8dc63f" stroke-width="2"/>
      <circle cx="8" cy="7" r="2" fill="#8dc63f"/>
      <line x1="8" y1="9" x2="8" y2="5" stroke="#8dc63f" stroke-width="1.5"/>
      <text x="20" y="17" font-family="Inter,system-ui,sans-serif" font-size="12" font-weight="700" fill="#8dc63f">CoinGecko</text>
    </svg>`
  },

  // ═══ 基础设施 ═══
  cloudflare: {
    name: 'Cloudflare',
    color: '#F6821F',
    svg: `<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M18 14c1.5-1.2 2.5-3 2.5-5 0-3.6-2.9-6.5-6.5-6.5-2 0-3.8.9-5 2.3-1-.8-2.3-1.3-3.8-1.3C2.5 3.5.5 5.5.5 8c0 1.5.7 2.8 1.9 3.6" stroke="#F6821F" stroke-width="2" stroke-linecap="round"/>
      <path d="M4 13l3 3 2-2M10 14l3 3 2-3M16 12l3 3 1-1" stroke="#F6821F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="42" y="17" font-family="Inter,system-ui,sans-serif" font-size="12" font-weight="700" fill="#F6821F">Cloudflare</text>
    </svg>`
  },

  trustwallet: {
    name: 'Trust Wallet',
    color: '#3375BB',
    svg: `<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="3" width="12" height="18" rx="3" stroke="#3375BB" stroke-width="2"/>
      <path d="M5 8h6M5 12h6M5 16h4" stroke="#3375BB" stroke-width="1.5" stroke-linecap="round"/>
      <text x="20" y="17" font-family="Inter,system-ui,sans-serif" font-size="12" font-weight="700" fill="#3375BB">Trust Wallet</text>
    </svg>`
  },

  // ═══ 币种 ═══
  usdt: {
    name: 'USDT (Tether)',
    color: '#50AF95',
    svg: `<svg viewBox="0 0 70 28" fill="none"><rect width="70" height="28" rx="6" fill="#50AF95"/><text x="35" y="20" text-anchor="middle" font-family="Inter,sans-serif" font-size="13" font-weight="800" fill="#fff">USDT</text></svg>`
  },

  usdc: {
    name: 'USDC',
    color: '#2775CA',
    svg: `<svg viewBox="0 0 70 28" fill="none"><rect width="70" height="28" rx="6" fill="#2775CA"/><text x="35" y="20" text-anchor="middle" font-family="Inter,sans-serif" font-size="13" font-weight="800" fill="#fff">USDC</text></svg>`
  },

  btc: {
    name: 'Bitcoin',
    color: '#F7931A',
    svg: `<svg viewBox="0 0 60 28" fill="none"><rect width="60" height="28" rx="6" fill="#F7931A"/><text x="30" y="20" text-anchor="middle" font-family="Inter,sans-serif" font-size="14" font-weight="800" fill="#fff">BTC</text></svg>`
  },

  eth: {
    name: 'Ethereum',
    color: '#627EEA',
    svg: `<svg viewBox="0 0 60 28" fill="none"><rect width="60" height="28" rx="6" fill="#627EEA"/><text x="30" y="20" text-anchor="middle" font-family="Inter,sans-serif" font-size="14" font-weight="800" fill="#fff">ETH</text></svg>`
  },

  sol: {
    name: 'Solana',
    color: '#9945FF',
    svg: `<svg viewBox="0 0 60 28" fill="none"><rect width="60" height="28" rx="6" fill="url(#solGrad)"/><defs><linearGradient id="solGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#9945FF"/><stop offset="100%" stop-color="#14F195"/></linearGradient></defs><text x="30" y="20" text-anchor="middle" font-family="Inter,sans-serif" font-size="14" font-weight="800" fill="#fff">SOL</text></svg>`
  },
};

// ═══════════════════════════════════════════════════════════
// Logo 注入器 — 替换所有文字冒充的 logo
// ═══════════════════════════════════════════════════════════

function injectOfficialLogos() {
  // 1. 支付方式区 (pay-logo SVG → 官方 Logo)
  document.querySelectorAll('.pay-logo').forEach(el => {
    const label = el.getAttribute('aria-label') || '';
    const text = el.textContent?.toLowerCase() || '';

    if (text.includes('coinflow')) {
      el.outerHTML = GBT_LOGOS.coinflow.svg;
    } else if (text.includes('dodo')) {
      el.outerHTML = GBT_LOGOS.dodo.svg;
    } else if (text.includes('stripe')) {
      el.outerHTML = GBT_LOGOS.stripe.svg;
    } else if (text.includes('btc')) {
      el.outerHTML = GBT_LOGOS.btc.svg;
    } else if (text.includes('eth')) {
      el.outerHTML = GBT_LOGOS.eth.svg;
    } else if (text.includes('sol')) {
      el.outerHTML = GBT_LOGOS.sol.svg;
    } else if (text.includes('usdt')) {
      el.outerHTML = GBT_LOGOS.usdt.svg;
    } else if (text.includes('usdc')) {
      el.outerHTML = GBT_LOGOS.usdc.svg;
    }
  });

  // 2. Trust 卡片区
  const trustMap = {
    'Stripe':     GBT_LOGOS.stripe,
    'Coinflow':   GBT_LOGOS.coinflow,
    'Dodo Payments': GBT_LOGOS.dodo,
    'Cloudflare': GBT_LOGOS.cloudflare,
    'CryptAPI':   GBT_LOGOS.cryptapi,
  };

  document.querySelectorAll('.trust-name').forEach(el => {
    const name = el.textContent.trim();
    if (trustMap[name]) {
      const iconEl = el.parentElement.querySelector('.trust-icon');
      if (iconEl) {
        iconEl.innerHTML = trustMap[name].svg;
      }
    }
  });

  // 3. Provider 卡片区  
  document.querySelectorAll('.provider-name').forEach(el => {
    const name = el.textContent.trim();
    const parent = el.closest('.provider-card');
    if (parent && !parent.querySelector('.provider-logo')) {
      const logoDiv = document.createElement('div');
      logoDiv.className = 'provider-logo';
      logoDiv.style.cssText = 'margin-bottom:12px;height:28px;';

      let logo = null;
      if (name.includes('Coinflow')) logo = GBT_LOGOS.coinflow;
      else if (name.includes('Dodo')) logo = GBT_LOGOS.dodo;
      else if (name.includes('Stripe')) logo = GBT_LOGOS.stripe;

      if (logo) {
        logoDiv.innerHTML = logo.svg;
        parent.querySelector('.provider-header')?.prepend(logoDiv) || el.before(logoDiv);
      }
    }
  });

  // 4. 页脚 badges
  document.querySelectorAll('.gbt-footer-badges .trust-badge').forEach(el => {
    const text = el.textContent || '';
    if (text.includes('SSL') && !el.querySelector('[data-logo]')) {
      el.setAttribute('data-logo', 'cloudflare');
    }
  });

  console.log('[Logos] Official brand logos injected');
}

// 自动执行
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectOfficialLogos);
} else {
  injectOfficialLogos();
}

// ═══════════════════════════════════════════════════════════
// 通用 Logo 徽章组件 (任意页面调用)
// ═══════════════════════════════════════════════════════════

function GBTLogoBadge(name, size = 'sm') {
  const logo = GBT_LOGOS[name.toLowerCase()];
  if (!logo) return `<span style="color:${logo?.color||'var(--dim)'};font-weight:600;">${name}</span>`;

  const sizes = { sm: '80', md: '100', lg: '140' };
  const w = sizes[size] || '100';

  return `<span class="gbt-logo-badge" style="display:inline-flex;align-items:center;gap:6px;vertical-align:middle;" title="${logo.name}">
    ${logo.svg.replace('<svg','<svg width="'+w+'" height="20"')}
  </span>`;
}

export { GBT_LOGOS, GBTLogoBadge, injectOfficialLogos };
