# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""brain/remote_body.py — AI远程身体
=====================================
用户同意 → AI接管远程电脑 → 跟操作本地一样用眼睛和手。

用法:
  from brain.remote_body import connect, RemoteBody
  
  # 用户运行 deploy_me.py 获得隧道URL
  # AI连接:
  body = connect("https://xxx.trycloudflare.com", "token123")
  
  # 跟本地一模一样:
  body.eyes.see()           # 看远程屏幕
  body.eyes.find("登录")    # 找远程屏幕上的文字
  body.hands.click(320,450) # 点远程桌面
  body.hands.type("hello")  # 在远程打字
  
  # 完成, 断开
  body.disconnect()
  
零学习成本。远程=本地。同一套eyes/hands接口。
"""
import json, urllib.request, urllib.error, base64
from typing import Optional


class RemoteEyes:
    """远程眼睛 — 通过隧道看远程屏幕"""
    
    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip("/")
        self.token = token
    
    def _post(self, action: str, params: dict = None, timeout: int = 15) -> dict:
        """发送指令到远程机器"""
        try:
            data = json.dumps({
                "cmd": f"python -c \"from brain.host_body import eyes; import json; r=eyes.{action}(**{json.dumps(params or {})}); print(json.dumps(r))\"",
                "timeout": timeout
            }).encode()
            req = urllib.request.Request(
                self.base,
                data=data,
                headers={
                    "X-GBT-Token": self.token,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
                result = json.loads(resp.read().decode())
                if result.get("ok"):
                    # Parse the nested result from remote eyes
                    inner = result.get("stdout", "{}")
                    return json.loads(inner) if inner else {"ok": False}
                return {"ok": False, "error": result.get("stderr", "")[:200]}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
    
    def see(self) -> dict:
        """看远程屏幕"""
        return self._post("see")
    
    def read_all(self) -> dict:
        """读远程全屏文字"""
        return self._post("read_all")
    
    def find(self, text: str) -> dict:
        """在远程屏幕上找文字，返回 {"ok": True/False, "found": True/False, "x": int, "y": int, ...}"""
        r = self._post("find", {"text": text})
        if r and isinstance(r, dict) and r.get("ok"):
            return {"ok": True, "found": True, "x": int(r.get("x", 0)), "y": int(r.get("y", 0))}
        return {"ok": True, "found": False, "message": f"'{text}' 未在远程屏幕上找到"}

    def wait_for(self, text: str, timeout: float = 30.0) -> dict:
        """等待远程屏幕出现文字，返回 {"ok": True/False, "found": True/False, "x": int, "y": int, ...}"""
        r = self._post("wait_for", {"text": text, "timeout": timeout}, timeout=int(timeout) + 10)
        if r and isinstance(r, dict) and r.get("ok"):
            return {"ok": True, "found": True, "x": int(r.get("x", 0)), "y": int(r.get("y", 0))}
        return {"ok": True, "found": False, "message": f"'{text}' 等待超时({timeout}s)未出现"}


class RemoteHands:
    """远程手 — 通过隧道操控远程键鼠"""
    
    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip("/")
        self.token = token
    
    def _post(self, action: str, params: dict = None, timeout: int = 10) -> dict:
        try:
            if action == "hotkey" and params and "keys" in params:
                keys_json = json.dumps(params["keys"])
                cmd = f"python -c \"from brain.host_body import hands; import json; r=hands.hotkey(*{keys_json}); print(json.dumps(r))\""
            else:
                cmd = f"python -c \"from brain.host_body import hands; import json; r=hands.{action}(**{json.dumps(params or {})}); print(json.dumps(r))\""
            data = json.dumps({
                "cmd": cmd,
                "timeout": timeout
            }).encode()
            req = urllib.request.Request(
                self.base,
                data=data,
                headers={
                    "X-GBT-Token": self.token,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
                result = json.loads(resp.read().decode())
                if result.get("ok"):
                    inner = result.get("stdout", "{}")
                    return json.loads(inner) if inner else {"ok": False}
                return {"ok": False, "error": result.get("stderr", "")[:200]}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
    
    def click(self, x: int, y: int) -> dict:
        return self._post("click", {"x": x, "y": y})
    
    def double_click(self, x: int, y: int) -> dict:
        return self._post("double_click", {"x": x, "y": y})
    
    def move(self, x: int, y: int) -> dict:
        return self._post("move", {"x": x, "y": y})
    
    def type(self, text: str) -> dict:
        return self._post("type", {"text": text})
    
    def press(self, key: str) -> dict:
        return self._post("press", {"key": key})
    
    def hotkey(self, *keys) -> dict:
        return self._post("hotkey", {"keys": list(keys)})
    
    def move_to_text(self, text: str) -> dict:
        return self._post("move_to_text", {"text": text})
    
    def type_and_enter(self, text: str) -> dict:
        return self._post("type_and_enter", {"text": text})
    
    def select_all_copy(self) -> dict:
        return self._post("select_all_copy")


class RemoteTerminal:
    """远程终端 — 在远程电脑上执行shell命令"""

    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip("/")
        self.token = token

    def _post(self, cmd: str, timeout: int = 30) -> dict:
        try:
            data = json.dumps({
                "cmd": cmd,
                "timeout": timeout
            }).encode()
            req = urllib.request.Request(
                self.base,
                data=data,
                headers={
                    "X-GBT-Token": self.token,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def exec(self, cmd: str, timeout: int = 30) -> dict:
        """执行shell命令, 返回 {"ok": bool, "stdout": str, "stderr": str, "returncode": int}"""
        return self._post(cmd, timeout)

    def run(self, cmd: str, timeout: int = 30) -> dict:
        """exec的别名"""
        return self.exec(cmd, timeout)


class RemoteBody:
    """远程身体 — 接管用户电脑"""
    
    def __init__(self, tunnel_url: str, token: str, terminal_url: str = None):
        self.eyes = RemoteEyes(tunnel_url, token)
        self.hands = RemoteHands(tunnel_url, token)
        self.terminal = RemoteTerminal(terminal_url, token) if terminal_url else None
        self.url = tunnel_url
        self.token = token
    
    def health(self) -> dict:
        """检查远程连接"""
        try:
            req = urllib.request.Request(
                self.url,
                headers={"X-GBT-Token": self.token}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
    def disconnect(self):
        """断开连接"""
        self.eyes = None
        self.hands = None
        self.terminal = None


def connect(tunnel_url: str, token: str, terminal_url: str = None) -> RemoteBody:
    """连接到远程电脑 — 获得远程身体控制权

    用户需要先在远程电脑运行:
      python agent.py
    获得 tunnel_url + token

    如果传入session JSON报告, 自动提取终端URL:
      body = connect(report_json)
    """
    # 自动解析session报告
    if isinstance(tunnel_url, dict) or (isinstance(tunnel_url, str) and tunnel_url.strip().startswith("{")):
        import json as _json
        report = _json.loads(tunnel_url) if isinstance(tunnel_url, str) else tunnel_url
        services = report.get("services", report.get("exposed", []))
        token = report.get("token", token)
        # 找主tunnel
        tunnel_url = services[0]["url"] if services else tunnel_url
        # 找终端tunnel
        for s in services:
            if s.get("type") == "terminal":
                terminal_url = s["url"]
                break
    body = RemoteBody(tunnel_url, token, terminal_url)
    health = body.health()
    if not health.get("ok"):
        raise ConnectionError(f"无法连接到远程电脑: {health.get('error', '未知错误')}")
    return body


def connect_from_active_tunnels() -> Optional[RemoteBody]:
    """从活跃隧道列表自动连接最新的远程电脑"""
    from pathlib import Path
    tunnels_file = Path.home() / ".gbt" / "active_tunnels.json"
    if not tunnels_file.exists():
        return None
    
    tunnels = json.loads(tunnels_file.read_text(encoding="utf-8"))
    if not tunnels:
        return None
    
    latest = max(tunnels.items(), key=lambda x: x[1].get("created", 0))
    session_id, info = latest
    
    body = RemoteBody(info["tunnel_url"], info["token"])
    health = body.health()
    if health.get("ok"):
        return body
    return None
