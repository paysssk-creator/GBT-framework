/* ══════════════════════════════════════════════
   GBT Analytics v1.0 · Privacy-Compliant
   - Respects Do Not Track / Global Privacy Control
   - Anonymous session ID (localStorage, no PII)
   - Batched sendBeacon to /api/analytics/event
   - GDPR cookie consent banner
   ══════════════════════════════════════════════ */
(function() {
  'use strict';

  // ── Privacy Gates ──────────────────
  if (navigator.doNotTrack === '1' || window.doNotTrack === '1' ||
      navigator.globalPrivacyControl === true) {
    return; // DNT/GPC active — never load
  }

  // ── Storage Keys ───────────────────
  var CONSENT_KEY = 'gbt_analytics_consent';
  var SESSION_KEY = 'gbt_session_id';
  var BATCH_KEY   = 'gbt_event_batch';

  // ── Session ────────────────────────
  var consented = false;
  var sessionId = '';
  try { consented = localStorage.getItem(CONSENT_KEY) === 'true'; } catch(e) {}
  try { sessionId = localStorage.getItem(SESSION_KEY); } catch(e) {}
  if (!sessionId) {
    sessionId = typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : 's' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 11);
    try { localStorage.setItem(SESSION_KEY, sessionId); } catch(e) {}
  }

  // ── Event Batch ────────────────────
  var batch = [];
  try { batch = JSON.parse(localStorage.getItem(BATCH_KEY) || '[]'); } catch(e) { batch = []; }
  if (!Array.isArray(batch)) batch = [];

  var API = '/api/analytics/event';

  function track(event, data) {
    if (!consented) return;
    batch.push({
      e: event,
      d: data || {},
      s: sessionId,
      p: location.pathname,
      r: document.referrer || '',
      t: Date.now(),
      u: location.href
    });
    try { localStorage.setItem(BATCH_KEY, JSON.stringify(batch)); } catch(e) {}
    flush();
  }

  function flush() {
    if (batch.length === 0) return;
    var toSend = batch.splice(0);
    try { localStorage.setItem(BATCH_KEY, JSON.stringify(batch)); } catch(e) {}
    try {
      navigator.sendBeacon(API, new Blob([JSON.stringify(toSend)], { type: 'application/json' }));
    } catch(e) {
      batch = toSend.concat(batch);
      try { localStorage.setItem(BATCH_KEY, JSON.stringify(batch)); } catch(e2) {}
    }
  }

  // Flush on page unload
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') flush();
  });
  window.addEventListener('pagehide', flush);
  window.addEventListener('beforeunload', flush);

  // ── Page View ──────────────────────
  function trackPageView() {
    track('page_view', {
      title: document.title,
      path: location.pathname,
      referrer: document.referrer
    });
  }

  // ── Public API ─────────────────────
  window.gbtAnalytics = {
    track: track,

    pageView: trackPageView,

    paymentStart: function(data) {
      track('payment_start', data);
    },
    paymentComplete: function(data) {
      track('payment_complete', data);
    },
    deployStart: function(data) {
      track('deploy_start', data);
    },
    projectView: function(data) {
      track('project_view', data);
    },
    search: function(data) {
      track('search', data);
    },

    consent: function(granted) {
      consented = !!granted;
      try { localStorage.setItem(CONSENT_KEY, granted ? 'true' : 'false'); } catch(e) {}
      if (granted) trackPageView();
    },

    hasConsented: function() { return consented; },

    sessionId: function() { return sessionId; }
  };

  // ── Auto-track on consent ──────────
  if (consented) {
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      trackPageView();
    } else {
      window.addEventListener('DOMContentLoaded', trackPageView);
    }
  }

  // ── GDPR Cookie Banner ─────────────
  if (!consented) injectBanner();

  function injectBanner() {
    var banner = document.createElement('div');
    banner.id = 'gbt-cookie-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Cookie consent');
    banner.innerHTML =
      '<div class="gbt-cookie-inner">' +
        '<div class="gbt-cookie-body">' +
          '<strong>Cookie 与隐私</strong>' +
          '<p>我们使用匿名分析来改善服务体验。不收集个人身份信息。继续使用即表示同意 <a href="/privacy.html" target="_blank">隐私政策</a>。</p>' +
        '</div>' +
        '<div class="gbt-cookie-actions">' +
          '<button class="gbt-cookie-btn gbt-cookie-accept" autofocus>接受全部</button>' +
          '<button class="gbt-cookie-btn gbt-cookie-essential">仅必要</button>' +
        '</div>' +
      '</div>';

    var style = document.createElement('style');
    style.textContent =
      '#gbt-cookie-banner{' +
        'position:fixed;bottom:0;left:0;right:0;z-index:99999;' +
        'background:rgba(0,0,0,.96);' +
        'backdrop-filter:saturate(180%) blur(24px);-webkit-backdrop-filter:saturate(180%) blur(24px);' +
        'border-top:1px solid rgba(255,255,255,.08);' +
        'padding:18px 24px;' +
        'animation:gbtCookieIn .4s cubic-bezier(.16,1,.3,1)' +
      '}' +
      '@keyframes gbtCookieIn{from{transform:translateY(100%)}to{transform:translateY(0)}}' +
      '@keyframes gbtCookieOut{from{transform:translateY(0);opacity:1}to{transform:translateY(100%);opacity:0}}' +
      '.gbt-cookie-inner{' +
        'max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;' +
        'gap:20px;flex-wrap:wrap' +
      '}' +
      '.gbt-cookie-body strong{' +
        'display:block;color:#f5f5f7;font-size:14px;font-weight:600;margin-bottom:4px' +
      '}' +
      '.gbt-cookie-body p{' +
        'color:#86868b;font-size:12px;line-height:1.55;margin:0;max-width:580px' +
      '}' +
      '.gbt-cookie-body a{' +
        'color:#ff6b35;text-decoration:underline;text-underline-offset:2px' +
      '}' +
      '.gbt-cookie-body a:hover{color:#ff9a56}' +
      '.gbt-cookie-actions{display:flex;gap:8px;flex-shrink:0}' +
      '.gbt-cookie-btn{border:none;padding:9px 22px;border-radius:8px;font-size:13px;font-weight:600;' +
        'cursor:pointer;transition:opacity .2s,transform .15s;font-family:inherit' +
      '}' +
      '.gbt-cookie-btn:hover{opacity:.85;transform:translateY(-1px)}' +
      '.gbt-cookie-accept{background:#ff6b35;color:#fff}' +
      '.gbt-cookie-essential{background:transparent;color:#86868b;border:1px solid rgba(255,255,255,.12)}' +
      '.gbt-cookie-essential:hover{color:#f5f5f7;border-color:rgba(255,255,255,.25)}' +
      '@media(max-width:640px){' +
        '.gbt-cookie-inner{flex-direction:column;align-items:stretch;gap:14px}' +
        '.gbt-cookie-body p{max-width:100%}' +
        '.gbt-cookie-actions{justify-content:flex-end}' +
      '}';

    document.head.appendChild(style);
    document.body.appendChild(banner);

    function dismiss() {
      banner.style.animation = 'gbtCookieOut .3s cubic-bezier(.16,1,.3,1) forwards';
      setTimeout(function() { banner.remove(); }, 320);
    }

    banner.querySelector('.gbt-cookie-accept').addEventListener('click', function() {
      window.gbtAnalytics.consent(true);
      dismiss();
    });
    banner.querySelector('.gbt-cookie-essential').addEventListener('click', function() {
      window.gbtAnalytics.consent(false);
      dismiss();
    });
  }

})();
