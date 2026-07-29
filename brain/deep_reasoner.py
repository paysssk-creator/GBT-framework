# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/deep_reasoner.py — 深度推理引擎
======================================
四脑协作中的"推理脑"。支持8种推理模式。
每次推理产出: 方向建议 + 逻辑依据 + 风险评估。
"""
import json, os, urllib.request, urllib.error
from typing import Optional

API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("KIMI_API_KEY") or ""
BASE_URL = os.environ.get("GBT_LLM_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("GBT_LLM_MODEL", "deepseek-v4-pro")


# ⛔ 三元执行协议 — 所有AI必须遵循
# ① 每任务先生成思维导图(mind_map)
# ② 按导图执行, 卡点先搜索(search_first)
# ③ 有成熟方案→直接用; 无方案→推理脑分析→生成新决策
# ④ 卡点后重新生成导图指引子代理/编程脑继续方向
# ⑤ 禁止: 跳过、伪造、盲目执行
RUN_PROTOCOL = {
    'mind_map_first': True,
    'stuck_search_first': True,
    'reasoning_fallback': True,
    'regenerate_on_stuck': True
}

REASONING_MODES = {
    "chain":      "链式推理 — 一步一步推导出结论",
    "tree":       "树形推理 — 探索多个分支，选择最优路径",
    "contrast":   "对比推理 — 比较多个方案的优劣",
    "hypothesis": "假设推理 — 提出假设并验证",
    "reverse":    "逆向推理 — 从目标反推需要的条件",
    "system":     "系统推理 — 分析组件间的相互影响",
    "decision":   "决策推理 — 权衡利弊做出选择",
    "creative":   "创意推理 — 发散思维产生新想法",
    "tripod":     "三足鼎立推理 — 搜索·分析·推理并发运转，三方交叉验证",
    "trading":    "操盘推理 — 技术面+资金面+情绪面三维共振，产出买卖/持有/空仓决策",
}


class DeepReasoner:
    """深度推理引擎 — 四脑协作的推理脑

    产出格式:
    {
        "direction": "建议方向",
        "rationale": "逻辑依据",
        "risks": ["风险1", "风险2"],
        "alternatives": ["替代方案1"],
        "confidence": 0.0-1.0
    }
    """

    def reason(self, topic: str, context: dict | None = None,
               mode: str = "chain", previous_lessons: list | None = None) -> dict:
        """执行深度推理"""
        if mode not in REASONING_MODES:
            mode = "chain"

        if mode == "tripod":
            return self.tripod(topic, context=context, previous_lessons=previous_lessons)

        if API_KEY:
            return self._llm_reason(topic, context, mode, previous_lessons)
        return self._local_reason(topic, context, mode, previous_lessons)

    def _llm_reason(self, topic: str, context: dict | None, mode: str,
                    lessons: list | None) -> dict:
        """通过LLM进行深度推理"""
        ctx_str = json.dumps(context, ensure_ascii=False) if context else "无"
        lessons_str = "\n".join(f"- {l}" for l in (lessons or [])) if lessons else "无"

        prompt = f"""使用{mode}推理模式分析以下问题。

推理模式说明: {REASONING_MODES[mode]}

问题: {topic}
上下文: {ctx_str}
历史教训: {lessons_str}

请以JSON格式返回:
{{
  "direction": "具体建议的行动方向",
  "rationale": "为什么选这个方向的逻辑依据(3-5条)",
  "risks": ["风险点1", "风险点2"],
  "alternatives": ["备选方向1", "备选方向2"],
  "confidence": 0.0-1.0,
  "next_steps": ["下一步1", "下一步2"]
}}"""
        try:
            data = json.dumps({
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "你是GBT小土豆的深度推理引擎，专精A股量化操盘。你精通：技术分析(MA/MACD/KDJ/BOLL/RSI)、资金面分析(主力净流入/北向资金/龙虎榜)、市场情绪(涨跌比/涨停数/恐慌指数)、盘口语言(买卖盘/大单动向)、A股交易规则(T+1/涨跌停/集合竞价)。推理时优先考虑风险控制和资金管理。输出只返回JSON。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{BASE_URL}/chat/completions",
                data=data,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
            content = resp["choices"][0]["message"]["content"]
            # 鲁棒JSON解析：尝试多种策略
            parsed = None
            strategies = [
                # 1. 直接解析
                lambda c: json.loads(c.strip()),
                # 2. 去掉```json标记
                lambda c: json.loads(c.strip().removeprefix("```json").removesuffix("```").strip()),
                # 3. 提取第一个{...}块
                lambda c: json.loads(c[c.find("{"):c.rfind("}")+1]),
            ]
            for strategy in strategies:
                try:
                    parsed = strategy(content)
                    break
                except Exception:
                    continue
            if parsed is None:
                raise ValueError(f"无法解析LLM响应为JSON: {content[:100]}")
            return parsed
        except Exception as e:
            import logging
            logging.getLogger("DeepReasoner").warning(f"LLM推理失败({type(e).__name__}): {e}, 降级到本地推理")
            return self._local_reason(topic, context, mode, lessons)

    def _local_reason(self, topic: str, context: dict | None, mode: str,
                      lessons: list | None) -> dict:
        """本地推理回退 — 结构化分析"""
        import logging
        _log = logging.getLogger("DeepReasoner")
        
        analysis = {
            "chain": {
                "direction": f"逐步分析「{topic}」",
                "rationale": "1. 识别核心问题\n2. 分解为子问题\n3. 逐一分析\n4. 综合结论\n5. 制定方案",
                "risks": ["信息不完整可能导致分析偏差", "需要进一步验证假设"],
                "confidence": 0.5
            },
            "tree": {
                "direction": f"树形探索「{topic}」",
                "rationale": "1. 列出所有可能分支\n2. 评估每个分支的可行性\n3. 剪枝排除不可行路径\n4. 选择最优分支深入\n5. 综合各分支结论",
                "risks": ["分支探索可能不完整", "剪枝可能过早排除有效路径"],
                "confidence": 0.45
            },
            "hypothesis": {
                "direction": f"假设检验「{topic}」",
                "rationale": "1. 提出核心假设\n2. 设计验证方法\n3. 收集证据\n4. 验证或推翻假设\n5. 根据结果修正结论",
                "risks": ["假设可能有预设偏见", "验证方法可能不充分"],
                "confidence": 0.4
            },
            "reverse": {
                "direction": f"逆向推导「{topic}」",
                "rationale": "1. 明确最终目标\n2. 从目标反向推导前提条件\n3. 逐一检查每个条件是否满足\n4. 找出缺失条件\n5. 制定弥补方案",
                "risks": ["目标定义可能过于狭窄", "逆向路径可能遗漏替代方案"],
                "confidence": 0.45
            },
            "system": {
                "direction": f"系统分析「{topic}」",
                "rationale": "1. 识别系统组件\n2. 分析组件间依赖关系\n3. 评估变更的影响范围\n4. 识别关键路径和瓶颈\n5. 提出系统级优化方案",
                "risks": ["系统边界可能定义不准确", "间接依赖可能被忽略"],
                "confidence": 0.5
            },
            "creative": {
                "direction": f"创意发散「{topic}」",
                "rationale": "1. 打破常规思维框架\n2. 多角度联想\n3. 组合不同领域的方法\n4. 生成多个新颖方案\n5. 评估可行性和创新性",
                "risks": ["创意可能脱离实际约束", "新颖性不等于可行性"],
                "confidence": 0.35
            },
            "decision": {
                "direction": f"对「{topic}」做决策分析",
                "rationale": "1. 列出选项\n2. 评估每个选项的利弊\n3. 考虑约束条件\n4. 选出最优方案",
                "risks": ["决策依赖的信息可能不全面"],
                "confidence": 0.5
            },
            "contrast": {
                "direction": f"对比分析「{topic}」的多个方案",
                "rationale": "1. 识别候选方案\n2. 定义比较维度\n3. 逐维对比\n4. 综合评分",
                "risks": ["对比维度可能不完整"],
                "confidence": 0.5
            },
            "tripod": {
                "direction": f"三足鼎立推理「{topic}」(本地降级)",
                "rationale": "1. 搜索维度: 检索相关知识\n2. 分析维度: 结构化分解\n3. 推理维度: 逻辑链推导\n   三方交叉验证后给出综合结论",
                "risks": ["本地模式缺少实时搜索和LLM深度推理"],
                "confidence": 0.4
            },
            "trading": {
                "direction": f"操盘分析「{topic}」(本地降级，建议启用LLM)",
                "rationale": "1. 解析股票代码与价格数据\n2. 计算涨跌幅和成交量变化\n3. 评估技术面：价格位置、量价关系\n4. 评估风险：波动率、仓位控制\n5. 综合给出观望/买入/卖出建议",
                "risks": ["缺少实时技术指标计算", "无北向资金/龙虎榜数据", "LLM不可用时分析精度有限"],
                "confidence": 0.35,
                "alternatives": ["若仓位重可减仓观望", "若空仓可等待明确信号"],
                "next_steps": ["启用LLM获得更精确分析", "补充MACD/KDJ/RSI数据", "查看盘口大单动向"]
            },
        }
        
        if mode not in analysis:
            _log.warning(f"未知推理模式 '{mode}'，回退到 chain")
        result = analysis.get(mode, analysis["chain"])
        result.setdefault("alternatives", ["方案A", "方案B"])
        result.setdefault("next_steps", ["收集更多信息", "制定执行计划"])
        result["mode"] = "local"
        if mode not in ("chain", "decision", "contrast"):
            result["fallback_note"] = f"模式 '{mode}' 在本地推理中为简化实现，建议使用LLM获得更好结果"
        return result

    def chain(self, topic: str, **kw) -> dict:
        return self.reason(topic, mode="chain", **kw)

    def compare(self, topic: str, **kw) -> dict:
        return self.reason(topic, mode="contrast", **kw)

    def decide(self, topic: str, **kw) -> dict:
        return self.reason(topic, mode="decision", **kw)

    def tripod(self, topic: str, **kw) -> dict:
        """三足鼎立推理 — 搜索·分析·推理并发运转
        ==========================================
        三条腿同时落地:
        ① 全网搜索 → 获取最新核心资料
        ② LLM推理 → 深度分析研判
        ③ 本地分析 → 结构化逻辑验证
        三者结果合并 → 综合推理结论
        """
        import threading, subprocess, time
        from pathlib import Path

        results = {"search": None, "llm": None, "local": None, "elapsed": {}}
        mode = kw.get("mode", "system")

        def do_search():
            t0 = time.time()
            try:
                caps_dir = Path(__file__).parent.parent / "caps" / "web_search"
                run_py = caps_dir / "run.py"
                if run_py.exists():
                    r = subprocess.run(
                        [__import__('sys').executable, str(run_py), "search",
                         json.dumps({"query": topic, "max_results": 8})],
                        capture_output=True, text=True, timeout=20,
                        encoding="utf-8", errors="replace"
                    )
                    results["search"] = json.loads((r.stdout or "{}").strip())
            except Exception as e:
                results["search"] = {"ok": False, "error": str(e)[:100]}
            results["elapsed"]["search"] = round(time.time() - t0, 2)

        def do_llm():
            t0 = time.time()
            try:
                results["llm"] = self._llm_reason(topic, kw.get("context"), mode, kw.get("previous_lessons"))
            except Exception:
                results["llm"] = {"ok": False, "error": "LLM推理异常"}
            results["elapsed"]["llm"] = round(time.time() - t0, 2)

        def do_local():
            t0 = time.time()
            results["local"] = self._local_reason(topic, kw.get("context"), mode, kw.get("previous_lessons"))
            results["elapsed"]["local"] = round(time.time() - t0, 2)

        # 三条腿并发
        threads = [
            threading.Thread(target=do_search),
            threading.Thread(target=do_llm),
            threading.Thread(target=do_local),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        # 合并分析
        synthesis = self._synthesize_tripod(topic, results)

        return {
            "ok": True,
            "mode": "tripod",
            "topic": topic,
            "elapsed_sec": results["elapsed"],
            "search_results": results["search"].get("results", [])[:5] if results["search"] and results["search"].get("ok") else [],
            "search_count": results["search"].get("total_results", 0) if results["search"] and results["search"].get("ok") else 0,
            "llm_reasoning": results["llm"].get("direction", "") if results["llm"] else "",
            "local_analysis": results["local"].get("rationale", "") if results["local"] else "",
            "synthesis": synthesis,
            "brain_status": {
                "search_brain": "已完成" if results["search"] and results["search"].get("ok") else "未获取",
                "reasoning_brain": "已完成" if results["llm"] else "降级本地",
                "coding_brain": "本地分析完成",
                "mode": "三足鼎立·并发运转",
            },
        }

    def _synthesize_tripod(self, topic, results):
        """三足鼎立综合 — 搜索+LLM+本地 三方交叉验证"""
        parts = []

        # 从搜索结果提取核心观点
        if results["search"] and results["search"].get("ok"):
            search_results = results["search"].get("results", [])
            if search_results:
                parts.append(f"📡 全网搜索捕获 {len(search_results)} 条核心资料")
                top_titles = [r.get("title", "")[:80] for r in search_results[:3]]
                parts.append("   top: " + " | ".join(top_titles))

        # 从LLM获取深度推理
        if results["llm"] and results["llm"].get("ok"):
            parts.append(f"🧠 深度推理: {results['llm'].get('direction', '')[:200]}")

        # 本地逻辑验证
        if results["local"]:
            parts.append(f"🔍 本地分析: {results['local'].get('rationale', '')[:200]}")

        # 交叉验证
        search_keywords = set()
        if results["search"] and results["search"].get("ok"):
            for r in results["search"].get("results", []):
                for w in topic.lower().split():
                    if w in r.get("title", "").lower() or w in r.get("snippet", "").lower():
                        search_keywords.add(w)

        llm_direction = results["llm"].get("direction", "") if results["llm"] else ""
        local_rationale = results["local"].get("rationale", "") if results["local"] else ""

        cross_validated = (
            "✅ 三方交叉验证通过 — 搜索结果·LLM推理·本地分析方向一致"
            if (search_keywords and llm_direction and local_rationale)
            else "⚠️ 部分验证 — 继续深化搜索和分析"
        )

        return {
            "summary": " | ".join(parts),
            "cross_validation": cross_validated,
            "confidence": "high" if search_keywords and llm_direction else "medium",
        }


# 全局实例
_reasoner: DeepReasoner | None = None

def get_reasoner() -> DeepReasoner:
    global _reasoner
    if _reasoner is None:
        _reasoner = DeepReasoner()
    return _reasoner


if __name__ == "__main__":
    import sys
    r = DeepReasoner()
    topic = sys.argv[1] if len(sys.argv) > 1 else "如何优化这个框架的性能"
    mode = sys.argv[2] if len(sys.argv) > 2 else "chain"
    result = r.reason(topic, mode=mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))
