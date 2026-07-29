# GBT AI Gateway · Cloudflare AI Gateway 集成
# 所有 LLM 调用通过 Cloudflare AI Gateway 代理
# 功能: 分析/缓存/限流/回退/日志
# ============================================================
"""
用法:
  from ai_gateway import ai_gateway
  
  # 替代直接调用 LLM:
  result = ai_gateway.chat(messages, model="deepseek-chat")
  
  # 带缓存的调用(相同问题返回缓存):
  result = ai_gateway.cached_chat(messages, model="deepseek-chat")
  
  # 带模型回退的调用:
  result = ai_gateway.fallback_chat(messages, 
      models=["deepseek-chat", "gpt-4o-mini", "claude-3-haiku"])

配置:
  AI_GATEWAY_ENABLED=true/false  — 是否启用
  AI_GATEWAY_ACCOUNT_ID          — Cloudflare 账户 ID
  AI_GATEWAY_NAME                — Gateway 名称 (默认: gbt-ai-gateway)
  AI_GATEWAY_CACHE_TTL           — 缓存 TTL (默认: 3600秒)
"""
import json, os, time, hashlib, urllib.request, urllib.error
from pathlib import Path

# ═══════════════ 配置 ═══════════════
AI_GATEWAY_ENABLED = os.environ.get("AI_GATEWAY_ENABLED", "true").lower() == "true"
ACCOUNT_ID = os.environ.get("AI_GATEWAY_ACCOUNT_ID", "82dd88c2a3907846e9797ea95419802f")
GATEWAY_NAME = os.environ.get("AI_GATEWAY_NAME", "gbt-ai-gateway")
CACHE_TTL = int(os.environ.get("AI_GATEWAY_CACHE_TTL", "3600"))
GATEWAY_BASE = f"https://gateway.ai.cloudflare.com/v1/{ACCOUNT_ID}/{GATEWAY_NAME}"

# Provider mapping — Cloudflare AI Gateway supports these
PROVIDER_ENDPOINTS = {
    "deepseek":    "/deepseek/chat/completions",
    "openai":      "/openai/chat/completions",
    "anthropic":   "/anthropic/v1/messages",
    "google":      "/google-ai-studio/v1/models",
    "workers-ai":  "/workers-ai",
}

# API keys per provider
_PROVIDER_KEYS = {
    "deepseek":   os.environ.get("DEEPSEEK_API_KEY", ""),
    "openai":     os.environ.get("OPENAI_API_KEY", ""),
    "anthropic":  os.environ.get("ANTHROPIC_API_KEY", ""),
    "google":     os.environ.get("GOOGLE_AI_API_KEY", ""),
    "workers-ai": os.environ.get("CLOUDFLARE_API_TOKEN", ""),
}
# ═══════════════ 缓存 ═══════════════
_cache_dir = Path.home() / ".gbt" / "ai_cache"
_cache_dir.mkdir(parents=True, exist_ok=True)

def _cache_key(messages, model):
    """生成缓存键"""
    content = json.dumps({"messages": messages, "model": model}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def _cache_get(key):
    f = _cache_dir / f"{key}.json"
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if time.time() - data.get("ts", 0) < CACHE_TTL:
                return data.get("response")
        except:
            pass
    return None

def _cache_set(key, response):
    f = _cache_dir / f"{key}.json"
    f.write_text(json.dumps({"ts": time.time(), "response": response}, ensure_ascii=False), encoding="utf-8")

# ═══════════════ AI Gateway 核心 ═══════════════
class AIGateway:
    """Cloudflare AI Gateway 代理层"""

    def __init__(self, provider="deepseek"):
        self.provider = provider
        self.api_key = _PROVIDER_KEYS.get(provider, "")
        self.endpoint = PROVIDER_ENDPOINTS.get(provider, f"/{provider}/chat/completions")

    def _build_url(self):
        if AI_GATEWAY_ENABLED:
            return f"{GATEWAY_BASE}{self.endpoint}"
        # 回退: 直连各Provider
        fallback_urls = {
            "deepseek":  "https://api.deepseek.com/chat/completions",
            "openai":    "https://api.openai.com/v1/chat/completions",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "google":    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
        }
        return fallback_urls.get(self.provider, f"https://api.{self.provider}.com/chat/completions")

    def _build_headers(self, cf_cache=False):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if AI_GATEWAY_ENABLED and cf_cache:
            # 启用 Cloudflare CDN 缓存
            headers["CF-Cache-TTL"] = str(CACHE_TTL)
        return headers

    def chat(self, messages, model=None, max_tokens=500, temperature=0.7, timeout=30, cache=False):
        """发送聊天请求 — 通过 AI Gateway"""
        if not self.api_key:
            return None

        model = model or os.environ.get("GBT_LLM_MODEL", "deepseek-chat")

        # 缓存检查
        if cache:
            ck = _cache_key(messages, model)
            cached = _cache_get(ck)
            if cached:
                return cached

        payload = json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }).encode()

        url = self._build_url()
        headers = self._build_headers(cf_cache=cache)

        try:
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                # 跨 provider 响应解析
                if self.provider == "anthropic":
                    result = data.get("content", [{}])[0].get("text", "")
                elif self.provider == "google":
                    result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                else:
                    result = data["choices"][0]["message"]["content"]

                # 写入缓存
                if cache:
                    ck = _cache_key(messages, model)
                    _cache_set(ck, result)

                # 解析 AI Gateway 响应头(用量/成本信息)
                usage = data.get("usage", {})
                gateway_info = {
                    "cached": resp.headers.get("cf-ai-gateway-cache", "miss"),
                    "model": model,
                    "tokens": usage.get("total_tokens", 0),
                }

                return result

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            print(f"[AI Gateway] HTTP {e.code}: {error_body[:200]}", flush=True)
            return None
        except Exception as e:
            print(f"[AI Gateway] 错误: {e}", flush=True)
            return None

    def fallback_chat(self, messages, models=None, **kwargs):
        """带模型回退的聊天 — 主模型失败自动切换"""
        models = models or ["deepseek-chat", "gpt-4o-mini", "claude-3-haiku"]

        for model in models:
            # 根据模型名推断 provider
            if "deepseek" in model.lower():
                provider = "deepseek"
            elif "gpt" in model.lower() or "o1" in model.lower() or "o3" in model.lower():
                provider = "openai"
            elif "claude" in model.lower():
                provider = "anthropic"
            elif "gemini" in model.lower():
                provider = "google"
            else:
                provider = self.provider

            gateway = AIGateway(provider)
            if not gateway.api_key:
                continue

            result = gateway.chat(messages, model=model, **kwargs)
            if result:
                return {
                    "ok": True,
                    "answer": result,
                    "model_used": model,
                    "fallback": model != models[0],
                }

        return {"ok": False, "error": f"所有模型不可用: {models}"}

    def vision(self, image_b64, question, model="deepseek-chat", **kwargs):
        """视觉分析 — 图片 + 文字"""
        if not self.api_key:
            return None

        payload = json.dumps({
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": question or "请描述这张图片"},
                    {"type": "image_url", "image_url": {"url": image_b64}},
                ]
            }],
            "max_tokens": kwargs.get("max_tokens", 1000),
        }).encode()

        url = self._build_url()
        headers = self._build_headers()

        try:
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 60)) as resp:
                data = json.loads(resp.read())
                # 多Provider响应格式适配
                if "choices" in data:  # OpenAI / DeepSeek 格式
                    return data["choices"][0]["message"]["content"]
                if "content" in data:  # Anthropic 格式
                    content = data["content"]
                    if isinstance(content, list):
                        return "".join(c.get("text", "") for c in content)
                    return str(content)
                if "candidates" in data:  # Google 格式
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                return str(data)
        except Exception as e:
            return {"error": str(e)}
ai_gateway = AIGateway("deepseek")

# ═══════════════ 便捷函数 ═══════════════
def cached_chat(messages, **kwargs):
    """带缓存的聊天"""
    return ai_gateway.chat(messages, cache=True, **kwargs)

def fallback_chat(messages, models=None, **kwargs):
    """带模型回退的聊天"""
    return ai_gateway.fallback_chat(messages, models=models, **kwargs)

def vision_chat(image_b64, question, **kwargs):
    """视觉分析"""
    return ai_gateway.vision(image_b64, question, **kwargs)

def gateway_status():
    """AI Gateway 状态"""
    return {
        "enabled": AI_GATEWAY_ENABLED,
        "account_id": ACCOUNT_ID,
        "gateway_name": GATEWAY_NAME,
        "gateway_url": GATEWAY_BASE if AI_GATEWAY_ENABLED else None,
        "cache_ttl": CACHE_TTL,
        "available_providers": [p for p, k in _PROVIDER_KEYS.items() if k],
    }
