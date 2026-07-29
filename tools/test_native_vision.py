import subprocess, json, sys, os
os.chdir("C:/Users/ADMIN/GBTxiaotudouV5")
runpy = "caps/native_vision/run.py"

entries = [
    ("1. see", ["see"]),
    ("2. read_all", ["read_all"]),
    ("3. find Windows", ["find", '{"text":"Windows"}']),
    ("4. click", ["click", '{"x":100,"y":100}']),
    ("5. type", ["type", '{"text":"test"}']),
    ("6. press", ["press", '{"key":"escape"}']),
    ("7. hotkey", ["hotkey", '{"keys":["ctrl","c"]}']),
    ("8. movie", ["movie", '{"duration":1,"fps":3}']),
    ("9. start_watching", ["start_watching", '{"fps":10}']),
    ("10. latest", ["latest"]),
    ("11. wait_for_stable", ["wait_for_stable", '{"timeout":2}']),
    ("12. browse_scroll", ["browse_scroll", '{"direction":"down","amount":1}']),
    ("13. look_and_click", ["look_and_click", '{"text":"test","timeout":2}']),
    ("14. unknown", ["unknown_action"]),
]
passed = 0
failed = 0
results = []
for name, args in entries:
    try:
        r = subprocess.run([sys.executable, runpy] + args, capture_output=True, text=True, timeout=30)
        out = r.stdout.strip()
        err = r.stderr.strip()
        if out:
            data = json.loads(out)
            results.append({"test": name, "status": "PASS", "output": {k:v for k,v in data.items() if k != "image"}})
            passed += 1
        elif err:
            results.append({"test": name, "status": "FAIL", "error": err[:300]})
            failed += 1
        else:
            results.append({"test": name, "status": "FAIL", "error": "no output"})
            failed += 1
    except subprocess.TimeoutExpired:
        results.append({"test": name, "status": "TIMEOUT", "error": "30s timeout"})
        failed += 1
    except Exception as e:
        results.append({"test": name, "status": "ERROR", "error": str(e)[:200]})
        failed += 1
print(json.dumps({"passed": passed, "failed": failed, "results": results}, ensure_ascii=False, indent=2))
