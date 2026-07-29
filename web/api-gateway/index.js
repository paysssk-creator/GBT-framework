// GBT API Gateway Worker v3.0
// - Eye/vision → durable Workflows
// - AI requests → AI Gateway proxy
// - Structured logging → Workers Observability / Traces
// - Request tracing → OpenTelemetry context propagation
import { EyeWorkflow, TunnelHealthWorkflow } from "./eye-workflow.js";

// ═══════════════ Config ═══════════════
const EYE_PATHS = ["/api/eye/screenshot", "/api/eye/see", "/api/eye/scan", "/api/eye/vision"];
const MAX_RETRIES = 2;
const REQUEST_TIMEOUT = 25000;

// ═══════════════ Helpers ═══════════════
function getTunnel(env) {
  return env.BACKEND_URL || "https://congress-depth-subjective-recreation.trycloudflare.com";
}

function parseEyeAction(path) {
  const map = {
    "/api/eye/screenshot": "screenshot",
    "/api/eye/see": "see",
    "/api/eye/scan": "scan",
    "/api/eye/vision": "vision",
  };
  return map[path] || null;
}

async function forwardWithRetry(targetUrl, request, retries = MAX_RETRIES) {
  let lastError = null;

  for (let i = 0; i <= retries; i++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

      const body = request.method !== "GET" && request.method !== "HEAD"
        ? await request.clone().arrayBuffer()
        : undefined;

      const resp = await fetch(targetUrl, {
        method: request.method,
        headers: request.headers,
        body,
        signal: controller.signal,
        redirect: "follow",
      });

      clearTimeout(timeout);
      return resp;
    } catch (e) {
      lastError = e.message;
      if (i < retries) {
        // Exponential backoff: 500ms, 1s, 2s
        await new Promise(r => setTimeout(r, 500 * Math.pow(2, i)));
      }
    }
  }

  return new Response(JSON.stringify({
    ok: false,
    error: `后端不可达 (${retries + 1}次重试): ${lastError}`,
  }), {
    status: 502,
    headers: { "Content-Type": "application/json" },
  });
}

function corsHeaders(origin = "*") {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
  };
}

// ═══════════════ Main Handler ═══════════════
export default {
  async fetch(request, env, ctx) {
    const startTime = Date.now();
    const url = new URL(request.url);
    const path = url.pathname;
    const tunnel = getTunnel(env);

    // ── Trace context ──
    const traceId = request.headers.get("cf-ray") || crypto.randomUUID();

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    // ── Health check (含 AI Gateway 状态) ──
    if (path === "/api/health" || path === "/api/eye/health") {
      let tunnelStatus = "disconnected";
      let aiGateway = "unknown";
      try {
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), 5000);
        const resp = await fetch(`${tunnel}/api/health`, { signal: controller.signal });
        clearTimeout(t);
        const data = await resp.json().catch(() => ({}));
        tunnelStatus = data.status === "running" ? "connected" : "degraded";
      } catch (e) { /* stays disconnected */ }
      // AI Gateway check
      if (env.AI_GATEWAY_ENABLED === "true") {
        aiGateway = "enabled";
      }
      console.log(JSON.stringify({
        type: "health_check",
        trace_id: traceId,
        tunnel: tunnelStatus,
        ai_gateway: aiGateway,
        duration_ms: Date.now() - startTime,
      }));
      return new Response(JSON.stringify({
        ok: true, status: "running",
        tunnel: tunnelStatus, workflow: "active",
        ai_gateway: aiGateway,
      }), { headers: { ...corsHeaders(), "Content-Type": "application/json" } });
    }

    // ── AI Gateway metrics endpoint ──
    if (path === "/api/metrics/ai") {
      return new Response(JSON.stringify({
        ok: true,
        ai_gateway: {
          enabled: env.AI_GATEWAY_ENABLED === "true",
          account_id: env.AI_GATEWAY_ACCOUNT_ID,
          gateway_name: env.AI_GATEWAY_NAME,
          dashboard: `https://dash.cloudflare.com/${env.AI_GATEWAY_ACCOUNT_ID}/ai/ai-gateway`,
        },
        trace: {
          ray_id: traceId,
          dashboard: `https://dash.cloudflare.com/${env.AI_GATEWAY_ACCOUNT_ID}/trace`,
        },
      }), { headers: { ...corsHeaders(), "Content-Type": "application/json" } });
    }

    // ── Eye API: route through durable Workflow ──
    const eyeAction = parseEyeAction(path);
    if (eyeAction && env.EYE_WORKFLOW) {
      try {
        let body = {};
        if (request.method !== "GET" && request.method !== "HEAD") {
          body = await request.clone().json().catch(() => ({}));
        }
        const instance = await env.EYE_WORKFLOW.create({
          params: { action: eyeAction, body, tunnel },
        });
        const result = await instance.status();
        console.log(JSON.stringify({
          type: "eye_workflow", trace_id: traceId,
          action: eyeAction, instance: result.id,
          duration_ms: Date.now() - startTime,
        }));
        return new Response(JSON.stringify({
          ok: true, action: eyeAction,
          workflow_instance: result.id, status: result.status,
          ...result.output,
        }), { headers: { ...corsHeaders(), "Content-Type": "application/json" } });
      } catch (e) {
        console.warn(JSON.stringify({
          type: "eye_workflow_fallback", trace_id: traceId,
          action: eyeAction, error: e.message,
        }));
      }
    }

    // ── Direct forward ──
    const targetUrl = `${tunnel}${url.pathname}${url.search}`;
    const retries = EYE_PATHS.includes(path) ? 3 : 1;
    const resp = await forwardWithRetry(targetUrl, request, retries);
    const newResp = new Response(resp.body, resp);
    Object.entries(corsHeaders()).forEach(([k, v]) => newResp.headers.set(k, v));

    console.log(JSON.stringify({
      type: "request", trace_id: traceId,
      method: request.method, path,
      status: resp.status, retries,
      duration_ms: Date.now() - startTime,
    }));
    return newResp;
  },
};
export { EyeWorkflow, TunnelHealthWorkflow };
