// GBT 土豆眼 · Cloudflare Workflow
// Durable execution for eye/screenshot operations
// Survives tunnel disconnects, retries with backoff, checkpoints progress

import { WorkflowEntrypoint } from "cloudflare:workers";

// ═══════════════ Params ═══════════════
const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000;   // 1s base, exponential backoff
const REQUEST_TIMEOUT_MS = 30000; // 30s per request
const CACHE_TTL_SEC = 10;      // cache screenshots for 10s

// ═══════════════ Workflow ═══════════════
export class EyeWorkflow extends WorkflowEntrypoint {
  async run(event, step) {
    const { action, body, tunnel } = event.payload;

    // Step 1: Validate request
    const valid = await step.do("validate", () => {
      const allowed = ["screenshot", "see", "scan", "vision"];
      if (!allowed.includes(action)) {
        return { ok: false, error: `未知眼睛动作: ${action}`, allowed };
      }
      return { ok: true };
    });
    if (!valid.ok) return valid;

    // Step 2: Forward to backend tunnel with retry
    const result = await step.do("forward-with-retry", async () => {
      let lastError = null;

      for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        try {
          const controller = new AbortController();
          const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

          const endpoint = this._getEndpoint(action);
          const targetUrl = `${tunnel}${endpoint}`;

          const resp = await fetch(targetUrl, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "User-Agent": "GBT-EyeWorkflow/1.0",
            },
            body: JSON.stringify(body || {}),
            signal: controller.signal,
          });

          clearTimeout(timeout);

          if (resp.ok) {
            const data = await resp.json();
            return { ok: true, ...data, _attempt: attempt + 1 };
          }

          // Non-retryable status codes
          if (resp.status === 400 || resp.status === 401 || resp.status === 403 || resp.status === 404) {
            const errData = await resp.json().catch(() => ({}));
            return { ok: false, error: errData.error || `HTTP ${resp.status}`, status: resp.status };
          }

          lastError = `HTTP ${resp.status}`;
        } catch (e) {
          lastError = e.message || "连接失败";
        }

        // Exponential backoff before retry
        if (attempt < MAX_RETRIES - 1) {
          const delaySec = Math.round(BASE_DELAY_MS * Math.pow(2, attempt) / 1000);
          await step.sleep(`retry-delay-${attempt}`, `${delaySec} seconds`);
        }
      }

      return { ok: false, error: `所有 ${MAX_RETRIES} 次重试失败: ${lastError}` };
    });

    // Step 3: Cache result for quick repeat access
    if (result.ok && action === "screenshot") {
      await step.do("cache-result", async () => {
        // Store in workflow state for potential quick re-fetch
        this._cachedResult = { data: result, ts: Date.now() };
      });
    }

    return result;
  }

  _getEndpoint(action) {
    const endpoints = {
      screenshot: "/api/eye/screenshot",
      see:        "/api/eye/see",
      scan:       "/api/eye/scan",
      vision:     "/api/eye/vision",
    };
    return endpoints[action] || "/api/eye/screenshot";
  }
}

// ═══════════════ Tunnel Health Checker ═══════════════
export class TunnelHealthWorkflow extends WorkflowEntrypoint {
  async run(event, step) {
    const { tunnel } = event.payload;
    const startMs = Date.now();
    const result = await step.do("health-check", async () => {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);

        const resp = await fetch(`${tunnel}/api/health`, {
          method: "GET",
          signal: controller.signal,
        });

        clearTimeout(timeout);
        if (resp.ok) {
          const data = await resp.json();
          return { ok: true, status: data.status || "running", latency_ms: Date.now() - startMs };
        }
        return { ok: false, status: `HTTP ${resp.status}` };
      } catch (e) {
        return { ok: false, status: "unreachable", error: e.message };
      }
    });

    // Circuit breaker: if down 3x consecutive, mark unhealthy
    const failures = (await step.do("track-failures", async () => {
      const prev = this._consecutiveFailures || 0;
      this._consecutiveFailures = result.ok ? 0 : prev + 1;
      return this._consecutiveFailures;
    }));

    return {
      ...result,
      consecutive_failures: failures,
      circuit: failures >= 3 ? "open" : "closed",
    };
  }
}
