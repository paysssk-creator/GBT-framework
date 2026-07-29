// GBT Telemetry Tail Worker
// 接收 Worker 遥测数据 → 结构化处理 → 存储到 Analytics
// Cloudflare Workers 自动将 trace/log 事件发送到此 Worker
// ============================================================

export default {
  async tail(events, env, ctx) {
    const metrics = {
      requests: 0,
      errors: 0,
      eye_ops: 0,
      total_latency_ms: 0,
      ai_requests: 0,
      tunnel_disconnects: 0,
    };

    for (const event of events) {
      metrics.requests++;

      // 统计错误
      if (event.outcome !== "ok") {
        metrics.errors++;
      }

      // 统计眼睛操作
      const url = event.scriptName || "";
      if (url.includes("/api/eye/")) {
        metrics.eye_ops++;
        metrics.total_latency_ms += event.event.duration || 0;
      }

      // 统计 AI 请求
      if (url.includes("/api/ask") || url.includes("/api/eye/vision")) {
        metrics.ai_requests++;
      }

      // 隧道断连检测
      if (event.outcome === "exception" && event.event?.error?.includes("tunnel")) {
        metrics.tunnel_disconnects++;
      }

      // 结构化日志输出 (自动进入 Workers Logs)
      console.log(JSON.stringify({
        ts: event.eventTimestamp,
        outcome: event.outcome,
        script: event.scriptName,
        method: event.event?.request?.method,
        path: event.event?.request?.url,
        status: event.event?.response?.status,
        duration_ms: event.event?.duration,
        cpu_ms: event.event?.cpuTime,
      }));
    }

    // 聚合指标输出
    const avg_latency = metrics.eye_ops > 0
      ? Math.round(metrics.total_latency_ms / metrics.eye_ops)
      : 0;

    console.log(JSON.stringify({
      type: "metrics_aggregate",
      ts: Date.now(),
      ...metrics,
      avg_eye_latency_ms: avg_latency,
    }));

    // 存储到 KV (如已绑定)
    if (env.TELEMETRY_KV) {
      const key = `metrics:${new Date().toISOString().slice(0, 13)}`; // hourly
      await env.TELEMETRY_KV.put(key, JSON.stringify(metrics), { expirationTtl: 86400 });
    }
  },
};
