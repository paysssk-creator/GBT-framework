# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
skill_library/run.py — 生产级工程技能库 v1.0

融合 agent-skills 的 Define→Plan→Build→Verify→Review→Ship 流水线
将24项生产级工程技能编码为 GBT 能力，AI编程时自动激活。

核心动作:
  spec     — 需求定义: 先写规格再写代码
  plan     — 任务规划: 拆分为小型原子任务
  build    — 增量构建: 一次一个切片
  test     — 验证: 测试是证明不是装饰
  review   — 代码审查: 五轴质量门
  ship     — 发布上线: 越快越安全
  skills   — 列出所有可用技能
  activate — 根据上下文自动激活匹配技能
"""

import sys, json, os, re
from pathlib import Path
from datetime import datetime, timezone

# ══════════════════════════════════════════════════════════
# 24项生产级工程技能定义 (融合 agent-skills)
# ══════════════════════════════════════════════════════════

SKILLS = {
    # ── Phase: DEFINE (定义) ──
    "spec-driven-development": {
        "phase": "define",
        "name": "规格驱动开发",
        "principle": "先写规格再写代码",
        "triggers": ["新功能", "需求", "spec", "设计", "feature"],
        "rules": [
            "编写详细的功能规格说明(PRD)后才开始编码",
            "包含: 目标、用户故事、验收标准、边界条件、错误处理",
            "用 /spec 命令生成规格文档",
            "规格经审查批准后才进入实现阶段",
        ],
    },
    "idea-refinement": {
        "phase": "define",
        "name": "想法精炼",
        "principle": "模糊想法→清晰需求",
        "triggers": ["想法", "idea", "能不能", "可否", "或许"],
        "rules": [
            "追问5个为什么深入理解动机",
            "将模糊想法转化为可执行的具体需求",
            "识别约束条件和成功标准",
        ],
    },
    "interview-me": {
        "phase": "define",
        "name": "需求访谈",
        "principle": "一个问题一个问题地澄清需求",
        "triggers": ["需求不明确", "澄清", "确认需求"],
        "rules": [
            "每次只问一个问题，逐步缩小不确定性",
            "问题必须是选择题或填空题，不能是开放题",
            "根据回答自动推断下一步问题",
        ],
    },

    # ── Phase: PLAN (规划) ──
    "planning-and-task-breakdown": {
        "phase": "plan",
        "name": "规划与任务分解",
        "principle": "小型原子任务",
        "triggers": ["规划", "plan", "拆分", "分解", "步骤"],
        "rules": [
            "将大任务分解为独立的小型原子任务",
            "每个任务: 单一职责、可独立测试、≤30分钟完成",
            "明确任务依赖关系，并行化独立任务",
            "每完成一个任务立即提交",
        ],
    },
    "incremental-implementation": {
        "phase": "plan",
        "name": "增量实现",
        "principle": "一次一个切片",
        "triggers": ["增量", "逐步", "迭代", "分步实现"],
        "rules": [
            "每次只改一个关注点",
            "改完即提交，保持每个commit原子化",
            "绝不积累多个不相关的改动在一次提交中",
        ],
    },
    "context-engineering": {
        "phase": "plan",
        "name": "上下文工程",
        "principle": "给AI最小必要上下文",
        "triggers": ["上下文", "context", "token", "太长"],
        "rules": [
            "只提供变更相关的文件/函数给AI",
            "用摘要替代完整文件（除非需要修改）",
            "使用结构化注释标记变更范围",
        ],
    },

    # ── Phase: BUILD (构建) ──
    "test-driven-development": {
        "phase": "build",
        "name": "测试驱动开发",
        "principle": "红→绿→重构循环",
        "triggers": ["测试", "TDD", "单元测试", "test"],
        "rules": [
            "先写失败的测试(Red)，再写最少代码通过(Green)，最后重构",
            "每个功能必须对应至少一个测试用例",
            "测试覆盖: 正常路径+边界条件+错误路径",
            "跑全量测试套件确认没有回归",
        ],
    },
    "frontend-ui-engineering": {
        "phase": "build",
        "name": "前端UI工程",
        "principle": "组件化+响应式+无障碍",
        "triggers": ["前端", "UI", "界面", "CSS", "React", "Vue", "组件"],
        "rules": [
            "组件单一职责，props类型明确",
            "支持键盘导航和屏幕阅读器",
            "响应式设计: mobile-first",
            "使用设计系统token而非硬编码值",
        ],
    },
    "api-and-interface-design": {
        "phase": "build",
        "name": "API与接口设计",
        "principle": "合约优先，版本控制",
        "triggers": ["API", "接口", "REST", "GraphQL", "endpoint"],
        "rules": [
            "先定义接口合约(OpenAPI/GraphQL schema)",
            "输入验证+错误标准化+速率限制",
            "向后兼容: 新增字段不破坏旧客户端",
            "文档同步更新: 改代码必改文档",
        ],
    },
    "source-driven-development": {
        "phase": "build",
        "name": "源码驱动开发",
        "principle": "参考现有代码风格",
        "triggers": ["改代码", "修改", "参考", "模仿"],
        "rules": [
            "先读3个相似的现有实现再动手",
            "遵循项目已有的模式和惯例",
            "不引入新的依赖/模式除非有充分理由",
        ],
    },

    # ── Phase: VERIFY (验证) ──
    "debugging-and-error-recovery": {
        "phase": "verify",
        "name": "调试与错误恢复",
        "principle": "假设→取证→修复→验证",
        "triggers": ["debug", "调试", "bug", "错误", "报错", "修复"],
        "rules": [
            "阅读完整错误堆栈，定位根因而非症状",
            "提出可证伪的假设，用日志/断点验证",
            "一次只改一个变量，确认修复后再改下一个",
            "修复后添加回归测试防止复发",
        ],
    },
    "browser-testing-with-devtools": {
        "phase": "verify",
        "name": "浏览器DevTools测试",
        "principle": "在真实浏览器中验证",
        "triggers": ["浏览器测试", "UI测试", "E2E", "端到端"],
        "rules": [
            "用真实浏览器(非headless)验证UI交互",
            "检查Console错误、Network请求、Performance指标",
            "模拟慢网络和移动设备测试",
        ],
    },
    "observability-and-instrumentation": {
        "phase": "verify",
        "name": "可观测性",
        "principle": "你不能优化你看不到的东西",
        "triggers": ["监控", "日志", "metrics", "性能", "排查"],
        "rules": [
            "关键路径必须有结构化日志",
            "错误必须包含: what/when/where/context",
            "指标: 延迟、错误率、吞吐量",
            "告警: 关键指标异常自动通知",
        ],
    },

    # ── Phase: REVIEW (审查) ──
    "code-review-and-quality": {
        "phase": "review",
        "name": "代码审查(五轴质量门)",
        "principle": "提交前5维度审查",
        "triggers": ["review", "审查", "检查", "代码质量"],
        "rules": [
            "① 正确性: 逻辑是否正确？边界条件？",
            "② 安全性: 输入验证？注入防护？认证授权？",
            "③ 性能: 不必要的循环？N+1查询？内存泄漏？",
            "④ 可维护性: 命名清晰？单一职责？无重复代码？",
            "⑤ 一致性: 符合项目风格？模式一致？",
        ],
    },
    "security-and-hardening": {
        "phase": "review",
        "name": "安全加固",
        "principle": "假设所有输入都是恶意的",
        "triggers": ["安全", "security", "加固", "漏洞"],
        "rules": [
            "输入验证: 所有外部输入必须校验和消毒",
            "认证授权: 检查每个端点是否有正确的权限控制",
            "敏感数据: 不在日志/URL/客户端暴露密钥",
            "依赖审计: 检查第三方库的已知漏洞",
        ],
    },
    "code-simplification": {
        "phase": "review",
        "name": "代码简化",
        "principle": "清晰优于聪明",
        "triggers": ["简化", "重构", "清理", "简化代码"],
        "rules": [
            "删除死代码和注释掉的代码",
            "合并重复逻辑，提取公共函数",
            "降低嵌套深度(≤3层)",
            "函数≤50行，参数≤5个",
        ],
    },
    "deprecation-and-migration": {
        "phase": "review",
        "name": "废弃与迁移",
        "principle": "平稳过渡，零停机",
        "triggers": ["迁移", "升级", "废弃", "deprecation"],
        "rules": [
            "先标记废弃(警告)，再删除(下个大版本)",
            "提供迁移指南和自动化脚本",
            "保持向后兼容至少一个版本周期",
        ],
    },
    "performance-optimization": {
        "phase": "review",
        "name": "性能优化",
        "principle": "先测量再优化",
        "triggers": ["性能", "优化", "加速", "慢", "卡"],
        "rules": [
            "用profiler找到真正的瓶颈(不要猜测)",
            "优化最热的20%代码(80/20法则)",
            "缓存: 计算结果/数据库查询/API响应",
            "优化后必须重新基准测试确认提升",
        ],
    },

    # ── Phase: SHIP (发布) ──
    "ci-cd-and-automation": {
        "phase": "ship",
        "name": "CI/CD自动化",
        "principle": "每次提交都通过流水线",
        "triggers": ["CI", "CD", "部署", "流水线", "自动化"],
        "rules": [
            "每次推送自动运行: lint→test→build→deploy",
            "失败阻止合并: 任何检查失败不能合入主分支",
            "自动化回滚: 部署失败自动回退到上一个稳定版本",
        ],
    },
    "shipping-and-launch": {
        "phase": "ship",
        "name": "发布上线",
        "principle": "越快发布越安全",
        "triggers": ["发布", "上线", "ship", "launch", "部署"],
        "rules": [
            "小批量频繁发布(每天多次)优于大批量偶尔发布",
            "功能开关: 新功能默认关闭，逐步灰度",
            "监控告警: 发布后立即观察错误率和延迟",
            "回滚预案: 任何异常立即回滚",
        ],
    },
    "documentation-and-adrs": {
        "phase": "ship",
        "name": "文档与架构决策记录",
        "principle": "为6个月后的维护者写文档",
        "triggers": ["文档", "doc", "README", "说明", "架构决策"],
        "rules": [
            "每个模块: 一句话说明用途+一个最小示例",
            "架构决策记录(ADR): 记录为什么这样设计",
            "README: 安装→快速开始→API→贡献指南",
            "代码注释: 解释why不是what",
        ],
    },
    "git-workflow-and-versioning": {
        "phase": "ship",
        "name": "Git工作流与版本管理",
        "principle": "语义化版本+规范化提交",
        "triggers": ["git", "提交", "commit", "版本", "分支"],
        "rules": [
            "语义化版本: MAJOR.MINOR.PATCH",
            "Conventional Commits: feat/fix/docs/refactor/test/chore",
            "分支策略: main(稳定)→feature分支→PR审查→合并",
            "每个commit只做一件事",
        ],
    },
    "doubt-driven-development": {
        "phase": "ship",
        "name": "质疑驱动开发",
        "principle": "对每个假设提出质疑",
        "triggers": ["质疑", "验证", "确认", "对不对", "是否"],
        "rules": [
            "这个方案有更简单的替代吗？",
            "这个假设经过验证吗？",
            "这个变更会影响其他功能吗？",
            "这个决策6个月后还合理吗？",
        ],
    },
    "ponytail-lazy-dev": {
        "phase": "build",
        "name": "Ponytail懒人开发",
        "principle": "最好的代码是不写的代码 — 六阶梯决策",
        "triggers": ["写代码", "实现", "开发", "coding", "代码", "编程", "构建", "build"],
        "rules": [
            "决策阶梯1: 这个功能真的需要存在吗？不需要就跳过(YAGNI)",
            "决策阶梯2: 代码库里已经有了？直接复用，不要重写",
            "决策阶梯3: 标准库能实现？用标准库，不引入依赖",
            "决策阶梯4: 原生平台功能？用原生<input>而非组件库",
            "决策阶梯5: 已安装的依赖能做？用现有依赖",
            "决策阶梯6: 一行代码能搞定？写一行，不写五十行",
            "安全底线: 输入验证/错误处理/安全检查绝不省略",
            "核心原则: 懒惰于解决方案，勤奋于阅读理解",
        ],
    },
    
}

# ══════════════════════════════════════════════════════════
# 代理角色定义 (融合 agent-skills agents/)
# ══════════════════════════════════════════════════════════

AGENTS = {
    "code-reviewer": {
        "role": "代码审查员",
        "focus": ["代码质量", "安全性", "性能", "可维护性", "一致性"],
        "instruction": "用五轴质量门审查代码: 正确性/安全性/性能/可维护性/一致性",
    },
    "security-auditor": {
        "role": "安全审计员",
        "focus": ["输入验证", "认证授权", "敏感数据", "依赖漏洞", "注入攻击"],
        "instruction": "假设所有输入都是恶意的，审计每个入口点的安全性",
    },
    "test-engineer": {
        "role": "测试工程师",
        "focus": ["单元测试", "集成测试", "E2E测试", "边界条件", "回归测试"],
        "instruction": "红→绿→重构: 先写失败测试，再写最少代码通过，最后重构",
    },
    "web-performance-auditor": {
        "role": "Web性能审计员",
        "focus": ["Core Web Vitals", "加载时间", "渲染性能", "资源优化"],
        "instruction": "先测量再优化: LCP<2.5s, FID<100ms, CLS<0.1",
    },
}

# ══════════════════════════════════════════════════════════
# Actions
# ══════════════════════════════════════════════════════════

def do_spec(params: dict) -> dict:
    """/spec — 需求定义: 先写规格再写代码"""
    task = params.get("task", params.get("prompt", ""))
    if not task:
        return {"ok": False, "error": "需要 task"}

    skill = SKILLS["spec-driven-development"]
    return {
        "ok": True,
        "phase": "define",
        "skill": skill["name"],
        "principle": skill["principle"],
        "rules": skill["rules"],
        "output_template": f"""# 功能规格说明
## 目标
{task}

## 用户故事
- 作为[角色]，我想要[功能]，以便[价值]

## 验收标准
- [ ] 标准1: ...
- [ ] 标准2: ...

## 边界条件
- 正常路径: ...
- 错误路径: ...
- 边界值: ...

## 技术约束
- ...
""",
    }


def do_plan(params: dict) -> dict:
    """/plan — 任务规划: 拆分为小型原子任务"""
    task = params.get("task", params.get("prompt", ""))
    skill = SKILLS["planning-and-task-breakdown"]

    return {
        "ok": True,
        "phase": "plan",
        "skill": skill["name"],
        "principle": skill["principle"],
        "rules": skill["rules"],
        "instruction": f"将'{task}'分解为独立的小型原子任务，每个≤30分钟，明确依赖关系",
    }


def do_build(params: dict) -> dict:
    """/build — 增量构建: 一次一个切片"""
    task = params.get("task", params.get("prompt", ""))
    auto = params.get("auto", False)

    skills = [
        SKILLS["test-driven-development"],
        SKILLS["incremental-implementation"],
        SKILLS["source-driven-development"],
    ]

    result = {
        "ok": True, "phase": "build", "auto_mode": auto,
        "active_skills": [s["name"] for s in skills],
        "rules": [],
    }
    for s in skills:
        result["rules"].extend(s["rules"])

    if auto:
        result["mode"] = "auto"
        result["instruction"] = "自主模式: 规划→逐任务TDD实现→每任务提交→遇失败暂停"
    return result


def do_test(params: dict) -> dict:
    """/test — 验证: 测试是证明不是装饰"""
    skill = SKILLS["test-driven-development"]
    return {
        "ok": True, "phase": "verify",
        "skill": skill["name"], "principle": skill["principle"],
        "rules": skill["rules"],
        "checklist": [
            "每个功能有对应测试吗？",
            "测试覆盖了正常路径+边界条件+错误路径吗？",
            "跑全量测试套件确认无回归了吗？",
        ],
    }


def do_review(params: dict) -> dict:
    """/review — 代码审查: 五轴质量门"""
    skill = SKILLS["code-review-and-quality"]
    sec = SKILLS["security-and-hardening"]
    perf = SKILLS["performance-optimization"]

    return {
        "ok": True, "phase": "review",
        "quality_gates": {
            "correctness": {"check": "逻辑正确？边界条件处理？", "weight": 5},
            "security": {"check": "输入验证？注入防护？认证授权？", "weight": 5},
            "performance": {"check": "不必要循环？N+1查询？内存泄漏？", "weight": 3},
            "maintainability": {"check": "命名清晰？单一职责？无重复？", "weight": 3},
            "consistency": {"check": "符合项目风格？模式一致？", "weight": 2},
        },
        "pass_threshold": "五轴全部通过才能合并",
    }


def do_ship(params: dict) -> dict:
    """/ship — 发布上线: 越快越安全"""
    cicd = SKILLS["ci-cd-and-automation"]
    launch = SKILLS["shipping-and-launch"]
    git = SKILLS["git-workflow-and-versioning"]

    return {
        "ok": True, "phase": "ship",
        "active_skills": [cicd["name"], launch["name"], git["name"]],
        "pipeline": [
            "1. 语义化版本号确定",
            "2. 全量测试套件通过",
            "3. 五轴质量门审查通过",
            "4. 构建产物验证",
            "5. 灰度发布(10%→50%→100%)",
            "6. 监控告警确认",
            "7. 回滚预案就绪",
        ],
        "principle": launch["principle"],
    }


def do_skills(params: dict) -> dict:
    """列出所有可用工程技能"""
    phase = params.get("phase", "")
    query = params.get("query", params.get("prompt", ""))

    if phase:
        matched = {k: v for k, v in SKILLS.items() if v["phase"] == phase}
    elif query:
        ql = query.lower()
        matched = {}
        for k, v in SKILLS.items():
            if ql in k.lower() or any(ql in t.lower() for t in v.get("triggers", [])):
                matched[k] = v
    else:
        matched = SKILLS

    return {
        "ok": True,
        "total_skills": len(SKILLS),
        "matched": len(matched),
        "skills": [{"id": k, "name": v["name"], "phase": v["phase"],
                     "principle": v["principle"]} for k, v in matched.items()],
        "phases": {
            "define": [k for k, v in SKILLS.items() if v["phase"] == "define"],
            "plan": [k for k, v in SKILLS.items() if v["phase"] == "plan"],
            "build": [k for k, v in SKILLS.items() if v["phase"] == "build"],
            "verify": [k for k, v in SKILLS.items() if v["phase"] == "verify"],
            "review": [k for k, v in SKILLS.items() if v["phase"] == "review"],
            "ship": [k for k, v in SKILLS.items() if v["phase"] == "ship"],
        },
    }


def do_activate(params: dict) -> dict:
    """根据上下文自动激活匹配的工程技能"""
    context = params.get("context", params.get("task", params.get("prompt", "")))
    if not context:
        return {"ok": False, "error": "需要 context"}

    context_lower = context.lower()
    activated = []

    for skill_id, skill in SKILLS.items():
        triggers = skill.get("triggers", [])
        for trigger in triggers:
            if trigger.lower() in context_lower:
                activated.append({
                    "id": skill_id,
                    "name": skill["name"],
                    "phase": skill["phase"],
                    "principle": skill["principle"],
                    "rules": skill["rules"][:3],  # 只返回前3条规则节省token
                })
                break

    # 按phase排序: define→plan→build→verify→review→ship
    phase_order = {"define": 0, "plan": 1, "build": 2, "verify": 3, "review": 4, "ship": 5}
    activated.sort(key=lambda s: phase_order.get(s["phase"], 99))

    return {
        "ok": True,
        "context": context[:200],
        "activated_count": len(activated),
        "activated": activated,
        "instruction": "以上工程技能已激活，请遵循对应规则执行任务",
    }


def do_agents(params: dict) -> dict:
    """列出/激活专业AI代理角色"""
    agent_id = params.get("agent", params.get("role", ""))
    if agent_id and agent_id in AGENTS:
        agent = AGENTS[agent_id]
        return {"ok": True, "agent_activated": True, **agent}

    return {
        "ok": True,
        "available_agents": [
            {"id": k, "role": v["role"], "focus": v["focus"]}
            for k, v in AGENTS.items()
        ],
    }


def do_auto_catalog(params: dict) -> dict:
    """auto_catalog — 扫描所有 caps 目录并编目能力"""
    caps_root = Path(__file__).parent.parent
    catalog: dict[str, dict] = {}

    for cap_dir in sorted(caps_root.iterdir()):
        if not cap_dir.is_dir() or cap_dir.name.startswith(".") or cap_dir.name.startswith("__"):
            continue

        run_py = cap_dir / "run.py"
        if not run_py.exists():
            continue

        try:
            content = run_py.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Extract docstring header
        header_match = re.search(r'^"""(.*?)"""', content, re.DOTALL)
        header = header_match.group(1).strip() if header_match else ""
        first_line = header.split("\n")[0].strip() if header else cap_dir.name

        # Extract all action/do_* function definitions
        actions: list[str] = []
        action_pat = re.compile(r'^def\s+do_(\w+)\s*\(', re.MULTILINE)
        for m in action_pat.finditer(content):
            actions.append(m.group(1))

        # Extract handler dict keys
        handler_keys: list[str] = []
        handler_pat = re.compile(r'["\'](\w+)["\']\s*:\s*do_', re.MULTILINE)
        for m in handler_pat.finditer(content):
            handler_keys.append(m.group(1))

        # Also check HANDLERS = { ... } block
        handler_block = re.search(r'(?:handlers|HANDLERS)\s*=\s*\{(.*?)\}', content, re.DOTALL)
        if handler_block:
            key_pat = re.compile(r'["\'](\w+)["\']\s*:', re.MULTILINE)
            for m in key_pat.finditer(handler_block.group(1)):
                k = m.group(1)
                if k not in handler_keys:
                    handler_keys.append(k)

        catalog[cap_dir.name] = {
            "capability": first_line[:120],
            "actions": actions if actions else handler_keys,
            "path": str(run_py.relative_to(caps_root.parent)),
        }

    # Compute summary statistics
    total_caps = len(catalog)
    total_actions = sum(len(v["actions"]) for v in catalog.values())

    return {
        "ok": True,
        "action": "auto_catalog",
        "total_capabilities": total_caps,
        "total_actions": total_actions,
        "catalog": catalog,
        "capability_names": sorted(catalog.keys()),
    }


def do_skill_gap_report(params: dict) -> dict:
    """skill_gap_report — 对比行业标准技能集，生成差距报告"""
    # Industry-standard engineering skill taxonomy
    industry_standards = {
        "testing": ["单元测试", "集成测试", "E2E测试", "性能测试", "安全测试", "混沌工程", "契约测试", "快照测试"],
        "ci_cd": ["持续集成", "持续部署", "金丝雀发布", "蓝绿部署", "特性开关", "回滚策略", "制品管理", "环境管理"],
        "observability": ["日志聚合", "分布式追踪", "指标监控", "告警管理", "SLO/SLI", "错误追踪", "APM", "RUM"],
        "security": ["SAST", "DAST", "依赖扫描", "密钥管理", "WAF", "RBAC", "审计日志", "威胁建模"],
        "infrastructure": ["IaC", "容器化", "编排", "服务网格", "自动扩缩容", "负载均衡", "DNS管理", "证书管理"],
        "data": ["数据建模", "迁移管理", "缓存策略", "数据治理", "ETL管道", "实时流处理", "数据血缘", "备份恢复"],
        "collaboration": ["代码审查", "结对编程", "文档即代码", "ADR", "RFC流程", "知识共享", "异步沟通", "事后复盘"],
        "ai_ml": ["模型训练", "特征工程", "模型服务", "ML管道", "漂移检测", "A/B测试", "可解释性", "模型治理"],
    }

    # Map our SKILLS keys to industry categories
    skill_to_category = {
        "test-driven-development": "testing",
        "observability-driven-dev": "observability",
        "ci-cd-pipeline": "ci_cd",
        "security-first": "security",
        "infrastructure-as-code": "infrastructure",
        "data-modeling": "data",
        "code-review": "collaboration",
        "documentation-and-adrs": "collaboration",
        "git-workflow-and-versioning": "collaboration",
        "containerization": "infrastructure",
        "api-design-first": "data",
        "error-handling": "observability",
        "dependency-management": "infrastructure",
        "shipping-and-launch": "ci_cd",
        "doubt-driven-development": "collaboration",
        "ponytail-lazy-dev": "collaboration",
    }

    # Compute coverage
    gaps: dict[str, dict] = {}
    covered: dict[str, list[str]] = {}
    for cat, standards in industry_standards.items():
        our_skills = [k for k, c in skill_to_category.items() if c == cat and k in SKILLS]
        covered[cat] = our_skills
        # Also check triggers for partial matches
        for std in standards:
            found = False
            for sk_id, sk_info in SKILLS.items():
                triggers = sk_info.get("triggers", [])
                if any(std.lower() in t.lower() or t.lower() in std.lower() for t in triggers):
                    found = True
                    break
            if not found and not any(std.lower() in sk_id.lower() for sk_id in our_skills):
                gaps.setdefault(cat, {"standards": [], "priority": ""})
                gaps[cat]["standards"].append(std)

    # Assign priority
    for cat, info in gaps.items():
        missing = len(info["standards"])
        total = len(industry_standards[cat])
        ratio = missing / total
        if ratio > 0.6:
            info["priority"] = "critical"
        elif ratio > 0.3:
            info["priority"] = "high"
        elif ratio > 0:
            info["priority"] = "medium"
        else:
            info["priority"] = "low"

    return {
        "ok": True,
        "action": "skill_gap_report",
        "total_skills": len(SKILLS),
        "categories_evaluated": len(industry_standards),
        "coverage": {cat: {"covered": len(v), "total": len(industry_standards[cat])} for cat, v in covered.items()},
        "gaps": {k: v for k, v in gaps.items() if v["standards"]},
        "recommendation": "优先填补 critical 和 high 优先级的技能缺口，增强体系完整性",
    }


def do_learn_from_devourer(params: dict) -> dict:
    """learn_from_devourer — 摄入 devourer 发现并创建新技能条目"""
    finding = params.get("finding", params.get("data", {}))
    skill_id = params.get("skill_id", params.get("id", ""))
    skill_name = params.get("skill_name", params.get("name", ""))
    phase = params.get("phase", "build")
    principle = params.get("principle", "")
    triggers = params.get("triggers", [])
    rules = params.get("rules", [])
    persist = params.get("persist", False)

    # If finding is a dict with specific keys, extract them
    if isinstance(finding, dict) and finding:
        if not skill_id:
            skill_id = finding.get("id", finding.get("skill_id", ""))
        if not skill_name:
            skill_name = finding.get("name", finding.get("title", finding.get("skill_name", "")))
        if not principle:
            principle = finding.get("principle", finding.get("description", ""))
        if not triggers:
            triggers = finding.get("triggers", finding.get("keywords", []))
        if not rules:
            rules = finding.get("rules", finding.get("best_practices", finding.get("learnings", [])))

    if not skill_id:
        return {"ok": False, "error": "需要 skill_id 或 finding 中包含 id"}
    if not rules:
        return {"ok": False, "error": "需要 rules 或 finding 中包含规则/最佳实践"}

    # Build the new skill entry
    new_skill = {
        "phase": phase,
        "name": skill_name or skill_id,
        "principle": principle or f"从 devourer 发现中学习的技能: {skill_id}",
        "triggers": triggers if triggers else [skill_id, skill_name] if skill_name else [skill_id],
        "rules": rules if isinstance(rules, list) else [str(rules)],
        "_source": "devourer",
        "_learned_at": datetime.now(timezone.utc).isoformat(),
    }

    # Check if skill already exists
    existing = SKILLS.get(skill_id)
    was_new = not existing

    # Update in-memory (and optionally persist)
    SKILLS[skill_id] = new_skill

    persisted_path = None
    if persist:
        # Persist to ~/.gbt/skills.json
        persist_dir = Path.home() / ".gbt"
        persist_dir.mkdir(parents=True, exist_ok=True)
        skills_file = persist_dir / "learned_skills.json"
        try:
            if skills_file.exists():
                stored = json.loads(skills_file.read_text(encoding="utf-8"))
            else:
                stored = {}
            stored[skill_id] = new_skill
            skills_file.write_text(json.dumps(stored, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            persisted_path = str(skills_file)
        except Exception as e:
            return {"ok": False, "error": f"持久化失败: {e}"}

    return {
        "ok": True,
        "action": "learn_from_devourer",
        "skill_id": skill_id,
        "was_new": was_new,
        "skill": new_skill,
        "persisted": persisted_path,
        "instruction": f"技能 '{skill_id}' {'已创建' if was_new else '已更新'}，现在可以在工程工作流中激活使用",
    }


# ══════════════════════════════════════════════════════════

HANDLERS = {
    "spec": do_spec, "plan": do_plan, "build": do_build,
    "test": do_test, "review": do_review, "ship": do_ship,
    "skills": do_skills, "activate": do_activate, "agents": do_agents,
    "auto_catalog": do_auto_catalog, "skill_gap_report": do_skill_gap_report, "learn_from_devourer": do_learn_from_devourer,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "skills"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知: {action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
