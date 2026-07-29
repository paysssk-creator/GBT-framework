# -*- coding: utf-8 -*-
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
gbt.py -- GBTxiaotudouV5 统一启动入口
=====================================
用法:
  python gbt.py chat        同上
  python gbt.py daemon      自主守护(每日自动吞噬+邻域监控+触手脉冲)
  python gbt.py ask "问题"  单次问答
  python gbt.py scan        邻域穿透扫描(L0~L7运行时穿透)
  python gbt.py tentacle    神经触手持续监控(--watch 30)
  python gbt.py see         视觉邻域: 截图+OCR+皮层分析
  python gbt.py status      系统状态
"""
import sys, os, json
try:
    import readline
except ImportError:
    import pyreadline3 as readline
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def cmd_boot():
    from brain.boot import boot
    result = boot()
    if result["ok"]:
        print("="*50)
        for layer in result["layers"]:
            status = "OK" if layer["ok"] else "FAIL"
            print(f"  [{status}] {layer['name']}")
            for c in layer.get("checks", []):
                cstatus = "OK" if c["ok"] else f"FAIL - {c.get('detail','')}"
                print(f"    {c['component']}: {cstatus}")
        print("="*50)
    print("\nReady. Run: python gbt.py chat")

def cmd_chat():
    from brain.chain_kernel import enforce_chain
    enforce_chain("gbt.chat")
    import subprocess
    subprocess.run([sys.executable, "gbt_tui.py"] + sys.argv[2:], cwd=os.path.dirname(__file__))

def cmd_ask():
    from brain.chain_kernel import enforce_chain
    enforce_chain("gbt.ask")
    if len(sys.argv) < 3:
        print("Usage: python gbt.py ask \"your question\"")
        return
    from brain.deep_reasoner import get_reasoner
    r = get_reasoner().think(sys.argv[2])
    print(f"GBT: {r.get('direction','')}\n   {r.get('rationale','')[:300]}")

def cmd_scan():
    from brain.chain_kernel import enforce_chain
    enforce_chain("gbt.scan")
    from brain.nexus import penetration_scan
    r = penetration_scan(auto_fix=True)
    print(f"\n{'='*50}")
    status = "ALL CLEAN" if r["ok"] else "ISSUES FOUND"
    print(f"  Penetration Scan: {status}")
    print(f"  {r['elapsed_ms']}ms | {r['total_issues']} issues | auto-fix {r['fixes_applied']}")
    for name, layer in r.get("layers", {}).items():
        icon = "OK" if layer["ok"] else "FAIL"
        print(f"  [{icon}] {name}: {layer['issues']} issues ({layer['errors']} errors)")
    print(f"{'='*50}")

def cmd_daemon():
    from brain.chain_kernel import enforce_chain
    enforce_chain("gbt.daemon")
    """Daemon mode v3.0 -- devour + gap fix + neighborhood monitor + self-evolve + tentacle"""
    import logging, time
    from datetime import datetime, date
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    L = logging.getLogger("Daemon")

    DAY = 86400
    HOUR = 3600
    started = time.time()

    L.info("GBT Daemon v3.0 active -- devour + tentacle + evolve")

    # Startup: immediate devour
    try:
        from caps.devourer.run import do_scan as devour_scan
        r = devour_scan({})
        L.info(f"Devour: scanned {r.get('total_platforms',0)} platforms, {r.get('new_skills',0)} new skills")
    except Exception as e:
        L.warning(f"Devour failed: {e}")

    # Startup: tentacle pulse
    try:
        from brain.neural_tentacle import get_tentacle
        t = get_tentacle(auto_heal=True)
        r = t.pulse()
        L.info(f"Tentacle: errors={r['total_errors']} fixes={r['fixes_applied']}")
    except Exception as e:
        L.warning(f"Tentacle failed: {e}")

    # Context cleanup
    try:
        from brain.self_evolve import get_evolver
        e = get_evolver()
        cleaned = e.clean_expired_contexts()
        L.info(f"Context: cleaned {cleaned} expired entries")
    except Exception as ex:
        L.warning(f"Context cleanup: {ex}")

    # Neighborhood monitor
    try:
        from brain.nexus import get_nexus
        n = get_nexus()
        s = n.deep_scan()
        if not s["ok"]:
            L.warning(f"Neighborhood: {s['total_issues']} disconnections!")
            n.penetration_scan(auto_fix=True)
    except Exception as ex:
        L.warning(f"Neighborhood: {ex}")

    # Main loop
    last_devour = date.today()
    last_tentacle = time.time()
    last_evolve = time.time()

    while True:
        try:
            now = time.time()
            today = date.today()

            if today > last_devour:
                devour_scan({})
                last_devour = today
                L.info("Daily devour done")

            if now - last_tentacle > HOUR:
                t = get_tentacle(auto_heal=True)
                t.pulse()
                last_tentacle = now

            if now - last_evolve > 6 * HOUR:
                get_evolver().clean_expired_contexts()
                last_evolve = now

            time.sleep(60)
        except KeyboardInterrupt:
            L.info("Daemon stopped")
            break
        except Exception as ex:
            L.error(f"Loop error: {ex}")
            time.sleep(60)

    elapsed = time.time() - started
    print(f"   Runtime: {int(elapsed//DAY)}d {int(elapsed%DAY//HOUR)}h")

def cmd_status():
    from brain.chain_kernel import enforce_chain
    enforce_chain("gbt.status")
    from brain.nexus import get_nexus
    from brain.cognition import get_cognition
    s = get_nexus().deep_scan()
    c = get_cognition()
    print(f"Neighborhood: {s['verdict']} ({s['health']}%)")
    print(f"Files: {s['files']['found']}/{s['files']['total']}")
    print(f"Issues: {s['total_issues']}")
    try:
        from brain.neural_tentacle import get_tentacle
        t = get_tentacle()
        print(f"Tentacle: scan#{t._scan_count} | found{t._issues_found_total} | healed{t._issues_fixed_total}")
    except:
        pass
    print(c.who_am_i()['message'])

def cmd_tentacle():
    from brain.chain_kernel import enforce_chain
    enforce_chain("gbt.tentacle")
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--watch', type=int, default=0)
    ap.add_argument('--auto-heal', action='store_true')
    args, _ = ap.parse_known_args(sys.argv[2:])
    from brain.neural_tentacle import NeuralTentacle
    t = NeuralTentacle(auto_heal=args.auto_heal)
    if args.watch:
        t.watch(interval=args.watch)
    else:
        r = t.pulse()
        icon = "OK" if r["ok"] else "FAIL"
        print(f"Tentacle pulse #{r['scan_count']} [{icon}]")
        print(f"   errors={r['total_errors']} new={r['new_issues']} healed={r['fixes_applied']}")
        print(f"   nexus={'OK' if r['nexus_injected'] else 'FAIL'} | {r['elapsed_ms']}ms")

def cmd_see():
    from brain.chain_kernel import enforce_chain
    enforce_chain("gbt.see")
    from brain.host_body import eyes
    from brain.visual_cortex import get_cortex
    import base64, io
    from PIL import Image
    import pytesseract

    print('Vision activated...')
    screen = eyes.see()
    if not screen.get('ok'):
        print('   FAIL:', screen.get('error', '?'))
        return
    sz = screen.get('size', [0, 0])
    print(f'   Capture: {sz[0]}x{sz[1]}px | {len(screen.get("image",""))//1024}KB')

    img_bytes = base64.b64decode(screen['image'])
    img = Image.open(io.BytesIO(img_bytes))
    text = pytesseract.image_to_string(img, lang='chi_sim+eng', config='--psm 6')

    print('   OCR:')
    for line in text.split('\n'):
        line = line.strip()
        if line:
            print(f'      {line[:150]}')

    cortex = get_cortex()
    report = cortex.analyze_screen()
    if 'error' not in report:
        s = report.get('summary', {})
        print(f'   Cortex: {s.get("components",0)} components, score {s.get("narrative_score",0)}')

    f = eyes.to_image()
    print(f'   Saved: {f.get("file", "?")}')

COMMANDS = {
    "chat": cmd_chat, "tui": cmd_chat,
    "scan": cmd_scan, "status": cmd_status,
    "daemon": cmd_daemon, "ask": cmd_ask,
    "tentacle": cmd_tentacle, "see": cmd_see,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tui"
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print("Available: " + ", ".join(COMMANDS.keys()))
    else:
        COMMANDS[cmd]()
