# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""数据库 — SQLite 查询/执行/表列表/备份"""
import sys, json, sqlite3, os, shutil

DB_PATH = os.path.expandvars(os.path.expanduser(r'~/.gbt/data/gbt.db'))

def _ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def do_query(params):
    sql = params.get('sql', '')
    if not sql.strip().upper().startswith('SELECT'):
        return {"ok": False, "error": "仅允许 SELECT 查询"}
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(r) for r in cur.fetchall()]
        return {"ok": True, "columns": columns, "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()

def do_execute(params):
    sql = params.get('sql', '')
    upper = sql.strip().upper()
    if not (upper.startswith('INSERT') or upper.startswith('UPDATE') or upper.startswith('DELETE')
            or upper.startswith('CREATE') or upper.startswith('DROP') or upper.startswith('ALTER')):
        return {"ok": False, "error": "仅允许 INSERT/UPDATE/DELETE/CREATE/DROP/ALTER"}
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(sql)
        conn.commit()
        return {"ok": True, "affected": cur.rowcount}
    except Exception as e:
        conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()

def do_tables(params):
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = []
        for row in cur.fetchall():
            name = row[0]
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
            tables.append({"name": name, "rows": cnt})
        return {"ok": True, "tables": tables}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()

def do_backup(params):
    dest = params.get('dest', '')
    if not dest:
        return {"ok": False, "error": "缺少 dest 路径"}
    _ensure_db()
    if not os.path.exists(DB_PATH):
        return {"ok": False, "error": "数据库文件不存在，无备份内容"}
    try:
        os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
        shutil.copy2(DB_PATH, dest)
        size_kb = round(os.path.getsize(dest) / 1024, 1)
        return {"ok": True, "source": DB_PATH, "dest": os.path.abspath(dest), "size_kb": size_kb}
    except Exception as e:
        return {"ok": False, "error": str(e)}

handlers = {'query': do_query, 'execute': do_execute, 'tables': do_tables, 'backup': do_backup}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "query"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = handlers.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(handlers.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
