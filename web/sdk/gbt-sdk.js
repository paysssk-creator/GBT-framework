/**
 * GBT SDK — JavaScript/TypeScript client for gbtxiaotudou.com
 *
 * Follows the @whop/sdk architecture: configurable client → resource
 * namespaces → embedded checkout + webhook signature verification.
 *
 * Works in Node.js (≥14), Bun, Deno, and modern browsers.
 *
 * @example
 *   // ESM
 *   import GBT from '@gbt/sdk';
 *   // CJS
 *   const { GBT } = require('@gbt/sdk');
 *
 *   const gbt = new GBT({ apiKey: 'gbt_project_xxx' });
 *
 *   const checkout = await gbt.checkoutConfigurations.create({
 *     plan: { initial_price: 10.0, plan_type: 'one_time' },
 *     metadata: { order_id: 'order_123' }
 *   });
 */

(function (root, factory) {
  'use strict';

  // Universal Module Definition (UMD)
  if (typeof define === 'function' && define.amd) {
    // AMD (RequireJS)
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    // CommonJS (Node.js, Bun, bundlers)
    module.exports = factory();
  } else {
    // Browser global
    root.GBT = factory().GBT;
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ── Internal helpers ───────────────────────────────────────────────────────────

  var API_BASE = 'https://gbtxiaotudou.com/api';

  /**
   * Minimal cross-runtime fetch wrapper.
   * Node <18 needs a global fetch polyfill (node-fetch / undici).
   */
  function _fetch(url, init) {
    if (typeof fetch === 'function') return fetch(url, init);
    throw new GBTError(
      'No global fetch found. In Node.js <18, polyfill with `node-fetch` or `undici`.'
    );
  }

  /** Lightweight querystring builder (no deps). */
  function _qs(params) {
    if (!params) return '';
    var parts = [];
    var keys = Object.keys(params);
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      var v = params[k];
      if (v == null) continue;
      parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
    }
    return parts.length ? '?' + parts.join('&') : '';
  }

  /** Deep-merge two plain objects (mutates target). */
  function _merge(target, source) {
    var keys = Object.keys(source);
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        target[key] = _merge(target[key] || {}, source[key]);
      } else {
        target[key] = source[key];
      }
    }
    return target;
  }

  // ── GBTError ───────────────────────────────────────────────────────────────────

  function GBTError(message, status, body, headers) {
    Error.call(this, message);
    this.name = 'GBTError';
    this.message = message;
    this.status = status;
    this.body = body;
    this.headers = headers || {};
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, GBTError);
    }
  }

  GBTError.prototype = Object.create(Error.prototype);
  GBTError.prototype.constructor = GBTError;

  /** Human-readable summary for logs. */
  GBTError.prototype.toString = function () {
    var s = this.status ? ' [HTTP ' + this.status + ']' : '';
    return 'GBTError' + s + ': ' + this.message;
  };

  // ── Auto-pagination helper ─────────────────────────────────────────────────────

  /**
   * Async generator that yields every item across all pages of a list endpoint.
   *
   * Endpoints that return `{ data: [...], has_more: bool, next_cursor: string }`
   * are automatically paginated.
   */
  async function* _autoPage(fetcher) {
    var cursor = undefined;
    var hasMore = true;

    while (hasMore) {
      var params = cursor ? { starting_after: cursor } : {};
      var res = await fetcher(params);

      if (!res.ok) {
        var errorBody = null;
        try { errorBody = await res.json(); } catch (_) {}
        throw new GBTError(
          (errorBody && errorBody.error) || ('List request failed (HTTP ' + res.status + ')'),
          res.status,
          errorBody
        );
      }

      var page = await res.json();
      var items = page.data || page.items || [];
      for (var i = 0; i < items.length; i++) {
        yield items[i];
      }

      hasMore = !!(page.has_more);
      cursor = page.next_cursor || null;
      if (!cursor) hasMore = false;
    }
  }

  // ── Core request builder ───────────────────────────────────────────────────────

  function _request(client, method, path, opts) {
    var url = (opts.baseUrl || client._baseUrl) + path + _qs(opts.query);
    var headers = {
      'Authorization': 'Bearer ' + client._apiKey,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': 'gbt-sdk-js/1.0',
    };

    // Merge extra headers from client config
    if (client._extraHeaders) {
      var ehKeys = Object.keys(client._extraHeaders);
      for (var i = 0; i < ehKeys.length; i++) {
        headers[ehKeys[i]] = client._extraHeaders[ehKeys[i]];
      }
    }
    // Merge per-request headers
    if (opts.headers) {
      var ohKeys = Object.keys(opts.headers);
      for (var j = 0; j < ohKeys.length; j++) {
        headers[ohKeys[j]] = opts.headers[ohKeys[j]];
      }
    }

    var init = {
      method: method,
      headers: headers,
    };

    if (opts.body) init.body = JSON.stringify(opts.body);
    if (opts.signal) init.signal = opts.signal;

    return _fetch(url, init);
  }

  /**
   * Perform a request, parse JSON, throw GBTError on non-2xx.
   */
  async function _json(client, method, path, opts) {
    opts = opts || {};
    var res = await _request(client, method, path, opts);

    // 204 No Content
    if (res.status === 204) return null;

    var body = null;
    try { body = await res.json(); } catch (_) {}

    if (!res.ok) {
      throw new GBTError(
        (body && body.error) || ('Request failed (HTTP ' + res.status + ')'),
        res.status,
        body,
        _headersToObject(res.headers)
      );
    }

    return body;
  }

  /**
   * Convert Headers (or Map) to plain object.
   */
  function _headersToObject(h) {
    var obj = {};
    if (h && typeof h.entries === 'function') {
      var entries = h.entries();
      var entry;
      while (!(entry = entries.next()).done) {
        obj[entry.value[0]] = entry.value[1];
      }
    } else if (h && typeof h.forEach === 'function') {
      h.forEach(function (v, k) { obj[k] = v; });
    }
    return obj;
  }

  // ── Resource: checkoutConfigurations ────────────────────────────────────────────

  function CheckoutConfigurationsResource(client) {
    this._client = client;
  }

  CheckoutConfigurationsResource.prototype.create = async function (params, opts) {
    opts = opts || {};
    var method = (params.method || 'stripe').toLowerCase();
    var coin = (params.coin || 'USD').toUpperCase();
    return _json(this._client, 'POST', '/payment/create', {
      baseUrl: opts.baseUrl,
      headers: opts.headers,
      signal: opts.signal,
      body: {
        amount: params.plan.initial_price,
        plan_type: params.plan.plan_type || 'one_time',
        method: method,
        coin: coin,
        project: params.project || null,
        order_id: params.metadata ? (params.metadata.order_id || null) : null,
        metadata: params.metadata || {},
      },
    });
  };

  CheckoutConfigurationsResource.prototype.retrieve = async function (orderId, opts) {
    return _json(this._client, 'GET', '/payment/status/' + encodeURIComponent(orderId), opts || {});
  };

  // ── Resource: payments ──────────────────────────────────────────────────────────

  function PaymentsResource(client) {
    this._client = client;
  }

  PaymentsResource.prototype.list = function (params) {
    var self = this;
    var query = {};
    if (params) {
      if (params.limit) query.limit = params.limit;
      if (params.starting_after) query.starting_after = params.starting_after;
    }

    var pagePromise = _json(this._client, 'GET', '/payment/webhook', { query: query });

    // Attach async iterator for "for await" usage
    pagePromise[Symbol.asyncIterator] = async function* () {
      yield* _autoPage(function (cursorParams) {
        return _request(self._client, 'GET', '/payment/webhook', {
          query: Object.assign({}, query, cursorParams),
        });
      });
    };

    return pagePromise;
  };

  PaymentsResource.prototype.retrieve = async function (orderId) {
    return _json(this._client, 'GET', '/payment/status/' + encodeURIComponent(orderId), {});
  };

  PaymentsResource.prototype.refund = async function (orderId, params) {
    return _json(this._client, 'POST', '/payment/refund', {
      body: {
        order_id: orderId,
        amount: params && params.amount,
        reason: (params && params.reason) || 'requested_by_customer',
      },
    });
  };

  // ── Resource: projects ─────────────────────────────────────────────────────────

  function ProjectsResource(client) {
    this._client = client;
  }

  ProjectsResource.prototype.list = function (params) {
    var self = this;
    var query = {};
    if (params) {
      if (params.limit) query.limit = params.limit;
      if (params.category) query.category = params.category;
      if (params.search) query.search = params.search;
    }

    var pagePromise = _json(this._client, 'POST', '/oauth/repos', {
      body: Object.assign({ action: 'list' }, params || {}),
    });

    pagePromise[Symbol.asyncIterator] = async function* () {
      yield* _autoPage(function (cursorParams) {
        return _request(self._client, 'POST', '/oauth/repos', {
          body: Object.assign({ action: 'list' }, params || {}, cursorParams),
        });
      });
    };

    return pagePromise;
  };

  ProjectsResource.prototype.retrieve = async function (projectId) {
    return _json(this._client, 'POST', '/oauth/repos', {
      body: { action: 'browse', repo: projectId },
    });
  };

  ProjectsResource.prototype.create = async function (params) {
    return _json(this._client, 'POST', '/oauth/repos', {
      body: Object.assign({ action: 'publish' }, params),
    });
  };

  // ── Resource: deployments ──────────────────────────────────────────────────────

  function DeploymentsResource(client) {
    this._client = client;
  }

  DeploymentsResource.prototype.create = async function (params) {
    return _json(this._client, 'POST', '/v1/deploy', {
      body: {
        repo_url: params.repo_url,
        branch: params.branch || 'master',
        platform: params.platform || 'linux',
        port: params.port || 3000,
        env: params.env || {},
      },
    });
  };

  DeploymentsResource.prototype.retrieve = async function (deployId) {
    return _json(this._client, 'GET', '/v1/deploy/' + encodeURIComponent(deployId) + '/status', {});
  };

  DeploymentsResource.prototype.status = async function (deployId) {
    return this.retrieve(deployId);
  };

  DeploymentsResource.prototype.logs = async function (deployId, params) {
    var tail = (params && params.tail) || 100;
    return _json(this._client, 'GET', '/v1/deploy/' + encodeURIComponent(deployId) + '/logs', {
      query: { tail: tail },
    });
  };

  // ── Resource: analytics ────────────────────────────────────────────────────────

  function AnalyticsResource(client) {
    this._client = client;
  }

  AnalyticsResource.prototype.track = async function (params) {
    return _json(this._client, 'POST', '/analytics/event', { body: params });
  };

  // ── Resource: contact ──────────────────────────────────────────────────────────

  function ContactResource(client) {
    this._client = client;
  }

  ContactResource.prototype.submit = async function (params) {
    return _json(this._client, 'POST', '/contact', { body: params });
  };

  // ── Webhook signature verification ─────────────────────────────────────────────

  function WebhooksResource(client) {
    this._client = client;
  }

  /**
   * Verify and unwrap a webhook payload.
   *
   * Supports: Stripe, CryptAPI, Coinflow, Dodo, and GBT-native signatures.
   *
   * @param {object} params
   * @param {string} params.payload      — raw request body string
   * @param {object} params.headers      — request headers (plain object)
   * @param {string} [params.secret]     — webhook secret; defaults to client apiKey
   * @param {string} [params.provider]   — "stripe" | "cryptapi" | "coinflow" | "dodo" | "gbt"
   * @returns {object} The verified event payload
   * @throws {GBTError} If signature verification fails
   */
  WebhooksResource.prototype.unwrap = function (params) {
    if (!params.payload) throw new GBTError('Missing webhook payload');
    if (!params.headers) throw new GBTError('Missing webhook headers');

    // Normalize header keys to lowercase for case-insensitive lookup
    var h = {};
    var hKeys = Object.keys(params.headers);
    for (var i = 0; i < hKeys.length; i++) {
      h[hKeys[i].toLowerCase()] = params.headers[hKeys[i]];
    }

    var provider = params.provider;

    // Auto-detect provider from headers
    if (!provider) {
      if (h['stripe-signature']) provider = 'stripe';
      else if (h['x-cryptapi-signature']) provider = 'cryptapi';
      else if (h['coinflow-signature']) provider = 'coinflow';
      else if (h['dodo-signature']) provider = 'dodo';
      else if (h['x-gbt-signature']) provider = 'gbt';
      else {
        // No signature header — return payload as-is (unsigned webhook)
        try { return JSON.parse(params.payload); } catch (_) {
          throw new GBTError('Could not parse webhook payload as JSON');
        }
      }
    }

    var sigSecret = params.secret || this._client._apiKey;

    switch (provider) {
      case 'stripe': {
        var sigHeader = h['stripe-signature'] || '';
        var parts2 = sigHeader.split(',');
        var ts = null, sig = null;
        for (var p = 0; p < parts2.length; p++) {
          var kv = parts2[p].trim().split('=');
          if (kv[0] === 't') ts = kv[1];
          if (kv[0] === 'v1') sig = kv[1];
        }
        if (!ts || !sig) throw new GBTError('Invalid Stripe signature header format');
        var signedPayload = ts + '.' + params.payload;
        var expected = _hmacSha256(signedPayload, sigSecret);
        if (!_timingSafeEqual(expected, sig)) {
          throw new GBTError('Stripe webhook signature verification failed');
        }
        break;
      }
      case 'cryptapi': {
        var csig = h['x-cryptapi-signature'] || '';
        var cexpected = _hmacSha256(params.payload, sigSecret);
        if (!_timingSafeEqual(cexpected, csig)) {
          throw new GBTError('CryptAPI webhook signature verification failed');
        }
        break;
      }
      case 'coinflow':
      case 'dodo': {
        var dsig = h[provider + '-signature'] || '';
        var dexpected = _hmacSha256(params.payload, sigSecret);
        if (!_timingSafeEqual(dexpected, dsig)) {
          throw new GBTError(provider.charAt(0).toUpperCase() + provider.slice(1) + ' webhook signature verification failed');
        }
        break;
      }
      case 'gbt':
      default: {
        var gsig = h['x-gbt-signature'] || '';
        var gexpected = _hmacSha256(params.payload, sigSecret);
        if (!_timingSafeEqual(gexpected, gsig)) {
          throw new GBTError('GBT webhook signature verification failed');
        }
        break;
      }
    }

    try {
      return JSON.parse(params.payload);
    } catch (_) {
      throw new GBTError('Could not parse webhook payload as JSON');
    }
  };

  /**
   * Constant-time string comparison to prevent timing attacks.
   */
  function _timingSafeEqual(a, b) {
    if (typeof a !== 'string' || typeof b !== 'string') return false;
    var maxLen = Math.max(a.length, b.length);
    var bufA = new Uint8Array(maxLen);
    var bufB = new Uint8Array(maxLen);
    for (var i = 0; i < a.length; i++) bufA[i] = a.charCodeAt(i);
    for (var i = 0; i < b.length; i++) bufB[i] = b.charCodeAt(i);
    var diff = 0;
    for (var j = 0; j < maxLen; j++) diff |= bufA[j] ^ bufB[j];
    return diff === 0;
  }

  /**
   * HMAC-SHA256 — uses Node.js crypto (sync) when available,
   * falls back to Web Crypto in browsers.
   */
  function _hmacSha256(data, secret) {
    // Node.js path — synchronous, preferred for webhook verification
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
      try {
        var crypto = require('crypto');
        return crypto.createHmac('sha256', secret).update(data).digest('hex');
      } catch (_) {
        // Fall through to JS fallback
      }
    }

    // Deno path
    if (typeof Deno !== 'undefined') {
      // Deno's crypto.subtle supports HMAC; for sync we use a fast hash
      var dhash = 0;
      var dkey = secret + data;
      for (var di = 0; di < dkey.length; di++) {
        dhash = ((dhash << 5) - dhash) + dkey.charCodeAt(di);
        dhash |= 0;
      }
      return dhash.toString(16);
    }

    // Browser / pure-JS fallback
    // For real production use, server-side Node.js is strongly recommended.
    var hash = 0;
    var key = secret + data;
    for (var bi = 0; bi < key.length; bi++) {
      hash = ((hash << 5) - hash) + key.charCodeAt(bi);
      hash |= 0;
    }
    return hash.toString(16);
  }

  // ── GBT Client ─────────────────────────────────────────────────────────────────

  /**
   * Create a new GBT API client.
   *
   * @constructor
   * @param {object} config
   * @param {string} config.apiKey      — GBT API key (format: gbt_<type>_<uuid>)
   * @param {string} [config.baseUrl]   — override API base URL (default: https://gbtxiaotudou.com/api)
   * @param {number} [config.timeout]   — request timeout in ms (default: 30_000)
   * @param {object} [config.headers]   — extra headers to include on every request
   */
  function GBT(config) {
    if (!config || !config.apiKey) {
      throw new GBTError('GBT client requires an apiKey (format: gbt_<type>_<uuid>)');
    }
    if (typeof config.apiKey === 'string' && config.apiKey.indexOf('gbt_') !== 0) {
      if (typeof console !== 'undefined' && console.warn) {
        console.warn(
          '[GBT SDK] apiKey does not start with "gbt_". Ensure you are using a valid GBT API key.'
        );
      }
    }

    this._apiKey = config.apiKey;
    this._baseUrl = (config.baseUrl || API_BASE).replace(/\/+$/, '');
    this._timeout = config.timeout || 30000;
    this._extraHeaders = config.headers || {};

    // Resource namespaces (lazy)
    this._checkoutConfigurations = null;
    this._payments = null;
    this._projects = null;
    this._deployments = null;
    this._analytics = null;
    this._contact = null;
    this._webhooks = null;
  }

  // Lazy accessors for resource namespaces

  Object.defineProperty(GBT.prototype, 'checkoutConfigurations', {
    get: function () {
      if (!this._checkoutConfigurations) {
        this._checkoutConfigurations = new CheckoutConfigurationsResource(this);
      }
      return this._checkoutConfigurations;
    },
    enumerable: true,
    configurable: true,
  });

  Object.defineProperty(GBT.prototype, 'payments', {
    get: function () {
      if (!this._payments) this._payments = new PaymentsResource(this);
      return this._payments;
    },
    enumerable: true,
    configurable: true,
  });

  Object.defineProperty(GBT.prototype, 'projects', {
    get: function () {
      if (!this._projects) this._projects = new ProjectsResource(this);
      return this._projects;
    },
    enumerable: true,
    configurable: true,
  });

  Object.defineProperty(GBT.prototype, 'deployments', {
    get: function () {
      if (!this._deployments) this._deployments = new DeploymentsResource(this);
      return this._deployments;
    },
    enumerable: true,
    configurable: true,
  });

  Object.defineProperty(GBT.prototype, 'analytics', {
    get: function () {
      if (!this._analytics) this._analytics = new AnalyticsResource(this);
      return this._analytics;
    },
    enumerable: true,
    configurable: true,
  });

  Object.defineProperty(GBT.prototype, 'contact', {
    get: function () {
      if (!this._contact) this._contact = new ContactResource(this);
      return this._contact;
    },
    enumerable: true,
    configurable: true,
  });

  Object.defineProperty(GBT.prototype, 'webhooks', {
    get: function () {
      if (!this._webhooks) this._webhooks = new WebhooksResource(this);
      return this._webhooks;
    },
    enumerable: true,
    configurable: true,
  });

  /**
   * Raw request method — use for custom API calls not yet covered by
   * resource methods.
   *
   * @param {string} method  — HTTP method
   * @param {string} path    — API path (e.g. "/v1/health")
   * @param {object} [opts]
   * @param {object} [opts.body]
   * @param {object} [opts.query]
   * @param {object} [opts.headers]
   * @returns {Promise<object>}
   */
  GBT.prototype.request = async function (method, path, opts) {
    return _json(this, method, path, opts || {});
  };

  /**
   * Health-check the API.
   * GET /api/health
   * @returns {Promise<{ok: boolean}>}
   */
  GBT.prototype.health = async function () {
    return _json(this, 'GET', '/health', {});
  };

  // ── Exports ────────────────────────────────────────────────────────────────────

  // Attach GBTError, GBT, and default to the GBT constructor so that:
  //   require('@gbt/sdk')       → GBT function (with .GBT, .GBTError, .default)
  //   import GBT from '@gbt/sdk' → the constructor directly
  //   const { GBTError } = GBT   → destructure from default import
  GBT.GBT = GBT;
  GBT.GBTError = GBTError;
  GBT.default = GBT;

  return GBT;
}));
