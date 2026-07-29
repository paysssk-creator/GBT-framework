# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""content_publisher/run.py — WordPress REST API + Medium API
=============================================================
发布/列表/上传媒体 — WP 通过 WORDPRESS_URL+USER+APP_PASSWORD, Medium 通过 MEDIUM_TOKEN
"""
import sys, json, os, base64, urllib.request, urllib.parse, urllib.error

WP_URL = os.environ.get("WORDPRESS_URL", "").rstrip("/")
WP_USER = os.environ.get("WORDPRESS_USER", "")
WP_PASS = os.environ.get("WORDPRESS_APP_PASSWORD", "")
MEDIUM_TOKEN = os.environ.get("MEDIUM_TOKEN", "")

def _r(method, url, headers=None, body=None, timeout=20):
    """通用 HTTP, 返回 (data|None, err|None)"""
    headers = headers or {}
    try:
        d = json.dumps(body).encode("utf-8") if body else None
        if d: headers.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(url, data=d, headers=headers, method=method)
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read().decode("utf-8")
        return (json.loads(raw), None) if raw.strip() else (None, None)
    except urllib.error.HTTPError as e:
        try: msg = json.loads(e.read().decode("utf-8")[:300]).get("message", str(e))
        except: msg = str(e)
        return None, f"HTTP {e.code}: {msg}"[:300]
    except Exception as e:
        return None, str(e)[:200]

def _wp_auth():
    return {"Authorization": "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode(),
            "Accept": "application/json"}

def _wp_ok():
    if not WP_URL: return "WORDPRESS_URL 未设置"
    if not WP_USER or not WP_PASS: return "WORDPRESS_USER 或 WORDPRESS_APP_PASSWORD 未设置"
    return None

def wp_publish(p):
    e = _wp_ok()
    if e: return {"ok": False, "error": e}
    body = {"title": p.get("title", "Untitled"), "content": p.get("content", ""),
            "status": p.get("status", "draft")}
    if p.get("excerpt"): body["excerpt"] = p["excerpt"]
    if p.get("categories"): body["categories"] = p["categories"] if isinstance(p["categories"], list) else [p["categories"]]
    if p.get("tags"): body["tags"] = p["tags"] if isinstance(p["tags"], list) else [p["tags"]]
    d, e = _r("POST", f"{WP_URL}/wp-json/wp/v2/posts", _wp_auth(), body)
    if e: return {"ok": False, "error": e}
    return {"ok": True, "cap": "content_publisher", "action": "publish_post", "platform": "wordpress",
            "post_id": d.get("id"), "link": d.get("link"), "status": d.get("status")}

def wp_list(p):
    e = _wp_ok()
    if e: return {"ok": False, "error": e}
    q = urllib.parse.urlencode({"per_page": p.get("per_page", 10), "page": p.get("page", 1),
         "status": p.get("status", "draft,publish"), "orderby": p.get("orderby", "date"),
         "order": p.get("order", "desc")})
    d, e = _r("GET", f"{WP_URL}/wp-json/wp/v2/posts?{q}", _wp_auth())
    if e: return {"ok": False, "error": e}
    posts = [{"id": x.get("id"), "title": x.get("title", {}).get("rendered", "")[:100],
              "link": x.get("link"), "status": x.get("status"), "date": x.get("date")} for x in (d or [])]
    return {"ok": True, "cap": "content_publisher", "action": "list_posts", "platform": "wordpress",
            "posts": posts, "count": len(posts)}

def wp_upload(p):
    e = _wp_ok()
    if e: return {"ok": False, "error": e}
    fp = p.get("file_path", "")
    fu = p.get("file_url", "")
    if not fp and not fu: return {"ok": False, "error": "需要 file_path 或 file_url"}
    if fp:
        import pathlib
        f = pathlib.Path(fp)
        if not f.is_file(): return {"ok": False, "error": f"文件不存在: {fp}"}
        name, raw = f.name, f.read_bytes()
    else:
        try:
            r = urllib.request.Request(fu, headers={"User-Agent": "GBT/1.0"})
            raw = urllib.request.urlopen(r, timeout=30).read()
            name = fu.rsplit("/", 1)[-1].split("?")[0] or "upload"
        except Exception as ex:
            return {"ok": False, "error": f"下载失败: {str(ex)[:200]}"}
    b = "----GbtBoundary"
    body = f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode() + raw + f"\r\n--{b}--\r\n".encode()
    h = _wp_auth()
    h["Content-Type"] = f"multipart/form-data; boundary={b}"
    try:
        req = urllib.request.Request(f"{WP_URL}/wp-json/wp/v2/media", data=body, headers=h, method="POST")
        d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    except Exception as ex:
        return {"ok": False, "error": str(ex)[:200]}
    return {"ok": True, "cap": "content_publisher", "action": "upload_media", "platform": "wordpress",
            "media_id": d.get("id"), "url": d.get("source_url"), "mime_type": d.get("mime_type")}

def _md_auth():
    return {"Authorization": f"Bearer {MEDIUM_TOKEN}", "Accept": "application/json",
            "Content-Type": "application/json"}

def _md_uid():
    d, e = _r("GET", "https://api.medium.com/v1/me", _md_auth())
    if e: return None, e
    return d.get("data", {}).get("id"), None

def md_publish(p):
    if not MEDIUM_TOKEN: return {"ok": False, "error": "MEDIUM_TOKEN 未设置"}
    uid, e = _md_uid()
    if e: return {"ok": False, "error": e}
    body = {"title": p.get("title", "Untitled"), "contentFormat": p.get("content_format", "markdown"),
            "content": p.get("content", ""),
            "publishStatus": "draft" if p.get("status") == "draft" else "public"}
    if p.get("tags"): body["tags"] = p["tags"] if isinstance(p["tags"], list) else [p["tags"]]
    if p.get("canonical_url"): body["canonicalUrl"] = p["canonical_url"]
    d, e = _r("POST", f"https://api.medium.com/v1/users/{uid}/posts", _md_auth(), body)
    if e: return {"ok": False, "error": e}
    post = d.get("data", {})
    return {"ok": True, "cap": "content_publisher", "action": "publish_post", "platform": "medium",
            "post_id": post.get("id"), "url": post.get("url"), "status": post.get("publishStatus")}

def md_list(p):
    if not MEDIUM_TOKEN: return {"ok": False, "error": "MEDIUM_TOKEN 未设置"}
    uid, e = _md_uid()
    if e: return {"ok": False, "error": e}
    d, e = _r("GET", f"https://api.medium.com/v1/users/{uid}/publications", _md_auth())
    if e: return {"ok": False, "error": e}
    pubs = [{"publication_id": x.get("id"), "name": x.get("name", ""),
             "note": "Medium API write-only; list posts via RSS"} for x in d.get("data", [])[:5]]
    return {"ok": True, "cap": "content_publisher", "action": "list_posts", "platform": "medium",
            "publications": pubs}

HANDLERS = {
    "publish_post": lambda p: wp_publish(p) if p.get("platform") != "medium" else md_publish(p),
    "list_posts": lambda p: wp_list(p) if p.get("platform") != "medium" else md_list(p),
    "upload_media": wp_upload,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list_posts"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    h = HANDLERS.get(action)
    r = h(params) if h else {"ok": False, "error": f"未知 action: {action}"}
    print(json.dumps(r, ensure_ascii=False, default=str))
