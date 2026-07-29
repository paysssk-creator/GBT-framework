/* ═══════════════════════════════════════════════════════════
   GBT 钱包组件 v2.0 — 资金账户 + 余额宝分离
   对标支付宝设计
   ═══════════════════════════════════════════════════════════ */

(function(global) {
  'use strict';

  const API_BASE = '/api/wallet';

  class GBTWalletEmbed {
    constructor(options = {}) {
      this.userId = options.userId || 'anonymous';
      this.token = options.token || '';
      this.theme = options.theme || 'dark';
      this.container = null;
      this.data = null;
      this._pollTimer = null;
      this._activeTab = 'capital'; // 'capital' | 'yuebao'
    }

    mount(selector) {
      this.container = typeof selector === 'string' ? document.querySelector(selector) : selector;
      if (!this.container) throw new Error('Container not found');
      this._render();
      this._fetchData();
      this._startPolling();
    }

    _render() {
      const el = this.container;
      el.innerHTML = `
        <div class="gbt-wallet-v2" style="
          font-family: Inter, system-ui, sans-serif;
          color: var(--fg, #f5f5f7);
          max-width: 420px;
          margin: 0 auto;
        ">
          <!-- ═══ 总资产卡片 ═══ -->
          <div class="gbt-total-card" style="
            background: linear-gradient(135deg, #0a0a12 0%, #111118 100%);
            border: 1px solid var(--border, rgba(255,255,255,.06));
            border-radius: 18px;
            padding: 24px;
            margin-bottom: 16px;
            text-align: center;
          ">
            <div style="font-size: 12px; color: var(--dim, #86868b); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">
              总资产 (美元)
            </div>
            <div class="gbt-total-assets" style="
              font-size: 40px;
              font-weight: 800;
              background: linear-gradient(135deg, #ff6b35, #ff9a56);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
            ">$0.00</div>
            <div style="display: flex; justify-content: center; gap: 20px; margin-top: 12px; font-size: 13px;">
              <div>
                <span style="color: var(--dim)">资金账户 </span>
                <span class="gbt-balance-val" style="font-weight: 600;">$0.00</span>
              </div>
              <div>
                <span style="color: var(--dim)">余额宝 </span>
                <span class="gbt-yuebao-val" style="font-weight: 600; color: #ff9a56;">$0.00</span>
              </div>
            </div>
            <div style="font-size: 11px; color: var(--dim); margin-top: 8px;">
              🔒 独立资金池 · 余额隔离 · 余额为0无法操作
            </div>
          </div>

          <!-- Alipay onramp banner -->
          <div class="gbt-alipay-banner" style="
            background: linear-gradient(135deg, rgba(22,119,255,.1), rgba(64,150,255,.05));
            border: 1px solid rgba(22,119,255,.2); border-radius: 12px;
            padding: 14px 18px; margin-bottom: 16px;
            display: flex; align-items: center; justify-content: space-between;
          ">
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="font-size:24px;">🔵</span>
              <div>
                <div style="font-size:13px;font-weight:600;">支付宝购买数字币</div>
                <div style="font-size:10px;color:var(--dim);">法币入金 · 秒到平台钱包</div>
              </div>
            </div>
            <a href="/onramp.html" class="gbt-alipay-btn" style="
              padding: 10px 20px; background: #1677FF; color: #fff;
              border-radius: 20px; font-size: 13px; font-weight: 600;
              text-decoration: none; white-space: nowrap;
              transition: all .2s;
            ">立即购买</a>
          </div>

          <!-- ═══ GBT 虚拟卡 ═══ -->
          <div class="gbt-card-section" style="
            background: linear-gradient(135deg, #1a1a2e 0%, #0d0d1a 100%);
            border: 1px solid rgba(99,91,255,.2);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            position: relative;
            overflow: hidden;
          ">
            <!-- 卡面背景装饰 -->
            <div style="position:absolute;top:-30px;right:-30px;width:120px;height:120px;border-radius:50%;background:rgba(99,91,255,.06);"></div>
            <div style="position:absolute;bottom:-20px;left:-20px;width:80px;height:80px;border-radius:50%;background:rgba(255,107,53,.06);"></div>

            <div style="position:relative;z-index:1;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <div style="font-size:14px;font-weight:700;display:flex;align-items:center;gap:8px;">
                  <span style="font-size:20px;">💳</span>
                  GBT Card
                  <span style="font-size:10px;background:rgba(99,91,255,.2);color:#a78bfa;padding:2px 8px;border-radius:8px;">Visa</span>
                </div>
                <span style="font-size:20px;opacity:.3;">⋯⋯ ⋯⋯ ⋯⋯ <span class="gbt-card-last4">4242</span></span>
              </div>

              <!-- 卡面 -->
              <div class="gbt-card-face" style="
                background: linear-gradient(135deg, #1a1a2e, #2d2d4a, #1a1a2e);
                border-radius: 14px;
                padding: 0;
                height: 200px;
                position: relative;
                margin: 14px 0;
                overflow: hidden;
                border: 1px solid rgba(255,255,255,.08);
              ">
                <!-- 芯片 -->
                <div style="position:absolute;top:24px;left:24px;width:40px;height:32px;background:linear-gradient(135deg,#c9a84c,#e8c56d);border-radius:5px;"></div>
                <!-- NFC -->
                <div style="position:absolute;top:24px;right:24px;width:24px;height:24px;opacity:.6;">
                  <svg viewBox="0 0 24 24" fill="white"><path d="M4 20V4h16v16H4zm2-2h12V6H6v12z"/><path d="M9 16V8l6 4-6 4z"/></svg>
                </div>
                <!-- 卡号 -->
                <div style="position:absolute;bottom:60px;left:24px;font-family:'SF Mono','Fira Code',monospace;font-size:20px;letter-spacing:3px;color:#fff;">
                  <span class="gbt-card-num">4242</span> ···· ···· ····
                </div>
                <!-- 有效期 -->
                <div style="position:absolute;bottom:30px;left:24px;font-size:10px;color:rgba(255,255,255,.5);">
                  <div>VALID THRU</div>
                  <div class="gbt-card-expiry" style="color:#fff;font-size:14px;font-weight:600;">12/29</div>
                </div>
                <!-- 品牌 -->
                <div style="position:absolute;bottom:24px;right:24px;">
                  <div style="font-size:12px;font-weight:800;color:#fff;letter-spacing:1px;">GBT</div>
                  <div style="font-size:9px;color:rgba(255,255,255,.4);">Platform Card</div>
                </div>
              </div>

              <!-- 操作 -->
              <div style="display:flex;gap:8px;margin-bottom:4px;">
                <button class="gbt-card-freeze" style="flex:1;padding:10px;border-radius:8px;border:1px solid var(--border);background:rgba(255,255,255,.03);color:var(--fg);font-size:12px;font-weight:500;cursor:pointer;">🔒 冻结</button>
                <button class="gbt-card-limit" style="flex:1;padding:10px;border-radius:8px;border:1px solid var(--border);background:rgba(255,255,255,.03);color:var(--fg);font-size:12px;font-weight:500;cursor:pointer;">📊 限额</button>
                <button class="gbt-card-txs" style="flex:1;padding:10px;border-radius:8px;border:1px solid var(--border);background:rgba(255,255,255,.03);color:var(--fg);font-size:12px;font-weight:500;cursor:pointer;">📋 账单</button>
              </div>

              <!-- 未开卡时的申请按钮 -->
              <div class="gbt-card-apply" style="text-align:center;padding:20px 0;">
                <div style="font-size:12px;color:var(--dim);margin-bottom:12px;">
                  全球消费 · 实时汇率 · 资金池额度
                </div>
                <button class="gbt-card-apply-btn" style="
                  padding:12px 32px; border:none; border-radius:10px;
                  background: linear-gradient(135deg, #635BFF, #a78bfa);
                  color: #fff; font-size:14px; font-weight:700; cursor:pointer;
                ">💳 申请 GBT Card · $30</button>
                <div style="font-size:10px;color:var(--dim);margin-top:8px;">
                  一次性开卡费 · 从钱包余额扣除 · 虚拟 Visa 卡
                </div>
              </div>
            </div>
          </div>

          <!-- ═══ Tab 切换 ═══ -->
          <div style="display: flex; gap: 0; margin-bottom: 16px; border-radius: 12px; overflow: hidden; border: 1px solid var(--border);">
            <button class="gbt-tab-btn active" data-tab="capital" style="
              flex: 1; padding: 12px; border: none; cursor: pointer;
              background: rgba(255,107,53,.1); color: var(--accent);
              font-size: 14px; font-weight: 600; transition: all .2s;
            ">💳 资金账户</button>
            <button class="gbt-tab-btn" data-tab="yuebao" style="
              flex: 1; padding: 12px; border: none; cursor: pointer;
              background: transparent; color: var(--dim);
              font-size: 14px; font-weight: 600; transition: all .2s;
            ">🏦 余额宝</button>
          </div>

          <!-- ═══ 资金账户面板 ═══ -->
          <div class="gbt-panel gbt-panel-capital" style="
            background: var(--bg2, #08080c);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
          ">
            <div style="font-size: 13px; color: var(--dim); margin-bottom: 8px;">可用余额</div>
            <div class="gbt-capital-balance" style="font-size: 28px; font-weight: 700; margin-bottom: 16px;">$0.00</div>

            <div style="display: flex; gap: 10px; margin-bottom: 16px;">
              <button class="gbt-btn-deposit" style="
                flex: 1; padding: 12px; border-radius: 10px; border: 1px solid var(--border);
                background: rgba(255,255,255,.03); color: var(--fg); font-size: 13px; font-weight: 600; cursor: pointer;
              ">📥 收款</button>
              <button class="gbt-btn-withdraw" style="
                flex: 1; padding: 12px; border-radius: 10px; border: 1px solid var(--border);
                background: rgba(255,255,255,.03); color: var(--fg); font-size: 13px; font-weight: 600; cursor: pointer;
              ">📤 提现</button>
              <button class="gbt-btn-to-yuebao" style="
                flex: 1; padding: 12px; border-radius: 10px; border: 1px solid rgba(255,154,86,.3);
                background: rgba(255,154,86,.08); color: #ff9a56; font-size: 13px; font-weight: 600; cursor: pointer;
              ">🏦 转入余额宝</button>
            </div>

            <!-- 收款面板 -->
            <div class="gbt-deposit-panel" style="display:none; margin-top: 12px;">
              <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 10px; padding: 16px; text-align: center;">
                <div style="font-size: 12px; color: var(--dim); margin-bottom: 8px;">向平台地址转账，资金秒到资金账户</div>
                <div style="display: flex; gap: 6px; justify-content: center; margin-bottom: 12px;">
                  <button class="gbt-net-btn active" data-net="trc20" style="padding:6px 14px;border-radius:20px;border:1px solid var(--accent);background:rgba(255,107,53,.1);color:var(--accent);font-size:11px;cursor:pointer;">TRC20</button>
                  <button class="gbt-net-btn" data-net="erc20" style="padding:6px 14px;border-radius:20px;border:1px solid var(--border);background:transparent;color:var(--dim);font-size:11px;cursor:pointer;">ERC20</button>
                </div>
                <div class="gbt-addr" style="background:rgba(0,0,0,.3);border:1px dashed var(--border);border-radius:8px;padding:10px;font-family:monospace;font-size:11px;color:var(--green);word-break:break-all;cursor:pointer;user-select:all;">加载中...</div>
                <canvas class="gbt-qr" style="width:140px;height:140px;border-radius:8px;background:#fff;padding:6px;margin-top:10px;"></canvas>
                <div style="font-size:10px;color:var(--dim);margin-top:6px;">⚡ 秒到账 · 最低 $1</div>
              </div>
            </div>

            <!-- 提现面板 -->
            <div class="gbt-withdraw-panel" style="display:none; margin-top: 12px;">
              <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 10px; padding: 16px;">
                <div style="font-size: 12px; color: var(--dim); margin-bottom: 12px;">提现到外部钱包</div>
                <input class="gbt-wd-addr" placeholder="外部钱包地址" style="width:100%;padding:10px;background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:8px;color:var(--fg);font-size:13px;margin-bottom:8px;box-sizing:border-box;">
                <div style="display:flex;gap:8px;margin-bottom:8px;">
                  <input class="gbt-wd-amt" type="number" placeholder="金额" min="1" style="flex:1;padding:10px;background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:8px;color:var(--fg);font-size:13px;">
                  <select class="gbt-wd-net" style="padding:10px;background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:8px;color:var(--fg);font-size:13px;"><option value="trc20">TRC20</option><option value="erc20">ERC20</option></select>
                </div>
                <button class="gbt-wd-submit" disabled style="width:100%;padding:12px;background:var(--accent);border:none;border-radius:10px;color:#fff;font-size:14px;font-weight:700;cursor:pointer;opacity:.5;">确认提现</button>
                <div class="gbt-wd-error" style="display:none;color:var(--red);font-size:11px;margin-top:6px;"></div>
              </div>
            </div>
          </div>

          <!-- ═══ 余额宝面板 (默认隐藏) ═══ -->
          <div class="gbt-panel gbt-panel-yuebao" style="
            background: var(--bg2, #08080c);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            display: none;
          ">
            <!-- 余额宝余额 -->
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
              <div>
                <div style="font-size: 12px; color: var(--dim); margin-bottom: 4px;">余额宝余额</div>
                <div class="gbt-yb-balance" style="font-size: 28px; font-weight: 700; color: #ff9a56;">$0.00</div>
              </div>
              <div style="text-align: right;">
                <div style="font-size: 11px; color: var(--dim);">年化收益率</div>
                <div style="font-size: 16px; font-weight: 700; color: #30d158;">3.65%</div>
              </div>
            </div>

            <!-- 收益信息 -->
            <div style="
              display: grid; grid-template-columns: 1fr 1fr 1fr;
              gap: 10px; margin-bottom: 16px;
              padding: 14px; background: rgba(48,209,88,.05);
              border: 1px solid rgba(48,209,88,.1); border-radius: 10px;
            ">
              <div style="text-align: center;">
                <div style="font-size: 10px; color: var(--dim);">累计收益</div>
                <div class="gbt-yb-accrued" style="font-size: 15px; font-weight: 700; color: #30d158;">$0.00</div>
              </div>
              <div style="text-align: center;">
                <div style="font-size: 10px; color: var(--dim);">今日预估</div>
                <div class="gbt-yb-today" style="font-size: 15px; font-weight: 700; color: #30d158;">$0.00</div>
              </div>
              <div style="text-align: center;">
                <div style="font-size: 10px; color: var(--dim);">待确认</div>
                <div class="gbt-yb-pending" style="font-size: 15px; font-weight: 700; color: var(--amber);">$0.00</div>
              </div>
            </div>

            <!-- 转入/转出按钮 -->
            <div style="display: flex; gap: 10px; margin-bottom: 16px;">
              <button class="gbt-yb-transfer-in" style="
                flex: 1; padding: 12px; border-radius: 10px; border: 1px solid rgba(255,154,86,.3);
                background: rgba(255,154,86,.08); color: #ff9a56; font-size: 13px; font-weight: 600; cursor: pointer;
              ">📥 转入</button>
              <button class="gbt-yb-transfer-out" style="
                flex: 1; padding: 12px; border-radius: 10px; border: 1px solid var(--border);
                background: rgba(255,255,255,.03); color: var(--fg); font-size: 13px; font-weight: 600; cursor: pointer;
              ">📤 转出</button>
            </div>

            <!-- 转入弹窗 -->
            <div class="gbt-yb-ti-panel" style="display:none; margin-top: 12px;">
              <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 10px; padding: 16px;">
                <div style="font-size: 12px; color: var(--dim); margin-bottom: 8px;">转入余额宝</div>
                <div style="font-size: 11px; color: var(--dim); margin-bottom: 10px;">
                  T日15:00前转入 → <b style="color:#30d158">T+1计息</b> → T+2显示收益
                </div>
                <input class="gbt-yb-ti-amt" type="number" placeholder="转入金额" min="1" style="width:100%;padding:10px;background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:8px;color:var(--fg);font-size:13px;margin-bottom:8px;box-sizing:border-box;">
                <div style="font-size: 10px; color: var(--dim); margin-bottom: 8px;">
                  资金账户可用: <span class="gbt-yb-ti-avail">$0.00</span>
                </div>
                <button class="gbt-yb-ti-submit" disabled style="width:100%;padding:12px;background:var(--accent);border:none;border-radius:10px;color:#fff;font-size:14px;font-weight:700;cursor:pointer;opacity:.5;">确认转入</button>
                <div class="gbt-yb-ti-error" style="display:none;color:var(--red);font-size:11px;margin-top:6px;"></div>
              </div>
            </div>

            <!-- 转出弹窗 -->
            <div class="gbt-yb-to-panel" style="display:none; margin-top: 12px;">
              <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 10px; padding: 16px;">
                <div style="font-size: 12px; color: var(--dim); margin-bottom: 8px;">从余额宝转出</div>
                <div style="display:flex;gap:8px;margin-bottom:10px;">
                  <button class="gbt-yb-to-mode active" data-mode="fast" style="flex:1;padding:8px;border-radius:8px;border:1px solid var(--accent);background:rgba(255,107,53,.1);color:var(--accent);font-size:11px;cursor:pointer;">⚡ 快速 (即时)</button>
                  <button class="gbt-yb-to-mode" data-mode="normal" style="flex:1;padding:8px;border-radius:8px;border:1px solid var(--border);background:transparent;color:var(--dim);font-size:11px;cursor:pointer;">🕐 普通 (T+1)</button>
                </div>
                <div class="gbt-yb-to-limit" style="font-size:10px;color:var(--dim);margin-bottom:8px;">快速转出单日限额 $10,000</div>
                <input class="gbt-yb-to-amt" type="number" placeholder="转出金额" min="1" style="width:100%;padding:10px;background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:8px;color:var(--fg);font-size:13px;margin-bottom:8px;box-sizing:border-box;">
                <div style="font-size: 10px; color: var(--dim); margin-bottom: 8px;">
                  余额宝可用: <span class="gbt-yb-to-avail">$0.00</span>
                </div>
                <button class="gbt-yb-to-submit" disabled style="width:100%;padding:12px;background:var(--accent);border:none;border-radius:10px;color:#fff;font-size:14px;font-weight:700;cursor:pointer;opacity:.5;">确认转出</button>
                <div class="gbt-yb-to-error" style="display:none;color:var(--red);font-size:11px;margin-top:6px;"></div>
              </div>
            </div>

            <!-- 规则说明 -->
            <div style="font-size: 10px; color: var(--dim); margin-top: 12px; line-height: 1.8;">
              <div style="font-weight:600;color:var(--fg);margin-bottom:4px;">📋 余额宝规则</div>
              <div>· 转入: T日15:00前 → T+1计息 → T+2显示</div>
              <div>· 转出: 快速转出即时到账 (单日$10,000)</div>
              <div>· 收益: 日复利, 每日0点结算</div>
              <div>· 最低: $1起投, 无上限</div>
            </div>
          </div>

          <!-- ═══ 交易记录 ═══ -->
          <div style="margin-top: 16px; background: var(--bg2); border: 1px solid var(--border); border-radius: 14px; padding: 16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
              <span style="font-size:13px;font-weight:600;">交易记录</span>
              <span style="font-size:10px;color:var(--dim);">近30天</span>
            </div>
            <div class="gbt-tx-list" style="max-height:240px;overflow-y:auto;">
              <div style="text-align:center;padding:20px;color:var(--dim);font-size:12px;">暂无交易</div>
            </div>
          </div>
        </div>
      `;

      this._wireTabs();
      this._wireCapitalButtons();
      this._wireYuebaoButtons();
    }

    // ═══ Tab 切换 ═══
    _wireTabs() {
      const self = this;
      this.container.querySelectorAll('.gbt-tab-btn').forEach(btn => {
        btn.onclick = function() {
          const tab = this.dataset.tab;
          self._activeTab = tab;
          self.container.querySelectorAll('.gbt-tab-btn').forEach(b => {
            b.classList.remove('active');
            b.style.background = 'transparent';
            b.style.color = 'var(--dim)';
          });
          this.classList.add('active');
          this.style.background = 'rgba(255,107,53,.1)';
          this.style.color = 'var(--accent)';

          self.container.querySelector('.gbt-panel-capital').style.display = tab === 'capital' ? 'block' : 'none';
          self.container.querySelector('.gbt-panel-yuebao').style.display = tab === 'yuebao' ? 'block' : 'none';
        };
      });
    }

    // ═══ 资金账户按钮 ═══
    _wireCapitalButtons() {
      const el = this.container;
      const self = this;

      // 收款
      el.querySelector('.gbt-btn-deposit').onclick = () => {
        const panel = el.querySelector('.gbt-deposit-panel');
        const wdPanel = el.querySelector('.gbt-withdraw-panel');
        if (wdPanel) wdPanel.style.display = 'none';
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        if (panel.style.display === 'block') self._fetchAddress();
      };

      // 网络切换
      el.querySelectorAll('.gbt-net-btn').forEach(btn => {
        btn.onclick = function() {
          el.querySelectorAll('.gbt-net-btn').forEach(b => {
            b.classList.remove('active');
            b.style.borderColor = 'var(--border)';
            b.style.background = 'transparent';
            b.style.color = 'var(--dim)';
          });
          this.classList.add('active');
          this.style.borderColor = 'var(--accent)';
          this.style.background = 'rgba(255,107,53,.1)';
          this.style.color = 'var(--accent)';
          self._fetchAddress();
        };
      });

      // 提现
      el.querySelector('.gbt-btn-withdraw').onclick = () => {
        const panel = el.querySelector('.gbt-withdraw-panel');
        const dpPanel = el.querySelector('.gbt-deposit-panel');
        if (dpPanel) dpPanel.style.display = 'none';
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
      };

      // 提现验证
      const wdAmt = el.querySelector('.gbt-wd-amt');
      const wdAddr = el.querySelector('.gbt-wd-addr');
      const wdSubmit = el.querySelector('.gbt-wd-submit');
      const wdError = el.querySelector('.gbt-wd-error');

      function validateWd() {
        const amt = parseFloat(wdAmt.value);
        const addr = wdAddr.value.trim();
        const valid = amt > 0 && amt <= (self.data ? self.data.balance : 0) && addr.length > 10;
        wdSubmit.disabled = !valid;
        wdSubmit.style.opacity = valid ? '1' : '.5';
      }
      if (wdAmt) { wdAmt.oninput = validateWd; wdAddr.oninput = validateWd; }

      if (wdSubmit) {
        wdSubmit.onclick = () => {
          if (!validateWd()) return;
          wdSubmit.textContent = '处理中...'; wdSubmit.disabled = true;
          wdError.style.display = 'none';

          fetch(API_BASE + '/withdraw', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token },
            body: JSON.stringify({
              user_id: self.userId,
              amount: parseFloat(wdAmt.value),
              address: wdAddr.value.trim(),
              network: el.querySelector('.gbt-wd-net')?.value || 'trc20',
              coin: 'USDT'
            })
          })
          .then(r => r.json())
          .then(d => {
            if (d.ok) {
              wdSubmit.textContent = '✅ 已提交'; wdSubmit.style.background = 'var(--green)';
              self._fetchData();
              setTimeout(() => { wdSubmit.textContent = '确认提现'; wdSubmit.style.background = 'var(--accent)'; wdAmt.value = ''; wdAddr.value = ''; wdSubmit.disabled = true; wdSubmit.style.opacity = '.5'; }, 3000);
            } else {
              wdError.textContent = d.error; wdError.style.display = 'block';
              wdSubmit.textContent = '确认提现'; wdSubmit.disabled = false;
            }
          })
          .catch(() => { wdError.textContent = '网络错误'; wdError.style.display = 'block'; wdSubmit.textContent = '确认提现'; wdSubmit.disabled = false; });
        };
      }

      // 转入余额宝按钮
      el.querySelector('.gbt-btn-to-yuebao').onclick = () => {
        // 切换到余额宝 tab 并打开转入弹窗
        el.querySelector('.gbt-tab-btn[data-tab="yuebao"]').click();
        setTimeout(() => {
          const tiPanel = el.querySelector('.gbt-yb-ti-panel');
          if (tiPanel) tiPanel.style.display = 'block';
        }, 200);
      };
    }

    // ═══ 余额宝按钮 ═══
    _wireYuebaoButtons() {
      const el = this.container;
      const self = this;

      // 转入弹窗
      el.querySelector('.gbt-yb-transfer-in').onclick = () => {
        const panel = el.querySelector('.gbt-yb-ti-panel');
        const toPanel = el.querySelector('.gbt-yb-to-panel');
        if (toPanel) toPanel.style.display = 'none';
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        if (panel.style.display === 'block' && self.data) {
          el.querySelector('.gbt-yb-ti-avail').textContent = '$' + (self.data.balance || 0).toFixed(2);
        }
      };

      // 转入金额验证
      const tiAmt = el.querySelector('.gbt-yb-ti-amt');
      const tiSubmit = el.querySelector('.gbt-yb-ti-submit');
      const tiError = el.querySelector('.gbt-yb-ti-error');

      if (tiAmt) tiAmt.oninput = () => {
        const amt = parseFloat(tiAmt.value);
        const valid = amt >= 1 && self.data && amt <= (self.data.balance || 0);
        tiSubmit.disabled = !valid;
        tiSubmit.style.opacity = valid ? '1' : '.5';
      };

      if (tiSubmit) {
        tiSubmit.onclick = () => {
          const amt = parseFloat(tiAmt.value);
          if (!amt || amt < 1) return;
          tiSubmit.textContent = '转入中...'; tiSubmit.disabled = true;
          tiError.style.display = 'none';

          fetch(API_BASE + '/yuebao/transfer-in', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token },
            body: JSON.stringify({ user_id: self.userId, amount: amt })
          })
          .then(r => r.json())
          .then(d => {
            if (d.ok) {
              tiSubmit.textContent = '✅ 已转入'; tiSubmit.style.background = 'var(--green)';
              self._fetchData();
              setTimeout(() => { tiSubmit.textContent = '确认转入'; tiSubmit.style.background = 'var(--accent)'; tiAmt.value = ''; tiSubmit.disabled = true; tiSubmit.style.opacity = '.5'; }, 3000);
            } else {
              tiError.textContent = d.error; tiError.style.display = 'block';
              tiSubmit.textContent = '确认转入'; tiSubmit.disabled = false;
            }
          })
          .catch(() => { tiError.textContent = '网络错误'; tiError.style.display = 'block'; tiSubmit.textContent = '确认转入'; tiSubmit.disabled = false; });
        };
      }

      // 转出弹窗
      el.querySelector('.gbt-yb-transfer-out').onclick = () => {
        const panel = el.querySelector('.gbt-yb-to-panel');
        const tiPanel = el.querySelector('.gbt-yb-ti-panel');
        if (tiPanel) tiPanel.style.display = 'none';
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        if (panel.style.display === 'block' && self.data) {
          el.querySelector('.gbt-yb-to-avail').textContent = '$' + ((self.data.yuebao && self.data.yuebao.balance) || 0).toFixed(2);
        }
      };

      // 转出模式切换
      el.querySelectorAll('.gbt-yb-to-mode').forEach(btn => {
        btn.onclick = function() {
          const mode = this.dataset.mode;
          el.querySelectorAll('.gbt-yb-to-mode').forEach(b => {
            b.classList.remove('active');
            b.style.borderColor = 'var(--border)';
            b.style.background = 'transparent';
            b.style.color = 'var(--dim)';
          });
          this.classList.add('active');
          this.style.borderColor = 'var(--accent)';
          this.style.background = 'rgba(255,107,53,.1)';
          this.style.color = 'var(--accent)';
          const limitEl = el.querySelector('.gbt-yb-to-limit');
          if (limitEl) limitEl.textContent = mode === 'fast' ? '快速转出单日限额 $10,000' : '普通转出 T+1 到账，无限额';
          self._ybOutMode = mode;
        };
      });

      // 转出提交
      const toAmt = el.querySelector('.gbt-yb-to-amt');
      const toSubmit = el.querySelector('.gbt-yb-to-submit');
      const toError = el.querySelector('.gbt-yb-to-error');

      if (toAmt) toAmt.oninput = () => {
        const amt = parseFloat(toAmt.value);
        const ybBal = (self.data && self.data.yuebao) ? self.data.yuebao.balance : 0;
        const valid = amt > 0 && amt <= ybBal;
        toSubmit.disabled = !valid;
        toSubmit.style.opacity = valid ? '1' : '.5';
      };

      if (toSubmit) {
        toSubmit.onclick = () => {
          const amt = parseFloat(toAmt.value);
          if (!amt) return;
          const mode = self._ybOutMode || 'fast';
          toSubmit.textContent = '转出中...'; toSubmit.disabled = true;
          toError.style.display = 'none';

          fetch(API_BASE + '/yuebao/transfer-out', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token },
            body: JSON.stringify({ user_id: self.userId, amount: amt, mode })
          })
          .then(r => r.json())
          .then(d => {
            if (d.ok) {
              toSubmit.textContent = '✅ ' + (mode === 'fast' ? '已到账' : '已提交');
              toSubmit.style.background = 'var(--green)';
              self._fetchData();
              setTimeout(() => { toSubmit.textContent = '确认转出'; toSubmit.style.background = 'var(--accent)'; toAmt.value = ''; toSubmit.disabled = true; toSubmit.style.opacity = '.5'; }, 3000);
            } else {
              toError.textContent = d.error; toError.style.display = 'block';
              toSubmit.textContent = '确认转出'; toSubmit.disabled = false;
            }
          })
          .catch(() => { toError.textContent = '网络错误'; toError.style.display = 'block'; toSubmit.textContent = '确认转出'; toSubmit.disabled = false; });
        };
      }
    }

    // ═══ 数据获取 ═══
    _fetchData() {
      const self = this;
      fetch(API_BASE + '/balance?user_id=' + this.userId, {
        headers: { 'Authorization': 'Bearer ' + this.token }
      })
      .then(r => r.json())
      .then(d => {
        if (!d.ok) return;
        self.data = d;
        self._updateUI(d);
      })
      .catch(() => {});
    }

    _updateUI(d) {
      const el = this.container;
      if (!el) return;

      // 总资产
      const totalEl = el.querySelector('.gbt-total-assets');
      if (totalEl) totalEl.textContent = '$' + (d.total_assets || 0).toFixed(2);

      // 资金账户
      const balEl = el.querySelector('.gbt-balance-val');
      if (balEl) balEl.textContent = '$' + (d.balance || 0).toFixed(2);
      const capBal = el.querySelector('.gbt-capital-balance');
      if (capBal) capBal.textContent = '$' + (d.balance || 0).toFixed(2);

      // 余额宝
      const yb = d.yuebao || {};
      const ybEl = el.querySelector('.gbt-yuebao-val');
      if (ybEl) ybEl.textContent = '$' + (yb.balance || 0).toFixed(2);
      const ybBal = el.querySelector('.gbt-yb-balance');
      if (ybBal) ybBal.textContent = '$' + (yb.balance || 0).toFixed(2);
      const ybAcc = el.querySelector('.gbt-yb-accrued');
      if (ybAcc) ybAcc.textContent = '$' + (yb.yield_accrued || 0).toFixed(4);
      const ybToday = el.querySelector('.gbt-yb-today');
      if (ybToday) ybToday.textContent = '$' + (yb.yield_today || 0).toFixed(6);
      const ybPend = el.querySelector('.gbt-yb-pending');
      if (ybPend) ybPend.textContent = '$' + (yb.pending || 0).toFixed(2);

      // 交易记录
      if (d.transactions) {
        this._renderTx(d.transactions);
      }
    }

    _renderTx(txs) {
      const list = this.container.querySelector('.gbt-tx-list');
      if (!list) return;
      if (!txs.length) {
        list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--dim);font-size:12px;">暂无交易</div>';
        return;
      }

      const typeMap = {
        deposit: { icon: '📥', color: 'var(--green)', sign: '+' },
        earning: { icon: '💰', color: 'var(--green)', sign: '+' },
        withdrawal: { icon: '📤', color: 'var(--red)', sign: '-' },
        yuebao_transfer_in: { icon: '🏦', color: '#ff9a56', sign: '→' },
        yuebao_transfer_out: { icon: '💳', color: '#ff9a56', sign: '←' },
        yuebao_confirm: { icon: '✅', color: 'var(--green)', sign: '+' },
        yield_settle: { icon: '📈', color: '#30d158', sign: '+' },
        withdrawal_fee: { icon: '⛽', color: 'var(--dim)', sign: '-' },
      };

      list.innerHTML = txs.slice(0, 30).map(tx => {
        const meta = typeMap[tx.type] || { icon: '•', color: 'var(--fg)', sign: '' };
        return `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.03);">
          <div>
            <span style="margin-right:6px;">${meta.icon}</span>
            <span style="font-size:12px;">${tx.description || tx.type}</span>
            <div style="font-size:9px;color:var(--dim);margin-top:2px;">${(tx.created_at||'').slice(0,16).replace('T',' ')}</div>
          </div>
          <span style="font-weight:600;color:${meta.color};font-size:13px;white-space:nowrap;">${meta.sign}$${tx.amount.toFixed(2)}</span>
        </div>`;
      }).join('');
    }

    _fetchAddress() {
      const el = this.container;
      const net = (el.querySelector('.gbt-net-btn.active') || {}).dataset?.net || 'trc20';
      const addrEl = el.querySelector('.gbt-addr');
      if (addrEl) addrEl.textContent = '加载中...';

      fetch(API_BASE + '/deposit-address?network=' + net + '&coin=USDT', {
        headers: { 'Authorization': 'Bearer ' + this.token }
      })
      .then(r => r.json())
      .then(d => {
        if (d.address && addrEl) {
          addrEl.textContent = d.address;
          addrEl.onclick = () => {
            navigator.clipboard.writeText(d.address).then(() => {
              addrEl.style.borderColor = 'var(--green)';
              setTimeout(() => { addrEl.style.borderColor = 'var(--border)'; }, 1500);
            });
          };
        }
      })
      .catch(() => { if (addrEl) addrEl.textContent = '网络错误'; });
    }

    _startPolling() {
      const self = this;
      this._pollTimer = setInterval(() => self._fetchData(), 15000);
    }

    destroy() {
      if (this._pollTimer) clearInterval(this._pollTimer);
      if (this.container) this.container.innerHTML = '';
    }
  }

  GBTWalletEmbed.mount = (selector, opts) => {
    const w = new GBTWalletEmbed(opts);
    w.mount(selector);
    return w;
  };

  function autoMount() {
    document.querySelectorAll('[data-gbt-wallet]').forEach(el => {
      GBTWalletEmbed.mount(el, {
        userId: el.dataset.gbtWalletUserId || el.dataset.gbtWallet || 'anonymous',
        token: el.dataset.gbtWalletToken || '',
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoMount);
  } else {
    autoMount();
  }

  global.GBTWallet = GBTWalletEmbed;
})(typeof window !== 'undefined' ? window : global);
