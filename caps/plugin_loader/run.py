# 开发者：自由的风
"""plugin_loader/run.py — 插件加载器·cap插件生命周期管理
=========================================================
基础设施 — 扫描 caps/ 目录，读取 plugin.json 清单，管理加载/卸载/重载。
已加载插件驻留在内存字典中；卸载仅从热注册中移除，不删除文件。
"""
import sys, json, os, importlib.util
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS_DIR = Path(SANDBOX)
STATE_FILE = Path.home() / ".gbt" / "plugins_state.json"

# 已加载插件注册表: {name: {"path": str, "manifest": dict, "module": module|None}}
_loaded = {}


def _restore_state():
    global _loaded
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            _loaded = {k: {"path": v["path"], "manifest": v.get("manifest", {}), "module": None}
                       for k, v in data.items()}
        except:
            _loaded = {}


def _save_state():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {k: {"path": v["path"], "manifest": v["manifest"]} for k, v in _loaded.items()}
    STATE_FILE.write_text(json.dumps(payload, indent=2, default=str))


def _scan_caps():
    """扫描 caps/ 目录，返回带 plugin.json 的插件列表"""
    plugins = []
    for entry in sorted(CAPS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("_") or entry.name.startswith("__"):
            continue
        cap_json = entry / "capability.json"
        plugin_json = entry / "plugin.json"
        if not cap_json.exists():
            continue
        try:
            cap_data = json.loads(cap_json.read_text(encoding="utf-8"))
        except:
            cap_data = {}
        manifest = {}
        if plugin_json.exists():
            try:
                manifest = json.loads(plugin_json.read_text(encoding="utf-8"))
            except:
                manifest = {}
        plugins.append({
            "name": entry.name,
            "path": str(entry),
            "capability": cap_data,
            "manifest": manifest,
            "loaded": entry.name in _loaded
        })
    return plugins


def do_list(params):
    """列出所有可发现插件"""
    _restore_state()
    plugins = _scan_caps()
    loaded_count = sum(1 for p in plugins if p["loaded"])
    return {"ok": True, "total": len(plugins), "loaded": loaded_count,
            "plugins": plugins}


def do_load(params):
    """加载指定插件到注册表"""
    name = (params.get("name") or params.get("plugin") or "").strip()
    if not name:
        return {"ok": False, "error": "缺少 name 参数 — 插件名称"}
    _restore_state()
    cap_dir = CAPS_DIR / name
    if not cap_dir.is_dir():
        return {"ok": False, "error": f"插件目录不存在: {name}"}
    cap_json = cap_dir / "capability.json"
    if not cap_json.exists():
        return {"ok": False, "error": f"缺少 capability.json: {name}"}
    plugin_json = cap_dir / "plugin.json"
    manifest = {}
    if plugin_json.exists():
        try:
            manifest = json.loads(plugin_json.read_text(encoding="utf-8"))
        except:
            manifest = {}
    try:
        cap_data = json.loads(cap_json.read_text(encoding="utf-8"))
    except:
        cap_data = {}
    _loaded[name] = {"path": str(cap_dir), "manifest": manifest, "module": None}
    _save_state()
    return {"ok": True, "name": name, "action": "loaded",
            "manifest": manifest, "capability": cap_data}


def do_unload(params):
    """卸载插件 — 从注册表中移除"""
    name = (params.get("name") or params.get("plugin") or "").strip()
    if not name:
        return {"ok": False, "error": "缺少 name 参数 — 插件名称"}
    _restore_state()
    if name not in _loaded:
        return {"ok": False, "error": f"插件未加载: {name}"}
    del _loaded[name]
    _save_state()
    return {"ok": True, "name": name, "action": "unloaded"}


def do_reload(params):
    """重载所有已加载插件 — 重新扫描并重新注册"""
    _restore_state()
    previously = set(_loaded.keys())
    # 重新扫描
    all_plugins = _scan_caps()
    _loaded.clear()
    reloaded = []
    skipped = []
    for p in all_plugins:
        if p["name"] in previously:
            _loaded[p["name"]] = {"path": p["path"], "manifest": p["manifest"], "module": None}
            reloaded.append(p["name"])
        else:
            skipped.append(p["name"])
    _save_state()
    return {"ok": True, "reloaded": len(reloaded), "skipped": len(skipped),
            "reloaded_list": reloaded}


HANDLERS = {"list": do_list, "load": do_load, "unload": do_unload, "reload": do_reload}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except:
            params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}",
                                          "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
