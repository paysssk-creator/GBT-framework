# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/intent_broker.py — 意图识别引擎
======================================
第1层管线第②步: LLM语义意图识别，四层拆解。
将用户自然语言映射到: 意图类别 → 能力模块 → 动作 → 参数。
"""
import json, os, urllib.request, urllib.error

# ── Provider-aware API key selection ──
_PROVIDER = os.environ.get("GBT_LLM_PROVIDER", "deepseek").lower()
_PROVIDER_KEY_MAP = {
    "deepseek": "DEEPSEEK_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "kimi":     "KIMI_API_KEY",
    "openai":   "OPENAI_API_KEY",
}
_PROVIDER_DEFAULTS = {
    "deepseek":  {"base": "https://api.deepseek.com",   "model": "deepseek-chat"},
    "moonshot":  {"base": "https://api.moonshot.cn/v1", "model": "moonshot-v1-128k"},
    "kimi":      {"base": "https://api.moonshot.cn/v1", "model": "moonshot-v1-128k"},
    "openai":    {"base": "https://api.openai.com/v1",  "model": "gpt-4o-mini"},
}

_key_env = _PROVIDER_KEY_MAP.get(_PROVIDER, "DEEPSEEK_API_KEY")
API_KEY = os.environ.get(_key_env, "")
_defaults = _PROVIDER_DEFAULTS.get(_PROVIDER, _PROVIDER_DEFAULTS["deepseek"])
BASE_URL = os.environ.get("GBT_LLM_BASE_URL", _defaults["base"])
MODEL = os.environ.get("GBT_LLM_MODEL", _defaults["model"])

# 意图分类体系
INTENT_CATEGORIES = {
    "code_write":    {"desc": "编写代码",     "caps": ["programming", "gbt_writer"]},
    "code_debug":    {"desc": "调试代码",     "caps": ["root_cause_debugger", "auto_fix"]},
    "code_review":   {"desc": "代码审查",     "caps": ["code_scanner", "programming"]},
    "code_refactor": {"desc": "重构代码",     "caps": ["programming", "ponytail"]},
    "code_explain":  {"desc": "解释代码",     "caps": ["codebase_memory", "rag_knowledge"]},
    "design":        {"desc": "设计方案",     "caps": ["design_brain", "task_mind"]},
    "reason":        {"desc": "深度推理",     "caps": ["deep_reasoner", "cloud_brain"]},
    "learn":         {"desc": "学习知识",     "caps": ["rag_knowledge", "web_search"]},
    "evolve":        {"desc": "自我进化",     "caps": ["self_evolve", "memory"]},
    "diagnose":      {"desc": "自我诊断",     "caps": ["self_diagnostic", "health_dashboard"]},
    "plan":          {"desc": "任务规划",     "caps": ["task_mind", "collab_dispatch"]},
    "create_media":  {"desc": "创作媒体",     "caps": ["mind_visual", "ai_drama", "voice_speak"]},
    "analyze_data":  {"desc": "分析数据",     "caps": ["data_engine", "database"]},
    "attack_full":   {"desc": "全攻击链轰炸",  "caps": ["n8n_attack_chain", "pentest_kali"]},
    "bombard":       {"desc": "一键轰炸",       "caps": ["n8n_attack_chain"]},
    "chat":          {"desc": "通用对话",     "caps": ["cloud_llm", "multi_llm"]},
}


class IntentBroker:
    """意图识别引擎 — 将自然语言映射到结构化的意图+能力路由"""

    def __init__(self):
        self.categories = INTENT_CATEGORIES

    def analyze(self, text: str) -> dict:
        """分析用户意图，返回四层拆解结果"""
        if not text or not text.strip():
            return {"intent": "unknown", "confidence": 0, "error": "empty input"}

        # 如果API可用，使用LLM分析
        if API_KEY:
            return self._llm_analyze(text)
        
        # 否则回退到关键词匹配
        return self._keyword_analyze(text)

    def _llm_analyze(self, text: str) -> dict:
        """通过LLM API进行语义意图识别"""
        prompt = f"""分析以下用户消息的意图。返回JSON格式:
{{
  "intent": "意图类别",
  "confidence": 0.0-1.0,
  "breakdown": {{
    "layer1_domain": "领域(engineering/creative/analysis/chat)",
    "layer2_action": "动作(write/review/debug/design/reason/learn/ask)",
    "layer3_target": "目标对象(代码/文档/系统/知识/方案)",
    "layer4_params": {{"key": "value"}}
  }},
  "suggested_caps": ["cap1", "cap2"],
  "reasoning": "为什么这样判断"
}}

可用意图类别: {list(self.categories.keys())}

用户消息: "{text[:500]}"
"""
        try:
            data = json.dumps({
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "你是意图识别引擎。只返回JSON，不返回其他内容。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.1
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{BASE_URL}/chat/completions",
                data=data,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
            content = resp["choices"][0]["message"]["content"]
            return json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        except Exception as e:
            import traceback, sys
            print(f"[IntentBroker] LLM分析失败: {e}", file=sys.stderr)
            return self._keyword_analyze(text)

    def _keyword_analyze(self, text: str) -> dict:
        """关键词匹配回退方案"""
        t = text.lower()
        kw_map = {
            "code_write":    ["写", "编写", "创建", "实现", "开发", "写代码", "coding", "write code"],
            "code_review":   ["审查", "review", "检查代码", "code review", "审计"],
            "code_debug":    ["调试", "debug", "修bug", "报错", "错误", "修复"],
            "code_refactor": ["重构", "refactor", "优化代码", "改进"],
            "code_explain":  ["解释", "这是什么", "什么意思", "explain", "说明"],
            "design":        ["设计", "架构", "方案", "design", "规划"],
            "reason":        ["推理", "分析", "思考", "reason", "think", "为什么"],
            "learn":         ["学习", "了解", "查询", "搜索", "learn", "search"],
            "plan":          ["计划", "规划", "安排", "plan", "任务"],
            "chat":          ["你好", "聊天", "hi", "hello", "怎么样"],
        }
        for intent, keywords in kw_map.items():
            if any(kw in t for kw in keywords):
                return {
                    "intent": intent,
                    "confidence": 0.5,
                    "breakdown": {
                        "layer1_domain": self.categories[intent]["desc"],
                        "layer2_action": intent,
                        "layer3_target": "unknown",
                        "layer4_params": {}
                    },
                    "suggested_caps": self.categories[intent]["caps"],
                    "reasoning": f"关键词匹配: {intent}",
                    "mode": "keyword"
                }
        return {"intent": "chat", "confidence": 0.3, "suggested_caps": ["cloud_llm"], "mode": "fallback"}

    def route(self, intent_result: dict) -> dict:
        """根据意图结果路由到能力模块 — 经邻域中枢验证"""
        intent = intent_result.get("intent", "chat")
        caps = intent_result.get("suggested_caps", ["cloud_llm"])
        
        # 只有这三个 cap 在目录级别带 gbt_ 前缀（且来源可能已带或未带）
        _GBT_PREFIXED = {"brain", "writer", "gigs"}

        def _fix_prefix(cap: str, prefixed: set) -> str:
            """仅在需要且尚未带前缀时添加 gbt_"""
            if cap.startswith("gbt_"):
                return cap
            return f"gbt_{cap}" if cap in prefixed else cap
        
        # 通过邻域神经系统验证路由
        try:
            from brain.nexus import get_nexus
            nexus = get_nexus()
            nexus_route = nexus.route(intent)
            # 邻域路由优先
            return {
                "caps": [_fix_prefix(c, _GBT_PREFIXED) for c in nexus_route["caps"]],
                "primary": _fix_prefix(nexus_route['primary'], _GBT_PREFIXED),
                "domain": nexus_route["domain"],
                "nexus_verified": True
            }
        except Exception:
            import traceback, sys
            traceback.print_exc(file=sys.stderr)
            return {
                "caps": [_fix_prefix(c, _GBT_PREFIXED) for c in caps],
                "primary": _fix_prefix(caps[0], _GBT_PREFIXED),
                "nexus_verified": False
            }


# 全局单例
_broker: IntentBroker | None = None

def get_broker() -> IntentBroker:
    global _broker
    if _broker is None:
        _broker = IntentBroker()
    return _broker


if __name__ == "__main__":
    import sys
    broker = IntentBroker()
    text = sys.argv[1] if len(sys.argv) > 1 else "帮我写一个排序算法"
    result = broker.analyze(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
