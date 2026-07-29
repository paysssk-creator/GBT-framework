# 开发者：自由的风
'''dev_gpu/run.py — GPU实时状态传感器'''
import sys, json, subprocess

def do_status(params):
    gpus = []
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                          capture_output=True, text=True, timeout=5)
        for line in r.stdout.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpus.append({
                    "name": parts[0], "temp_c": int(parts[1]) if parts[1].isdigit() else 0,
                    "utilization_percent": int(parts[2]) if parts[2].isdigit() else 0,
                    "vram_used_mb": int(parts[3]) if parts[3].isdigit() else 0,
                    "vram_total_mb": int(parts[4]) if parts[4].isdigit() else 0,
                })
    except Exception:
        gpus = [{"note": "nvidia-smi不可用或无NVIDIA GPU"}]
    return {
        "ok": True, "cap": "dev_gpu", "action": "status", "domain": "设备感知层",
        "gpus": gpus, "gpu_count": len(gpus),
    }

HANDLERS = {"status": do_status}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
