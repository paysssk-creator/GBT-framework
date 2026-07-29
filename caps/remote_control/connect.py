# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# remote_control/connect.py — GBT 侧远程接入模块
# ============================================================
"""GBT Remote Connector — 接入用户远程通道

用法 (GBT 内部):
  from caps.remote_control.connect import RemoteSession
  session = RemoteSession(session_json)
  await session.connect()
  # 操控
  await session.call_api("/api/endpoint")
  await session.browser.goto("https://...")
"""

import json, asyncio, aiohttp
from urllib.parse import urljoin

class RemoteService:
    """远程服务代理 — 自动注入令牌"""
    def __init__(self, info, token):
        self.port = info["port"]
        self.url = info["url"]
        self.type = info.get("type", "http")
        self._token = token

    def _headers(self):
        return {"X-GBT-Token": self._token} if self._token else {}

    async def get(self, path="/", **kwargs):
        h = {**self._headers(), **kwargs.pop("headers", {})}
        async with aiohttp.ClientSession() as s:
            async with s.get(urljoin(self.url, path), headers=h, **kwargs) as resp:
                return {"status": resp.status, "body": await resp.text()}

    async def post(self, path="/", data=None, **kwargs):
        h = {**self._headers(), **kwargs.pop("headers", {})}
        async with aiohttp.ClientSession() as s:
            async with s.post(urljoin(self.url, path), json=data, headers=h, **kwargs) as resp:
                return {"status": resp.status, "body": await resp.text()}

    def __repr__(self):
        return f"RemoteService(port={self.port}, url={self.url}, auth={'yes' if self._token else 'no'})"


class RemoteCDP:
    """远程 Chrome DevTools Protocol 接入"""
    def __init__(self, info):
        self.url = info["url"]
        self.port = info["port"]
        self._ws = None
        self._msg_id = 0

    async def connect(self):
        """获取 WebSocket 端点"""
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.url}/json/version") as resp:
                data = await resp.json()
                ws_url = data.get("webSocketDebuggerUrl")
                if not ws_url:
                    # 尝试直接访问
                    async with s.get(f"{self.url}/json") as resp2:
                        pages = await resp2.json()
                        if pages:
                            ws_url = pages[0].get("webSocketDebuggerUrl")
                if ws_url:
                    self._ws = await aiohttp.ClientSession().ws_connect(ws_url)
                    return True
        return False

    async def send(self, method, params=None):
        """发送 CDP 命令"""
        if not self._ws:
            raise RuntimeError("CDP not connected. Call connect() first.")
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method, "params": params or {}}
        await self._ws.send_json(msg)
        resp = await self._ws.receive_json()
        return resp.get("result", resp)

    async def navigate(self, url):
        await self.send("Page.enable")
        return await self.send("Page.navigate", {"url": url})

    async def evaluate(self, expression):
        """在页面执行 JS"""
        result = await self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True
        })
        return result.get("result", {}).get("value")

    async def screenshot(self):
        """截取页面截图 (base64)"""
        await self.send("Page.enable")
        return await self.send("Page.captureScreenshot", {"format": "png"})

    async def close(self):
        if self._ws:
            await self._ws.close()

    def __repr__(self):
        return f"RemoteCDP(url={self.url})"


class RemoteSession:
    """GBT 远程会话 — 统一操控入口 (自动令牌鉴权)"""
    def __init__(self, session_data):
        if isinstance(session_data, str):
            session_data = json.loads(session_data)
        self.data = session_data
        self.token = session_data.get("token", "")
        self.services = []
        self.cdp = None
        self._parse()

    def _parse(self):
        for svc in self.data.get("services", []):
            if svc.get("type") == "cdp":
                self.cdp = RemoteCDP(svc)
            else:
                self.services.append(RemoteService(svc, self.token))

    def get_service(self, port=None, name=None):
        """按端口或名称查找服务"""
        for svc in self.services:
            if port and svc.port == port:
                return svc
        return self.services[0] if self.services else None

    async def connect(self):
        """建立连接"""
        if self.cdp:
            return await self.cdp.connect()
        return True

    def info(self):
        return {
            "hostname": self.data.get("hostname"),
            "platform": self.data.get("platform"),
            "timestamp": self.data.get("timestamp"),
            "services": len(self.services),
            "cdp": self.cdp is not None,
        }

    def __repr__(self):
        i = self.info()
        return f"RemoteSession(host={i['hostname']}, services={i['services']}, cdp={i['cdp']})"


# ===================== 便捷函数 =====================
def parse_session_report(report_json):
    """解析用户发来的会话报告"""
    return RemoteSession(report_json)

def load_session_file(path=None):
    """从文件加载会话"""
    from pathlib import Path
    path = path or Path.home() / ".gbt_remote_session.json"
    return RemoteSession(Path(path).read_text())


# ===================== 测试 =====================
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        session = RemoteSession(sys.argv[1])
        print(session.info())
        # 测试连接
        async def test():
            await session.connect()
            svc = session.get_service()
            if svc:
                resp = await svc.get("/")
                print(f"Service response: {resp['status']}")
            if session.cdp:
                title = await session.cdp.evaluate("document.title")
                print(f"Page title: {title}")
        asyncio.run(test())
