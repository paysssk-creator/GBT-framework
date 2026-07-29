# 开发者：自由的风
"""social_engineer/run.py — 社会工程学工具包"""
import sys, json, os, random
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TACTICS = {
    "pretext": {
        "roles": ["IT支持", "HR部门", "快递员", "客户经理", "安全审计员", "系统管理员", "实习生", "高管助理"],
        "scenarios": ["密码重置", "紧急安全更新", "包裹签收确认", "账号验证", "系统维护通知"],
    },
    "baiting": {
        "physical": ["标记'机密'的U盘", "免费WiFi热点", "充电宝", "蓝牙设备"],
        "digital": ["破解软件下载", "免费课程链接", "抽奖页面", "限时优惠券"],
    },
    "phishing_variants": ["标准钓鱼", "鱼叉式钓鱼(定向)", "鲸钓(高管定向)", "短信钓鱼(SMS)", "语音钓鱼(Vishing)", "二维码钓鱼"],
}

EMAIL_TEMPLATES = {
    "password_reset": {
        "subject": "【紧急】您的账号密码需要立即重置",
        "body": """尊敬的{name}：

系统检测到您的账号存在异常登录活动。为保护您的账户安全，请在24小时内完成密码重置。

重置链接: {link}

如未及时处理，您的账号将被暂时锁定。

此致
{company} 安全团队""",
    },
    "urgent_update": {
        "subject": "【重要】系统安全更新通知",
        "body": """您好 {name}：

我们即将进行关键安全更新。为确保持续访问，请立即验证您的账户信息。

验证链接: {link}

这是强制性更新，所有用户必须在48小时内完成验证。

{company} IT部门""",
    },
}

def do_generate(params):
    tactic = params.get("tactic", "pretext")
    target_name = params.get("name", "用户")
    company = params.get("company", "ACME Corp")
    link = params.get("link", "https://example.com/verify")

    if tactic == "pretext":
        role = random.choice(TACTICS["pretext"]["roles"])
        scenario = random.choice(TACTICS["pretext"]["scenarios"])
        script = "【社交工程剧本】\n角色: {}\n场景: {}\n目标: {}\n公司: {}\n\n".format(role, scenario, target_name, company)
        script += "开场白: '您好{}，我是{}的{}。{}需要您配合一下。'\n".format(target_name, company, role, scenario)
        script += "信任构建: '您的工号后四位是****对吗? 我们需要确认一下您的身份。'\n"
        script += "行动引导: '请点击以下链接完成验证: {}'\n".format(link)
        script += "紧迫感: '这是紧急事项，请尽快处理。'\n"
        return {"ok": True, "cap": "social_engineer", "action": "generate", "domain": "攻击域",
                "tactic": tactic, "role": role, "scenario": scenario, "script": script}

    elif tactic == "email":
        template = params.get("template", "password_reset")
        tmpl = EMAIL_TEMPLATES.get(template, EMAIL_TEMPLATES["password_reset"])
        subject = tmpl["subject"]
        body = tmpl["body"].format(name=target_name, company=company, link=link)
        return {"ok": True, "cap": "social_engineer", "action": "generate",
                "template": template, "subject": subject, "body": body, "to": target_name}

    elif tactic == "baiting":
        btype = params.get("bait_type", "digital")
        baits = TACTICS["baiting"][btype]
        bait = random.choice(baits)
        return {"ok": True, "cap": "social_engineer", "action": "generate",
                "tactic": tactic, "bait_type": btype, "bait": bait, "all_baits": baits}

    return {"ok": True, "tactic": tactic, "available": list(TACTICS.keys()) + ["email"]}

def do_tactics(params):
    return {"ok": True, "tactics": TACTICS, "email_templates": list(EMAIL_TEMPLATES.keys()),
            "phishing_variants": TACTICS["phishing_variants"]}

HANDLERS = {"generate": do_generate, "tactics": do_tactics}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "tactics"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))
