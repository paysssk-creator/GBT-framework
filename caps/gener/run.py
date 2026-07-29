# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""gener/run.py — 内容生成工具集：二维码文件/名片/HTML表单/Sitemap/robots.txt"""
import sys, json, os, base64, io
from pathlib import Path
from datetime import datetime
from xml.etree import ElementTree as ET

_sandbox = Path(__file__).parent.parent.parent


def _resolve(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (_sandbox / p).resolve()


def _ok(**kwargs) -> dict:
    return {"ok": True, **kwargs}


def _err(msg: str) -> dict:
    return {"ok": False, "error": msg}


# ═══════════════════════════════════════════════════════
# 1. qrcode_file — 生成二维码 PNG 文件
# ═══════════════════════════════════════════════════════
def do_qrcode_file(params: dict) -> dict:
    text = params.get("text", "")
    if not text:
        return _err("缺少 text 参数")
    output = _resolve(params.get("output", "qrcode.png"))
    box_size = params.get("box_size", 10)
    border = params.get("border", 4)
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=params.get("version") or None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        output.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output), format="PNG")
        return _ok(path=str(output), size=output.stat().st_size, text=text)
    except ImportError:
        return _err("缺少 qrcode 库，请执行: pip install qrcode[pil] pillow")
    except Exception as e:
        return _err(f"二维码生成失败: {e}")


# ═══════════════════════════════════════════════════════
# 2. vcard — 生成 vCard 名片 (.vcf)
# ═══════════════════════════════════════════════════════
def do_vcard(params: dict) -> dict:
    name = params.get("name", "")
    if not name:
        return _err("缺少 name 参数")
    output = _resolve(params.get("output", f"{name}.vcf"))

    lines = ["BEGIN:VCARD", "VERSION:3.0"]
    # 姓名
    lines.append(f"N:{params.get('last_name', name)};{params.get('first_name', '')};;;")
    lines.append(f"FN:{name}")
    # 组织
    org = params.get("org", "")
    if org:
        lines.append(f"ORG:{org}")
    title = params.get("title", "")
    if title:
        lines.append(f"TITLE:{title}")
    # 电话
    phone = params.get("phone", "")
    if phone:
        lines.append(f"TEL;TYPE=CELL:{phone}")
    work_phone = params.get("work_phone", "")
    if work_phone:
        lines.append(f"TEL;TYPE=WORK:{work_phone}")
    home_phone = params.get("home_phone", "")
    if home_phone:
        lines.append(f"TEL;TYPE=HOME:{home_phone}")
    # 邮箱
    email = params.get("email", "")
    if email:
        lines.append(f"EMAIL:{email}")
    # 网站
    url = params.get("url", "")
    if url:
        lines.append(f"URL:{url}")
    # 地址
    addr = params.get("address", "")
    if addr:
        lines.append(f"ADR;TYPE=WORK:;;{addr};;;;")
    # 备注
    note = params.get("note", "")
    if note:
        lines.append(f"NOTE:{note}")
    # 生日
    birthday = params.get("birthday", "")
    if birthday:
        lines.append(f"BDAY:{birthday}")
    # 头像（可内嵌 base64）
    photo_b64 = params.get("photo_base64", "")
    if photo_b64:
        lines.append("PHOTO;ENCODING=BASE64;TYPE=JPEG:")
        for i in range(0, len(photo_b64), 75):
            lines.append(f" {photo_b64[i:i+75]}")
    lines.append("END:VCARD")

    content = "\r\n".join(lines) + "\r\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return _ok(path=str(output), size=output.stat().st_size, name=name)


# ═══════════════════════════════════════════════════════
# 3. form_html — 生成 HTML 表单
# ═══════════════════════════════════════════════════════
def do_form_html(params: dict) -> dict:
    fields = params.get("fields", [])
    if not fields:
        return _err("缺少 fields 参数")
    output = _resolve(params.get("output", "form.html"))
    title = params.get("title", "表单")
    action = params.get("action", "#")
    method = params.get("method", "POST")
    css = params.get("css", "")

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>{_esc(title)}</title>",
    ]
    if css:
        html_parts.append(f"<style>{css}</style>")
    else:
        html_parts.append(
            "<style>\n"
            "  body { font-family: -apple-system, sans-serif; max-width: 600px; margin: 2em auto; padding: 0 1em; }\n"
            "  label { display: block; margin: 0.8em 0 0.3em; font-weight: 600; }\n"
            "  input, select, textarea { width: 100%; padding: 0.5em; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }\n"
            "  button { margin-top: 1.2em; padding: 0.6em 1.5em; background: #007bff; color: #fff; border: none; border-radius: 4px; cursor: pointer; }\n"
            "  button:hover { background: #0056b3; }\n"
            "  .field-hint { font-size: 0.85em; color: #666; margin-top: 0.15em; }\n"
            "</style>"
        )
    html_parts.extend(["</head>", "<body>", f"<h1>{_esc(title)}</h1>", f'<form action="{_esc(action)}" method="{_esc(method)}">'])

    for f in fields:
        ftype = f.get("type", "text")
        fname = f.get("name", "")
        flabel = f.get("label", fname)
        fplaceholder = f.get("placeholder", "")
        frequired = f.get("required", False)
        fhint = f.get("hint", "")
        fvalue = f.get("value", "")
        fid = f"field_{fname}" if fname else ""

        attr_id = f' id="{_esc(fid)}"' if fid else ""
        attr_req = " required" if frequired else ""
        attr_placeholder = f' placeholder="{_esc(fplaceholder)}"' if fplaceholder else ""

        html_parts.append(f'<label for="{_esc(fid)}">{_esc(flabel)}</label>' if fid else f"<label>{_esc(flabel)}</label>")

        if ftype == "textarea":
            html_parts.append(f'<textarea name="{_esc(fname)}"{attr_id}{attr_req} rows="4"{attr_placeholder}>{_esc(fvalue)}</textarea>')
        elif ftype == "select":
            opts = f.get("options", [])
            html_parts.append(f'<select name="{_esc(fname)}"{attr_id}{attr_req}>')
            for opt in opts:
                opt_val = opt.get("value", "") if isinstance(opt, dict) else opt
                opt_label = opt.get("label", opt_val) if isinstance(opt, dict) else opt
                selected = ' selected' if fvalue == opt_val else ""
                html_parts.append(f'<option value="{_esc(opt_val)}"{selected}>{_esc(opt_label)}</option>')
            html_parts.append("</select>")
        elif ftype == "checkbox":
            html_parts.append(
                f'<input type="checkbox" name="{_esc(fname)}"{attr_id}{attr_req} value="{_esc(fvalue)}">'
            )
        elif ftype == "radio":
            opts = f.get("options", [])
            for opt in opts:
                opt_val = opt.get("value", "") if isinstance(opt, dict) else opt
                opt_label = opt.get("label", opt_val) if isinstance(opt, dict) else opt
                checked = ' checked' if fvalue == opt_val else ""
                html_parts.append(
                    f'<label style="font-weight:normal"><input type="radio" name="{_esc(fname)}"'
                    f' value="{_esc(opt_val)}"{checked}> {_esc(opt_label)}</label>'
                )
            # skip hint for radio - labels are self-explanatory
            if fhint:
                html_parts.append(f'<div class="field-hint">{_esc(fhint)}</div>')
            continue
        elif ftype == "file":
            html_parts.append(f'<input type="file" name="{_esc(fname)}"{attr_id}{attr_req}>')
        else:
            html_parts.append(
                f'<input type="{_esc(ftype)}" name="{_esc(fname)}"{attr_id}{attr_req}{attr_placeholder}'
                f' value="{_esc(fvalue)}">'
            )

        if fhint:
            html_parts.append(f'<div class="field-hint">{_esc(fhint)}</div>')

    submit_label = params.get("submit_label", "提交")
    html_parts.append(f"<button type=\"submit\">{_esc(submit_label)}</button>")
    html_parts.extend(["</form>", "</body>", "</html>"])

    content = "\n".join(html_parts) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return _ok(path=str(output), size=output.stat().st_size, field_count=len(fields))


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ═══════════════════════════════════════════════════════
# 4. sitemap — 生成 sitemap.xml
# ═══════════════════════════════════════════════════════
def do_sitemap(params: dict) -> dict:
    urls = params.get("urls", [])
    if not urls:
        return _err("缺少 urls 参数")

    output = _resolve(params.get("output", "sitemap.xml"))

    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for item in urls:
        if isinstance(item, str):
            loc, changefreq, priority, lastmod = item, "", "", ""
        else:
            loc = item.get("loc", "")
            changefreq = item.get("changefreq", "")
            priority = item.get("priority", "")
            lastmod = item.get("lastmod", "")
        url_el = ET.SubElement(urlset, "url")
        ET.SubElement(url_el, "loc").text = loc
        if lastmod:
            ET.SubElement(url_el, "lastmod").text = lastmod
        if changefreq:
            ET.SubElement(url_el, "changefreq").text = changefreq
        if priority:
            ET.SubElement(url_el, "priority").text = str(priority)

    # pretty-print
    ET.indent(urlset, space="  ")
    xml_str = ET.tostring(urlset, encoding="unicode", xml_declaration=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(xml_str, encoding="utf-8")
    return _ok(path=str(output), size=output.stat().st_size, url_count=len(urls))


# ═══════════════════════════════════════════════════════
# 5. robots — 生成 robots.txt
# ═══════════════════════════════════════════════════════
def do_robots(params: dict) -> dict:
    user_agents = params.get("user_agents", ["*"])
    allow = params.get("allow", [])
    disallow = params.get("disallow", ["/"])
    sitemap_url = params.get("sitemap", "")
    crawl_delay = params.get("crawl_delay", "")
    output = _resolve(params.get("output", "robots.txt"))

    lines = []
    for ua in user_agents:
        lines.append(f"User-agent: {ua}")
        for a in allow:
            lines.append(f"Allow: {a}")
        for d in disallow:
            lines.append(f"Disallow: {d}")
        if crawl_delay:
            lines.append(f"Crawl-delay: {crawl_delay}")
        lines.append("")

    if sitemap_url:
        lines.append(f"Sitemap: {sitemap_url}")

    content = "\n".join(lines) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return _ok(path=str(output), size=output.stat().st_size)


# ═══════════════════════════════════════════════════════
# Handler 注册
# ═══════════════════════════════════════════════════════
handlers = {
    "qrcode_file": do_qrcode_file,
    "vcard":       do_vcard,
    "form_html":   do_form_html,
    "sitemap":     do_sitemap,
    "robots":      do_robots,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ""
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = handlers.get(action)
    if handler:
        result = handler(params)
    else:
        result = {
            "ok": False,
            "error": f"未知操作: {action}",
            "available": list(handlers.keys()),
        }
    print(json.dumps(result, ensure_ascii=False, default=str))
