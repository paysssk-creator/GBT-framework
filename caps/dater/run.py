# 开发者：自由的风
'''dater/run.py — 数据处理工具箱：CSV↔JSON / 分析 / 过滤 / 排序 / 合并'''
import sys, json, csv, io, math, statistics
from pathlib import Path

# ═══════════════════ 1. csv2json: CSV → JSON ═══════════════════
def do_csv2json(params: dict) -> dict:
    """CSV 文本转 JSON 数组"""
    csv_text = params.get("csv", params.get("text", params.get("data", "")))
    if not csv_text:
        return {"ok": False, "error": "缺少 csv 参数"}
    try:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        rows = [row for row in reader]
        return {"ok": True, "count": len(rows), "data": rows}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════ 2. json2csv: JSON → CSV ═══════════════════
def do_json2csv(params: dict) -> dict:
    """JSON 数组转 CSV 文本"""
    data = params.get("json", params.get("data", []))
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return {"ok": False, "error": "JSON 解析失败"}
    if not isinstance(data, list) or len(data) == 0:
        return {"ok": False, "error": "数据为空或不是数组"}
    if not all(isinstance(r, dict) for r in data):
        return {"ok": False, "error": "数组元素必须都是对象"}
    try:
        headers = list(data[0].keys())
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        return {"ok": True, "csv": buf.getvalue()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════ 3. analyze: 统计分析 ═══════════════════
def do_analyze(params: dict) -> dict:
    """对数值数组做统计分析：均值 / 中位数 / 最大最小 / 标准差"""
    data = params.get("data", params.get("numbers", []))
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return {"ok": False, "error": "JSON 解析失败"}
    if not isinstance(data, list) or len(data) == 0:
        return {"ok": False, "error": "数据为空或不是数组"}
    try:
        nums = [float(x) for x in data]
    except (ValueError, TypeError):
        return {"ok": False, "error": "数组元素必须都是数值"}
    n = len(nums)
    total = sum(nums)
    mean = total / n
    nums_sorted = sorted(nums)
    if n % 2 == 0:
        median = (nums_sorted[n // 2 - 1] + nums_sorted[n // 2]) / 2
    else:
        median = nums_sorted[n // 2]
    variance = sum((x - mean) ** 2 for x in nums) / n
    stddev = math.sqrt(variance)
    return {
        "ok": True,
        "count": n,
        "sum": round(total, 6),
        "mean": round(mean, 6),
        "median": round(median, 6),
        "min": round(nums_sorted[0], 6),
        "max": round(nums_sorted[-1], 6),
        "stddev": round(stddev, 6),
    }

# ═══════════════════ 4. filter: 数据过滤 ═══════════════════
def _match_value(val, op, target):
    """单值条件匹配"""
    if op == "eq":
        return val == target
    elif op == "ne":
        return val != target
    elif op == "gt":
        try:
            return float(val) > float(target)
        except (ValueError, TypeError):
            return str(val) > str(target)
    elif op == "lt":
        try:
            return float(val) < float(target)
        except (ValueError, TypeError):
            return str(val) < str(target)
    elif op == "gte":
        try:
            return float(val) >= float(target)
        except (ValueError, TypeError):
            return str(val) >= str(target)
    elif op == "lte":
        try:
            return float(val) <= float(target)
        except (ValueError, TypeError):
            return str(val) <= str(target)
    elif op == "contains":
        return target in str(val)
    elif op == "startswith":
        return str(val).startswith(str(target))
    elif op == "endswith":
        return str(val).endswith(str(target))
    elif op == "in":
        return val in target if isinstance(target, list) else val == target
    return False

def do_filter(params: dict) -> dict:
    """按条件筛选行"""
    data = params.get("data", [])
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return {"ok": False, "error": "JSON 解析失败"}
    if not isinstance(data, list):
        return {"ok": False, "error": "data 必须是数组"}
    conditions = params.get("conditions", params.get("cond", []))
    if not conditions:
        return {"ok": False, "error": "缺少 conditions 参数"}
    logic = params.get("logic", "and").lower()
    result = []
    for row in data:
        if isinstance(row, dict):
            matches = []
            for cond in conditions:
                field = cond.get("field", cond.get("key", ""))
                op = cond.get("op", "eq")
                value = cond.get("value", cond.get("val"))
                match = _match_value(row.get(field), op, value)
                matches.append(match)
            if logic == "and":
                if all(matches):
                    result.append(row)
            else:  # or
                if any(matches):
                    result.append(row)
        else:
            # 标量数组 → 按值过滤
            for cond in conditions:
                op = cond.get("op", "eq")
                value = cond.get("value", cond.get("val"))
                if _match_value(row, op, value):
                    result.append(row)
                    break
    return {"ok": True, "count": len(result), "data": result}

# ═══════════════════ 5. sort: 数据排序 ═══════════════════
def do_sort(params: dict) -> dict:
    """数据排序"""
    data = params.get("data", [])
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return {"ok": False, "error": "JSON 解析失败"}
    if not isinstance(data, list):
        return {"ok": False, "error": "data 必须是数组"}
    by = params.get("by", params.get("field", params.get("key", None)))
    order = params.get("order", "asc").lower()
    reverse = order == "desc"
    try:
        if by and len(data) > 0 and isinstance(data[0], dict):
            result = sorted(data, key=lambda r: r.get(by, ""), reverse=reverse)
        else:
            result = sorted(data, reverse=reverse)
        return {"ok": True, "count": len(result), "data": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════ 6. merge: 合并两个数据源 ═══════════════════
def do_merge(params: dict) -> dict:
    """合并两个数据源"""
    left = params.get("left", params.get("data_a", []))
    right = params.get("right", params.get("data_b", []))
    if isinstance(left, str):
        try:
            left = json.loads(left)
        except Exception:
            return {"ok": False, "error": "left JSON 解析失败"}
    if isinstance(right, str):
        try:
            right = json.loads(right)
        except Exception:
            return {"ok": False, "error": "right JSON 解析失败"}
    if not isinstance(left, list):
        return {"ok": False, "error": "left 必须是数组"}
    if not isinstance(right, list):
        return {"ok": False, "error": "right 必须是数组"}
    mode = params.get("mode", "concat").lower()
    on = params.get("on", params.get("key", "id"))
    try:
        if mode == "concat":
            result = left + right
        elif mode == "inner":
            right_index = {r.get(on): r for r in right if isinstance(r, dict)}
            result = []
            for l in left:
                if isinstance(l, dict) and l.get(on) in right_index:
                    merged = dict(l)
                    merged.update(right_index[l[on]])
                    result.append(merged)
        elif mode == "left":
            right_index = {r.get(on): r for r in right if isinstance(r, dict)}
            result = []
            for l in left:
                if isinstance(l, dict):
                    merged = dict(l)
                    if l.get(on) in right_index:
                        merged.update(right_index[l[on]])
                    result.append(merged)
                else:
                    result.append(l)
        elif mode == "append":
            # 按索引追加字段：right 的字段加到 left 对应行
            result = []
            for i, l in enumerate(left):
                if isinstance(l, dict):
                    row = dict(l)
                    if i < len(right) and isinstance(right[i], dict):
                        row.update(right[i])
                    result.append(row)
                else:
                    result.append(l)
        else:
            return {"ok": False, "error": f"不支持的合并模式: {mode}"}
        return {"ok": True, "count": len(result), "data": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════ Handler 注册 ═══════════════════
HANDLERS = {
    "csv2json": do_csv2json,
    "json2csv": do_json2csv,
    "analyze":  do_analyze,
    "filter":   do_filter,
    "sort":     do_sort,
    "merge":    do_merge,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
    else:
        result = {
            "ok": False,
            "error": f"未知动作: {action}",
            "available": list(HANDLERS.keys()),
        }
    print(json.dumps(result, ensure_ascii=False, default=str))
