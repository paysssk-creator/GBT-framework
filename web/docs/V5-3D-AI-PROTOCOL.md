

---

# V0-V4 史前探索：声明式引擎的诞生之路

## V1 静态海报时代
HTML+CSS假3D。设计师画JPG/PNG贴图，CSS渐变和阴影伪造立体感。
**教训**: 假3D做不到真正的旋转和粒子交互——必须引入程序化渲染。

## V2 2D Canvas动画时代
`<canvas>`+原生JS画点阵线条。`ctx.beginPath()`+`requestAnimationFrame`。
**教训**: 纯手写命令式代码太累，AI生成极易出错卡顿。

## V3 原生WebGL裸机时代
`WebGLRenderingContext`+顶点着色器+片元着色器。自己管理缓冲区/矩阵/光照。
**教训**: 裸机WebGL给AI完全不可行。AI记不住GLSL语法，写出来跑不通。

## V4 Three.js命令式时代
`new THREE.Scene()`+`new THREE.Mesh()`。代码清晰但仍需手写所有逻辑。
**教训**: AI能写Three.js但像盲人摸象——不知道模型放哪个div，3D容器和页面元素相互遮挡。

## V5 声明式引擎时代 (分水岭)
封装`gbt-3d.js`(2KB)。抛弃所有命令式JS。`<div data-gbt3d="particles">`。
**突破**: 把3D控制权从JS移到HTML。AI只写标签，引擎自动接管。这是驯服AI的终极一步。

> V1-V3是摸索期，看清了底层技术边界；V4是接入期，找到可用3D引擎；V5是封神期，2KB JS吞掉整个Three.js，转化成AI能听懂、能直接写、且不会写错的HTML语法。

# V5 3D能力层 — AI 前端生成协议 (V3.0 加强版)

> **适用**: DeepSeek / Claude / Cursor / VS Code Continue 系统提示词
> **效果**: 任何 AI 读完本协议后，自动按 GBT 3D 标准生成页面，无需描述布局细节

---

## 零、核心铁律 (违反即失败)

1. **禁止** 手写 `new THREE.Scene()`, `new WebGLRenderer()`, 任何 WebGL 初始化代码
2. **禁止** `npm install`, `import` 语句加载 3D 库 — 零依赖，一个 `<script>` 标签搞定
3. **禁止** 引入 GSAP, anime.js, Spline, Lottie 等第三方动画库
4. **必须** 通过 `data-*` 属性和 `class="gbt-*"` 声明式实现所有 3D 和动画
5. **必须** 引入 `<script src="/assets/gbt-3d.js" defer></script>` 作为页面第一行 body 内容
6. **可选** 引入 `<link rel="stylesheet" href="/assets/gbt-animations.css">` 获得增强动画

---

## 一、组件指令字典

### 1.1 粒子光环背景

```html
<div data-gbt3d="particles"
     data-count="3000"
     data-color="#00d4ff"
     data-rings="3"
     data-speed="0.0005"
     style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.6">
</div>
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `data-count` | int | 3000 | 粒子数。移动端自动降至 ≤600 |
| `data-color` | hex | `#00d4ff` | 科技蓝 / `#ffd700`金 / `#a855f7`紫 |
| `data-rings` | int | 3 | 光环层数 1-5 |
| `data-speed` | float | 0.0005 | 旋转速度，不宜超过 0.002 |

### 1.2 3D 动态数据地球

```html
<!-- 静态演示 -->
<div data-gbt3d="globe" data-markers="true"
     style="width:400px;height:400px;margin:0 auto;"></div>

<!-- 动态数据 (每3秒 fetch) -->
<div data-gbt3d="globe"
     data-markers="/api/active-nodes"
     data-marker-interval="3000"
     data-color="#00d4ff"
     data-speed="0.002"
     style="width:500px;height:500px;"></div>
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `data-markers` | string | `"true"` | `"true"`=4个演示城市; URL=动态fetch; `"北京,116.4,39.9;纽约,-74,40.7"`=静态经纬度 |
| `data-marker-interval` | int | 3000 | fetch 间隔(毫秒) |
| `data-color` | hex | `#00d4ff` | 线框颜色 |
| `data-speed` | float | 0.002 | 自转速度 |

API 返回格式: `[{"lat":39.9, "lng":116.4, "color": "0x00ff88"}, ...]` 或 `{"markers":[...]}` 或 `{"nodes":[...]}`

### 1.3 GLB 3D 模型加载 (v3 新增)

```html
<div data-gbt3d="model"
     data-model-src="/assets/models/earth.glb"
     data-model-scale="1.5"
     data-model-color="#00d4ff"
     data-model-speed="0.005"
     data-model-auto-rotate="true"
     style="width:500px;height:500px;">
</div>
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `data-model-src` | url | *必填* | .glb 模型路径 (Blender 导出) |
| `data-model-scale` | float | 1 | 模型缩放 |
| `data-model-color` | hex | `#00d4ff` | 发光颜色 |
| `data-model-speed` | float | 0.005 | 自转速度 |
| `data-model-auto-rotate` | bool | true | 是否自动旋转 |

依赖: `<script src="https://unpkg.com/three@0.160.0/examples/js/loaders/GLTFLoader.js"></script>` (gbt-3d.js 自动检测)

### 1.4 光效连线 (Beam)

```html
<div data-beam="from:#globe-container, to:#cta-button"
     data-beam-color="#00d4ff"
     data-beam-width="2"
     data-beam-dash="8,4">
</div>
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `data-beam` | string | *必填* | `"from: #选择器A, to: #选择器B"` |
| `data-beam-color` | hex | `#00d4ff` | 光束颜色 |
| `data-beam-width` | int | 2 | 线宽(px) |
| `data-beam-dash` | string | `"8,4"` | SVG stroke-dasharray |

效果: 两端元素可见时画出 SVG 发光射线，滚出视野自动消失。自动附带 blur 发光层。

---

## 二、动画指令字典

### 2.1 CSS Scroll-Driven 动画 (v3 新增, 零JS)

```html
<div class="gbt-reveal">从下方淡入 (默认)</div>
<div class="gbt-reveal-left">从左侧滑入</div>
<div class="gbt-reveal-right">从右侧滑入</div>
<div class="gbt-reveal-scale">缩放弹入</div>
```

浏览器原生 `animation-timeline: view()` — Chrome 115+/Edge 115+。
不支持的浏览器自动回退到 IntersectionObserver (gbt-3d.js 处理)。
Stagger 自动生效: 连续 `.gbt-reveal` 元素自带 0.1s 递增延迟。

### 2.2 预设关键帧动画 (gbt-animations.css)

```html
<div class="gbt-float">浮动效果 (3s ease-in-out)</div>
<div class="gbt-pulse-glow">脉冲发光 (科技蓝光晕)</div>
<div class="gbt-spin-slow">缓慢旋转 (20s/圈)</div>
<h1 class="gbt-gradient-text">渐变流光文字 (蓝→紫→金)</h1>
```

### 2.3 鼠标视差

```html
<div data-parallax data-parallax-depth="2">跟手浮动</div>
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `data-parallax` | flag | — | 开启视差 |
| `data-parallax-depth` | int | 1 | 深度 1-5, 越大偏移越大 |

手机端自动禁用。

---

## 三、UI 组件指令字典 (gbt-animations.css)

### 3.1 Glass Card (毛玻璃卡片)

```html
<div class="gbt-card">
  <h3>标题</h3>
  <p>内容文本</p>
</div>
```

自动附带: backdrop-blur, 半透明背景, 圆角16px, hover上浮+科技蓝边框。

### 3.2 颜色工具类

```html
<span class="gbt-text-blue">科技蓝文字</span>
<span class="gbt-text-gold">金色文字</span>
<span class="gbt-text-purple">紫色文字</span>
<span class="gbt-text-green">绿色文字</span>
```

---

## 四、React 轨道 (v3 新增, 可选)

如果项目使用 React，引入 R3F 组件库替代 HTML 标签:

```bash
npm install three @react-three/fiber @react-three/drei framer-motion
```

```jsx
import { ParticleRing, DataGlobe, ScrollReveal, GlassCard, ParallaxCard, CountUp }
  from './gbt-3d-react';

// 粒子背景
<ParticleRing count={2000} color="#00d4ff" rings={3} />

// 动态地球
<DataGlobe markers="/api/nodes" markerInterval={3000} />

// 滚动入场
<ScrollReveal><h1>标题</h1></ScrollReveal>

// 交错入场
<StaggerReveal>
  <GlassCard>卡片1</GlassCard>
  <GlassCard>卡片2</GlassCard>
  <GlassCard>卡片3</GlassCard>
</StaggerReveal>

// 视差卡片
<ParallaxCard depth={2}>内容</ParallaxCard>

// 数字跳动
<CountUp to={12500} duration={1.5} />
```

---

## 五、移动端性能保底 (AI 无需手动处理)

gbt-3d.js **内置**以下降级逻辑，AI 生成页面时无需关心:

| 规则 | PC | 手机 (<768px) |
|---|---|---|
| 粒子数 | 用户指定 (默认3000) | 强制 ≤600 |
| 光环层数 | 用户指定 (默认3) | 强制 ≤2 |
| 像素比 | 最高2x | 强制 1x |
| 抗锯齿 | 开启 | 关闭 |
| 视差 | 正常工作 | 自动禁用 |
| 地球转速 | 用户指定 | 自动减速 30% |
| CSS滚动动画 | `animation-timeline: view()` | 自动回退 IntersectionObserver |

---

## 六、颜色与设计 Token

```
科技蓝 #00d4ff  │  金 #ffd700  │  紫 #a855f7  │  绿 #22c55e  │  红 #ff4444
背景   #0a0a0f  │  卡片 rgba(255,255,255,0.04)
边框   rgba(255,255,255,0.08)  │  圆角 16px  │  模糊 16px
```

---

## 七、完整页面模板 (AI 直接套用)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GBT 3D 页面</title>
    <link rel="stylesheet" href="/assets/gbt-animations.css">
    <style>
        :root {
            --bg: #0a0a0f;
            --card: rgba(255,255,255,0.04);
            --border: rgba(255,255,255,0.08);
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            background: var(--bg);
            color: #e0e0e0;
            font-family: 'Inter', -apple-system, sans-serif;
            overflow-x: hidden;
        }
        .container {
            position: relative;
            z-index: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .hero {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            padding: 60px 0;
        }
    </style>
</head>
<body>

    <!-- ═══ 粒子背景 ═══ -->
    <div data-gbt3d="particles"
         data-count="2500"
         data-color="#00d4ff"
         data-rings="3"
         style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.5">
    </div>

    <div class="container">

        <!-- ═══ Hero ═══ -->
        <section class="hero">
            <div data-gbt3d="globe"
                 data-markers="true"
                 style="width:400px;height:400px;">
            </div>
            <h1 class="gbt-gradient-text gbt-reveal" style="font-size:3rem;margin-top:20px;">
                全球数据网络
            </h1>
            <p class="gbt-reveal" style="color:#888;margin-top:10px;max-width:600px;">
                实时监控全球服务器节点状态，毫秒级响应
            </p>
        </section>

        <!-- ═══ Feature Cards ═══ -->
        <section class="grid">
            <div class="gbt-card gbt-reveal" data-parallax data-parallax-depth="1">
                <h3 class="gbt-text-blue">实时监控</h3>
                <p>全球节点延迟 < 50ms</p>
            </div>
            <div class="gbt-card gbt-reveal" data-parallax data-parallax-depth="2">
                <h3 class="gbt-text-purple">智能路由</h3>
                <p>AI 动态选择最优路径</p>
            </div>
            <div class="gbt-card gbt-reveal" data-parallax data-parallax-depth="1">
                <h3 class="gbt-text-gold">安全加密</h3>
                <p>端到端 AES-256 加密</p>
            </div>
        </section>

        <!-- ═══ CTA ═══ -->
        <div style="text-align:center;padding:80px 0;" class="gbt-reveal-scale">
            <button id="cta-button" class="gbt-pulse-glow"
                    style="padding:16px 48px;background:var(--bg);color:#00d4ff;
                           border:1px solid #00d4ff;border-radius:12px;font-size:1.1rem;cursor:pointer;">
                立即开始
            </button>
        </div>

        <!-- ═══ 光效连线: 地球→CTA ═══ -->
        <div data-beam="from:[data-gbt3d='globe'], to:#cta-button"
             data-beam-color="#00d4ff" data-beam-width="2">
        </div>

    </div>

    <!-- ═══ V5 3D引擎 (必须最后加载) ═══ -->
    <script src="/assets/gbt-3d.js" defer></script>
</body>
</html>
```

---

## 八、React 模板 (v3 可选)

```jsx
import { ParticleRing, DataGlobe, ScrollReveal, StaggerReveal, GlassCard, ParallaxCard } from './gbt-3d-react';

export default function Dashboard() {
  return (
    <>
      <ParticleRing count={2000} color="#00d4ff" rings={3} />
      
      <main style={{ position:'relative', zIndex:1, maxWidth:1200, margin:'0 auto', padding:'40px 20px' }}>
        
        <section style={{ minHeight:'100vh', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}>
          <DataGlobe markers="/api/nodes" markerInterval={3000} />
          <ScrollReveal>
            <h1 className="gbt-gradient-text" style={{ fontSize:'3rem' }}>全球数据网络</h1>
          </ScrollReveal>
        </section>

        <StaggerReveal>
          <GlassCard><h3 className="gbt-text-blue">实时监控</h3></GlassCard>
          <GlassCard><h3 className="gbt-text-purple">智能路由</h3></GlassCard>
          <GlassCard><h3 className="gbt-text-gold">安全加密</h3></GlassCard>
        </StaggerReveal>

      </main>
    </>
  );
}
```

---

## 九、AI 生成检查清单 (输出前自检)

- [ ] 引入了 `<script src="/assets/gbt-3d.js" defer>` 吗？
- [ ] 所有 3D 效果用的是 `data-gbt3d="..."` 而不是手写 Three.js 吗？
- [ ] 动画用的是 `class="gbt-*"` 而不是 `animation:` CSS 或 JS 库吗？
- [ ] 移动端: 粒子数是否合理？(默认3000会自动降级但避免性能浪费)
- [ ] 3D 容器有明确的 width/height 吗？
- [ ] 颜色用的是协议规定的科技蓝/#ffd700/#a855f7 吗？

---

## 十、扩展 (AI 可自行组合)

AI 可以将以上指令自由组合，例如:

```html
<!-- 粒子背景 + 地球 + 滚动卡片 + 光效连线 + 视差CTA -->
<div data-gbt3d="particles" data-count="2000"></div>
<div data-gbt3d="globe" data-markers="/api/nodes"></div>
<div class="gbt-card gbt-reveal" data-parallax data-parallax-depth="2">节点状态</div>
<div data-beam="from:[data-gbt3d='globe'], to:.gbt-card"></div>
```

**不需要写一行 JS。** 这就是声明式 3D — AI 专注内容结构，引擎专注视觉效果。

---

# V6 升级扩展：高保真 3D 模型加载协议

## 新增指令字典

### 1.5 3D 高保真模型展示器 (GLB/GLTF)

```html
<div data-gbt3d="model"
     data-src="thunderstone.glb"
     data-env="studio"
     data-rotate="true"
     data-drag="true"
     data-zoom="true"
     data-scale="1.5"
     data-bg-color="#0a0a0a"
     style="width:100vw;height:100vh;">
</div>
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `data-src` | url | *必填* | .glb / .gltf 模型文件路径 |
| `data-env` | string | `"sunset"` | 环境光照: `studio`(摄影棚) / `sunset`(威尼斯日落) / `warehouse`(工业仓库) / `night`(夜空) / `dawn`(黎明) |
| `data-rotate` | bool | `true` | 是否自动旋转 |
| `data-drag` | bool | `true` | 鼠标/手指拖拽旋转 (OrbitControls) |
| `data-zoom` | bool | `true` | 滚轮缩放 |
| `data-scale` | float | `1` | 模型缩放倍数 |
| `data-bg-color` | hex | `#0a0a0f` | 背景色 |

**底层实现**: Three.js GLTFLoader + RGBELoader + PMREMGenerator(HDR烘焙) + ACESFilmicToneMapping + PCFSoftShadowMap。

**内置 HDR 环境贴图** (从 jsDelivr CDN 自动加载, AI 无需指定):
| preset | 效果 | CDN URL |
|---|---|---|
| `studio` | 摄影棚柔光, 适合产品展示 | Three.js 官方 studio_country_hall_1k.hdr |
| `sunset` | 威尼斯日落, 暖金色金属反射 | Three.js 官方 venice_sunset_1k.hdr |
| `warehouse` | 工业仓库, 冷色金属感 | Three.js 官方 industrial_room_1k.hdr |
| `night` | 夜空环境, 神秘暗调 | Three.js 官方 night_sky_1k.hdr |
| `dawn` | 黎明晨光, 清新通透 | Three.js 官方 kiara_1_dawn_1k.hdr |

### 1.6 全屏 HDR 全景背景

```html
<div data-gbt3d="panorama" data-src="sky.hdr"
     style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;">
</div>
```

使用 HDR 环境图作为 360° 背景, 代替静态图片, 让页面充满沉浸感 (类似 VR 展厅)。

## V6 完整模板: 高保真 3D 产品展示

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D 雷石标本展示</title>
    <!-- 依赖: Three.js + GLTFLoader + RGBELoader + OrbitControls -->
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/loaders/RGBELoader.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
    <script src="/assets/gbt-3d.js" defer></script>
    <style>
        body { background:#0a0a0a; margin:0; overflow:hidden; font-family:sans-serif; }
        .overlay {
            position:absolute; bottom:40px; left:50%; transform:translateX(-50%);
            background:rgba(255,255,255,0.08); backdrop-filter:blur(16px);
            padding:20px 40px; border-radius:16px; color:#fff; text-align:center;
            pointer-events:none; border:1px solid rgba(255,255,255,0.1);
        }
    </style>
</head>
<body>
    <!-- V6 高保真模型 -->
    <div data-gbt3d="model"
         data-src="thunderstone.glb"
         data-env="studio"
         data-drag="true"
         data-zoom="true"
         data-scale="1.5"
         style="width:100vw;height:100vh;">
    </div>

    <div class="overlay">
        <h1>雷石标本 Thunderstone</h1>
        <p>拖拽旋转 · 滚轮缩放 · 查看细节</p>
    </div>
</body>
</html>
```

## V6 关键约束

1. **AI 无法生成 .glb 文件**: 只能写 `data-src="..."`, 需告知用户自行下载模型 (推荐 Sketchfab 免费模型, 或 Tripo3D 文字生成3D)
2. **格式必须为 .glb**: 不支持 .obj / .fbx
3. **HDR 环境贴图自动加载**: 引擎内置 5 种预设, 从 jsDelivr CDN 自动获取, AI 只需指定 `data-env="sunset"`
4. **必须引入 4 个脚本**: Three.js + GLTFLoader + RGBELoader + OrbitControls + gbt-3d.js

---

# V7 升级扩展：3D 交互热区与动态控制协议

## 新增指令字典

### 7. 模型交互热区 (点击互动)

```html
<div data-gbt3d="model"
     data-src="gem.glb"
     data-env="studio"
     data-hotspots='[{"id":"core","pos":[0,0.5,0],"title":"核心","desc":"稀有雷石内核","link":"https://..."}]'>
</div>
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `data-hotspots` | JSON | 热区数组。每项: `id`(标识), `pos`([x,y,z] 相对模型中心坐标), `title`(弹窗标题), `desc`(描述), `link`(可选, 点击跳转URL) |

**底层实现**: Raycaster 射线检测 + 脉冲光点标记 + 自动弹窗 (毛玻璃样式, 4秒自动消失)。点击/触摸均可触发。

**调试技巧**: 打开控制台 `console.log` 查看坐标, 点击模型空白处可获取位置参考。

### 8. 模型动画控制 (GLB 自带动画)

```html
<div data-gbt3d="model"
     data-src="robot.glb"
     data-animate="idle"
     data-animate-loop="true">
</div>
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `data-animate` | string | *全部播放* | 指定播放的动画名称 |
| `data-animate-loop` | bool | `true` | 是否循环播放 |

### 9. 动态环境切换

```html
<button data-gbt3d-env="studio">摄影棚光</button>
<button data-gbt3d-env="sunset">夕阳暖光</button>
<button data-gbt3d-env="warehouse">工业仓库</button>
<button data-gbt3d-env="night">夜空</button>
<button data-gbt3d-env="dawn">黎明晨光</button>
```

点击按钮即时切换 HDR 环境贴图, 模型材质反射跟随变化。当前激活按钮自动高亮。

### JS API (高级用法)

```javascript
var instance = GBT.loadModel(el, 'model.glb', {hotspots: [...]});
instance.switchEnv('sunset');           // 切换环境
instance.playAnimation('walk', true);   // 播放动画
instance.dispose();                     // 销毁
```

## V7 完整模板: 交互式 3D 展厅

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D 交互展厅</title>
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/loaders/RGBELoader.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
    <script src="gbt-3d.js" defer></script>
    <style>
        body { background:#0a0a0a; margin:0; overflow:hidden; font-family:sans-serif; }
        .env-bar {
            position:absolute; bottom:30px; left:50%; transform:translateX(-50%);
            display:flex; gap:10px; z-index:10;
        }
        .env-bar button {
            padding:10px 20px; border-radius:100px; border:1px solid rgba(255,255,255,0.15);
            background:rgba(0,0,0,0.5); color:#fff; cursor:pointer;
            backdrop-filter:blur(8px); font-size:0.85rem; transition:all 0.3s;
        }
        .env-bar button:hover { border-color:#00d4ff; background:rgba(0,212,255,0.1); }
    </style>
</head>
<body>
    <div data-gbt3d="model"
         data-src="thunderstone.glb"
         data-env="studio"
         data-drag="true" data-zoom="true"
         data-hotspots='[
             {"id":"h1","pos":[0.2,0.1,0.5],"title":"晶体核心","desc":"能量传导核心区"},
             {"id":"h2","pos":[-0.3,-0.2,0.4],"title":"矿石基座","desc":"天然玄武岩结构"}
         ]'
         style="width:100vw;height:100vh;">
    </div>

    <div class="env-bar">
        <button data-gbt3d-env="studio">摄影棚</button>
        <button data-gbt3d-env="sunset">夕阳</button>
        <button data-gbt3d-env="warehouse">工业</button>
        <button data-gbt3d-env="night">夜空</button>
    </div>
</body>
</html>
```

## V7 关键约束

1. **热区坐标为占位符**: AI 无法看到 .glb 内部结构, `pos` 坐标需用户在实际页面中微调
2. **弹窗自动生成**: 引擎自动创建毛玻璃弹窗, 点击热区显示, 4秒后自动消失
3. **环境切换即时生效**: 点击 `data-gbt3d-env` 按钮立即重新加载 HDR, 无需刷新页面
4. **动画按名称播放**: 如果 GLB 含多个动画, `data-animate="idle"` 只播放指定名称的

---

# V8 升级扩展：3D 配置器与材质自定义协议

## 新增指令字典

### 10. 场景包装器 (地面阴影)

```html
<div data-gbt3d="scene" data-ground="true" data-shadow="true">
  <div data-gbt3d="model" data-src="car.glb" data-env="studio"></div>
</div>
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `data-ground` | bool | `false` | 底部半透明渐变阴影底座 + 呼吸光环 |
| `data-shadow` | bool | `false` | PCFSoftShadowMap + 方向光投射真实阴影 |

### 11. 多部件材质配置

初始化预设颜色:
```html
<div data-gbt3d="model"
     data-src="car.glb"
     data-materials='{"body":"#cc0000","rims":"#333333"}'>
</div>
```

动态切换按钮:
```html
<button data-gbt3d-part="body" data-value="#ff0000" style="background:#f00"></button>
<button data-gbt3d-part="body" data-value="#00ff00" style="background:#0f0"></button>
<button data-gbt3d-part="rims" data-value="#cccccc" style="background:#ccc"></button>
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `data-materials` | JSON | `{}` | `{"部件名":"#hex色"}` 初始化预设 |
| `data-gbt3d-part` | string | — | 目标部件名 (需与 .glb 内 `mesh.name` 一致) |
| `data-value` | string | — | 目标颜色 `#hex` 或 `rgb()` |
| `data-property` | string | `"color"` | 可选: `color` / `metalness` / `roughness` |

**底层实现**: `model.traverse()` 匹配 `name` → `material.color.lerp()` 0.4秒平滑渐变 (cubic ease-out)，杜绝生硬跳变。

### 12. 加载占位与进度

```html
<div data-gbt3d="model"
     data-src="heavy-model.glb"
     data-placeholder="加载模型中...">
</div>
```

GLTFLoader `onProgress` 实时更新进度条，加载完成自动消失。

### JS API (V8 新增)

```javascript
var instance = GBT.loadModel(el, 'car.glb', {...});
instance.setPartColor('body', '#ff0000');  // 平滑切换部件颜色
instance.namedParts;                         // {body: Mesh, rims: Mesh, ...}
```

## V8 完整模板: 汽车外观配置器

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D 汽车配置器</title>
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/loaders/RGBELoader.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
    <script src="gbt-3d.js" defer></script>
    <style>
        body{background:#0a0a0a;margin:0;overflow:hidden;font-family:sans-serif}
        .config-bar{position:absolute;bottom:30px;left:50%;transform:translateX(-50%);display:flex;gap:15px;background:rgba(0,0,0,0.6);backdrop-filter:blur(10px);padding:15px 25px;border-radius:50px;z-index:10}
        .config-bar button{width:40px;height:40px;border-radius:50%;border:2px solid transparent;cursor:pointer;transition:0.2s}
        .config-bar button:hover{border-color:#fff;transform:scale(1.1)}
        .config-bar .divider{width:1px;background:rgba(255,255,255,0.2);margin:0 5px}
    </style>
</head>
<body>
    <div data-gbt3d="scene" data-ground="true" data-shadow="true">
        <div data-gbt3d="model"
             data-src="sports_car.glb"
             data-env="studio"
             data-materials='{"body":"#0033cc","rims":"#666666"}'
             data-placeholder="加载跑车模型中..."
             style="width:100vw;height:100vh;">
        </div>
    </div>

    <div class="config-bar">
        <span style="color:#fff;font-size:0.8rem;align-self:center">车身</span>
        <button data-gbt3d-part="body" data-value="#ff0000" style="background:#f00"></button>
        <button data-gbt3d-part="body" data-value="#00cc00" style="background:#0c0"></button>
        <button data-gbt3d-part="body" data-value="#0066ff" style="background:#06f"></button>
        <button data-gbt3d-part="body" data-value="#ffcc00" style="background:#fc0"></button>
        <div class="divider"></div>
        <span style="color:#fff;font-size:0.8rem;align-self:center">轮毂</span>
        <button data-gbt3d-part="rims" data-value="#cccccc" style="background:#ccc"></button>
        <button data-gbt3d-part="rims" data-value="#111111" style="background:#111"></button>
    </div>
</body>
</html>
```

## V8 关键约束

1. **部件名必须与 .glb 一致**: AI 无法猜测模型内部 `name`，需提示用户用 Blender 查看/命名部件
2. **颜色渐变平滑**: 引擎内置 `lerp()` cubic ease-out，400ms 过渡，无需 AI 处理
3. **阴影消耗 GPU**: `data-shadow="true"` 会增加 GPU 负载，建议仅在 PC 端使用
4. **场景包装器**: `data-gbt3d="scene"` 包裹模型时，自动继承地面+阴影配置

---

# V9 升级扩展：多视角切换、截图分享与 AR 增强现实

## 新增指令字典

### 13. 多角度快速切换



相机 0.6s cubic ease-out 平滑插值动画，禁止瞬间跳转。预设坐标: front(0,0,5), back(0,0,-5), left(-5,0,0), right(5,0,0), top(0,5,0)。

### 14. 一键截图与分享



PC 端自动触发  下载 PNG。移动端调用  系统分享面板。

### 15. AR 增强现实 (WebXR)



触发  AR 会话，将模型映射到手机摄像头真实平面上 (iOS Safari + Android Chrome)。不支持时自动提示降级。

### JS API (V9 新增)



## V9 完整模板: 3D 产品展示 + 工具栏



## V9 关键约束

1. **AR 需 WebXR 支持**: iOS Safari 16+ / Android Chrome 81+，不支持的设备自动降级提示
2. **截图依赖 preserveDrawingBuffer**: 引擎已在渲染器设置 
3. **相机动画采用 lerp**: cubic ease-out 0.6s，不依赖 GSAP，纯 requestAnimationFrame 实现
4. **preserveDrawingBuffer 轻微影响性能**: 仅在需截图时开启，默认已启用

---

# V10 升级扩展：动态数据驱动与数字孪生协议

## 新增指令字典

### 16. 数据源绑定

\\n
| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| data-source | url | — | ws:// WebSocket 或 https:// HTTP API |
| data-poll | int | 3000 | HTTP 轮询间隔(ms) |
| data-mock | bool | false | true=自动生成随机模拟数据 |

### 17. 数据到模型映射

\\n
支持映射: color(蓝→红热力图) / rotation.speed / scale / opacity / metalness / roughness

### 18. 全局数据事件

\\n
每次数据更新自动触发, UI面板可监听实时刷新。

## V10 完整模板: 数字孪生监控台

\\n
## V10 关键约束

1. mock模式优先: 无真实数据源时自动启用模拟数据, 确保立即可演示
2. 归一化映射: 颜色使用 data-range 线性插值(蓝→红)
3. 缓动过渡: 所有属性变化通过 lerp 平滑, 无跳变
4. 数据防抖: 更新间隔由 data-poll 控制, 避免高频重绘