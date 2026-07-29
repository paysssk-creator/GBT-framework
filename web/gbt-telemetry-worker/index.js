// GBT Telemetry Worker — 接收 API Gateway 遥测事件
// 绑定: gbt-telemetry-worker (wrangler.toml tail_consumers)
export default {
  async tail(events) {
    const counts = { requests: 0, errors: 0, eye_ops: 0, ai: 0, tunnel: 0 };

    for (const event of events) {
      counts.requests++;
      const logs = event.logs || [];
      for (const log of logs) {
        const msg = log.message?.[1] || '';
        if (msg.includes('error') || msg.includes('Error')) counts.errors++;
        if (msg.includes('eye') || msg.includes('Eye')) counts.eye_ops++;
        if (msg.includes('AI Gateway') || msg.includes('ai_gateway')) counts.ai++;
        if (msg.includes('tunnel') || msg.includes('Tunnel')) counts.tunnel++;
      }
    }

    console.log(JSON.stringify({
      ts: Date.now(),
      batchSize: events.length,
      ...counts,
    }));

    return { outcome: 'ok', counts };
  },

  async fetch(request) {
    return new Response(JSON.stringify({ ok: true, service: 'gbt-telemetry-worker' }), {
      headers: { 'Content-Type': 'application/json' },
    });
  },
};
