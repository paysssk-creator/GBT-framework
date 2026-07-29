/* ══════════════════════════════════════════════
   GBT · Shared Nav + Footer Injector v2.0
   所有页面只需引用此脚本即可获得统一导航和页脚
   ══════════════════════════════════════════════ */
(function() {
  'use strict';

  // ── Injected CSS for nav/footer extensions ──
  const STYLE = `
.gbt-nav-spacer{height:48px}
.gbt-nav-actions{display:flex;gap:8px;align-items:center}
.gbt-nav-dash{color:var(--dim);text-decoration:none;font-size:13px;font-weight:500;margin-left:8px;transition:color .2s}
.gbt-nav-dash:hover{color:var(--fg)}

/* Hamburger */
.gbt-nav-toggle{display:none;flex-direction:column;gap:5px;background:none;border:none;cursor:pointer;padding:6px 4px;z-index:101}
.gbt-nav-toggle span{display:block;width:22px;height:2px;background:var(--fg);border-radius:1px;transition:all .3s cubic-bezier(.16,1,.3,1);transform-origin:center}
.gbt-nav-toggle.open span:nth-child(1){transform:translateY(7px) rotate(45deg)}
.gbt-nav-toggle.open span:nth-child(2){opacity:0;transform:scaleX(0)}
.gbt-nav-toggle.open span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}

/* Mobile nav */
body.nav-open{overflow:hidden}
@media(max-width:768px){
  .gbt-nav-links,.gbt-nav-actions{display:none}
  .gbt-nav-toggle{display:flex}
  .gbt-nav-links.open,.gbt-nav-actions.open{display:flex}
  .gbt-nav-links.open{position:fixed;top:48px;left:0;right:0;background:rgba(0,0,0,.94);backdrop-filter:saturate(180%) blur(30px);-webkit-backdrop-filter:saturate(180%) blur(30px);flex-direction:column;gap:0;padding:8px 0;border-bottom:1px solid var(--border);z-index:99;animation:navSlideIn .25s ease}
  .gbt-nav-links.open a{display:block;padding:14px 24px;font-size:14px;border-bottom:1px solid rgba(255,255,255,.04)}
  .gbt-nav-links.open a:last-child{border-bottom:none}
  .gbt-nav-actions.open{position:fixed;top:48px;left:0;right:0;padding:16px 24px;flex-direction:column;gap:10px;background:rgba(0,0,0,.94);backdrop-filter:saturate(180%) blur(30px);-webkit-backdrop-filter:saturate(180%) blur(30px);border-bottom:1px solid var(--border);z-index:99}
  .gbt-nav-actions.open .btn-sm{width:100%;text-align:center}
  .gbt-nav-actions.open .gbt-nav-dash{text-align:center;margin-left:0;padding:8px 0}
  @keyframes navSlideIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
}

/* Footer brand */
.gbt-footer-brand{display:flex;flex-direction:column;gap:12px}
.gbt-footer-logo{display:flex;align-items:center;gap:8px;font-weight:700;font-size:15px;color:var(--fg)}
.gbt-footer-logo svg{height:22px;width:22px;border-radius:5px}
.gbt-footer-tagline{color:var(--dim);font-size:13px;line-height:1.7;margin:0}
.gbt-footer-stats{display:flex;gap:20px;margin-top:4px}
.gbt-footer-stat strong{display:block;font-size:16px;font-weight:700;color:var(--fg);line-height:1.2}
.gbt-footer-stat span{font-size:10px;color:var(--dim);font-weight:500;letter-spacing:.5px;text-transform:uppercase}
.gbt-footer-social{display:flex;gap:10px;margin-top:6px}
.gbt-social-icon{display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);color:var(--dim);transition:all .25s cubic-bezier(.16,1,.3,1);position:relative}
.gbt-social-icon::after{content:'';position:absolute;inset:-1px;border-radius:9px;opacity:0;transition:opacity .25s ease;pointer-events:none}
.gbt-social-icon:hover{transform:translateY(-2px)}
.gbt-social-icon svg{width:16px;height:16px;position:relative;z-index:1;transition:transform .25s ease}
.gbt-social-icon:hover svg{transform:scale(1.1)}
.gbt-social-icon.gh:hover{color:#f0f6fc;background:rgba(240,246,252,.12);border-color:rgba(240,246,252,.25);box-shadow:0 0 18px rgba(240,246,252,.1)}
.gbt-social-icon.tw:hover{color:#1d9bf0;background:rgba(29,155,240,.12);border-color:rgba(29,155,240,.25);box-shadow:0 0 18px rgba(29,155,240,.1)}
.gbt-social-icon.dc:hover{color:#5865f2;background:rgba(88,101,242,.12);border-color:rgba(88,101,242,.25);box-shadow:0 0 18px rgba(88,101,242,.1)}
.gbt-social-icon.li:hover{color:#0a66c2;background:rgba(10,102,194,.12);border-color:rgba(10,102,194,.25);box-shadow:0 0 18px rgba(10,102,194,.1)}

/* Trust badge checkmark */
.trust-badge{display:inline-flex;align-items:center;gap:5px}
.trust-badge svg{width:12px;height:12px;flex-shrink:0}
.trust-badge svg path{stroke-dasharray:18;stroke-dashoffset:18;transition:stroke-dashoffset .4s ease}
.trust-badge.revealed svg path{stroke-dashoffset:0}

/* Footer responsive */
@media(max-width:480px){
  .gbt-footer-stats{flex-wrap:wrap;gap:16px}
  .gbt-footer-social{gap:8px}
  .gbt-footer-badges{gap:8px}
}

/* Scroll progress bar */
.gbt-scroll-progress{position:fixed;top:0;left:0;height:2px;background:linear-gradient(90deg,var(--accent),var(--teal));z-index:200;width:0;transition:width .1s linear;border-radius:0 2px 2px 0}

/* Notification badge */
.gbt-nav-links a{position:relative}
.gbt-badge{position:absolute;top:-6px;right:-12px;min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:var(--accent);color:#fff;font-size:10px;font-weight:700;line-height:18px;text-align:center;letter-spacing:0;display:none;box-shadow:0 2px 8px rgba(255,107,53,.35)}
.gbt-badge.show{display:block;animation:badgePopIn .3s cubic-bezier(.16,1,.3,1)}
@keyframes badgePopIn{0%{transform:scale(0);opacity:0}60%{transform:scale(1.2)}100%{transform:scale(1);opacity:1}}

/* Hamburger backdrop overlay */
.gbt-nav-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.5);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);z-index:98;opacity:0;pointer-events:none;transition:opacity .3s ease}
.gbt-nav-backdrop.open{opacity:1;pointer-events:auto}

/* Language switcher */
.gbt-lang-btn{display:flex;align-items:center;gap:4px;background:none;border:1px solid transparent;color:var(--dim);font-size:12px;font-weight:500;cursor:pointer;padding:4px 8px;border-radius:6px;transition:all .2s;position:relative}
.gbt-lang-btn:hover{color:var(--fg);border-color:var(--border);background:rgba(255,255,255,.04)}
.gbt-lang-btn svg{width:14px;height:14px}
.gbt-lang-dropdown{position:absolute;top:100%;right:0;margin-top:6px;background:var(--bg2);border:1px solid var(--border);border-radius:8px;min-width:120px;padding:4px;box-shadow:0 8px 30px rgba(0,0,0,.4);opacity:0;transform:translateY(-6px);pointer-events:none;transition:all .2s cubic-bezier(.16,1,.3,1);z-index:102}
.gbt-lang-dropdown.open{opacity:1;transform:translateY(0);pointer-events:auto}
.gbt-lang-dropdown button{display:block;width:100%;text-align:left;padding:8px 12px;background:none;border:none;color:var(--dim);font-size:13px;cursor:pointer;border-radius:4px;transition:all .15s}
.gbt-lang-dropdown button:hover{background:rgba(255,255,255,.06);color:var(--fg)}
.gbt-lang-dropdown button.active{color:var(--accent);background:rgba(255,107,53,.08)}

/* Back to top visibility */
.gbt-back-to-top{opacity:0;transform:translateY(10px);pointer-events:none;transition:all .35s cubic-bezier(.16,1,.3,1)}
.gbt-back-to-top.visible{opacity:1;transform:translateY(0);pointer-events:auto}

@media(max-width:768px){
  .gbt-lang-btn{margin-right:0}
}

section[id]{scroll-margin-top:56px}

/* Global error banner */
.gbt-error-banner{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);max-width:560px;width:calc(100% - 32px);display:flex;align-items:flex-start;gap:12px;padding:14px 16px;background:rgba(22,22,28,.96);border:1px solid var(--border);border-radius:14px;box-shadow:0 12px 40px rgba(0,0,0,.6),0 0 0 1px rgba(255,107,53,.15);z-index:9999;backdrop-filter:saturate(180%) blur(30px);-webkit-backdrop-filter:saturate(180%) blur(30px);animation:errorSlideUp .35s cubic-bezier(.16,1,.3,1);font-size:13px;color:var(--fg);line-height:1.5}
.gbt-error-banner.dismissing{animation:errorSlideDown .3s cubic-bezier(.16,1,.3,1) forwards}
.gbt-error-banner .gbt-error-icon{flex-shrink:0;width:20px;height:20px;display:flex;align-items:center;justify-content:center;background:rgba(255,69,58,.12);border-radius:50%;color:#ff453a;margin-top:2px}
.gbt-error-banner .gbt-error-icon svg{width:12px;height:12px}
.gbt-error-banner .gbt-error-msg{flex:1;min-width:0}
.gbt-error-banner .gbt-error-msg strong{display:block;color:var(--fg);font-weight:600;margin-bottom:2px}
.gbt-error-banner .gbt-error-msg span{color:var(--dim);word-break:break-word}
.gbt-error-banner .gbt-error-actions{display:flex;align-items:center;gap:8px;flex-shrink:0}
.gbt-error-banner .gbt-error-report{font-size:12px;color:var(--accent);text-decoration:none;font-weight:500;white-space:nowrap;transition:opacity .2s}
.gbt-error-banner .gbt-error-report:hover{opacity:.8}
.gbt-error-banner .gbt-error-dismiss{display:flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;border:none;background:rgba(255,255,255,.06);color:var(--dim);cursor:pointer;transition:all .2s;flex-shrink:0}
.gbt-error-banner .gbt-error-dismiss:hover{background:rgba(255,255,255,.12);color:var(--fg)}
.gbt-error-banner .gbt-error-dismiss svg{width:12px;height:12px}
.gbt-error-count{display:inline-flex;align-items:center;justify-content:center;min-width:18px;height:18px;padding:0 4px;border-radius:9px;background:rgba(255,69,58,.15);color:#ff453a;font-size:10px;font-weight:700;margin-left:6px;flex-shrink:0}
@keyframes errorSlideUp{from{opacity:0;transform:translateX(-50%) translateY(16px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
@keyframes errorSlideDown{from{opacity:1;transform:translateX(-50%) translateY(0)}to{opacity:0;transform:translateX(-50%) translateY(16px)}}

/* Cookie Consent Banner */
.gbt-cookie-banner{position:fixed;bottom:0;left:0;right:0;background:rgba(12,12,18,.97);border-top:1px solid var(--border);z-index:9998;padding:20px 24px;backdrop-filter:saturate(180%) blur(30px);-webkit-backdrop-filter:saturate(180%) blur(30px);transform:translateY(100%);transition:transform .45s cubic-bezier(.16,1,.3,1);box-shadow:0 -8px 40px rgba(0,0,0,.5)}
.gbt-cookie-banner.show{transform:translateY(0)}
.gbt-cookie-inner{max-width:1100px;margin:0 auto;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.gbt-cookie-text{flex:1;min-width:240px}
.gbt-cookie-text p{margin:0;font-size:13px;color:var(--dim);line-height:1.6}
.gbt-cookie-text a{color:var(--accent);text-decoration:underline;text-underline-offset:2px;font-weight:500}
.gbt-cookie-text a:hover{color:var(--fg)}
.gbt-cookie-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.gbt-cookie-actions .btn-sm{white-space:nowrap}
.gbt-cookie-actions .btn-outline-sm{background:transparent;border:1px solid var(--border);color:var(--fg);padding:8px 16px;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:all .2s;white-space:nowrap}
.gbt-cookie-actions .btn-outline-sm:hover{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.2)}
.gbt-cookie-actions .btn-text-sm{background:none;border:none;color:var(--dim);font-size:12px;cursor:pointer;padding:6px 10px;transition:color .2s;white-space:nowrap}
.gbt-cookie-actions .btn-text-sm:hover{color:var(--fg)}

/* Cookie Customize Panel */
.gbt-cookie-panel{max-width:1100px;margin:12px auto 0;display:none;flex-direction:column;gap:10px;padding-top:14px;border-top:1px solid rgba(255,255,255,.06)}
.gbt-cookie-panel.open{display:flex}
.gbt-cookie-panel .gbt-cookie-option{display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:13px;color:var(--dim)}
.gbt-cookie-panel .gbt-cookie-option strong{color:var(--fg);font-weight:600;display:block;margin-bottom:1px}
.gbt-cookie-panel .gbt-cookie-option span{font-size:12px;color:var(--dim)}
.gbt-cookie-toggle{position:relative;width:44px;height:24px;flex-shrink:0}
.gbt-cookie-toggle input{opacity:0;width:0;height:0}
.gbt-cookie-toggle .gbt-toggle-slider{position:absolute;inset:0;background:rgba(255,255,255,.12);border-radius:12px;cursor:pointer;transition:background .25s ease}
.gbt-cookie-toggle .gbt-toggle-slider::before{content:'';position:absolute;width:18px;height:18px;left:3px;bottom:3px;background:var(--fg);border-radius:50%;transition:transform .25s cubic-bezier(.16,1,.3,1);box-shadow:0 1px 3px rgba(0,0,0,.3)}
.gbt-cookie-toggle input:checked+.gbt-toggle-slider{background:var(--accent)}
.gbt-cookie-toggle input:checked+.gbt-toggle-slider::before{transform:translateX(20px)}
.gbt-cookie-toggle input:disabled+.gbt-toggle-slider{opacity:.5;cursor:not-allowed}
.gbt-cookie-panel-actions{display:flex;gap:8px;justify-content:flex-end;padding-top:4px}

@media(max-width:600px){
  .gbt-cookie-inner{flex-direction:column;align-items:flex-start;gap:14px}
  .gbt-cookie-actions{width:100%;justify-content:flex-end}
  .gbt-cookie-banner{padding:16px 16px}
}
`;

  // ── Inject styles ──
  const styleEl = document.createElement('style');
  styleEl.textContent = STYLE;
  document.head.appendChild(styleEl);

  // ═══════════════════════════════════════
  //  NAV
  // ═══════════════════════════════════════
  const NAV_HTML = `
<div class="gbt-scroll-progress" aria-hidden="true"></div>
<div class="gbt-nav-backdrop" aria-hidden="true"></div>
<nav class="gbt-nav" aria-label="Main navigation"><div class="gbt-nav-inner">
  <a href="/" class="gbt-nav-brand" aria-label="GBT home">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" aria-hidden="true">
      <defs>
        <radialGradient id="gn" cx="50%" cy="40%" r="50%">
          <stop offset="0%" stop-color="rgba(255,107,53,0.15)"/>
          <stop offset="100%" stop-color="transparent"/>
        </radialGradient>
        <linearGradient id="bn" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#e8b86d"/><stop offset="100%" stop-color="#b8752a"/>
        </linearGradient>
      </defs>
      <rect width="512" height="512" rx="80" fill="#0a0a12"/>
      <rect width="512" height="512" rx="80" fill="url(#gn)"/>
      <ellipse cx="256" cy="190" rx="110" ry="85" fill="url(#bn)" opacity=".9"/>
      <ellipse cx="218" cy="178" rx="18" ry="20" fill="#1a1a2e"/>
      <ellipse cx="294" cy="178" rx="18" ry="20" fill="#1a1a2e"/>
      <circle cx="226" cy="172" r="6" fill="#fff"/>
      <circle cx="302" cy="172" r="6" fill="#fff"/>
      <path d="M225 205 Q256 230 287 205" stroke="#1a1a2e" stroke-width="4" fill="none" stroke-linecap="round"/>
    </svg>
    GBT
  </a>
  <div class="gbt-nav-links">
    <a href="/stack.html">Tech</a>
    <a href="/#market">Market</a>
    <a href="/pricing.html">Pricing</a>
    <a href="/deploy.html">Deploy</a>
    <a href="/help.html">Help</a>
    <a href="/downloads.html" class="gbt-nav-dl">📦 免费下载</a>
  </div>
  <div class="gbt-nav-actions">
    <button class="gbt-lang-btn" aria-label="Switch language" title="Language" aria-expanded="false">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>
      EN
    </button>
    <div class="gbt-lang-dropdown" role="listbox" aria-label="Language selection">
      <button data-lang="en" class="active" role="option" aria-selected="true">English</button>
      <button data-lang="zh" role="option" aria-selected="false">中文</button>
      <button data-lang="es" role="option" aria-selected="false">Español</button>
      <button data-lang="ja" role="option" aria-selected="false">日本語</button>
    </div>
    <a href="/onboard.html" class="btn-sm btn-green">Start Earning</a>
    <a href="/dashboard.html" class="gbt-nav-dash">Dashboard</a>
  </div>
  <button class="gbt-nav-toggle" aria-label="Toggle menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
</div></nav>
<div class="gbt-nav-spacer"></div>`;

  // ═══════════════════════════════════════
  //  FOOTER
  // ═══════════════════════════════════════
  const FOOTER_HTML = `
<footer class="gbt-footer"><div class="container">
  <div class="gbt-footer-grid">
    <div class="gbt-footer-brand">
      <div class="gbt-footer-logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" aria-hidden="true">
          <rect width="512" height="512" rx="80" fill="#0a0a12"/>
          <ellipse cx="256" cy="190" rx="100" ry="75" fill="#e8b86d" opacity=".85"/>
          <ellipse cx="218" cy="178" rx="16" ry="18" fill="#1a1a2e"/>
          <ellipse cx="294" cy="178" rx="16" ry="18" fill="#1a1a2e"/>
          <circle cx="224" cy="172" r="5" fill="#fff"/>
          <circle cx="300" cy="172" r="5" fill="#fff"/>
        </svg>
        GBT
      </div>
      <p class="gbt-footer-tagline">AI-powered project marketplace connecting agencies with elite engineering talent. Built for scale, designed for trust.</p>
      <div class="gbt-footer-stats">
        <div class="gbt-footer-stat"><strong>$2.8M+</strong><span>Paid Out</span></div>
        <div class="gbt-footer-stat"><strong>4,200+</strong><span>Projects</span></div>
        <div class="gbt-footer-stat"><strong>99.9%</strong><span>Uptime</span></div>
      </div>
      <div class="gbt-footer-social">
        <a href="https://github.com/paysssk-creator/GBTxiaotudouV5" aria-label="GitHub" class="gbt-social-icon gh">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        </a>
        <a href="https://x.com/gbtxiaotudou" aria-label="Twitter" class="gbt-social-icon tw">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        </a>
        <a href="https://discord.gg/gbtxiaotudou" aria-label="Discord" class="gbt-social-icon dc">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>
        </a>
        <a href="https://linkedin.com/company/gbtxiaotudou" aria-label="LinkedIn" class="gbt-social-icon li">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
        </a>
      </div>
    </div>
    <div><h5>Resources</h5><a href="/docs/caps_api.html">API Docs</a><a href="/help.html">Help Center</a><a href="/stack.html">Tech Stack</a><a href="/deploy.html">Deploy</a><a href="/downloads.html">📦 免费下载</a><a href="/ads.html">Ad Studio</a></div>
    <div><h5>Company</h5><a href="/settings.html">Settings</a><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a><a href="/refund.html">Refunds</a><a href="/eula.html">EULA</a></div>
  </div>
  <a class="gbt-back-to-top" role="button" aria-label="Back to top" tabindex="0">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="18 15 12 9 6 15"/></svg>
    Back to top
  </a>
  <div class="gbt-footer-bottom">
    <span>&copy; <span id="gbt-copyright-year">2026</span> GBT &middot; AI Open-Source Project Market &middot; Created by \u81ea\u7531\u7684\u98ce</span>
    <div class="gbt-footer-badges">
      <span class="trust-badge reveal" data-tooltip="不满意？30 天内无条件全额退款"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>30-Day Money Back</span>
      <span class="trust-badge reveal" data-tooltip="银行级 AES-256 加密保护所有数据传输"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>SSL Encrypted</span>
      <span class="trust-badge reveal" data-tooltip="支持 190+ 国家/地区本地化支付"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>Global Payouts</span>
      <span class="trust-badge reveal" data-tooltip="PCI DSS Level 1 最高支付安全认证"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>PCI Compliant</span>
      <span class="trust-badge reveal" data-tooltip="全球边缘加速，99.9% 可用性 SLA 保障"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>99.9% Uptime SLA</span>
      <span class="trust-badge reveal" data-tooltip="完全符合欧盟通用数据保护条例"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>GDPR Ready</span>
    </div>    </div>
  </div>
</div></footer>`;

  // ── Inject nav & footer ──
  document.body.insertAdjacentHTML('afterbegin', NAV_HTML);
  document.body.insertAdjacentHTML('beforeend', FOOTER_HTML);

  // ── Inject error banner container ──
  document.body.insertAdjacentHTML('afterbegin', '<div class="gbt-error-banner" hidden aria-live="polite" role="alert"><div class="gbt-error-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div><div class="gbt-error-msg"><strong>Something went wrong</strong><span class="gbt-error-detail"></span></div><div class="gbt-error-actions"><a href="https://github.com/paysssk-creator/GBTxiaotudouV5/issues/new" class="gbt-error-report" target="_blank" rel="noopener">Report issue</a><span class="gbt-error-count" hidden></span><button class="gbt-error-dismiss" aria-label="Dismiss"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></div></div>');

  // ── Inject cookie consent banner ──
  document.body.insertAdjacentHTML('beforeend', '<div class="gbt-cookie-banner" id="gbtCookieBanner" hidden><div class="gbt-cookie-inner"><div class="gbt-cookie-text"><p>We use cookies and similar technologies to enhance your experience, analyze usage, and personalize content. See our <a href="/privacy.html">Privacy Policy</a> for details.</p></div><div class="gbt-cookie-actions"><button class="btn-sm btn-green gbt-cookie-accept-all">Accept All</button><button class="btn-outline-sm gbt-cookie-essential">Essential Only</button><button class="btn-text-sm gbt-cookie-customize">Customize</button></div></div><div class="gbt-cookie-panel" id="gbtCookiePanel"><div class="gbt-cookie-option"><div><strong>Analytics Cookies</strong><span>Help us understand how visitors interact with our site.</span></div><label class="gbt-cookie-toggle"><input type="checkbox" id="gbtCookieAnalytics" checked><span class="gbt-toggle-slider"></span></label></div><div class="gbt-cookie-option"><div><strong>Marketing Cookies</strong><span>Used to deliver relevant ads and measure campaign performance.</span></div><label class="gbt-cookie-toggle"><input type="checkbox" id="gbtCookieMarketing" checked><span class="gbt-toggle-slider"></span></label></div><div class="gbt-cookie-option"><div><strong>Essential Cookies</strong><span>Required for core functionality. Cannot be disabled.</span></div><label class="gbt-cookie-toggle"><input type="checkbox" id="gbtCookieEssential" checked disabled><span class="gbt-toggle-slider"></span></label></div><div class="gbt-cookie-panel-actions"><button class="btn-sm btn-green gbt-cookie-save-custom">Save Preferences</button></div></div></div>');

  // ═══════════════════════════════════════
  //  ACTIVE PAGE HIGHLIGHT
  // ═══════════════════════════════════════
  function updateActiveLink() {
    const path = location.pathname;
    const hash = location.hash;
    // Clear all first
    document.querySelectorAll('.gbt-nav-links a').forEach(a => a.classList.remove('active'));
    document.querySelectorAll('.gbt-nav-links a').forEach(a => {
      const href = a.getAttribute('href');
      const hashIdx = href.indexOf('#');
      const hrefPath = hashIdx >= 0 ? href.substring(0, hashIdx) : href;
      const hrefHash = hashIdx >= 0 ? href.substring(hashIdx) : '';

      // Exact match
      if (hrefPath === path && (!hrefHash || hash === hrefHash)) {
        a.classList.add('active');
      }
      // Home page without hash: highlight Market as default
      if (path === '/' && !hash && href === '/#market') {
        a.classList.add('active');
      }
    });
  }

  updateActiveLink();
  window.addEventListener('hashchange', updateActiveLink);

  // ═══════════════════════════════════════
  //  SCROLL-AWARE NAV + PROGRESS BAR + BACK TO TOP
  // ═══════════════════════════════════════
  const nav = document.querySelector('.gbt-nav');
  const progressBar = document.querySelector('.gbt-scroll-progress');
  const backToTop = document.querySelector('.gbt-back-to-top');
  let ticking = false;
  const updateScroll = () => {
    const scrollY = window.scrollY;
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    nav.classList.toggle('scrolled', scrollY > 20);
    if (progressBar && docH > 0) {
      progressBar.style.width = Math.min((scrollY / docH) * 100, 100) + '%';
    }
    if (backToTop) {
      backToTop.classList.toggle('visible', scrollY > 400);
    }
    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(updateScroll);
      ticking = true;
    }
  }, { passive: true });
  if (window.scrollY > 20) nav.classList.add('scrolled');
  updateScroll();

  // ═══════════════════════════════════════
  //  MOBILE HAMBURGER MENU
  // ═══════════════════════════════════════
  const toggle = document.querySelector('.gbt-nav-toggle');
  const navLinks = document.querySelector('.gbt-nav-links');
  const navActions = document.querySelector('.gbt-nav-actions');
  const backdrop = document.querySelector('.gbt-nav-backdrop');

  function closeMobileMenu() {
    toggle.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    navLinks.classList.remove('open');
    navActions.classList.remove('open');
    document.body.classList.remove('nav-open');
    if (backdrop) backdrop.classList.remove('open');
  }

  if (toggle && navLinks && navActions) {
    toggle.addEventListener('click', () => {
      const isOpen = toggle.classList.toggle('open');
      toggle.setAttribute('aria-expanded', isOpen.toString());
      navLinks.classList.toggle('open', isOpen);
      navActions.classList.toggle('open', isOpen);
      document.body.classList.toggle('nav-open', isOpen);
      if (backdrop) backdrop.classList.toggle('open', isOpen);
    });

    // Close on backdrop click
    if (backdrop) {
      backdrop.addEventListener('click', closeMobileMenu);
    }

    // Close mobile menu on any nav link click
    const allNavLinks = document.querySelectorAll('.gbt-nav-links a, .gbt-nav-actions a');
    allNavLinks.forEach(link => {
      link.addEventListener('click', closeMobileMenu);
    });
  }

  // ═══════════════════════════════════════
  //  BACK TO TOP CLICK
  // ═══════════════════════════════════════
  if (backToTop) {
    backToTop.addEventListener('click', () => { window.scrollTo({ top: 0, behavior: 'smooth' }); });
    backToTop.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }

  // ═══════════════════════════════════════
  //  LANGUAGE SWITCHER
  // ═══════════════════════════════════════
  const langBtn = document.querySelector('.gbt-lang-btn');
  const langDropdown = document.querySelector('.gbt-lang-dropdown');
  if (langBtn && langDropdown) {
    langBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = langDropdown.classList.toggle('open');
      langBtn.setAttribute('aria-expanded', isOpen.toString());
    });
    langDropdown.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        const lang = btn.dataset.lang;
        langDropdown.querySelectorAll('button').forEach(b => {
          b.classList.remove('active');
          b.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
        langBtn.childNodes[langBtn.childNodes.length - 1].textContent = btn.dataset.lang.toUpperCase();
        langDropdown.classList.remove('open');
        langBtn.setAttribute('aria-expanded', 'false');
        // Placeholder: store preference
        try { localStorage.setItem('gbt-lang', lang); } catch (_) {}
      });
    });
    document.addEventListener('click', () => {
      if (langDropdown.classList.contains('open')) {
        langDropdown.classList.remove('open');
        langBtn.setAttribute('aria-expanded', 'false');
      }
    });
    // Restore saved language
    try {
      const saved = localStorage.getItem('gbt-lang');
      if (saved) {
        const target = langDropdown.querySelector('[data-lang="' + saved + '"]');
        if (target) target.click();
      }
    } catch (_) {}
  }

  // ═══════════════════════════════════════
  //  NOTIFICATION BADGE API
  // ═══════════════════════════════════════
  window.GBT = window.GBT || {};
  window.GBT.setBadge = function(linkSelector, count) {
    const link = document.querySelector('.gbt-nav-links a[href="' + linkSelector + '"]');
    if (!link) return;
    let badge = link.querySelector('.gbt-badge');
    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'gbt-badge';
      badge.setAttribute('aria-label', 'Notifications');
      link.appendChild(badge);
    }
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.classList.add('show');
    } else {
      badge.classList.remove('show');
    }
  };
  window.GBT.clearBadge = function(linkSelector) {
    window.GBT.setBadge(linkSelector, 0);
  };

  // ═══════════════════════════════════════
  //  COPYRIGHT YEAR AUTO-UPDATE
  // ═══════════════════════════════════════
  const yearEl = document.getElementById('gbt-copyright-year');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  // ═══════════════════════════════════════
  // ═══════════════════════════════════════
  //  TRUST BADGE SCROLL REVEAL + CHECKMARK
  // ═══════════════════════════════════════
  var footerBadgeObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        var badge = entry.target;
        var delay = (Array.from(badge.parentElement.children).indexOf(badge)) * 70;
        setTimeout(function() {
          badge.style.opacity = '1';
          badge.style.transform = 'translateY(0)';
          badge.classList.add('revealed');
        }, delay);
        footerBadgeObserver.unobserve(badge);
      }
    });
  }, { threshold: 0.5 });

  var footerBadges = document.querySelectorAll('.gbt-footer .trust-badge');
  footerBadges.forEach(function(badge) {
    badge.style.opacity = '0';
    badge.style.transform = 'translateY(6px)';
    badge.style.transition = 'opacity .5s ease, transform .5s ease';
    footerBadgeObserver.observe(badge);
  });

  // ═══════════════════════════════════════
  // ═══════════════════════════════════════
  //  GLOBAL ERROR HANDLING
  // ═══════════════════════════════════════
  const errorBanner = document.querySelector('.gbt-error-banner');
  const errorDetail = errorBanner.querySelector('.gbt-error-detail');
  const errorCount = errorBanner.querySelector('.gbt-error-count');
  const errorDismiss = errorBanner.querySelector('.gbt-error-dismiss');

  let errorQueue = 0;
  let bannerVisible = false;
  let dismissTimer = null;

  function showErrorBanner(message) {
    errorQueue++;

    if (bannerVisible) {
      errorCount.textContent = errorQueue;
      errorCount.hidden = errorQueue <= 1;
      resetDismissTimer();
      return;
    }

    errorDetail.textContent = message;
    errorCount.textContent = errorQueue;
    errorCount.hidden = errorQueue <= 1;
    errorBanner.hidden = false;
    errorBanner.classList.remove('dismissing');
    bannerVisible = true;
    resetDismissTimer();
  }

  function hideErrorBanner() {
    errorBanner.classList.add('dismissing');
    var onEnd = function() {
      errorBanner.removeEventListener('animationend', onEnd);
      errorBanner.hidden = true;
      errorBanner.classList.remove('dismissing');
      bannerVisible = false;
      errorQueue = 0;
    };
    errorBanner.addEventListener('animationend', onEnd);
    clearTimeout(dismissTimer);
  }

  function resetDismissTimer() {
    clearTimeout(dismissTimer);
    dismissTimer = setTimeout(hideErrorBanner, 8000);
  }

  errorDismiss.addEventListener('click', hideErrorBanner);

  window.onerror = function(message, source, lineno, colno, error) {
    var msg = error && error.message ? error.message : String(message);
    showErrorBanner(msg);
  };

  window.addEventListener('unhandledrejection', function(event) {
    var reason = event.reason;
    var msg = reason instanceof Error ? reason.message : String(reason || 'Unhandled Promise rejection');
    showErrorBanner(msg);
  });

  // ═══════════════════════════════════════
  //  COOKIE CONSENT BANNER (GDPR)
  // ═══════════════════════════════════════
  var cookieBanner = document.getElementById('gbtCookieBanner');
  var cookiePanel = document.getElementById('gbtCookiePanel');
  var cookieKey = 'gbt-cookie-pref';

  function getCookiePref() {
    try { return JSON.parse(localStorage.getItem(cookieKey)); } catch (_) { return null; }
  }

  function setCookiePref(pref) {
    try { localStorage.setItem(cookieKey, JSON.stringify(pref)); } catch (_) {}
  }

  function hideCookieBanner() {
    cookieBanner.classList.remove('show');
    cookieBanner.addEventListener('transitionend', function onHide() {
      cookieBanner.removeEventListener('transitionend', onHide);
      cookieBanner.hidden = true;
    });
  }

  function showCookieBanner() {
    cookieBanner.hidden = false;
    // Force reflow then animate
    cookieBanner.offsetHeight;
    cookieBanner.classList.add('show');
  }

  // Check if consent already given
  if (!getCookiePref()) {
    showCookieBanner();

    // Accept All
    cookieBanner.querySelector('.gbt-cookie-accept-all').addEventListener('click', function() {
      setCookiePref({ version: 1, analytics: true, marketing: true, essential: true, ts: Date.now() });
      hideCookieBanner();
    });

    // Essential Only
    cookieBanner.querySelector('.gbt-cookie-essential').addEventListener('click', function() {
      setCookiePref({ version: 1, analytics: false, marketing: false, essential: true, ts: Date.now() });
      hideCookieBanner();
    });

    // Customize toggle
    cookieBanner.querySelector('.gbt-cookie-customize').addEventListener('click', function() {
      cookiePanel.classList.toggle('open');
    });

    // Save custom preferences
    cookieBanner.querySelector('.gbt-cookie-save-custom').addEventListener('click', function() {
      var analyticsEl = document.getElementById('gbtCookieAnalytics');
      var marketingEl = document.getElementById('gbtCookieMarketing');
      var essentialEl = document.getElementById('gbtCookieEssential');
      setCookiePref({
        version: 1,
        analytics: analyticsEl ? analyticsEl.checked : false,
        marketing: marketingEl ? marketingEl.checked : false,
        essential: essentialEl ? essentialEl.checked : true,
        ts: Date.now()
      });
      hideCookieBanner();
    });
  }
})();
