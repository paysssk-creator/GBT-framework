/* ═══════════════════════════════════════════════════
   GBT 企业级折叠系统 — 区块默认收起，点击展开
   ═══════════════════════════════════════════════════ */
(function() {
  'use strict';

  const CSS = `
.gbt-collapse-section{margin-bottom:2px;overflow:hidden}
.gbt-collapse-header{display:flex;align-items:center;justify-content:space-between;padding:20px 28px;background:var(--bg2,#08080c);border:1px solid var(--border,rgba(255,255,255,.06));cursor:pointer;user-select:none;transition:all .25s;position:relative}
.gbt-collapse-header:hover{background:var(--bg3,#111118);border-color:rgba(255,255,255,.1)}
.gbt-collapse-header::after{content:'';position:absolute;bottom:0;left:28px;right:28px;height:1px;background:linear-gradient(90deg,transparent,rgba(255,107,53,.15),transparent);opacity:0;transition:opacity .3s}
.gbt-collapse-section.open .gbt-collapse-header::after{opacity:1}
.gbt-collapse-title{display:flex;align-items:center;gap:14px;font-size:16px;font-weight:700;color:var(--fg)}
.gbt-collapse-icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.gbt-collapse-icon.payments{background:rgba(99,91,255,.12)}.gbt-collapse-icon.market{background:rgba(48,209,88,.12)}.gbt-collapse-icon.agency{background:rgba(255,154,86,.12)}.gbt-collapse-icon.trust{background:rgba(13,148,136,.12)}.gbt-collapse-icon.products{background:rgba(6,182,212,.12)}
.gbt-collapse-meta{display:flex;align-items:center;gap:12px;font-size:12px;color:var(--dim)}
.gbt-collapse-arrow{width:20px;height:20px;transition:transform .35s cubic-bezier(.16,1,.3,1);opacity:.5;flex-shrink:0}
.gbt-collapse-section.open .gbt-collapse-arrow{transform:rotate(180deg);opacity:1}
.gbt-collapse-badge{padding:3px 10px;border-radius:10px;font-size:10px;font-weight:600;letter-spacing:.5px}
.gbt-collapse-badge.active{background:rgba(48,209,88,.12);color:#30d158}
.gbt-collapse-badge.count{background:rgba(255,255,255,.06);color:var(--dim)}
.gbt-collapse-body{max-height:0;overflow:hidden;transition:max-height .5s cubic-bezier(.16,1,.3,1);border-left:1px solid var(--border);border-right:1px solid var(--border);border-bottom:1px solid transparent}
.gbt-collapse-section.open .gbt-collapse-body{max-height:12000px;border-bottom-color:var(--border)}
.gbt-enterprise-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:0}
.gbt-enterprise-stat{text-align:center;padding:24px 16px;position:relative}
.gbt-enterprise-stat::after{content:'';position:absolute;right:0;top:20%;height:60%;width:1px;background:rgba(255,255,255,.06)}
.gbt-enterprise-stat:last-child::after{display:none}
.gbt-enterprise-stat-value{font-size:28px;font-weight:800;letter-spacing:-1px;background:linear-gradient(180deg,#fff,rgba(255,255,255,.7));-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.2}
.gbt-enterprise-stat-label{font-size:11px;color:var(--dim);font-weight:500;text-transform:uppercase;letter-spacing:1px;margin-top:4px}
@media(max-width:768px){.gbt-enterprise-stats{grid-template-columns:repeat(2,1fr)}.gbt-enterprise-stat::after{display:none}.gbt-enterprise-stat{border-bottom:1px solid rgba(255,255,255,.04)}.gbt-collapse-header{padding:16px 20px}.gbt-collapse-title{font-size:14px;gap:10px}.gbt-collapse-icon{width:30px;height:30px;font-size:15px}.gbt-collapse-meta span{display:none}}
@media(max-width:480px){.gbt-enterprise-stat-value{font-size:22px}}
`;

  const styleEl = document.createElement('style');
  styleEl.textContent = CSS;
  document.head.appendChild(styleEl);

  // ═══ 企业统计条 ═══
  function injectEnterpriseStats() {
    const wrapper = document.querySelector('.stats-wrapper');
    if (!wrapper) return;
    const container = wrapper.querySelector('.container');
    if (!container) return;

    container.innerHTML = `
      <div class="gbt-enterprise-stats">
        <div class="gbt-enterprise-stat"><div class="gbt-enterprise-stat-value">$2.8M+</div><div class="gbt-enterprise-stat-label">Paid Out</div></div>
        <div class="gbt-enterprise-stat"><div class="gbt-enterprise-stat-value">4,200+</div><div class="gbt-enterprise-stat-label">Projects</div></div>
        <div class="gbt-enterprise-stat"><div class="gbt-enterprise-stat-value">99.9%</div><div class="gbt-enterprise-stat-label">Uptime</div></div>
        <div class="gbt-enterprise-stat"><div class="gbt-enterprise-stat-value">~30s</div><div class="gbt-enterprise-stat-label">Deploy</div></div>
      </div>`;
    wrapper.style.background = 'linear-gradient(180deg,rgba(255,255,255,.02),transparent)';
    wrapper.style.borderTop = '1px solid rgba(255,255,255,.06)';
    wrapper.style.borderBottom = '1px solid rgba(255,255,255,.06)';
  }

  // ═══ 包装 sections ═══
  function wrapSections() {
    const configs = [
      { id:'payments', icon:'💳', cls:'payments', title:'Payments', sub:'Stripe · Coinflow · CryptAPI · Dodo', badge:'Active', bcls:'active' },
      { id:'market', icon:'📦', cls:'market', title:'Market', sub:'4,200+ open-source projects', badge:'4,200+', bcls:'count' },
      { id:'agency', icon:'🏢', cls:'agency', title:'Agency', sub:'批量部署 · 服务客户 · 被动收入', badge:'', bcls:'' },
      { id:'what-gbt-does', icon:'⚡', cls:'products', title:'Products', sub:'AI 部署 · 验证码 · 安全审计 · 更多', badge:'16+', bcls:'count' },
      { id:'trust', icon:'🛡️', cls:'trust', title:'Trust & Security', sub:'AES-256 · PCI DSS · GDPR · 99.9% SLA', badge:'', bcls:'' },
    ];

    configs.forEach((cfg, i) => {
      const section = document.getElementById(cfg.id);
      if (!section || section._done) return;
      section._done = true;

      const wrapper = document.createElement('div');
      wrapper.className = 'gbt-collapse-section' + (i === 0 ? ' open' : '');

      const header = document.createElement('div');
      header.className = 'gbt-collapse-header';
      header.setAttribute('tabindex','0');
      header.setAttribute('role','button');
      header.setAttribute('aria-expanded', i === 0 ? 'true' : 'false');
      header.innerHTML = `
        <div class="gbt-collapse-title">
          <span class="gbt-collapse-icon ${cfg.cls}">${cfg.icon}</span><span>${cfg.title}</span>
          ${cfg.badge?`<span class="gbt-collapse-badge ${cfg.bcls}">${cfg.badge}</span>`:''}
        </div>
        <div class="gbt-collapse-meta">
          <span>${cfg.sub}</span>
          <svg class="gbt-collapse-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
        </div>`;

      const body = document.createElement('div');
      body.className = 'gbt-collapse-body';
      body.appendChild(section.cloneNode(true));

      wrapper.appendChild(header);
      wrapper.appendChild(body);
      section.replaceWith(wrapper);
    });

    // 点击事件
    document.querySelectorAll('.gbt-collapse-header').forEach(h => {
      if (h._on) return;
      h._on = true;
      h.addEventListener('click', function() {
        const sec = this.closest('.gbt-collapse-section');
        if (!sec) return;
        const wasOpen = sec.classList.contains('open');
        // 手风琴: 关其他的
        document.querySelectorAll('.gbt-collapse-section.open').forEach(s => { if(s!==sec)s.classList.remove('open'); });
        sec.classList.toggle('open', !wasOpen);
        this.setAttribute('aria-expanded', !wasOpen);
      });
      h.addEventListener('keydown', function(e) { if(e.key==='Enter'||e.key===' '){ e.preventDefault(); this.click(); } });
    });
  }

  function init() {
    injectEnterpriseStats();
    wrapSections();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
