/* ══════════════════════════════════════════════
   GBT · AI Concierge Widget v1.0
   Whop-style floating chat assistant
   ══════════════════════════════════════════════ */
(function () {
  'use strict';

  // ── Config ────────────────────────────────────────────────────────────────
  const CONFIG = {
    apiBase: '/api/ai',
    storageKey: 'gbt_ai_conversation',
    maxHistory: 50,
    widgetLabel: 'AI 助手',
    placeholder: '输入消息...',
    typingDelay: 800,
    animateIn: true,
  };

  // ── State ─────────────────────────────────────────────────────────────────
  let isOpen = false;
  let isTyping = false;
  let messages = [];
  let currentPage = window.location.pathname || '/';

  // ── Load conversation from localStorage ───────────────────────────────────
  function loadHistory() {
    try {
      const raw = localStorage.getItem(CONFIG.storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          messages = parsed.slice(-CONFIG.maxHistory);
        }
      }
    } catch (_) {
      messages = [];
    }
  }

  function saveHistory() {
    try {
      localStorage.setItem(
        CONFIG.storageKey,
        JSON.stringify(messages.slice(-CONFIG.maxHistory))
      );
    } catch (_) {
      // storage full or unavailable — silently ignore
    }
  }

  function addMessage(role, content, extra = {}) {
    messages.push({ role, content, ...extra, time: Date.now() });
    saveHistory();
  }

  // ── DOM Construction ─────────────────────────────────────────────────────
  const shadowHost = document.createElement('div');
  shadowHost.id = 'gbt-ai-concierge';
  const shadowRoot = shadowHost.attachShadow({ mode: 'open' });

  const STYLES = `
    :host {
      --gbt-bg: #000;
      --gbt-bg2: #08080c;
      --gbt-bg3: #111118;
      --gbt-fg: #f5f5f7;
      --gbt-dim: #86868b;
      --gbt-accent: #ff6b35;
      --gbt-accent2: #ff9a56;
      --gbt-border: rgba(255,255,255,.06);
      --gbt-border-strong: rgba(255,255,255,.10);
      --gbt-glass: rgba(255,255,255,.03);
      --gbt-glass-hover: rgba(255,255,255,.06);
      --gbt-radius: 16px;
      --gbt-radius-sm: 10px;
      --gbt-radius-lg: 20px;
      --gbt-radius-full: 9999px;
      --gbt-shadow: 0 8px 40px rgba(0,0,0,.5);
      --gbt-font: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', system-ui, sans-serif;
      --gbt-ease: cubic-bezier(.16,1,.3,1);
      font-family: var(--gbt-font);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    /* ── Float Button ─────────────────────── */
    .gbt-fab {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 52px;
      height: 52px;
      border-radius: var(--gbt-radius-full);
      background: var(--gbt-accent);
      color: #fff;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 24px rgba(255,107,53,.35);
      transition: transform .25s var(--gbt-ease), box-shadow .25s var(--gbt-ease);
      z-index: 2147483646;
      -webkit-tap-highlight-color: transparent;
    }
    .gbt-fab:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 32px rgba(255,107,53,.45);
    }
    .gbt-fab:active { transform: scale(.96); }
    .gbt-fab svg { width: 24px; height: 24px; fill: none; stroke: currentColor; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }
    .gbt-fab .icon-close { display: none; }
    .gbt-fab.open .icon-chat { display: none; }
    .gbt-fab.open .icon-close { display: block; }

    /* Pulse dot */
    .gbt-fab::after {
      content: '';
      position: absolute;
      top: 4px;
      right: 4px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #30d158;
      border: 2px solid var(--gbt-accent);
      animation: gbt-pulse 2s ease-in-out infinite;
    }
    @keyframes gbt-pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: .6; transform: scale(1.25); }
    }

    /* ── Panel ──────────────────────────── */
    .gbt-panel {
      position: fixed;
      bottom: 92px;
      right: 24px;
      width: 380px;
      max-width: calc(100vw - 32px);
      height: 560px;
      max-height: calc(100vh - 120px);
      background: var(--gbt-bg2);
      border: 1px solid var(--gbt-border);
      border-radius: var(--gbt-radius-lg);
      box-shadow: var(--gbt-shadow);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      z-index: 2147483645;
      transform-origin: bottom right;
      transition: opacity .25s var(--gbt-ease), transform .25s var(--gbt-ease);
    }
    .gbt-panel:not(.open) {
      opacity: 0;
      transform: translateY(16px) scale(.95);
      pointer-events: none;
    }
    .gbt-panel.open {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }

    /* ── Header ─────────────────────────── */
    .gbt-header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 16px;
      background: var(--gbt-bg3);
      border-bottom: 1px solid var(--gbt-border);
      flex-shrink: 0;
    }
    .gbt-header-avatar {
      width: 36px;
      height: 36px;
      border-radius: var(--gbt-radius-sm);
      background: linear-gradient(135deg, var(--gbt-accent), #ff9a56);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      flex-shrink: 0;
    }
    .gbt-header-info { flex: 1; min-width: 0; }
    .gbt-header-name { font-size: 14px; font-weight: 600; color: var(--gbt-fg); line-height: 1.2; }
    .gbt-header-sub { font-size: 11px; color: var(--gbt-dim); line-height: 1.2; }
    .gbt-header-actions { display: flex; gap: 4px; }
    .gbt-header-btn {
      width: 32px; height: 32px;
      border-radius: var(--gbt-radius-sm);
      background: transparent;
      border: none;
      color: var(--gbt-dim);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: color .2s, background .2s;
      -webkit-tap-highlight-color: transparent;
    }
    .gbt-header-btn:hover { color: var(--gbt-fg); background: var(--gbt-glass-hover); }
    .gbt-header-btn svg { width: 16px; height: 16px; }

    /* ── Messages ───────────────────────── */
    .gbt-messages {
      flex: 1;
      overflow-y: auto;
      padding: 12px 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      scroll-behavior: smooth;
      overscroll-behavior: contain;
    }
    .gbt-messages::-webkit-scrollbar { width: 4px; }
    .gbt-messages::-webkit-scrollbar-track { background: transparent; }
    .gbt-messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,.08); border-radius: 2px; }

    /* Bubbles */
    .gbt-bubble {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: var(--gbt-radius);
      font-size: 13px;
      line-height: 1.6;
      word-break: break-word;
      animation: gbt-bubbleIn .25s var(--gbt-ease);
      white-space: pre-wrap;
    }
    @keyframes gbt-bubbleIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .gbt-bubble.assistant {
      align-self: flex-start;
      background: var(--gbt-glass);
      border: 1px solid var(--gbt-border);
      color: var(--gbt-fg);
      border-bottom-left-radius: 4px;
    }
    .gbt-bubble.user {
      align-self: flex-end;
      background: var(--gbt-accent);
      color: #fff;
      border-bottom-right-radius: 4px;
    }

    /* Typing indicator */
    .gbt-typing {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 8px 14px;
      align-self: flex-start;
      background: var(--gbt-glass);
      border: 1px solid var(--gbt-border);
      border-radius: var(--gbt-radius);
      border-bottom-left-radius: 4px;
    }
    .gbt-typing span {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--gbt-dim);
      animation: gbt-dotBounce 1.4s ease-in-out infinite;
    }
    .gbt-typing span:nth-child(2) { animation-delay: .15s; }
    .gbt-typing span:nth-child(3) { animation-delay: .3s; }
    @keyframes gbt-dotBounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-5px); }
    }

    /* ── Suggestions ────────────────────── */
    .gbt-suggestions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 4px 0 0;
    }
    .gbt-suggestion-btn {
      padding: 6px 12px;
      border-radius: var(--gbt-radius-full);
      background: var(--gbt-glass);
      border: 1px solid var(--gbt-border-strong);
      color: var(--gbt-dim);
      font-size: 12px;
      cursor: pointer;
      font-family: var(--gbt-font);
      transition: all .2s;
      white-space: nowrap;
      -webkit-tap-highlight-color: transparent;
    }
    .gbt-suggestion-btn:hover {
      color: var(--gbt-fg);
      background: var(--gbt-glass-hover);
      border-color: rgba(255,255,255,.18);
    }

    /* ── Actions (cards) ────────────────── */
    .gbt-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 4px 0 0;
    }
    .gbt-action-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: var(--gbt-radius-sm);
      background: var(--gbt-accent);
      color: #fff;
      border: none;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      font-family: var(--gbt-font);
      transition: all .2s;
      -webkit-tap-highlight-color: transparent;
    }
    .gbt-action-btn:hover {
      background: var(--gbt-accent2);
      transform: translateY(-1px);
    }

    /* ── Input Area ─────────────────────── */
    .gbt-input-area {
      display: flex;
      align-items: flex-end;
      gap: 8px;
      padding: 12px 16px;
      border-top: 1px solid var(--gbt-border);
      background: var(--gbt-bg3);
      flex-shrink: 0;
    }
    .gbt-input {
      flex: 1;
      min-height: 38px;
      max-height: 120px;
      padding: 9px 14px;
      border: 1px solid var(--gbt-border-strong);
      border-radius: var(--gbt-radius-sm);
      background: var(--gbt-glass);
      color: var(--gbt-fg);
      font-size: 13px;
      font-family: var(--gbt-font);
      line-height: 1.5;
      resize: none;
      outline: none;
      transition: border-color .2s;
    }
    .gbt-input:focus { border-color: var(--gbt-accent); }
    .gbt-input::placeholder { color: var(--gbt-dim); }
    .gbt-send-btn {
      width: 38px;
      height: 38px;
      border-radius: var(--gbt-radius-sm);
      background: var(--gbt-accent);
      border: none;
      color: #fff;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: all .2s;
      -webkit-tap-highlight-color: transparent;
    }
    .gbt-send-btn:disabled { opacity: .4; cursor: default; }
    .gbt-send-btn:not(:disabled):hover { background: var(--gbt-accent2); }
    .gbt-send-btn svg { width: 18px; height: 18px; }

    /* ── Quick replies below input ──────── */
    .gbt-quick-row {
      display: flex;
      gap: 6px;
      padding: 0 16px 10px;
      flex-wrap: wrap;
      flex-shrink: 0;
    }
    .gbt-quick-chip {
      padding: 5px 12px;
      border-radius: var(--gbt-radius-full);
      background: var(--gbt-glass);
      border: 1px solid var(--gbt-border);
      color: var(--gbt-dim);
      font-size: 11px;
      cursor: pointer;
      font-family: var(--gbt-font);
      transition: all .2s;
      -webkit-tap-highlight-color: transparent;
    }
    .gbt-quick-chip:hover {
      color: var(--gbt-fg);
      background: var(--gbt-glass-hover);
    }

    /* ── Empty state ────────────────────── */
    .gbt-empty {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      padding: 24px;
      text-align: center;
    }
    .gbt-empty-icon {
      width: 56px;
      height: 56px;
      border-radius: var(--gbt-radius);
      background: linear-gradient(135deg, var(--gbt-accent), #ff9a56);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
    }
    .gbt-empty-title { font-size: 15px; font-weight: 600; color: var(--gbt-fg); }
    .gbt-empty-sub { font-size: 12px; color: var(--gbt-dim); line-height: 1.6; }

    /* ── Responsive ─────────────────────── */
    @media (max-width: 420px) {
      .gbt-panel {
        bottom: 0;
        right: 0;
        width: 100%;
        max-width: 100%;
        height: 100%;
        max-height: 100%;
        border-radius: 0;
      }
      .gbt-fab { bottom: 16px; right: 16px; }
      .gbt-panel:not(.open) {
        transform: translateY(40px) scale(.95);
      }
    }

    /* ── Business Wizard Card ───────────── */
    .gbt-wizard-card {
      border: 1px solid var(--gbt-border);
      border-radius: var(--gbt-radius);
      background: var(--gbt-glass);
      padding: 14px;
      margin-top: 4px;
    }
    .gbt-wizard-title { font-size: 13px; font-weight: 600; color: var(--gbt-fg); margin-bottom: 8px; }
    .gbt-wizard-step {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 0;
      border-bottom: 1px solid var(--gbt-border);
      font-size: 12px;
      color: var(--gbt-dim);
    }
    .gbt-wizard-step:last-child { border-bottom: none; }
    .gbt-wizard-check {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      border: 2px solid var(--gbt-border-strong);
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
    }
  `;

  // ── Build DOM ─────────────────────────────────────────────────────────────
  shadowRoot.innerHTML = `<style>${STYLES}</style>${buildHTML()}`;

  function buildHTML() {
    return `
      <button class="gbt-fab" aria-label="AI Assistant" title="GBT AI 助手">
        <svg class="icon-chat" viewBox="0 0 24 24"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/><circle cx="9" cy="10" r="1"/><circle cx="15" cy="10" r="1"/><line x1="9" y1="13" x2="15" y2="13"/></svg>
        <svg class="icon-close" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
      <div class="gbt-panel">
        <div class="gbt-header">
          <div class="gbt-header-avatar">🥔</div>
          <div class="gbt-header-info">
            <div class="gbt-header-name">GBT小土豆 AI</div>
            <div class="gbt-header-sub">智能助手 · 7×24在线</div>
          </div>
          <div class="gbt-header-actions">
            <button class="gbt-header-btn gbt-new-chat" title="新对话">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            </button>
            <button class="gbt-header-btn gbt-close-panel" title="关闭">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
        <div class="gbt-messages"></div>
        <div class="gbt-input-area">
          <textarea class="gbt-input" placeholder="${CONFIG.placeholder}" rows="1"></textarea>
          <button class="gbt-send-btn" title="发送" disabled>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
        <div class="gbt-quick-row">
          <button class="gbt-quick-chip" data-msg="列出项目">📦 列出项目</button>
          <button class="gbt-quick-chip" data-msg="查看收益">💰 查看收益</button>
          <button class="gbt-quick-chip" data-msg="部署项目">🚀 部署项目</button>
          <button class="gbt-quick-chip" data-msg="创建业务">🏪 创建业务</button>
        </div>
      </div>
    `;
  }

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const fab = shadowRoot.querySelector('.gbt-fab');
  const panel = shadowRoot.querySelector('.gbt-panel');
  const msgContainer = shadowRoot.querySelector('.gbt-messages');
  const input = shadowRoot.querySelector('.gbt-input');
  const sendBtn = shadowRoot.querySelector('.gbt-send-btn');
  const closePanelBtn = shadowRoot.querySelector('.gbt-close-panel');
  const newChatBtn = shadowRoot.querySelector('.gbt-new-chat');
  const quickChips = shadowRoot.querySelectorAll('.gbt-quick-chip');

  // ── Render ────────────────────────────────────────────────────────────────
  function scrollToBottom() {
    requestAnimationFrame(() => {
      msgContainer.scrollTop = msgContainer.scrollHeight;
    });
  }

  function renderMessages() {
    if (messages.length === 0) {
      msgContainer.innerHTML = `
        <div class="gbt-empty">
          <div class="gbt-empty-icon">🥔</div>
          <div class="gbt-empty-title">有什么可以帮你的？</div>
          <div class="gbt-empty-sub">我是 GBT小土豆 AI 助手<br>可以帮你部署项目、查看收益、浏览商品</div>
        </div>
      `;
      return;
    }

    let html = '';
    for (const msg of messages) {
      if (msg.role === 'user') {
        html += `<div class="gbt-bubble user">${escapeHTML(msg.content)}</div>`;
      } else if (msg.role === 'assistant') {
        html += `<div class="gbt-bubble assistant">${formatContent(msg.content)}</div>`;
        if (msg.suggestions && msg.suggestions.length) {
          html += '<div class="gbt-suggestions">';
          for (const s of msg.suggestions) {
            html += `<button class="gbt-suggestion-btn" data-msg="${escapeAttr(s)}">${escapeHTML(s)}</button>`;
          }
          html += '</div>';
        }
        if (msg.actions && msg.actions.length) {
          html += '<div class="gbt-actions">';
          for (const a of msg.actions) {
            html += `<button class="gbt-action-btn" data-action="${escapeAttr(a.type)}">${escapeHTML(a.label)}</button>`;
          }
          html += '</div>';
        }
        if (msg.wizard) {
          html += renderWizardCard(msg.wizard);
        }
      }
    }
    msgContainer.innerHTML = html;
    bindDynamicButtons();
    scrollToBottom();
  }

  function renderWizardCard(wizard) {
    let stepsHTML = '';
    for (const step of wizard.steps) {
      stepsHTML += `
        <div class="gbt-wizard-step">
          <div class="gbt-wizard-check"></div>
          <div>
            <strong style="color:var(--gbt-fg)">${escapeHTML(step.title)}</strong>
            <div>${escapeHTML(step.description)}</div>
          </div>
        </div>
      `;
    }
    let tipsHTML = '';
    if (wizard.tips && wizard.tips.length) {
      tipsHTML = wizard.tips.map(t => `<div style="font-size:11px;color:var(--gbt-dim);margin-top:2px;">💡 ${escapeHTML(t)}</div>`).join('');
    }
    return `
      <div class="gbt-wizard-card">
        <div class="gbt-wizard-title">🏗️ ${escapeHTML(wizard.title || '业务创建向导')}</div>
        ${stepsHTML}
        ${wizard.checkout_url ? `<a class="gbt-action-btn" href="${escapeAttr(wizard.checkout_url)}" target="_blank" style="margin-top:10px;text-decoration:none;display:inline-flex;">🚀 前往支付</a>` : ''}
        ${tipsHTML}
      </div>
    `;
  }

  function formatContent(text) {
    // Bold: **text**
    return escapeHTML(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  }

  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function escapeAttr(str) {
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;');
  }

  function bindDynamicButtons() {
    // Suggestion chips in message bubbles
    msgContainer.querySelectorAll('.gbt-suggestion-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const msg = btn.dataset.msg;
        if (msg) sendMessage(msg);
      });
    });

    // Action buttons
    msgContainer.querySelectorAll('.gbt-action-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        // Emit custom event for host page to handle
        shadowHost.dispatchEvent(new CustomEvent('gbt-action', {
          detail: { action },
          bubbles: true,
          composed: true,
        }));

        // Default behaviors
        switch (action) {
          case 'deploy':
            sendMessage('我想部署一个项目');
            break;
          case 'browse':
            sendMessage('列出所有项目');
            break;
          case 'earnings':
            sendMessage('查看我的收益');
            break;
          case 'payment':
            sendMessage('支付帮助');
            break;
        }
      });
    });
  }

  // ── Typing Indicator ──────────────────────────────────────────────────────
  function showTyping() {
    isTyping = true;
    const el = document.createElement('div');
    el.className = 'gbt-typing';
    el.innerHTML = '<span></span><span></span><span></span>';
    el.id = 'gbt-typing-indicator';
    msgContainer.appendChild(el);
    scrollToBottom();
  }

  function hideTyping() {
    isTyping = false;
    const el = msgContainer.querySelector('#gbt-typing-indicator');
    if (el) el.remove();
  }

  // ── API ───────────────────────────────────────────────────────────────────
  async function callAPI(endpoint, body) {
    const res = await fetch(`${CONFIG.apiBase}/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
  }

  async function sendMessage(text) {
    if (!text || isTyping) return;

    // Add user message
    addMessage('user', text);
    renderMessages();

    // Clear input
    input.value = '';
    resizeInput();
    updateSendButton();

    showTyping();

    try {
      // Build API payload — only send recent context to keep payloads small
      const apiMessages = messages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .slice(-20)
        .map(m => ({ role: m.role, content: m.content }));

      const data = await callAPI('chat', {
        messages: apiMessages,
        context: { page: currentPage },
      });

      // Small delay for natural feel
      await new Promise(r => setTimeout(r, CONFIG.typingDelay));
      hideTyping();

      if (data.reply) {
        addMessage('assistant', data.reply.text, {
          suggestions: data.reply.suggestions,
          actions: data.reply.actions,
        });
      }
      renderMessages();
    } catch (err) {
      hideTyping();
      addMessage('assistant', `抱歉，出了点问题：${err.message}。请稍后再试。`, {
        suggestions: ['列出项目', '查看收益', '支付帮助'],
      });
      renderMessages();
    }
  }

  async function createBusiness(type, name, description) {
    showTyping();
    try {
      const data = await callAPI('create-business', { type, name, description });

      await new Promise(r => setTimeout(r, CONFIG.typingDelay));
      hideTyping();

      if (data.message) {
        addMessage('assistant', data.message, {
          wizard: {
            title: `${name || '业务'} 创建向导`,
            steps: data.steps,
            tips: data.tips,
            checkout_url: data.checkout_url,
          },
        });
      }
      renderMessages();
    } catch (err) {
      hideTyping();
      addMessage('assistant', `业务创建失败：${err.message}`, {
        suggestions: ['重试', '联系客服'],
      });
      renderMessages();
    }
  }

  // ── Panel Toggle ──────────────────────────────────────────────────────────
  function openPanel() {
    isOpen = true;
    fab.classList.add('open');
    panel.classList.add('open');
    renderMessages();
    setTimeout(() => input.focus(), 300);
  }

  function closePanel() {
    isOpen = false;
    fab.classList.remove('open');
    panel.classList.remove('open');
  }

  function togglePanel() {
    if (isOpen) closePanel();
    else openPanel();
  }

  // ── Input Handlers ────────────────────────────────────────────────────────
  function resizeInput() {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  }

  function updateSendButton() {
    sendBtn.disabled = !input.value.trim() || isTyping;
  }

  // ── Event Bindings ────────────────────────────────────────────────────────
  fab.addEventListener('click', togglePanel);
  closePanelBtn.addEventListener('click', closePanel);

  newChatBtn.addEventListener('click', () => {
    messages = [];
    saveHistory();
    renderMessages();
    if (msgContainer.querySelector('.gbt-empty') === null) {
      // Force re-render empty state
      renderMessages();
    }
  });

  input.addEventListener('input', () => {
    resizeInput();
    updateSendButton();
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const text = input.value.trim();
      if (text) sendMessage(text);
    }
  });

  sendBtn.addEventListener('click', () => {
    const text = input.value.trim();
    if (text) sendMessage(text);
  });

  // Quick chips
  quickChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const msg = chip.dataset.msg;
      if (msg) {
        if (msg === '创建业务') {
          // Trigger business creation wizard flow
          createBusiness('agency', '我的代理业务', '通过GBT小土豆代理优质开源项目');
        } else {
          sendMessage(msg);
        }
      }
    });
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen) {
      closePanel();
    }
  });

  // ── Public API ────────────────────────────────────────────────────────────
  const api = {
    open: openPanel,
    close: closePanel,
    toggle: togglePanel,
    send: sendMessage,
    createBusiness,
    clearHistory() {
      messages = [];
      saveHistory();
      renderMessages();
    },
    get isOpen() { return isOpen; },
    get messages() { return [...messages]; },
  };

  // ── Init ──────────────────────────────────────────────────────────────────
  loadHistory();
  document.body.appendChild(shadowHost);

  // Expose global
  window.GBTAI = api;

  // Auto-detect page for context
  if (document.querySelector('meta[name="gbt-page"]')) {
    currentPage = document.querySelector('meta[name="gbt-page"]').content;
  }
})();
