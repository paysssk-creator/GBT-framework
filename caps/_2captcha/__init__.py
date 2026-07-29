# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""_2captcha — 共享2Captcha客户端库

提供四条产品线的统一Python客户端:
  - CaptchaSolver   — 验证码识别 (API v2)
  - ProxyNetwork    — 住宅代理网络
  - FingerprintAPI  — 浏览器指纹生成
  - CloudBrowser    — 云端CDP浏览器

环境变量:
  CAPTCHA_API_KEY  — 2Captcha API Key (32-char)
"""
from caps._2captcha.client import (
    CaptchaSolver,
    ProxyNetwork,
    FingerprintAPI,
    CloudBrowser,
    get_solver,
    get_proxy,
    get_fingerprint,
    get_browser,
)

__all__ = [
    "CaptchaSolver", "ProxyNetwork", "FingerprintAPI", "CloudBrowser",
    "get_solver", "get_proxy", "get_fingerprint", "get_browser",
]
