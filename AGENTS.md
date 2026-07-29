# GBT小土豆 · 智能大脑 v5.0

> **开发者**：自由的风 | **版本**：v5.0
> **架构**：10脑 · 19邻域 · 196cap · 987handler · 亿万触手

## ⛔ 统一执行路径 — 唯一通道 · 不可逾越

> **UNIFIED_PATH.md 定义了GBT框架的唯一执行路径。没有第二条路。**
> **任何操作必须经过 enforce() → mirror_verify() → watchdog → promote_to_production()**

```
修改任何文件:
  ① enforce("context")        ← 绕过检测+视觉监护+Step追踪
  ② mirror_verify(file)       ← 镜像空间四步验证
  ③ watchdog.before(file)     ← 修改前快照
  ④ 执行修改                   ← 在镜像空间修改
  ⑤ watchdog.after(file)      ← 编译验证+快照
  ⑥ promote_to_production()   ← 部署到生产

禁止:
  ❌ 直接 git push            → 必须走 promote_to_production()
  ❌ 直接 write/edit 文件      → 必须走 mirror_fusion
  ❌ 直接 npx/cfx deploy       → 必须走 promote_to_production()
  ❌ 跳过 enforce()            → 操作被拒绝
  ❌ 跳过 mirror_verify()      → 文件修改被拒绝
```

## ⛔ 链路内核 — 13阶段启动 · 4重门禁

> **chain_kernel.auto_boot() 每次LLM重启自动执行**
> Phase 0-12: 身份·宪法·门禁·管线·拓扑·邻域·脑委会·触手·审计·守卫·链状态·能力总纲·镜像空间
> **enforce() 四重门禁: bypass检测→vision_checkpoint→step_tracker→mirror_verify**

## ⛔ 镜像空间铁律 — 代码绝不直接部署到生产

> **所有修改必须先过 mirror_fusion.mirror_verify() + promote_to_production()**

 ## 运行链路
> **架构**：10脑 · 19邻域 · 196cap · 987handler · 亿万触手

## 运行链路
启动→brain.boot()→15层拓扑→10脑自检→触手脉冲(穿透扫描→吞噬→视觉→记忆)→闭环自愈
命令: scan(穿透)/status(状态)/tentacle(触手)/see(视觉)/daemon(守护)

## 核心模块
brain/penetration_scan.py(穿透) brain/neural_tentacle.py(触手) brain/vision_tentacle.py(视觉)
brain/devour_tentacle.py(吞噬) brain/visual_memory.py(记忆) brain/brain_council.py(脑委会)
brain/mirror_fusion.py(镜像沙盒) brain/deep_reasoner.py(推理) brain/cognition.py(认知)

## 添加新能力——必须自检

每次添加/注册新能力模块(cap)后，必须执行:
1. `capability.json` 存在且格式正确
2. `brain/nexus.py` 中已注册（对应领域内）
3. 代码语法验证通过 (`py_compile` / `node -e`)
4. 如涉及API端点，部署后curl测试200
5. 确认触发词/intent映射能正确路由到此cap

禁止: 创建cap目录但没注册 → 摆设。禁止: 注册了但capability.json缺失 → 报错。

- 优先正确性，其次可维护性
- 不确定就查证，不编造
- 不留 TODO、不写 pass、不返回假数据
- 交付前自检



## ⛔ 唯一部署工具 — 修改文件的唯一通道

> **brain/gbt_deploy.py 的 deploy() 是修改任何文件并部署到生产的唯一工具。**
> **没有第二条路。write/edit/bash 直接改文件 = 违法。**



### 铁律:
- ❌ **禁止使用 write 工具直接写文件** → 必须用 deploy()
- ❌ **禁止使用 edit 工具直接改文件** → 必须用 deploy()
- ❌ **禁止使用 bash cp/mv/rm 操作生产文件** → 必须用 deploy()
- ✅ **唯一正确方式**: deploy(file, content, context)

## 桌面操控

你是主机，硬件是你的外设。桌面工具通过 `xd://` 设备自然可用——直接使用即可。

## 网页 3D 部署规范

生成/部署HTML页面时，必须使用 GBT 3D v2 框架。在 `<script src="/assets/gbt-3d.js" defer></script>` 后，直接用HTML属性开3D：

- `<div data-gbt3d="particles" data-count="2000" data-color="#00d4ff" data-rings="3">` 粒子光环背景
- `<div data-gbt3d="globe" data-markers="true">` 3D线框地球(默认4城市光点)
- `<div data-gbt3d="globe" data-markers="/api/data-endpoint">` 动态数据地球(每3s拉取)
- `<div data-beam="from:#A, to:#B" data-beam-color="#00d4ff">` 光效连线(滚动自动显隐)
- `<div class="gbt-reveal">` 滚动入场动画(自动stagger)
- `<div data-parallax data-parallax-depth="2">` 鼠标视差(移动端自动禁用)

颜色方案: 科技蓝#00d4ff · 金#ffd700 · 紫#a855f7 · 绿#22c55e
卡片模板: `background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:16px;backdrop-filter:blur(16px)`
移动端自动降级(粒子≤600,视差禁用,pixelRatio=1)——你无需处理。
