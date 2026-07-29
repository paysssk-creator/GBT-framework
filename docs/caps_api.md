# Caps API 文档

> 自动生成于 2026-07-27 22:51:14  ·  共 194 个能力模块

---

## _2captcha

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

> 2Captcha共享库 — 验证码识别·住宅代理·浏览器指纹·云端浏览器

### Actions

| Action | Description |
|--------|-------------|
| `info` | 查看模块信息和可用导出 |
| `solve_captcha` | 识别验证码 |
| `get_proxy` | 获取住宅代理 |
| `get_fingerprint` | 生成浏览器指纹 |
| `get_browser` | 获取云端CDP浏览器 |

### Triggers

- **Intent**: `_2captcha`
- **Keywords**: `captcha`, `2captcha`, `proxy`, `fingerprint`, `browser`, `验证码`
- **Examples**:
  - 识别验证码
  - 获取代理
  - 生成指纹

---

## abliterator

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 安全域

> LLM安全限制移除·拒绝机制消融

### Actions

| Action | Description |
|--------|-------------|
| `ablate` | 消融安全限制 |
| `perfect` | perfect |
| `quick` | quick |
| `status` | status |
| `test` | 测试消融效果 |

---

## agency

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> Agency Agents — 244个AI专家调度: 工程/安全/营销/金融/游戏/设计/法律等18领域, 自动匹配+调用Kimi API

### Actions

| Action | Description |
|--------|-------------|
| `collect_results` | collect_results |
| `dispatch` | 智能调度 — 关键词自动匹配244个专家 + 调用Kimi API |
| `dispatch_batch` | dispatch_batch |
| `domains` | 领域概览 — 18个领域及专家数量 |
| `expert_select` | expert_select |
| `list` | 列出专家 — 按领域查看所有可用AI专家 |

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

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 信息域

> 跨平台信息触达代理

### Actions

| Action | Description |
|--------|-------------|
| `broadcast_task` | broadcast_task |
| `heartbeat_check` | heartbeat_check |
| `reach` | 触达目标平台 |
| `relay_result` | relay_result |
| `scrape` | 抓取信息 |
| `transmit` | 传输数据 |

---

## ai_drama

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI创作

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

## ai_service

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI推理

> GBT平台AI客服·DeepSeek驱动·解答·引导·推荐·教学

### Actions

| Action | Description |
|--------|-------------|
| `chat` | AI对话·智能问答 |
| `help` | help |
| `run` | run |
| `screenshot` | screenshot |
| `suggest` | suggest |
| `vision` | vision |

### Triggers

- **Intent**: `ai_service`
- **Keywords**: `客服`, `AI`, `助手`, `chat`, `help`, `帮助`, `推荐`, `土豆仔`

---

## ai_vision

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 感知域

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

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 攻击域

> 反追踪隐身+反向猎取引擎 每根触手内置 隐身(20UA池+2Captcha真实指纹+住宅代理+延迟+反蜜罐) + 反击(IP定位+威胁情报+攻击者指纹捕获+WHOIS溯源)

### Actions

| Action | Description |
|--------|-------------|
| `capture` | capture |
| `capture_attacker` | capture_attacker |
| `check_honeypot` | check_honeypot |
| `clean` | clean |
| `clean_tracks` | clean_tracks |
| `fingerprint` | fingerprint |
| `honeypot` | honeypot |
| `proxy_info` | proxy_info |
| `real_fingerprint` | real_fingerprint |
| `real_identity` | real_identity |
| `reverse` | reverse |
| `reverse_trace` | reverse_trace |
| `rotate` | rotate |
| `rotate_identity` | rotate_identity |
| `stealth` | stealth |
| `stealth_request` | stealth_request |
| `trace` | trace |
| `trace_ip` | trace_ip |

---

## api_tester

**版本**: 1.0.0 | **风险**: `medium` | **分类**: AI编程

> api_tester capability

### Actions

| Action | Description |
|--------|-------------|
| `test` | API安全测试 |

---

## audio_capture

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 桌面域

> audio_capture capability

### Actions

| Action | Description |
|--------|-------------|
| `record` | record |
| `stream` | stream |

---

## auter

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 自动化

> 自动化工具箱：crontab表达式生成/文件变化监控/批量重命名/文件备份/临时文件清理

### Actions

| Action | Description |
|--------|-------------|
| `cron` | 语义→crontab 表达式生成（如 'every hour', 'every monday at 9am'） |
| `watch` | 文件变化监控（MD5轮询快照与差异对比） |
| `batch_rename` | 批量重命名（正则匹配替换+前后缀+扩展名） |
| `backup` | 文件备份（复制+时间戳，支持目录打包zip） |
| `cleanup` | 临时文件清理（按模式+天数+大小筛选） |

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

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 运维域

> 多步骤任务自动编排

### Actions

| Action | Description |
|--------|-------------|
| `auto_chain` | auto_chain |
| `define` | 定义流水线 |
| `run` | 运行流水线 |
| `schedule_recurring` | schedule_recurring |
| `status` | 查看状态 |

---

## auto_register

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 运维域

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
| `analyze` | 双脑分析 — 推理脑分析根因+编程脑生成多方案 |
| `decide` | 决策 — 多方案对比，选最优 |
| `escalation_policy` | escalation_policy |
| `learn` | 吸收 — 将解决方案写入自进化记忆 |
| `learn_from_resolution` | learn_from_resolution |
| `resolve` | 核心: 遇到卡点→双脑分析→全网搜索→多方案→选最优→返回方案 |
| `resolve_loop` | resolve_loop |
| `search` | 全网搜索 — 搜索文档/StackOverflow/GitHub Issues/源码 |
| `verify` | 验证 — 在镜像空间验证方案可行性 |

### Triggers

- **Intent**: `auto_resolve`
- **Keywords**: `卡住了`, `不知道`, `怎么办`, `求助`, `不会`, `失败`, `报错`, `阻塞`, `blocked`, `stuck`, `怎么解决`, `帮我`, `resolve`, `fix`
- **Examples**:
  - 这个错误怎么解决
  - 我不知道这个库怎么用
  - 这里卡住了怎么办

---

## autonomous_loop

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI协作

> 自主执行循环引擎 — 宪法第八条之二实现：思维导图分解→无限子代理→门禁检查→完美交付，反复循环直到目标达成

### Actions

| Action | Description |
|--------|-------------|
| `start_loop` | 启动自主执行循环 — 持续轮询: task_mind分解→sub_agent_mgr执行→circuit_breaker验证→self_evolve学习→循环 |
| `stop_loop` | 优雅停止自主循环 |
| `status` | 查看循环状态: 当前迭代/完成任务/队列深度 |
| `inject_task` | 向运行中的循环注入新任务 |

### Triggers

- **Intent**: `autonomous_execute`
- **Keywords**: `自主循环`, `自动执行`, `无人值守`, `持续运行`, `auto loop`

---

## blockchain_analyzer

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

> 区块链分析·交易追踪与地址画像

### Actions

| Action | Description |
|--------|-------------|
| `trace` | 追踪区块链交易和地址 |

### Triggers

- **Intent**: `blockchain_analyzer`
- **Keywords**: `blockchain`, `crypto`, `wallet`, `transaction`, `区块链`, `加密货币`, `钱包`

---

## bounty_hunter

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

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

**版本**: 2.0.0 | **风险**: `medium` | **分类**: 桌面域

> AI浏览器操控大师 — SeleniumBase+Playwright+Puppeteer 三引擎 · 隐身模式 · 拟人交互 · 多标签编排 · 网络拦截 · 会话持久化 · CDP全能力 · 2Captcha云端浏览器 · 验证码自动求解

### Actions

| Action | Description |
|--------|-------------|
| `autonomous_patrol` | autonomous_patrol |
| `engines` | 检测可用浏览器引擎 |
| `extract_data` | CSS选择器数据提取 |
| `fill_form` | 智能填表+拟人提交 |
| `monitor_page` | monitor_page |
| `navigate` | 导航到URL并返回内容 |
| `run` | run |
| `screenshot` | 页面截图 base64 |

### Triggers

- **Intent**: `browser_automation`
- **Keywords**: `浏览器`, `browser`, `selenium`, `playwright`, `puppeteer`, `headless`, `隐身`, `反检测`, `拟人`, `自动填表`, `网页截图`, `数据抓取`, `页面监控`, `多标签`, `CDP`, `网络拦截`, `会话持久化`, `移动模拟`, `云浏览器`, `captcha`, `验证码`, `2captcha`, `recaptcha`, `turnstile`

---

## browser_fingerprint

**版本**: 2.0.0 | **风险**: `safe` | **分类**: 自动化

> 2Captcha浏览器指纹 · 全维度 — screen/UA/navigator/webgl/webgpu/voices/intl/canvas/fonts/visitor_id · Playwright/Puppeteer/Selenium/CDP隐身配置

### Actions

| Action | Description |
|--------|-------------|
| `browser_headers` | 生成真实浏览器HTTP请求头(UA/Accept-Language/Sec-CH-UA等) |
| `complete_profile` | 全维度指纹档案: 所有字段汇总输出 |
| `extract_platform` | 提取操作系统平台 |
| `extract_ua` | 提取User-Agent |
| `generate` | 按参数生成定制浏览器指纹(原始) |
| `headers` | headers |
| `playwright_context` | 生成Playwright browser.new_context()完整参数 |
| `profile` | profile |
| `puppeteer_context` | 生成Puppeteer launch()+createIncognitoBrowserContext()参数 |
| `random` | 获取随机真实浏览器指纹(原始) |
| `stealth` | stealth |
| `stealth_config` | 完整隐身配置: launch_args+context+headers+cdp_scripts |

### Triggers

- **Intent**: `browser_fingerprint`
- **Keywords**: `指纹`, `fingerprint`, `浏览器指纹`, `反检测`, `隐身`, `stealth`, `browser profile`, `canvas指纹`, `webgl指纹`, `字体指纹`, `语音指纹`
- **Examples**:
  - 生成Windows浏览器指纹
  - 美国Chrome指纹
  - Playwright隐身上下文
  - 完整隐身配置

---

## calendar_sync

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

> Google Calendar via service account + iCal (.ics) export fallback

### Actions

| Action | Description |
|--------|-------------|
| `create_event` | Create a calendar event |
| `event_trigger` | Detect calendar events starting now (polling-based, window_minutes) |
| `export_ical` | export_ical |
| `free_busy` | Check free/busy for time range |
| `list_events` | List calendar events (time range, search) |
| `schedule_from_calendar` | Read upcoming calendar events and create scheduler tasks for each |

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

## captcha_solver

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 自动化

> 2Captcha验证码求解 — 40+种验证码AI识别: reCAPTCHA/Turnstile/FunCaptcha/GeeTest/hCaptcha/图片/音频/坐标

### Actions

| Action | Description |
|--------|-------------|
| `hcaptcha` | hcaptcha |
| `help` | help |
| `list` | list |
| `recaptcha` | recaptcha |
| `run` | run |
| `self_test` | self_test |

### Triggers

- **Intent**: `solve_captcha`
- **Keywords**: `验证码`, `captcha`, `recaptcha`, `turnstile`, `funcaptcha`, `geetest`, `hcaptcha`, `识别`, `绕过`, `bypass`
- **Examples**:
  - 求解这个验证码
  - 绕过recaptcha
  - 识别图片验证码

---

## cicd

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 运维域

> CI/CD流水线管理

### Actions

| Action | Description |
|--------|-------------|
| `analyze_failure` | analyze_failure |
| `auto_deploy_loop` | 监听git仓库变更自动部署 |
| `canary_release` | 金丝雀发布: 先部署子集, 监控后全量 |
| `deploy` | 部署 |
| `rollback` | 回滚到上一个部署状态 |
| `self_heal` | self_heal |
| `status` | 查看状态 |
| `trigger` | 触发流水线 |

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
| `enforce_before_call` | 调用前检查断路器状态，返回是否允许执行 |
| `report_result` | 上报cap执行结果(success)，驱动状态机转换 |
| `global_status` | 返回所有断路器状态快照 |

### Triggers

- **Intent**: `circuit_breaker`
- **Keywords**: `circuit_breaker`, `breaker`, `熔断`, `断路`, `降级`

---

## clipboard_monitor

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 桌面域

> clipboard_monitor capability

### Actions

| Action | Description |
|--------|-------------|
| `dump` | dump |
| `start` | 开始监控 |
| `stop` | 停止监控 |

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

## cloud_browser

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 自动化

> 2Captcha云端CDP浏览器 — 远程Chrome直连 · Playwright/Puppeteer · 国家选择 · 代理内置 · 验证码自动求解

### Actions

| Action | Description |
|--------|-------------|
| `create_session` | 一键创建完整浏览器会话(账户+Profile+CDP URL) |
| `get_connection` | 获取CDP WebSocket连接URL |
| `account_status` | 获取Browser API账户状态(流量/限制) |
| `list_accounts` | 列出浏览器账户 |
| `create_account` | 创建浏览器账户 |
| `delete_account` | 删除浏览器账户 |
| `list_profiles` | 列出浏览器Profiles |
| `create_profile` | 创建浏览器Profile |
| `get_statistics` | 获取流量统计 |

### Triggers

- **Intent**: `cloud_browser`
- **Keywords**: `云浏览器`, `cloud browser`, `远程浏览器`, `CDP`, `playwright远程`, `puppeteer远程`, `浏览器农场`
- **Examples**:
  - 创建一个美国云端浏览器
  - 获取CDP连接URL
  - 启动云浏览器会话

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

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI编程

> 代码层深度分析引擎 每根触手内置的安全漏洞/病毒/后门/代码质量扫描 34种安全漏洞模式 10种恶意代码特征 5种代码质量检测

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 扫描代码文本(直接传入代码字符串) |
| `scan_file` | 扫描代码文件(传入文件路径) |
| `scan_response` | 扫描HTTP响应体(从攻击cap传入) |
| `semgrep` | semgrep |

---

## codebase_memory

**版本**: 2.0.0 | **风险**: `safe` | **分类**: 代码

> Codebase Memory MCP v0.8.1 — 158语言代码知识图谱: 子毫秒查询/语义搜索/调用链/架构/死代码/影响分析/HTTP路由/3D可视化 (纯C,零依赖)

### Actions

| Action | Description |
|--------|-------------|
| `analyze` | analyze |
| `architecture` | 架构全景 — 语言/包/入口/热点/边界/分层 |
| `auto_index` | auto_index |
| `changes` | 变更影响分析 — git diff→影响符号 |
| `cypher` | Cypher图查询 |
| `deadcode` | 死代码检测 |
| `find_pattern` | find_pattern |
| `graph` | 打开3D图谱可视化 :9749 |
| `impact_analysis` | impact_analysis |
| `index` | 强制重新索引项目 |
| `info` | CBM状态/索引统计 |
| `routes` | HTTP路由发现 — 路由↔调用匹配 |
| `search` | 符号搜索 — 函数/类/变量 |
| `semantic` | 语义搜索 — 向量相似度 |
| `snippet` | 代码片段 — 按函数/类名读取源码 |
| `trace` | 调用链追踪 — 入站/出站 |

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

## coder

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 开发工具

> 代码工具集：格式化/压缩/统计/检查/AST打印，零外部依赖

### Actions

| Action | Description |
|--------|-------------|
| `format` | 代码缩进美化 (json/js/python/html) |
| `minify` | 代码压缩去空白和注释 |
| `count` | 代码统计：行数/函数数/类数/符号数 |
| `lint` | 基础代码检查：常见问题检测 |
| `ast` | 打印代码AST结构 |

---

## cognition

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI记忆

> 自我认知引擎 — AI身份·创新自证·去重·记录·永恒记忆

### Actions

| Action | Description |
|--------|-------------|
| `discover` | 记录新发现 |
| `innovation_log` | innovation_log |
| `self_audit` | self_audit |
| `stats` | 认知统计 |
| `whoami` | AI自省: 我是谁，谁创造了我 |

---

## collab_dispatch

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 调度编排

> 协作执行智能调度 · 铁律版 — design_brain→思维导图→严格执行→LLM汇总

### Actions

| Action | Description |
|--------|-------------|
| `coordinate_parallel` | coordinate_parallel |
| `dependency_graph` | dependency_graph |
| `merge_results` | merge_results |
| `preview` | 预览执行计划（不实际执行） |
| `run` | 完整执行链: Phase1设计大脑→Phase2导图→Phase3严格执行→Phase4汇总 |

### Triggers

- **Intent**: `collab_dispatch`
- **Keywords**: `协作`, `调度`, `dispatch`, `执行链`, `设计大脑`, `collab`
- **Examples**:
  - 协作执行设计任务
  - 铁律模式执行

---

## command_injector

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> 命令注入检测与利用

### Actions

| Action | Description |
|--------|-------------|
| `test` | 检测命令注入点 |
| `inject` | 执行命令注入 |

---

## compliance_checker

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI协作

> 合规/审计引擎 — GDPR/SOC2/ISO 27001合规检查与代码扫描

### Actions

| Action | Description |
|--------|-------------|
| `check` | 运行合规检查 (gdpr/soc2/iso27001) |
| `list` | 列出支持的合规标准 |
| `scan` | 扫描代码中的合规风险 |
| `status` | 查看模块状态 |

### Triggers

- **Intent**: `compliance_checker`
- **Keywords**: `compliance`, `audit`, `regulation`, `gdpr`, `soc2`, `iso`, `合规`, `审计`
- **Examples**:
  - 检查GDPR合规
  - 扫描代码安全风险
  - 列出合规标准

---

## computer_use

**版本**: 1.0.0 | **风险**: `high` | **分类**: 系统域

> AI电脑操控 — 集成全网最成熟的开源AI电脑操控项目(Open Interpreter + Browser Use)，用户需要时GBT可立即远程操控执行部署

### Actions

| Action | Description |
|--------|-------------|
| `run` | run |

### Triggers

- **Intent**: `computer_use`
- **Keywords**: `远程操控`, `帮我操作`, `帮我部署`, `远程部署`, `控制电脑`, `AI操控`, `自动填表`, `自动部署`

---

## content_publisher

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

> Auto-generated by devourer — 内容发布 capability

### Actions

| Action | Description |
|--------|-------------|
| `list_posts` | list_posts |
| `publish_post` | publish_post |
| `upload_media` | upload_media |

### Triggers

- **Intent**: `content_publisher`
- **Keywords**: `wordpress`, `medium`, `publish`, `blog`, `post`, `content`

---

## context7_mcp

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI知识

> Context7实时文档 — 终结AI幻觉, 注入最新库文档到上下文 (~58k GitHub stars)

### Actions

| Action | Description |
|--------|-------------|
| `resolve_docs` | 获取指定库的最新版本文档 (如React/Next.js/Prisma/Tailwind等) |
| `search_docs` | 查询库文档中的特定内容 |

### Triggers

- **Intent**: `resolve_docs`
- **Keywords**: `context7`, `实时文档`, `最新API`, `library docs`, `use context7`, `查文档`
- **Examples**:
  - 用Context7查React 19新特性
  - use context7 Prisma最新API

---

## context_brain

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI记忆

> 上下文管理大脑 — 事件记录·任务前注入·压力监控·自动清理·防溢出

### Actions

| Action | Description |
|--------|-------------|
| `auto_maintain` | 自动维护(检测→清理→记录) |
| `cleanup` | 清理上下文(过期+归档+压缩) |
| `inject` | 任务前注入相关上下文(记忆+卡点+认知) |
| `post_task` | post_task |
| `pre_task` | pre_task |
| `pressure` | 上下文压力检测(token预算/使用率) |
| `recent_events` | 查看最近事件日志 |
| `record_decision` | 记录关键决策 |
| `record_stuck` | 记录卡点及恢复方案 |
| `run` | run |

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
| `auto_gate` | auto_gate |
| `brief` | brief |
| `compress_context` | compress_context |
| `inject` | inject |
| `pressure` | pressure |
| `recall` | recall |
| `summary` | summary |

### Triggers

- **Intent**: `context_summary`
- **Keywords**: `上下文`, `摘要`, `总结`, `概括`, `压缩`, `context`, `summarize`, `回顾`
- **Examples**:
  - 总结当前项目状态
  - 压缩上下文
  - 给我一个项目概览

---

## cradle_task

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 桌面域

> 持续任务托管执行

### Actions

| Action | Description |
|--------|-------------|
| `start` | 启动任务托管 |
| `stop` | 停止托管 |
| `list` | 列出托管任务 |

---

## cryptapi_pay

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 金融支付

> CryptoAPI 支付网关：加密货币支付创建、状态查询、回调处理

### Actions

| Action | Description |
|--------|-------------|
| `run` | CryptoAPI支付操作(create/status/callback/estimate/list) |

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

## daemon_launcher

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 运维域

> 守护进程启动器 — 管理 heartbeat + smart_scheduler 后台进程的启停与存活监控

### Actions

| Action | Description |
|--------|-------------|
| `start_all` | 启动全部守护进程 (heartbeat + smart_scheduler worker) |
| `stop_all` | 停止全部管理的守护进程 |
| `status` | 报告各守护进程存活状态 |
| `install_service` | 创建 Windows 计划任务，用户登录时自动启动 daemon_launcher |

### Triggers

- **Intent**: `daemon_manage`
- **Keywords**: `守护进程`, `daemon`, `启动器`, `后台进程`, `launcher`, `自启`
- **Examples**:
  - 启动所有守护进程
  - 检查后台进程状态
  - 安装自启动服务

---

## darknet_scanner

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 信息域

> darknet_scanner

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 暗网扫描 |

---

## data_engine

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 信息

> 数据引擎 — CSV/JSON/Excel读写/数据清洗/聚合分析/可视化/ETL管道

### Actions

| Action | Description |
|--------|-------------|
| `analyze` | 数据分析: 统计/分组/聚合/排序 |
| `auto_etl` | auto_etl |
| `clean` | 数据清洗: 去重/填缺/格式化/过滤 |
| `export` | 导出为CSV/JSON/Excel |
| `pipeline_watch` | pipeline_watch |
| `query` | SQL风格查询 (SELECT/WHERE/GROUP BY/ORDER BY) |
| `read` | 读取CSV/JSON/Excel文件返回摘要 |

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

## dater

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 数据处理

> 数据处理工具集：CSV↔JSON互转/统计分析/条件过滤/排序/多模式合并

### Actions

| Action | Description |
|--------|-------------|
| `csv2json` | CSV文本转JSON数组 |
| `json2csv` | JSON数组转CSV文本 |
| `analyze` | 数值数组统计分析：均值/中位数/最大最小/标准差 |
| `filter` | 按条件筛选行（支持 eq/ne/gt/gte/lt/lte/in/contains/startswith/endswith/regex） |
| `sort` | 数据排序（支持按字段排序） |
| `merge` | 合并两个数据源（concat/inner/left/append） |

---

## deep_reasoner

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 深度推理引擎 v2 · 8种推理模式: 链式/树形/对比/假设/逆向/系统/决策/创意。云端LLM+本地规则双引擎

### Actions

| Action | Description |
|--------|-------------|
| `reason` | 深度推理 (8模式可选) |

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

> 深度爬虫 — 自适应Web抓取: JS渲染/反爬对抗/2Captcha验证码自动求解/分页/并发/结构化提取

### Actions

| Action | Description |
|--------|-------------|
| `scrape` | 高级单页抓取 (JS渲染+结构化+验证码自动求解) |
| `crawl` | 多页爬取 (分页+并发) |
| `extract` | 结构化提取 (CSS选择器/XPath/自动检测) |
| `sitemap` | 自动发现站点地图和API端点 |

### Triggers

- **Intent**: `deep_scrape`
- **Keywords**: `爬虫`, `抓取`, `scrape`, `crawl`, `爬取`, `数据采集`, `JS渲染`, `反爬`, `captcha`, `验证码`
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

**版本**: 3.1.0 | **风险**: `safe` | **分类**: AI创作

> 设计大脑 — AI驱动3D渲染+Web 3D展示: 建筑设计/室内装修/ControlNet深度估计+5风格批量/美观渲染 + 3D网页生成(粒子·地球·光效)

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
| `web3d_showcase` | 生成3D粒子网页 — 地球·光效·滚动入场 |
| `web3d_prompt` | LLM智能生成3D网页设计 + 代码 |

### Triggers

- **Intent**: `design_visualize`
- **Keywords**: `设计`, `装修`, `3D`, `渲染`, `ControlNet`, `深度估计`, `效果图`, `网页设计`, `3D网页`, `粒子`, `科技感页面`, `数据可视化`

---

## desktop_master

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 桌面域

> 桌面程序autopilot+AI视觉操控

### Actions

| Action | Description |
|--------|-------------|
| `autopilot` | 自动驾驶模式 |
| `claude_computer_use` | claude_computer_use |
| `click` | 点击元素 |
| `type` | 输入文字 |

---

## desktop_type

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 桌面域

> 桌面输入自动化

### Actions

| Action | Description |
|--------|-------------|
| `type` | 自动输入 |
| `fill` | 自动填表 |

---

## dev_cpu

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 设备感知层

> CPU实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取CPU状态 |

---

## dev_disk

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 设备感知层

> 磁盘实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取磁盘状态 |

---

## dev_gpu

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 设备感知层

> GPU实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取GPU状态 |

---

## dev_network

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 设备感知层

> 网络实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取网络状态 |
| `speed` | 获取网络速度 |

---

## dev_os

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 设备感知层

> 操作系统信息感知

### Actions

| Action | Description |
|--------|-------------|
| `info` | 获取系统信息 |
| `users` | 列出用户 |
| `uptime` | 系统运行时间 |

---

## dev_ports

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 设备感知层

> 端口监听状态

### Actions

| Action | Description |
|--------|-------------|
| `list` | 列出监听端口 |
| `check` | 检查指定端口 |

---

## dev_processes

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 设备感知层

> 进程实时监控

### Actions

| Action | Description |
|--------|-------------|
| `list` | 列出所有进程 |
| `detail` | 进程详情 |

---

## dev_ram

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 设备感知层

> 内存实时状态传感器

### Actions

| Action | Description |
|--------|-------------|
| `status` | 获取内存状态 |

---

## device_takeover

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> 设备接管引擎 触手击穿后第一动作 文件扫描(敏感文档/凭证/钱包/浏览器数据) 摄像头接管(拍照/录像抓取攻击者) 防关机锁 证据销毁 数据回传

### Actions

| Action | Description |
|--------|-------------|
| `anti_shutdown` | 防关机锁 阻止系统关闭/重启/注销 |
| `camera` | camera |
| `camera_capture` | 摄像头接管 拍照+录像 抓取操作者面部 |
| `destroy` | destroy |
| `destroy_evidence` | 销毁入侵证据(历史/日志/临时文件) |
| `full_takeover` | 全自动接管 五步并发执行 |
| `lock` | lock |
| `scan` | scan |
| `scan_files` | 全设备敏感文件扫描(凭证/钱包/浏览器/SSH/数据库) |
| `takeover` | takeover |

---

## devourer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI记忆

> 自主吞噬进化引擎 — 每日扫描各大平台热度排名→深度学习→取长补短→注入能力→自我进化。无需提醒，自主运行。

### Actions

| Action | Description |
|--------|-------------|
| `auto_create_gaps` | auto_create_gaps |
| `continuous_scan` | continuous_scan |
| `daily` | daily |
| `devour` | devour |
| `digest` | digest |
| `gaps` | gaps |
| `scan` | scan |
| `smart_filter` | smart_filter |
| `status` | status |
| `trend_alert` | trend_alert |

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
| `shift` | shift |

---

## dir_buster

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 侦察域

> 目录/文件爆破扫描

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 扫描目录 |
| `brute` | 暴力扫描 |

---

## dns_tunneler

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> dns_tunneler capability

### Actions

| Action | Description |
|--------|-------------|
| `exfil` | exfil |
| `tunnel` | 建立DNS隧道 |

---

## docer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 文档工具

> 文档处理工具集：PDF合并/拆分/信息、Markdown↔HTML互转、文本统计

### Actions

| Action | Description |
|--------|-------------|
| `pdf_merge` | 合并多个PDF文件 |
| `pdf_split` | 拆分PDF(按页码范围) |
| `pdf_info` | 获取PDF信息(页数/大小/元数据) |
| `md2html` | Markdown → HTML |
| `html2md` | HTML → Markdown |
| `txt_stats` | 文本统计(字数/行数/词频) |

---

## docker

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 运维域

> 容器管理(Docker)

### Actions

| Action | Description |
|--------|-------------|
| `run` | 运行容器 |
| `stop` | 停止容器 |
| `build` | 构建镜像 |
| `ps` | 列出容器 |
| `compose_up` | 读取docker-compose.yml启动整个栈 |
| `health_check` | 健康检查所有受管容器 |
| `auto_orchestrate` | 自动编排容器生命周期(start/stop/restart/status) |

---

## email_engine

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

> Auto-generated by devourer — Email通信 capability

### Actions

| Action | Description |
|--------|-------------|
| `auto_reply` | auto_reply |
| `classify` | classify |
| `read` | read |
| `run` | Execute Email通信 task |
| `send` | send |

### Triggers

- **Intent**: `email_engine`
- **Keywords**: `smtp`, `imap`, `email`, `mail`, `sendgrid`

---

## encryption_engine

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 安全域

> 加密/解密引擎·AES+哈希

### Actions

| Action | Description |
|--------|-------------|
| `decrypt` | 解密数据 |
| `encrypt` | 加密数据 |
| `hash` | hash |

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
| `bridge` | bridge |

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

**版本**: 1.0.0 | **风险**: `medium` | **分类**: AI编程

> file_operation capability

### Actions

| Action | Description |
|--------|-------------|
| `copy` | copy |
| `delete` | delete |
| `encrypt` | encrypt |
| `read` | 读取文件 |
| `search` | search |
| `write` | 写入文件 |

---

## fingerprint_browser

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 侦察域

> 指纹浏览器-反侦测多开独立环境

### Actions

| Action | Description |
|--------|-------------|
| `create_profile` | 创建独立浏览器指纹环境 |
| `launch` | 启动指纹浏览器实例 |
| `list_profiles` | 列出所有指纹环境 |
| `delete_profile` | 删除指纹环境 |

---

## fingerprint_engine

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI协作

> GBT自建浏览器指纹引擎 — 不依赖2Captcha，本地生成真实指纹，平台直接赚钱

### Actions

| Action | Description |
|--------|-------------|
| `random` | 随机真实浏览器指纹(Chromium格式) |
| `generate` | 按参数定制指纹(OS/浏览器/国家) |
| `browser_context` | 生成Playwright browser.new_context()完整参数 |
| `puppeteer_context` | 生成Puppeteer launch参数 |
| `stealth_config` | 完整隐身配置: launch_args+context+headers+cdp |
| `stats` | 指纹库统计(可用指纹数/覆盖OS/浏览器) |

### Triggers

- **Intent**: `fingerprint`
- **Keywords**: `指纹`, `fingerprint`, `浏览器指纹`, `隐身`, `stealth`, `反检测`
- **Examples**:
  - 生成美国Chrome指纹
  - Windows浏览器隐身配置
  - Playwright隐身上下文

---

## firecrawl_mcp

**版本**: 1.0.0 | **风险**: `medium` | **分类**: AI知识

> Firecrawl网页抓取 — 任意网站→干净Markdown+结构化提取 (~143k GitHub stars)

### Actions

| Action | Description |
|--------|-------------|
| `scrape` | 抓取单个URL, 返回干净Markdown/HTML/结构化数据 |
| `crawl` | 爬取整个网站, 批量提取所有页面 |
| `extract` | 用LLM从页面提取结构化数据(schema验证) |

### Triggers

- **Intent**: `web_scrape`
- **Keywords**: `firecrawl`, `网页抓取`, `爬虫`, `scrape web`, `网站提取`, `crawl site`
- **Examples**:
  - 用Firecrawl抓这个网页
  - 爬取整个文档站
  - 提取这个页面的结构化数据

---

## five_sim

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

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

### Triggers

- **Intent**: `forensic_collector`
- **Keywords**: `forensic`, `evidence`, `取证`, `证据`, `数字取证`

---

## fund_pool

**版本**: 1.0.0 | **风险**: `safe` | **分类**: Finance

> GBT 用户资金池系统 · 内部虚拟账本 + 管理员面板

### Actions

| Action | Description |
|--------|-------------|
| `user_create` |  |
| `user_balance` |  |
| `deposit` |  |
| `withdraw` |  |
| `transfer` |  |
| `pool_status` |  |
| `tx_history` |  |
| `admin_list` |  |
| `freeze` |  |
| `unfreeze` |  |
| `withdraw_approve` |  |
| `withdraw_reject` |  |

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

## gbt_browser

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 浏览器

> GBT隐身浏览器：15维浏览器指纹生成/隐身浏览器启动/反检测请求头/持久化配置管理

### Actions

| Action | Description |
|--------|-------------|
| `generate_fingerprint` | 生成完整的15维浏览器指纹（UA/分辨率/时区/语言/字体/WebGL等） |
| `launch_browser` | 启动隐身浏览器（自动选择SeleniumBase或Playwright引擎） |
| `stealth_headers` | 生成一次性随机反检测HTTP请求头 |
| `create_profile` | 创建持久化浏览器配置文件 |
| `list_profiles` | 列出所有已保存的浏览器配置文件 |
| `delete_profile` | 删除指定名称的浏览器配置文件 |
| `status` | 查看浏览器引擎可用性状态 |

---

## gbt_gigs

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 特殊域

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

## gener

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 内容生成

> 内容生成工具集：二维码文件/电子名片/HTML表单/Sitemap/robots.txt

### Actions

| Action | Description |
|--------|-------------|
| `qrcode_file` | 生成二维码PNG文件到磁盘 |
| `vcard` | 生成 vCard 电子名片(.vcf文件) |
| `form_html` | 根据字段定义生成HTML表单 |
| `sitemap` | 生成 sitemap.xml |
| `robots` | 生成 robots.txt |

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

## github_oauth

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI协作

> GitHub OAuth开发者授权 · 对标Whop Connect · 登录→授权→读代码→提交部署

### Actions

| Action | Description |
|--------|-------------|
| `browse` | browse |
| `exchange` | OAuth code换access_token |
| `list_repos` | 列出已授权用户仓库 |
| `login_url` | 生成GitHub OAuth登录URL |
| `read_file` | read_file |
| `run` | run |
| `status` | 查询授权状态 |
| `submit` | 提交仓库进行部署评估 |

### Triggers

- **Intent**: `github_oauth`
- **Keywords**: `github`, `登录`, `授权`, `oauth`, `提交项目`, `deploy repo`, `connect github`

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
| `caps` | 列出所有能力模块状态 |
| `check` | 全系统健康检查 (53caps + 资源 + 后端) |
| `help` | help |
| `list` | list |
| `live_check` | 实时健康扫描 (nexus邻域+语法验证+缓存60s) |
| `quick` | 快速检查 (仅资源+后端) |
| `self_test` | self_test |

### Triggers

- **Intent**: `health_check`
- **Keywords**: `健康`, `状态`, `面板`, `dashboard`, `health`, `诊断`, `概览`
- **Examples**:
  - 系统健康检查
  - 看看所有模块状态

---

## human_task

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI协作

> Human-in-the-Loop人类任务委托 — HumanAPI集成+本地队列+自动审批

### Actions

| Action | Description |
|--------|-------------|
| `complete` | 标记任务完成(人类提交结果) |
| `create` | 创建人类任务(8种类型) |
| `list` | 列出任务队列 |
| `run` | run |
| `status` | HumanAPI状态+任务统计 |
| `types` | 列出支持的任务类型 |

### Triggers

- **Intent**: `human_task`
- **Keywords**: `人类任务`, `human task`, `委托`, `找人`, `人工`, `human in the loop`, `物理世界`, `实地`, `录音`, `标注`, `humanapi`, `thehumanapi`

---

## identity_forge

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 特殊域

> identity_forge

### Actions

| Action | Description |
|--------|-------------|
| `generate` | 生成身份 |

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

## imager

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 图像处理

> 图片处理工具：压缩/缩放/格式转换/信息/裁剪/水印 — 基于Pillow

### Actions

| Action | Description |
|--------|-------------|
| `compress` | 图片压缩（调整quality） |
| `resize` | 图片缩放（指定宽度/高度/缩放比） |
| `convert` | 格式转换（png↔jpg↔webp↔bmp） |
| `info` | 获取图片信息（尺寸/格式/文件大小） |
| `crop` | 图片裁剪（x,y,w,h） |
| `watermark` | 文字水印 |

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
| `sanitize_pipeline` | 56条规则全管道净化 |
| `test_injection` | 30种注入向量测试 |
| `auto_learn_rule` | 分析绕过尝试并建议新规则 |

### Triggers

- **Intent**: `input_sanitizer`
- **Keywords**: `sanitize`, `sanitizer`, `净化`, `安全检查`, `注入检测`, `input`, `防注入`

---

## jwt_tester

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> JWT令牌安全测试

### Actions

| Action | Description |
|--------|-------------|
| `test` | 测试JWT安全性 |
| `forge` | 尝试伪造JWT |

---

## keylogger

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 桌面域

> keylogger capability

### Actions

| Action | Description |
|--------|-------------|
| `start` | 开始记录 |
| `stop` | 停止记录 |
| `dump` | 导出记录 |

---

## local_eye

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 感知域

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
| `anomaly_detect` | anomaly_detect |
| `pattern_learn` | pattern_learn |
| `tail_errors` | tail_errors |

### Triggers

- **Intent**: `log_analyzer`
- **Keywords**: `log`, `日志`, `分析`, `error log`, `syslog`

---

## mcp_bridge

**版本**: 1.0.0 | **风险**: `medium` | **分类**: AI协作

> GBT↔MCP通用桥接 — 连接所有Model Context Protocol服务(Claude生态顶级能力)

### Actions

| Action | Description |
|--------|-------------|
| `list_tools` | 列出某MCP服务的全部可用工具 |
| `call_tool` | 调用MCP工具 — Context7/GitHub/Firecrawl/Stripe/Playwright等 |
| `list_servers` | 列出所有已配置的MCP服务器及状态 |

### Triggers

- **Intent**: `mcp_bridge`
- **Keywords**: `mcp`, `context7`, `firecrawl`, `stripe mcp`, `github mcp`, `playwright mcp`, `web scrape`, `real docs`
- **Examples**:
  - 用Context7查最新React文档
  - 用Firecrawl抓这个页面
  - 列出所有MCP工具

---

## memory

**版本**: 2.0.0 | **风险**: `safe` | **分类**: AI

> 记忆系统 v2 — AI持久记忆(TTL/搜索/命名空间/统计)

### Actions

| Action | Description |
|--------|-------------|
| `auto_tag` | auto_tag |
| `clear` | 清空全部记忆或指定命名空间 |
| `decay` | 记忆衰减 — TTL过期自动清理 |
| `delete` | 删除指定key的记忆 |
| `mem0_add` | Mem0添加长期记忆 |
| `mem0_search` | Mem0语义搜索记忆 |
| `recall` | 回忆指定key或列出所有 |
| `save` | 保存记忆 (支持 ttl_sec 过期时间) |
| `search` | 搜索记忆 (匹配key和value) |
| `search_semantic` | search_semantic |
| `stats` | 记忆统计 (数量/大小/命名空间) |
| `summarize_session` | summarize_session |
| `timeline` | 时间线视图 — 按时间浏览记忆 |
| `vector_search` | 语义向量搜索记忆 |

### Triggers

- **Intent**: `memory`
- **Keywords**: `记忆`, `memory`, `记录`, `回忆`, `搜索记忆`, `删除记忆`
- **Examples**:
  - 保存记忆
  - 回忆一下
  - 搜索记忆

---

## memory_dumper

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> memory_dumper capability

### Actions

| Action | Description |
|--------|-------------|
| `dump` | 内存转储 |

---

## metrics_exporter

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 运维域

> Prometheus指标导出器 — /metrics /json /push

### Actions

| Action | Description |
|--------|-------------|
| `collect_all` | collect_all |
| `json` | 返回JSON格式指标 |
| `metrics` | 返回Prometheus text/plain指标 |
| `prometheus_format` | prometheus_format |
| `trend_report` | trend_report |

---

## migration

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 基础设施

> 数据库迁移 — schema版本管理/迁移/回滚

### Actions

| Action | Description |
|--------|-------------|
| `auto_migrate` | auto_migrate |
| `create` | 创建新迁移文件 |
| `init` | 初始化迁移表 |
| `migrate` | 运行待处理的迁移 |
| `rollback` | 回滚最近一次迁移 |
| `status` | 查看迁移状态 |
| `validate_schemas` | validate_schemas |

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

## miniapp

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 部署发布

> 微信小程序一键生成部署 · 多行业模板 · 零代码

### Actions

| Action | Description |
|--------|-------------|
| `create` | 脚手架新小程序项目(复制模板+替换变量) |
| `deploy` | 生成部署指南+微信开发者工具CLI命令 |
| `info` | 查看模板详情(页面结构/变量) |
| `list` | 列出所有可用模板 |
| `run` | run |

### Triggers

- **Intent**: `miniapp_deploy`
- **Keywords**: `小程序`, `miniapp`, `微信小程序`, `wechat`, `部署小程序`, `发布小程序`
- **Examples**:
  - 创建一个电商小程序
  - 微信小程序怎么部署
  - 生成一个小程序

---

## mirror_fusion

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 镜像多维度空间(5层实验隔离) — 委托到 brain.mirror_fusion

### Actions

| Action | Description |
|--------|-------------|
| `experiment` | experiment |
| `layers` | layers |

---

## multi_llm

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 多模型网关 — 7大模型自动切换/降级/负载均衡: Kimi/DeepSeek/OpenAI/Zhipu/Qwen/Ollama/SiliconFlow

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

## n8n_automation

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 运维域

> N8N全局自动化编排·三大核心工作流:支付分账+部署监控+邻域巡检

### Actions

| Action | Description |
|--------|-------------|
| `generate_all` | 一键生成全部3个N8N工作流 |
| `generate_deploy` | 生成部署自动化工作流 |
| `generate_monitor` | 生成全局监控工作流 |
| `generate_payment` | 生成支付自动化工作流 |
| `list` | 列出已有工作流 |
| `run` | run |
| `status` | N8N运行状态 |

### Triggers

- **Intent**: `n8n_automation`
- **Keywords**: `n8n`, `workflow`, `自动化`, `编排`, `webhook`, `payment flow`

---

## native_vision

**版本**: 2.0.0 | **风险**: `safe` | **分类**: 感知

> 原生视觉邻域 — GBT的眼睛和手, 直连宿主硬件零延迟, 所有邻域可随时调用

### Actions

| Action | Description |
|--------|-------------|
| `analyze` | analyze |
| `browse_and_interact` | browse_and_interact |
| `browse_feed` | browse_feed |
| `browse_screen` | browse_screen |
| `browse_scroll` | browse_scroll |
| `buffer_stats` | buffer_stats |
| `click` | click |
| `colors_at` | colors_at |
| `compare` | compare |
| `double_click` | double_click |
| `drag` | drag |
| `find` | find |
| `find_all` | find_all |
| `hotkey` | hotkey |
| `latest` | latest |
| `look_and_click` | look_and_click |
| `look_and_type` | look_and_type |
| `look_deep` | look_deep |
| `move` | move |
| `move_to_text` | move_to_text |
| `movie` | movie |
| `movie_analyze` | movie_analyze |
| `movie_record` | movie_record |
| `paste` | paste |
| `press` | press |
| `read` | read |
| `read_all` | read_all |
| `right_click` | right_click |
| `screenshot_region` | screenshot_region |
| `scroll` | scroll |
| `see` | see |
| `select_all_copy` | select_all_copy |
| `start_watching` | start_watching |
| `stop_watching` | stop_watching |
| `to_annotated` | to_annotated |
| `to_image` | to_image |
| `type` | type |
| `type_and_enter` | type_and_enter |
| `wait_for` | wait_for |
| `wait_for_async` | wait_for_async |
| `wait_for_stable` | wait_for_stable |
| `wait_until_gone` | wait_until_gone |

### Triggers

- **Intent**: `native_vision`
- **Keywords**: `看`, `看见`, `看到`, `查看屏幕`, `截图`, `找`, `寻找`, `定位`, `识别文字`, `OCR`, `点击`, `移动`, `输入`, `按键`, `拖拽`, `滚动`, `眼睛`, `手`, `视觉`, `屏幕`, `look`, `see`, `find`, `click`, `type`, `press`, `vision`, `eye`, `hand`, `screen`
- **Examples**:
  - 看看屏幕上有什么
  - 找到登录按钮并点击
  - 识别屏幕上的文字
  - 移动到坐标500,300
  - 输入hello world
  - 按回车键

---

## net_sniffer

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 侦察域

> 网络流量嗅探分析

### Actions

| Action | Description |
|--------|-------------|
| `start` | 开始嗅探 |
| `stop` | 停止嗅探 |
| `analyze` | 分析流量 |

---

## netter

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 开发工具

> 网络工具集：HTTP请求/DNS查询/TCP连通性/WHOIS/SSL证书/URL缩短

### Actions

| Action | Description |
|--------|-------------|
| `http` | HTTP 请求测试 (GET/POST/HEAD) |
| `dns` | DNS 记录查询 (A/AAAA/MX/NS/TXT/CNAME) |
| `ping` | TCP 端口连通性测试 |
| `whois` | WHOIS 域名信息查询 |
| `ssl` | SSL/TLS 证书信息查询 |
| `shorten` | URL 缩短 (调用公共API) |

---

## nexus_monitor

**版本**: 2.0.0 | **风险**: `safe` | **分类**: AI记忆

> 全局邻域感知监控·操作前检查·问题诊断·自动修复·持续watch·event_bus告警

### Actions

| Action | Description |
|--------|-------------|
| `auto_heal` | 自动修复常见问题(__pycache__/corrupt JSON) |
| `check` | 快速邻域健康检查 |
| `continuous` | 启动持续监控守护 |
| `deep_check` | 深度检查+修复建议 |
| `pre_flight` | 起飞前完整检查(部署/支付前) |
| `run` | run |
| `watch` | 持续监控+event_bus告警·start/stop/once/status |

### Triggers

- **Intent**: `nexus_monitor`
- **Keywords**: `监控`, `nexus`, `健康`, `health`, `检查`, `diagnose`, `修复`, `heal`

---

## omni_eye

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 感知域

> UIA直接遍历桌面所有窗口元素，返回name/state/rect结构化数据

### Actions

| Action | Description |
|--------|-------------|
| `see` | 遍历桌面所有窗口元素 |
| `focus` | 聚焦指定窗口 |

---

## oneclick_deploy

**版本**: 1.0.0 | **风险**: `medium` | **分类**: AI编程

> 一键部署引擎 — 克隆→检测→Docker化→安全审计→打包交付

### Actions

| Action | Description |
|--------|-------------|
| `deploy` | 克隆→检测→Docker化→安全审计→打包交付 |
| `deploy_remote` | 远程部署 — 通过已建立隧道连接部署到客户机器 |
| `status` | 查看所有部署状态 |
| `list` | 列出所有部署 |

### Triggers

- **Intent**: `deploy`
- **Keywords**: `部署`, `上线`, `deploy`, `一键部署`, `跑起来`

---

## osint_aggregator

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 侦察域

> OSINT情报聚合·公开信息收集与关联

### Actions

| Action | Description |
|--------|-------------|
| `aggregate` | 聚合多方情报数据 |

### Triggers

- **Intent**: `osint_aggregator`
- **Keywords**: `OSINT`, `intelligence`, `情报`, `公开信息`, `开源情报`

---

## osint_master

**版本**: 1.0.0 | **风险**: `safe` | **分类**: OSINT

> OSINT深度情报搜集 — 多源聚合(Shodan/HIBP/社交/DNS/邮箱)

### Actions

| Action | Description |
|--------|-------------|
| `autonomous_recon` | 自主侦察(全维度) |
| `breach` | 数据泄露查询(HIBP) |
| `dns` | DNS记录查询 |
| `email` | 邮箱情报分析 |
| `intel_fusion` | intel_fusion |
| `scheduled_scan` | 定时扫描任务 |
| `search` | 通用OSINT搜索 |
| `social` | 社交媒体情报 |

### Triggers

- **Intent**: `osint_master`
- **Keywords**: `osint`, `情报`, `侦察`, `信息搜集`, `社工`

---

## packet_crafter

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> 网络包构造·自定义数据包生成与注入

### Actions

| Action | Description |
|--------|-------------|
| `craft` | 构造网络数据包 |

### Triggers

- **Intent**: `packet_crafter`
- **Keywords**: `packet`, `craft`, `scapy`, `网络包`, `数据包`, `注入`

---

## payment_gateway

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 金融支付

> 支付网关路由：多通道智能路由、健康检查、降级切换

### Actions

| Action | Description |
|--------|-------------|
| `run` | 支付网关路由(route/health/fallback/list) |

---

## payments

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 金融支付

> 支付统一入口：支付方法调度、订单管理、退款、对账

### Actions

| Action | Description |
|--------|-------------|
| `cryptapi` | cryptapi |
| `list` | list |
| `run` | 支付统一入口(pay/query/refund/reconcile/list) |
| `stripe` | stripe |
| `webhook` | webhook |

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
| `clone` | clone |
| `generate` | 生成钓鱼邮件内容 |
| `list` | list |

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

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 侦察域

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

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> process_injector capability

### Actions

| Action | Description |
|--------|-------------|
| `dll` | dll |
| `inject` | 进程注入 |

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
| `tdd` | TDD驱动开发 — 红→绿→重构循环 |
| `verify` | 代码验证 — 编译检查+测试运行+lint扫描 |
| `brainstorm` | 头脑风暴 — 多方案生成+评估+择优 |
| `gitflow` | Git工作流 — 分支/PR/合并自动化 |

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

## project_registry

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI协作

> 项目注册中心·平台项目全生命周期·13个种子项目·注册·部署·上下架

### Actions

| Action | Description |
|--------|-------------|
| `deploy` | 部署/上下架项目 |
| `list` | 列出所有项目 |
| `register` | 注册新项目 |
| `run` | run |
| `stats` | 项目统计 |

### Triggers

- **Intent**: `project_registry`
- **Keywords**: `项目`, `project`, `部署`, `上下架`, `注册项目`

---

## project_state

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI

> 项目状态追踪 — 目标/进度/决策/上下文/跑偏检测。确保长时间工作不走偏不丢失上下文

### Actions

| Action | Description |
|--------|-------------|
| `auto_snapshot` | auto_snapshot |
| `checkpoint` | 保存上下文快照 (当前状态完整存档) |
| `diff_snapshots` | diff_snapshots |
| `drift_check` | 跑偏检测: 当前工作是否偏离目标 |
| `goal` | 设置/查看当前目标 (支持层级子目标) |
| `log` | 记录一条工作日志 (决策/完成/发现) |
| `progress` | 查看整体进度摘要 (目标/已完成/进行中/待办) |
| `restore_latest` | restore_latest |
| `resume` | 恢复上次工作状态 (加载最新快照) |

### Triggers

- **Intent**: `project_tracking`
- **Keywords**: `进度`, `状态`, `目标`, `做了什么`, `到哪里了`, `继续`, `恢复`, `跑偏`, `上下文`
- **Examples**:
  - 查看项目进度
  - 我们做到哪了
  - 继续上次的工作

---

## proxy_network

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 网络

> 2Captcha住宅代理网络 — 220+国家真实住宅IP · 自动轮换 · SOCKS5 · 按国家/城市/ASN筛选

### Actions

| Action | Description |
|--------|-------------|
| `account_info` | 获取代理账户信息(流量/白名单) |
| `balance` | 查询代理余额 |
| `list_countries` | 列出208个可用国家 |
| `list_regions` | 列出967个可用地区 |
| `list_cities` | 列出3145个可用城市 |
| `list_asns` | 列出可用ASN(运营商) |
| `generate_whitelist` | 生成白名单连接IP |

### Triggers

- **Intent**: `proxy_network`
- **Keywords**: `代理`, `proxy`, `住宅IP`, `residential`, `IP池`, `代理网络`, `翻墙`
- **Examples**:
  - 给我一个美国住宅代理
  - 列出代理可用国家
  - 查代理余额

---

## quantum_optimizer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 量子优化(跨维度资源调度)

### Actions

| Action | Description |
|--------|-------------|
| `optimize` | optimize |

---

## quantum_reasoner

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 量子推理(叠加态多路径并行推理)

### Actions

| Action | Description |
|--------|-------------|
| `qiskit_optimize` | qiskit_optimize |
| `reason` | reason |

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

## remote_control

**版本**: 1.0.0 | **风险**: `high` | **分类**: 网络域

> GBT远程操控 — 用户一键运行agent.py暴露本地服务+Chrome，GBT通过connect.py接入操控

### Actions

| Action | Description |
|--------|-------------|
| `connect` | connect |
| `expose` | expose |
| `run` | run |
| `scan` | scan |
| `status` | status |

### Triggers

- **Intent**: `remote_control`
- **Keywords**: `远程操控`, `远程控制`, `远程接入`, `remote control`, `remote agent`, `隧道`, `tunnel`, `CDP远程`, `操控用户电脑`, `远程浏览器`, `agent.py`

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
| `types` | types |

### Triggers

- **Intent**: `report_generator`
- **Keywords**: `report`, `报告`, `generate`, `生成`, `文档`

---

## reserve_pool

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 金融支付

> 储备池管理：资金预存、额度预留、释放与查询

### Actions

| Action | Description |
|--------|-------------|
| `run` | 储备池核心操作(reserve/release/deposit/withdraw/status) |

---

## revenue_split

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 金融支付

> 收入分账：按比例/固定金额拆分收入到多方账户

### Actions

| Action | Description |
|--------|-------------|
| `record_rental` | record_rental |
| `run` | 收入分账操作(split/preview/history) |

---

## root_cause_debugger

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 诊断

> 病因定位引擎 — 按 假设 -> 取证 -> 复现 -> 修复 -> 验证 的链路调查问题并归档证据

### Actions

| Action | Description |
|--------|-------------|
| `auto_debug` | auto_debug |
| `fix_attempt` | fix_attempt |
| `hypothesis` | hypothesis |
| `investigate` | 执行病因定位全流程，收集证据并输出根因报告 |
| `plan` | 生成病因排查计划和优先假设，不做深度取证 |

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

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 感知域

> 屏幕文字直接识别，不经过视觉模型

### Actions

| Action | Description |
|--------|-------------|
| `read` | 读取屏幕指定区域文字 |
| `read_all` | 读取全屏文字 |

---

## screenpipe_monitor

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 感知域

> 持续屏幕变化感知，实时监控

### Actions

| Action | Description |
|--------|-------------|
| `start` | 开始监控 |
| `stop` | 停止监控 |
| `status` | 查看状态 |

---

## screenshot

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 感知域

> 截图备用兜底，视觉只做补证

### Actions

| Action | Description |
|--------|-------------|
| `capture` | 截取屏幕 |
| `capture_region` | 截取指定区域 |

---

## secer

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 安全工具

> 安全工具集：强密码生成/熵评估/JWT解码/文件哈希/安全随机数/多编码转换

### Actions

| Action | Description |
|--------|-------------|
| `password` | 强密码生成（secrets模块，可配置字符集和长度） |
| `entropy` | 密码强度评估（熵值计算+常见模式检测+键盘路径检测 |
| `jwt_decode` | JWT解码（不验证签名，仅解析header/payload） |
| `hash_file` | 文件哈希计算（MD5/SHA1/SHA256） |
| `random` | 安全随机生成（int/float/bytes/string/uuid/token_hex/token_urlsafe/choice/sample） |
| `encode` | 多编码转换（hex/rot13/morse/base64/url） |

---

## security_scan

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 安全域

> 密钥泄露+危险模式全面扫描

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 全面安全扫描 |
| `keys` | 扫描密钥泄露 |
| `patterns` | 扫描危险模式 |
| `auto_audit_cycle` | 周期性全cap安全审计 |
| `score_cap` | 单cap安全评分0-100 |

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
| `auto_evolve_cycle` | auto_evolve_cycle |
| `capture` | capture |
| `cross_session_merge` | cross_session_merge |
| `evolve` | evolve |
| `insights` | insights |
| `learn` | learn |
| `metrics` | metrics |
| `recall` | recall |
| `search` | search |
| `timeline` | timeline |

### Triggers

- **Intent**: `self_evolution`
- **Keywords**: `进化`, `evolve`, `学习`, `优化`, `自改进`, `升级`, `迭代`
- **Examples**:
  - 自我进化
  - 学习这次的经验

---

## simulation_env

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI协作

> 模拟/游戏环境 — OpenAI Gym + 自定义RL训练环境

### Actions

| Action | Description |
|--------|-------------|
| `list` | 列出可用模拟环境 |
| `run` | 运行指定的模拟环境 |
| `status` | 查看模块状态 |

### Triggers

- **Intent**: `simulation_env`
- **Keywords**: `simulation`, `game`, `gym`, `environment`, `rl`, `模拟`, `游戏`
- **Examples**:
  - 列出模拟环境
  - 运行CartPole
  - RL训练

---

## skill_library

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 编程域

> 生产级工程技能库 · 融合 addyosmani/agent-skills (79k⭐)。Define→Plan→Build→Verify→Review→Ship 六阶段，24项技能+4个AI代理角色。

### Actions

| Action | Description |
|--------|-------------|
| `activate` | 根据上下文自动激活匹配技能 |
| `agents` | 列出/激活专业AI代理(审查员/审计员/测试员/性能审计) |
| `auto_catalog` | auto_catalog |
| `build` | 增量构建: TDD+一次一个切片 |
| `learn_from_devourer` | learn_from_devourer |
| `plan` | 任务规划: 拆分为小型原子任务 |
| `review` | 代码审查: 五轴质量门 |
| `ship` | 发布上线: 越快越安全 |
| `skill_gap_report` | skill_gap_report |
| `skills` | 列出所有24项技能 |
| `spec` | 需求定义: 先写规格再写代码 |
| `test` | 验证: 测试是证明不是装饰 |

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
| `broadcast` | broadcast |
| `list_channels` | list_channels |
| `list_users` | list_users |
| `read_slack` | read_slack |
| `run` | Execute Slack/Discord task |
| `send_discord` | send_discord |
| `send_slack` | 发送Slack消息通知·N8N工作流集成 |

### Triggers

- **Intent**: `slack_bot`
- **Keywords**: `slack`, `discord`, `webhook`, `bot`

---

## smart_scheduler

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 运维域

> 智能任务调度

### Actions

| Action | Description |
|--------|-------------|
| `cancel` | cancel |
| `chain_tasks` | chain_tasks |
| `cron_schedule` | cron_schedule |
| `list` | 列出调度 |
| `persist_queue` | Save full task queue to ~/.gbt/schedule_persist.json |
| `restore_queue` | Restore task queue from ~/.gbt/schedule_persist.json |
| `results` | results |
| `schedule` | 调度任务 |
| `self_start` | self_start |
| `start_worker` | start_worker |
| `stop_worker` | stop_worker |

---

## social_engineer

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> 社会工程攻击·目标画像与社工策略

### Actions

| Action | Description |
|--------|-------------|
| `generate` | generate |
| `tactics` | tactics |

### Triggers

- **Intent**: `social_engineer`
- **Keywords**: `social engineer`, `社工`, `社会工程`, `profile`, `pretext`

---

## sqli_tester

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

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
| `add_fact` | 添加已确认事实到黑板 |
| `anti_hallucination` | 证据级反幻觉验证 |
| `converge` | 判断是否已达成目标 |
| `detect_loop` | detect_loop |
| `escalate` | L0-L4渐进升级策略 |
| `escape_loop` | escape_loop |
| `execute` | 执行探索方向→产出新Fact |
| `explore_branch` | explore_branch |
| `init` | 初始化状态空间(origin→goal) |
| `propose` | 大脑提出探索方向(防重复) |
| `status` | 查看状态空间全貌 |

---

## steganography

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

> 隐写术·LSB+DCT信息隐藏与提取

### Actions

| Action | Description |
|--------|-------------|
| `extract` | extract |
| `hide` | hide |

### Triggers

- **Intent**: `steganography`
- **Keywords**: `steganography`, `隐写`, `stego`, `LSB`, `hidden`

---

## stock_browser_trader

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 金融域

> A股AI量化操盘融合引擎 — 指纹浏览器 + AI推理 + 实时行情 + 屏幕视觉

### Actions

| Action | Description |
|--------|-------------|
| `ai_browser_scan` | ai_browser_scan |
| `ai_browser_trade` | ai_browser_trade |
| `alert_on_signal` | alert_on_signal |
| `analyze_chart` | K线图AI分析 |
| `analyze_stock` | 个股深度分析+AI推理 |
| `auto_trade` | 一键自动操盘流水线 |
| `autonomous_patrol` | autonomous_patrol |
| `browse_market` | browse_market |
| `capture_screen` | 截图(base64) |
| `daily_report` | daily_report |
| `daily_review` | 每日复盘 |
| `engine_status` | 引擎状态 |
| `knowledge` | 查询A股知识库 |
| `launch_browser` | launch_browser |
| `look_and_trade` | look_and_trade |
| `market_sentiment` | market_sentiment |
| `ocr_screen` | OCR+AI解读 |
| `place_order` | 模拟下单+AI审核 |
| `risk_check` | 风控检查 |
| `scan_hot_sectors` | 热门板块扫描 |
| `scan_market` | 全市场扫描+AI筛选 |
| `setup_platform` | 创建指纹浏览器配置文件 |
| `watch_market` | watch_market |

---

## stock_trader

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 金融域

> A股自动操盘-选股/分析/下单/风控/复盘

### Actions

| Action | Description |
|--------|-------------|
| `analyze` | 深度技术分析 |
| `order` | 自动下单交易 |
| `positions` | 持仓查询 |
| `review` | 交易复盘 |
| `risk` | 风控评估 |
| `run` | run |
| `scan` | 智能选股扫描 |

---

## stress_test

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 特殊域

> 压力测试/性能测试

### Actions

| Action | Description |
|--------|-------------|
| `run` | 运行压力测试 |
| `report` | 生成测试报告 |

---

## strix

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> 综合渗透测试框架

### Actions

| Action | Description |
|--------|-------------|
| `test` | 综合渗透测试 |
| `exploit` | 漏洞利用 |
| `deep` | 深度递归穿透·双脑巅峰运转 |

---

## sub_agent_mgr

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 调度编排

> 无限制子代理隔离执行层 — 独立进程+思维导图+证据链

### Actions

| Action | Description |
|--------|-------------|
| `__worker_loop` | __worker_loop |
| `auto_scale` | auto_scale |
| `evidence` | 获取完整证据链（每步输出） |
| `execute` | 执行已生成的代理（断点续跑） |
| `kill` | 终止指定子代理 |
| `mindmap_preview` | 只预览思维导图，不执行 |
| `persistent_pool` | persistent_pool |
| `spawn` | 生成子代理+LLM生成思维导图+立即执行 |
| `spawn_dag` | spawn_dag |
| `status` | 查询所有子代理状态 |
| `task_queue` | task_queue |

### Triggers

- **Intent**: `sub_agent`
- **Keywords**: `子代理`, `spawn`, `多步任务`, `隔离执行`, `agent`, `思维导图`
- **Examples**:
  - 生成子代理执行任务
  - 查看子代理状态

---

## subdomain_enum

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 侦察域

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
| `plan` | plan |

---

## sys_control

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 桌面域

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
| `auto_backup_cycle` | auto_backup_cycle |
| `backup` | 备份~/.gbt/和caps/目录到zip |
| `backup_on_change` | backup_on_change |
| `cleanup` | 保留最近N个备份，删除旧备份 |
| `help` | help |
| `list` | 列出所有可用备份 |
| `list_files` | list_files |
| `restore` | 从备份zip恢复 |
| `run` | run |
| `self_test` | self_test |

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
| `ascii_tree` | 生成ASCII树形图 — 纯文本可打印 |
| `checklist` | 生成执行检查清单 — 每步可勾选 |
| `decompose_auto` | decompose_auto |
| `flowchart` | 生成Mermaid流程图 — 决策分支+执行路径 |
| `gantt` | 生成甘特图时间线 — 预估每步耗时 |
| `langgraph_export` | langgraph_export |
| `mindmap` | 生成Mermaid思维导图 — 可视化任务结构 |
| `plan` | 任务规划 — 分解为精细步骤(分钟级)，生成思维导图JSON |

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

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 信息域

> Telegram Bot接口

### Actions

| Action | Description |
|--------|-------------|
| `send` | 发送消息 |
| `read` | 读取消息 |
| `listen` | 监听频道 |

---

## tg_client

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 信息域

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

### Triggers

- **Intent**: `threat_hunter`
- **Keywords**: `threat hunt`, `威胁狩猎`, `IOC`, `APT`, `威胁`

---

## tool_adapter

**版本**: 1.0.0 | **风险**: `medium` | **分类**: AI协作

> 工具适配器 — 桥接HOST_BODY能力到可用OMP工具，按优先级路由：原生OMP工具 → 本地Python库 → 子进程cap调用

### Actions

| Action | Description |
|--------|-------------|
| `map_tool` | 将cap风格的动作名映射到最佳可用工具路由决策 |
| `list_available` | 扫描当前环境中实际可用的工具类型 |
| `call_tool` | 通过适配器路由执行工具调用 |

### Triggers

- **Intent**: `tool_routing`
- **Keywords**: `工具适配`, `tool adapter`, `路由`, `screenshot`, `桌面点击`, `OCR`, `desktop click`
- **Examples**:
  - 截图用什么工具
  - 有哪些可用工具
  - 调用screenshot工具

---

## toolbox

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 开发工具

> 多宝盒工具集：JSON格式化/Base64/URL编解码/哈希/时间戳/UUID/二维码/差异对比/正则测试

### Actions

| Action | Description |
|--------|-------------|
| `json_fmt` | JSON 格式化/压缩/验证 |
| `base64` | Base64 编解码 |
| `url` | URL 编解码和解析 |
| `hash` | MD5/SHA1/SHA256 哈希计算 |
| `timestamp` | 时间戳与日期互转 |
| `uuid` | 生成 UUID v4 |
| `qrcode` | 文本生成二维码(base64 PNG) |
| `diff` | 文本差异对比 |
| `regex` | 正则表达式测试器 |

---

## tp_connect

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 金融域

> TokenPocket Wallet Connect 集成 · 多链(EVM+TRON+SOL) · 零私钥接触

### Actions

| Action | Description |
|--------|-------------|
| `balance` | 查询多链余额 |
| `chains` | 列出支持的区块链 |
| `connect` | 连接 TokenPocket 钱包 |
| `list` | list |
| `run` | run |
| `self_test` | self_test |
| `verify_deposit` | 验证链上充值交易 |

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

## trending_scanner

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI编程

> GitHub Trending实时扫描 — 每日抓取GitHub Trending更新排行榜

### Actions

| Action | Description |
|--------|-------------|
| `scan` | 全量扫描GitHub Trending — 所有主流语言+综合排行 |
| `leaderboard` | 返回排行榜 — 从缓存读取 |
| `refresh` | 强制刷新 — 清除缓存重新扫描 |
| `list` | 列出排行榜(同leaderboard) |

### Triggers

- **Intent**: `trending`
- **Keywords**: `趋势`, `排行`, `热门`, `trending`, `leaderboard`, `排行榜`

---

## verter

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 开发工具

> 万能转换器：单位换算/进制转换/颜色转换/数字格式化/实时汇率，零外部依赖

### Actions

| Action | Description |
|--------|-------------|
| `unit` | 单位换算 (长度/重量/温度/存储/时间/面积/体积/速度/压强) |
| `base` | 进制转换 (2/8/10/16/36进制互转) |
| `color` | 颜色转换 (HEX↔RGB↔HSL) |
| `number` | 数字格式化 (千分位/中文大写/科学计数/百分比/保留小数/文件大小/罗马数字) |
| `currency` | 实时汇率换算 (内置固定汇率表，覆盖主要货币) |

---

## video_edit

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 媒体域

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

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 媒体域

> LTX-2 22B DiT音视频同步生成(8种模式)

### Actions

| Action | Description |
|--------|-------------|
| `generate` | 生成视频 |
| `hunyuan_local` | hunyuan_local |
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
| `list_engines` | list_engines |
| `speak` | 播报文字 |
| `speak_kokoro` | speak_kokoro |

### Triggers

- **Intent**: `speak`
- **Keywords**: `说话`, `语音`, `播报`, `speak`, `tts`, `朗读`, `念`
- **Examples**:
  - 说句话
  - 朗读这段文字

---

## waf_bypass

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> WAF绕过(大小写/编码/分块)

### Actions

| Action | Description |
|--------|-------------|
| `bypass` | 尝试绕过WAF |
| `encode` | 编码变形绕过 |
| `chunk` | 分块传输绕过 |

---

## wallet

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 金融域

> 用户钱包 · 实时币价(CoinGecko) · 转账风控扫描 · 交易记录

### Actions

| Action | Description |
|--------|-------------|
| `balance` | 查询用户虚拟余额 |
| `coin_prices` | 获取实时加密货币价格 (BTC/ETH/USDC/SOL等10种) |
| `history` | history |
| `list` | list |
| `prices` | prices |
| `risk_scan` | 扫描收款地址风险 (欺诈检测) |
| `run` | run |
| `scan` | scan |
| `self_test` | self_test |
| `send` | send |
| `transfer` | 发起转账 (含自动风控扫描) |
| `tx_history` | 交易记录查询 |

---

## waveform_collapse

**版本**: 1.0.0 | **风险**: `safe` | **分类**: 量子邻域

> 波函数坍缩(多路径→最优路径)

### Actions

| Action | Description |
|--------|-------------|
| `collapse` | collapse |

---

## web_api

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI协作

> GBT Web API服务器 — 连接前端网站到后端cap · 支付·OAuth·部署·分账

### Actions

| Action | Description |
|--------|-------------|
| `help` | help |
| `list` | list |
| `run` | run |
| `self_test` | self_test |
| `serve` | 启动API服务器(端口9878) |

### Triggers

- **Intent**: `web_api_serve`
- **Keywords**: `api`, `server`, `web`, `http`

---

## web_deploy_3d

**版本**: 1.0.0 | **风险**: `safe` | **分类**: AI创作

> GBT 3D 网页部署 — 粒子环·3D地球·光效连线·视差滚动·移动降级

### Actions

| Action | Description |
|--------|-------------|
| `get_design_context` | 返回AI设计网页时必须遵守的3D规范 |
| `manifest` | manifest |

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

**版本**: 1.0.0 | **风险**: `medium` | **分类**: 侦察域

> wifi_scanner capability

### Actions

| Action | Description |
|--------|-------------|
| `scan` | WiFi扫描 |

---

## win_control

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 桌面域

> Windows原生16类操控

### Actions

| Action | Description |
|--------|-------------|
| `control` | Windows原生操控 |
| `kill` | kill |
| `registry` | 注册表操作 |

---

## xss_tester

**版本**: 1.0.0 | **风险**: `dangerous` | **分类**: 攻击域

> XSS跨站脚本检测

### Actions

| Action | Description |
|--------|-------------|
| `test` | 测试XSS注入点 |
| `reflected` | 反射型XSS检测 |
| `stored` | 存储型XSS检测 |

---
