# 开发者：自由的风
"""calendar_sync/run.py — Google Calendar (service account) + iCal (.ics) export
GOOGLE_CALENDAR_CREDENTIALS env → service-account JSON key path."""
import sys, json, os, time, base64, subprocess
import urllib.request, urllib.parse, urllib.error
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_URI = "https://oauth2.googleapis.com/token"
API_BASE  = "https://www.googleapis.com/calendar/v3"
SCOPE     = "https://www.googleapis.com/auth/calendar"

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _load_sa():
    path = os.environ.get("GOOGLE_CALENDAR_CREDENTIALS", "")
    if not path: return None, "GOOGLE_CALENDAR_CREDENTIALS env var not set"
    try:
        with open(path) as f: sa = json.load(f)
        for k in ("client_email", "private_key", "token_uri"):
            if k not in sa: return None, f"Missing '{k}' in credentials"
        return sa, None
    except FileNotFoundError: return None, f"Credentials file not found: {path}"
    except json.JSONDecodeError as e: return None, f"Invalid credentials JSON: {e}"

def _make_jwt(sa):
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError: return None, "Missing cryptography (pip install cryptography)"
    header = {"alg": "RS256", "typ": "JWT"}
    now = int(time.time())
    claims = {"iss": sa["client_email"], "scope": SCOPE,
              "aud": sa.get("token_uri", TOKEN_URI), "exp": now + 3600, "iat": now}
    inp = _b64url(json.dumps(header).encode()) + "." + _b64url(json.dumps(claims).encode())
    try:
        key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
        return inp + "." + _b64url(key.sign(inp.encode(), padding.PKCS1v15(), hashes.SHA256())), None
    except Exception as e: return None, f"JWT signing failed: {e}"

def _get_token(sa):
    jwt, err = _make_jwt(sa)
    if err: return None, err
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt}).encode()
    try:
        req = urllib.request.Request(TOKEN_URI, data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("access_token"), None
    except urllib.error.HTTPError as e:
        return None, f"Token exchange {e.code}: {e.read().decode()[:200]}"
    except Exception as e: return None, f"Token request error: {e}"

def _api(method, path, params=None, body=None):
    sa, err = _load_sa()
    if err: return None, err
    token, err = _get_token(sa)
    if err: return None, err
    url = API_BASE + path
    if params: url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"API {e.code}: {e.read().decode()[:300]}"
    except Exception as e: return None, str(e)

def do_list_events(params):
    cid = params.get("calendar_id", "primary")
    qp = {"maxResults": params.get("max_results", 10),
          "orderBy": "startTime", "singleEvents": "true"}
    for k in ("timeMin", "timeMax"):
        if v := params.get(k): qp[k] = v
    if v := params.get("query"): qp["q"] = v
    data, err = _api("GET", f"/calendars/{urllib.parse.quote(cid)}/events", qp)
    if err: return {"ok": False, "error": err}
    items = [{"id": e.get("id"), "summary": e.get("summary", ""),
              "start": e.get("start", {}), "end": e.get("end", {}),
              "location": e.get("location", ""), "description": e.get("description", ""),
              "attendees": [a.get("email") for a in e.get("attendees", [])],
              "html_link": e.get("htmlLink", "")}
             for e in data.get("items", [])]
    return {"ok": True, "events": items, "count": len(items)}

def do_create_event(params):
    start, end = params.get("start"), params.get("end")
    if not start or not end:
        return {"ok": False, "error": "start and end required (RFC 3339)"}
    tz = params.get("timezone", "UTC")
    body = {"summary": params.get("summary", "New Event"),
            "start": {"dateTime": start, "timeZone": tz},
            "end":   {"dateTime": end,   "timeZone": tz}}
    for k in ("description", "location"):
        if v := params.get(k): body[k] = v
    if v := params.get("attendees"):
        body["attendees"] = [{"email": a.strip()} for a in v.split(",")]
    cid = params.get("calendar_id", "primary")
    data, err = _api("POST", f"/calendars/{urllib.parse.quote(cid)}/events", body=body)
    if err: return {"ok": False, "error": err}
    return {"ok": True, "event_id": data.get("id"),
            "html_link": data.get("htmlLink", ""), "summary": data.get("summary", body["summary"])}

def do_free_busy(params):
    tmin, tmax = params.get("time_min"), params.get("time_max")
    if not tmin or not tmax:
        return {"ok": False, "error": "time_min and time_max required (RFC 3339)"}
    items = [{"id": i.strip()} for i in params.get("items", "primary").split(",")]
    data, err = _api("POST", "/freeBusy", body={"timeMin": tmin, "timeMax": tmax, "items": items})
    if err: return {"ok": False, "error": err}
    busy = [{"calendar": cid, "start": s.get("start"), "end": s.get("end")}
            for cid, cal in data.get("calendars", {}).items()
            for s in cal.get("busy", [])]
    return {"ok": True, "busy": busy, "count": len(busy)}

def do_export_ical(params):
    events = params.get("events", [])
    if not events: return {"ok": False,
        "error": "No events: pass [{\"start\":\"…\",\"end\":\"…\",\"summary\":\"…\"},…]"}
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//GBT//Calendar Sync//EN"]
    for ev in events:
        uid = ev.get("id") or base64.urlsafe_b64encode(os.urandom(8)).decode()
        lines.extend(["BEGIN:VEVENT", f"UID:{uid}", f"DTSTART:{ev['start']}",
                      f"DTEND:{ev['end']}", f"SUMMARY:{ev.get('summary','Untitled')}"])
        if d := ev.get("description"): lines.append(f"DESCRIPTION:{d.replace(chr(10),'\\n')}")
        if l := ev.get("location"): lines.append(f"LOCATION:{l}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    out = params.get("output_path", os.path.join(SANDBOX, "calendar_export.ics"))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f: f.write("\r\n".join(lines))
    return {"ok": True, "path": out, "size": os.path.getsize(out), "event_count": len(events)}

def do_schedule_from_calendar(params):
    """从日历读取即将到来的事件，并为每个事件创建smart_scheduler任务
    桥接: 外部日历 → GBT自主任务执行"""
    cid = params.get("calendar_id", "primary")
    max_results = params.get("max_results", 20)
    time_min = params.get("time_min")
    time_max = params.get("time_max")
    default_priority = params.get("priority", 5)
    task_prefix = params.get("task_prefix", "calendar_event")

    # 读取日历事件
    list_params = {"calendar_id": cid, "max_results": max_results}
    if time_min: list_params["timeMin"] = time_min
    if time_max: list_params["timeMax"] = time_max

    events_result = do_list_events(list_params)
    if not events_result.get("ok"):
        return {"ok": False, "error": f"list_events失败: {events_result.get('error')}"}

    events = events_result.get("events", [])
    if not events:
        return {"ok": True, "scheduled": 0, "task_ids": [], "message": "无即将到来的事件"}

    # 调用 smart_scheduler 为每个事件创建任务
    scheduler_py = os.path.join(SANDBOX, "smart_scheduler", "run.py")
    task_ids = []
    for ev in events:
        start_time = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
        summary = ev.get("summary", "Untitled")
        event_id = ev.get("id", "unknown")

        # 构建任务命令: 使用event_trigger或自定义命令
        if template := params.get("task_template"):
            cmd = template.replace("{summary}", summary).replace(
                "{start}", start_time).replace("{event_id}", event_id)
        else:
            cmd = f'python "{scheduler_py}" event_trigger {{{{}}}}'

        sched_params = {"task": f"{task_prefix}: {summary} [{start_time}]", "cmd": cmd,
                        "priority": default_priority}

        try:
            r = subprocess.run([sys.executable, scheduler_py, "schedule",
                                json.dumps(sched_params, ensure_ascii=False)],
                               capture_output=True, text=True, timeout=15,
                               cwd=os.path.dirname(SANDBOX))
            result = json.loads((r.stdout or "{}").strip())
            if result.get("ok"):
                task_ids.append(result.get("task_id", ""))
        except Exception:
            continue

    _save = params.get("save_ical")
    ical_result = None
    if _save:
        ical_result = do_export_ical({"events": events})

    return {"ok": True, "action": "schedule_from_calendar",
            "calendar_id": cid, "events_found": len(events),
            "scheduled": len(task_ids), "task_ids": task_ids,
            "ical": ical_result.get("path") if ical_result else None}


def do_event_trigger(params):
    """轮询检测当前/即将开始的日历事件
    window_minutes: 检测窗口(分钟), 默认±2分钟"""
    cid = params.get("calendar_id", "primary")
    window = params.get("window_minutes", 2)

    # 时间窗口: 从N分钟前到N分钟后
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(minutes=window)).isoformat()
    time_max = (now + timedelta(minutes=window)).isoformat()

    list_params = {"calendar_id": cid, "max_results": 50,
                   "timeMin": time_min, "timeMax": time_max}

    events_result = do_list_events(list_params)
    if not events_result.get("ok"):
        return {"ok": False, "error": f"list_events失败: {events_result.get('error')}"}

    events = events_result.get("events", [])

    triggered = []
    for ev in events:
        start_str = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
        end_str = ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date", ""))

        ev_start = None
        ev_end = None
        try:
            if start_str:
                ev_start = datetime.fromisoformat(start_str)
            if end_str:
                ev_end = datetime.fromisoformat(end_str)
        except (ValueError, TypeError):
            continue

        if ev_start is None:
            continue

        # 判断事件是否"正在触发"
        delta = (now - ev_start).total_seconds()
        status = "upcoming"
        if delta >= 0 and (ev_end is None or now <= ev_end):
            status = "active"
        elif abs(delta) <= window * 60:
            status = "imminent"

        triggered.append({"event_id": ev.get("id"), "summary": ev.get("summary", ""),
                          "start": start_str, "end": end_str,
                          "status": status,
                          "seconds_offset": int(delta),
                          "location": ev.get("location", ""),
                          "description": ev.get("description", ""),
                          "html_link": ev.get("html_link", "")})

    running = [t for t in triggered if t["status"] == "active"]
    imminent = [t for t in triggered if t["status"] == "imminent"]
    upcoming = [t for t in triggered if t["status"] == "upcoming"]

    return {"ok": True, "action": "event_trigger",
            "window_minutes": window, "total_matched": len(triggered),
            "active": len(running), "imminent": len(imminent),
            "events": triggered,
            "has_active": len(running) > 0,
            "has_imminent": len(imminent) > 0}


HANDLERS = {"list_events": do_list_events, "create_event": do_create_event,
            "free_busy": do_free_busy, "export_ical": do_export_ical,
            "schedule_from_calendar": do_schedule_from_calendar,
            "event_trigger": do_event_trigger}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list_events"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
