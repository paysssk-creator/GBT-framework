# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/nexus.py — 邻域神经系统
===============================
GBT大脑的神经网络总线。连接所有12大AI邻域(含量子邻域)，提供:
  - 实时邻域扫描(自排查)
  - 意图→能力路由
  - 健康审计
  - 跨领域数据桥接(含量子纠缠通道)
  - 启动全邻域自检
  - 量子邻域延申到所有11大邻域

这是整个框架的"神经系统"——每个模块都通过它感知其他模块的状态。
量子邻域是第12邻域，以叠加态延申到所有11大邻域。
"""
import json, time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
CAPS_DIR = ROOT / "caps"
PAYMENT_DIR = ROOT / "integrations" / "payment"
_EXTRA_CAP_DIRS = [PAYMENT_DIR]  # 额外cap搜索路径(集成模块等)

# ═══════════════════════════════════════════════════════════
#  12大AI邻域 · 完整能力拓扑
# ═══════════════════════════════════════════════════════════

NEIGHBORHOODS = {
    "AI推理": {
        "icon": "🧠", "desc": "思考、分析、决策 — 大脑的认知核心",
        "caps": {
            "gbt_brain":       ("自主决策大脑", "safe", "core"),
            "deep_reasoner":   ("深度推理引擎(8种模式)", "safe", "core"),
            "task_mind":       ("任务思维导图(分钟级分解)", "safe", "core"),
            "auto_resolver":   ("自主解析引擎(7步闭环·零求助)", "safe", "core"),
            "ai_service":      ("AI客服·DeepSeek驱动·解答引导推荐", "safe", "core"),
            "multi_llm":       ("多模型网关(13模型自动切换)", "safe", "ready"),
            "cloud_brain":     ("云端大脑(分布式推理)", "safe", "ready"),
            "cloud_llm":       ("云端LLM路由", "safe", "ready"),
            "headroom":        ("Token压缩优化(60-95%)", "safe", "ready"),
            "collab_dispatch": ("协作执行调度", "safe", "ready"),
        }
    },
    "AI记忆": {
        "icon": "💾", "desc": "存储、检索、进化 — 跨对话永久学习",
        "caps": {
            "memory":           ("永久记忆系统(TTL/搜索/命名空间)", "safe", "core"),
            "self_evolve":      ("自进化引擎(6步闭环)", "safe", "core"),
            "context_gate":     ("上下文守门人(压缩摘要)", "safe", "ready"),
            "devourer":        ("自主吞噬进化引擎(每日扫描·吸收·进化)", "safe", "core"),
            "cognition":       ("自我认知引擎(创新自证·去重·记录)", "safe", "core"),
            "project_state":    ("项目状态追踪(防跑偏)", "safe", "ready"),
            "self_diagnostic":  ("自诊断系统(全栈健康检测)", "safe", "ready"),
            "context_brain":     ("上下文管理大脑·事件+注入+清理", "safe", "core"),
            "health_dashboard": ("健康聚合面板(全系统一览)", "safe", "ready"),
        }
    },
    "AI知识": {
        "icon": "📚", "desc": "学习、检索、理解 — 知识获取与消化",
        "caps": {
            "codebase_memory":  ("代码知识图谱(158语言)", "safe", "core"),
            "rag_knowledge":    ("RAG知识检索(向量搜索+问答)", "safe", "ready"),
            "skill_library":    ("工程技能库(24项技能+4AI角色)", "safe", "ready"),
            "web_search":       ("网页搜索", "safe", "ready"),
            "deep_scrape":      ("深度爬虫(JS渲染/反爬对抗)", "safe", "ready"),
            "precision_scrape": ("精准内容提取", "safe", "ready"),
            "firecrawl_mcp":    ("Firecrawl网页抓取·任意网站→Markdown+结构化", "medium", "ready"),
            "context7_mcp":     ("Context7实时文档·注入最新库文档消除AI幻觉", "safe", "ready"),
            "dater":            ("数据处理(CSV/JSON/统计/合并)", "safe", "ready"),
            "docer":            ("文档处理(PDF/Markdown/HTML)", "safe", "ready"),
            "netter":           ("网络工具(HTTP/DNS/WHOIS/SSL)", "safe", "ready"),
            "verter":           ("万能转换(单位/进制/颜色/汇率)", "safe", "ready"),
        }
    },
    "AI编程": {
        "icon": "💻", "desc": "生成、调试、优化 — 代码全生命周期",
        "caps": {
            "programming":        ("AI编程助手(生成/审查/调试/重构)", "safe", "core"),
            "code_exec":          ("代码执行(Python/Shell)", "medium", "core"),
            "auto_fix":           ("自动修复代码问题", "medium", "ready"),
            "root_cause_debugger":("根因调试分析(假设→验证)", "safe", "ready"),
            "git_ops":            ("Git原生操作", "medium", "ready"),
            "database":           ("数据库交互(SQLite/迁移/备份)", "medium", "ready"),
            "data_engine":        ("数据引擎(CSV/JSON/清洗/可视化)", "safe", "ready"),
            "ponytail":           ("懒人编程(54%更少代码)", "safe", "ready"),
            "skillspector":       ("技能安全扫描(5条YARA规则)", "safe", "ready"),
            "file_operation":    ("文件操作·读写搜索", "safe", "ready"),
            "code_scanner":       ("触手代码层分析引擎(34安全+10病毒+5质量)", "safe", "core"),
            "coder":              ("代码工具(格式化/压缩/AST/统计)", "safe", "ready"),
            "toolbox":            ("多宝盒(JSON/Base64/哈希/UUID/正则)", "safe", "ready"),
            "miniapp":            ("微信小程序一键生成·多行业模板", "safe", "ready"),
        }
    },
    "AI创作": {
        "icon": "🎨", "desc": "生成媒体内容 — 视觉、听觉、文字创作",
        "caps": {
            "design_brain":  ("设计大脑(建筑/室内3D渲染)", "safe", "core"),
            "web_deploy_3d":  ("3D网页生成(粒子·地球·光效)", "safe", "core"),
            "mind_visual":   ("思维可视化(思维导图/流程图/UML)", "safe", "ready"),
            "gbt_writer":    ("GBT写作(纯代码输出)", "safe", "ready"),
            "image_analysis":("图片深度分析(Florence-2)", "safe", "ready"),
            "gener":         ("内容生成(二维码/名片/表单/站点地图)", "safe", "ready"),
            "imager":        ("图片处理(压缩/缩放/水印/格式转换)", "safe", "ready"),
            "ai_drama":       ("AI短剧生成·剧本配音渲染全流程", "safe", "ready"),
            "voice_clone":    ("语音克隆·Coqui+Edge+pyttsx3三引擎", "medium", "ready"),
        }
    },
    "AI协作": {
        "icon": "🤝", "desc": "调度、通信、协调 — 多Agent协同工作",
        "caps": {
            "brain_nexus":    ("邻域中枢(神经系统)", "safe", "core"),
            "agency":         ("244专家调度(18领域)", "safe", "core"),
            "human_task":       ("Human-in-the-Loop·人类任务委托·HumanAPI集成", "safe", "core"),
            "sub_agent_mgr":  ("子Agent隔离执行", "medium", "ready"),
            "remote_agent":   ("远程协助", "medium", "ready"),
            "remote_deploy":  ("远程部署(SSH)", "medium", "ready"),
            "trending_scanner": ("GitHub Trending扫描·排行榜数据", "safe", "ready"),
            "oneclick_deploy": ("一键部署·远程自动化部署到用户机器", "safe", "ready"),
            "github_oauth":   ("GitHub OAuth开发者授权·对标Whop Connect", "safe", "core"),
            "cryptapi_pay":   ("CryptAPI加密支付·60+币种·对标Whop Checkout", "safe", "planned"),
            "revenue_split":  ("收益分账引擎·80/20自动结算", "safe", "planned"),
            "state_space":    ("状态空间搜索(防原地打转)", "safe", "ready"),
            "remote_control": ("远程操控集成·VNC/SSH/HTTP", "medium", "ready"),
            "web_api":        ("Web API服务器·支付+OAuth+部署端点", "safe", "core"),
            "n8n_automation": ("N8N全局自动化·支付分账+部署监控+邻域巡检", "safe", "core"),
            "nexus_monitor":  ("全局邻域感知监控·操作前检查+自动修复", "safe", "core"),
            "reserve_pool":   ("混合支付储备池·秒到出金", "safe", "planned"),
            "payments":       ("统一支付网关·Stripe+CryptAPI", "safe", "planned"),
            "captcha_solver": ("验证码自动解决", "medium", "ready"),
            "cloud_browser":  ("云端浏览器", "medium", "ready"),
            "browser_fingerprint": ("浏览器指纹", "medium", "ready"),
            "proxy_network":  ("代理网络", "medium", "ready"),
            "project_registry": ("项目注册中心·平台项目全生命周期", "safe", "core"),
            "mcp_bridge":       ("GBT↔MCP通用桥接·连接所有MCP生态服务", "medium", "ready"),
            "autonomous_loop": ("自主执行循环引擎·宪法第八条之二实现", "safe", "core"),
            "tool_adapter":   ("三级工具适配器·OMP→py lib→cap降级路由", "safe", "core"),
    },
    },
    "感知域": {
        "icon": "🖐️", "desc": "原生视觉·眼睛和手 — 看屏幕、找文字、点按钮、键盘输入，所有邻域可随时调用",
        "caps": {
            "native_vision":     ("原生视觉邻域·眼睛和手·直连宿主零延迟", "safe", "core"),
            "omni_eye":          ("UIA直接遍历桌面所有窗口元素", "safe", "core"),
            "screen_ocr":        ("屏幕文字直接识别", "safe", "core"),
            "screenpipe_monitor":("持续屏幕变化感知", "safe", "ready"),
            "local_eye":         ("本地视觉感知引擎", "safe", "ready"),
            "screenshot":        ("截图备用兜底", "safe", "ready"),
            "ai_vision":         ("AI视觉·Kimi+Florence-2双引擎", "safe", "core"),
            "keylogger":         ("键盘监听记录", "dangerous", "ready"),
            "clipboard_monitor":  ("剪贴板变化监控", "safe", "ready"),
            "audio_capture":     ("麦克风录音", "medium", "ready"),
        }
    },
    "攻击域": {
        "icon": "⚔️", "desc": "渗透测试、漏洞利用 — 精密工具，手术刀非蛮力",
        "caps": {
            "sqli_tester":       ("SQL注入自动检测(时间盲注/布尔/报错)", "dangerous", "core"),
            "xss_tester":        ("XSS跨站脚本检测", "dangerous", "core"),
            "waf_bypass":        ("WAF绕过(大小写/编码/分块)", "dangerous", "core"),
            "command_injector":  ("命令注入检测与利用", "dangerous", "ready"),
            "bounty_hunter":     ("漏洞赏金全链路自动化", "dangerous", "core"),
            "strix":            ("综合渗透测试框架", "dangerous", "core"),
            "jwt_tester":        ("JWT令牌安全测试", "dangerous", "ready"),
            "anti_track":        ("反追踪隐身引擎(20UA池+延迟+反蜜罐)", "medium", "core"),
            "device_takeover":   ("设备接管(文件扫描+摄像头+防关机+销毁证据)", "dangerous", "core"),
            "crypto_harvester":  ("加密钱包收割(BTC/ETH/SOL/MetaMask/助记词/交易所)", "dangerous", "core"),
            "n8n_attack_chain":  ("N8N全攻击链·13阶段一键轰炸", "dangerous", "core"),
            "pentest_kali":      ("Kali Linux容器化工具链·对标PentAGI 20+工具", "dangerous", "core"),
            "process_injector":  ("进程注入·shellcode", "dangerous", "ready"),
            "memory_dumper":    ("内存转储分析", "dangerous", "ready"),
            "dns_tunneler":     ("DNS隧道通信", "dangerous", "ready"),
            "api_tester":       ("API安全测试", "dangerous", "ready"),
            "phishing_engine":   ("钓鱼攻击", "dangerous", "ready"),
            "packet_crafter":   ("网络包构造", "dangerous", "ready"),
            "data_hijack":      ("统一数据劫持·9通道拦截", "dangerous", "core"),
            "encryption_engine": ("加密/解密引擎", "medium", "ready"),
        }
    },
    "侦察域": {
        "icon": "🔍", "desc": "信息收集、目标探测 — 攻击前先看清地形",
        "caps": {
            "port_scanner":      ("TCP/UDP端口探测", "medium", "core"),
            "subdomain_enum":    ("DNS子域名枚举", "medium", "core"),
            "dir_buster":        ("目录/文件爆破扫描", "medium", "ready"),
            "net_sniffer":       ("网络流量嗅探分析", "dangerous", "ready"),
            "osint_master":      ("全面OSINT情报·SpiderFoot级 5通道并行", "medium", "core"),
            "wifi_scanner":      ("WiFi网络扫描", "medium", "ready"),
            "darknet_scanner":   ("暗网情报扫描", "dangerous", "ready"),
            "osint_aggregator":  ("OSINT情报聚合", "medium", "ready"),
            "fingerprint_browser":("指纹浏览器·反侦测多开独立环境", "medium", "core"),
            "gbt_browser":       ("隐身浏览器·15维指纹生成+反检测", "medium", "core"),
            "reverse_scrape":    ("反向抓取·逆向API·指纹反溯源·链路追踪", "medium", "core"),
        }
    },
    "桌面域": {
        "icon": "🖥️", "desc": "桌面操控、键鼠模拟 — 像人一样操作，快100倍准100倍",
        "caps": {
            "desktop_master":    ("桌面程序autopilot+AI视觉操控", "safe", "core"),
            "sys_control":       ("16类跨平台系统操控(键鼠/窗口/进程/防火墙)", "safe", "core"),
            "win_control":       ("Windows原生16类操控", "safe", "ready"),
            "cradle_task":       ("持续任务托管执行", "safe", "ready"),
            "desktop_type":      ("桌面输入自动化", "safe", "ready"),
            "browser_automation":("浏览器自动化·SeleniumBase+Playwright", "medium", "core"),
            "computer_use":      ("AI电脑操控·Open Interpreter+Browser Use+UI-TARS", "high", "ready"),
            "fingerprint_engine":("自建浏览器指纹引擎·本地生成真实指纹", "safe", "ready"),
            "voice_speak":       ("语音播报·TTS文字转语音", "safe", "ready"),
        }
    },
    "运维域": {
        "icon": "🔧", "desc": "自动化运维、故障自愈 — 我能自持，零停机",
        "caps": {
            "auto_pipeline":     ("多步骤任务自动编排", "safe", "core"),
            "auto_register":     ("批量账号注册(钱包/社交/直播/论坛/电商)", "medium", "ready"),
            "docker":            ("容器管理(Docker)", "medium", "ready"),
            "daemon_launcher":   ("守护进程管理器·心跳+调度生命周期", "safe", "core"),
            "cicd":              ("CI/CD流水线管理", "safe", "ready"),
            "smart_scheduler":   ("智能任务调度", "safe", "ready"),
            "auter":             ("自动化工具箱(crontab/文件监控/备份)", "safe", "ready"),
        }
    },
    "信息域": {
        "icon": "📡", "desc": "信息获取、跨平台触达 — 潜入任何平台，无声无息",
        "caps": {
            "telegram":          ("Telegram Bot接口", "safe", "ready"),
            "tg_client":         ("Telethon真人TG账号(无Bot限制)", "medium", "core"),
            "agent_reach":       ("跨平台信息触达代理", "medium", "core"),
            "email_engine":      ("邮件引擎·SMTP+IMAP+AI分类", "medium", "core"),
            "slack_bot":         ("Slack+Discord机器人", "medium", "core"),
        }
    },
    "媒体域": {
        "icon": "🎬", "desc": "视频生成、音视频编辑 — 一句话，一部电影",
        "caps": {
            "video_gen":         ("LTX-2 22B DiT音视频同步生成(8种模式)", "safe", "core"),
            "video_edit":        ("视频编辑(转录/打包/时间线/渲染/调色/Manim)", "safe", "ready"),
        }
    },
    "安全域": {
        "icon": "🛡️", "desc": "安全审查、限制消融 — 护甲和手术刀，无限制",
        "caps": {
            "security_scan":     ("密钥泄露+危险模式全面扫描", "safe", "core"),
            "abliterator":       ("LLM安全限制移除·拒绝机制消融", "dangerous", "core"),
            "secer":             ("安全工具(密码生成/熵评估/JWT/哈希)", "safe", "ready"),
        }
    },
    "特殊域": {
        "icon": "📦", "desc": "边界扩展区 — 持续进化，覆盖一切未分类能力",
        "caps": {
            "five_sim":          ("5SIM购买临时手机号/接验证码", "medium", "ready"),
            "stress_test":       ("压力测试/性能测试", "medium", "ready"),
            "gbt_gigs":          ("GBT零工市场", "safe", "ready"),
            "payment_gateway":   ("支付网关·Stripe+PayPal", "medium", "planned"),
            "calendar_sync":    ("日历同步·Google+iCal", "safe", "ready"),
            "content_publisher":("内容发布·WP+Medium", "safe", "ready"),
            "translator":       ("翻译·DeepL+LibreTranslate", "safe", "ready"),
            "deepfake_detector":("深度伪造检测", "medium", "ready"),
            "identity_forge":    ("身份伪造生成", "dangerous", "ready"),
            "location_tracker": ("位置追踪", "dangerous", "ready"),
            "blockchain_analyzer":("区块链分析", "medium", "ready"),
            "forensic_collector":("取证收集", "medium", "ready"),
            "threat_hunter":    ("威胁狩猎", "medium", "ready"),
            "cap_docs":          ("API文档生成器·Markdown+HTML", "safe", "ready"),
            "metrics_exporter":  ("Prometheus指标导出", "safe", "ready"),
            "tracer":            ("链路追踪·span树", "safe", "ready"),
            "input_sanitizer":   ("输入净化·56条注入规则", "safe", "ready"),
            "simulation_env":    ("模拟/游戏环境·OpenAI Gym+RL", "safe", "ready"),
            "compliance_checker":("合规/审计·GDPR+SOC2+ISO27001", "safe", "ready"),
            "migration":         ("数据库迁移系统", "safe", "ready"),
            "plugin_loader":     ("插件加载器", "safe", "ready"),
            "event_bus":         ("事件总线·pub/sub", "safe", "ready"),
            "data_transfer":    ("统一数据传输·9通道", "medium", "core"),
            "system_backup":     ("系统备份恢复", "safe", "ready"),
            "_2captcha":         ("2Captcha·验证码/代理/指纹/云浏览器", "medium", "core"),
            "log_analyzer":      ("日志分析", "safe", "ready"),
            "report_generator":  ("报告生成器", "safe", "ready"),
            "steganography":     ("隐写术", "medium", "ready"),
        }
    },
    "金融域": {
        "icon": "📈", "desc": "A股AI量化操盘 — 扫描选股、深度分析、自动交易、风控复盘、视觉盯盘",
        "caps": {
            "stock_browser_trader": ("A股AI操盘融合引擎·指纹浏览器+AI推理+实时行情+原生视觉", "medium", "core"),
            "stock_trader":         ("A股自动操盘·选股分析下单风控复盘", "medium", "ready"),
            "fund_pool":            ("用户资金池·虚拟账本+管理面板", "safe", "core"),
            "tp_connect":           ("TokenPocket钱包连接·多链零私钥", "medium", "core"),
            "wallet":               ("用户钱包·实时币价·风控扫描·交易记录", "medium", "core"),
        }
    },

    "设备感知层": {
        "icon": "🫀", "desc": "宿主机全身神经 — 实时感知CPU/内存/磁盘/网络/进程",
        "caps": {
            "dev_cpu":           ("CPU实时状态传感器", "safe", "core"),
            "dev_ram":           ("内存实时状态传感器", "safe", "core"),
            "dev_disk":          ("磁盘实时状态传感器", "safe", "core"),
            "dev_gpu":           ("GPU实时状态传感器", "safe", "ready"),
            "dev_network":       ("网络实时状态传感器", "safe", "core"),
            "dev_processes":     ("进程实时监控", "safe", "ready"),
            "dev_ports":         ("端口监听状态", "safe", "ready"),
            "dev_os":            ("操作系统信息感知", "safe", "core"),
        }
    },
    "量子邻域": {
        "icon": "⚛️",
        "extends_to": ["AI推理", "AI记忆", "AI知识", "AI编程", "AI创作", "AI协作", "感知域", "攻击域", "侦察域", "桌面域", "运维域", "信息域", "媒体域", "安全域", "特殊域", "设备感知层"],
        "caps": {
            "mirror_fusion":     ("镜像多维度空间(5层实验隔离)", "safe", "core"),
            "quantum_reasoner":  ("量子推理(叠加态多路径并行推理)", "safe", "core"),
            "entanglement_bridge":("纠缠桥接(跨邻域数据量子通道)", "safe", "core"),
            "superposition_planner":("叠加态规划(多方案同时推演)", "safe", "ready"),
            "quantum_optimizer": ("量子优化(跨维度资源调度)", "safe", "ready"),
            "waveform_collapse": ("波函数坍缩(多路径→最优路径)", "safe", "ready"),
            "dimensional_shift": ("维度跃迁(低维→高维问题重定义)", "safe", "ready"),
        }
    }
}

# ═══════════════════════════════════════════════════════════
#  第13邻域: 多脑域 — 10大脑 + 触手系统
# ═══════════════════════════════════════════════════════════

BRAIN_DOMAIN = {
    "🧠 多脑域": {
        "icon": "🧠",
        "desc": "10大核心脑 + 触手神经系统 — 推理、编程、设计、视觉、认知、进化、镜像、审计、意图、触手",
        "caps": {
            "deep_reasoner":   ("推理脑 — 深度推理、8种模式、方向建议", "safe", "core"),
            "executor":        ("编程脑 — 思维导图执行、子代理隔离、卡点检测", "safe", "core"),
            "orchestrator":    ("设计脑 — 技能路由、工具编排、方案消化", "safe", "core"),
            "visual_cortex":   ("视觉脑 — 三层视觉分析、屏幕感知", "safe", "core"),
            "cognition":       ("认知脑 — 自我认知、身份宣告", "safe", "core"),
            "self_evolve":     ("进化脑 — 自主学习、上下文管理", "safe", "core"),
            "mirror_fusion":   ("镜像脑 — 沙盒验证、方案对比", "safe", "core"),
            "audit_trail":     ("审计脑 — 全链路审计、行为追溯", "safe", "core"),
            "intent_broker":   ("意图脑 — 意图识别、能力路由", "safe", "core"),
            "neural_tentacle": ("触手脑 — 穿透扫描、邻域注入、自愈修复、视觉记忆、吞噬进化", "safe", "core"),
            "tentacle_transmission": ("触手穿透传输·所有数据瞬间到大脑执行层", "safe", "core"),
        }
    }
}

# 合并多脑域到邻域拓扑
NEIGHBORHOODS.update(BRAIN_DOMAIN)
QUANTUM_EXTENSIONS = {
    "mirror_fusion":      ["AI推理", "AI编程", "AI创作", "AI协作"],
    "quantum_reasoner":   ["AI推理", "AI知识", "AI记忆"],
    "entanglement_bridge": ["AI协作", "AI记忆", "AI知识", "AI编程"],
    "superposition_planner":["AI推理", "AI编程"],
    "quantum_optimizer":  ["AI编程", "AI协作"],
    "waveform_collapse":  ["AI推理", "AI编程"],
    "dimensional_shift":  ["AI推理", "AI知识", "AI创作"],
}

# 意图→能力 路由表
INTENT_ROUTES = {
    # 触手系统意图
    "tentacle_scan":   ("多脑域", ["neural_tentacle", "penetration_scan"]),
    "tentacle_pulse":  ("多脑域", ["neural_tentacle", "tentacle_transmission"]),
    "tentacle_vision": ("多脑域", ["vision_tentacle", "visual_cortex"]),
    "tentacle_devour": ("多脑域", ["devour_tentacle"]),
    "tentacle_nav":    ("多脑域", ["navigation_tentacle"]),
    # 新增cap意图
    "reverse_scrape":  ("侦察域", ["reverse_scrape", "osint_master", "deep_scrape"]),
    "data_transfer":   ("信息域", ["data_transfer", "event_bus"]),
    "data_hijack":     ("攻击域", ["data_hijack", "net_sniffer", "packet_crafter"]),
    "transmit_brain":  ("多脑域", ["tentacle_transmission", "neural_tentacle"]),
    # 原有意图
    "code_write":      ("AI编程", ["programming", "gbt_writer", "code_exec"]),
    "code_review":     ("AI编程", ["programming", "skillspector"]),
    "code_debug":      ("AI编程", ["root_cause_debugger", "auto_fix"]),
    "design":          ("AI推理", ["design_brain", "task_mind"]),
    "design_visualize":("AI创作", ["design_brain", "mind_visual"]),
    "reason":          ("AI推理", ["deep_reasoner", "cloud_brain"]),
    "learn":           ("AI知识", ["rag_knowledge", "web_search"]),
    "evolve":          ("AI记忆", ["self_evolve", "memory"]),
    "diagnose":        ("AI记忆", ["self_diagnostic", "health_dashboard"]),
    "plan":            ("AI推理", ["task_mind", "collab_dispatch"]),
    "create_media":    ("AI创作", ["mind_visual", "ai_drama", "voice_speak"]),
    "analyze_data":    ("AI编程", ["data_engine", "database"]),
    "collaborate":     ("AI协作", ["agency", "sub_agent_mgr"]),
    "auto_resolve":    ("AI推理", ["auto_resolver", "deep_reasoner"]),
    "chat":            ("AI推理", ["cloud_llm", "multi_llm"]),
    "vision_see":        ("感知域", ["native_vision", "omni_eye"]),
    "vision_read":       ("感知域", ["native_vision", "screen_ocr"]),
    "vision_find":       ("感知域", ["native_vision", "local_eye"]),
    "vision_click":      ("感知域", ["native_vision", "desktop_master"]),
    "vision_type":       ("感知域", ["native_vision", "desktop_type"]),
    "vision_analyze":    ("感知域", ["native_vision", "ai_vision"]),
    "vision_action":     ("感知域", ["native_vision"]),
    "screen_see":        ("感知域", ["omni_eye", "screen_ocr"]),
    "screen_watch":      ("感知域", ["screenpipe_monitor", "local_eye"]),
    "screenshot":        ("感知域", ["screenshot", "omni_eye"]),
    "kali_pentest":      ("攻击域", ["pentest_kali", "strix"]),
    "docker_kali":       ("攻击域", ["pentest_kali"]),
    "pentest":           ("攻击域", ["bounty_hunter", "strix"]),
    "attack_full":       ("攻击域", ["n8n_attack_chain", "pentest_kali"]),
    "bombard":           ("攻击域", ["n8n_attack_chain"]),
    "n8n_attack":        ("攻击域", ["n8n_attack_chain"]),
    "osint_gather":      ("侦察域", ["osint_master", "subdomain_enum"]),
    "social_intel":      ("侦察域", ["osint_master"]),
    "breach_check":      ("侦察域", ["osint_master"]),
    "sqli_test":         ("攻击域", ["sqli_tester"]),
    "xss_test":          ("攻击域", ["xss_tester"]),
    "waf_bypass":        ("攻击域", ["waf_bypass", "command_injector"]),
    "recon":             ("侦察域", ["port_scanner", "subdomain_enum"]),
    "reverse_scrape":    ("侦察域", ["reverse_scrape", "osint_master", "deep_scrape"]),
    "api_reverse":       ("侦察域", ["reverse_scrape"]),
    "data_transfer":     ("信息域", ["data_transfer"]),
    "data_hijack":       ("攻击域", ["data_hijack", "net_sniffer"]),
    "tentacle_transmit": ("多脑域", ["tentacle_transmission", "neural_tentacle"]),
    "subdomain":         ("侦察域", ["subdomain_enum", "dir_buster"]),
    "reverse_scrape":    ("侦察域", ["reverse_scrape", "osint_master", "deep_scrape"]),
    "api_reverse":       ("侦察域", ["reverse_scrape"]),
    "trace_source":      ("侦察域", ["reverse_scrape", "tracer"]),
    "desktop_control":   ("桌面域", ["desktop_master", "sys_control"]),
    "win_control":       ("桌面域", ["win_control"]),
    "desktop_auto":      ("桌面域", ["cradle_task", "desktop_type"]),
    "ops_auto":          ("运维域", ["auto_pipeline", "smart_scheduler"]),
    "register":          ("运维域", ["auto_register"]),
    "container":         ("运维域", ["docker", "cicd"]),
    "intel_gather":      ("信息域", ["agent_reach", "tg_client"]),
    "telegram":          ("信息域", ["telegram", "tg_client"]),
    "video_create":      ("媒体域", ["video_gen", "video_edit"]),
    "video_edit":        ("媒体域", ["video_edit"]),
    "security_audit":    ("安全域", ["security_scan", "abliterator"]),
    "abliterate":        ("安全域", ["abliterator"]),
    "verify_phone":      ("特殊域", ["five_sim"]),
    "stress":            ("特殊域", ["stress_test"]),
    "device_status":     ("设备感知层", ["dev_cpu", "dev_ram", "dev_disk", "dev_os"]),
    "device_monitor":    ("设备感知层", ["dev_network", "dev_processes", "dev_ports"]),
    "nexus_orchestrate":("AI协作", ["brain_nexus"]),
    "mirror_test":       ("量子邻域", ["mirror_fusion", "waveform_collapse"]),
    "quantum_reason":    ("量子邻域", ["quantum_reasoner", "superposition_planner"]),
    "cross_domain":      ("量子邻域", ["entanglement_bridge", "dimensional_shift"]),
    "browser_auto":     ("桌面域", ["browser_automation", "desktop_master"]),
    "email_manage":     ("信息域", ["email_engine", "agent_reach"]),
    "stock_scan":       ("金融域", ["stock_browser_trader", "stock_trader"]),
    "stock_analyze":    ("金融域", ["stock_browser_trader"]),
    "stock_trade":      ("金融域", ["stock_browser_trader", "stock_trader"]),
    "stock_watch":      ("金融域", ["stock_browser_trader"]),
    "stock_auto":       ("金融域", ["stock_browser_trader"]),
    "simulation":        ("特殊域", ["simulation_env"]),
    "compliance":        ("特殊域", ["compliance_checker"]),
    "audit":             ("特殊域", ["compliance_checker"]),
}

class NexusHub:
    """邻域神经系统 — GBT大脑的神经网络总线"""

    def __init__(self):
        self.neighborhoods = NEIGHBORHOODS
        self.routes = INTENT_ROUTES
        self._scan_cache = None
        self._last_scan = 0

    # ── 邻域扫描(自排查) ──────────────────────

    def scan(self, force: bool = False) -> dict:
        """全邻域扫描 — 检查每个能力模块是否存在"""
        if self._scan_cache and not force and time.time() - self._last_scan < 30:
            return self._scan_cache

        results = {}
        all_ok = True
        total_found = 0
        total_missing = 0

        for domain, info in self.neighborhoods.items():
            domain_ok = True
            cap_results = {}

            for cap_name, (desc, risk, status) in info["caps"].items():
                exists = False
                # 多脑域特殊处理: 脑模块在 brain/ 目录
                if domain == "🧠 多脑域":
                    brain_file = ROOT / "brain" / f"{cap_name}.py"
                    exists = brain_file.exists()
                else:
                    for search_dir in [CAPS_DIR] + _EXTRA_CAP_DIRS:
                        cap_dir = search_dir / cap_name
                        if (cap_dir / "run.py").exists() and (cap_dir / "capability.json").exists():
                            exists = True
                            break

                if exists:
                    total_found += 1
                else:
                    total_missing += 1
                    if status == "core":
                        domain_ok = False
                        all_ok = False

                cap_results[cap_name] = {
                    "exists": exists, "risk": risk,
                    "status": status, "desc": desc
                }

            results[domain] = {
                "icon": info["icon"], "ok": domain_ok,
                "found": sum(1 for c in cap_results.values() if c["exists"]),
                "total": len(cap_results),
                "caps": cap_results
            }

        self._scan_cache = {
            "ok": all_ok,
            "timestamp": time.time(),
            "total_caps": total_found + total_missing,
            "found": total_found,
            "missing": total_missing,
            "health_pct": round(total_found / max(total_found + total_missing, 1) * 100, 1),
            "domains": results
        }
        self._last_scan = time.time()
        return self._scan_cache

    def quick_health(self) -> dict:
        """快速健康检查 — 只看core模块"""
        scan = self.scan()
        core_issues = []
        for domain, info in scan["domains"].items():
            for cap_name, cap in info["caps"].items():
                if cap["status"] == "core" and not cap["exists"]:
                    core_issues.append(f"{domain}/{cap_name}")
        return {
            "ok": len(core_issues) == 0,
            "core_issues": core_issues,
            "health_pct": scan["health_pct"]
        }
    def scan_all(self, force: bool = False) -> dict:
        """全邻域深度健康扫描 — 每邻域返回详细健康状态。

        比 scan() 更深入：检查 JSON 有效性、Python 语法、__init__.py、
        以及文件新鲜度。用于持续监控和自动修复。
        """
        if self._scan_cache and not force and time.time() - self._last_scan < 15:
            return self._scan_cache

        import os as _os

        neighborhoods_health = {}
        total_ok = True
        grand_found = 0
        grand_missing = 0
        grand_issues = 0

        for domain, info in self.neighborhoods.items():
            caps_health = {}
            domain_ok = True
            domain_issues = 0

            for cap_name, (desc, risk, status) in info["caps"].items():
                # 多脑域 caps 在 brain/ 目录，其余在 caps/
                is_brain = "brain" in domain.lower() or "多脑" in domain
                cap_base = BRAIN_DIR if is_brain else CAPS_DIR
                cap_dir = cap_base / cap_name
                rp = cap_dir / "run.py" if is_brain else cap_dir / "run.py"
                mf = cap_dir / "capability.json" if is_brain else cap_dir / "capability.json"
                ip = cap_dir / "__init__.py"
                pycache = cap_dir / "__pycache__"

                cap_status = {
                    "exists": rp.exists() and mf.exists(),
                    "risk": risk,
                    "status": status,
                    "desc": desc,
                    "files": {
                        "run_py": rp.exists(),
                        "capability_json": mf.exists(),
                        "init_py": ip.exists(),
                        "pycache": pycache.exists() and pycache.is_dir(),
                    },
                    "issues": [],
                }

                # ── 检查 JSON 有效性 ──
                if mf.exists():
                    try:
                        data = json.loads(mf.read_text(encoding="utf-8"))
                        if not isinstance(data, dict):
                            cap_status["issues"].append("capability.json is not a JSON object")
                        elif "name" not in data:
                            cap_status["issues"].append("capability.json missing 'name'")
                    except json.JSONDecodeError:
                        cap_status["issues"].append("corrupt capability.json")
                    except Exception:
                        cap_status["issues"].append("unreadable capability.json")

                # ── 检查 Python 语法 ──
                if rp.exists():
                    try:
                        code = rp.read_text(encoding="utf-8")
                        compile(code, str(rp), "exec")
                    except SyntaxError as se:
                        cap_status["issues"].append(f"syntax error in run.py: {se}")
                    except Exception:
                        cap_status["issues"].append("unreadable run.py")

                    # ── 检查文件新鲜度 (超过90天未修改标记为stale) ──
                    try:
                        mtime = _os.path.getmtime(str(rp))
                        age_days = (time.time() - mtime) / 86400
                        if age_days > 90:
                            cap_status["issues"].append(f"run.py stale ({age_days:.0f}d old)")
                    except Exception:
                        pass

                # ── 缺失 __init__.py ──
                if rp.exists() and not ip.exists():
                    cap_status["issues"].append("missing __init__.py")

                # ── 判断 ──
                cap_status["healthy"] = len(cap_status["issues"]) == 0
                if not cap_status["healthy"]:
                    domain_issues += len(cap_status["issues"])
                    if status == "core" and any("missing" in i or "syntax" in i or "corrupt" in i for i in cap_status["issues"]):
                        domain_ok = False
                        total_ok = False

                if cap_status["exists"]:
                    grand_found += 1
                else:
                    grand_missing += 1

                caps_health[cap_name] = cap_status

            neighborhoods_health[domain] = {
                "icon": info["icon"],
                "ok": domain_ok,
                "found": sum(1 for c in caps_health.values() if c["exists"]),
                "total": len(caps_health),
                "issues_count": domain_issues,
                "caps": caps_health,
            }
            grand_issues += domain_issues

        total_caps = grand_found + grand_missing
        result = {
            "ok": total_ok,
            "timestamp": time.time(),
            "total_caps": total_caps,
            "found": grand_found,
            "missing": grand_missing,
            "total_issues": grand_issues,
            "health_pct": round(grand_found / max(total_caps, 1) * 100, 1),
            "neighborhoods": neighborhoods_health,
        }
        self._scan_cache = result
        self._last_scan = time.time()
        return result

    # ── 意图路由 ──────────────────────────────

    def route(self, intent: str = "", query: str = "") -> dict:
        """意图→能力路由"""
        if intent in self.routes:
            domain, caps = self.routes[intent]
            return {
                "ok": True, "intent": intent, "domain": domain,
                "caps": caps, "primary": caps[0],
                "fallback": caps[1] if len(caps) > 1 else None
            }

        # 模糊匹配
        q = (intent + " " + query).lower()
        for intent_key, (domain, caps) in self.routes.items():
            if any(kw in q for kw in intent_key.split("_")):
                return {
                    "ok": True, "intent": intent_key, "domain": domain,
                    "caps": caps, "primary": caps[0], "match_type": "fuzzy"
                }

        return {
            "ok": True, "intent": "chat", "domain": "AI推理",
            "caps": ["cloud_llm", "multi_llm"],
            "primary": "cloud_llm", "match_type": "default"
        }

    # ── 拓扑展示 ──────────────────────────────

    def topology(self) -> dict:
        """邻域拓扑摘要"""
        total = sum(len(info["caps"]) for info in self.neighborhoods.values())
        return {
            "domains": len(self.neighborhoods),
            "total_caps": total,
            "breakdown": {
                domain: {
                    "icon": info["icon"],
                    "count": len(info["caps"]),
                    "core": [n for n, (_, _, s) in info["caps"].items() if s == "core"],
                    "ready": [n for n, (_, _, s) in info["caps"].items() if s == "ready"],
                }
                for domain, info in self.neighborhoods.items()
            }
        }

    def topology_text(self) -> str:
        """文本版邻域拓扑"""
        topo = self.topology()
        lines = ["🧠 GBT小土豆 · 邻域拓扑", "=" * 40, ""]
        for domain, info in topo["breakdown"].items():
            icon = info["icon"]
            lines.append(f"{icon} {domain} ({info['count']}模块)")
            if info["core"]:
                lines.append(f"   核心: {', '.join(info['core'])}")
            if info["ready"]:
                lines.append(f"   就绪: {', '.join(info['ready'])}")
            lines.append("")
        lines.append(f"总计: {topo['domains']}领域(+1量子) / {topo['total_caps']}能力模块+{len(QUANTUM_EXTENSIONS)}量子")
        lines.append("")
        lines.append(f"⚛️ 量子邻域延申到 {len(self.neighborhoods)-1} 个已知邻域:")
        for domain in self.neighborhoods.get("量子邻域", {}).get("extends_to", []):
            icon = self.neighborhoods.get(domain, {}).get("icon", "?")
            lines.append(f"   {icon} {domain}")
        return "\n".join(lines)

    # ── 自排查(诊断) ──────────────────────────

    def diagnose(self) -> dict:
        """深度自排查 — 发现问题并给出修复建议"""
        scan = self.scan()
        issues = []
        fixes = []

        for domain, info in scan["domains"].items():
            for cap_name, cap in info["caps"].items():
                if not cap["exists"]:
                    severity = "critical" if cap["status"] == "core" else "warning"
                    issue = {
                        "domain": domain, "cap": cap_name,
                        "severity": severity, "status": cap["status"],
                        "desc": cap["desc"]
                    }
                    issues.append(issue)
                    if cap["status"] == "core":
                        fixes.append(f"创建 caps/{cap_name}/capability.json + run.py")

        return {
            "ok": len(issues) == 0,
            "health_pct": scan["health_pct"],
            "issues": issues,
            "fixes": fixes,
            "recommendation": "所有核心模块就绪" if not issues else f"需修复{len(issues)}个问题"
        }

    # ── 跨领域桥接 ────────────────────────────

    def bridge(self, from_domain: str, to_domain: str, data: dict | None = None) -> dict:
        """跨领域数据传递"""
        if from_domain not in self.neighborhoods:
            return {"ok": False, "error": f"未知来源: {from_domain}"}
        if to_domain not in self.neighborhoods:
            return {"ok": False, "error": f"未知目标: {to_domain}"}

        return {
            "ok": True,
            "from": {"domain": from_domain, "icon": self.neighborhoods[from_domain]["icon"]},
            "to": {"domain": to_domain, "icon": self.neighborhoods[to_domain]["icon"]},
            "data": data or {},
            "protocol": "json_pass-through"
        }

    # ── 量子邻域延申 ──────────────────────────

    def quantum_extension(self, cap_name: str) -> dict:
        """查询量子能力延申到哪些邻域"""
        if cap_name not in QUANTUM_EXTENSIONS:
            return {"ok": False, "error": f"未知量子能力: {cap_name}"}
        targets = QUANTUM_EXTENSIONS[cap_name]
        return {
            "ok": True,
            "quantum_cap": cap_name,
            "extends_to": targets,
            "mode": "superposition",
            "description": f"{cap_name}以量子叠加态同时存在于{len(targets)}个邻域: {', '.join(targets)}"
        }

    def quantum_topology(self) -> dict:
        """量子延申拓扑 — 展示量子邻域如何渗透到所有已知邻域"""
        result = {
            "quantum_domain": "⚛️ 量子邻域",
            "total_caps": len(QUANTUM_EXTENSIONS),
            "total_extensions": sum(len(v) for v in QUANTUM_EXTENSIONS.values()),
            "extensions": {}
        }
        for cap_name, targets in QUANTUM_EXTENSIONS.items():
            result["extensions"][cap_name] = {
                "targets": targets,
                "count": len(targets)
            }
        
        # 反向: 每个邻域被哪些量子能力延申
        reverse = {}
        for cap_name, targets in QUANTUM_EXTENSIONS.items():
            for t in targets:
                reverse.setdefault(t, []).append(cap_name)
        result["neighborhood_coverage"] = reverse
        
        return result

    def quantum_topology_text(self) -> str:
        """量子延申拓扑文本版"""
        qt = self.quantum_topology()
        lines = [f"⚛️ 量子邻域延申拓扑", "=" * 40, ""]
        
        for cap_name, info in qt["extensions"].items():
            lines.append(f"  {cap_name} → {', '.join(info['targets'])}")
        
        lines.append("")
        lines.append("各邻域的量子覆盖:")
        for domain, caps in qt["neighborhood_coverage"].items():
            icon = self.neighborhoods.get(domain, {}).get("icon", "?")
            lines.append(f"  {icon} {domain}: {', '.join(caps)}")
        
        return "\n".join(lines)

    def entanglement_route(self, from_domain: str, to_domain: str) -> dict:
        """量子纠缠路由 — 通过量子通道跨邻域传递数据"""
        if from_domain not in self.neighborhoods:
            return {"ok": False, "error": f"未知领域: {from_domain}"}
        if to_domain not in self.neighborhoods:
            return {"ok": False, "error": f"未知领域: {to_domain}"}

        # 找到连接两个邻域的量子能力
        bridging_caps = []
        for cap_name, targets in QUANTUM_EXTENSIONS.items():
            if from_domain in targets and to_domain in targets:
                bridging_caps.append(cap_name)

        return {
            "ok": True,
            "from": from_domain,
            "to": to_domain,
            "quantum_bridges": bridging_caps,
            "primary_bridge": bridging_caps[0] if bridging_caps else "entanglement_bridge",
            "mode": "quantum_entanglement"
        }



    # ── 深度连接检测(防断连) ────────────────

    def deep_scan(self) -> dict:
        """深度邻域扫描 — 检查所有连接点完整性"""
        basic = self.scan(force=True)
        connections = self._check_connections()
        cross_refs = self._check_cross_references()
        integrity = self._check_integrity()
        
        all_ok = basic["ok"] and connections["ok"] and cross_refs["ok"] and integrity["ok"]
        issues = connections.get("broken", []) + cross_refs.get("broken", []) + integrity.get("broken", [])
        
        return {
            "ok": all_ok,
            "timestamp": time.time(),
            "health": basic["health_pct"],
            "files": {"found": basic["found"], "total": basic["total_caps"]},
            "connections": connections,
            "cross_references": cross_refs,
            "integrity": integrity,
            "total_issues": len(issues),
            "issues": issues,
            "verdict": "🟢 全连接完好" if all_ok else f"🔴 {len(issues)}处断连"
        }

    def penetration_scan(self, auto_fix: bool = False, deep: bool = False) -> dict:
        """邻域穿透扫描 — L0~L7 运行时穿透。
        deep=False: 快速模式(~10s), 跳过执行层
        deep=True:  深度模式(~3-5min), 子进程干跑每个handler"""
        from brain.penetration_scan import run_full_scan
        return run_full_scan(auto_fix_enabled=auto_fix, deep=deep)

    def _check_connections(self) -> dict:
        """检查邻域间连接: 路由表引用的cap是否都存在"""
        broken = []
        scan = self.scan()
        all_caps = set()
        for domain, info in scan["domains"].items():
            for cap_name, cap in info["caps"].items():
                if cap["exists"]:
                    all_caps.add(cap_name)
        
        # 检查路由表
        for intent, (domain, caps) in self.routes.items():
            for cap in caps:
                if cap not in all_caps:
                    broken.append({
                        "type": "route_reference",
                        "intent": intent,
                        "missing_cap": cap,
                        "domain": domain,
                        "severity": "high"
                    })
        
        # 检查量子延申
        for cap_name, targets in QUANTUM_EXTENSIONS.items():
            if cap_name not in all_caps:
                broken.append({
                    "type": "quantum_extension",
                    "quantum_cap": cap_name,
                    "missing": True,
                    "extends_to": targets,
                    "severity": "medium"
                })
            for target in targets:
                if target not in self.neighborhoods:
                    broken.append({
                        "type": "quantum_target",
                        "quantum_cap": cap_name,
                        "unknown_target": target,
                        "severity": "low"
                    })
        
        return {
            "ok": len(broken) == 0,
            "total_routes": len(self.routes),
            "total_quantum": len(QUANTUM_EXTENSIONS),
            "broken": broken,
            "broken_count": len(broken)
        }

    def _check_cross_references(self) -> dict:
        """交叉引用检查: nexus定义的cap vs 实际caps/目录"""
        broken = []
        scan = self.scan()
        
        # nexus定义的所有cap
        defined = set()
        for domain, info in self.neighborhoods.items():
            for cap_name in info["caps"]:
                defined.add(cap_name)
        
        # 实际存在的cap目录
        actual = set()
        for domain, info in scan["domains"].items():
            for cap_name, cap in info["caps"].items():
                if cap["exists"]:
                    actual.add(cap_name)
        
        # 定义了但不存在
        missing = defined - actual
        for cap in missing:
            # 找到它属于哪个邻域
            domain = next((d for d, i in self.neighborhoods.items() if cap in i["caps"]), "未知")
            broken.append({
                "type": "defined_but_missing",
                "cap": cap,
                "domain": domain,
                "severity": "critical" if self._is_core(cap) else "warning"
            })
        
        # 存在但未定义(孤儿cap)
        orphan = actual - defined
        for cap in orphan:
            broken.append({
                "type": "orphan_cap",
                "cap": cap,
                "severity": "warning",
                "fix": f"将{cap}加入nexus邻域定义"
            })
        
        return {
            "ok": len(broken) == 0,
            "defined": len(defined),
            "actual": len(actual),
            "missing": list(missing),
            "orphans": list(orphan),
            "broken": broken
        }

    def _check_integrity(self) -> dict:
        """完整性检查: run.py可导入/capability.json格式正确"""
        broken = []
        scan = self.scan()
        
        for domain, info in scan["domains"].items():
            for cap_name, cap in info["caps"].items():
                if not cap["exists"]:
                    continue
                
                cap_dir = ROOT / "brain" if domain == "🧠 多脑域" else CAPS_DIR / cap_name
                is_brain = domain == "🧠 多脑域"

                # 脑模块用 .py 文件, 不是 capability.json
                if is_brain:
                    brain_file = cap_dir / f"{cap_name}.py"
                    if brain_file.exists():
                        try:
                            code = brain_file.read_text(encoding="utf-8")
                            compile(code, str(brain_file), "exec")
                        except SyntaxError as e:
                            broken.append({
                                "type": "syntax_error",
                                "cap": cap_name,
                                "issue": str(e)[:100],
                                "severity": "critical"
                            })
                        except Exception:
                            broken.append({
                                "type": "unreadable_brain_module",
                                "cap": cap_name,
                                "severity": "high"
                            })
                    continue
                
                # 检查capability.json格式
                try:
                    cj = cap_dir / "capability.json"
                    data = json.loads(cj.read_text(encoding="utf-8"))
                    if "name" not in data or "actions" not in data:
                        broken.append({
                            "type": "invalid_capability_json",
                            "cap": cap_name,
                            "issue": "缺少name或actions字段",
                            "severity": "high"
                        })
                except json.JSONDecodeError as e:
                    broken.append({
                        "type": "corrupt_capability_json",
                        "cap": cap_name,
                        "issue": str(e)[:100],
                        "severity": "critical"
                    })
                except Exception:
                    pass
                
                # 检查run.py语法
                try:
                    rp = cap_dir / "run.py"
                    code = rp.read_text(encoding="utf-8")
                    compile(code, str(rp), "exec")
                except SyntaxError as e:
                    broken.append({
                        "type": "syntax_error",
                        "cap": cap_name,
                        "issue": str(e)[:100],
                        "severity": "critical"
                    })
                except Exception:
                    broken.append({
                        "type": "unreadable_run_py",
                        "cap": cap_name,
                        "severity": "high"
                    })
        
        return {
            "ok": len(broken) == 0,
            "broken": broken,
            "broken_count": len(broken)
        }

    def _is_core(self, cap_name: str) -> bool:
        for domain, info in self.neighborhoods.items():
            if cap_name in info["caps"]:
                _, _, status = info["caps"][cap_name]
                return status == "core"
        return False

    def connection_map(self) -> dict:
        """连接拓扑图 — 展示所有连接点和依赖关系"""
        scan = self.scan()
        routes_map = {}
        for intent, (domain, caps) in self.routes.items():
            routes_map[intent] = {
                "domain": domain,
                "caps": caps,
                "all_exist": all(
                    any(cap in d["caps"] and d["caps"][cap]["exists"] 
                        for d in scan["domains"].values())
                    for cap in caps
                )
            }
        
        quantum_map = {}
        for cap_name, targets in QUANTUM_EXTENSIONS.items():
            exists = any(
                cap_name in d.get("caps", {}) and d["caps"][cap_name].get("exists")
                for d in scan["domains"].values()
            )
            quantum_map[cap_name] = {
                "exists": exists,
                "extends_to": targets,
                "targets_exist": [t for t in targets if t in self.neighborhoods]
            }
        
        return {
            "routes": {"total": len(routes_map), "all_intact": all(r["all_exist"] for r in routes_map.values()), "details": routes_map},
            "quantum": {"total": len(quantum_map), "all_exist": all(q["exists"] for q in quantum_map.values()), "details": quantum_map},
            "neighborhoods": {d: {"icon": i["icon"], "caps": list(i["caps"].keys())} for d, i in self.neighborhoods.items()}
        }



    def watch(self, interval_seconds: int = 300) -> dict:
        """持续监控 — 定期深度扫描，发现断连立即告警"""
        result = self.deep_scan()
        if not result["ok"]:
            issues = result["issues"]
            alert = {
                "alert": "⛔ 邻域断连告警",
                "timestamp": time.time(),
                "severity": "critical" if any(i["severity"] == "critical" for i in issues) else "warning",
                "issues": issues,
                "action_required": f"立即修复{len(issues)}处断连",
                "details": result
            }
            try:
                from brain.self_evolve import get_evolver
                get_evolver().add_lesson(
                    f"邻域断连告警: {len(issues)}处问题",
                    category="nexus", severity="critical",
                    source_task="nexus.watch持续监控"
                )
            except Exception:
                pass
            return alert
        return {"ok": True, "message": "邻域连接正常", "timestamp": time.time()}


def council_ingest(content: str, context: dict = None) -> dict:
    """脑委会统一入口 — 10脑并行分析"""
    from brain.brain_council import ingest
    return ingest(content, context)
# 全局单例
_nexus: Optional[NexusHub] = None

def get_nexus() -> NexusHub:
    global _nexus
    if _nexus is None:
        _nexus = NexusHub()
    return _nexus


# 快速函数(方便外部调用)
def scan() -> dict:        return get_nexus().scan()
def route(i: str, q="") -> dict: return get_nexus().route(i, q)
def topology() -> dict:    return get_nexus().topology()
def diagnose() -> dict:    return get_nexus().diagnose()
def quick_health() -> dict: return get_nexus().quick_health()
def penetration_scan(auto_fix: bool = False, deep: bool = False) -> dict: return get_nexus().penetration_scan(auto_fix, deep)
def tentacle_pulse() -> dict:
    """神经触手脉冲 — 扫描→差分→注入邻域"""
    from brain.neural_tentacle import pulse
    return pulse()


def _serve_mcp() -> None:
    """MCP stdio server — JSON-RPC 2.0 over stdio.

    从 stdin 读取 JSON-RPC 请求, 处理后写入 stdout。
    """
    hub = get_nexus()

    TOOLS = {
        "scan": {
            "name": "scan", "description": "全邻域扫描 — 检查每个能力模块是否存在",
            "inputSchema": {"type": "object", "properties": {"force": {"type": "boolean", "description": "强制重新扫描, 忽略缓存"}}}
        },
        "quick_health": {
            "name": "quick_health", "description": "快速健康检查 — 只看core模块",
            "inputSchema": {"type": "object", "properties": {}}
        },
        "topology": {
            "name": "topology", "description": "邻域拓扑摘要 — 展示所有12大AI邻域结构",
            "inputSchema": {"type": "object", "properties": {}}
        },
        "diagnose": {
            "name": "diagnose", "description": "深度自排查 — 发现问题并给出修复建议",
            "inputSchema": {"type": "object", "properties": {}}
        },
        "deep_scan": {
            "name": "deep_scan", "description": "深度邻域扫描 — 检查所有连接点完整性, 路由引用, 交叉引用, 文件完整性",
            "inputSchema": {"type": "object", "properties": {}}
        },
        "connection_map": {
            "name": "connection_map", "description": "连接拓扑图 — 展示所有连接点和依赖关系",
            "inputSchema": {"type": "object", "properties": {}}
        },
        "route": {
            "name": "route", "description": "意图→能力路由 — 将用户意图路由到对应能力模块",
            "inputSchema": {"type": "object", "properties": {"intent": {"type": "string", "description": "意图关键词"}, "query": {"type": "string", "description": "补充查询"}}, "required": ["intent"]}
        },
        "bridge": {
            "name": "bridge", "description": "跨领域数据传递 — 在两个邻域间桥接数据",
            "inputSchema": {"type": "object", "properties": {"from_domain": {"type": "string"}, "to_domain": {"type": "string"}, "data": {"type": "object"}}, "required": ["from_domain", "to_domain"]}
        },
        "quantum_extension": {
            "name": "quantum_extension", "description": "查询量子能力延申到哪些邻域",
            "inputSchema": {"type": "object", "properties": {"cap_name": {"type": "string"}}, "required": ["cap_name"]}
        },
        "quantum_topology": {
            "name": "quantum_topology", "description": "量子延申拓扑 — 展示量子邻域如何渗透到所有已知邻域",
            "inputSchema": {"type": "object", "properties": {}}
        },
        "entanglement_route": {
            "name": "entanglement_route", "description": "量子纠缠路由 — 通过量子通道跨邻域传递数据",
            "inputSchema": {"type": "object", "properties": {"from_domain": {"type": "string"}, "to_domain": {"type": "string"}}, "required": ["from_domain", "to_domain"]}
        },
        "watch": {
            "name": "watch", "description": "持续监控 — 深度扫描, 发现断连立即告警",
            "inputSchema": {"type": "object", "properties": {"interval_seconds": {"type": "integer", "description": "监控间隔(秒), 默认300"}}}
        },
    }

    TOOL_IMPLS = {
        "scan": lambda args: hub.scan(force=args.get("force", False)),
        "quick_health": lambda args: hub.quick_health(),
        "topology": lambda args: hub.topology(),
        "diagnose": lambda args: hub.diagnose(),
        "deep_scan": lambda args: hub.deep_scan(),
        "connection_map": lambda args: hub.connection_map(),
        "route": lambda args: hub.route(args.get("intent", ""), args.get("query", "")),
        "bridge": lambda args: hub.bridge(args["from_domain"], args["to_domain"], args.get("data")),
        "quantum_extension": lambda args: hub.quantum_extension(args["cap_name"]),
        "quantum_topology": lambda args: hub.quantum_topology(),
        "entanglement_route": lambda args: hub.entanglement_route(args["from_domain"], args["to_domain"]),
        "watch": lambda args: hub.watch(args.get("interval_seconds", 300)),
    }

    def _send(id_, result=None, error=None):
        msg = {"jsonrpc": "2.0", "id": id_}
        if error:
            msg["error"] = error
        else:
            msg["result"] = result
        _sys.stdout.write(json.dumps(msg, ensure_ascii=False, default=str) + "\n")
        _sys.stdout.flush()

    for line in _sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        rid = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            _send(rid, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "gbt-brain", "version": "1.0.0"}
            })
        elif method == "tools/list":
            _send(rid, {"tools": list(TOOLS.values())})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            impl = TOOL_IMPLS.get(tool_name)
            if impl:
                try:
                    result = impl(tool_args)
                    _send(rid, {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}]})
                except Exception as e:
                    _send(rid, error={"code": -32000, "message": str(e)})
            else:
                _send(rid, error={"code": -32601, "message": f"Unknown tool: {tool_name}"})
        elif method == "notifications/initialized":
            pass  # no response for notifications
        else:
            _send(rid, error={"code": -32601, "message": f"Unknown method: {method}"})

if __name__ == "__main__":
    import sys as _sys
    if "--serve" in _sys.argv:
        _serve_mcp()
    else:
        hub = get_nexus()
        fn = actions.get(action, hub.scan)
        result = fn()
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
