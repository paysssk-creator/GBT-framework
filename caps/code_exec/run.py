# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""代码执行 — 运行Python/Shell代码"""
import sys, json, subprocess

def do_run(params):
    code = params.get('code', '')
    lang = params.get('lang', 'python')
    try:
        if lang == 'python':
            r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
        else:
            r = subprocess.run(code, shell=False, capture_output=True, text=True, timeout=30)
        return {"ok": r.returncode==0, "stdout": r.stdout[:5000], "stderr": r.stderr[:1000]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "执行超时(30s)"}

handlers = {'run': do_run}
if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv)>1 else 'run'
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = handlers.get(action, lambda p: {"ok":False,"error":f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False))
