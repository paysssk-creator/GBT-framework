# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""system_backup/run.py — 系统备份恢复 v1.0
===========================================
备份存储于 ~/.gbt/backups/gbt_backup_YYYYMMDD_HHMMSS_ffffff.zip
"""
import sys, json, os, zipfile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
GBT_HOME = Path.home() / ".gbt"
BACKUP_DIR = GBT_HOME / "backups"

def do_backup(params=None):
    """zip entire ~/.gbt/ directory + caps/ directory"""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        zip_name = f"gbt_backup_{timestamp}.zip"
        zip_path = BACKUP_DIR / zip_name

        file_count = 0
        total_bytes = 0
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Backup ~/.gbt/ (exclude backups dir to avoid recursion)
            if GBT_HOME.exists():
                for fp in GBT_HOME.rglob('*'):
                    if fp.is_file() and 'backups' not in fp.parts:
                        arcname = str(fp.relative_to(GBT_HOME.parent))
                        zf.write(fp, arcname)
                        file_count += 1
                        total_bytes += fp.stat().st_size
            # Backup caps/
            caps_dir = ROOT / "caps"
            if caps_dir.exists():
                for fp in caps_dir.rglob('*'):
                    if fp.is_file() and '__pycache__' not in fp.parts:
                        arcname = str(fp.relative_to(ROOT))
                        zf.write(fp, arcname)
                        file_count += 1
                        total_bytes += fp.stat().st_size

        zip_size = zip_path.stat().st_size
        return {
            "ok": True, "backup": zip_name, "path": str(zip_path),
            "zip_size": zip_size, "file_count": file_count,
            "total_bytes": total_bytes, "timestamp": timestamp,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_restore(params):
    """restore from a backup zip"""
    backup_name = params.get("backup", params.get("name", "")) if params else ""
    if not backup_name:
        return {"ok": False, "error": "缺少backup名称"}

    if os.path.isabs(backup_name):
        zip_path = Path(backup_name)
    else:
        zip_path = BACKUP_DIR / backup_name

    if not zip_path.exists():
        avail = sorted(BACKUP_DIR.glob("gbt_backup_*.zip")) if BACKUP_DIR.exists() else []
        return {"ok": False, "error": f"备份不存在: {backup_name}",
                "available": [b.name for b in avail]}

    try:
        restored = 0
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.namelist():
                if member.startswith("caps/"):
                    target = ROOT / member
                else:
                    target = GBT_HOME.parent / member

                if member.endswith('/'):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src:
                        target.write_bytes(src.read())
                restored += 1

        return {"ok": True, "restored": zip_path.name, "files_restored": restored}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_list(params=None):
    """list available backups"""
    try:
        if not BACKUP_DIR.exists():
            return {"ok": True, "backups": [], "count": 0, "dir": str(BACKUP_DIR)}

        backups = []
        for bp in sorted(BACKUP_DIR.glob("gbt_backup_*.zip"),
                         key=lambda p: p.stat().st_mtime, reverse=True):
            backups.append({
                "name": bp.name,
                "size": bp.stat().st_size,
                "modified": datetime.fromtimestamp(bp.stat().st_mtime).isoformat(),
            })

        return {"ok": True, "backups": backups, "count": len(backups),
                "dir": str(BACKUP_DIR)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_cleanup(params):
    """keep last N backups, delete older ones"""
    keep = int((params or {}).get("keep", (params or {}).get("n", 5)))
    try:
        if not BACKUP_DIR.exists():
            return {"ok": True, "deleted": [], "kept": [], "message": "无备份目录"}

        all_bps = sorted(BACKUP_DIR.glob("gbt_backup_*.zip"),
                         key=lambda p: p.stat().st_mtime, reverse=True)
        kept, deleted = all_bps[:keep], all_bps[keep:]

        for dp in deleted:
            dp.unlink()

        return {
            "ok": True,
            "kept": [p.name for p in kept],
            "deleted": [p.name for p in deleted],
            "total_before": len(all_bps),
            "total_after": len(kept),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_auto_backup_cycle(params):
    """periodic auto-backup: ~/.gbt/, caps/capability.json, brain/*.py — keep last N"""
    keep = int((params or {}).get("keep", 10))
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        zip_name = f"gbt_auto_{timestamp}.zip"
        zip_path = BACKUP_DIR / zip_name

        file_count = 0
        total_bytes = 0
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1) ~/.gbt/ — all memory/evolve/sessions, exclude backups and temp
            if GBT_HOME.exists():
                for fp in GBT_HOME.rglob('*'):
                    if fp.is_file() and 'backups' not in fp.parts and '__pycache__' not in fp.parts:
                        skip_suffixes = ('.session', '.journal')
                        if fp.name.endswith(skip_suffixes):
                            continue
                        arcname = "gbt/" + str(fp.relative_to(GBT_HOME))
                        zf.write(fp, arcname)
                        file_count += 1
                        total_bytes += fp.stat().st_size
            # 2) caps/ directory listing + capability.json files
            caps_dir = ROOT / "caps"
            if caps_dir.exists():
                # Directory listing
                cap_list = []
                for d in sorted(caps_dir.iterdir()):
                    if d.is_dir():
                        cap_json = d / "capability.json"
                        cap_list.append({
                            "dir": d.name,
                            "has_capability_json": cap_json.exists(),
                            "capability_json_size": cap_json.stat().st_size if cap_json.exists() else 0,
                        })
                listing_path = BACKUP_DIR / f"_caps_listing_{timestamp}.json"
                listing_path.write_text(json.dumps(cap_list, indent=2, ensure_ascii=False), encoding="utf-8")
                # Add listing to zip
                zf.write(listing_path, f"caps_listing_{timestamp}.json")
                listing_path.unlink()  # cleanup temp
                file_count += 1
                # capability.json files
                for cap_json in caps_dir.rglob("capability.json"):
                    arcname = str(cap_json.relative_to(ROOT))
                    zf.write(cap_json, arcname)
                    file_count += 1
                    total_bytes += cap_json.stat().st_size
            # 3) brain/ Python files
            brain_dir = ROOT / "brain"
            if brain_dir.exists():
                for fp in brain_dir.rglob("*.py"):
                    if '__pycache__' not in fp.parts:
                        arcname = str(fp.relative_to(ROOT))
                        zf.write(fp, arcname)
                        file_count += 1
                        total_bytes += fp.stat().st_size

        zip_size = zip_path.stat().st_size
        # Cleanup: keep last N
        cleanup_result = do_cleanup({"keep": keep})
        return {
            "ok": True, "backup": zip_name, "path": str(zip_path),
            "zip_size": zip_size, "file_count": file_count,
            "total_bytes": total_bytes, "timestamp": timestamp,
            "cleanup": cleanup_result,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_backup_on_change(params):
    """one-shot change detector: compare ~/.gbt/ mtimes vs snapshot, backup if changed"""
    snapshot_file = BACKUP_DIR / ".change_snapshot.json"
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        # Scan current state
        current = {}
        changed = []
        added = []
        removed = []
        if GBT_HOME.exists():
            for fp in GBT_HOME.rglob('*'):
                if fp.is_file() and 'backups' not in fp.parts and '__pycache__' not in fp.parts:
                    rel = str(fp.relative_to(GBT_HOME))
                    current[rel] = {"mtime": fp.stat().st_mtime, "size": fp.stat().st_size}

        # Load previous snapshot
        prev = {}
        if snapshot_file.exists():
            try:
                prev = json.loads(snapshot_file.read_text(encoding="utf-8"))
            except Exception:
                prev = {}

        # Diff
        prev_keys = set(prev.keys())
        curr_keys = set(current.keys())
        added_keys = curr_keys - prev_keys
        removed_keys = prev_keys - curr_keys

        for k in curr_keys & prev_keys:
            if current[k]["mtime"] != prev[k]["mtime"] or current[k]["size"] != prev[k]["size"]:
                changed.append(k)

        added = sorted(added_keys)
        removed = sorted(removed_keys)
        has_changes = bool(changed or added or removed)

        # Save new snapshot
        snapshot_file.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")

        # Trigger backup if changed
        backup_result = None
        if has_changes:
            backup_result = do_backup({})

        return {
            "ok": True,
            "has_changes": has_changes,
            "changed": changed[:50],
            "added": added[:50],
            "removed": removed[:50],
            "total_changes": len(changed) + len(added) + len(removed),
            "backup_triggered": backup_result["ok"] if backup_result else False,
            "backup": backup_result.get("backup") if backup_result else None,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}




def do_list_ops(params=None):
    """list supported operations"""
    return {
        "ok": True,
        "action": "list",
        "operations": [
            "backup",
            "restore",
            "list_files",
            "cleanup",
            "auto_backup_cycle",
            "backup_on_change",
            "list",
            "self_test",
            "help",
        ],
        "description": "系统备份恢复 — 备份/恢复/列表/清理/自动备份/变更检测",
    }


def do_self_test(params=None):
    """check backup directory permissions"""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        test_file = BACKUP_DIR / ".self_test_write"
        test_file.write_text("test")
        test_file.unlink()
        return {
            "ok": True,
            "action": "self_test",
            "message": "备份目录权限正常",
            "backup_dir": str(BACKUP_DIR),
        }
    except Exception as e:
        return {
            "ok": False,
            "action": "self_test",
            "error": str(e)[:200],
            "backup_dir": str(BACKUP_DIR),
        }


do_help = do_list_ops  # help 同 list
HANDLERS = {
    "backup": do_backup, "restore": do_restore,
    "list_files": do_list, "cleanup": do_cleanup,
    "run": do_backup,
    "auto_backup_cycle": do_auto_backup_cycle,
    "backup_on_change": do_backup_on_change,
    "list": do_list_ops,
    "self_test": do_self_test,
    "help": do_help,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "backup"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
