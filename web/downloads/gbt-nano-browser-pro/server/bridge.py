# ⛔ GBT Nano Browser Pro — 全邻域网关
# 连接AI到所有GBT能力：股票操盘/浏览器/资讯/支付/部署
import http.server, json, subprocess, sys, os
from pathlib import Path

PORT = 15999

# ── 查找GBT项目 ──
GBT = None
for c in [Path(__file__).parent.parent.parent.parent, Path.home()/'GBTxiaotudouV5',
          Path('C:/Users/ADMIN/GBTxiaotudouV5')]:
    if (c/'brain'/'deep_reasoner.py').exists(): GBT = c; sys.path.insert(0,str(c)); break

HAS_GBT = GBT is not None
CAPS_DIR = GBT/'caps' if HAS_GBT else None

# ── 邻域能力路由表 ──
CAP_ROUTES = {
    # 金融
    "股票扫描|扫描股票|行情扫描|scan stock": ("stock_scalper","scan"),
    "股票状态|持仓|操盘状态": ("stock_scalper","status"),
    "启动操盘|开始割草|自动操盘": ("stock_scalper","start"),
    "停止操盘": ("stock_scalper","stop"),
    "市场情绪|大盘情绪|sentiment": ("stock_scalper","sentiment"),
    "每日复盘|今天复盘|review": ("stock_scalper","review"),
    # 浏览器
    "打开网页|打开网站|浏览|browse": ("browser_automation","navigate"),
    "截图|screenshot": ("browser_automation","screenshot"),
    # 搜索
    "搜索|search|查找": ("web_search","search"),
    # 编程
    "写代码|编程|code": ("programming","generate"),
    # 资讯
    "GitHub热门|trending|排行榜": ("trending_scanner","scan"),
    # 支付
    "支付|购买|pay": ("payments","status"),
    # 部署
    "部署|deploy|安装": ("oneclick_deploy","deploy"),
}

def find_cap(query):
    """根据用户意图找到匹配的cap"""
    q = query.lower()
    for pattern, (cap, action) in CAP_ROUTES.items():
        for p in pattern.split('|'):
            if p in q: return cap, action
    return None, None

def call_cap(cap_name, action, params=None):
    """调用cap模块"""
    if not HAS_GBT: return {"ok":False,"error":"GBT项目未连接"}
    cap_py = CAPS_DIR / cap_name / 'run.py'
    if not cap_py.exists(): return {"ok":False,"error":f"cap {cap_name} 不存在"}
    try:
        r = subprocess.run(
            [sys.executable, str(cap_py), action, json.dumps(params or {}, ensure_ascii=False)],
            capture_output=True, text=True, timeout=30, cwd=str(GBT),
            encoding='utf-8', errors='replace'
        )
        return json.loads(r.stdout) if r.stdout.strip() else {"ok":False,"error":"无输出"}
    except subprocess.TimeoutExpired:
        return {"ok":False,"error":"超时"}
    except Exception as e:
        return {"ok":False,"error":str(e)[:100]}

def ai_answer(question):
    """AI智能回答——优先路由到cap，其次用推理引擎"""
    # 1. 尝试cap路由
    cap, action = find_cap(question)
    if cap:
        result = call_cap(cap, action, {"query": question})
        return f"[{cap}] {json.dumps(result, ensure_ascii=False)[:1500]}"
    
    # 2. 通用问答——知识库
    q = question.lower()
    if any(w in q for w in ['怎么用','帮助','help','功能','能做什么']):
        return """我能帮你：
📈 股票: "扫描股票" "市场情绪" "每日复盘" "启动操盘"
🌐 浏览: "打开淘宝" "打开京东"  
🔍 搜索: "搜索Python教程"
💰 支付: "怎么购买Pro版"
🚀 部署: "部署到我的电脑"
💬 其他: 直接问我任何问题"""
    
    if any(w in q for w in ['买','pro','价格','多少钱']):
        return """GBT Nano Browser Pro 价格：
🆓 免费: 基础浏览+AI问答
⭐ Pro $29/月: 无限标签+指纹隐身+2Captcha+AI全控+股票操盘
🏢 企业 $99/月: 全部+API+定制
购买: https://gbtxiaotudou.com/pricing.html"""
    
    if any(w in q for w in ['验证码','captcha','2captcha']):
        return """2Captcha验证码自动解决:
1. 去 https://2captcha.com 注册充值
2. 在设置中填入API Key
3. 开启自动解决
Playwright专用: https://2captcha.com/p/playwright-captcha-solver"""
    
    # 3. DeepSeek推理
    if HAS_GBT:
        try:
            from brain.deep_reasoner import get_reasoner
            return str(get_reasoner().reason(question, mode="decision"))[:2000]
        except:
            pass
    
    return f"关于「{question}」，试试问我：股票扫描 | 打开网页 | 怎么购买 | 验证码怎么用"

# ── HTTP服务 ──
class Handler(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._cors()

    def do_POST(self):
        try:
            d = json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))))

            if self.path == '/ai':
                resp = {"ok":True, "answer": ai_answer(d.get('question',''))}
            elif self.path == '/cap':
                cap, action = d.get('cap'), d.get('action')
                resp = call_cap(cap, action, d.get('params')) if cap else {"ok":False,"error":"缺少cap"}
            elif self.path == '/cmd':
                r = subprocess.run(d.get('cmd','echo ok'), shell=True, capture_output=True, text=True, timeout=30)
                resp = {"ok":True, "stdout":r.stdout[:3000], "stderr":r.stderr[:500]}
            else:
                resp = {"ok":False,"error":"unknown path"}

            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(resp,ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if self.path == '/health':
            caps = list({c for c,_ in CAP_ROUTES.values()}) if HAS_GBT else []
            self.wfile.write(json.dumps({
                "status":"ok", "port":PORT, "gbt":HAS_GBT,
                "gbt_root":str(GBT) if GBT else None,
                "neighborhoods": len(caps), "caps": caps[:20]
            }, ensure_ascii=False).encode())
        else:
            caps = list({c for c,_ in CAP_ROUTES.values()}) if HAS_GBT else []
            self.wfile.write(json.dumps({
                "status":"ok", "port":PORT, "gbt":HAS_GBT,
                "gbt_root":str(GBT) if GBT else None,
                "neighborhoods": len(caps), "caps": caps[:20]
            }, ensure_ascii=False).encode())

    def log_message(self,*a): pass

if __name__ == '__main__':
    print(f'🫀 GBT Neighborhood Gateway :{PORT} | GBT={"ON" if HAS_GBT else "OFF"} | {len(CAP_ROUTES)} routes', flush=True)
    http.server.HTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
