# GBT 3D v2 部署规范 — AI 必读

框架已升级 v2，你的每一页自动拥有：

## 1. 粒子光环
```html
<div data-gbt3d="particles"
     data-count="2500"
     data-color="#00d4ff"
     data-rings="4"
     style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.6">
</div>
```
| 参数 | 默认 | 说明 |
|---|---|---|
| data-count | 2000 | 粒子数，手机自动降到600 |
| data-color | #00d4ff | 科技蓝/金#ffd700/紫#a855f7 |
| data-rings | 3 | 环数 1-5 |
| data-speed | 0.0005 | 旋转速度 |

## 2. 3D 动态数据地球（v2核心）
```html
<!-- 静态标记 -->
<div data-gbt3d="globe" data-markers="北京,116.4,39.9;纽约,-74,40.7;伦敦,-0.1,51.5"
     style="width:400px;height:400px;margin:0 auto;"></div>

<!-- 默认演示标记(4个城市) -->
<div data-gbt3d="globe" data-markers="true"></div>

<!-- 动态API模式 — 每3秒拉取实时数据 -->
<div data-gbt3d="globe" data-markers="/api/active-nodes" data-marker-interval="3000"></div>
```
API格式: `[{lat:39.9, lng:116.4, color: 0xff4444}, ...]` 或 `{markers: [...]}` 或 `{nodes: [...]}`

## 3. 光效连线（v2新增）
```html
<!-- 地球→CTA按钮 光束 -->
<div data-beam="from: #globe-container, to: #cta-button"
     data-beam-color="#00d4ff"
     data-beam-width="2"
     data-beam-dash="8,4">
</div>
```
自动跟随滚动——两端元素可见时光束出现，滚出视野自动消失。

## 4. 滚动入场
```html
<div class="gbt-reveal">从下方淡入</div>
```

## 5. 鼠标视差（移动端自动禁用）
```html
<div data-parallax data-parallax-depth="2">跟手浮动</div>
```

## 移动端保底（内置，零配置）
- 粒子数自动降到 ≤600
- 环数降到 ≤2
- 像素比锁在 1x
- 视差效果自动禁用
- 地球旋转减速 30%

## 颜色方案
科技蓝 #00d4ff | 金 #ffd700 | 紫 #a855f7 | 绿 #22c55e | 红 #ff4444
背景 #0a0a0f | 卡片 rgba(255,255,255,0.04) | 边框 rgba(255,255,255,0.08)

## 引入方式
```html
<script src="/assets/gbt-3d.js" defer></script>
```
index.html 已自动加载，新页面复制这一行即可。

---

# GBT 3D v3 — 开源视觉栈 (2026-07)

## 技术栈全景

| 功能 | 原方案 | 开源替代 | 协议 |
|---|---|---|---|
| 3D渲染 | Spline | **Three.js** (gbt-3d.js) / **R3F** (React) | MIT |
| 3D建模 | Spline编辑器 | **Blender** → .glb | GPL |
| UI组件 | V0.dev | **Shadcn/ui** (React) / **gbt-card** (CSS) | MIT |
| 动画引擎 | GSAP | **Framer Motion** (React) / **CSS Scroll-Driven** (Vanilla) | MIT |
| AI编程 | Cursor | **VS Code + Continue** + DeepSeek API | Apache 2.0 |

## 双轨架构

### 轨道1: Vanilla (零依赖)
```html
<script src="/assets/gbt-3d.js" defer></script>
<link rel="stylesheet" href="/assets/gbt-animations.css">
```
适用: 快速原型、静态页面、已有 HTML 项目

### 轨道2: React (现代栈)
```bash
npm install three @react-three/fiber @react-three/drei framer-motion
```
```jsx
import { ParticleRing, DataGlobe, ScrollReveal, GlassCard } from './gbt-3d-react';
```
适用: SPA、交互密集型页面、需要 Shadcn/ui 组件

## GLB 模型加载 (v3新增)
```html
<!-- Vanilla -->
<div data-gbt3d="model"
     data-model-src="/assets/models/earth.glb"
     data-model-scale="1.5"
     data-model-color="#00d4ff"
     data-model-speed="0.005">
</div>
```
```jsx
// React (R3F)
<Canvas>
  <GlobeScene modelUrl="/assets/models/earth.glb" color="#00d4ff" />
</Canvas>
```
**Blender建模流程**: 建模→上材质→导出.glb→放入 /assets/models/ → 一行标签加载

## CSS Scroll-Driven 动画 (v3新增, 零JS)
```html
<div class="gbt-reveal">从下方淡入</div>           <!-- 默认 -->
<div class="gbt-reveal-left">从左侧滑入</div>       <!-- 左右 -->
<div class="gbt-reveal-right">从右侧滑入</div>
<div class="gbt-reveal-scale">缩放弹入</div>
```
浏览器原生 `animation-timeline: view()` — Chrome 115+/Edge 115+。
不支持的浏览器自动回退到 IntersectionObserver (gbt-3d.js 处理)。

## gbt-animations.css 工具类
```html
<div class="gbt-float">浮动</div>           <!-- 3s ease-in-out -->
<div class="gbt-pulse-glow">脉冲发光</div>   <!-- 2s 科技蓝光晕 -->
<h1 class="gbt-gradient-text">渐变流光</h1>  <!-- 蓝→紫→金 渐变文字 -->
```

## 颜色方案 (不变)
科技蓝 #00d4ff | 金 #ffd700 | 紫 #a855f7 | 绿 #22c55e | 红 #ff4444
背景 #0a0a0f | 卡片 rgba(255,255,255,0.04) | 边框 rgba(255,255,255,0.08)
