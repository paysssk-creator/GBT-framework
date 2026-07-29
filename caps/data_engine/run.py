# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""data_engine/run.py — 数据引擎 (CSV/JSON/Excel)"""
import sys, json, os, csv, io, time, subprocess
from pathlib import Path
from datetime import datetime

def _read_file(path):
    fp = Path(path)
    if not fp.exists():
        return None, f"文件不存在: {path}"
    suffix = fp.suffix.lower()
    if suffix == ".csv":
        with open(fp, encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            return [row for row in reader], None
    elif suffix == ".json":
        return json.loads(fp.read_text(encoding="utf-8")), None
    elif suffix in (".xlsx", ".xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(fp, read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows: return [], None
            headers = [str(c) if c else f"col_{i}" for i, c in enumerate(rows[0])]
            return [dict(zip(headers, row)) for row in rows[1:]], None
        except ImportError:
            return None, "需要 openpyxl: pip install openpyxl"
    return None, f"不支持格式: {suffix}"

def _summarize(data):
    if not data: return {"count": 0, "columns": []}
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict):
            cols = list(data[0].keys())
            sample = data[:3]
            types = {}
            for c in cols:
                vals = [row.get(c) for row in data if row.get(c) is not None]
                if vals:
                    try:
                        [float(v) for v in vals[:10]]
                        types[c] = "number"
                    except:
                        types[c] = "string"
            return {"count": len(data), "columns": cols, "types": types, "sample": sample}
        return {"count": len(data), "sample": data[:3]}
    return {"count": 1, "type": type(data).__name__}

def do_read(params):
    path = params.get("file", params.get("path", ""))
    query = params.get("query", "")
    if not path: return {"ok": False, "error": "缺少 file 参数"}
    data, err = _read_file(path)
    if err: return {"ok": False, "error": err}
    summary = _summarize(data)
    summary["ok"] = True
    return summary

def do_analyze(params):
    path = params.get("file", params.get("path", ""))
    group_by = params.get("group_by", "")
    agg = params.get("agg", "count")  # count/sum/avg/min/max
    field = params.get("field", "")
    sort_by = params.get("sort_by", "")
    limit = params.get("limit", 100)
    if not path: return {"ok": False, "error": "缺少 file 参数"}
    data, err = _read_file(path)
    if err: return {"ok": False, "error": err}
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return {"ok": False, "error": "数据格式不支持分析 (需要表格数据)"}
    result = data
    # 分组聚合
    if group_by and group_by in data[0]:
        groups = {}
        for row in data:
            key = str(row.get(group_by, ""))
            groups.setdefault(key, []).append(row)
        agg_result = []
        for key, rows in groups.items():
            entry = {group_by: key, "count": len(rows)}
            if field and agg in ("sum", "avg", "min", "max"):
                vals = [float(r.get(field, 0)) for r in rows if r.get(field) is not None]
                if vals:
                    if agg == "sum": entry[f"sum_{field}"] = round(sum(vals), 2)
                    elif agg == "avg": entry[f"avg_{field}"] = round(sum(vals)/len(vals), 2)
                    elif agg == "min": entry[f"min_{field}"] = min(vals)
                    elif agg == "max": entry[f"max_{field}"] = max(vals)
            agg_result.append(entry)
        result = agg_result
    # 排序
    if sort_by:
        try:
            result = sorted(result, key=lambda r: float(r.get(sort_by, 0)) if r.get(sort_by) else 0, reverse=True)
        except:
            result = sorted(result, key=lambda r: str(r.get(sort_by, "")), reverse=True)
    # 限制
    if limit and len(result) > limit:
        result = result[:limit]
    return {"ok": True, "count": len(result), "data": result}

def do_clean(params):
    path = params.get("file", params.get("path", ""))
    output = params.get("output", "")
    drop_duplicates = params.get("drop_duplicates", True)
    fill_na = params.get("fill_na", "")
    drop_columns = params.get("drop_columns", [])
    if not path: return {"ok": False, "error": "缺少 file 参数"}
    data, err = _read_file(path)
    if err: return {"ok": False, "error": err}
    if not isinstance(data, list): return {"ok": False, "error": "需要表格数据"}
    before = len(data)
    # 去重
    if drop_duplicates and data and isinstance(data[0], dict):
        seen = set()
        unique = []
        for row in data:
            key = json.dumps(row, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                unique.append(row)
        data = unique
    # 填缺
    if fill_na and data:
        for row in data:
            for k in row:
                if row[k] is None or row[k] == "":
                    row[k] = fill_na
    # 删列
    if drop_columns and data and isinstance(data[0], dict):
        for row in data:
            for col in drop_columns:
                row.pop(col, None)
    after = len(data)
    if output:
        suffix = Path(output).suffix.lower()
        if suffix == ".csv":
            with open(output, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=data[0].keys())
                w.writeheader(); w.writerows(data)
        elif suffix == ".json":
            Path(output).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "before": before, "after": after, "removed": before - after,
            "output": output if output else None}

def do_export(params):
    path = params.get("file", params.get("path", ""))
    output = params.get("output", "export.csv")
    if not path: return {"ok": False, "error": "缺少 file 参数"}
    data, err = _read_file(path)
    if err: return {"ok": False, "error": err}
    suffix = Path(output).suffix.lower()
    if suffix == ".csv" and isinstance(data, list) and data and isinstance(data[0], dict):
        with open(output, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=data[0].keys())
            w.writeheader(); w.writerows(data)
    elif suffix == ".json":
        Path(output).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "output": output, "size_kb": round(Path(output).stat().st_size/1024, 1)}

def do_query(params):
    path = params.get("file", params.get("path", ""))
    where = params.get("where", {})
    select = params.get("select", [])
    sort_by = params.get("sort_by", "")
    limit = params.get("limit", 100)
    if not path: return {"ok": False, "error": "缺少 file 参数"}
    data, err = _read_file(path)
    if err: return {"ok": False, "error": err}
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return {"ok": False, "error": "需要表格数据"}
    # WHERE
    result = data
    if where:
        result = [r for r in result if all(str(r.get(k, "")) == str(v) for k, v in where.items())]
    # SELECT
    if select:
        result = [{k: r.get(k) for k in select if k in r} for r in result]
    # SORT
    if sort_by:
        result = sorted(result, key=lambda r: str(r.get(sort_by, "")))
    # LIMIT
    if limit and len(result) > limit:
        result = result[:limit]
    return {"ok": True, "count": len(result), "data": result}
# ═══════════════════ 自动ETL ═══════════════════

DATA_WATCH_DIR = Path.home() / '.gbt' / 'data_inbox'
DATA_PROCESSED_LOG = DATA_WATCH_DIR / '_processed.json'

def _load_processed():
    if DATA_PROCESSED_LOG.exists():
        try:
            return set(json.loads(DATA_PROCESSED_LOG.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()

def _save_processed(processed):
    DATA_WATCH_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_LOG.write_text(json.dumps(list(processed), default=str), encoding="utf-8")

def do_auto_etl(params):
    """自动ETL — 监控目录, 自动发现并处理新数据文件

    params:
        watch_dir: str   — 监控目录 (默认 ~/.gbt/data_inbox/)
        poll_interval: int — 轮询间隔秒数 (默认10)
        max_rounds: int  — 最大轮次 (默认0=无限)
        auto_export: bool — 处理后导出 (默认True)
    """
    watch_dir = Path(params.get("watch_dir", DATA_WATCH_DIR))
    poll_interval = params.get("poll_interval", 10)
    max_rounds = params.get("max_rounds", 0)
    auto_export = params.get("auto_export", True)

    watch_dir.mkdir(parents=True, exist_ok=True)

    processed = _load_processed()
    results = []
    round_num = 0
    total_processed = 0

    supported_exts = {'.csv', '.json', '.xlsx', '.xls'}

    while True:
        round_num += 1
        if max_rounds > 0 and round_num > max_rounds:
            break

        new_files = []
        for f in sorted(watch_dir.iterdir()):
            if not f.is_file():
                continue
            if f.name.startswith('_'):
                continue
            if f.suffix.lower() not in supported_exts:
                continue
            fid = f"{f.name}:{f.stat().st_mtime}"
            if fid not in processed:
                new_files.append(f)

        round_result = {"round": round_num, "ts": datetime.now().isoformat(),
                        "new_files": len(new_files), "processed": []}

        for fp in new_files:
            try:
                data, err = _read_file(str(fp))
                if err:
                    round_result["processed"].append({"file": fp.name, "status": "error", "error": err})
                    continue

                summary = _summarize(data)
                proc_result = {"file": fp.name, "status": "ok",
                               "rows": summary.get("count", 0),
                               "columns": summary.get("columns", [])}

                if auto_export and data:
                    export_dir = watch_dir / "_processed"
                    export_dir.mkdir(parents=True, exist_ok=True)
                    export_path = export_dir / f"{fp.stem}_clean.json"
                    export_path.write_text(json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8")
                    proc_result["exported"] = str(export_path)

                round_result["processed"].append(proc_result)
                fid = f"{fp.name}:{fp.stat().st_mtime}"
                processed.add(fid)
                total_processed += 1

            except Exception as e:
                round_result["processed"].append({"file": fp.name, "status": "error", "error": str(e)[:100]})

        if round_result["processed"]:
            results.append(round_result)
            _save_processed(processed)

        time.sleep(poll_interval)

    return {"ok": True, "watch_dir": str(watch_dir), "total_rounds": round_num,
            "total_processed": total_processed, "last_results": results[-3:] if results else []}


# ═══════════════════ 管道监控 ═══════════════════

PIPELINE_STATE_FILE = Path.home() / '.gbt' / 'data_inbox' / '_pipeline_state.json'

def _load_pipeline_state():
    if PIPELINE_STATE_FILE.exists():
        try:
            return json.loads(PIPELINE_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"stages": {}, "failures": [], "last_check": None}

def _save_pipeline_state(state):
    PIPELINE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["last_check"] = datetime.now().isoformat()
    PIPELINE_STATE_FILE.write_text(json.dumps(state, default=str, indent=2), encoding="utf-8")

def _alert_pipeline_failure(stage, error, severity="warning"):
    """通过event_bus发布管道故障告警"""
    try:
        eb_run = Path(__file__).parent.parent / "event_bus" / "run.py"
        if eb_run.exists():
            subprocess.run(
                ["python", str(eb_run), "publish",
                 f"topic=data_pipeline/{stage}",
                 f"event_type=pipeline_failure",
                 f"payload={json.dumps({'stage': stage, 'error': str(error)[:200], 'severity': severity, 'ts': datetime.now().isoformat()}, default=str, ensure_ascii=False)}"],
                capture_output=True, text=True, timeout=10,
                cwd=str(Path(__file__).parent.parent)
            )
    except Exception:
        pass

def do_pipeline_watch(params):
    """管道监控 — 监控数据管道状态, 故障自动告警

    params:
        pipeline_dir: str — 管道目录 (默认 ~/.gbt/data_inbox/)
        stages: list[str] — 管道阶段 (默认 ['ingest','validate','transform','export'])
        check_interval: int — 检查间隔秒数 (默认30)
        max_rounds: int — 最大轮次 (默认0=无限)
    """
    pipeline_dir = Path(params.get("pipeline_dir", DATA_WATCH_DIR))
    stages = params.get("stages", ["ingest", "validate", "transform", "export"])
    check_interval = params.get("check_interval", 30)
    max_rounds = params.get("max_rounds", 0)
    max_failures_before_alert = params.get("max_failures_before_alert", 3)

    pipeline_dir.mkdir(parents=True, exist_ok=True)

    state = _load_pipeline_state()
    round_num = 0
    alerts = []

    while True:
        round_num += 1
        if max_rounds > 0 and round_num > max_rounds:
            break

        check_result = {"round": round_num, "ts": datetime.now().isoformat(), "stages": {}}

        for stage in stages:
            stage_dir = pipeline_dir / stage
            stage_state = state["stages"].get(stage, {"ok": True, "failures": 0, "last_ok": None})

            if stage_dir.exists():
                error_files = sorted(stage_dir.glob("*.error"))
                pending_files = sorted(stage_dir.glob("*"))

                if error_files:
                    stage_state["ok"] = False
                    stage_state["failures"] += 1
                    stage_state["last_error"] = str(error_files[-1])
                    stage_state["error_count"] = len(error_files)

                    if stage_state["failures"] >= max_failures_before_alert:
                        alert = {"stage": stage, "error": stage_state["last_error"],
                                 "consecutive_failures": stage_state["failures"],
                                 "ts": datetime.now().isoformat()}
                        alerts.append(alert)
                        _alert_pipeline_failure(stage, stage_state["last_error"], "critical")
                elif pending_files:
                    stage_state["ok"] = True
                    stage_state["pending"] = len(pending_files)
                else:
                    stage_state["ok"] = True
                    stage_state["pending"] = 0
            else:
                stage_state["ok"] = False
                stage_state["missing"] = True
                stage_state["failures"] += 1

                if stage_state["failures"] >= max_failures_before_alert:
                    alert = {"stage": stage, "error": "目录缺失",
                             "consecutive_failures": stage_state["failures"],
                             "ts": datetime.now().isoformat()}
                    alerts.append(alert)
                    _alert_pipeline_failure(stage, "目录缺失", "critical")

            state["stages"][stage] = stage_state
            check_result["stages"][stage] = {
                "ok": stage_state["ok"],
                "pending": stage_state.get("pending", 0),
                "failures": stage_state.get("failures", 0),
                "errors": stage_state.get("error_count", 0),
            }

        _save_pipeline_state(state)
        time.sleep(check_interval)

    return {"ok": True, "pipeline_dir": str(pipeline_dir), "total_rounds": round_num,
            "total_alerts": len(alerts), "stages_summary": check_result.get("stages", {}),
            "alerts": alerts[-10:]}

HANDLERS = {"read": do_read, "analyze": do_analyze, "clean": do_clean,
            "export": do_export, "query": do_query,
            "auto_etl": do_auto_etl, "pipeline_watch": do_pipeline_watch}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "read"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
