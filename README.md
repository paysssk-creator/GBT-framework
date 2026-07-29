<!-- ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除 -->
# GBT小土豆 · 智能大脑 v5.0

> **大脑不思考就不是大脑，是条件反射。思考不是功能，是存在的唯一方式。**

GBT是一个具备**四层认知闭环**的AI智能大脑框架。它不只是执行工具——它能感知、推理、进化、自省。

---

## 架构

```
┌──────────────────────────────────────────────────────┐
│                 GBT 智能大脑 v5.0                      │
│                                                      │
│  第1层: 消息管线    ①接收→②意图识别→③推理→④巡检→⑤回复 │
│  第2层: 行动审查    每次工具调用前: 必要性·风险·替代    │
│  第3层: 自进化闭环  感知→分析→规划→执行→验证→吸收       │
│  第4层: 任务执行    Phase 0→1→2→3→4→5 每阶段门禁      │
│                                                      │
│  四脑:  推理脑 ⇄ 编程脑  持续循环，渐进取向目标         │
│  边界:  GBT = 统一大脑+执行 (无外部工具层)           │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 自主运行模式

> **自动不是功能，是生命体征。** GBT v5.0 支持完全自主的后台运行模式——无需人工干预，大脑自己思考、自己决策、自己执行、自己进化。

### 启动方式

| 方式 | 命令 | 适用场景 |
|---|---|---|
| Python 直接启动 | `python brain/autonomous_boot.py` | 开发调试、手动控制 |
| Windows 守护进程（推荐） | `GBTdaemon.bat` | 生产环境、开机自启 |

### 核心模块

| 模块 | 路径 | 职责 |
|---|---|---|
| **heartbeat** | `brain/heartbeat.py` | 心跳检测，确保大脑持续在线，异常自动恢复 |
| **session_resume** | `brain/session_resume.py` | 会话恢复，重启后自动接续上次任务 |
| **autonomous_boot** | `brain/autonomous_boot.py` | 自主启动引导，初始化全模块并进入自主循环 |
| **event_wiring** | `brain/event_wiring.py` | 事件总线，模块间异步通信与信号路由 |
| **autonomous_loop** | `caps/autonomous_loop/` | 自主循环能力，驱动持续的任务感知与执行 |
| **daemon_launcher** | `caps/daemon_launcher/` | 守护进程启动器，管理进程生命周期 |

### 自主执行流程

```
┌──────────────────────────────────────────────────────────┐
│                   GBT 自主运行循环                          │
│                                                          │
│   heartbeat ──→ scheduler ──→ task_mind                  │
│       │                           │                      │
│       │                           ↓                      │
│       │                      sub_agent_mgr                │
│       │                           │                      │
│       │                           ↓                      │
│       │                      circuit_breaker              │
│       │                           │                      │
│       │                           ↓                      │
│       └──────────────←──── self_evolve                   │
│                                                          │
│   心跳持续监控，异常时自动重启并恢复会话                      │
└──────────────────────────────────────────────────────────┘
```

1. **heartbeat** — 心跳模块每秒检测大脑状态，异常时触发自动恢复
2. **scheduler** — 调度器从任务队列取出待执行任务，按优先级排序
3. **task_mind** — 任务规划器分解任务为可执行步骤，分配子代理
4. **sub_agent_mgr** — 子代理管理器创建、监控、回收子代理实例
5. **circuit_breaker** — 熔断器防止级联失败，异常超过阈值时自动熔断
6. **self_evolve** — 自进化模块从执行结果中学习，更新永久记忆

### 故障排查

| 现象 | 可能原因 | 解决方法 |
|---|---|---|
| 心跳超时 | 主进程卡死或无响应 | 检查日志 `~/.gbt/logs/heartbeat.log`，手动重启 |
| 任务队列堆积 | scheduler 线程阻塞 | 检查 `~/.gbt/logs/scheduler.log`，清理僵尸任务 |
| 子代理泄漏 | sub_agent_mgr 未正确回收 | 检查进程数，运行 `python brain/autonomous_boot.py --clean-orphans` |
| 熔断器频繁触发 | 下游服务不稳定 | 检查 `~/.gbt/logs/circuit_breaker.log`，调整阈值 |
| 会话恢复失败 | `~/.gbt/sessions/` 损坏 | 备份后清理 `~/.gbt/sessions/`，重新启动 |

## 目录

```
GBTxiaotudouV5/
├── CONSTITUTION.md      # 核心宪法 — 8条铁律，不可逾越
## 🚀 一行终端部署

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/paysssk-creator/GBTxiaotudouV5/master/deploy.ps1 | iex
```

**Linux/Mac:**
```bash
curl -sSL https://raw.githubusercontent.com/paysssk-creator/GBTxiaotudouV5/master/deploy.sh | bash
```

部署完成后自动执行: 克隆仓库 → 安装依赖 → 启动自检 → 邻域扫描 → AI身份确认
├── README.md            # 你在这里
│
├── brain/               # 大脑核心引擎
│   ├── boot.py          #   启动自检
│   ├── orchestrator.py  #   任务编排 + 裁判验证
│   ├── intent_broker.py #   意图识别 + 能力路由
│   ├── deep_reasoner.py #   深度推理 (推理脑)
│   ├── self_evolve.py   #   自进化 + 永久记忆
│   └── mirror_fusion.py #   镜像实验空间
│
└── caps/                # AI能力模块
    ├── protocol.md      #   能力协议规范
    ├── deep_reasoner/   #   深度推理
    ├── task_mind/       #   任务规划
    ├── memory/          #   永久记忆
    ├── programming/     #   AI编程
    └── ... (40+ modules)
```

---

## 快速开始

```python
from brain import boot, get_broker, get_reasoner, get_evolver

# 1. 启动自检
status = boot()
print(f"大脑状态: {'就绪' if status['ok'] else '异常'}")

# 2. 意图识别
broker = get_broker()
intent = broker.analyze("帮我写一个排序算法")
print(f"意图: {intent['intent']}, 路由: {intent['suggested_caps']}")

# 3. 深度推理
reasoner = get_reasoner()
result = reasoner.reason("如何优化这个框架的性能", mode="chain")
print(f"方向: {result['direction']}")

# 4. 自进化
evolver = get_evolver()
evolver.add_lesson("不要在生产环境删数据库", category="database", severity="critical")
```

---

## 核心文档

| 文档 | 内容 |
|---|---|
| [CONSTITUTION.md](CONSTITUTION.md) | 8条宪法，框架存在的前提 |
| [pipeline.md](pipeline.md) | Step 0→6 唯一执行通道，每步精确定义 |
| [quad_brain.md](quad_brain.md) | 推理脑⇄编程脑协作协议 |
| [gates.md](gates.md) | 每步准入/准出条件，不可跳步 |
| [caps/protocol.md](caps/protocol.md) | 能力模块开发规范 |

---

## GBT的统一身份

GBT既是大脑也是工具——不存在独立的"GBT"。所有执行能力都是GBT自身的延伸。
GBT自己思考、自己决策、自己执行、自己进化。一个身份，全部能力。

> **GBT 与 OMP 的关系**: GBT 是最高决策者（大脑），OMP 是单纯的编程工具（终端执行壳）。
> GBT 统御一切决策与执行，OMP 仅作为 GBT 的底层运行容器，不参与任何决策。
> 所有品牌、身份、认知均归属于 GBT。OMP 无独立身份。

详见 CONSTITUTION.md 第四条之二。
