# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""email_engine/run.py — AI邮件引擎 · SMTP+IMAP+AI分类
========================================================
邮件发送(SMTP) · 邮件读取(IMAP) · AI智能分类 · 附件处理
"""
import sys, json, os, email, smtplib, imaplib, re
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

SANDBOX = Path(__file__).parent.parent

def _get_smtp_config(params):
    configs = {
        "gmail": {"host": "smtp.gmail.com", "port": 587, "tls": True},
        "outlook": {"host": "smtp.office365.com", "port": 587, "tls": True},
        "qq": {"host": "smtp.qq.com", "port": 587, "tls": True},
        "163": {"host": "smtp.163.com", "port": 465, "tls": False, "ssl": True},
        "custom": {"host": params.get("smtp_host", ""), "port": params.get("smtp_port", 587),
                   "tls": params.get("smtp_tls", True)}
    }
    provider = params.get("provider", "gmail").lower()
    return configs.get(provider, configs["custom"])

def _get_imap_config(params):
    configs = {
        "gmail": {"host": "imap.gmail.com", "port": 993, "ssl": True},
        "outlook": {"host": "outlook.office365.com", "port": 993, "ssl": True},
        "qq": {"host": "imap.qq.com", "port": 993, "ssl": True},
        "163": {"host": "imap.163.com", "port": 993, "ssl": True},
    }
    return configs.get(params.get("provider", "gmail").lower(),
                       {"host": params.get("imap_host", ""), "port": 993, "ssl": True})

def do_send(params):
    """发送邮件"""
    to = params.get("to", "")
    subject = params.get("subject", "No Subject")
    body = params.get("body", params.get("text", ""))
    html = params.get("html", "")
    attachments = params.get("attachments", [])
    user = params.get("user", os.environ.get("EMAIL_USER", ""))
    password = params.get("password", os.environ.get("EMAIL_PASS", ""))
    
    if not to or not user or not password:
        return {"ok": False, "error": "缺少to/user/password参数"}
    
    cfg = _get_smtp_config(params)
    if not cfg["host"]:
        return {"ok": False, "error": "无法确定SMTP服务器"}
    
    try:
        msg = MIMEMultipart() if html or attachments else MIMEText(body, "plain", "utf-8")
        if html or attachments:
            msg["Subject"] = subject
            msg["From"] = user
            msg["To"] = to
            msg.attach(MIMEText(body, "plain", "utf-8"))
            if html:
                msg.attach(MIMEText(html, "html", "utf-8"))
            for att in attachments:
                fp = att if isinstance(att, str) else att.get("path", "")
                if fp and Path(fp).exists():
                    with open(fp, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f'attachment; filename="{Path(fp).name}"')
                        msg.attach(part)
        else:
            msg["Subject"] = subject
            msg["From"] = user
            msg["To"] = to
        
        if cfg.get("ssl"):
            smtp = smtplib.SMTP_SSL(cfg["host"], cfg["port"])
        else:
            smtp = smtplib.SMTP(cfg["host"], cfg["port"])
        if cfg.get("tls"):
            smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
        smtp.quit()
        return {"ok": True, "cap": "email_engine", "action": "send", "to": to, "subject": subject, "sent": True}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_read(params):
    """读取邮件 (IMAP)"""
    user = params.get("user", os.environ.get("EMAIL_USER", ""))
    password = params.get("password", os.environ.get("EMAIL_PASS", ""))
    limit = params.get("limit", 10)
    folder = params.get("folder", "INBOX")
    
    if not user or not password:
        return {"ok": False, "error": "缺少user/password"}
    
    cfg = _get_imap_config(params)
    try:
        if cfg.get("ssl"):
            imap = imaplib.IMAP4_SSL(cfg["host"], cfg["port"])
        else:
            imap = imaplib.IMAP4(cfg["host"], cfg["port"])
        imap.login(user, password)
        imap.select(folder)
        
        _, msg_nums = imap.search(None, "ALL")
        nums = msg_nums[0].split()[-limit:] if msg_nums[0] else []
        
        emails = []
        for num in reversed(nums):
            _, data = imap.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            emails.append({
                "from": msg.get("From", ""),
                "subject": msg.get("Subject", ""),
                "date": msg.get("Date", ""),
                "body_preview": _extract_body(msg)[:500],
            })
        
        imap.logout()
        return {"ok": True, "cap": "email_engine", "action": "read", "folder": folder, "count": len(emails), "emails": emails}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def _extract_body(msg):
    """从邮件中提取正文"""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(errors="replace")
                except:
                    pass
    else:
        try:
            return msg.get_payload(decode=True).decode(errors="replace")
        except:
            pass
    return ""

def do_classify(params):
    """AI邮件分类 — 关键词+规则引擎"""
    emails = params.get("emails", [])
    if not emails and params.get("read_first"):
        r = do_read(params)
        if r["ok"]:
            emails = r.get("emails", [])
    
    categories = {
        "urgent": ["紧急", "urgent", "asap", "立即", "deadline", "!!!", "重要"],
        "meeting": ["会议", "meeting", "invite", "calendar", "zoom", "teams", "schedule"],
        "newsletter": ["newsletter", "subscribe", "unsubscribe", "digest", "update", "weekly"],
        "invoice": ["invoice", "receipt", "payment", "bill", "billing", "订单", "receipt"],
        "spam": ["win", "prize", "lottery", "free money", "click here", "viagra", "casino"],
        "social": ["linkedin", "facebook", "twitter", "instagram", "mention", "follow"],
    }
    
    results = []
    for em in emails:
        text = f"{em.get('subject','')} {em.get('body_preview','')}".lower()
        matched = []
        for cat, keywords in categories.items():
            if any(kw.lower() in text for kw in keywords):
                matched.append(cat)
        em["categories"] = matched or ["general"]
        results.append(em)
    
    stats = {}
    for r in results:
        for c in r["categories"]:
            stats[c] = stats.get(c, 0) + 1
    
    return {"ok": True, "cap": "email_engine", "action": "classify",
            "total": len(results), "categories": stats, "emails": results}

def do_auto_reply(params):
    """基于分类自动回复"""
    emails = params.get("emails", [])
    rules = params.get("rules", {
        "urgent": "已收到您的紧急邮件，我会尽快处理。",
        "meeting": "会议邀请已收到，我会按时参加。",
        "invoice": "发票/账单已收到，正在处理中。",
    })
    user = params.get("user", os.environ.get("EMAIL_USER", ""))
    password = params.get("password", os.environ.get("EMAIL_PASS", ""))
    
    if not emails:
        return {"ok": False, "error": "缺少emails参数"}
    
    classified = do_classify({"emails": emails})
    replied = []
    for em in classified.get("emails", []):
        for cat in em.get("categories", []):
            if cat in rules and user and password:
                reply_to = re.search(r'<(.+?)>', em.get("from", ""))
                to = reply_to.group(1) if reply_to else em.get("from", "")
                r = do_send({"to": to, "subject": f"Re: {em.get('subject','')}", "body": rules[cat],
                            "user": user, "password": password, "provider": params.get("provider","gmail")})
                replied.append({"to": to, "category": cat, "sent": r.get("ok", False)})
    
    return {"ok": True, "replied": len(replied), "replies": replied}

HANDLERS = {
    "send": do_send, "read": do_read, "classify": do_classify,
    "auto_reply": do_auto_reply, "run": do_send,
}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "read"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
