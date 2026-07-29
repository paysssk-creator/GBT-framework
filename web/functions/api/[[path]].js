// GBT API Gateway — OAuth + proxy
export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
  };
  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  // Handle OAuth endpoints directly
  if (url.pathname === "/api/oauth/login" || url.pathname === "/api/oauth/login/") {
    const clientId = env.GITHUB_CLIENT_ID || "";
    const redirectUri = env.GBT_OAUTH_REDIRECT || "https://gbtxiaotudou.com/oauth-callback.html";
    const state = crypto.randomUUID();
    const githubUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=repo,read:user&state=${state}`;
    return Response.redirect(githubUrl, 302);
  }

  if (url.pathname === "/api/oauth/exchange" || url.pathname === "/api/oauth/exchange/") {
    try {
      const body = await request.json();
      const code = body.code || "";
      const clientId = env.GITHUB_CLIENT_ID || "";
      const clientSecret = env.GITHUB_CLIENT_SECRET || "";
      const ghResp = await fetch("https://github.com/login/oauth/access_token", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ client_id: clientId, client_secret: clientSecret, code: code })
      });
      const data = await ghResp.json();
      // Store token in KV if available
      if (data.access_token && env.GBT_KV) {
        const userResp = await fetch("https://api.github.com/user", {
          headers: { "Authorization": `Bearer ${data.access_token}`, "User-Agent": "GBT" }
        });
        const user = await userResp.json();
        await env.GBT_KV.put(`oauth:${user.login}`, JSON.stringify({
          token: data.access_token, login: user.login, avatar: user.avatar_url, at: Date.now()
        }));
        return new Response(JSON.stringify({ ok: true, login: user.login }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }
      return new Response(JSON.stringify(data.access_token ? { ok: true, token: data.access_token } : { ok: false, error: "no token" }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
    } catch (e) {
      return new Response(JSON.stringify({ ok: false, error: e.message }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
    }
  }

  if (url.pathname === "/api/oauth/status" || url.pathname === "/api/oauth/status/") {
    try {
      if (env.GBT_KV) {
        const list = await env.GBT_KV.list({ prefix: "oauth:" });
        return new Response(JSON.stringify({ ok: true, sessions: list.keys.length }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }
      return new Response(JSON.stringify({ ok: true, note: "KV not configured" }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
    } catch (e) {
      return new Response(JSON.stringify({ ok: false, error: e.message }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
    }
  }

  // Fallback: proxy to backend tunnel
  const BACKEND = env.BACKEND_URL || "https://api-tunnel.gbtxiaotudou.com";
  url.hostname = new URL(BACKEND).hostname;
  url.protocol = "https:";
  const modified = new Request(url.toString(), {
    method: request.method, headers: request.headers,
    body: request.method !== "GET" && request.method !== "HEAD" ? await request.arrayBuffer() : undefined,
    redirect: "follow"
  });
  const response = await fetch(modified);
  const newResponse = new Response(response.body, response);
  Object.entries(corsHeaders).forEach(([k, v]) => newResponse.headers.set(k, v));
  return newResponse;
}
