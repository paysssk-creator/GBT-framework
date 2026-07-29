/**
 * GBT Wallet — 白标钱包引擎
 * 
 * TP作为底层密钥引擎(不可见)，GBT完全掌控UI和品牌。
 * 用户看到的是GBT钱包，不是TP。
 */
(function() {
  'use strict';
  const API = 'https://gbtxiaotudou.com/api/wallet';
  let _address = null, _ready = false;

  // 内部使用TP SDK获取地址(用户不可见)
  async function _tpGetAddress() {
    try {
      if (window.tronWeb?.ready) {
        return window.tronWeb.defaultAddress.base58;
      }
    } catch(e) { /* TP not available, use stored */ }
    return localStorage.getItem('gbt_wallet_address') || null;
  }

  // ═══ 公开API(用户可见) ═══
  const GBT = {
    get ready() { return _ready; },
    get address() { return _address; },

    // 初始化钱包(内部调TP)
    async init() {
      _address = await _tpGetAddress();
      if (_address) {
        _ready = true;
        localStorage.setItem('gbt_wallet_address', _address);
        return { ok: true, address: _address };
      }
      return { ok: false, error: '钱包初始化失败' };
    },

    // 获取充值地址
    async depositAddress(net='trc20', coin='USDT') {
      const r = await fetch(`${API}/deposit-address?network=${net}&coin=${coin}`).then(r=>r.json());
      return r;
    },

    // 查询余额
    async balance() {
      if (!_address) return { ok: false };
      return fetch(`${API}/balance?user_id=${_address}`).then(r=>r.json());
    },

    // 提现
    async withdraw(amount, toAddr) {
      return fetch(`${API}/withdraw`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ user_id: _address, amount, address: toAddr, network:'trc20', coin:'USDT' })
      }).then(r=>r.json());
    },

    // 内部转账
    async transfer(toUserId, amount) {
      return fetch(`${API}/internal-transfer`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ from_user_id: _address, to_user_id: toUserId, amount })
      }).then(r=>r.json());
    },

    // 余额宝
    yuebao: {
      async info() {
        return fetch(`${API}/balance?user_id=${_address}`).then(r=>r.json());
      },
      async deposit(amount) {
        return fetch(`${API}/yuebao/transfer-in`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ user_id: _address, amount })
        }).then(r=>r.json());
      },
      async withdraw(amount) {
        return fetch(`${API}/yuebao/transfer-out`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ user_id: _address, amount, mode:'fast' })
        }).then(r=>r.json());
      },
      async yield() {
        return fetch(`${API}/yuebao/yield-history?user_id=${_address}`).then(r=>r.json());
      }
    },

    // 平台信息
    async stats() { return fetch(`${API}/pool`).then(r=>r.json()); },
    async health() { return fetch(`${API}/health`).then(r=>r.json()); },
  };

  window.GBT = GBT;
  GBT.init();

// ═══ TP Card 虚拟卡 ══════════════════════════════════════
GBT.card = {
  // 跳转TP Card页面(白标: 用户看到GBT Card)
  open() {
    const url = 'https://card.tokenpocket.pro/?utm_source=gbt&utm_medium=wallet';
    if (typeof window !== 'undefined') window.open(url, '_blank');
    return { ok: true, url, note: 'GBT Card · Powered by TokenPocket · Mastercard' };
  },
  
  // 卡片信息 (通过TP Card API获取, 需要用户授权)
  async info(userToken) {
    if (!userToken) return { ok: false, error: '请先连接TP钱包授权' };
    try {
      const r = await fetch('https://card.tokenpocket.pro/api/card/info', {
        headers: { 'Authorization': `Bearer ${userToken}` }
      }).then(r => r.json());
      return { ok: true, ...r };
    } catch(e) {
      return { ok: false, error: 'TP Card暂不可用' };
    }
  },

  // 支持的功能列表
  features: [
    'Mastercard全球消费',
    'Apple Pay / Google Pay',
    '微信支付 / 支付宝',
    'USDT/USDC链上充值',
    '即时兑换消费',
  ],

  // 费率
  fees: {
    issuance: '$0 (免费开卡)',
    topup: '1% (链上充值)',
    forex: '≤1.5% (跨境消费)',
    atm: '$2.5/笔',
  },
};

// ═══ 钱包底部自动注入卡入口 ═══
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', function() {
    var cardBtn = document.createElement('button');
    cardBtn.className = 'gbt-card-btn';
    cardBtn.innerHTML = '💳 GBT Card';
    cardBtn.title = 'Mastercard虚拟卡 · 全球消费 · Apple Pay/微信/支付宝';
    cardBtn.style.cssText = 'display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:20px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,107,53,.1),rgba(99,102,241,.1));color:#fff;font-size:13px;font-weight:600;cursor:pointer;transition:all .3s ease';
    cardBtn.onmouseover = function() { this.style.borderColor='rgba(255,107,53,.4)'; this.style.boxShadow='0 0 20px rgba(255,107,53,.15)'; };
    cardBtn.onmouseout = function() { this.style.borderColor='rgba(255,255,255,.12)'; this.style.boxShadow='none'; };
    cardBtn.onclick = function() { GBT.card.open(); };
    
    var wallet = document.querySelector('.gbt-wallet, [data-gbt-wallet], #gbt-wallet');
    if (wallet) {
      var header = wallet.querySelector('.gbt-wallet-header, .gbt-wallet-tabs');
      if (header) header.appendChild(cardBtn);
      else wallet.insertBefore(cardBtn, wallet.firstChild);
    }
  });
}
})();

// ═══ 安全底部声明(可嵌入任何钱包页面) ═══
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', function() {
    var footer = document.createElement('div');
    footer.className = 'gbt-security-footer';
    footer.innerHTML = '<div style="text-align:center;padding:16px 20px;font-size:12px;color:rgba(255,255,255,.35);line-height:1.8;border-top:1px solid rgba(255,255,255,.05);margin-top:24px">'
      + '<span style="font-weight:600;color:rgba(255,255,255,.5)">GBT Wallet</span>'
      + ' <span style="color:rgba(255,107,53,.5)">×</span>'
      + ' <span style="font-weight:600;color:rgba(255,255,255,.5)">TokenPocket</span>'
      + ' 联合保障 · 资金安全 · MPC多重签名 · 冷热钱包分离'
      + '<br><span style="font-size:11px;color:rgba(255,255,255,.2)">Powered by MPCH · TRC20 · Cloudflare</span>'
      + '</div>';
    // 自动附加到钱包容器底部
    var wallet = document.querySelector('.gbt-wallet, [data-gbt-wallet], #gbt-wallet');
    if (wallet) { wallet.appendChild(footer); }
  });
}