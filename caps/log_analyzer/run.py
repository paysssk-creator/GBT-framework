# 开发者：自由的风
"""log_analyzer/run.py — 日志分析引擎"""
import sys, json, re, gzip
from pathlib import Path
from collections import Counter

THREAT_PATTERNS = [
    (r'Failed password for (?:root|admin)', 'SSH暴力破解', 'critical'),
    (r'Failed password for .* from (\d+\.\d+\.\d+\.\d+)', 'SSH可疑登录', 'high'),
    (r'sudo:.*COMMAND=', 'sudo执行', 'warning'),
    (r'File not found.*\.php', 'PHP扫描探测', 'high'),
    (r'(?:union.*select|information_schema)', 'SQL注入探测', 'critical'),
    (r'(?:../../|\.\.\\\\)', '路径遍历攻击', 'critical'),
    (r'(?:;wget|;curl|;nc\s)', '命令注入下载', 'critical'),
    (r'out of memory|OOM killer', '内存耗尽', 'critical'),
    (r'disk.*full|no space left', '磁盘满', 'critical'),
    (r'connection refused|too many connections', '连接耗尽', 'high'),
    (r'Invalid user .* from', '无效用户登录', 'high'),
    (r'error.*token|jwt.*invalid', '认证异常', 'warning'),
]

ERROR_LINE_PATTERNS = [
    (re.compile(r'ERROR|FATAL|CRITICAL|Traceback|Exception', re.IGNORECASE), 'error'),
    (re.compile(r'WARN(?:ING)?', re.IGNORECASE), 'warning'),
    (re.compile(r'FATAL|CRITICAL', re.IGNORECASE), 'critical'),
]

SUGGESTED_FIXES = {
    'connection refused': ('检查目标服务是否运行，确认端口和防火墙配置', 'network'),
    'too many connections': ('增加连接池大小或检查连接泄漏，考虑添加连接超时', 'network'),
    'timeout': ('增加超时时间或优化查询，检查网络延迟', 'network'),
    'out of memory': ('增加内存限制或排查内存泄漏，检查大对象分配', 'resource'),
    'disk.*full': ('清理磁盘空间或扩展存储', 'resource'),
    'permission denied': ('检查文件权限和所有权，确认运行用户', 'security'),
    'file not found': ('确认文件路径是否正确，检查部署是否完整', 'config'),
    'syntax error': ('检查代码语法，确认Python/Shell版本兼容性', 'code'),
    'module not found': ('安装缺失的依赖包或修正导入路径', 'dependency'),
    'cannot import': ('检查Python环境和依赖安装，确认模块名称', 'dependency'),
}


def _read_log(params):
    path = params.get("path", params.get("file", ""))
    text = params.get("text", "")
    try:
        return text if text else (gzip.open(path, 'rt', errors='replace').read() if path.endswith('.gz') else Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def do_tail_errors(params):
    content = _read_log(params)
    if content is None:
        return {"ok": False, "error": "无法读取日志"}
    cursor = params.get("cursor", 0)
    lines = content.split('\n')[cursor:]
    errors = []
    new_cursor = cursor
    for i, line in enumerate(lines):
        for pat, level in ERROR_LINE_PATTERNS:
            if pat.search(line):
                errors.append({"line": cursor + i + 1, "level": level, "text": line.strip()[:200]})
                break
        new_cursor = cursor + i + 1
    return {"ok": True, "action": "tail_errors", "cursor": new_cursor,
            "errors": errors, "total_lines": len(content.split('\n')),
            "new_count": len(errors)}


def do_pattern_learn(params):
    content = _read_log(params)
    if content is None:
        return {"ok": False, "error": "无法读取日志"}
    error_lines = []
    for line in content.split('\n'):
        for pat, level in ERROR_LINE_PATTERNS:
            if pat.search(line):
                error_lines.append(line.strip()[:200])
                break
    patterns = Counter()
    for line in error_lines:
        cleaned = re.sub(r'\d+', 'N', re.sub(r'0x[0-9a-fA-F]+', 'HEX', re.sub(r'[./@]?[\w.-]+@[\w.-]+', 'PATH', line)))
        patterns[cleaned[:120]] += 1
    top = patterns.most_common(20)
    suggestions = []
    for pat_text, count in top:
        fix = None
        for keyword, (advice, category) in SUGGESTED_FIXES.items():
            if re.search(keyword, pat_text, re.IGNORECASE):
                fix = {"advice": advice, "category": category}
                break
        if not fix:
            fix = {"advice": "检查相关日志上下文并对照文档排查", "category": "general"}
        suggestions.append({"pattern": pat_text, "count": count, "fix": fix})
    return {"ok": True, "action": "pattern_learn", "total_errors": len(error_lines),
            "unique_patterns": len(patterns), "suggestions": suggestions}


def do_anomaly_detect(params):
    content = _read_log(params)
    if content is None:
        return {"ok": False, "error": "无法读取日志"}
    lines = content.split('\n')
    window_size = params.get("window", 100)
    baseline = params.get("baseline")
    bursts = []
    new_types = []
    known_types = set()
    for i in range(0, len(lines), window_size):
        chunk = lines[i:i + window_size]
        chunk_errors = 0
        chunk_types = set()
        for line in chunk:
            for pat, level in ERROR_LINE_PATTERNS:
                if pat.search(line):
                    chunk_errors += 1
                    cleaned = re.sub(r'\d+', 'N', line.strip()[:80])
                    chunk_types.add(cleaned)
                    break
        if baseline is None:
            baseline = max(1, chunk_errors)
        if chunk_errors > baseline * 3 and chunk_errors > 2:
            bursts.append({"window_start": i + 1, "window_end": min(i + window_size, len(lines)),
                           "error_count": chunk_errors, "baseline": baseline, "spike_ratio": round(chunk_errors / max(1, baseline), 1)})
        for t in chunk_types:
            if t not in known_types:
                new_types.append(t[:120])
        known_types.update(chunk_types)
    return {"ok": True, "action": "anomaly_detect", "total_lines": len(lines),
            "bursts": bursts[:20], "new_error_types": new_types[:30],
            "burst_count": len(bursts), "new_type_count": len(new_types)}


def do_analyze(params):
    file_path = params.get('file', str(Path.home() / '.gbt' / 'errors.log'))
    try:
        content = (gzip.open(file_path, 'rt', errors='replace').read()
                   if file_path.endswith('.gz')
                   else Path(file_path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {"ok": False, "error": f"无法读取日志文件: {file_path}"}
    lines = content.split('\n')
    errors = []
    warnings = []
    for i, line in enumerate(lines):
        for pat, level in ERROR_LINE_PATTERNS:
            if pat.search(line):
                entry = {"line": i + 1, "level": level, "text": line.strip()[:200]}
                if level in ('error', 'critical'):
                    errors.append(entry)
                elif level == 'warning':
                    warnings.append(entry)
                break
    error_count = len(errors)
    warning_count = len(warnings)
    parts = []
    if error_count:
        parts.append(f"{error_count} 个错误/严重")
    if warning_count:
        parts.append(f"{warning_count} 个警告")
    if not parts:
        summary = f"日志共 {len(lines)} 行，未发现错误或警告"
    else:
        summary = f"日志共 {len(lines)} 行，发现 {'，'.join(parts)}"
    return {"ok": True, "lines": len(lines), "errors": errors, "warnings": warnings, "summary": summary}


HANDLERS = {"analyze": do_analyze, "tail_errors": do_tail_errors,
             "pattern_learn": do_pattern_learn, "anomaly_detect": do_anomaly_detect}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "analyze"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))
