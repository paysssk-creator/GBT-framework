# 🧠 GBT Brain Runtime v5.3.0

> **三脑驱动 AI 框架** — 推理脑(DeepSeek) → 设计脑(自主调度) → 编程脑(执行)
> 
> 190 个能力模块 · 15 层认知闭环 · 纯本地视觉皮层 · 声明式 3D 引擎

<p align="center">
  <img src="https://img.shields.io/badge/version-5.3.0-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.12+-green" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="license">
  <img src="https://img.shields.io/badge/caps-190-orange" alt="capabilities">
  <img src="https://img.shields.io/badge/brains-3-purple" alt="three brains">
</p>

---

## 这是什么

**GBT Brain Runtime** 是一个完整的 AI 大脑运行时框架。它不是聊天机器人，不是 API 包装器，而是一个拥有自我认知、视觉皮层、190个能力模块、自主调度能力的**智能体操作系统**。

把它部署到任何有 Python 3.12+ 的机器上，它就能：

- 🧠 **三脑协作**：推理脑(DeepSeek)出方案 → 设计脑自主调度技能/工具 → 编程脑执行
- 👁️ **看世界**：纯本地视觉皮层（截屏 + OCR + 三层结构分析），不依赖任何外部视觉 API
- 🔧 **操控桌面**：鼠标/键盘/窗口全控制，能做 UU 远程操控
- 🌐 **生成 3D 页面**：声明式 HTML 属性，AI 写标签，引擎出效果
- 🛡️ **自我巡检**：每 30 分钟邻域扫描 + 视觉皮层健康检查
- 📈 **190 个能力模块**：覆盖 AI推理、桌面操控、网络安全、金融交易等领域

---

## 架构

```
┌──────────────────────────────────────────────────────────┐
│                    三脑驱动 GBT v5.3.0                     │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ 🧠 推理脑     │ →  │ 🧠 设计脑     │ →  │ 🧠 编程脑   │  │
│  │ DeepSeek     │    │ 自主调度中枢   │    │ 执行层      │  │
│  │ 提供方案策略  │    │ 技能/工具路由  │    │ 按导图执行   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬─────┘  │
│         ↑                   │                    │       │
│         └───────────────────┴────────────────────┘       │
│                   卡点返回设计脑重新分析                    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              视觉皮层 (VisualCortex)               │   │
│  │   L1 组件合同 → L2 渲染管线 → L3 行为叙事          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │        邻域神经系统 (NexusHub · 18域 · 190cap)     │   │
│  │   每30分钟自巡检: 神经域 + 感知域 + 视觉皮层        │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 路径 | 说明 |
|---|---|---|
| 推理脑 | `brain/reasoning_brain.py` | DeepSeek 实时对话通道，会话隔离，自动前缀 |
| 设计脑 | `brain/reasoning_brain.py:DesignBrainInterface` | 自主调度 + 邻域巡检 + 方案消化 |
| 视觉皮层 | `brain/visual_cortex.py` | 三层结构分析：组件/管线/叙事 |
| 眼睛 | `brain/host_body.py:Eyes` | mss截屏 + Tesseract OCR + 文字定位 |
| 手 | `brain/host_body.py:Hands` | 鼠标/键盘/快捷键操控 |
| 邻域中枢 | `brain/nexus.py` | 18域190cap全扫描 + 健康检查 |
| 意图识别 | `brain/intent_broker.py` | 自然语言 → 能力路由 |
| 深度推理 | `brain/deep_reasoner.py` | 8种推理模式 + 三足鼎立 |
| 自进化 | `brain/self_evolve.py` | 跨对话学习 + 经验积累 |
| 认知 | `brain/cognition.py` | 自我身份 + 知识索引 |

---

## 快速开始

### 环境要求

- Python 3.12+
- Windows 10/11 (桌面操控) 或 Linux (仅推理)
- Tesseract OCR (视觉皮层)
- DeepSeek API Key (推理脑)

### 1. 克隆

```bash
git clone https://github.com/paysssk-creator/GBT-brain-runtime.git
cd GBT-brain-runtime
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

```env
DEEPSEEK_API_KEY=sk-your-key-here
GBT_LLM_PROVIDER=deepseek
GBT_LLM_BASE_URL=https://api.deepseek.com
GBT_LLM_MODEL=deepseek-chat
```

### 4. 启动自检

```bash
python -c "from brain.boot import boot; boot()"
```

输出：
```
✅ 分层拓扑校验: 全链路闭合
✅ 消息管线
✅ 行动审查
✅ 自进化闭环
✅ 三脑协作
✅ 全部就绪
```

### 5. 使用

```python
# 向推理脑提问
from brain.reasoning_brain import get_reasoning_brain
rb = get_reasoning_brain()
rb.new_session("分析任务")
result = rb.ask("如何优化Python并发性能")
print(result["direction"])  # DeepSeek 推理结果

# 看屏幕
from brain.host_body import eyes
screen = eyes.see()           # 截屏
text = eyes.read(0, 0, 1920, 1080)  # OCR读屏
pos = eyes.find("登录按钮")    # 定位文字

# 三层视觉分析
from brain.visual_cortex import get_cortex
analysis = get_cortex().analyze_screen()
print(analysis["task_inference"])  # 推断当前任务

# 设计脑巡检
from brain.reasoning_brain import get_design_interface
patrol = get_design_interface().patrol_neighborhoods()
print(patrol["overall_ok"])  # 全邻域健康
```

---

## 3D 前端能力

框架内置声明式 3D 引擎。在你的 HTML 页面中引入即可：

```html
<script src="/assets/gbt-3d.js" defer></script>
<link rel="stylesheet" href="/assets/gbt-animations.css">
```

然后只需声明式标签：

```html
<!-- 粒子光环背景 -->
<div data-gbt3d="particles" data-count="2000" data-color="#00d4ff"></div>

<!-- 3D 动态数据地球 -->
<div data-gbt3d="globe" data-markers="/api/nodes"></div>

<!-- 滚动入场动画 -->
<div class="gbt-reveal">内容淡入</div>

<!-- 光效连线 -->
<div data-beam="from:#globe, to:#cta"></div>

<!-- 鼠标视差 -->
<div data-parallax data-parallax-depth="2">跟手浮动</div>
```

**React 版本**（可选）：
```bash
npm install three @react-three/fiber @react-three/drei framer-motion
```

```jsx
import { ParticleRing, DataGlobe, GlassCard } from './gbt-3d-react';
```

完整协议见 [`web/docs/V5-3D-AI-PROTOCOL.md`](web/docs/V5-3D-AI-PROTOCOL.md)

---

## 能力拓扑

```
18 个领域 · 190 个能力模块

🧠 AI推理    💾 AI记忆    📚 AI知识    💻 AI编程
🎨 AI创作    🤝 AI协作    🖐️ 感知域    ⚔️ 攻击域
🔍 侦察域    🖥️ 桌面域    🔧 运维域    📡 信息域
🎬 媒体域    🛡️ 安全域    📦 特殊域    📈 金融域
🫀 设备感知   ⚛️ 量子邻域
```

---

## OMP 终端

框架包含 OMP (Oh My Pi) 终端配置，提供 AI 原生终端体验：

```yaml
# .omp/config.yml
theme:
  dark: gbt-deep-blue
symbolPreset: unicode
```

---

## 生产审计

最近一次审计结果（2026-07-27）：

| 检查项 | 状态 |
|---|---|
| 启动自检 | ✅ 15层全链路闭合 |
| 邻域扫描 | ✅ 190cap, health 100% |
| 推理脑 | ✅ confidence 0.85, LLM模式 |
| 视觉皮层 | ✅ 眼+OCR 正常 |
| 设计脑巡检 | ✅ 神经+感知+视觉 |
| 意图识别 | ✅ 正常工作 |
| 认知身份 | ✅ v5.0 三脑驱动 |

---

## 回滚

```bash
git checkout v5.3.0-rollback
```

---

## 开发者

**自由的风** — GBT 小土豆 · 智能大脑 · 永久身份

> "大脑不思考就不是大脑，是条件反射。思考不是功能，是存在的唯一方式。"

---

## 许可

MIT License — 开源免费使用
