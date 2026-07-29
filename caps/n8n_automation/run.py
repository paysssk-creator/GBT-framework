# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""n8n_automation/run.py — N8N全局自动化编排
================================================
所有支付/部署/分账的自动化N8N工作流触发器。
每个关键事件都经N8N工作流编排，确保可追溯、可回滚。
"""
import sys, json, os, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

SANDBOX = Path(__file__).parent.parent
N8N_DIR = Path.home() / ".gbt" / "n8n"
N8N_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  三大核心N8N工作流定义
# ═══════════════════════════════════════════════════════════

def _gen_n8n_node(node_id, name, node_type, position, params, webhook_path=None):
    """生成标准N8N节点"""
    node = {"id": node_id, "name": name, "type": node_type, "position": position, "parameters": params}
    if webhook_path: node["webhookId"] = node_id
    return node

def do_generate_payment_flow(params):
    """生成支付自动化工作流: 收到支付→验证→分账→通知→结算"""
    nodes = [
        _gen_n8n_node("webhook", "Crypto Payment Received", "n8n-nodes-base.webhook",
                       [400, 100], {"httpMethod": "POST", "path": "gbt-payment-webhook", "responseMode": "lastNode"}),
        _gen_n8n_node("validate", "Validate Payment", "n8n-nodes-base.function",
                       [400, 280], {"functionCode": _get_validate_code()}),
        _gen_n8n_node("split", "80/20 Revenue Split", "n8n-nodes-base.executeCommand",
                       [400, 460], {"command": "python caps/revenue_split/run.py record '{\"project\":\"{{$json.project}}\",\"developer\":\"{{$json.developer}}\",\"hours\":24,\"rate\":{{$json.rate}}}'"}),
        _gen_n8n_node("notify", "Notify Developer", "n8n-nodes-base.executeCommand",
                       [400, 640], {"command": "python caps/slack_bot/run.py send_slack '{\"channel\":\"revenue\",\"text\":\"💰 New payment: ${{$json.amount}} for {{$json.project}}\"}'"}),
        _gen_n8n_node("settle", "Daily Settlement", "n8n-nodes-base.scheduleTrigger",
                       [400, 820], {"rule": {"interval": [{"field": "hours", "hoursInterval": 24}]}}),
        _gen_n8n_node("settle_exec", "Execute Settlement", "n8n-nodes-base.executeCommand",
                       [400, 1000], {"command": "python caps/revenue_split/run.py settle '{}'"}),
    ]
    
    connections = {
        "webhook": {"main": [[{"node": "validate", "type": "main", "index": 0}]]},
        "validate": {"main": [[{"node": "split", "type": "main", "index": 0}]]},
        "split": {"main": [[{"node": "notify", "type": "main", "index": 0}]]},
        "settle": {"main": [[{"node": "settle_exec", "type": "main", "index": 0}]]},
    }
    
    workflow = {"name": "GBT Payment Automation", "nodes": nodes, "connections": connections, "settings": {"executionOrder": "v1"}}
    fpath = N8N_DIR / "gbt_payment_flow.json"
    fpath.write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return {"ok": True, "workflow": "gbt_payment_flow.json", "path": str(fpath),
            "triggers": ["POST /gbt-payment-webhook", "Daily 0:00 settlement"],
            "actions": ["validate→split(80/20)→notify→settle"]}

def _get_validate_code():
    return """// Validate incoming crypto payment
const payment = $input.first().json;
const minAmount = 0.01;
if (!payment.amount || payment.amount < minAmount) {
  throw new Error(`Payment too small: ${payment.amount}`);
}
// Check 3 confirmations minimum
if (payment.confirmations < 3) {
  return [{json: {...payment, status: 'pending', note: 'Waiting for confirmations'}}];
}
// Calculate split
const devShare = payment.amount * 0.8;
const platformShare = payment.amount * 0.2;
return [{
  json: {
    ...payment,
    status: 'confirmed',
    dev_share: devShare.toFixed(4),
    platform_share: platformShare.toFixed(4),
    timestamp: new Date().toISOString()
  }
}];"""

def do_generate_deploy_flow(params):
    """生成部署自动化工作流: 收到部署请求→健康检查→部署→监控→通知"""
    nodes = [
        _gen_n8n_node("webhook", "Deploy Request", "n8n-nodes-base.webhook",
                       [400, 100], {"httpMethod": "POST", "path": "gbt-deploy-webhook", "responseMode": "lastNode"}),
        _gen_n8n_node("health_check", "Nexus Health Check", "n8n-nodes-base.executeCommand",
                       [400, 280], {"command": "python -c \"from brain.nexus import get_nexus; n=get_nexus(); s=n.quick_health(); import json; print(json.dumps(s))\" "}),
        _gen_n8n_node("gate", "Health Gate", "n8n-nodes-base.if",
                       [400, 460], {"conditions": {"string": [{"value1": "={{$json.ok}}", "operation": "equals", "value2": "True"}]}}),
        _gen_n8n_node("deploy", "Docker Deploy", "n8n-nodes-base.executeCommand",
                       [400, 640], {"command": "python caps/docker/run.py run '{\"image\":\"{{$json.project}}\",\"name\":\"gbt-{{$json.project}}\",\"port\":\"{{$json.port}}\"}' "}),
        _gen_n8n_node("monitor", "Start Monitoring", "n8n-nodes-base.executeCommand",
                       [400, 820], {"command": "python caps/dev_cpu/run.py status '{}' "}),
        _gen_n8n_node("alert", "Alert on Failure", "n8n-nodes-base.executeCommand",
                       [750, 460], {"command": "python caps/slack_bot/run.py send_slack '{\"channel\":\"alerts\",\"text\":\"🚨 Deploy health check FAILED for {{$json.project}}\"}' "}),
    ]
    
    connections = {
        "webhook": {"main": [[{"node": "health_check", "type": "main", "index": 0}]]},
        "health_check": {"main": [[{"node": "gate", "type": "main", "index": 0}]]},
        "gate": {"main": [
            [{"node": "deploy", "type": "main", "index": 0}],
            [{"node": "alert", "type": "main", "index": 0}]
        ]},
        "deploy": {"main": [[{"node": "monitor", "type": "main", "index": 0}]]},
    }
    
    workflow = {"name": "GBT Deploy Automation", "nodes": nodes, "connections": connections, "settings": {"executionOrder": "v1"}}
    fpath = N8N_DIR / "gbt_deploy_flow.json"
    fpath.write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return {"ok": True, "workflow": "gbt_deploy_flow.json", "path": str(fpath),
            "triggers": ["POST /gbt-deploy-webhook"],
            "actions": ["health_check→gate→deploy→monitor (or alert)"]}

def do_generate_monitor_flow(params):
    """生成全局监控工作流: 定时邻域扫描→异常检测→自动修复→告警"""
    nodes = [
        _gen_n8n_node("schedule", "Every 30min", "n8n-nodes-base.scheduleTrigger",
                       [400, 100], {"rule": {"interval": [{"field": "minutes", "minutesInterval": 30}]}}),
        _gen_n8n_node("nexus_scan", "Nexus Deep Scan", "n8n-nodes-base.executeCommand",
                       [400, 280], {"command": "python -c \"from brain.nexus import get_nexus; import json; print(json.dumps(get_nexus().deep_scan()))\" "}),
        _gen_n8n_node("health_check", "Health Score", "n8n-nodes-base.function",
                       [400, 460], {"functionCode": _get_health_code()}),
        _gen_n8n_node("alert_gate", "Alert Gate", "n8n-nodes-base.if",
                       [400, 640], {"conditions": {"number": [{"value1": "={{$json.health_pct}}", "operation": "smaller", "value2": 90}]}}),
        _gen_n8n_node("auto_fix", "Auto Fix", "n8n-nodes-base.executeCommand",
                       [400, 820], {"command": "python caps/auto_resolver/run.py resolve '{\"topic\":\"Nexus health {{$json.health_pct}}% below 90%. Issues: {{$json.issues}}\"}' "}),
        _gen_n8n_node("notify", "Alert Admin", "n8n-nodes-base.executeCommand",
                       [750, 640], {"command": "python caps/slack_bot/run.py send_slack '{\"channel\":\"alerts\",\"text\":\"⛔ NEXUS HEALTH {{$json.health_pct}}% · {{$json.issue_count}} issues\"}' "}),
        _gen_n8n_node("devourer", "Daily Evolution", "n8n-nodes-base.executeCommand",
                       [400, 1000], {"command": "python caps/devourer/run.py daily '{}' "}),
    ]
    
    connections = {
        "schedule": {"main": [[{"node": "nexus_scan", "type": "main", "index": 0}]]},
        "nexus_scan": {"main": [[{"node": "health_check", "type": "main", "index": 0}]]},
        "health_check": {"main": [[{"node": "alert_gate", "type": "main", "index": 0}]]},
        "alert_gate": {"main": [
            [{"node": "auto_fix", "type": "main", "index": 0}],
            [{"node": "notify", "type": "main", "index": 0}]
        ]},
        "auto_fix": {"main": [[{"node": "devourer", "type": "main", "index": 0}]]},
    }
    
    workflow = {"name": "GBT Global Monitor", "nodes": nodes, "connections": connections, "settings": {"executionOrder": "v1"}}
    fpath = N8N_DIR / "gbt_monitor_flow.json"
    fpath.write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return {"ok": True, "workflow": "gbt_monitor_flow.json", "path": str(fpath),
            "triggers": ["Every 30 minutes", "Daily devourer"],
            "actions": ["nexus_scan→health_check→alert→auto_fix→devourer"]}

def _get_health_code():
    return """const data = $input.first().json;
const health = data.health || 100;
const issues = data.issues || [];
const broken = data.connections?.broken || [];
return [{
  json: {
    health_pct: health,
    issue_count: issues.length + broken.length,
    issues: JSON.stringify(issues.slice(0,5)),
    status: health >= 90 ? 'healthy' : (health >= 70 ? 'warning' : 'critical'),
    timestamp: new Date().toISOString()
  }
}];"""

def do_generate_all(params):
    """一键生成全部3个N8N工作流"""
    r1 = do_generate_payment_flow(params)
    r2 = do_generate_deploy_flow(params)
    r3 = do_generate_monitor_flow(params)
    return {"ok": True, "workflows": [r1["workflow"], r2["workflow"], r3["workflow"]],
            "total": 3, "n8n_dir": str(N8N_DIR),
            "import": "N8N → Settings → Import → 选择上述JSON文件"}

def do_list(params):
    """列出已有工作流"""
    workflows = []
    for f in N8N_DIR.glob("*.json"):
        try:
            wf = json.loads(f.read_text(encoding="utf-8"))
            workflows.append({"name": f.name, "nodes": len(wf.get("nodes", [])), "size": f.stat().st_size})
        except: pass
    return {"ok": True, "workflows": workflows, "total": len(workflows), "n8n_dir": str(N8N_DIR)}

def do_status(params):
    """N8N状态检测"""
    try:
        r = subprocess.run(["n8n","--version"], capture_output=True, text=True, timeout=5)
        n8n_installed = r.returncode == 0
    except: n8n_installed = False
    
    try:
        r = subprocess.run(["curl","-s","http://localhost:5678/healthz"], capture_output=True, text=True, timeout=5)
        n8n_running = "ok" in r.stdout.lower() if r.stdout else False
    except: n8n_running = False
    
    return {"ok": True, "n8n_installed": n8n_installed, "n8n_running": n8n_running,
            "workflow_count": len(list(N8N_DIR.glob("*.json"))),
            "webhook_endpoints": ["/gbt-payment-webhook", "/gbt-deploy-webhook"],
            "start_n8n": "n8n start" if not n8n_running else "already running"}

HANDLERS = {
    "generate_payment": do_generate_payment_flow,
    "generate_deploy": do_generate_deploy_flow,
    "generate_monitor": do_generate_monitor_flow,
    "generate_all": do_generate_all,
    "list": do_list, "status": do_status, "run": do_generate_all,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "generate_all"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
