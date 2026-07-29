# 开发者：自由的风
"""migration/run.py — 数据库迁移·schema版本管理
===============================================
基础设施 — 管理 gbt.db schema 版本，支持迁移/回滚/状态查询。
迁移文件存放在 ~/.gbt/migrations/ 目录，按时间戳排序。
"""
import sys, json, os, re, sqlite3, time
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.expandvars(os.path.expanduser(r"~/.gbt/data/gbt.db"))
MIG_DIR = Path.home() / ".gbt" / "migrations"

TABLE_SQL = """CREATE TABLE IF NOT EXISTS _migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    batch INTEGER NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
)"""


def _ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    MIG_DIR.mkdir(parents=True, exist_ok=True)


def _get_conn():
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def do_init(params):
    """初始化迁移表"""
    conn = _get_conn()
    try:
        conn.execute(TABLE_SQL)
        conn.commit()
        cur = conn.execute("SELECT COUNT(*) as n FROM _migrations")
        count = cur.fetchone()["n"]
        return {"ok": True, "message": "迁移表已就绪", "existing_migrations": count}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def do_create(params):
    """创建新迁移文件"""
    name = (params.get("name") or "").strip()
    if not name:
        return {"ok": False, "error": "缺少 name 参数 — 迁移名称"}
    safe_name = re.sub(r"[^\w\-]", "_", name)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{safe_name}.sql"
    filepath = MIG_DIR / filename
    _ensure_db()
    content = params.get("sql", params.get("content", f"-- migration: {name}\n"))
    try:
        filepath.write_text(content, encoding="utf-8")
        return {"ok": True, "migration": filename, "path": str(filepath)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def do_migrate(params):
    """运行所有待处理的迁移"""
    conn = _get_conn()
    try:
        conn.execute(TABLE_SQL)
        conn.commit()
        cur = conn.execute("SELECT name FROM _migrations ORDER BY id")
        applied = {r["name"] for r in cur.fetchall()}
        cur = conn.execute("SELECT COALESCE(MAX(batch), 0) as mx FROM _migrations")
        batch = cur.fetchone()["mx"] + 1

        mig_files = sorted(MIG_DIR.glob("*.sql"))
        pending = [f for f in mig_files if f.name not in applied]
        if not pending:
            return {"ok": True, "message": "无待处理迁移", "applied": len(applied), "pending": 0}

        results = []
        for mf in pending:
            sql = mf.read_text(encoding="utf-8")
            try:
                conn.executescript(sql)
                conn.execute("INSERT INTO _migrations (name, batch) VALUES (?, ?)", (mf.name, batch))
                conn.commit()
                results.append({"name": mf.name, "status": "ok"})
            except Exception as e:
                conn.rollback()
                results.append({"name": mf.name, "status": "fail", "error": str(e)})
                break  # 失败则停止，保护数据库状态

        ok_count = sum(1 for r in results if r["status"] == "ok")
        fail_count = len(results) - ok_count
        return {"ok": fail_count == 0, "batch": batch, "applied": ok_count,
                "failed": fail_count, "results": results}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def do_rollback(params):
    """回滚最近一个batch的迁移"""
    conn = _get_conn()
    try:
        conn.execute(TABLE_SQL)
        cur = conn.execute("SELECT COALESCE(MAX(batch), 0) as mx FROM _migrations")
        max_batch = cur.fetchone()["mx"]
        if max_batch == 0:
            return {"ok": False, "error": "无可回滚的迁移"}
        cur = conn.execute("SELECT name FROM _migrations WHERE batch = ? ORDER BY id DESC", (max_batch,))
        names = [r["name"] for r in cur.fetchall()]
        conn.execute("DELETE FROM _migrations WHERE batch = ?", (max_batch,))
        conn.commit()
        return {"ok": True, "rollback_batch": max_batch, "reverted": names,
                "message": f"已回滚 batch {max_batch}，共 {len(names)} 条迁移。注意：需要手动编写回滚SQL来恢复schema。"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def do_status(params):
    """查看迁移状态"""
    conn = _get_conn()
    try:
        conn.execute(TABLE_SQL)
        cur = conn.execute("SELECT name, batch, applied_at FROM _migrations ORDER BY id")
        applied = [dict(r) for r in cur.fetchall()]
        mig_files = sorted(MIG_DIR.glob("*.sql"))
        applied_names = {r["name"] for r in applied}
        pending = [f.name for f in mig_files if f.name not in applied_names]
        latest_batch = applied[-1]["batch"] if applied else 0
        return {"ok": True, "applied": len(applied), "pending": len(pending),
                "latest_batch": latest_batch, "applied_list": applied,
                "pending_list": pending}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


SCHEMA_REGISTRY = {
    "project_registry.json": {
        "version": "projects",
    },
    "plugins_state.json": {
        "enabled": {},
        "disabled": [],
    },
    "breakers.json": {
        "circuits": {},
    },
    "browser_state.json": {
        "tabs": [],
        "active": None,
    },
}

GBT_HOME = Path.home() / ".gbt"


def do_auto_migrate(params):
    """detect schema drift across ~/.gbt/ JSON files and auto-migrate"""
    dry_run = (params or {}).get("dry_run", False)
    try:
        results = []
        migrated = 0
        if not GBT_HOME.exists():
            return {"ok": True, "message": "~/.gbt/ 不存在", "results": [], "migrated": 0}

        for fp in sorted(GBT_HOME.rglob("*.json")):
            if 'backups' in fp.parts or '__pycache__' in fp.parts:
                continue
            rel = str(fp.relative_to(GBT_HOME))
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                results.append({"file": rel, "status": "skip_broken", "error": str(e)[:100]})
                continue

            schema = SCHEMA_REGISTRY.get(fp.name)
            if schema is None:
                results.append({"file": rel, "status": "no_schema", "note": "无注册schema，跳过"})
                continue

            if not isinstance(data, dict):
                results.append({"file": rel, "status": "skip_non_dict", "type": type(data).__name__})
                continue

            # Detect missing keys and add with default values
            added = {}
            for key, default in schema.items():
                if key not in data:
                    added[key] = default
                    data[key] = default

            if added:
                if not dry_run:
                    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                migrated += 1
                results.append({"file": rel, "status": "migrated", "added_keys": list(added.keys())})
            else:
                results.append({"file": rel, "status": "uptodate"})

        return {
            "ok": True,
            "dry_run": dry_run,
            "total_scanned": len(results),
            "migrated": migrated,
            "results": results,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_validate_schemas(params):
    """check all JSON files in ~/.gbt/ for structural integrity"""
    try:
        valid = []
        broken = []
        empty_files = []
        if not GBT_HOME.exists():
            return {"ok": True, "message": "~/.gbt/ 不存在", "valid": 0, "broken": 0}

        for fp in sorted(GBT_HOME.rglob("*.json")):
            if 'backups' in fp.parts or '__pycache__' in fp.parts:
                continue
            rel = str(fp.relative_to(GBT_HOME))
            size = fp.stat().st_size
            if size == 0:
                empty_files.append({"file": rel, "size": 0})
                continue
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                valid.append({
                    "file": rel,
                    "size": size,
                    "type": type(data).__name__,
                    "keys": sorted(data.keys()) if isinstance(data, dict) else None,
                    "len": len(data) if isinstance(data, (list, dict)) else None,
                })
            except json.JSONDecodeError as e:
                broken.append({"file": rel, "size": size, "error": str(e)[:150]})
            except UnicodeDecodeError as e:
                broken.append({"file": rel, "size": size, "error": f"编码错误: {e}"})
            except Exception as e:
                broken.append({"file": rel, "size": size, "error": str(e)[:100]})

        return {
            "ok": len(broken) == 0,
            "total": len(valid) + len(broken) + len(empty_files),
            "valid_count": len(valid),
            "broken_count": len(broken),
            "empty_count": len(empty_files),
            "valid": valid,
            "broken": broken,
            "empty_files": empty_files,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


HANDLERS = {"init": do_init, "create": do_create, "migrate": do_migrate,
            "rollback": do_rollback, "status": do_status,
            "auto_migrate": do_auto_migrate,
            "validate_schemas": do_validate_schemas}

if __name__ == "__main__":
    import re
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except:
            params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}",
                                          "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
