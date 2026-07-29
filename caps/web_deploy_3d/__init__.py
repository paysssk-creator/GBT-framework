"""
GBT 网页部署 Cap — 自动注入 3D 设计规范
当 AI 生成/部署网页时，自动加载 GBT-3D-DESIGN.md 作为设计上下文
"""
import json, os
from pathlib import Path

CAP_NAME = "web_deploy_3d"
CAP_DIR = Path(__file__).parent
DESIGN_DOC = CAP_DIR.parent.parent / "web" / "docs" / "GBT-3D-DESIGN.md"

def get_design_context():
    """返回 AI 设计网页时必须遵守的 3D 规范 + 开源视觉栈"""
    if DESIGN_DOC.exists():
        return DESIGN_DOC.read_text(encoding="utf-8")
    return """
# GBT 3D 快速参考 (v3)

## 技术栈
| 功能 | 方案 | 协议 |
|---|---|---|
| 3D渲染 | Three.js / R3F | MIT |
| 3D建模 | Blender → .glb | GPL |
| UI | Shadcn/ui / gbt-card | MIT |
| 动画 | Framer Motion / CSS Scroll-Driven | MIT |
| AI编程 | VS Code + Continue + DeepSeek | Apache 2.0 |

## Vanilla 标签
- 粒子环: <div data-gbt3d="particles" data-count="2500" data-color="#00d4ff" data-rings="4">
- 3D地球: <div data-gbt3d="globe" data-markers="北京,116.4,39.9">
- GLB模型: <div data-gbt3d="model" data-model-src="/assets/models/earth.glb">
- 滚动入场: class="gbt-reveal" (CSS Scroll-Driven, 零JS)
- 鼠标视差: data-parallax data-parallax-depth="2"
- 必须引入: <script src="/assets/gbt-3d.js" defer></script>
- CSS动画: <link rel="stylesheet" href="/assets/gbt-animations.css">

## React 组件
- import { ParticleRing, DataGlobe, ScrollReveal, GlassCard } from './gbt-3d-react'

## 颜色
科技蓝#00d4ff 金色#ffd700 紫色#a855f7 绿色#22c55e 红色#ff4444
""".strip()

def manifest():
    return {
        "name": CAP_NAME,
        "version": "1.0.0",
        "description": "GBT 3D 网页部署 — 粒子环·3D地球·视差·滚动动画",
        "entry": "get_design_context",
        "category": "AI创作",
        "risk": "safe",
        "status": "core",
    }

if __name__ == "__main__":
    print(json.dumps(manifest(), ensure_ascii=False, indent=2))
