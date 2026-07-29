# -*- coding: utf-8 -*-
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/visual_cortex.py -- 视觉皮层 · 三层结构视觉引擎
========================================================
AI不是"看像素"，而是"编译结构"。

三层视觉模型:
  L1 组件架构层 -- 识别声明式组件、Props绑定、数据流合同
  L2 渲染管线层 -- 分析 DOM→CSS→JS→GPU 性能漏斗
  L3 行为叙事层 -- 分析用户注意力漏斗：吸引→阐述→转化

输入: 屏幕OCR文本 + HTML源码
输出: 结构化的视觉理解报告
"""
import json, re, time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent


class VisualCortex:
    """视觉皮层 -- 三层结构视觉分析引擎
    
    不分析颜色/光影/美学。分析的是:
      - 组件合同 (data-* → props → JS引擎)
      - 渲染管线 (HTML比重 → CSS开销 → JS负载 → GPU压力)
      - 行为叙事 (首屏→滚动→CTA 注意力漏斗)
    """

    def __init__(self):
        self._last_analysis: dict = {}
        self._page_cache: dict = {}

    # ═══════════════ L1: 组件架构层 ═══════════════

    def analyze_components(self, html: str) -> dict:
        """识别声明式组件实例及其Props绑定

        从HTML中提取:
          - data-gbt3d="..." → 3D组件实例
          - class="gbt-*"    → 动画组件实例
          - data-* 属性      → Props输入
          - 组件间的父子/兄弟关系
        """
        result = {
            "layer": 1,
            "name": "组件架构层",
            "components": [],
            "props_map": {},
            "hierarchy": {},
        }

        # 识别 3D 组件
        pattern_3d = re.compile(
            r'<div[^>]*data-gbt3d="(\w+)"[^>]*>',
            re.IGNORECASE
        )
        for m in pattern_3d.finditer(html):
            tag = m.group(0)
            comp_type = m.group(1)
            props = self._extract_props(tag)
            result["components"].append({
                "type": f"gbt3d:{comp_type}",
                "props": props,
                "declarative": True,
                "engine": "gbt-3d.js" if comp_type in ("particles","globe","model") else "native",
            })

        # 识别动画组件
        anim_classes = {
            "gbt-reveal": "ScrollReveal",
            "gbt-reveal-left": "SlideLeft",
            "gbt-reveal-right": "SlideRight",
            "gbt-reveal-scale": "ScaleIn",
            "gbt-float": "Float",
            "gbt-pulse-glow": "PulseGlow",
            "gbt-spin-slow": "SpinSlow",
            "gbt-gradient-text": "GradientText",
            "gbt-card": "GlassCard",
        }
        for cls_name, comp_name in anim_classes.items():
            pattern = re.compile(
                rf'class="[^"]*\b{cls_name}\b[^"]*"',
                re.IGNORECASE
            )
            matches = pattern.findall(html)
            if matches:
                result["components"].append({
                    "type": f"animation:{comp_name}",
                    "count": len(matches),
                    "declarative": True,
                    "engine": "gbt-animations.css" if cls_name.startswith("gbt-") else "gbt-3d.js",
                })

        # 识别 Parallax 组件
        parallax_matches = re.findall(
            r'<[^>]*data-parallax[^>]*data-parallax-depth="(\d+)"[^>]*>',
            html, re.IGNORECASE
        )
        if parallax_matches:
            result["components"].append({
                "type": "interaction:Parallax",
                "count": len(parallax_matches),
                "props": {"depth": [int(d) for d in parallax_matches]},
                "declarative": True,
                "engine": "gbt-3d.js",
            })

        # 识别 Beam 组件
        beam_matches = re.findall(
            r'data-beam="from:\s*([^,]+),\s*to:\s*([^"]+)"',
            html, re.IGNORECASE
        )
        if beam_matches:
            result["components"].append({
                "type": "interaction:Beam",
                "count": len(beam_matches),
                "connections": [{"from": f.strip(), "to": t.strip()} for f, t in beam_matches],
                "declarative": True,
                "engine": "gbt-3d.js (SVG overlay)",
            })

        result["total_components"] = len(result["components"])
        return result

    def _extract_props(self, tag: str) -> dict:
        """从HTML标签提取所有data-*属性作为Props"""
        props = {}
        for m in re.finditer(r'data-(\w[\w-]*)\s*=\s*"([^"]*)"', tag, re.IGNORECASE):
            key = m.group(1)
            val = m.group(2)
            # 类型推断
            if val.isdigit():
                props[key] = int(val)
            elif re.match(r'^-?\d+\.?\d*$', val):
                props[key] = float(val)
            elif val in ("true", "false"):
                props[key] = val == "true"
            else:
                props[key] = val
        return props

    # ═══════════════ L2: 渲染管线层 ═══════════════

    def analyze_pipeline(self, html: str) -> dict:
        """分析渲染管线压力分布

        四步流水线:
          DOM结构  → 标签数量/深度
          样式层   → CSS选择器复杂度
          交互逻辑 → JS事件监听/动画循环
          渲染帧   → GPU粒子数/几何体数
        """
        result = {
            "layer": 2,
            "name": "渲染管线层",
            "pipeline": {},
            "bottlenecks": [],
            "mobile_risk": "low",
        }

        # DOM 层
        tag_count = len(re.findall(r'<\w+', html))
        div_depth = self._estimate_depth(html)
        result["pipeline"]["dom"] = {
            "tag_count": tag_count,
            "estimated_depth": div_depth,
            "weight": "heavy" if tag_count > 500 else "normal",
        }

        # CSS 层
        css_refs = len(re.findall(r'<link[^>]*stylesheet[^>]*>', html, re.IGNORECASE))
        inline_style = len(re.findall(r'<style[^>]*>', html, re.IGNORECASE))
        result["pipeline"]["css"] = {
            "external_sheets": css_refs,
            "inline_blocks": inline_style,
            "weight": "normal",
        }

        # JS 层
        script_count = len(re.findall(r'<script[^>]*>', html, re.IGNORECASE))
        has_gbt3d = 'gbt-3d.js' in html
        has_three = 'three' in html.lower()
        has_r3f = 'react-three-fiber' in html.lower() or 'R3F' in html
        result["pipeline"]["js"] = {
            "script_tags": script_count,
            "gbt3d_loaded": has_gbt3d,
            "threejs_loaded": has_three,
            "react_r3f": has_r3f,
            "weight": "heavy" if (has_three or has_r3f) and script_count > 3 else "normal",
        }

        # GPU 层
        particles_total = 0
        for m in re.finditer(r'data-count="(\d+)"', html):
            particles_total += int(m.group(1))
        globe_count = len(re.findall(r'data-gbt3d="globe"', html))
        model_count = len(re.findall(r'data-gbt3d="model"', html))

        gpu_load = particles_total + globe_count * 500 + model_count * 1000
        result["pipeline"]["gpu"] = {
            "estimated_particles": particles_total,
            "globe_instances": globe_count,
            "model_instances": model_count,
            "total_gpu_load": gpu_load,
            "weight": "critical" if gpu_load > 3000 else ("heavy" if gpu_load > 1500 else "normal"),
        }

        # 瓶颈检测
        if gpu_load > 3000:
            result["bottlenecks"].append({
                "stage": "GPU",
                "issue": f"粒子+几何体总量{gpu_load}超过3000",
                "fix": "移动端 data-count 自动降到600, 环数降到2 (gbt-3d.js 已内置)",
                "severity": "high",
            })
        if tag_count > 500:
            result["bottlenecks"].append({
                "stage": "DOM",
                "issue": f"标签数{tag_count}偏高",
                "fix": "考虑懒加载或虚拟滚动",
                "severity": "medium",
            })

        # 移动端风险评估
        if gpu_load > 3000 and not ('IS_MOBILE' in html or 'mobile' in html.lower()):
            result["mobile_risk"] = "high"
            result["bottlenecks"].append({
                "stage": "Mobile",
                "issue": "GPU负载高但无移动端降级逻辑",
                "fix": "引入 gbt-3d.js 自动降级 (粒子≤600, 视差禁用, pixelRatio=1)",
                "severity": "critical",
            })

        return result

    def _estimate_depth(self, html: str) -> int:
        """估算DOM树最大深度"""
        max_depth = 0
        current = 0
        for line in html.split('\n'):
            stripped = line.lstrip()
            if stripped.startswith('</'):
                current -= 1
            elif stripped.startswith('<') and not stripped.startswith('<!'):
                current += 1
                max_depth = max(max_depth, current)
            elif stripped.startswith('<!--'):
                pass
        return max_depth

    # ═══════════════ L3: 行为叙事层 ═══════════════

    def analyze_narrative(self, html: str) -> dict:
        """分析用户注意力漏斗

        阶段1 吸引: 首屏3D元素 + 大标题
        阶段2 阐述: 滚动入场动画序列
        阶段3 转化: 视差引导 + 光束指向CTA
        """
        result = {
            "layer": 3,
            "name": "行为叙事层",
            "funnel": {},
            "score": 0,
            "suggestions": [],
        }

        # 阶段1: 吸引
        has_particles = bool(re.search(r'data-gbt3d="particles"', html))
        has_globe = bool(re.search(r'data-gbt3d="globe"', html))
        has_hero = bool(re.search(r'<h1[^>]*>', html))
        result["funnel"]["attract"] = {
            "particles": has_particles,
            "globe_3d": has_globe,
            "hero_title": has_hero,
            "score": (2 if has_particles else 0) + (3 if has_globe else 0) + (1 if has_hero else 0),
            "max": 6,
        }

        # 阶段2: 阐述
        reveal_count = len(re.findall(r'class="[^"]*gbt-reveal[^"]*"', html))
        has_stagger = 'stagger' in html.lower() or 'gbt-reveal:nth-child' in html
        result["funnel"]["explain"] = {
            "reveal_elements": reveal_count,
            "has_stagger": has_stagger,
            "score": min(reveal_count, 5) + (2 if has_stagger else 0),
            "max": 7,
        }

        # 阶段3: 转化
        has_parallax = bool(re.search(r'data-parallax', html))
        has_beam = bool(re.search(r'data-beam', html))
        has_cta = bool(re.search(r'(?i)(cta|call.to.action|get.started|sign.up|buy.now|立即|马上)', html))
        result["funnel"]["convert"] = {
            "parallax": has_parallax,
            "beams": has_beam,
            "cta_present": has_cta,
            "score": (2 if has_parallax else 0) + (3 if has_beam else 0) + (2 if has_cta else 0),
            "max": 7,
        }

        # 总评分
        scores = result["funnel"]
        total = scores["attract"]["score"] + scores["explain"]["score"] + scores["convert"]["score"]
        max_total = scores["attract"]["max"] + scores["explain"]["max"] + scores["convert"]["max"]
        result["score"] = round(total / max_total * 100, 1)

        # 建议
        if not has_particles and not has_globe:
            result["suggestions"].append({
                "stage": "attract",
                "action": "首屏缺少3D焦点。添加 <div data-gbt3d=\"particles\"> 或 <div data-gbt3d=\"globe\">",
            })
        if reveal_count < 3:
            result["suggestions"].append({
                "stage": "explain",
                "action": "滚动叙事元素不足。为关键内容添加 class=\"gbt-reveal\"",
            })
        if not has_beam and has_globe and has_cta:
            result["suggestions"].append({
                "stage": "convert",
                "action": "地球和CTA之间缺少视觉引导。添加 <div data-beam=\"from:#globe, to:#cta\">",
            })

        return result

    # ═══════════════ 全栈分析 ═══════════════

    def analyze_page(self, html: str, url: str = "") -> dict:
        """三层全栈分析 -- 一次调用输出完整视觉理解报告"""
        t0 = time.time()

        l1 = self.analyze_components(html)
        l2 = self.analyze_pipeline(html)
        l3 = self.analyze_narrative(html)

        report = {
            "url": url,
            "timestamp": time.time(),
            "analysis_time_ms": round((time.time() - t0) * 1000),
            "html_size_kb": round(len(html) / 1024, 1),
            "layers": {
                "L1_architecture": l1,
                "L2_pipeline": l2,
                "L3_narrative": l3,
            },
            "summary": {
                "components": l1["total_components"],
                "gpu_load": l2["pipeline"]["gpu"]["total_gpu_load"],
                "mobile_risk": l2["mobile_risk"],
                "narrative_score": l3["score"],
                "bottlenecks": len(l2["bottlenecks"]),
                "suggestions": len(l3["suggestions"]),
            },
            "verdict": self._verdict(l1, l2, l3),
        }

        self._last_analysis = report
        if url:
            self._page_cache[url] = report

        return report

    def _verdict(self, l1: dict, l2: dict, l3: dict) -> str:
        """综合判定"""
        issues = []
        if l1["total_components"] == 0:
            issues.append("无声明式组件")
        if l2["mobile_risk"] == "high":
            issues.append("移动端高风险")
        if l2["bottlenecks"]:
            issues.append(f'{len(l2["bottlenecks"])}个性能瓶颈')
        if l3["score"] < 40:
            issues.append(f'叙事评分低({l3["score"]}%)')

        if not issues:
            return "生产级: 组件声明完备, 性能达标, 叙事结构完整"
        return f"需优化: {'; '.join(issues)}"

    # ═══════════════ 屏幕视觉分析 ═══════════════

    def analyze_screen(self) -> dict:
        """分析当前屏幕 -- 通过OCR+视觉皮层理解屏幕上有什么"""
        try:
            from brain.host_body import eyes
            ocr_result = eyes.read_all()
            if not ocr_result.get("ok"):
                return {"error": "OCR失败", "detail": ocr_result.get("error", "")}

            text_blocks = ocr_result.get("text_blocks", [])
            full_text = " ".join(b["text"] for b in text_blocks)

            # L1: 从OCR文本推断组件
            component_hints = []
            if re.search(r'(?i)3d|particle|globe|模型', full_text):
                component_hints.append("3D组件")
            if re.search(r'(?i)button|btn|按钮|点击|提交|登录|注册', full_text):
                component_hints.append("交互控件")
            if re.search(r'(?i)chart|graph|图表|数据|统计', full_text):
                component_hints.append("数据可视化")

            # L2: 屏幕区域密度
            screen_zones = {
                "top": {"blocks": 0, "density": 0},
                "middle": {"blocks": 0, "density": 0},
                "bottom": {"blocks": 0, "density": 0},
            }
            for b in text_blocks:
                y = b.get("y", 0)
                if y < 200:
                    screen_zones["top"]["blocks"] += 1
                elif y < 700:
                    screen_zones["middle"]["blocks"] += 1
                else:
                    screen_zones["bottom"]["blocks"] += 1

            total = len(text_blocks) or 1
            for zone in screen_zones:
                screen_zones[zone]["density"] = round(screen_zones[zone]["blocks"] / total * 100)

            # L3: 推断当前任务
            task_hints = []
            if re.search(r'(?i)code|coding|编程|代码|python|js|html|css', full_text):
                task_hints.append("编程")
            if re.search(r'(?i)chat|对话|聊天|deepseek|gpt|claude', full_text):
                task_hints.append("AI对话")
            if re.search(r'(?i)browser|chrome|edge|标签|tab', full_text):
                task_hints.append("浏览网页")
            if re.search(r'(?i)trade|交易|股票|stock|买入|卖出', full_text):
                task_hints.append("交易")

            return {
                "ok": True,
                "total_blocks": total,
                "screen_zones": screen_zones,
                "component_hints": component_hints,
                "task_inference": task_hints or ["未知"],
                "text_sample": full_text[:200],
            }

        except Exception as e:
            return {"error": str(e)}

    # ═══════════════ 集成设计脑 ═══════════════

    def patrol_visual_health(self) -> dict:
        """视觉皮层巡检 -- 检查视觉系统各层是否正常"""
        result = {
            "timestamp": time.time(),
            "eyes": {"ok": False, "detail": ""},
            "ocr": {"ok": False, "detail": ""},
            "cortex": {"ok": True, "layers": 3},
        }

        try:
            from brain.host_body import eyes
            see_result = eyes.see()
            result["eyes"]["ok"] = see_result.get("ok", False)
            result["eyes"]["detail"] = f'截屏{"成功" if result["eyes"]["ok"] else "失败"}'
        except Exception as e:
            result["eyes"]["detail"] = str(e)[:100]

        try:
            ocr = self.analyze_screen()
            result["ocr"]["ok"] = ocr.get("ok", False)
            result["ocr"]["detail"] = f'识别{ocr.get("total_blocks",0)}个文字块'
            if ocr.get("task_inference"):
                result["ocr"]["task_inference"] = ocr["task_inference"]
        except Exception as e:
            result["ocr"]["detail"] = str(e)[:100]

        result["all_ok"] = result["eyes"]["ok"] and result["ocr"]["ok"]
        return result


# ═══════════════ 全局单例 ═══════════════

_cortex: Optional[VisualCortex] = None


def get_cortex() -> VisualCortex:
    global _cortex
    if _cortex is None:
        _cortex = VisualCortex()
    return _cortex


def analyze_html(html: str, url: str = "") -> dict:
    """快捷: 三层全栈HTML分析"""
    return get_cortex().analyze_page(html, url)


def analyze_current_screen() -> dict:
    """快捷: 分析当前屏幕"""
    return get_cortex().analyze_screen()


if __name__ == "__main__":
    import sys
    cortex = VisualCortex()

    if len(sys.argv) > 1 and sys.argv[1] == "screen":
        print(json.dumps(cortex.analyze_screen(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1:
        html = Path(sys.argv[1]).read_text(encoding="utf-8")
        print(json.dumps(cortex.analyze_page(html, sys.argv[1]), ensure_ascii=False, indent=2))
    else:
        # 测试: 分析一个模拟的页面
        test_html = """
        <div data-gbt3d="particles" data-count="2000" data-color="#00d4ff" data-rings="3"></div>
        <div data-gbt3d="globe" data-markers="/api/nodes" data-marker-interval="3000"></div>
        <h1 class="gbt-gradient-text">Welcome</h1>
        <div class="gbt-reveal gbt-card">Feature 1</div>
        <div class="gbt-reveal gbt-card">Feature 2</div>
        <div class="gbt-reveal gbt-card">Feature 3</div>
        <div data-parallax data-parallax-depth="2">CTA Section</div>
        <div data-beam="from: #globe, to: #cta-button"></div>
        <button id="cta-button">Get Started</button>
        <script src="/assets/gbt-3d.js" defer></script>
        <link rel="stylesheet" href="/assets/gbt-animations.css">
        """
        report = cortex.analyze_page(test_html, "test-page")
        print(json.dumps(report, ensure_ascii=False, indent=2))
