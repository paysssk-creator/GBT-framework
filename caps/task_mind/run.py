# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
caps/task_mind/run.py — 任务思维导图引擎
===========================================
将任何任务分解为精细到分钟级的执行步骤。
每步包含: 做什么 → 怎么做 → 用什么工具 → 预期产出 → 如何验证 → 预估耗时

输出格式:
  - mindmap:  Mermaid mindmap 思维导图
  - flowchart: Mermaid flowchart 决策流程图
  - checklist: 可勾选执行清单
  - ascii_tree: ASCII树形文本
  - gantt: 甘特图时间线
  - plan: 完整JSON规划 (4层深度)
"""
import sys, json, os, time, urllib.request, urllib.error

API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("KIMI_API_KEY") or ""
BASE_URL = os.environ.get("GBT_LLM_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("GBT_LLM_MODEL", "deepseek-chat")

# ═══════════════════════════════════════════════════════════
#  LLM调用
# ═══════════════════════════════════════════════════════════

def _call_llm(system: str, user: str, temp: float = 0.3, max_tok: int = 4000) -> dict:
    if not API_KEY:
        return {"ok": False, "error": "未配置LLM API Key"}
    try:
        data = json.dumps({
            "model": MODEL, "max_tokens": max_tok, "temperature": temp,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        }).encode("utf-8")
        req = urllib.request.Request(f"{BASE_URL}/chat/completions", data=data,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=90).read())
        return {"ok": True, "content": resp["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════
#  任务分解核心引擎
# ═══════════════════════════════════════════════════════════

PHASE_TEMPLATES = {
    "coding": {
        "phases": ["需求分析", "方案设计", "环境准备", "编码实现", "测试验证", "优化重构", "文档交付"],
        "detail_level": "函数级",
        "time_unit": "分钟"
    },
    "design": {
        "phases": ["需求调研", "概念设计", "详细设计", "原型验证", "设计交付"],
        "detail_level": "像素/组件级",
        "time_unit": "分钟"
    },
    "deploy": {
        "phases": ["环境检查", "备份", "部署执行", "健康检查", "监控配置", "回滚预案"],
        "detail_level": "命令级",
        "time_unit": "分钟"
    },
    "research": {
        "phases": ["问题定义", "资料收集", "分析对比", "实验验证", "结论输出"],
        "detail_level": "搜索词/论文级",
        "time_unit": "分钟"
    },
    "general": {
        "phases": ["理解任务", "准备资源", "执行核心", "验证结果", "整理交付"],
        "detail_level": "操作级",
        "time_unit": "分钟"
    }
}


def decompose_task(description: str, task_type: str = "general",
                   depth: int = 4, language: str = "zh") -> dict:
    """核心: 将任务分解为4层深度的精细步骤树"""
    
    if API_KEY:
        return _llm_decompose(description, task_type, depth, language)
    return _rule_decompose(description, task_type, depth, language)


def _llm_decompose(desc: str, task_type: str, depth: int, lang: str) -> dict:
    """LLM驱动: 极致精细的任务分解"""
    
    template = PHASE_TEMPLATES.get(task_type, PHASE_TEMPLATES["general"])
    
    system = f"""你是世界顶级项目管理和任务分解专家。你的专长是将任何任务分解到原子级操作。

任务类型: {task_type}
分解深度: {depth}层
时间精度: {template['time_unit']}级
细节级别: {template['detail_level']}

请返回JSON(严格遵守格式):
{{
  "task": "任务名称",
  "type": "{task_type}",
  "total_estimated_minutes": 总预估分钟数,
  "phases": [
    {{
      "phase": "阶段名称",
      "estimated_minutes": 阶段总分钟数,
      "objective": "阶段目标(一句话)",
      "steps": [
        {{
          "step_id": "1.1",
          "action": "具体操作(动词开头, 15-30字)",
          "how": "怎么做(具体方法, 50-150字) — 包括确切命令/工具/输入",
          "tool": "需要的工具/命令",
          "expected_output": "这一步完成后的具体产出(可验证的)",
          "verify": "如何验证这一步做对了(具体检查方法)",
          "estimated_minutes": 单步分钟数(整数),
          "depends_on": ["依赖的step_id"],
          "sub_steps": [
            {{
              "micro_id": "1.1.1",
              "micro_action": "微操作(5-15字)",
              "micro_how": "精确到手指动作的操作说明",
              "micro_time": 微操分钟数
            }}
          ]
        }}
      ]
    }}
  ],
  "critical_path": ["关键路径步骤ID列表"],
  "risk_points": [
    {{"step": "step_id", "risk": "风险描述", "mitigation": "缓解措施"}}
  ]
}}

规则:
1. 每个阶段包含3-8个步骤
2. 每个步骤包含2-5个微操作(sub_steps)
3. 微操作精确到: 打开什么文件→修改哪一行→运行什么命令→看到什么结果
4. how字段必须包含可执行的命令或伪代码
5. verify字段必须是可以客观检查的标准(不是"看起来OK")
6. 使用{'中文' if lang == 'zh' else 'English'}"""
    
    user = f"请将以下任务分解为极致精细的执行计划:\n\n{desc}"
    
    llm = _call_llm(system, user, temp=0.2, max_tok=4000)
    
    if llm.get("ok"):
        try:
            content = llm["content"].strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return {"ok": True, **json.loads(content)}
        except json.JSONDecodeError:
            pass
    
    return _rule_decompose(desc, task_type, depth, lang)


def _rule_decompose(desc: str, task_type: str, depth: int, lang: str) -> dict:
    """规则驱动回退: 结构化任务分解"""
    
    template = PHASE_TEMPLATES.get(task_type, PHASE_TEMPLATES["general"])
    
    step_templates = {
        "理解任务": [
            {"action": "通读需求", "how": "逐字阅读任务描述3遍，用笔标注关键词", 
             "tool": "大脑+纸笔", "verify": "能用自己的话复述需求且无歧义", "time": 5},
            {"action": "拆解关键词", "how": "从描述中提取: 做什么/给谁/限制条件/期望结果",
             "tool": "文本编辑器", "verify": "列出≥5个关键词和≥3个约束条件", "time": 5},
            {"action": "确认边界", "how": "明确: 哪些属于范围? 哪些明确排除? 输出边界清单",
             "tool": "Markdown", "verify": "边界清单有明确的include/exclude", "time": 3},
            {"action": "评估复杂度", "how": "根据关键词和边界评估: 简单(<1h)/中等(1-4h)/复杂(>4h)",
             "tool": "经验判断", "verify": "有明确的复杂度评级和理由", "time": 2},
        ],
        "准备资源": [
            {"action": "列出依赖", "how": "列出所有需要的: 文件/库/API/数据/权限/工具",
             "tool": "文本编辑器", "verify": "依赖清单每一项都可获取", "time": 5},
            {"action": "检查可用性", "how": "逐一确认每个依赖: 文件是否存在/库是否安装/API是否可用",
             "tool": "bash: ls/which/curl", "verify": "每个依赖状态=可用", "time": 5},
            {"action": "搭建环境", "how": "创建隔离工作目录，安装缺失依赖，配置环境变量",
             "tool": "bash: mkdir/pip install/export", "verify": "环境变量打印正确，依赖import不报错", "time": 10},
            {"action": "准备模板", "how": "创建文件骨架/目录结构/代码模板",
             "tool": "编辑器/touch命令", "verify": "模板文件存在且语法正确", "time": 5},
        ],
        "执行核心": [
            {"action": "执行第1步", "how": "按照分解的步骤，从最小可验证单元开始。每完成一个小步骤立即验证",
             "tool": "编辑器+终端", "verify": "小步骤的验收标准通过", "time": 15},
            {"action": "逐步骤推进", "how": "每步: 读当前状态→编辑→运行验证→如果失败→分析根因→修正→再验证",
             "tool": "编辑器+终端+调试器", "verify": "每步通过4a→4d子通道", "time": 30},
            {"action": "集成组装", "how": "将所有子模块按依赖顺序组装。先单元测试→再集成测试",
             "tool": "终端+测试框架", "verify": "集成测试全部通过", "time": 15},
            {"action": "边界测试", "how": "测试: 空输入/超长输入/特殊字符/并发/超时",
             "tool": "测试脚本", "verify": "所有边界case有预期行为", "time": 10},
        ],
        "验证结果": [
            {"action": "功能验证", "how": "按原始需求逐条对照验证。每条需求必须有一个对应的验证结果",
             "tool": "验收清单", "verify": "所有需求条目验证通过", "time": 10},
            {"action": "回归检查", "how": "检查改动是否影响其他模块: grep所有引用→确认无意外影响",
             "tool": "grep + 手动检查", "verify": "无新增错误/警告", "time": 10},
            {"action": "性能检查", "how": "如果涉及算法: 测试时间复杂度。如果涉及IO: 测试吞吐量",
             "tool": "time命令/性能测试脚本", "verify": "性能在可接受范围内", "time": 5},
            {"action": "安全审查", "how": "检查: 注入风险/权限泄露/敏感信息硬编码",
             "tool": "grep + 审查清单", "verify": "无高危安全问题", "time": 5},
        ],
        "整理交付": [
            {"action": "清理临时代码", "how": "删除所有: print调试/注释掉的旧代码/todo标记/临时文件",
             "tool": "编辑器+grep", "verify": "grep无debug关键词", "time": 5},
            {"action": "撰写文档", "how": "更新: README/API文档/使用说明/变更日志",
             "tool": "Markdown编辑器", "verify": "文档与代码一致", "time": 10},
            {"action": "最终检查", "how": "完整执行一遍: 从零搭建→运行→验证。模拟新用户首次使用",
             "tool": "全新终端", "verify": "从零到运行不超过文档描述的步骤", "time": 10},
            {"action": "交付确认", "how": "逐条确认验收标准→自检两遍→提交/部署",
             "tool": "git commit + push", "verify": "所有验收标准满足，零已知问题", "time": 5},
        ],
    }
    
    # 阶段名→通用步骤模板 映射
    PHASE_MAP = {
        "需求分析": "理解任务",   "方案设计": "理解任务",
        "环境准备": "准备资源",   "编码实现": "执行核心",
        "测试验证": "验证结果",   "优化重构": "执行核心",
        "文档交付": "整理交付",   "需求调研": "理解任务",
        "概念设计": "理解任务",   "详细设计": "理解任务",
        "原型验证": "验证结果",   "设计交付": "整理交付",
        "环境检查": "准备资源",   "备份":     "准备资源",
        "部署执行": "执行核心",   "健康检查": "验证结果",
        "监控配置": "整理交付",   "回滚预案": "整理交付",
        "问题定义": "理解任务",   "资料收集": "准备资源",
        "分析对比": "执行核心",   "实验验证": "验证结果",
        "结论输出": "整理交付",
    }
    
    phases = []
    total_time = 0
    step_counter = [0]
    
    for phase_name in template["phases"]:
        mapped = PHASE_MAP.get(phase_name, phase_name)
        if mapped not in step_templates:
            continue
        
        steps = []
        phase_time = 0
        
        for i, tmpl in enumerate(step_templates[mapped]):
            step_counter[0] += 1
            sid = f"{len(phases)+1}.{i+1}"
            t = tmpl["time"]
            phase_time += t
            
            sub_steps = []
            for j in range(3):
                micro_actions = [
                    (f"准备: 确认{tmpl['tool']}就绪", f"打开终端/编辑器, 检查{tmpl['tool']}可用", 1),
                    (f"执行: {tmpl['action'][:20]}", f"按照how字段的指示操作: {tmpl['how'][:80]}", max(1, t//2)),
                    (f"确认: 验证结果", f"按照verify标准检查: {tmpl['verify'][:80]}", 1),
                ]
                sub_steps.append({
                    "micro_id": f"{sid}.{j+1}",
                    "micro_action": micro_actions[j][0],
                    "micro_how": micro_actions[j][1],
                    "micro_time": micro_actions[j][2]
                })
            
            steps.append({
                "step_id": sid,
                "action": tmpl["action"],
                "how": tmpl["how"],
                "tool": tmpl["tool"],
                "expected_output": f"验证通过: {tmpl['verify']}",
                "verify": tmpl["verify"],
                "estimated_minutes": t,
                "depends_on": [f"{len(phases)+1}.{i}"] if i > 0 else [],
                "sub_steps": sub_steps
            })
        
        phases.append({
            "phase": phase_name,
            "objective": f"完成{phase_name}阶段的所有任务",
            "estimated_minutes": phase_time,
            "steps": steps
        })
        total_time += phase_time
    
    return {
        "ok": True,
        "task": desc[:100],
        "type": task_type,
        "total_estimated_minutes": total_time,
        "phases": phases,
        "critical_path": [s["step_id"] for p in phases for s in p["steps"]],
        "risk_points": [
            {"step": "2.1", "risk": "依赖不可用导致阻塞", "mitigation": "提前检查并准备替代方案"},
            {"step": "3.1", "risk": "执行出错导致返工", "mitigation": "小步快跑，每步即时验证"},
        ],
        "mode": "rule_based"
    }

# ═══════════════════════════════════════════════════════════
#  可视化生成器
# ═══════════════════════════════════════════════════════════

def generate_mindmap(plan: dict) -> str:
    """从规划JSON生成Mermaid mindmap"""
    lines = ["mindmap"]
    lines.append(f"  root(({plan.get('task', '任务')}))")
    
    for phase in plan.get("phases", []):
        pname = phase["phase"]
        ptime = phase["estimated_minutes"]
        lines.append(f"    {pname}[{pname} ⏱{ptime}min]")
        
        for step in phase.get("steps", []):
            sid = step["step_id"]
            action = step["action"][:25]
            stime = step["estimated_minutes"]
            lines.append(f"      {sid}[{sid}: {action} ⏱{stime}min]")
            
            for sub in step.get("sub_steps", []):
                mid = sub["micro_id"]
                maction = sub["micro_action"][:20]
                mtime = sub["micro_time"]
                lines.append(f"        {mid}[{maction} ⏱{mtime}min]")
    
    return "\n".join(lines)


def generate_flowchart(plan: dict) -> str:
    """从规划JSON生成Mermaid flowchart(决策分支)"""
    lines = ["flowchart TD"]
    lines.append(f"  START([开始: {plan.get('task', '任务')[:40]}])")
    
    prev_node = "START"
    
    for pi, phase in enumerate(plan.get("phases", [])):
        pname = phase["phase"]
        pnode = f"P{pi+1}"
        lines.append(f"  {prev_node} --> {pnode}{{{{{pname} ⏱{phase['estimated_minutes']}min}}}}")
        
        prev_step = pnode
        steps = phase.get("steps", [])
        for si, step in enumerate(steps):
            sid = step["step_id"].replace(".", "_")
            snode = f"S{sid}"
            lines.append(f"  {prev_step} --> {snode}[{step['step_id']}: {step['action'][:20]}]")
            
            # 验证分支
            vnode = f"V{sid}"
            lines.append(f"  {snode} --> {vnode}{{{{验证: {step['verify'][:30]}?}}}}")
            lines.append(f"  {vnode} -->|✅ 通过| NEXT{sid}")
            
            if si < len(steps) - 1:
                nsid = steps[si+1]["step_id"].replace(".", "_")
                lines.append(f"  NEXT{sid} --> S{nsid}")
            else:
                lines.append(f"  NEXT{sid} --> NEXT_P{pi+1}")
            
            lines.append(f"  {vnode} -->|❌ 失败| FIX{sid}[分析根因+修正]")
            lines.append(f"  FIX{sid} --> {snode}")
            prev_step = f"NEXT{sid}"
        
        if pi < len(plan.get("phases", [])) - 1:
            lines.append(f"  NEXT_P{pi+1} --> P{pi+2}")
        else:
            lines.append(f"  NEXT_P{pi+1} --> DONE([✅ 交付完成])")
    
    return "\n".join(lines)


def generate_checklist(plan: dict) -> str:
    """生成Markdown可勾选清单"""
    lines = [f"# 📋 执行检查清单: {plan.get('task', '')}", ""]
    lines.append(f"> 预估总时间: **{plan.get('total_estimated_minutes', 0)}分钟**", "")
    
    for phase in plan.get("phases", []):
        lines.append(f"## {phase['phase']} ⏱ {phase['estimated_minutes']}min")
        lines.append(f"> {phase.get('objective', '')}", "")
        
        for step in phase.get("steps", []):
            lines.append(f"- [ ] **{step['step_id']}** {step['action']} `⏱{step['estimated_minutes']}min`")
            lines.append(f"  - 🔧 工具: {step['tool']}")
            lines.append(f"  - 📝 方法: {step['how'][:120]}")
            lines.append(f"  - ✅ 验证: {step['verify'][:100]}")
            
            for sub in step.get("sub_steps", []):
                lines.append(f"    - [ ] {sub['micro_id']} {sub['micro_action']} `⏱{sub['micro_time']}min`")
            lines.append("")
    
    return "\n".join(lines)


def generate_ascii_tree(plan: dict) -> str:
    """生成ASCII树形图"""
    lines = [f"📋 {plan.get('task', '任务')}", f"⏱ 总预估: {plan.get('total_estimated_minutes', 0)}分钟", ""]
    
    phases = plan.get("phases", [])
    for pi, phase in enumerate(phases):
        is_last_phase = pi == len(phases) - 1
        prefix = "└── " if is_last_phase else "├── "
        lines.append(f"{prefix}📁 {phase['phase']} [{phase['estimated_minutes']}min]")
        
        step_prefix_base = "    " if is_last_phase else "│   "
        steps = phase.get("steps", [])
        
        for si, step in enumerate(steps):
            is_last_step = si == len(steps) - 1
            sp = step_prefix_base + ("└── " if is_last_step else "├── ")
            lines.append(f"{sp}📌 {step['step_id']} {step['action']} [{step['estimated_minutes']}min]")
            lines.append(f"{sp}   🔧 {step['tool']}")
            lines.append(f"{sp}   ✅ {step['verify'][:60]}")
            
            sub_prefix = step_prefix_base + ("    " if is_last_step else "│   ")
            subs = step.get("sub_steps", [])
            for ji, sub in enumerate(subs):
                is_last_sub = ji == len(subs) - 1
                sup = sub_prefix + ("└── " if is_last_sub else "├── ")
                lines.append(f"{sup}⏱ {sub['micro_id']} {sub['micro_action']} [{sub['micro_time']}min]")
    
    return "\n".join(lines)


def generate_gantt(plan: dict) -> str:
    """生成Mermaid甘特图"""
    lines = ["gantt"]
    lines.append(f"    title {plan.get('task', '任务')[:50]}")
    lines.append("    dateFormat HH:mm")
    lines.append("    axisFormat %H:%M")
    lines.append("    section 准备")
    
    cum_time = 0
    for phase in plan.get("phases", []):
        pname = phase["phase"]
        lines.append(f"    section {pname}")
        
        for step in phase.get("steps", []):
            t = step["estimated_minutes"]
            start = cum_time
            end = cum_time + t
            
            sh = start // 60
            sm = start % 60
            eh = end // 60
            em = end % 60
            
            start_str = f"{sh:02d}:{sm:02d}"
            end_str = f"{eh:02d}:{em:02d}"
            
            lines.append(f"    {step['step_id']} {step['action'][:20]} :{start_str} {end_str}")
            cum_time += t
    
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════
#  动作处理
# ═══════════════════════════════════════════════════════════

def do_plan(params: dict) -> dict:
    desc = params.get("task", params.get("description", params.get("prompt", "")))
    task_type = params.get("type", "general")
    depth = params.get("depth", 4)
    lang = params.get("language", "zh")
    return decompose_task(desc, task_type, depth, lang)


def do_mindmap(params: dict) -> dict:
    plan = do_plan(params)
    if not plan.get("ok"):
        return plan
    return {"ok": True, "action": "mindmap", "mermaid": generate_mindmap(plan),
            "type": "mermaid", "plan": plan}


def do_flowchart(params: dict) -> dict:
    plan = do_plan(params)
    if not plan.get("ok"):
        return plan
    return {"ok": True, "action": "flowchart", "mermaid": generate_flowchart(plan),
            "type": "mermaid", "plan": plan}


def do_checklist(params: dict) -> dict:
    plan = do_plan(params)
    if not plan.get("ok"):
        return plan
    return {"ok": True, "action": "checklist", "markdown": generate_checklist(plan),
            "type": "markdown", "plan": plan}


def do_ascii_tree(params: dict) -> dict:
    plan = do_plan(params)
    if not plan.get("ok"):
        return plan
    return {"ok": True, "action": "ascii_tree", "tree": generate_ascii_tree(plan),
            "type": "text", "plan": plan}


def do_gantt(params: dict) -> dict:
    plan = do_plan(params)
    if not plan.get("ok"):
        return plan
    return {"ok": True, "action": "gantt", "mermaid": generate_gantt(plan),
            "type": "mermaid", "plan": plan}

def do_langgraph_export(params: dict) -> dict:
    """将任务规划导出为LangGraph StateGraph Python代码 (纯规则模式,不需LLM)"""
    # 强制跳过LLM, 直接使用规则引擎分解 — 导出功能不应依赖API
    # 函数在本文件内, 直接调用
    task_type = params.get("task_type", "general")
    desc = params.get("task", params.get("description", params.get("prompt", "")))
    lang = params.get("language", params.get("lang", "zh"))
    plan = _rule_decompose(desc, task_type, 4, lang)
    
    code = []
    code.append('from typing import TypedDict, Annotated')
    code.append('from langgraph.graph import StateGraph, END')
    code.append('')
    code.append('class AgentState(TypedDict):')
    code.append('    task: str')
    code.append('    current_phase: str')
    code.append('    results: dict')
    for i, phase in enumerate(plan.get('phases', [])):
        pname = phase['phase'].replace(' ', '_')
        code.append(f'def node_{pname}(state: AgentState):')
        code.append(f'    """{phase["objective"]}"""')
        for step in phase.get('steps', []):
            code.append(f'    # {step["step_id"]}: {step["action"]}')
            code.append(f'    # tool: {step["tool"]}')
        code.append(f'    return {{"current_phase": "{pname}"}}')
    code.append('')
    code.append('graph = StateGraph(AgentState)')
    for i, phase in enumerate(plan.get('phases', [])):
        pname = phase['phase'].replace(' ', '_')
        code.append(f'graph.add_node("{pname}", node_{pname})')
    code.append('graph.set_entry_point("{}")'.format(plan['phases'][0]['phase'].replace(' ', '_')))
    for i in range(len(plan['phases']) - 1):
        src = plan['phases'][i]['phase'].replace(' ', '_')
        dst = plan['phases'][i + 1]['phase'].replace(' ', '_')
        code.append(f'graph.add_edge("{src}", "{dst}")')
    code.append(f'graph.add_edge("{plan["phases"][-1]["phase"].replace(" ", "_")}", END)')
    code.append('app = graph.compile()')
    return {'ok': True, 'action': 'langgraph_export', 'code': '\n'.join(code), 'plan': plan}


def do_decompose_auto(params: dict) -> dict:
    """将高层目标分解为auto_pipeline可执行的步骤计划
    输出: {pipeline_name, steps: [{cap, action, params, timeout, retry}]}
    桥接 task_mind「思考」→ auto_pipeline「执行」
    """
    goal = params.get("goal", params.get("task", params.get("description", params.get("prompt", ""))))
    if not goal:
        return {"ok": False, "error": "缺少 goal 参数"}

    lang = params.get("language", "zh")
    pipeline_name = params.get("name", f"auto_{int(time.time())}")

    system = (
        "你是GBT自主系统的任务编排专家。将高层目标分解为auto_pipeline可执行的分钟级步骤。\n"
        "可用能力模块(cap)及动作:\n"
        "- devourer: scan/devour/daily/digest/status\n"
        "- self_evolve: evolve/learn/insights/metrics/capture\n"
        "- health_dashboard: check/quick/caps/live_check\n"
        "- web_search: search\n"
        "- code_exec: run\n"
        "- file_operation: read/write/list/copy/move/delete\n"
        "- git_ops: pull/commit/push/status\n"
        "- project_state: snapshot/compare\n"
        "- auto_fix: fix/analyze\n"
        "- task_mind: plan/mindmap\n"
        "- report_generator: generate\n"
        "- nexus_monitor: scan\n"
        "- auto_pipeline: auto_chain\n"
        "输出严格JSON，无markdown包裹，无注释:\n"
        '{"pipeline_name": "str", "steps": [\n'
        '  {"cap": "模块id", "action": "动作", "params": {}, "timeout": 秒数, "retry": 重试次数}\n'
        "]}\n"
        "规则: 步骤≤8个; timeout默认60; retry默认2; params可为空{}; 步骤间有逻辑依赖(先分析后执行)"
    )

    user = f"目标: {goal}\n语言: {lang}\n流水线名: {pipeline_name}"

    llm_result = _call_llm(system, user, temp=0.2, max_tok=2000)
    if not llm_result.get("ok"):
        # LLM不可用时回退到规则模式
        return _rule_decompose_auto(goal, pipeline_name)

    raw = llm_result["content"].strip()
    # 清洗可能的markdown包裹
    for marker in ("```json", "```"):
        if raw.startswith(marker):
            raw = raw[len(marker):].strip()
        if raw.endswith(marker):
            raw = raw[:-len(marker)].strip()

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": False, "error": "LLM输出非有效JSON", "raw": raw[:500]}

    if "steps" not in plan:
        return {"ok": False, "error": "输出缺少 steps 字段", "raw": raw[:500]}

    return {"ok": True, "action": "decompose_auto",
            "pipeline_name": plan.get("pipeline_name", pipeline_name),
            "steps": plan["steps"], "source": "llm"}


def _rule_decompose_auto(goal: str, pipeline_name: str) -> dict:
    """规则回退: 关键词驱动的自动流水线分解 (不依赖LLM)"""
    gl = goal.lower()
    steps = []

    # 通用模式: 搜索→学习→执行→检查→报告
    if any(kw in gl for kw in ("搜索", "调研", "search", "research", "信息")):
        steps.append({"cap": "web_search", "action": "search", "params": {"query": goal}, "timeout": 60, "retry": 2})
    if any(kw in gl for kw in ("代码", "code", "编程", "开发", "实现", "修复", "fix", "bug")):
        steps.append({"cap": "auto_fix", "action": "analyze", "params": {"task": goal}, "timeout": 120, "retry": 2})
    if any(kw in gl for kw in ("学习", "进化", "evolve", "learn", "优化")):
        steps.append({"cap": "self_evolve", "action": "evolve", "params": {"lesson": goal}, "timeout": 60, "retry": 2})
    if any(kw in gl for kw in ("检查", "健康", "health", "诊断", "状态")):
        steps.append({"cap": "health_dashboard", "action": "check", "params": {}, "timeout": 60, "retry": 1})
    if any(kw in gl for kw in ("吞噬", "devour", "扫描", "热度")):
        steps.append({"cap": "devourer", "action": "devour", "params": {}, "timeout": 300, "retry": 1})
    if any(kw in gl for kw in ("报告", "report", "总结", "生成")):
        steps.append({"cap": "report_generator", "action": "generate", "params": {"topic": goal}, "timeout": 60, "retry": 2})
    if any(kw in gl for kw in ("git", "提交", "commit", "推送", "push")):
        steps.append({"cap": "git_ops", "action": "status", "params": {}, "timeout": 30, "retry": 1})

    if not steps:
        # 兜底: 通用两阶段 — 搜索+报告
        steps = [
            {"cap": "web_search", "action": "search", "params": {"query": goal}, "timeout": 60, "retry": 2},
            {"cap": "report_generator", "action": "generate", "params": {"topic": goal}, "timeout": 60, "retry": 2},
        ]

    return {"ok": True, "action": "decompose_auto",
            "pipeline_name": pipeline_name, "steps": steps, "source": "rule"}


# ═══════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════
HANDLERS = {
    "plan": do_plan, "mindmap": do_mindmap, "flowchart": do_flowchart,
    "checklist": do_checklist, "ascii_tree": do_ascii_tree, "gantt": do_gantt,
    "langgraph_export": do_langgraph_export,
    "decompose_auto": do_decompose_auto,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "mindmap"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            params = {"task": sys.argv[2]}
    
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知: {action}"}
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
