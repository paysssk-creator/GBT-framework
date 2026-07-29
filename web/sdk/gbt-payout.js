/* ══════════════════════════════════════════════
   GBT Payout Portal v1.0 · Embedded Payout SDK
   Whop-style: Mountable components with
   loading / error / empty states.
   Dark theme design system (uses :root vars).
   ══════════════════════════════════════════════ */
(function() {
  'use strict';

  /* ── Helpers ───────────────────────── */

  var API_BASE = '/api/payout';

  function h(tag, attrs, children) {
    var el = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function(k) {
        if (k === 'className') { el.className = attrs[k]; }
        else if (k === 'style' && typeof attrs[k] === 'object') {
          Object.keys(attrs[k]).forEach(function(s) { el.style[s] = attrs[k][s]; });
        }
        else if (k.slice(0,2) === 'on' && typeof attrs[k] === 'function') {
          el.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
        }
        else if (k === 'html') { el.innerHTML = attrs[k]; }
        else { el.setAttribute(k, attrs[k]); }
      });
    }
    if (children) {
      (Array.isArray(children) ? children : [children]).forEach(function(c) {
        if (typeof c === 'string') el.appendChild(document.createTextNode(c));
        else if (c) el.appendChild(c);
      });
    }
    return el;
  }

  function apiFetch(endpoint, options) {
    var opts = options || {};
    var headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + (opts.token || '')
    };
    return fetch(API_BASE + endpoint, {
      method: opts.method || 'GET',
      headers: headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined
    }).then(function(res) {
      if (!res.ok) {
        return res.json().then(function(err) {
          throw new Error(err.error || err.message || 'Request failed (' + res.status + ')');
        }).catch(function() {
          throw new Error('Request failed (' + res.status + ')');
        });
      }
      return res.json();
    });
  }

  function formatCurrency(cents, currency) {
    var c = currency || 'USD';
    var amt = (cents || 0) / 100;
    try {
      return new Intl.NumberFormat('en-US', { style: 'currency', currency: c }).format(amt);
    } catch(e) {
      return c + ' ' + amt.toFixed(2);
    }
  }

  function formatDate(iso) {
    if (!iso) return '—';
    try {
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
      }).format(new Date(iso));
    } catch(e) { return iso; }
  }

  function statusPill(status) {
    var map = { completed: 'active', pending: 'pending', failed: 'error', processing: 'pending', cancelled: 'idle' };
    var cls = map[status] || 'idle';
    var label = (status || 'unknown').charAt(0).toUpperCase() + (status || 'unknown').slice(1);
    return h('span', { className: 'status-pill ' + cls }, label);
  }

  /* ── Spinner ───────────────────────── */

  function spinner(sm) {
    return h('div', {
      className: 'loading-spinner' + (sm ? ' loading-spinner-sm' : ''),
      style: { margin: '24px auto', display: 'block' }
    });
  }

  /* ── State wrappers ────────────────── */

  function wrapState(state, renderContent) {
    var el = h('div', { className: 'gbt-payout-panel' });
    var inner;
    if (state === 'loading') {
      inner = h('div', { className: 'gbt-payout-state' },
        [spinner(false), h('p', { className: 'text-dim text-sm', style: { textAlign: 'center', marginTop: '12px' } }, 'Loading...')]
      );
    } else if (state === 'error') {
      inner = h('div', { className: 'gbt-payout-state' },
        h('p', { className: 'text-sm', style: { color: 'var(--red)', textAlign: 'center' } },
          state === 'error' && arguments[2] ? arguments[2] : 'Something went wrong. Please try again.'
        )
      );
    } else if (state === 'empty') {
      inner = h('div', { className: 'gbt-payout-state' },
        h('p', { className: 'text-dim text-sm', style: { textAlign: 'center' } },
          arguments[2] || 'No data yet.'
        )
      );
    } else {
      inner = renderContent();
    }
    el.appendChild(inner);
    return el;
  }

  /* ═══════════════════════════════════════════ */
  /*  GTBalance — Earnings balance display      */
  /* ═══════════════════════════════════════════ */

  function GTBalance(opts) {
    this.companyId = opts.companyId;
    this.token = opts.token;
    this.pollInterval = opts.pollInterval || 30000;
    this.el = null;
    this._timer = null;
  }

  GTBalance.prototype.mount = function(target) {
    var self = this;
    this.el = typeof target === 'string' ? document.querySelector(target) : target;
    if (!this.el) throw new Error('GTBalance mount target not found');
    this._render('loading');
    this._fetch();
    if (this.pollInterval > 0) {
      this._timer = setInterval(function() { self._fetch(); }, this.pollInterval);
    }
  };

  GTBalance.prototype.unmount = function() {
    if (this._timer) { clearInterval(this._timer); this._timer = null; }
    if (this.el) { this.el.innerHTML = ''; this.el = null; }
  };

  GTBalance.prototype._fetch = function() {
    var self = this;
    apiFetch('/balance?company_id=' + encodeURIComponent(this.companyId), { token: this.token })
      .then(function(data) { self._render('ok', data); })
      .catch(function(err) { self._render('error', null, err.message); });
  };

  GTBalance.prototype._render = function(state, data) {
    if (!this.el) return;
    this.el.innerHTML = '';

    var content;
    if (state === 'loading') {
      content = wrapState('loading', null);
    } else if (state === 'error') {
      content = wrapState('error', null, data);
    } else {
      var bal = (data && data.balance !== undefined) ? data.balance : 0;
      var pend = (data && data.pending_balance !== undefined) ? data.pending_balance : 0;
      var currency = (data && data.currency) || 'USD';
      content = h('div', { className: 'card card-green gbt-balance-card' },
        h('div', { className: 'gbt-balance-inner' }, [
          h('div', { className: 'gbt-balance-amount', style: { fontSize: 'clamp(24px, 3vw, 36px)', fontWeight: '800', color: 'var(--green)', letterSpacing: '-.03em', lineHeight: '1.2' } },
            formatCurrency(bal + pend, currency)
          ),
          h('div', { className: 'gbt-balance-meta', style: { display: 'flex', gap: '24px', marginTop: '12px', flexWrap: 'wrap' } }, [
            h('div', null, [
              h('span', { className: 'text-xs text-dim', style: { display: 'block' } }, 'Available'),
              h('span', { className: 'text-sm font-semibold', style: { color: 'var(--fg)' } }, formatCurrency(bal, currency))
            ]),
            h('div', null, [
              h('span', { className: 'text-xs text-dim', style: { display: 'block' } }, 'Pending'),
              h('span', { className: 'text-sm font-semibold', style: { color: 'var(--amber)' } }, formatCurrency(pend, currency))
            ])
          ])
        ])
      );
    }
    this.el.appendChild(content);
  };

  /* ═══════════════════════════════════════════ */
  /*  GTWithdrawButton — Withdrawal initiator   */
  /* ═══════════════════════════════════════════ */

  function GTWithdrawButton(opts) {
    this.companyId = opts.companyId;
    this.token = opts.token;
    this.destinationLabel = opts.destinationLabel || 'wallet';
    this.onSuccess = opts.onSuccess || null;
    this.onError = opts.onError || null;
    this.el = null;
    this._mounted = false;
  }

  GTWithdrawButton.prototype.mount = function(target) {
    this.el = typeof target === 'string' ? document.querySelector(target) : target;
    if (!this.el) throw new Error('GTWithdrawButton mount target not found');
    this._mounted = true;
    this._renderIdle();
  };

  GTWithdrawButton.prototype.unmount = function() {
    this._mounted = false;
    if (this.el) { this.el.innerHTML = ''; this.el = null; }
  };

  GTWithdrawButton.prototype._renderIdle = function() {
    if (!this.el) return;
    var self = this;
    this.el.innerHTML = '';

    var wrapper = h('div', { className: 'gbt-withdraw-wrapper' });
    var btn = h('button', {
      className: 'btn btn-green',
      onclick: function() { if (self._mounted) self._openForm(); }
    }, [
      h('span', { style: { display: 'inline-flex', alignItems: 'center', gap: '6px' } }, [
        'Withdraw to ' + this.destinationLabel,
        h('span', { html: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12l7 7 7-7"/></svg>' })
      ])
    ]);
    wrapper.appendChild(btn);
    this.el.appendChild(wrapper);
  };

  GTWithdrawButton.prototype._openForm = function() {
    if (!this.el) return;
    var self = this;
    this.el.innerHTML = '';

    var amtInput = h('input', {
      type: 'number', placeholder: '0.00', min: '1', step: '0.01',
      style: {
        width: '100%', padding: '12px 16px', background: 'var(--bg3)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)', color: 'var(--fg)', fontSize: '15px', fontFamily: 'var(--font)',
        outline: 'none', boxSizing: 'border-box', marginBottom: '12px'
      }
    });
    var destInput = h('input', {
      type: 'text', placeholder: this.destinationLabel + ' address or account',
      style: {
        width: '100%', padding: '12px 16px', background: 'var(--bg3)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)', color: 'var(--fg)', fontSize: '15px', fontFamily: 'var(--font)',
        outline: 'none', boxSizing: 'border-box', marginBottom: '12px'
      }
    });

    var msgEl = h('div', { className: 'gbt-withdraw-msg', style: { marginBottom: '12px', fontSize: '13px' } });

    var submitBtn = h('button', {
      className: 'btn btn-primary btn-sm',
      style: { width: '100%' },
      onclick: function() {
        var amount = parseFloat(amtInput.value);
        if (!amount || amount <= 0) {
          msgEl.style.color = 'var(--red)';
          msgEl.textContent = 'Please enter a valid amount.';
          return;
        }
        if (!destInput.value.trim()) {
          msgEl.style.color = 'var(--red)';
          msgEl.textContent = 'Please enter a destination address.';
          return;
        }
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
        msgEl.style.color = 'var(--dim)';
        msgEl.textContent = '';

        apiFetch('/withdraw', {
          method: 'POST',
          token: self.token,
          body: {
            company_id: self.companyId,
            amount: Math.round(amount * 100),
            destination: destInput.value.trim(),
            destination_label: self.destinationLabel
          }
        }).then(function(data) {
          msgEl.style.color = 'var(--green)';
          msgEl.textContent = 'Withdrawal requested! Status: ' + (data.status || 'pending');
          if (self.onSuccess) self.onSuccess(data);
          setTimeout(function() { if (self._mounted) self._renderIdle(); }, 3000);
        }).catch(function(err) {
          msgEl.style.color = 'var(--red)';
          msgEl.textContent = err.message;
          submitBtn.disabled = false;
          submitBtn.textContent = 'Confirm Withdrawal';
          if (self.onError) self.onError(err);
        });
      }
    }, 'Confirm Withdrawal');

    var cancelBtn = h('button', {
      className: 'btn btn-outline btn-sm',
      style: { width: '100%', marginTop: '8px' },
      onclick: function() { if (self._mounted) self._renderIdle(); }
    }, 'Cancel');

    var form = h('div', { className: 'gbt-withdraw-form card card-bordered card-sm', style: { maxWidth: '420px' } }, [
      h('h4', { style: { marginBottom: '16px' } }, 'Withdraw Funds'),
      h('label', { className: 'text-xs text-dim', style: { display: 'block', marginBottom: '4px' } }, 'Amount'),
      amtInput,
      h('label', { className: 'text-xs text-dim', style: { display: 'block', marginBottom: '4px' } }, 'Destination'),
      destInput,
      msgEl,
      submitBtn,
      cancelBtn
    ]);

    this.el.appendChild(form);
    setTimeout(function() { amtInput.focus(); }, 100);
  };

  /* ═══════════════════════════════════════════ */
  /*  GTWithdrawHistory — Past withdrawals table */
  /* ═══════════════════════════════════════════ */

  function GTWithdrawHistory(opts) {
    this.companyId = opts.companyId;
    this.token = opts.token;
    this.el = null;
  }

  GTWithdrawHistory.prototype.mount = function(target) {
    var self = this;
    this.el = typeof target === 'string' ? document.querySelector(target) : target;
    if (!this.el) throw new Error('GTWithdrawHistory mount target not found');
    this._render('loading');
    apiFetch('/withdrawals?company_id=' + encodeURIComponent(this.companyId), { token: this.token })
      .then(function(data) { self._render('ok', data); })
      .catch(function(err) { self._render('error', null, err.message); });
  };

  GTWithdrawHistory.prototype.unmount = function() {
    if (this.el) { this.el.innerHTML = ''; this.el = null; }
  };

  GTWithdrawHistory.prototype._render = function(state, data) {
    if (!this.el) return;
    this.el.innerHTML = '';

    var content;
    if (state === 'loading') {
      content = wrapState('loading', null);
    } else if (state === 'error') {
      content = wrapState('error', null, data);
    } else {
      var items = (data && data.withdrawals) || [];
      if (!items.length) {
        content = wrapState('empty', null, 'No withdrawals yet.');
      } else {
        content = h('div', { className: 'gbt-history-list' },
          items.map(function(w) {
            return h('div', {
              className: 'gbt-history-row',
              style: {
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '16px 0', borderBottom: '1px solid var(--border)', flexWrap: 'wrap', gap: '8px'
              }
            }, [
              h('div', { style: { minWidth: '140px' } }, [
                h('div', { className: 'text-sm font-semibold' }, formatCurrency(w.amount, w.currency)),
                h('div', { className: 'text-xs text-dim', style: { marginTop: '2px' } }, w.destination_label || 'wallet')
              ]),
              h('div', { style: { display: 'flex', alignItems: 'center', gap: '12px' } }, [
                h('span', { className: 'text-xs text-dim' }, formatDate(w.created_at)),
                statusPill(w.status)
              ])
            ]);
          })
        );
      }
    }
    this.el.appendChild(content);
  };

  /* ═══════════════════════════════════════════ */
  /*  GTKYCForm — Identity verification form    */
  /* ═══════════════════════════════════════════ */

  function GTKYCForm(opts) {
    this.companyId = opts.companyId;
    this.token = opts.token;
    this.onComplete = opts.onComplete || null;
    this.el = null;
    this._mounted = false;
  }

  GTKYCForm.prototype.mount = function(target) {
    this.el = typeof target === 'string' ? document.querySelector(target) : target;
    if (!this.el) throw new Error('GTKYCForm mount target not found');
    this._mounted = true;
    this._checkStatus();
  };

  GTKYCForm.prototype.unmount = function() {
    this._mounted = false;
    if (this.el) { this.el.innerHTML = ''; this.el = null; }
  };

  GTKYCForm.prototype._checkStatus = function() {
    var self = this;
    if (!this.el) return;
    this._renderState('loading');

    apiFetch('/kyc/status?company_id=' + encodeURIComponent(this.companyId), { token: this.token })
      .then(function(data) {
        if (data && data.status === 'verified') {
          self._renderVerified(data);
        } else if (data && data.status === 'pending') {
          self._renderPending(data);
        } else if (data && data.status === 'rejected') {
          self._renderForm(data);
        } else {
          self._renderForm(null);
        }
      })
      .catch(function() {
        // API not ready or error — show form anyway as fallback
        self._renderForm(null);
      });
  };

  GTKYCForm.prototype._renderState = function(state) {
    if (!this.el) return;
    this.el.innerHTML = '';
    if (state === 'loading') {
      this.el.appendChild(wrapState('loading', null));
    }
  };

  GTKYCForm.prototype._renderVerified = function(data) {
    if (!this.el) return;
    this.el.innerHTML = '';
    this.el.appendChild(
      h('div', { className: 'card card-green card-sm', style: { textAlign: 'center' } }, [
        h('div', {
          style: { width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(48,209,88,.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }
        }, h('span', { html: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>' })),
        h('h4', { style: { color: 'var(--green)' } }, 'Identity Verified'),
        h('p', { className: 'text-sm text-dim' }, 'Your KYC verification is complete. You can withdraw funds.')
      ])
    );
  };

  GTKYCForm.prototype._renderPending = function(data) {
    if (!this.el) return;
    this.el.innerHTML = '';
    this.el.appendChild(
      h('div', { className: 'card card-accent card-sm', style: { textAlign: 'center' } }, [
        h('div', {
          style: { width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(255,107,53,.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }
        }, h('span', { html: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' })),
        h('h4', { style: { color: 'var(--accent)' } }, 'Verification Pending'),
        h('p', { className: 'text-sm text-dim' }, 'Your KYC documents are under review. This typically takes 1-3 business days.')
      ])
    );
  };

  GTKYCForm.prototype._renderForm = function(prevData) {
    if (!this.el || !this._mounted) return;
    var self = this;
    this.el.innerHTML = '';

    var msgEl = h('div', { className: 'gbt-kyc-msg', style: { marginBottom: '12px', fontSize: '13px' } });

    var nameInput = h('input', {
      type: 'text', placeholder: 'Full legal name',
      style: formInputStyle(), value: (prevData && prevData.name) || ''
    });
    var countrySelect = h('select', {
      style: formInputStyle()
    }, COUNTRIES.map(function(c) {
      return h('option', { value: c.code, selected: prevData && prevData.country === c.code ? 'selected' : undefined }, c.name);
    }));
    var docTypeSelect = h('select', {
      style: formInputStyle()
    }, [
      h('option', { value: 'passport' }, 'Passport'),
      h('option', { value: 'drivers_license' }, "Driver's License"),
      h('option', { value: 'national_id' }, 'National ID Card'),
      h('option', { value: 'residence_permit' }, 'Residence Permit')
    ]);
    var fileInput = h('input', { type: 'file', accept: 'image/*,.pdf', style: formInputStyle() });
    var fileLabel = h('div', {
      className: 'text-xs text-dim',
      style: { marginTop: '-8px', marginBottom: '12px' }
    }, 'Upload a clear photo or scan of your ID document (JPG, PNG, or PDF, max 10MB)');

    var submitBtn = h('button', {
      className: 'btn btn-primary btn-sm',
      style: { width: '100%' },
      onclick: function() {
        var name = nameInput.value.trim();
        if (!name) { msgEl.style.color = 'var(--red)'; msgEl.textContent = 'Please enter your full legal name.'; return; }
        if (!fileInput.files || !fileInput.files[0]) { msgEl.style.color = 'var(--red)'; msgEl.textContent = 'Please upload an ID document.'; return; }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        msgEl.style.color = 'var(--dim)';
        msgEl.textContent = '';

        var formData = new FormData();
        formData.append('company_id', self.companyId);
        formData.append('name', name);
        formData.append('country', countrySelect.value);
        formData.append('document_type', docTypeSelect.value);
        formData.append('document', fileInput.files[0]);

        fetch(API_BASE + '/kyc/submit', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + self.token },
          body: formData
        }).then(function(res) {
          if (!res.ok) {
            return res.json().then(function(err) { throw new Error(err.error || 'KYC submission failed (' + res.status + ')'); });
          }
          return res.json();
        }).then(function(data) {
          msgEl.style.color = 'var(--green)';
          msgEl.textContent = 'KYC submitted successfully! Your documents are under review.';
          submitBtn.style.display = 'none';
          if (self.onComplete) self.onComplete(data);
          setTimeout(function() { if (self._mounted) self._checkStatus(); }, 3000);
        }).catch(function(err) {
          msgEl.style.color = 'var(--red)';
          msgEl.textContent = err.message;
          submitBtn.disabled = false;
          submitBtn.textContent = 'Submit for Verification';
        });
      }
    }, 'Submit for Verification');

    var rejectNote = prevData && prevData.reason
      ? h('div', {
          className: 'gbt-kyc-reject',
          style: { background: 'rgba(255,71,87,.08)', border: '1px solid rgba(255,71,87,.15)', borderRadius: 'var(--radius-xs)', padding: '12px', marginBottom: '16px' }
        }, [
          h('p', { className: 'text-sm', style: { color: 'var(--red)', fontWeight: '600', marginBottom: '4px' } }, 'Previous submission rejected'),
          h('p', { className: 'text-xs text-dim' }, prevData.reason)
        ])
      : null;

    var form = h('div', { className: 'gbt-kyc-form card card-bordered card-sm', style: { maxWidth: '480px' } }, [
      h('h4', { style: { marginBottom: '4px' } }, 'Identity Verification'),
      h('p', { className: 'text-xs text-dim', style: { marginBottom: '20px' } }, 'We need to verify your identity to enable withdrawals.'),
      rejectNote,
      h('label', { className: 'text-xs text-dim', style: labelStyle() }, 'Full Legal Name'),
      nameInput,
      h('label', { className: 'text-xs text-dim', style: labelStyle() }, 'Country of Residence'),
      countrySelect,
      h('label', { className: 'text-xs text-dim', style: labelStyle() }, 'Document Type'),
      docTypeSelect,
      h('label', { className: 'text-xs text-dim', style: labelStyle() }, 'ID Document'),
      fileInput,
      fileLabel,
      msgEl,
      submitBtn
    ]);

    this.el.appendChild(form);
  };

  /* ── KYC style helpers (not in class scope, used by _renderForm) ── */

  function formInputStyle() {
    return {
      width: '100%', padding: '12px 16px', background: 'var(--bg3)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-sm)', color: 'var(--fg)', fontSize: '15px', fontFamily: 'var(--font)',
      outline: 'none', boxSizing: 'border-box', marginBottom: '12px'
    };
  }

  function labelStyle() {
    return { display: 'block', marginBottom: '4px' };
  }


  /* ── Country list ──────────────────── */

  var COUNTRIES = [
    { code: 'US', name: 'United States' },
    { code: 'GB', name: 'United Kingdom' },
    { code: 'CA', name: 'Canada' },
    { code: 'AU', name: 'Australia' },
    { code: 'DE', name: 'Germany' },
    { code: 'FR', name: 'France' },
    { code: 'JP', name: 'Japan' },
    { code: 'KR', name: 'South Korea' },
    { code: 'SG', name: 'Singapore' },
    { code: 'HK', name: 'Hong Kong' },
    { code: 'CN', name: 'China' },
    { code: 'IN', name: 'India' },
    { code: 'BR', name: 'Brazil' },
    { code: 'MX', name: 'Mexico' },
    { code: 'AE', name: 'United Arab Emirates' },
    { code: 'CH', name: 'Switzerland' },
    { code: 'NL', name: 'Netherlands' },
    { code: 'SE', name: 'Sweden' },
    { code: 'NO', name: 'Norway' },
    { code: 'DK', name: 'Denmark' },
    { code: 'FI', name: 'Finland' },
    { code: 'IE', name: 'Ireland' },
    { code: 'NZ', name: 'New Zealand' },
    { code: 'ES', name: 'Spain' },
    { code: 'IT', name: 'Italy' },
    { code: 'PT', name: 'Portugal' },
    { code: 'PL', name: 'Poland' },
    { code: 'CZ', name: 'Czech Republic' },
    { code: 'RO', name: 'Romania' },
    { code: 'BG', name: 'Bulgaria' },
    { code: 'HR', name: 'Croatia' },
    { code: 'EE', name: 'Estonia' },
    { code: 'LV', name: 'Latvia' },
    { code: 'LT', name: 'Lithuania' },
    { code: 'SK', name: 'Slovakia' },
    { code: 'SI', name: 'Slovenia' },
    { code: 'HU', name: 'Hungary' },
    { code: 'AT', name: 'Austria' },
    { code: 'BE', name: 'Belgium' },
    { code: 'GR', name: 'Greece' },
    { code: 'ZA', name: 'South Africa' },
    { code: 'NG', name: 'Nigeria' },
    { code: 'KE', name: 'Kenya' },
    { code: 'EG', name: 'Egypt' },
    { code: 'TH', name: 'Thailand' },
    { code: 'VN', name: 'Vietnam' },
    { code: 'PH', name: 'Philippines' },
    { code: 'ID', name: 'Indonesia' },
    { code: 'MY', name: 'Malaysia' },
    { code: 'TW', name: 'Taiwan' },
    { code: 'AR', name: 'Argentina' },
    { code: 'CL', name: 'Chile' },
    { code: 'CO', name: 'Colombia' },
    { code: 'PE', name: 'Peru' },
    { code: 'IL', name: 'Israel' },
    { code: 'TR', name: 'Turkey' },
    { code: 'SA', name: 'Saudi Arabia' },
    { code: 'QA', name: 'Qatar' },
    { code: 'KW', name: 'Kuwait' },
    { code: 'RU', name: 'Russia' },
    { code: 'UA', name: 'Ukraine' }
  ];

  /* ═══════════════════════════════════════════ */
  /*  GBTPayoutPortal — orchestrator            */
  /* ═══════════════════════════════════════════ */

  function GBTPayoutPortal(opts) {
    this.companyId = opts.companyId;
    this.token = opts.token;
    this.balance = new GTBalance({ companyId: opts.companyId, token: opts.token, pollInterval: opts.pollInterval });
    this.withdraw = new GTWithdrawButton({ companyId: opts.companyId, token: opts.token, destinationLabel: opts.destinationLabel, onSuccess: opts.onWithdrawSuccess, onError: opts.onWithdrawError });
    this.history = new GTWithdrawHistory({ companyId: opts.companyId, token: opts.token });
    this.kyc = new GTKYCForm({ companyId: opts.companyId, token: opts.token, onComplete: opts.onKYCComplete });
  }

  GBTPayoutPortal.prototype.render = function(container) {
    var el = typeof container === 'string' ? document.querySelector(container) : container;
    if (!el) throw new Error('GBTPayoutPortal render target not found');

    var self = this;
    el.innerHTML = '';

    var grid = h('div', { className: 'gbt-payout-grid', style: 'display:grid;gap:24px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));' });

    var balanceSlot = h('div', { className: 'gbt-payout-slot' });
    var kycSlot = h('div', { className: 'gbt-payout-slot' });
    var withdrawSlot = h('div', { className: 'gbt-payout-slot' });
    var historySlot = h('div', { className: 'gbt-payout-slot', style: 'grid-column:1/-1;' });

    this.balance.mount(balanceSlot);
    this.kyc.mount(kycSlot);
    this.withdraw.mount(withdrawSlot);
    this.history.mount(historySlot);

    grid.appendChild(balanceSlot);
    grid.appendChild(kycSlot);
    grid.appendChild(withdrawSlot);
    grid.appendChild(historySlot);
    el.appendChild(grid);
  };

  /* ═══════════════════════════════════════════ */
  /*  Static mount helpers                       */
  /* ═══════════════════════════════════════════ */

  function mountBalance(target, opts) {
    var inst = new GTBalance(opts || {});
    inst.mount(target);
    return inst;
  }

  function mountWithdrawButton(target, opts) {
    var inst = new GTWithdrawButton(opts || {});
    inst.mount(target);
    return inst;
  }

  function mountWithdrawHistory(target, opts) {
    var inst = new GTWithdrawHistory(opts || {});
    inst.mount(target);
    return inst;
  }

  function mountKYCForm(target, opts) {
    var inst = new GTKYCForm(opts || {});
    inst.mount(target);
    return inst;
  }

  function mountPortal(target, opts) {
    var portal = new GBTPayoutPortal(opts || {});
    portal.render(target);
    return portal;
  }

  /* ═══════════════════════════════════════════ */
  /*  Public API                                 */
  /* ═══════════════════════════════════════════ */

  window.GBTPayout = {
    // Classes
    Portal: GBTPayoutPortal,
    Balance: GTBalance,
    WithdrawButton: GTWithdrawButton,
    WithdrawHistory: GTWithdrawHistory,
    KYCForm: GTKYCForm,
    // Static mount helpers
    mountBalance: mountBalance,
    mountWithdrawButton: mountWithdrawButton,
    mountWithdrawHistory: mountWithdrawHistory,
    mountKYCForm: mountKYCForm,
    mountPortal: mountPortal
  };

})();
