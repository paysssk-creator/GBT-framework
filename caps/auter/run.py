# 开发者：自由的风
'''auter/run.py — 自动化工具箱：crontab表达式生成/文件监控/批量重命名/文件备份/临时清理'''
import sys, json, os, hashlib, shutil, re, fnmatch
from pathlib import Path
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════
# 1. cron — 语义→crontab 表达式生成
# ═══════════════════════════════════════════════

# 预置常用表达式
_CRON_PRESETS = {
    "every minute":                ("* * * * *",   "每分钟执行"),
    "every 5 minutes":             ("*/5 * * * *", "每5分钟执行"),
    "every 10 minutes":            ("*/10 * * * *","每10分钟执行"),
    "every 15 minutes":            ("*/15 * * * *","每15分钟执行"),
    "every 30 minutes":            ("*/30 * * * *","每30分钟执行"),
    "every hour":                  ("0 * * * *",   "每小时整点执行"),
    "every 2 hours":               ("0 */2 * * *", "每2小时整点执行"),
    "every 3 hours":               ("0 */3 * * *", "每3小时整点执行"),
    "every 6 hours":               ("0 */6 * * *", "每6小时整点执行"),
    "every 12 hours":              ("0 */12 * * *","每12小时执行"),
    "every day at midnight":       ("0 0 * * *",   "每天午夜0点执行"),
    "every day at noon":           ("0 12 * * *",  "每天中午12点执行"),
    "every day at 3am":            ("0 3 * * *",   "每天凌晨3点执行"),
    "every day at 6am":            ("0 6 * * *",   "每天早上6点执行"),
    "every day at 9am":            ("0 9 * * *",   "每天早上9点执行"),
    "every weekday at 9am":        ("0 9 * * 1-5", "每个工作日（周一至周五）上午9点执行"),
    "every weekday at 6pm":        ("0 18 * * 1-5","每个工作日（周一至周五）下午6点执行"),
    "every monday at 9am":         ("0 9 * * 1",   "每周一上午9点执行"),
    "every tuesday at 9am":        ("0 9 * * 2",   "每周二上午9点执行"),
    "every wednesday at 9am":      ("0 9 * * 3",   "每周三上午9点执行"),
    "every thursday at 9am":       ("0 9 * * 4",   "每周四上午9点执行"),
    "every friday at 9am":         ("0 9 * * 5",   "每周五上午9点执行"),
    "every saturday at 9am":       ("0 9 * * 6",   "每周六上午9点执行"),
    "every sunday at 9am":         ("0 9 * * 0",   "每周日（周日=0）上午9点执行"),
    "every monday at midnight":    ("0 0 * * 1",   "每周一午夜0点执行"),
    "every friday at midnight":    ("0 0 * * 5",   "每周五午夜0点执行"),
    "every weekend at midnight":   ("0 0 * * 6,0", "每周末（周六、周日）午夜0点执行"),
    "every first day of month":    ("0 0 1 * *",   "每月1号午夜0点执行"),
    "every 15th at noon":          ("0 12 15 * *", "每月15号中午12点执行"),
    "every last day of month":     ("0 0 L * *",   "每月最后一天午夜0点执行（部分cron实现支持L）"),
    "every january first":         ("0 0 1 1 *",   "每年1月1日午夜0点执行"),
}

# cron 字段顺序: minute hour day month weekday
_DAY_MAP = {
    "monday": "1", "tuesday": "2", "wednesday": "3",
    "thursday": "4", "friday": "5", "saturday": "6", "sunday": "0",
    "mon": "1", "tue": "2", "wed": "3", "thu": "4", "fri": "5", "sat": "6", "sun": "0",
    "weekday": "1-5", "weekend": "6,0",
}

def _parse_every_minutes(schedule: str) -> tuple:
    """解析 'every N minutes' / 'every minute'"""
    m = re.match(r'every\s+(\d+)\s*minutes?', schedule, re.I)
    if not m:
        m = re.match(r'every\s+minute', schedule, re.I)
    if m:
        n = int(m.group(1)) if m.lastindex else 1
        if n == 1:
            return ("* * * * *", "每分钟执行")
        elif n <= 59:
            return (f"*/{n} * * * *", f"每{n}分钟执行")
    return None

def _parse_every_hours(schedule: str) -> tuple:
    """解析 'every N hours' / 'every hour'"""
    m = re.match(r'every\s+(\d+)\s*hours?', schedule, re.I)
    if m:
        n = int(m.group(1))
        if n == 1:
            return ("0 * * * *", "每小时整点执行")
        return (f"0 */{n} * * *", f"每{n}小时整点执行")
    m = re.match(r'every\s+hour', schedule, re.I)
    if m:
        return ("0 * * * *", "每小时整点执行")
    return None

def _parse_time_of_day(schedule: str) -> tuple:
    """解析 'at HH:MM' 返回 (hour, minute)"""
    m = re.search(r'at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?', schedule, re.I)
    if m:
        h = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)
        if ampm:
            ampm = ampm.lower()
            if ampm == "pm" and h != 12:
                h += 12
            elif ampm == "am" and h == 12:
                h = 0
        if 0 <= h <= 23 and 0 <= minute <= 59:
            return (h, minute)
    m = re.search(r'at\s+(midnight|noon)', schedule, re.I)
    if m:
        word = m.group(1).lower()
        return (0, 0) if word == "midnight" else (12, 0)
    return None

def _parse_days(schedule: str) -> tuple:
    """返回 (dow: str | None, dom: int | None, desc_part: str)"""
    dow = None
    dom = None
    desc = ""

    # 每月第几天
    m = re.search(r'(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\s*(?:day\s*)?(?:of\s*)?(?:the\s*)?(?:month\s*)?(?:at\b)?', schedule, re.I)
    if m:
        dom = int(m.group(1))
        if 1 <= dom <= 30:
            desc += f"每月{dom}号"

    # 最后一天
    if re.search(r'last\s+day', schedule, re.I):
        dom = "L"
        desc += "每月最后一天"

    # 星期几
    for day_en in _DAY_MAP:
        p = re.compile(r'\b' + day_en + r'(?:day)?\b', re.I)
        if p.search(schedule):
            dow = _DAY_MAP[day_en]
            if day_en in ("weekday", "weekend"):
                desc_part = "工作日" if day_en == "weekday" else "周末"
            else:
                desc_part = day_en.capitalize()
            desc += f"每{desc_part}"
            break

    # 每月初一
    if re.search(r'first\s+day', schedule, re.I):
        dom = 1
        desc += "每月1号"

    return (dow, dom, desc)

def do_cron(params: dict) -> dict:
    """将语义调度语句转换为 crontab 表达式"""
    schedule = params.get("schedule", "").strip().lower()
    if not schedule:
        return {"ok": False, "error": "缺少 schedule 参数"}

    # 精确匹配预置
    if schedule in _CRON_PRESETS:
        expr, desc = _CRON_PRESETS[schedule]
        return {
            "ok": True,
            "expression": expr,
            "schedule": schedule,
            "explanation": desc,
            "fields": _explain_fields(expr),
        }

    # 匹配 "every N minutes"
    result = _parse_every_minutes(schedule)
    if result:
        expr, desc = result
        return {"ok": True, "expression": expr, "schedule": schedule, "explanation": desc, "fields": _explain_fields(expr)}

    # 匹配 "every N hours"
    result = _parse_every_hours(schedule)
    if result:
        expr, desc = result
        return {"ok": True, "expression": expr, "schedule": schedule, "explanation": desc, "fields": _explain_fields(expr)}

    # 动态构建：时间 + 星期/日期
    time_part = _parse_time_of_day(schedule)
    day_dow, day_dom, day_desc = _parse_days(schedule)

    if time_part:
        h, m = time_part
        if day_dow or day_dom:
            minute_f = str(m)
            hour_f = str(h)
            dom_f = str(day_dom) if day_dom else "*"
            month_f = "*"
            dow_f = day_dow if day_dow else "*"
            expr = f"{minute_f} {hour_f} {dom_f} {month_f} {dow_f}"
            time_desc = f"{h:02d}:{m:02d}"
            desc = f"{day_desc} {time_desc}执行"
            return {"ok": True, "expression": expr, "schedule": schedule, "explanation": desc, "fields": _explain_fields(expr)}
        else:
            expr = f"{m} {h} * * *"
            desc = f"每天{h:02d}:{m:02d}执行"
            return {"ok": True, "expression": expr, "schedule": schedule, "explanation": desc, "fields": _explain_fields(expr)}

    # 未匹配
    return {
        "ok": False,
        "error": f"无法解析调度语句: '{params.get('schedule', '')}'",
        "hint": "试试: 'every hour', 'every day at 3am', 'every monday at 9am', 'every 30 minutes'",
        "presets": sorted(_CRON_PRESETS.keys()),
    }

def _explain_fields(expr: str) -> dict:
    """将 crontab 表达式拆解为人类可读的字段说明"""
    parts = expr.split()
    if len(parts) != 5:
        return {}
    names = ["minute", "hour", "day_of_month", "month", "day_of_week"]
    explains = {}
    for name, val in zip(names, parts):
        if val == "*":
            explains[name] = "任意"
        elif val.startswith("*/"):
            n = val[2:]
            if name == "minute":
                explains[name] = f"每{n}分钟"
            elif name == "hour":
                explains[name] = f"每{n}小时"
            else:
                explains[name] = f"每{n}{name}"
        elif "," in val:
            explains[name] = f"在 {val} 时" if name in ("minute", "hour") else f"在 {val}"
        elif "-" in val:
            explains[name] = f"范围 {val}"
        elif val == "L":
            explains[name] = "最后一天"
        else:
            if name == "minute":
                explains[name] = f"第{val}分钟"
            elif name == "hour":
                explains[name] = f"第{val}小时"
            elif name == "day_of_month":
                explains[name] = f"每月{val}号"
            elif name == "month":
                explains[name] = f"第{val}月"
            elif name == "day_of_week":
                day_names = {"0": "周日", "1": "周一", "2": "周二", "3": "周三", "4": "周四", "5": "周五", "6": "周六"}
                explains[name] = day_names.get(val, val)
    return explains


# ═══════════════════════════════════════════════
# 2. watch — 文件变化监控 (MD5 轮询)
# ═══════════════════════════════════════════════

def _md5_hex(path: Path) -> str:
    """计算文件 MD5 哈希"""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _file_snapshot(base_path: Path, pattern: str | None, recursive: bool) -> dict:
    """获取目录/文件当前快照 {relpath: md5}"""
    snap = {}
    if base_path.is_file():
        snap[str(base_path)] = _md5_hex(base_path)
    elif base_path.is_dir():
        it = base_path.rglob("*") if recursive else base_path.glob("*")
        for p in it:
            if p.is_file():
                if pattern and not fnmatch.fnmatch(p.name, pattern):
                    continue
                snap[str(p)] = _md5_hex(p)
    return snap

def do_watch(params: dict) -> dict:
    """
    文件变化监控 (轮询 MD5)
    参数:
      path: 文件或目录路径
      pattern: glob 模式 (目录模式下过滤，如 "*.py")
      recursive: 是否递归子目录 (默认 true)
      prev: 上一轮快照 (用于比较变化)，首次调用不传
      action: "snapshot" 仅获取当前快照 | "diff" 传入 prev 获取变化
    """
    action = params.get("action", "snapshot").lower()
    target = params.get("path", params.get("dir", "."))
    pattern = params.get("pattern", None)
    recursive = params.get("recursive", True)
    prev_snap = params.get("prev", {})

    base = Path(target)
    if not base.exists():
        return {"ok": False, "error": f"路径不存在: {target}"}

    current = _file_snapshot(base, pattern, recursive)

    if action == "snapshot":
        return {
            "ok": True,
            "action": "snapshot",
            "path": str(base),
            "files": len(current),
            "snapshot": current,
        }

    # diff 模式：返回变化
    added = {}
    changed = {}
    removed = []

    for path, md5 in current.items():
        if path not in prev_snap:
            added[path] = md5
        elif prev_snap[path] != md5:
            changed[path] = {"old": prev_snap[path], "new": md5}

    for path in prev_snap:
        if path not in current:
            removed.append(path)

    return {
        "ok": True,
        "action": "diff",
        "path": str(base),
        "files_total": len(current),
        "changes": {
            "added": list(added.keys()),
            "modified": list(changed.keys()),
            "removed": removed,
        },
        "added_count": len(added),
        "modified_count": len(changed),
        "removed_count": len(removed),
        "snapshot": current,
    }


# ═══════════════════════════════════════════════
# 3. batch_rename — 批量重命名
# ═══════════════════════════════════════════════

def do_batch_rename(params: dict) -> dict:
    """
    批量重命名文件
    参数:
      path: 目标目录
      pattern: glob 模式 (如 "*.txt")
      find:   正则匹配模式 (匹配文件名部分)
      replace: 替换字符串 (支持 \\1 \\2 等反向引用)
      prefix: 添加前缀
      suffix: 添加后缀 (在扩展名之前)
      extension: 统一修改扩展名
      dry_run: 仅预览，不实际执行 (默认 true)
    """
    target = params.get("path", params.get("dir", "."))
    pattern = params.get("pattern", "*")
    find = params.get("find", "")
    replace = params.get("replace", "")
    prefix = params.get("prefix", "")
    suffix = params.get("suffix", "")
    extension = params.get("extension", "")
    dry_run = params.get("dry_run", True)

    base = Path(target)
    if not base.is_dir():
        return {"ok": False, "error": f"目录不存在: {target}"}

    files = sorted([p for p in base.glob(pattern) if p.is_file()])
    if not files:
        return {"ok": True, "path": str(base), "matched": 0, "renamed": 0, "results": [], "message": "没有匹配到文件"}

    results = []
    errors = []

    for fp in files:
        old_name = fp.name
        stem = fp.stem
        ext = fp.suffix

        # 应用 find/replace 正则
        if find:
            try:
                new_stem = re.sub(find, replace, stem)
            except Exception as e:
                errors.append({"file": old_name, "error": f"正则替换失败: {e}"})
                continue
        else:
            new_stem = stem

        # prefix / suffix
        if prefix:
            new_stem = prefix + new_stem
        if suffix:
            new_stem = new_stem + suffix

        # extension
        new_ext = f".{extension.lstrip('.')}" if extension else ext

        new_name = new_stem + new_ext
        new_path = fp.parent / new_name

        entry = {
            "old_name": old_name,
            "new_name": new_name,
            "old_path": str(fp),
            "new_path": str(new_path),
        }

        if new_name == old_name:
            entry["skipped"] = True
            entry["reason"] = "名称未变化"
        elif new_path.exists():
            entry["skipped"] = True
            entry["reason"] = "目标文件已存在"
        else:
            if not dry_run:
                try:
                    fp.rename(new_path)
                    entry["renamed"] = True
                except Exception as e:
                    errors.append({"file": old_name, "error": str(e)})
                    continue
            else:
                entry["renamed"] = False

        results.append(entry)

    renamed_count = sum(1 for r in results if r.get("renamed"))

    return {
        "ok": True,
        "path": str(base),
        "matched": len(files),
        "renamed": renamed_count,
        "dry_run": dry_run,
        "results": results,
        "errors": errors,
    }


# ═══════════════════════════════════════════════
# 4. backup — 文件备份 (复制+时间戳)
# ═══════════════════════════════════════════════

def do_backup(params: dict) -> dict:
    """
    文件备份：将文件/目录复制到备份位置，自动附加时间戳
    参数:
      path: 源文件或目录路径
      dest: 备份目标目录 (默认源文件所在目录下的 backup/)
      name: 备份文件名（不含时间戳部分），默认使用原名
      timestamp_fmt: 时间戳格式 (默认 "%Y%m%d_%H%M%S")
      keep: 保留最近 N 个备份 (0 = 不清理)
      compress: 是否打包为 zip (仅目录模式)
    """
    src = params.get("path", "")
    dest_dir = params.get("dest", "")
    name = params.get("name", "")
    timestamp_fmt = params.get("timestamp_fmt", "%Y%m%d_%H%M%S")
    keep = params.get("keep", 0)
    compress = params.get("compress", False)

    if not src:
        return {"ok": False, "error": "缺少 path 参数"}

    src_path = Path(src)
    if not src_path.exists():
        return {"ok": False, "error": f"源路径不存在: {src}"}

    ts = datetime.now().strftime(timestamp_fmt)

    # 确定目标目录
    if dest_dir:
        dest_dir_path = Path(dest_dir)
    else:
        # 默认: 源文件旁边创建 backup 目录
        dest_dir_path = (src_path.parent if src_path.is_file() else src_path.parent) / "backup"

    dest_dir_path.mkdir(parents=True, exist_ok=True)

    # 确定备份名称
    base_name = name if name else src_path.name
    if src_path.is_file():
        stem, ext = src_path.stem, src_path.suffix
        if name:
            backup_name = f"{name}_{ts}{ext}"
        else:
            backup_name = f"{stem}_{ts}{ext}"
        dest_path = dest_dir_path / backup_name
        try:
            shutil.copy2(src_path, dest_path)
        except Exception as e:
            return {"ok": False, "error": f"复制失败: {e}"}
        result_type = "file"
        backup_path = dest_path
    else:
        # 目录备份
        if compress:
            backup_name = f"{base_name}_{ts}"
            dest_path = dest_dir_path / backup_name
            try:
                shutil.make_archive(str(dest_path), 'zip', src_path)
                backup_path = Path(str(dest_path) + ".zip")
            except Exception as e:
                return {"ok": False, "error": f"打包失败: {e}"}
            result_type = "archive"
        else:
            backup_name = f"{base_name}_{ts}"
            dest_path = dest_dir_path / backup_name
            try:
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(src_path, dest_path)
            except Exception as e:
                return {"ok": False, "error": f"目录复制失败: {e}"}
            result_type = "directory"
            backup_path = dest_path

    result = {
        "ok": True,
        "source": str(src_path),
        "backup": str(backup_path),
        "type": result_type,
        "timestamp": ts,
        "dest_dir": str(dest_dir_path),
    }

    size_bytes = 0
    if backup_path.is_file():
        size_bytes = backup_path.stat().st_size
    elif backup_path.is_dir():
        size_bytes = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
    result["size_bytes"] = size_bytes

    # 保留策略：清理旧备份
    if keep > 0:
        # 匹配同名备份模式
        if src_path.is_file():
            stem, ext = src_path.stem, src_path.suffix
            if name:
                prefix = f"{name}_"
            else:
                prefix = f"{stem}_"
            pattern = f"{prefix}*{ext}"
        else:
            prefix = f"{base_name}_"
            pattern = f"{prefix}*"

        old_backups = sorted(
            [p for p in dest_dir_path.glob(f"{base_name}_*")],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        cleaned = old_backups[keep:]
        for old in cleaned:
            try:
                if old.is_dir():
                    shutil.rmtree(old)
                else:
                    old.unlink()
            except Exception:
                pass
        result["cleaned"] = len(cleaned)

    return result


# ═══════════════════════════════════════════════
# 5. cleanup — 临时文件清理
# ═══════════════════════════════════════════════

def do_cleanup(params: dict) -> dict:
    """
    临时文件清理
    参数:
      path: 目标目录
      pattern: glob 模式 (默认 "*.tmp;*.temp;*.bak;*.log;*.cache;*~")
      older_than_days: 清理 N 天前的文件 (0 = 不限)
      recursive: 递归子目录 (默认 false)
      dry_run: 仅预览 (默认 true)
      max_size_mb: 清理超过此大小的文件 (0 = 不限)
    """
    target = params.get("path", params.get("dir", "."))
    pattern_str = params.get("pattern", "*.tmp;*.temp;*.bak;*.log;*.cache;*~")
    older_than_days = params.get("older_than_days", 0)
    recursive = params.get("recursive", False)
    dry_run = params.get("dry_run", True)
    max_size_mb = params.get("max_size_mb", 0)

    base = Path(target)
    if not base.is_dir():
        return {"ok": False, "error": f"目录不存在: {target}"}

    patterns = [p.strip() for p in pattern_str.split(";") if p.strip()]

    now = datetime.now()
    cutoff = now - timedelta(days=older_than_days) if older_than_days > 0 else None
    max_size = max_size_mb * 1024 * 1024 if max_size_mb > 0 else 0

    candidates = []
    for pat in patterns:
        it = base.rglob(pat) if recursive else base.glob(pat)
        candidates.extend(it)

    # 去重（同一文件可能匹配多个 glob）
    seen = set()
    unique_files = []
    for fp in candidates:
        if fp.is_file() and str(fp) not in seen:
            seen.add(str(fp))
            unique_files.append(fp)

    matched = []
    freed_bytes = 0

    for fp in sorted(unique_files):
        stat = fp.stat()
        age_days = (now - datetime.fromtimestamp(stat.st_mtime)).days

        skip_reason = None
        if cutoff and datetime.fromtimestamp(stat.st_mtime) > cutoff:
            skip_reason = f"未超过{older_than_days}天"
        if max_size > 0 and stat.st_size < max_size:
            skip_reason = f"小于{max_size_mb}MB"

        entry = {
            "path": str(fp),
            "name": fp.name,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "age_days": age_days,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

        if skip_reason:
            entry["skipped"] = True
            entry["reason"] = skip_reason
        else:
            if not dry_run:
                try:
                    fp.unlink()
                    entry["deleted"] = True
                    freed_bytes += stat.st_size
                except Exception as e:
                    entry["error"] = str(e)
            else:
                entry["deleted"] = False

        matched.append(entry)

    deleted_count = sum(1 for m in matched if m.get("deleted"))
    total_size = sum(m["size_bytes"] for m in matched)

    return {
        "ok": True,
        "path": str(base),
        "patterns": patterns,
        "matched": len(matched),
        "deleted": deleted_count,
        "freed_bytes": freed_bytes,
        "total_size_bytes": total_size,
        "dry_run": dry_run,
        "files": matched,
    }


# ═══════════════════════════════════════════════
# Handler 注册
# ═══════════════════════════════════════════════

handlers = {
    "cron":          do_cron,
    "watch":         do_watch,
    "batch_rename":  do_batch_rename,
    "backup":        do_backup,
    "cleanup":       do_cleanup,
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
            "error": f"未知工具: {action}",
            "available": list(handlers.keys()),
        }
    print(json.dumps(result, ensure_ascii=False, default=str))
