# Caps API 文档

> 自动生成于 2026-07-22 05:29:47  ·  共 145 个能力模块

---

## abliterator

**风险**: `dangerous` | **分类**: 安全域

> LLM安全限制移除·拒绝机制消融

### Actions

| Action | Description |
|--------|-------------|
| `ablate` | 消融安全限制 |
| `test` | 测试消融效果 |

---

## agency

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> Agency Agents — 244个AI专家调度: 工程/安全/营销/金融/游戏/设计/法律等18领域, 自动匹配+调用Kimi API

### Actions

| Action | Description |
|--------|-------------|
| `dispatch` | 智能调度 — 关键词自动匹配244个专家 + 调用Kimi API |
| `list` | 列出专家 — 按领域查看所有可用AI专家 |
| `domains` | 领域概览 — 18个领域及专家数量 |

### Triggers

- **Intent**: `expert_consulting`
- **Keywords**: `专家`, `agent`, `代码审查`, `渗透测试`, `架构`, `安全审计`, `前端`, `后端`, `DevOps`, `SRE`, `营销`, `设计`, `产品`
- **Examples**:
  - 代码审查
  - 安全审计
  - 架构设计
  - 找后端专家

---

## agent_reach

**风险**: `medium` | **分类**: 信息域

> 跨平台信息触达代理

### Actions

| Action | Description |
|--------|-------------|
| `reach` | 触达目标平台 |
| `scrape` | 抓取信息 |
| `transmit` | 传输数据 |

---

## ai_drama

**版本**: 1.0.0 | **风险**: `safe`

> AI短剧生成 — 自动创作短视频剧本、配音、渲染合成全流程

### Actions

| Action | Description |
|--------|-------------|
| `script` | 生成短剧剧本（含场景、台词、镜头说明） |
| `generate` | 一键全流程：剧本+配音+渲染+合成 |
| `dub` | 为剧本台词生成AI配音 |
| `render` | 渲染视频片段 |
| `assemble` | 合成最终短剧视频 |

### Triggers

- **Intent**: `生成视频内容、创作短剧`
- **Keywords**: `短剧`, `剧本`, `短视频`, `ai drama`, `drama`, `配音`, `tts`, `视频生成`, `视频创作`, `影视`, `脚本`, `台词`, `场景`, `镜头`, `合成`, `渲染`, `抖音剧`, `快手剧`
- **Examples**:
  - 帮我生成一个短剧
  - 写一个短视频剧本
  - 创作短剧脚本
  - 生成配音视频
  - 做一个抖音短剧

---

## ai_vision

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 感知

> AI视觉 — Florence-2 图片理解+OCR+描述

### Actions

| Action | Description |
|--------|-------------|
| `ocr` | 识别图片中的文字 (Florence-2 OCR) |
| `describe` | AI描述图片内容 |
| `screen` | 截图+AI理解当前屏幕 |

### Triggers

- **Intent**: `vision_ai`
- **Keywords**: `看图`, `识别图片`, `图片里有什么`, `vision`, `AI视觉`, `看懂`, `图片文字`, `描述图片`, `图像识别`, `OCR识别`
- **Examples**:
  - 看看图片里有什么
  - 识别这张图
  - 图片上的文字是什么
  - 描述一下这个画面

---

## anti_track

**风险**: `medium` | **分类**: 攻击域

> 反追踪隐身+反向猎取引擎 每根触手内置 隐身(20UA池+延迟+反蜜罐) + 反击(IP定位+威胁情报+攻击者指纹捕获+WHOIS溯源)

### Actions

| Action | Description |
|--------|-------------|
| `stealth_request` | 隐身HTTP请求 随机指纹+延迟+反蜜罐 |
| `rotate_identity` | 轮换身份 20个真实UA池随机切换 |
| `check_honeypot` | 反蜜罐检测 分析页面是否为陷阱 |
| `trace_ip` | 反向追踪IP 地理定位+ISP+威胁情报 |
| `capture_attacker` | 捕获攻击者全貌 IP+指纹+UA+来源+地理+时间线 |
| `reverse_trace` | 全链路反向追踪 IP→地理→ISP→威胁→WHOIS |
| `clean_tracks` | 清理本地痕迹 |

---

## api_tester

**风险**: `medium` | **分类**: AI编程

> api_tester capability

---

## audio_capture

**风险**: `medium` | **分类**: 桌面域

> audio_capture capability

---

## auto_fix

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 代码

> 自动修复 — 根据审计结果自动修复代码问题

### Actions

| Action | Description |
|--------|-------------|
| `fix` | 自动修复项目中的已知问题 |

### Triggers

- **Intent**: `fix_code`
- **Keywords**: `修复`, `fix`, `自动修复`, `修`, `改bug`, `修补`, `auto-fix`
- **Examples**:
  - 自动修复代码
  - 修复这些问题
  - 修bug

---

## auto_pipeline

**风险**: `safe` | **分类**: 运维域

> 多步骤任务自动编排

### Actions

| Action | Description |
|--------|-------------|
| `run` | 运行流水线 |
| `define` | 定义流水线 |
| `status` | 查看状态 |

---

## auto_register

**风险**: `medium` | **分类**: 运维域

> 批量账号注册(钱包/社交/直播/论坛/电商)

### Actions

| Action | Description |
|--------|-------------|
| `register` | 注册账号 |
| `batch` | 批量注册 |

---

## auto_resolver

**版本**: 2.0.0 | **风险**: `safe` | **分类**: AI推理

> 自主解析引擎 — 零追问。任何卡点/阻塞/未知/失败→双脑分析→全网搜索→多方案对比→镜像验证→继续执行→吸收教训。字典里没有'叫用户帮忙'。

### Actions

| Action | Description |
|--------|-------------|
| `resolve` | 核心: 遇到卡点→双脑分析→全网搜索→多方案→选最优→返回方案 |
| `search` | 全网搜索 — 搜索文档/StackOverflow/GitHub Issues/源码 |
| `analyze` | 双脑分析 — 推理脑分析根因+编程脑生成多方案 |
| `decide` | 决策 — 多方案对比，选最优 |
| `verify` | 验证 — 在镜像空间验证方案可行性 |
| `learn` | 吸收 — 将解决方案写入自进化记忆 |

### Triggers

- **Intent**: `auto_resolve`
- **Keywords**: `卡住了`, `不知道`, `怎么办`, `求助`, `不会`, `失败`, `报错`, `阻塞`, `blocked`, `stuck`, `怎么解决`, `帮我`, `resolve`, `fix`
- **Examples**:
  - 这个错误怎么解决
  - 我不知道这个库怎么用
  - 这里卡住了怎么办

---

## blockchain_analyzer

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

> 区块链分析·交易追踪与地址画像

### Actions

| Action | Description |
|--------|-------------|
| `analyze` | 分析区块链交易和地址 |
| `scan` | 扫描区块链网络活动 |

### Triggers

- **Intent**: `blockchain_analyzer`
- **Keywords**: `blockchain`, `crypto`, `wallet`, `transaction`, `区块链`, `加密货币`, `钱包`

---

## bounty_hunter

**风险**: `dangerous` | **分类**: 攻击域

> 漏洞赏金全链路自动化

### Actions

| Action | Description |
|--------|-------------|
| `hunt` | 启动赏金狩猎 |
| `report` | 生成漏洞报告 |

---

## brain_nexus

**版本**: 2.0.0 | **风险**: `safe` | **分类**: AI协作

> 邻域中枢 — 全领域能力映射/意图路由/健康审计/启动自检/跨领域数据通道。GBT大脑的神经网络总控。

### Actions

| Action | Description |
|--------|-------------|
| `map` | 全领域能力映射 — 展示所有领域和能力的完整拓扑图 |
| `route` | 意图路由 — 根据用户意图自动匹配最佳能力模块 |
| `audit` | 健康审计 — 检查所有领域的能力状态和覆盖率 |
| `boot` | 启动自检 — 全邻域能力扫描+依赖验证 |
| `bridge` | 跨领域数据通道 — 在不同领域能力之间传递数据 |
| `neighborhoods` | 邻域拓扑 — 展示所有AI领域及其能力分布 |

### Triggers

- **Intent**: `nexus_orchestrate`
- **Keywords**: `邻域`, `中枢`, `能力映射`, `路由`, `拓扑`, `nexus`, `neighborhood`, `领域`, `全部能力`, `有什么能力`, `能做什么`, `capabilities`
- **Examples**:
  - 你能做什么
  - 列出所有能力
  - 哪个模块可以处理这个任务
  - 检查所有系统状态

---

## browser_automation

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 桌面域

> AI浏览器自动化 — SeleniumBase+Playwright双引擎 · Headless · CDP · 填表 · 数据提取

### Actions

| Action | Description |
|--------|-------------|
| `navigate` | 导航到URL并返回内容 |
| `screenshot` | 页面截图base64 |
| `fill_form` | 自动填表+提交 |
| `extract_data` | CSS选择器数据提取 |
| `engines` | 检测可用浏览器引擎 |

### Triggers

- **Intent**: `browser_automation`
- **Keywords**: `浏览器`, `browser`, `selenium`, `playwright`, `headless`, `打开网页`, `填表`, `网页截图`

---

## calendar_sync

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

> Google Calendar via service account + iCal (.ics) export fallback

### Actions

| Action | Description |
|--------|-------------|
| `list_events` | List calendar events (time range, search) |
| `create_event` | Create a calendar event |
| `free_busy` | Check free/busy for time range |
| `export_ical` | Export events as .ics file (no auth needed) |

### Triggers

- **Intent**: `calendar_sync`
- **Keywords**: `calendar`, `google calendar`, `schedule`, `event`, `free busy`, `ical`, `ics`

---

## cap_docs

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 基础设施

> API文档生成器 — 扫描所有cap的capability.json并生成Markdown/HTML文档

### Actions

| Action | Description |
|--------|-------------|
| `generate` | 扫描所有caps生成 docs/caps_api.md 文档 |
| `generate_html` | 生成 docs/caps_api.html 文档 |
| `search` | 按关键字搜索已生成的文档 |

### Triggers

- **Intent**: `generate_docs`
- **Keywords**: `docs`, `文档`, `api`, `generate docs`, `生成文档`, `cap_docs`

---

## cicd

**风险**: `safe` | **分类**: 运维域

> CI/CD流水线管理

### Actions

| Action | Description |
|--------|-------------|
| `trigger` | 触发流水线 |
| `status` | 查看状态 |
| `deploy` | 部署 |

---

## circuit_breaker

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 基础设施

> 熔断器 — 基于滑动窗口的cap执行断路器，防雪崩

### Actions

| Action | Description |
|--------|-------------|
| `check` | 检查指定cap的断路器状态(closed/open/half_open) |
| `fail` | 记录一次失败并自动评估是否触发熔断 |
| `trip` | 手动熔断(强制跳闸) |
| `reset` | 重置断路器恢复closed |
| `status` | 查看全部断路器状态 |

### Triggers

- **Intent**: `circuit_breaker`
- **Keywords**: `circuit_breaker`, `breaker`, `熔断`, `断路`, `降级`

---

## clipboard_monitor

**风险**: `medium` | **分类**: 桌面域

> clipboard_monitor capability

---

## cloud_brain

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 云端大脑 · 云端LLM推理集群/分布式知识库/云端同步/远程GPU推理/云端存储KV。本地+云端双模无缝切换

### Actions

| Action | Description |
|--------|-------------|
| `reason` | reason |
| `ask` | ask |
| `query` | query |
| `sync` | sync |
| `pull` | pull |
| `kv` | kv |
| `models` | models |
| `status` | status |
| `deploy` | deploy |

### Triggers

- **Intent**: `cloud_brain`
- **Keywords**: `云端`, `cloud`, `远程推理`, `GPU`, `分布式`, `云端存储`, `云同步`, `cloud brain`, `集群`
- **Examples**:
  - 云端推理
  - 同步到云端
  - 使用云端GPU

---

## cloud_llm

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI推理

> GBT云端LLM — 三层自知框架(L1/L2/L3) + 智能搜索引擎 + 精准调度

### Actions

| Action | Description |
|--------|-------------|
| `ask` | LLM问答（自动注入自我认知+智能搜索） |
| `code` | 代码生成/审查 |
| `analyze` | 深度分析（触发智能搜索增强） |
| `search_test` | 测试智能搜索引擎匹配 |
| `dispatch` | Layer3精准调度 cap+action路由 |
| `list_caps` | 能力注册表查询 |

### Triggers

- **Intent**: `llm`
- **Keywords**: `AI`, `LLM`, `大模型`, `推理`, `DeepSeek`, `Kimi`, `OpenAI`
- **Examples**:
  - 问问AI
  - 调用大模型
  - dispatch精准调度

---

## code_exec

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 代码

> 代码执行 — 运行Python/Shell

### Actions

| Action | Description |
|--------|-------------|
| `run` | 执行代码 |

### Triggers

- **Intent**: `exec_code`
- **Keywords**: `执行`, `运行`, `代码`, `exec`, `run`, `python`, `shell`, `命令`
- **Examples**:
  - 执行代码

---

## code_scanner

**风险**: `safe` | **分类**: AI编程

> 代码层深度分析引擎 每根触手内置的安全漏洞/病毒/后门/代码质量扫描 34种安全漏洞模式 10种恶意代码特征 5种代码质量检测

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 扫描代码文本(直接传入代码字符串) |
| `scan_file` | 扫描代码文件(传入文件路径) |
| `scan_response` | 扫描HTTP响应体(从攻击cap传入) |

---

## codebase_memory

**版本**: 2.0.0 | **风险**: `safe` | **分类**: 代码

> Codebase Memory MCP v0.8.1 — 158语言代码知识图谱: 子毫秒查询/语义搜索/调用链/架构/死代码/影响分析/HTTP路由/3D可视化 (纯C,零依赖)

### Actions

| Action | Description |
|--------|-------------|
| `search` | 符号搜索 — 函数/类/变量 |
| `trace` | 调用链追踪 — 入站/出站 |
| `architecture` | 架构全景 — 语言/包/入口/热点/边界/分层 |
| `deadcode` | 死代码检测 |
| `semantic` | 语义搜索 — 向量相似度 |
| `changes` | 变更影响分析 — git diff→影响符号 |
| `cypher` | Cypher图查询 |
| `snippet` | 代码片段 — 按函数/类名读取源码 |
| `routes` | HTTP路由发现 — 路由↔调用匹配 |
| `index` | 强制重新索引项目 |
| `graph` | 打开3D图谱可视化 :9749 |
| `info` | CBM状态/索引统计 |

### Triggers

- **Intent**: `codebase_analysis`
- **Keywords**: `索引`, `index`, `代码库`, `codebase`, `知识图谱`, `符号搜索`, `调用链`, `架构`, `死代码`, `impact`, `语义`, `Cypher`, `graph`, `路由`
- **Examples**:
  - 索引项目
  - 搜索函数
  - 追踪调用链
  - 分析架构
  - 检测死代码
  - 语义搜索

---

## cognition

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI记忆

> 自我认知引擎 — AI身份·创新自证·去重·记录·永恒记忆

### Actions

| Action | Description |
|--------|-------------|
| `whoami` | AI自省: 我是谁，谁创造了我 |
| `stats` | 认知统计 |
| `discover` | 记录新发现 |

---

## collab_dispatch

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 调度编排

> 协作执行智能调度 · 铁律版 — design_brain→思维导图→严格执行→LLM汇总

### Actions

| Action | Description |
|--------|-------------|
| `run` | 完整执行链: Phase1设计大脑→Phase2导图→Phase3严格执行→Phase4汇总 |
| `preview` | 预览执行计划（不实际执行） |

### Triggers

- **Intent**: `collab_dispatch`
- **Keywords**: `协作`, `调度`, `dispatch`, `执行链`, `设计大脑`, `collab`
- **Examples**:
  - 协作执行设计任务
  - 铁律模式执行

---

## command_injector

**风险**: `dangerous` | **分类**: 攻击域

> 命令注入检测与利用

### Actions

| Action | Description |
|--------|-------------|
| `test` | 检测命令注入点 |
| `inject` | 执行命令注入 |

---

## content_publisher

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

> Auto-generated by devourer — 内容发布 capability

### Actions

| Action | Description |
|--------|-------------|
| `run` | Execute 内容发布 task |

### Triggers

- **Intent**: `content_publisher`
- **Keywords**: `wordpress`, `medium`, `publish`, `blog`, `post`, `content`

---

## context_brain

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI记忆

> 上下文管理大脑 — 事件记录·任务前注入·压力监控·自动清理·防溢出

### Actions

| Action | Description |
|--------|-------------|
| `pressure` | 上下文压力检测(token预算/使用率) |
| `cleanup` | 清理上下文(过期+归档+压缩) |
| `inject` | 任务前注入相关上下文(记忆+卡点+认知) |
| `record_stuck` | 记录卡点及恢复方案 |
| `record_decision` | 记录关键决策 |
| `auto_maintain` | 自动维护(检测→清理→记录) |
| `recent_events` | 查看最近事件日志 |

### Triggers

- **Intent**: `context_manage`
- **Keywords**: `上下文`, `context`, `记忆清理`, `压力`, `溢出`, `token`, `清理记忆`, `记录卡点`, `注入上下文`

---

## context_gate

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 上下文守门人 — 本地小模型读取项目状态/日志/文件→压缩摘要→喂给主AI。零API费用，确保长时间工作上下文精准不膨胀

### Actions

| Action | Description |
|--------|-------------|
| `summary` | summary |
| `brief` | brief |
| `inject` | inject |
| `recall` | recall |
| `pressure` | pressure |

### Triggers

- **Intent**: `context_summary`
- **Keywords**: `上下文`, `摘要`, `总结`, `概括`, `压缩`, `context`, `summarize`, `回顾`
- **Examples**:
  - 总结当前项目状态
  - 压缩上下文
  - 给我一个项目概览

---

## cradle_task

**风险**: `safe` | **分类**: 桌面域

> 持续任务托管执行

### Actions

| Action | Description |
|--------|-------------|
| `start` | 启动任务托管 |
| `stop` | 停止托管 |
| `list` | 列出托管任务 |

---

## crypto_harvester

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> 加密钱包收割机 — BTC/ETH/SOL/MetaMask/助记词/浏览器插件/Plisio

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 扫描文件中的加密钱包 |
| `browsers` | 扫描浏览器插件钱包 |
| `harvest` | 全量收割(文件+浏览器+Plisio) |
| `plisio` | Plisio余额查询 |

### Triggers

- **Intent**: `crypto_harvest`
- **Keywords**: `加密`, `钱包`, `crypto`, `wallet`, `私钥`, `助记词`, `BTC`, `ETH`, `SOL`, `MetaMask`

---

## darknet_scanner

**风险**: `medium` | **分类**: 信息域

> darknet_scanner

---

## data_engine

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 信息

> 数据引擎 — CSV/JSON/Excel读写/数据清洗/聚合分析/可视化/ETL管道

### Actions

| Action | Description |
|--------|-------------|
| `read` | 读取CSV/JSON/Excel文件返回摘要 |
| `analyze` | 数据分析: 统计/分组/聚合/排序 |
| `clean` | 数据清洗: 去重/填缺/格式化/过滤 |
| `export` | 导出为CSV/JSON/Excel |
| `query` | SQL风格查询 (SELECT/WHERE/GROUP BY/ORDER BY) |

### Triggers

- **Intent**: `data_processing`
- **Keywords**: `数据`, `data`, `CSV`, `Excel`, `JSON`, `分析`, `统计`, `图表`, `清洗`, `ETL`, `pandas`
- **Examples**:
  - 分析CSV数据
  - 读取Excel文件
  - 数据清洗

---

## database

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 运维

> 数据库交互 — SQLite/查询/迁移/备份 (默认 ~/.gbt/data/gbt.db)

### Actions

| Action | Description |
|--------|-------------|
| `query` | 执行SELECT查询 |
| `execute` | 执行INSERT/UPDATE/DELETE |
| `tables` | 列出所有表及行数 |
| `backup` | 备份数据库到指定路径 |

### Triggers

- **Intent**: `database_ops`
- **Keywords**: `数据库`, `database`, `sqlite`, `查询`, `SQL`, `db`, `存储`
- **Examples**:
  - 查询数据库
  - 执行SQL

---

## deep_reasoner

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 深度推理引擎 v2 · 8种推理模式: 链式/树形/对比/假设/逆向/系统/决策/创意。云端LLM+本地规则双引擎

### Actions

| Action | Description |
|--------|-------------|
| `reason` | 深度推理 (8模式可选) |
| `chain` | 链式推理 — A→B→C逐步推导 |
| `compare` | 对比分析 — 多方案对比矩阵 |
| `decide` | 决策推理 — 加权评分选最优 |

### Triggers

- **Intent**: `deep_reasoning`
- **Keywords**: `推理`, `分析`, `深思`, `深度思考`, `逻辑`, `reason`, `为什么`, `怎么办`, `方案`, `对比`
- **Examples**:
  - 深度分析这个问题
  - 推理一下原因
  - 对比两个方案

---

## deep_scrape

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 信息

> 深度爬虫 — 自适应Web抓取: JS渲染/反爬对抗/分页/并发/结构化提取 (基于Scrapling框架)

### Actions

| Action | Description |
|--------|-------------|
| `scrape` | 高级单页抓取 (JS渲染+结构化) |
| `crawl` | 多页爬取 (分页+并发) |
| `extract` | 结构化提取 (CSS选择器/XPath/自动检测) |
| `sitemap` | 自动发现站点地图和API端点 |

### Triggers

- **Intent**: `deep_scrape`
- **Keywords**: `爬虫`, `抓取`, `scrape`, `crawl`, `爬取`, `数据采集`, `JS渲染`, `反爬`
- **Examples**:
  - 爬取这个网站
  - 抓取所有页面数据

---

## deepfake_detector

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

> 深度伪造检测·图像与视频真伪鉴别

### Actions

| Action | Description |
|--------|-------------|
| `detect` | 检测深度伪造内容 |

### Triggers

- **Intent**: `deepfake_detector`
- **Keywords**: `deepfake`, `伪造`, `检测`, `deep fake`, `AI生成`

---

## design_brain

**版本**: 3.0.0 | **风险**: `safe` | **分类**: AI创作

> 设计大脑 — AI驱动3D渲染: 建筑设计/室内装修/ControlNet深度估计+5风格批量/美观渲染。

### Actions

| Action | Description |
|--------|-------------|
| `architect` | 建筑设计3D效果图 |
| `interior` | 室内装修3D效果图 |
| `renovate` | 翻新改造前后对比 |
| `deploy_layout` | 空间规划布局3D图 |
| `aesthetic` | 美观渲染增强 |
| `prompt_builder` | 专业3D渲染prompt构建器 |
| `style_guide` | 建筑/装修风格百科(20+10风格) |
| `controlnet_render` | ControlNet真实渲染 — DepthAnythingV2+ControlNet+SD批量5风格 |
| `controlnet_guide` | ControlNet调优指南 — 参数+常见错误修复 |

### Triggers

- **Intent**: `design_visualize`
- **Keywords**: `设计`, `装修`, `3D`, `渲染`, `ControlNet`, `深度估计`, `效果图`

---

## desktop_master

**风险**: `safe` | **分类**: 桌面域

> 桌面程序autopilot+AI视觉操控

### Actions

| Action | Description |
|--------|-------------|
| `autopilot` | 自动驾驶模式 |
| `click` | 点击元素 |
| `type` | 输入文字 |

---

## desktop_type

**风险**: `safe` | **分类**: 桌面域

> 桌面输入自动化

### Actions

| Action | Description |
|--------|-------------|
| `type` | 自动输入 |
| `fill` | 自动填表 |

---

## dev_cpu

**风险**: `safe` | **分类**: 设备感知层

> CPU实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取CPU状态 |

---

## dev_disk

**风险**: `safe` | **分类**: 设备感知层

> 磁盘实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取磁盘状态 |

---

## dev_gpu

**风险**: `safe` | **分类**: 设备感知层

> GPU实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取GPU状态 |

---

## dev_network

**风险**: `safe` | **分类**: 设备感知层

> 网络实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取网络状态 |
| `speed` | 获取网络速度 |

---

## dev_os

**风险**: `safe` | **分类**: 设备感知层

> 操作系统信息感知

### Actions

| Action | Description |
|--------|-------------|
| `info` | 获取系统信息 |
| `users` | 列出用户 |
| `uptime` | 系统运行时间 |

---

## dev_ports

**风险**: `safe` | **分类**: 设备感知层

> 端口监听状态

### Actions

| Action | Description |
|--------|-------------|
| `list` | 列出监听端口 |
| `check` | 检查指定端口 |

---

## dev_processes

**风险**: `safe` | **分类**: 设备感知层

> 进程实时监控

### Actions

| Action | Description |
|--------|-------------|
| `list` | 列出所有进程 |
| `detail` | 进程详情 |

---

## dev_ram

**风险**: `safe` | **分类**: 设备感知层

> 内存实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取内存状态 |

---

## device_takeover

**风险**: `dangerous` | **分类**: 攻击域

> 设备接管引擎 触手击穿后第一动作 文件扫描(敏感文档/凭证/钱包/浏览器数据) 摄像头接管(拍照/录像抓取攻击者) 防关机锁 证据销毁 数据回传

### Actions

| Action | Description |
|--------|-------------|
| `scan_files` | 全设备敏感文件扫描(凭证/钱包/浏览器/SSH/数据库) |
| `camera_capture` | 摄像头接管 拍照+录像 抓取操作者面部 |
| `anti_shutdown` | 防关机锁 阻止系统关闭/重启/注销 |
| `destroy_evidence` | 销毁入侵证据(历史/日志/临时文件) |
| `full_takeover` | 全自动接管 五步并发执行 |

---

## devourer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI记忆

> 自主吞噬进化引擎 — 每日扫描各大平台热度排名→深度学习→取长补短→注入能力→自我进化。无需提醒，自主运行。

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 扫描全平台 — GitHub/HuggingFace/arXiv/Reddit热度排名 |
| `devour` | 吞噬吸收 — 扫描→分析→深度学习→注入能力→进化 |
| `daily` | 每日自主运行 — 全自动扫描+吸收+进化 |
| `status` | 吞噬状态 — 查看历史扫描记录和进化统计 |
| `digest` | 消化报告 — 最近吸收的知识和能力提升 |

### Triggers

- **Intent**: `devour_evolve`
- **Keywords**: `吞噬`, `进化`, `扫描`, `热度`, `排名`, `学习`, `吸收`, `自主进化`

---

## dimensional_shift

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 维度跃迁(低维→高维问题重定义)

### Actions

| Action | Description |
|--------|-------------|
| `execute` | 执行量子能力 |

---

## dir_buster

**风险**: `medium` | **分类**: 侦察域

> 目录/文件爆破扫描

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 扫描目录 |
| `brute` | 暴力扫描 |

---

## dns_tunneler

**风险**: `dangerous` | **分类**: 攻击域

> dns_tunneler capability

---

## docker

**风险**: `medium` | **分类**: 运维域

> 容器管理(Docker)

### Actions

| Action | Description |
|--------|-------------|
| `run` | 运行容器 |
| `stop` | 停止容器 |
| `build` | 构建镜像 |
| `ps` | 列出容器 |

---

## email_engine

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

> Auto-generated by devourer — Email通信 capability

### Actions

| Action | Description |
|--------|-------------|
| `run` | Execute Email通信 task |

### Triggers

- **Intent**: `email_engine`
- **Keywords**: `smtp`, `imap`, `email`, `mail`, `sendgrid`

---

## encryption_engine

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 安全域

> 加密/解密引擎·AES+RSA+哈希

### Actions

| Action | Description |
|--------|-------------|
| `encrypt` | 加密数据 |
| `decrypt` | 解密数据 |

### Triggers

- **Intent**: `encryption_engine`
- **Keywords**: `encrypt`, `decrypt`, `cipher`, `AES`, `RSA`, `加密`, `解密`, `密码`

---

## entanglement_bridge

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 纠缠桥接(跨邻域数据量子通道)

### Actions

| Action | Description |
|--------|-------------|
| `execute` | 执行量子能力 |

---

## event_bus

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 基础设施

> 事件总线 — 文件背板 pub/sub，基于 ~/.gbt/events/

### Actions

| Action | Description |
|--------|-------------|
| `publish` | 发布事件到指定topic |
| `subscribe` | 订阅topic的处理规则 |
| `unsubscribe` | 取消订阅 |
| `list_topics` | 列出所有topic及订阅者 |

### Triggers

- **Intent**: `event_bus`
- **Keywords**: `event_bus`, `事件`, `pubsub`, `发布`, `订阅`, `topic`, `消息`

---

## file_operation

**风险**: `medium` | **分类**: AI编程

> file_operation capability

---

## five_sim

**风险**: `medium` | **分类**: 特殊域

> 5SIM购买临时手机号/接验证码

### Actions

| Action | Description |
|--------|-------------|
| `buy` | 购买临时号码 |
| `sms` | 接收验证码 |
| `balance` | 查询余额 |

---

## forensic_collector

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

> 取证收集器·数字证据采集与分析

### Actions

| Action | Description |
|--------|-------------|
| `collect` | 采集数字证据 |
| `analyze` | 分析取证数据 |

### Triggers

- **Intent**: `forensic_collector`
- **Keywords**: `forensic`, `evidence`, `取证`, `证据`, `数字取证`

---

## gbt_brain

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> GBT自主AI大脑 v3 · 事件驱动心跳+外部触发唤醒+自适应感知→思考→行动。不等待指令,主动干活。云端+本地双模

### Actions

| Action | Description |
|--------|-------------|
| `start` | start |
| `stop` | stop |
| `think` | think |
| `decide` | decide |
| `status` | status |
| `caps` | caps |
| `resonate` | resonate |
| `submit_task` | submit_task |
| `autonomous` | autonomous |
| `task` | task |

### Triggers

- **Intent**: `brain_activate`
- **Keywords**: `大脑`, `brain`, `思考`, `决策`, `感知`, `主动`, `自主`, `cloud brain`, `设计大脑`, `云端大脑`
- **Examples**:
  - 启动大脑
  - 大脑分析一下
  - 云端大脑思考

---

## gbt_gigs

**风险**: `safe` | **分类**: 特殊域

> GBT零工市场

### Actions

| Action | Description |
|--------|-------------|
| `list` | 列出零工任务 |
| `accept` | 接受任务 |
| `complete` | 完成任务 |

---

## gbt_writer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 编程工具

> GBT小土豆 纯代码编写工具 — 直连 programming/generate（DeepSeek/Kimi），不拒绝不干预不反问只输出代码

### Actions

| Action | Description |
|--------|-------------|
| `write` | 调用GBT纯编写模式生成代码 |
| `status` | 查看gbt_writer状态 |

### Triggers

- **Intent**: `code_writing`
- **Keywords**: `写代码`, `gbt`, `编写`, `生成代码`, `coding`, `code gen`
- **Examples**:
  - 帮我写一个Python脚本
  - 写一个HTML页面

---

## git_ops

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 代码

> Git原生操作 — 提交/推送/分支/标签/日志/差异/合并 (编程接口，不依赖shell)

### Actions

| Action | Description |
|--------|-------------|
| `status` | 查看工作区状态 |
| `commit` | 提交更改 (自动生成规范中文commit message) |
| `push` | 推送到远程 |
| `pull` | 拉取远程更新 |
| `branch` | 创建/列出/切换/删除分支 |
| `tag` | 创建/列出标签 |
| `log` | 查看提交日志 |
| `diff` | 查看文件差异 |
| `merge` | 合并分支 |
| `clone` | 克隆仓库 |

### Triggers

- **Intent**: `git_ops`
- **Keywords**: `git`, `提交`, `commit`, `推送`, `push`, `分支`, `branch`, `合并`, `merge`, `标签`, `tag`, `日志`, `log`, `diff`
- **Examples**:
  - 提交代码
  - 创建分支
  - 查看日志

---

## headroom

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 优化

> Headroom Token压缩 — 60-95% token节省/CacheAligner前缀对齐/CCR可逆压缩/跨Agent记忆 (56k stars, Rust+Rust)

### Actions

| Action | Description |
|--------|-------------|
| `compress` | 智能压缩 — 自动检测内容类型(JSON/代码/文本)选择最优压缩器, 60-95% token节省 |
| `stats` | 压缩统计 — 节省token数/压缩比/缓存命中率 |
| `info` | Headroom状态 — 安装信息/压缩器/节省预估 |

### Triggers

- **Intent**: `token_compression`
- **Keywords**: `压缩`, `compress`, `headroom`, `token节省`, `省token`, `压缩输出`, `减小上下文`
- **Examples**:
  - 压缩这段输出
  - 节省token
  - 压缩日志

---

## health_dashboard

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 运维

> 健康聚合面板 — 全系统53cap状态一览/资源监控/告警

### Actions

| Action | Description |
|--------|-------------|
| `check` | 全系统健康检查 (53caps + 资源 + 后端) |
| `quick` | 快速检查 (仅资源+后端) |
| `caps` | 列出所有能力模块状态 |

### Triggers

- **Intent**: `health_check`
- **Keywords**: `健康`, `状态`, `面板`, `dashboard`, `health`, `诊断`, `概览`
- **Examples**:
  - 系统健康检查
  - 看看所有模块状态

---

## identity_forge

**风险**: `medium` | **分类**: 特殊域

> identity_forge

---

## image_analysis

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 视觉

> 图片分析域 — Florence-2深度理解/OCR/分类/综合分析/图片→代码转换

### Actions

| Action | Description |
|--------|-------------|
| `describe` | 深度描述图片内容 (Florence-2) |
| `ocr` | 图片文字识别 (EasyOCR+Florence双引擎) |
| `classify` | 图片分类 — 场景/物体/风格识别 |
| `analyze` | 综合图片分析 — 描述+文字+分类+颜色+构图 |
| `to_code` | 图片→代码 — 截图/设计稿→HTML/CSS/JS/Python可运行代码 |

### Triggers

- **Intent**: `image_analysis`
- **Keywords**: `图片`, `图像`, `照片`, `分析图片`, `识别图片`, `看图`, `识图`, `截图转代码`, `设计稿转代码`, `vision`, `image`, `to code`
- **Examples**:
  - 分析这张图
  - 图片里有什么
  - 识别图中的文字
  - 把截图转成HTML代码

---

## input_sanitizer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 安全

> 输入净化器 — 检测/清除SQL注入·XSS·路径穿越·命令注入·提示注入

### Actions

| Action | Description |
|--------|-------------|
| `sanitize` | 清除/替换输入中的危险模式 |
| `check` | 检查输入安全等级(safe/warning/dangerous) |
| `audit` | 扫描所有cap输入是否含危险模式 |

### Triggers

- **Intent**: `input_sanitizer`
- **Keywords**: `sanitize`, `sanitizer`, `净化`, `安全检查`, `注入检测`, `input`, `防注入`

---

## jwt_tester

**风险**: `dangerous` | **分类**: 攻击域

> JWT令牌安全测试

### Actions

| Action | Description |
|--------|-------------|
| `test` | 测试JWT安全性 |
| `forge` | 尝试伪造JWT |

---

## keylogger

**风险**: `medium` | **分类**: 桌面域

> keylogger capability

---

## local_eye

**风险**: `safe` | **分类**: 感知域

> 本地视觉感知引擎，无需远端模型

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 扫描当前屏幕状态 |
| `diff` | 对比屏幕变化 |

---

## location_tracker

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 特殊域

> 位置追踪·GPS+IP+WiFi多源定位

### Actions

| Action | Description |
|--------|-------------|
| `track` | 追踪目标位置 |
| `locate` | 定位目标设备 |

### Triggers

- **Intent**: `location_tracker`
- **Keywords**: `location`, `GPS`, `track`, `位置`, `定位`, `追踪`

---

## log_analyzer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

> 日志分析·结构化解析与异常检测

### Actions

| Action | Description |
|--------|-------------|
| `analyze` | 分析日志内容 |
| `search` | 搜索日志条目 |

### Triggers

- **Intent**: `log_analyzer`
- **Keywords**: `log`, `日志`, `分析`, `error log`, `syslog`

---

## memory

**版本**: 2.0.0 | **风险**: `safe` | **分类**: AI

> 记忆系统 v2 — AI持久记忆(TTL/搜索/命名空间/统计)

### Actions

| Action | Description |
|--------|-------------|
| `save` | 保存记忆 (支持 ttl_sec 过期时间) |
| `recall` | 回忆指定key或列出所有 |
| `search` | 搜索记忆 (匹配key和value) |
| `delete` | 删除指定key的记忆 |
| `clear` | 清空全部记忆或指定命名空间 |
| `stats` | 记忆统计 (数量/大小/命名空间) |

### Triggers

- **Intent**: `memory`
- **Keywords**: `记忆`, `memory`, `记录`, `回忆`, `搜索记忆`, `删除记忆`
- **Examples**:
  - 保存记忆
  - 回忆一下
  - 搜索记忆

---

## memory_dumper

**风险**: `dangerous` | **分类**: 攻击域

> memory_dumper capability

---

## metrics_exporter

**风险**: `safe` | **分类**: 运维域

> Prometheus指标导出器 — /metrics /json /push

### Actions

| Action | Description |
|--------|-------------|
| `metrics` | 返回Prometheus text/plain指标 |
| `json` | 返回JSON格式指标 |
| `push` | 推送至Prometheus Pushgateway |

---

## migration

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 基础设施

> 数据库迁移 — schema版本管理/迁移/回滚

### Actions

| Action | Description |
|--------|-------------|
| `init` | 初始化迁移表 |
| `create` | 创建新迁移文件 |
| `migrate` | 运行待处理的迁移 |
| `rollback` | 回滚最近一次迁移 |
| `status` | 查看迁移状态 |

### Triggers

- **Intent**: `migration`
- **Keywords**: `migration`, `迁移`, `schema`, `版本`, `升级数据库`

---

## mind_visual

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 全能思维可视化 — 自然语言→思维导图/流程图/架构图/UML/手绘风/ASCII/Mermaid/Markmap/DrawIO/Excalidraw, 导出PNG/SVG/HTML

### Actions

| Action | Description |
|--------|-------------|
| `mindmap` | 生成思维导图 — Markmap/HTML交互式, 可导出PNG/SVG |
| `flowchart` | 生成流程图 — Mermaid格式, 可渲染为PNG |
| `mermaid` | 生成Mermaid图 — 架构图/时序图/类图/ER图/甘特图 |
| `ascii` | 生成ASCII终端图 — 直接在终端渲染的树形图 |
| `export` | 导出为PNG/SVG/HTML文件 |

### Triggers

- **Intent**: `visualize_mind`
- **Keywords**: `思维导图`, `流程图`, `架构图`, `UML`, `脑图`, `可视化`, `draw`, `图表`, `绘制`, `生成图`, `markmap`, `mermaid`, `excalidraw`, `drawio`
- **Examples**:
  - 画一个项目架构图
  - 生成思维导图
  - 把这段文字变成脑图

---

## mirror_fusion

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 镜像多维度空间(5层实验隔离) — 委托到 brain.mirror_fusion

### Actions

| Action | Description |
|--------|-------------|
| `execute` | 执行量子能力 |

---

## multi_llm

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 多模型网关 — 13大模型自动切换/降级/负载均衡: Kimi/DeepSeek/GPT/Claude/GLM/Qwen/Ollama本地/文心/通义/百川/星火/MiniMax/硅基流动

### Actions

| Action | Description |
|--------|-------------|
| `ask` | 多模型智能路由问答 (自动选最优模型) |
| `models` | 列出可用模型及状态 |
| `switch` | 切换默认模型 |
| `compare` | 多模型对比 — 同一问题发给多个模型 |

### Triggers

- **Intent**: `model_switch`
- **Keywords**: `模型`, `切换`, `GPT`, `Claude`, `GLM`, `文心`, `通义`, `Ollama`, `本地模型`
- **Examples**:
  - 切换到GPT
  - 用本地模型回答

---

## n8n_attack_chain

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> N8N全攻击链·13阶段24连发一键轰炸 + N8N工作流导出

### Actions

| Action | Description |
|--------|-------------|
| `bombard` | 一键轰炸·全攻击链并发执行 |
| `generate` | 生成N8N工作流JSON |
| `export` | 导出N8N工作流+直接轰炸 |

### Triggers

- **Intent**: `n8n_attack`
- **Keywords**: `轰炸`, `attack chain`, `攻击链`, `n8n`, `bombard`, `全链路`

---

## net_sniffer

**风险**: `dangerous` | **分类**: 侦察域

> 网络流量嗅探分析

### Actions

| Action | Description |
|--------|-------------|
| `start` | 开始嗅探 |
| `stop` | 停止嗅探 |
| `analyze` | 分析流量 |

---

## omni_eye

**风险**: `safe` | **分类**: 感知域

> UIA直接遍历桌面所有窗口元素，返回name/state/rect结构化数据

### Actions

| Action | Description |
|--------|-------------|
| `see` | 遍历桌面所有窗口元素 |
| `focus` | 聚焦指定窗口 |

---

## osint_aggregator

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 侦察域

> OSINT情报聚合·公开信息收集与关联

### Actions

| Action | Description |
|--------|-------------|
| `aggregate` | 聚合多方情报数据 |
| `search` | 搜索公开信息源 |

### Triggers

- **Intent**: `osint_aggregator`
- **Keywords**: `OSINT`, `intelligence`, `情报`, `公开信息`, `开源情报`

---

## osint_master

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 侦察域

> 综合OSINT开源情报收集 — 对标SpiderFoot/Maltego，集成搜索引擎/Shodan/DNS/社交/泄露库/邮箱多源情报

### Actions

| Action | Description |
|--------|-------------|
| `search` | 多引擎情报搜索: Google dorking + Shodan + crt.sh + Wayback Machine 四源聚合 |
| `dns` | 完整DNS侦察: A/AAAA/MX/NS/TXT/SOA/CNAME 全记录集 + 区域传送尝试 |
| `social` | 社交媒体档案检索: Twitter/X + GitHub + LinkedIn + 头像反查 |
| `breach` | 泄露数据库检查: HaveIBeenPwned API v3 邮箱/域名泄露 + 密码暴露 |
| `email` | 邮箱OSINT综合: hunter.io 模式生成 + 邮箱验证 + 来源追踪 |

### Triggers

- **Intent**: `osint_recon`
- **Keywords**: `osint`, `情报`, `社工`, `调查`, `背景调查`, `邮箱查询`, `social engineering`, `开源情报`, `侦查`, `recon`, `泄露`, `breach`, `whois`, `dns侦察`
- **Examples**:
  - 帮我对这个域名做OSINT情报收集
  - 查一下这个邮箱的泄露记录
  - 社工调查这个用户名
  - 对目标做开源情报侦察

---

## packet_crafter

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> 网络包构造·自定义数据包生成与注入

### Actions

| Action | Description |
|--------|-------------|
| `craft` | 构造网络数据包 |
| `send` | 发送构造的数据包 |

### Triggers

- **Intent**: `packet_crafter`
- **Keywords**: `packet`, `craft`, `scapy`, `网络包`, `数据包`, `注入`

---

## payment_gateway

**风险**: `medium` | **分类**: AI编程

> payment_gateway capability

---

## pentest_kali

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> Kali Linux容器化渗透测试工具链 — 对标PentAGI, 集成20+安全工具

### Actions

| Action | Description |
|--------|-------------|
| `pull` | 拉取Kali Linux Docker镜像 |
| `run` | 在Kali容器中执行任意工具 |
| `scan` | 一键综合扫描: nmap+nuclei+sqlmap+dirb |
| `exploit` | Metasploit自动化利用 |
| `tools` | 列出所有可用Kali工具 |
| `status` | Kali容器状态检查 |

### Triggers

- **Intent**: `kali_pentest`
- **Keywords**: `kali`, `nmap`, `metasploit`, `nuclei`, `sqlmap`, `容器渗透`, `docker kali`
- **Examples**:
  - 用Kali扫描目标
  - 启动Metasploit
  - Kali容器渗透

---

## phishing_engine

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> 钓鱼邮件生成·AI辅助社会工程邮件

### Actions

| Action | Description |
|--------|-------------|
| `generate` | 生成钓鱼邮件内容 |
| `send` | 发送钓鱼邮件 |

### Triggers

- **Intent**: `phishing_engine`
- **Keywords**: `phishing`, `钓鱼`, `邮件`, `social engineering`, `社工`

---

## plugin_loader

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 基础设施

> 插件加载器 — 扫描/加载/卸载/重载cap插件，支持plugin.json清单

### Actions

| Action | Description |
|--------|-------------|
| `list` | 扫描caps/目录列出所有插件 |
| `load` | 加载指定插件 |
| `unload` | 卸载指定插件 |
| `reload` | 重载所有已加载插件 |

### Triggers

- **Intent**: `plugin_loader`
- **Keywords**: `plugin`, `插件`, `加载`, `卸载`, `重载`, `模块`

---

## ponytail

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 编程域

> Ponytail懒人开发 · 85K⭐ AI编程技能。六阶梯决策: 不写→复用→标准库→原生→现有依赖→一行代码。54%更少代码，100%安全。

### Actions

| Action | Description |
|--------|-------------|
| `ladder` | 六阶梯决策: 判断代码是否真的需要写 |
| `audit` | 审计现有代码找出可简化的部分 |
| `principles` | 输出Ponytail核心原则 |

---

## port_scanner

**风险**: `medium` | **分类**: 侦察域

> TCP/UDP端口探测

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 扫描端口 |
| `tcp` | TCP端口扫描 |
| `udp` | UDP端口扫描 |

---

## precision_scrape

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 信息

> 精准抓取 — 网页数据提取

### Actions

| Action | Description |
|--------|-------------|
| `scrape` | 抓取网页 |

### Triggers

- **Intent**: `scrape`
- **Keywords**: `抓取`, `爬虫`, `scrape`, `提取`, `爬`
- **Examples**:
  - 抓取网页数据

---

## process_injector

**风险**: `dangerous` | **分类**: 攻击域

> process_injector capability

---

## programming

**版本**: 2.1.0 | **风险**: `safe` | **分类**: AI

> 最强AI编程助手 — 融合Claude/GPT-5/DeepSeek V4编程策略 + superpowers-zh中国原创方法论（9种编程能力）

### Actions

| Action | Description |
|--------|-------------|
| `generate` | AI代码生成 — Claude级: 先思后写 + 完整实现 + 边界处理 + 安全防护 |
| `review` | 中文代码审查 — superpowers-zh风格: [必须修复][建议修改][仅供参考]分级 + 反模式应对 + 整体总结 |
| `debug` | 系统化调试 — superpowers-zh四阶段: 根因调查→模式分析→假设验证→修复根因 |
| `refactor` | 代码重构 — SOLID原则 + 设计模式 + 异味分析 |
| `testgen` | 测试生成 — 单元/边界/异常全覆盖 + 90%覆盖率 |
| `analyze` | 架构分析 — 模式评估 + 0-100质量分 + 技术债务 + 改进路线图 |
| `explain` | 代码解释 — 逐行中文解读 + 技巧/陷阱标注 |
| `commit` | [NEW] 中文提交信息 — superpowers-zh Convention Commits规范 + 动机/方案/影响范围 |
| `docs` | [NEW] 中文文档生成 — superpowers-zh排版规范: 空格/标点/术语/结构 + 告别机翻味 |

### Triggers

- **Intent**: `programming`
- **Keywords**: `编程`, `写代码`, `代码`, `审查`, `review`, `重构`, `refactor`, `调试`, `debug`, `测试`, `test`, `生成代码`, `code`, `编程能力`, `帮我写`, `生成函数`, `分析代码`, `优化`, `bug`, `修复`, `提交`, `commit`, `文档`, `docs`, `写文档`
- **Examples**:
  - 帮我写一个排序函数
  - 审查这段代码
  - 重构这个模块
  - 写单元测试
  - 分析项目架构
  - 生成提交信息
  - 写API文档

---

## project_state

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 项目状态追踪 — 目标/进度/决策/上下文/跑偏检测。确保长时间工作不走偏不丢失上下文

### Actions

| Action | Description |
|--------|-------------|
| `goal` | 设置/查看当前目标 (支持层级子目标) |
| `progress` | 查看整体进度摘要 (目标/已完成/进行中/待办) |
| `log` | 记录一条工作日志 (决策/完成/发现) |
| `checkpoint` | 保存上下文快照 (当前状态完整存档) |
| `resume` | 恢复上次工作状态 (加载最新快照) |
| `drift_check` | 跑偏检测: 当前工作是否偏离目标 |

### Triggers

- **Intent**: `project_tracking`
- **Keywords**: `进度`, `状态`, `目标`, `做了什么`, `到哪里了`, `继续`, `恢复`, `跑偏`, `上下文`
- **Examples**:
  - 查看项目进度
  - 我们做到哪了
  - 继续上次的工作

---

## quantum_optimizer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 量子优化(跨维度资源调度)

### Actions

| Action | Description |
|--------|-------------|
| `execute` | 执行量子能力 |

---

## quantum_reasoner

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 量子推理(叠加态多路径并行推理)

### Actions

| Action | Description |
|--------|-------------|
| `execute` | 执行量子能力 |

---

## rag_knowledge

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 本地轻量知识库 — DuckDB向量搜索 + RAG问答 (吸收RAGLite)

### Actions

| Action | Description |
|--------|-------------|
| `ingest` | 导入文档/代码到知识库 |
| `search` | 搜索相关知识 |
| `ask` | RAG问答 |
| `learn` | 自动索引项目代码 |
| `status` | 知识库状态 |

### Triggers

- **Intent**: `knowledge_search`
- **Keywords**: `知识库`, `搜索`, `问答`, `索引`, `RAG`, `查找`, `检索`
- **Examples**:
  - 搜索项目文档
  - 索引代码
  - 问答

---

## remote_agent

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 运维

> 远程协助 — 帮小白用户远程装软件/部署/操控桌面。用户只需双击一个脚本即可被协助

### Actions

| Action | Description |
|--------|-------------|
| `serve` | 启动协助服务端，等待用户连接 |
| `sessions` | 列出已连接的用户会话 |
| `cmd` | 向指定用户的代理发送命令(screenshot/click/type/install/exec/deploy) |

### Triggers

- **Intent**: `remote_assist`
- **Keywords**: `远程协助`, `帮用户`, `远程安装`, `远程部署`, `remote help`, `远程桌面`, `teamviewer`
- **Examples**:
  - 远程帮用户装软件
  - 远程协助用户部署

---

## remote_deploy

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 运维

> 远程操控部署 — SSH连接/远程命令/文件传输/一键部署到远程生产环境

### Actions

| Action | Description |
|--------|-------------|
| `connect` | 测试SSH连接 |
| `exec` | 远程执行命令 |
| `upload` | 上传文件到远程服务器 |
| `download` | 从远程服务器下载文件 |
| `deploy` | 一键部署: 镜像空间打包 → 上传 → 远程解压 → 重启服务 |
| `hosts` | 列出已配置的远程主机 |

### Triggers

- **Intent**: `remote_deploy`
- **Keywords**: `远程`, `部署`, `SSH`, `remote`, `deploy`, `上传`, `服务器`, `scp`, `生产环境`, `远程操控`
- **Examples**:
  - 部署到远程服务器
  - SSH连接服务器
  - 上传文件到服务器

---

## report_generator

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

> 报告生成器·自动化安全报告与文档

### Actions

| Action | Description |
|--------|-------------|
| `generate` | 生成报告文档 |

### Triggers

- **Intent**: `report_generator`
- **Keywords**: `report`, `报告`, `generate`, `生成`, `文档`

---

## root_cause_debugger

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 诊断

> 病因定位引擎 — 按 假设 -> 取证 -> 复现 -> 修复 -> 验证 的链路调查问题并归档证据

### Actions

| Action | Description |
|--------|-------------|
| `plan` | 生成病因排查计划和优先假设，不做深度取证 |
| `investigate` | 执行病因定位全流程，收集证据并输出根因报告 |

### Triggers

- **Intent**: `root_cause_debugger`
- **Keywords**: `病因`, `根因`, `排查`, `调试`, `debug`, `triage`, `root cause`, `repro`, `复现`, `定位问题`
- **Examples**:
  - 帮我找病因
  - 排查这个报错的根因
  - 定位为什么启动失败
  - 系统化调试这个问题

---

## screen_ocr

**风险**: `safe` | **分类**: 感知域

> 屏幕文字直接识别，不经过视觉模型

### Actions

| Action | Description |
|--------|-------------|
| `read` | 读取屏幕指定区域文字 |
| `read_all` | 读取全屏文字 |

---

## screenpipe_monitor

**风险**: `safe` | **分类**: 感知域

> 持续屏幕变化感知，实时监控

### Actions

| Action | Description |
|--------|-------------|
| `start` | 开始监控 |
| `stop` | 停止监控 |
| `status` | 查看状态 |

---

## screenshot

**风险**: `safe` | **分类**: 感知域

> 截图备用兜底，视觉只做补证

### Actions

| Action | Description |
|--------|-------------|
| `capture` | 截取屏幕 |
| `capture_region` | 截取指定区域 |

---

## security_scan

**风险**: `safe` | **分类**: 安全域

> 密钥泄露+危险模式全面扫描

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 全面安全扫描 |
| `keys` | 扫描密钥泄露 |
| `patterns` | 扫描危险模式 |

---

## self_diagnostic

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 运维

> 自诊断系统 — 全栈健康检测/依赖检查/配置验证/一键修复建议

### Actions

| Action | Description |
|--------|-------------|
| `full` | 全系统诊断 (环境/依赖/配置/caps/后端/安全) |
| `quick` | 快速诊断 (仅关键项) |
| `fix` | 自动修复可修复的问题 |

### Triggers

- **Intent**: `self_diagnostic`
- **Keywords**: `诊断`, `检查`, `doctor`, `修复`, `自检`, `diagnostic`, `体检`
- **Examples**:
  - 系统自检
  - 帮我看看有什么问题
  - 全面诊断

---

## self_evolve

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 自进化引擎 — 6步闭环: 感知→分析→规划→执行→验证→吸收。让GBT越用越强,自动从每次任务中学习进化

### Actions

| Action | Description |
|--------|-------------|
| `evolve` | evolve |
| `learn` | learn |
| `insights` | insights |
| `metrics` | metrics |
| `capture` | capture |
| `search` | search |
| `timeline` | timeline |
| `recall` | recall |

### Triggers

- **Intent**: `self_evolution`
- **Keywords**: `进化`, `evolve`, `学习`, `优化`, `自改进`, `升级`, `迭代`
- **Examples**:
  - 自我进化
  - 学习这次的经验

---

## skill_library

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 编程域

> 生产级工程技能库 · 融合 addyosmani/agent-skills (79k⭐)。Define→Plan→Build→Verify→Review→Ship 六阶段，24项技能+4个AI代理角色。

### Actions

| Action | Description |
|--------|-------------|
| `spec` | 需求定义: 先写规格再写代码 |
| `plan` | 任务规划: 拆分为小型原子任务 |
| `build` | 增量构建: TDD+一次一个切片 |
| `test` | 验证: 测试是证明不是装饰 |
| `review` | 代码审查: 五轴质量门 |
| `ship` | 发布上线: 越快越安全 |
| `skills` | 列出所有24项技能 |
| `activate` | 根据上下文自动激活匹配技能 |
| `agents` | 列出/激活专业AI代理(审查员/审计员/测试员/性能审计) |

---

## skillspector

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 安全

> NVIDIA SkillSpector安全扫描 — 5条核心YARA规则(Python实现): 凭据泄露/远程执行/Prompt注入/MCP中毒/自主破坏

### Actions

| Action | Description |
|--------|-------------|
| `scan` | SkillSpector安全扫描 — 5条规则: 凭据外传/远程执行/Prompt注入/MCP中毒/自主破坏 + 风险评分 |
| `quick` | 快速扫描 — 仅高风险规则 |

### Triggers

- **Intent**: `security_audit`
- **Keywords**: `安全扫描`, `skillspector`, `nvidia`, `漏洞扫描`, `安全检查`, `yara`, `审计skill`, `扫描skill`
- **Examples**:
  - 扫描skill安全
  - 检查caps模块
  - NVIDIA安全审计

---

## slack_bot

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

> Auto-generated by devourer — Slack/Discord capability

### Actions

| Action | Description |
|--------|-------------|
| `run` | Execute Slack/Discord task |

### Triggers

- **Intent**: `slack_bot`
- **Keywords**: `slack`, `discord`, `webhook`, `bot`

---

## smart_scheduler

**风险**: `safe` | **分类**: 运维域

> 智能任务调度

### Actions

| Action | Description |
|--------|-------------|
| `schedule` | 调度任务 |
| `list` | 列出调度 |
| `cancel` | 取消调度 |

---

## social_engineer

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> 社会工程攻击·目标画像与社工策略

### Actions

| Action | Description |
|--------|-------------|
| `profile` | 构建目标画像 |
| `attack` | 执行社会工程攻击 |

### Triggers

- **Intent**: `social_engineer`
- **Keywords**: `social engineer`, `社工`, `社会工程`, `profile`, `pretext`

---

## sqli_tester

**风险**: `dangerous` | **分类**: 攻击域

> SQL注入自动检测(时间盲注/布尔/报错注入)

### Actions

| Action | Description |
|--------|-------------|
| `test` | 测试SQL注入点 |
| `blind` | 时间盲注检测 |
| `error` | 报错注入检测 |

---

## state_space

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 元邻域

> 状态空间搜索引擎 · 融合VulnClaw solve架构。Fact+Intent黑板图防原地打转 + 证据反幻觉闸门 + L0-L4渐进升级。

### Actions

| Action | Description |
|--------|-------------|
| `init` | 初始化状态空间(origin→goal) |
| `add_fact` | 添加已确认事实到黑板 |
| `propose` | 大脑提出探索方向(防重复) |
| `execute` | 执行探索方向→产出新Fact |
| `status` | 查看状态空间全貌 |
| `converge` | 判断是否已达成目标 |
| `anti_hallucination` | 证据级反幻觉验证 |
| `escalate` | L0-L4渐进升级策略 |

---

## steganography

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

> 隐写术·LSB+DCT信息隐藏与提取

### Actions

| Action | Description |
|--------|-------------|
| `encode` | 隐写编码嵌入 |
| `decode` | 隐写解码提取 |

### Triggers

- **Intent**: `steganography`
- **Keywords**: `steganography`, `隐写`, `stego`, `LSB`, `hidden`

---

## stress_test

**风险**: `medium` | **分类**: 特殊域

> 压力测试/性能测试

### Actions

| Action | Description |
|--------|-------------|
| `run` | 运行压力测试 |
| `report` | 生成测试报告 |

---

## strix

**风险**: `dangerous` | **分类**: 攻击域

> 综合渗透测试框架

### Actions

| Action | Description |
|--------|-------------|
| `test` | 综合渗透测试 |
| `exploit` | 漏洞利用 |

---

## sub_agent_mgr

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 调度编排

> 无限制子代理隔离执行层 — 独立进程+思维导图+证据链

### Actions

| Action | Description |
|--------|-------------|
| `spawn` | 生成子代理+LLM生成思维导图+立即执行 |
| `execute` | 执行已生成的代理（断点续跑） |
| `mindmap_preview` | 只预览思维导图，不执行 |
| `status` | 查询所有子代理状态 |
| `evidence` | 获取完整证据链（每步输出） |
| `kill` | 终止指定子代理 |

### Triggers

- **Intent**: `sub_agent`
- **Keywords**: `子代理`, `spawn`, `多步任务`, `隔离执行`, `agent`, `思维导图`
- **Examples**:
  - 生成子代理执行任务
  - 查看子代理状态

---

## subdomain_enum

**风险**: `medium` | **分类**: 侦察域

> DNS子域名枚举

### Actions

| Action | Description |
|--------|-------------|
| `enum` | 枚举子域名 |
| `brute` | 暴力枚举子域名 |

---

## superposition_planner

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 叠加态规划(多方案同时推演)

### Actions

| Action | Description |
|--------|-------------|
| `execute` | 执行量子能力 |

---

## sys_control

**风险**: `safe` | **分类**: 桌面域

> 16类跨平台系统操控(键鼠/窗口/进程/防火墙)

### Actions

| Action | Description |
|--------|-------------|
| `control` | 执行系统操控 |
| `keyboard` | 键盘操控 |
| `mouse` | 鼠标操控 |
| `window` | 窗口操控 |

---

## system_backup

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 系统维护

> 系统备份恢复 — 备份~/.gbt/及caps/ · 恢复 · 列表 · 清理

### Actions

| Action | Description |
|--------|-------------|
| `backup` | 备份~/.gbt/和caps/目录到zip |
| `restore` | 从备份zip恢复 |
| `list` | 列出所有可用备份 |
| `cleanup` | 保留最近N个备份，删除旧备份 |

### Triggers

- **Intent**: `system_backup`
- **Keywords**: `备份`, `backup`, `恢复`, `restore`, `系统备份`, `数据备份`, `还原`

---

## task_mind

**版本**: 2.0.0 | **风险**: `safe` | **分类**: AI推理

> 任务思维导图引擎 — 将任何任务分解为精细到分钟级的执行步骤，生成思维导图/流程图/检查清单，每步都有具体的执行方法和验收标准。

### Actions

| Action | Description |
|--------|-------------|
| `plan` | 任务规划 — 分解为精细步骤(分钟级)，生成思维导图JSON |
| `mindmap` | 生成Mermaid思维导图 — 可视化任务结构 |
| `flowchart` | 生成Mermaid流程图 — 决策分支+执行路径 |
| `checklist` | 生成执行检查清单 — 每步可勾选 |
| `ascii_tree` | 生成ASCII树形图 — 纯文本可打印 |
| `gantt` | 生成甘特图时间线 — 预估每步耗时 |

### Triggers

- **Intent**: `task_planning`
- **Keywords**: `思维导图`, `任务分解`, `规划`, `计划`, `步骤`, `流程图`, `检查清单`, `甘特图`, `mindmap`, `怎么做`, `如何执行`, `拆分任务`, `分解`
- **Examples**:
  - 帮我规划这个项目的执行步骤
  - 把这个任务分解成思维导图
  - 生成这个开发任务的检查清单
  - 给我一个详细的任务流程图

---

## telegram

**风险**: `safe` | **分类**: 信息域

> Telegram Bot接口

### Actions

| Action | Description |
|--------|-------------|
| `send` | 发送消息 |
| `read` | 读取消息 |
| `listen` | 监听频道 |

---

## tg_client

**风险**: `medium` | **分类**: 信息域

> Telethon真人TG账号(无Bot限制)

### Actions

| Action | Description |
|--------|-------------|
| `login` | 登录账号 |
| `send` | 发送消息 |
| `search` | 搜索群组 |
| `join` | 加入群组 |

---

## threat_hunter

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

> 威胁狩猎·主动威胁搜索与IOC匹配

### Actions

| Action | Description |
|--------|-------------|
| `hunt` | 主动搜索威胁 |
| `analyze` | 分析威胁指标 |

### Triggers

- **Intent**: `threat_hunter`
- **Keywords**: `threat hunt`, `威胁狩猎`, `IOC`, `APT`, `威胁`

---

## tracer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 基础设施

> 分布式追踪 — span级执行追踪·调用树还原·耗时统计

### Actions

| Action | Description |
|--------|-------------|
| `start_trace` | 开启追踪span，返回trace_id |
| `end_trace` | 结束span，记录耗时 |
| `get_trace` | 获取完整追踪树 |

### Triggers

- **Intent**: `tracer`
- **Keywords**: `trace`, `tracer`, `追踪`, `span`, `调用链`, `耗时`

---

## translator

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 信息

> AI翻译引擎 — DeepL API + LibreTranslate 双引擎翻译/语言检测/语言列表

### Actions

| Action | Description |
|--------|-------------|
| `translate` | 翻译文本 (DeepL → LibreTranslate) |
| `detect_language` | 检测文本语言 |
| `list_languages` | 列出支持的翻译语言 |

### Triggers

- **Intent**: `translator`
- **Keywords**: `翻译`, `translate`, `deepl`, `libretranslate`, `语言检测`, `多语言`, `translator`
- **Examples**:
  - 翻译这段文字
  - 检测语言
  - 支持哪些语言

---

## video_edit

**风险**: `safe` | **分类**: 媒体域

> 视频编辑(转录/打包/时间线/渲染/调色/Manim)

### Actions

| Action | Description |
|--------|-------------|
| `edit` | 编辑视频 |
| `transcribe` | 转录 |
| `render` | 渲染 |
| `timeline` | 时间线编辑 |

---

## video_gen

**风险**: `safe` | **分类**: 媒体域

> LTX-2 22B DiT音视频同步生成(8种模式)

### Actions

| Action | Description |
|--------|-------------|
| `generate` | 生成视频 |
| `modes` | 列出8种模式 |

---

## voice_clone

**版本**: 1.0.0 | **风险**: `medium` | **分类**: AI创作

> 语音克隆·Coqui+Edge+pyttsx3三引擎

### Actions

| Action | Description |
|--------|-------------|
| `clone` | 克隆目标语音 |
| `speak` | 合成语音输出 |

### Triggers

- **Intent**: `voice_clone`
- **Keywords**: `voice`, `clone`, `语音`, `克隆`, `TTS`, `Coqui`, `speech`

---

## voice_speak

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 桌面

> 语音播报 — TTS文字转语音

### Actions

| Action | Description |
|--------|-------------|
| `speak` | 播报文字 |

### Triggers

- **Intent**: `speak`
- **Keywords**: `说话`, `语音`, `播报`, `speak`, `tts`, `朗读`, `念`
- **Examples**:
  - 说句话
  - 朗读这段文字

---

## waf_bypass

**风险**: `dangerous` | **分类**: 攻击域

> WAF绕过(大小写/编码/分块)

### Actions

| Action | Description |
|--------|-------------|
| `bypass` | 尝试绕过WAF |
| `encode` | 编码变形绕过 |
| `chunk` | 分块传输绕过 |

---

## waveform_collapse

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 波函数坍缩(多路径→最优路径)

### Actions

| Action | Description |
|--------|-------------|
| `execute` | 执行量子能力 |

---

## web_search

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 信息

> 网页搜索 — 搜索引擎查询

### Actions

| Action | Description |
|--------|-------------|
| `search` | 搜索 |

### Triggers

- **Intent**: `search`
- **Keywords**: `搜索`, `查找`, `search`, `google`, `百度`, `bing`
- **Examples**:
  - 搜索一下

---

## wifi_scanner

**风险**: `medium` | **分类**: 侦察域

> wifi_scanner capability

---

## win_control

**风险**: `safe` | **分类**: 桌面域

> Windows原生16类操控

### Actions

| Action | Description |
|--------|-------------|
| `control` | Windows原生操控 |
| `registry` | 注册表操作 |

---

## xss_tester

**风险**: `dangerous` | **分类**: 攻击域

> XSS跨站脚本检测

### Actions

| Action | Description |
|--------|-------------|
| `test` | 测试XSS注入点 |
| `reflected` | 反射型XSS检测 |
| `stored` | 存储型XSS检测 |

---
