# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""brain/host_body.py — AI原生身体
====================================
眼睛和手是AI的与生俱来的能力，不是"cap调用"。
这是主机的外设，直接操控。

用法:
  from brain.host_body import eyes, hands
  
  # 眼睛 — 直接看
  eyes.see()                    → 截全屏, 返回base64图片
  eyes.read(x,y,w,h)            → OCR读屏幕区域文字
  eyes.find("登录")             → 在屏幕上找文字, 返回坐标
  eyes.watch(interval=2)        → 持续监控屏幕变化
  
  # 手 — 直接动
  hands.move(x, y)              → 移动鼠标
  hands.click(x, y)             → 点击
  hands.double_click(x, y)      → 双击
  hands.type("hello")           → 键盘输入
  hands.press("enter")          → 按键
  hands.hotkey("ctrl", "c")     → 组合键
  hands.drag(x1,y1, x2,y2)     → 拖拽
  hands.scroll(amount)          → 滚轮
"""
import subprocess, json, sys, os, base64, time, threading
from collections import deque
from pathlib import Path
from typing import Optional, Tuple, List

ROOT = Path(__file__).parent.parent
CAPS_DIR = ROOT / "caps"

def _call_cap(cap_name, action, params=None, timeout=15):
    """内部调用cap — 不是路由，是直达"""
    search = [CAPS_DIR, ROOT / "integrations", ROOT / "deploy"]
    for sd in search:
        rp = sd / cap_name / "run.py"
        if rp.exists():
            break
    else:
        return {"ok": False, "error": f"cap {cap_name} not found"}
    
    try:
        params_json = json.dumps(params or {}, ensure_ascii=False)
        # 大 payload (>4000 chars) 用临时文件避免 Windows 命令行长度限制
        if len(params_json) > 4000:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
            tmp.write(params_json)
            tmp.close()
            r = subprocess.run(
                [sys.executable, str(rp), action, "--file", tmp.name],
                capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace"
            )
            os.unlink(tmp.name)
        else:
            r = subprocess.run(
                [sys.executable, str(rp), action, params_json],
                capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace"
            )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
        return {"ok": False, "error": r.stderr[:200] if r.stderr else "no output"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}



# ═══════════ FrameBuffer · 后台持续视觉 ═══════════

class FrameBuffer:
    """后台帧缓冲 — 持续采集，眼手并行不阻塞
    
    独立daemon线程持续抓屏→环形缓冲，主线程随时取最新帧。
    这才是人类级别的视觉: 眼睛一直在看，手随时能动。
    """
    
    def __init__(self, fps: int = 30, maxlen: int = 60):
        self._fps = fps
        self._buffer = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._frame_count = 0
        self._start_time = None
    
    def start(self):
        """启动后台采集线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True, name="FrameBuffer")
        self._thread.start()
    
    def stop(self):
        """停止后台采集"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
    
    def _capture_loop(self):
        """后台采集循环 — daemon线程"""
        import mss
        from PIL import Image
        import io as _io
        
        self._start_time = time.time()
        interval = 1.0 / self._fps
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while self._running:
                t0 = time.time()
                try:
                    frame = sct.grab(monitor)
                    img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
                    buf = _io.BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    
                    with self._lock:
                        self._buffer.append({
                            "ok": True,
                            "image": b64,
                            "timestamp": time.time(),
                            "size": list(img.size),
                            "frame_id": self._frame_count
                        })
                        self._frame_count += 1
                except Exception:
                    import traceback as _tb
                    _tb.print_exc()
                    time.sleep(0.5)  # 出错后稍等，避免疯狂重试
                
                elapsed = time.time() - t0
                time.sleep(max(0, interval - elapsed))
    
    @property
    def latest(self) -> dict:
        """取最新帧 — 零阻塞，即时返回"""
        with self._lock:
            if self._buffer:
                return dict(self._buffer[-1])
            return {"ok": False, "error": "buffer empty, call start() first"}
    
    def recent(self, n: int = 5) -> list:
        """取最近n帧"""
        with self._lock:
            items = list(self._buffer)[-n:]
            return [dict(item) for item in items]
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "buffer_size": len(self._buffer),
                "maxlen": self._buffer.maxlen,
                "total_frames": self._frame_count,
                "fps_target": self._fps,
                "uptime": round(time.time() - (self._start_time or time.time()), 1)
            }

# 全局帧缓冲单例 — 首次访问自动启动
_frame_buffer: Optional[FrameBuffer] = None

def _get_buffer(fps: int = 30) -> FrameBuffer:
    global _frame_buffer
    if _frame_buffer is None:
        _frame_buffer = FrameBuffer(fps=fps)
    if not _frame_buffer.is_running:
        _frame_buffer.start()
    return _frame_buffer


# ═══════════ BetterCam 240Hz+ 高速视觉 ═══════════
try:
    import bettercam
    HAS_BETTERCAM = True
except:
    HAS_BETTERCAM = False

class HighSpeedEye:
    """高速眼睛 — BetterCam 240Hz+ 采集, 跟人类一样的视觉刷新率"""
    
    def __init__(self):
        if not HAS_BETTERCAM:
            raise RuntimeError("BetterCam not installed. pip install bettercam")
        self._cam = bettercam.create()
        self._fps = 240
    
    def grab(self, region=None):
        """抓取一帧 (numpy array BGR)"""
        if region:
            return self._cam.grab(region=(region['x'], region['y'], region['w'], region['h']))
        return self._cam.grab()
    
    def see(self, region=None):
        """看一帧 — 返回base64 PNG"""
        import base64, io
        try:
            from PIL import Image
            frame = self.grab(region)
            img = Image.fromarray(frame)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return {
                'ok': True,
                'image': base64.b64encode(buf.getvalue()).decode(),
                'shape': list(frame.shape),
                'fps_capable': self._fps
            }
        except:
            return {'ok': False, 'error': 'capture failed'}
    
    def stream(self, callback, duration=10.0, fps=60):
        """实时视频流 — 回调每帧"""
        import time
        start = time.time()
        interval = 1.0 / fps
        frames = 0
        while time.time() - start < duration:
            frame = self.grab()
            callback(frame, frames)
            frames += 1
            time.sleep(max(0, interval - 0.001))
        return frames
    
    def record(self, duration=10.0, fps=60, output=None):
        """录制视频 — 保存为MP4"""
        import time
        frames = []
        interval = 1.0 / fps
        start = time.time()
        while time.time() - start < duration:
            frames.append(self.grab())
            time.sleep(max(0, interval - 0.001))
        
        if output and frames:
            try:
                import cv2
                h, w = frames[0].shape[:2]
                writer = cv2.VideoWriter(output, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                for f in frames:
                    writer.write(f)
                writer.release()
            except:
                pass
        
        return {'ok': True, 'frames': len(frames), 'duration': duration, 'fps': fps,
                'output': output}
    
    @property
    def fps(self):
        return self._fps
    
    @fps.setter
    def fps(self, value):
        self._fps = min(value, 360)

# 高速眼 — 延迟初始化, 避免 import 时 BetterCam 冲突
highspeed_eye = None

def _get_highspeed_eye():
    global highspeed_eye
    if highspeed_eye is None and HAS_BETTERCAM:
        try:
            highspeed_eye = HighSpeedEye()
        except Exception:
            pass
    return highspeed_eye


# Tesseract路径(Windows)
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except: pass

class Eyes:
    """AI的眼睛 — 39FPS电影级视觉 + OCR"""
    
    def see(self, region: dict = None) -> dict:
        """看屏幕 — mss直连(优先,零初始化) 或 BetterCam(备选)"""
        # mss 优先 — 避免 BetterCam 初始化冲突导致挂死
        # BetterCam 仍可通过 highspeed_eye.see() 显式调用
        try:
            import mss, base64, io
            from PIL import Image
            with mss.mss() as sct:
                if region:
                    monitor = {"top": region.get("y",0), "left": region.get("x",0),
                              "width": region.get("w",1920), "height": region.get("h",1080)}
                else:
                    monitor = sct.monitors[1]
                frame = sct.grab(monitor)
                img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return {"ok": True, "image": base64.b64encode(buf.getvalue()).decode(),
                        "size": list(img.size), "mode": "mss-direct"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}
    
    # ── 原生视野 · 多引擎全维度看清 ──────
    
    def read(self, x: int = 0, y: int = 0, w: int = 1920, h: int = 1080, 
             enhance: bool = True, lang: str = 'chi_sim+eng') -> dict:
        """OCR读屏幕 — 多引擎级联: 图像增强→Tesseract→EasyOCR→AI兜底"""
        try:
            import pytesseract, mss
            from PIL import Image, ImageFilter, ImageEnhance
            
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": w, "height": h}
                frame = sct.grab(monitor)
                img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
                
                # 图像增强: 放大2倍 + 锐化 + 对比度提升
                if enhance:
                    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
                    img = img.filter(ImageFilter.SHARPEN)
                    img = ImageEnhance.Contrast(img).enhance(1.5)
                
                # 引擎1: Tesseract
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang=lang)
                blocks = []
                scale = 0.5 if enhance else 1.0
                for i in range(len(data['text'])):
                    if data['text'][i].strip():
                        blocks.append({
                            'text': data['text'][i],
                            'conf': data['conf'][i],
                            'x': int(data['left'][i] * scale), 'y': int(data['top'][i] * scale),
                            'w': int(data['width'][i] * scale), 'h': int(data['height'][i] * scale)
                        })
                
                high_conf = [b for b in blocks if int(b.get('conf',0)) > 40]
                if high_conf:
                    return {"ok": True, "text_blocks": blocks, "high_conf_blocks": len(high_conf),
                            "total_blocks": len(blocks), "mode": "tesseract-enhanced"}
                
                # 引擎2: 尝试EasyOCR
                try:
                    import easyocr
                    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
                    # 转numpy
                    import numpy as np
                    img_np = np.array(img)
                    results = reader.readtext(img_np)
                    blocks = []
                    for bbox, text, conf in results:
                        x1, y1 = bbox[0]
                        x2, y2 = bbox[2]
                        blocks.append({
                            'text': text, 'conf': int(conf * 100),
                            'x': int(x1 * scale), 'y': int(y1 * scale),
                            'w': int((x2-x1) * scale), 'h': int((y2-y1) * scale)
                        })
                    return {"ok": True, "text_blocks": blocks, "total_blocks": len(blocks),
                            "mode": "easyocr-fallback"}
                except ImportError:
                    pass
                
                # 低质量也返回
                return {"ok": True, "text_blocks": blocks, "total_blocks": len(blocks), 
                        "mode": "tesseract-lowconf"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def read_all(self) -> dict:
        """OCR全文扫描 — 整屏OCR，被find/find_all/to_annotated调用"""
        import mss
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                return self.read(
                    x=monitor["left"], y=monitor["top"],
                    w=monitor["width"], h=monitor["height"]
                )
        except Exception as e:
            return {"ok": False, "error": str(e)[:100], "text_blocks": []}
    
    def find(self, text: str) -> dict:
        """在屏幕上找文字，返回 {"ok": True/False, "found": True/False, "x": int, "y": int, ...}"""
        result = self.read_all()
        if not result.get("ok"):
            return {"ok": False, "found": False, "error": result.get("error", "read_all failed")}
        blocks = result.get("text_blocks", [])
        for block in blocks:
            if text.lower() in block.get("text", "").lower():
                x = block.get("x", 0) + block.get("w", 0) // 2
                y = block.get("y", 0) + block.get("h", 0) // 2
                return {
                    "ok": True, "found": True,
                    "x": int(x), "y": int(y),
                    "text": block.get("text", ""),
                    "conf": block.get("conf", 0),
                }
        return {"ok": True, "found": False, "message": f"'{text}' 未在屏幕上找到"}

    def find_all(self, text: str) -> dict:
        """找所有匹配位置，返回 {"ok": True/False, "found": int, "positions": [(x,y), ...]}"""
        result = self.read_all()
        if not result.get("ok"):
            return {"ok": False, "found": 0, "error": result.get("error", "read_all failed"), "positions": []}
        blocks = result.get("text_blocks", [])
        positions = []
        for block in blocks:
            if text.lower() in block.get("text", "").lower():
                x = block.get("x", 0) + block.get("w", 0) // 2
                y = block.get("y", 0) + block.get("h", 0) // 2
                positions.append({
                    "x": int(x), "y": int(y),
                    "text": block.get("text", ""),
                    "conf": block.get("conf", 0),
                })
        return {"ok": True, "found": len(positions), "positions": positions}
    
    def analyze(self, question: str = "屏幕上有什么?") -> dict:
        """AI视觉分析 — 看屏幕，理解内容 (通过temp文件避免命令行溢出)"""
        import tempfile, os as _os
        img = self.see()
        if not img.get("ok"):
            return img
        # 写入临时文件避免base64超命令行限制
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.write(base64.b64decode(img.get("image", "")))
        tmp.close()
        result = _call_cap("ai_vision", "describe", {
            "path": tmp.name,
            "question": question
        }, timeout=30)
        try: _os.unlink(tmp.name)
        except: pass
        return result
    
    def look_deep(self, x: int = 0, y: int = 0, w: int = 1920, h: int = 1080) -> dict:
        """深度视觉 — 多通道增强扫描，用于远程桌面等低质量画面
        通道1: 标准OCR 
        通道2: 2x增强OCR (锐化+对比度+放大)
        通道3: 4x超分辨率OCR
        通道4: AI视觉兜底
        返回合并去重结果
        """
        results = []
        
        # 通道1: 标准
        r1 = self.read(x, y, w, h, enhance=False)
        if r1.get('ok'):
            results.append(('standard', r1))
        
        # 通道2: 增强
        r2 = self.read(x, y, w, h, enhance=True)
        if r2.get('ok'):
            results.append(('enhanced', r2))
        
        # 通道3: 4x超分
        try:
            from PIL import Image, ImageFilter, ImageEnhance
            import mss, io as _io
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": w, "height": h}
                frame = sct.grab(monitor)
                img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
                img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
                img = img.filter(ImageFilter.SHARPEN)
                img = ImageEnhance.Contrast(img).enhance(2.0)
                import pytesseract as _pt
                data = _pt.image_to_data(img, output_type=_pt.Output.DICT, lang='chi_sim+eng')
                blocks = []
                for i in range(len(data['text'])):
                    if data['text'][i].strip():
                        blocks.append({
                            'text': data['text'][i], 'conf': data['conf'][i],
                            'x': int(data['left'][i]*0.25), 'y': int(data['top'][i]*0.25),
                            'w': int(data['width'][i]*0.25), 'h': int(data['height'][i]*0.25)
                        })
                results.append(('4x_superres', {"ok": True, "text_blocks": blocks, "mode": "4x-superres"}))
        except:
            pass
        
        # 通道4: AI兜底
        if not any(len(r[1].get('text_blocks',[])) > 10 for r in results):
            ai = self.analyze("详细描述屏幕上的所有内容，包括窗口、文字、按钮、图标")
            results.append(('ai_vision', {"ok": True, "ai_description": ai, "mode": "ai-vision"}))
        
        # 合并去重
        seen = set()
        merged = []
        for channel, r in results:
            for b in r.get('text_blocks', []):
                key = (b['text'].strip().lower(), b['x']//20, b['y']//20)
                if key not in seen:
                    seen.add(key)
                    merged.append(b)
        
        return {
            "ok": True,
            "total_blocks": len(merged),
            "text_blocks": merged,
            "channels_used": [c for c, _ in results],
            "mode": "look_deep"
        }
    
    def colors_at(self, x: int, y: int) -> dict:
        """获取屏幕某点的颜色(RGB+HEX)"""
        try:
            import pyautogui
            c = pyautogui.pixel(x, y)
            rgb = [c[0], c[1], c[2]]
            return {"ok": True, "x": x, "y": y, "rgb": rgb, 
                    "hex": f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
                    "is_dark": sum(rgb) < 384, "is_light": sum(rgb) > 640}
        except:
            return {"ok": False, "error": "color read failed"}
    
    def dominant_colors(self, region: dict = None, count: int = 5) -> dict:
        """屏幕区域的主色调"""
        img = self.see(region)
        if not img.get("ok"):
            return img
        # Use PIL for color analysis
        try:
            from PIL import Image
            import io
            img_data = __import__('base64').b64decode(img.get("image", ""))
            pil_img = Image.open(io.BytesIO(img_data))
            pil_img = pil_img.resize((100, int(100 * pil_img.height / pil_img.width)))  # shrink for speed
            pixels = list(pil_img.getdata())
            from collections import Counter
            # Quantize colors
            quantized = [(r//32*32, g//32*32, b//32*32) for r,g,b in pixels[:1000]]
            top = Counter(quantized).most_common(count)
            return {"ok": True, "colors": [
                {"rgb": list(c), "hex": f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}", "pct": round(n/len(pixels[:1000])*100,1)}
                for c, n in top
            ]}
        except:
            return {"ok": False, "error": "PIL not available"}
    
    def compare(self, region1: dict, region2: dict) -> dict:
        """比较屏幕两个区域是否相同"""
        img1 = self.see(region1)
        img2 = self.see(region2)
        if not img1.get("ok") or not img2.get("ok"):
            return {"ok": False, "error": "capture failed"}
        same = img1.get("image", "") == img2.get("image", "")
        return {"ok": True, "same": same}
    
    def wait_for(self, text: str, timeout: float = 30.0, interval: float = 0.5) -> Optional[tuple]:
        """等待屏幕上出现指定文字, 返回坐标"""
        import time
        start = time.time()
        while time.time() - start < timeout:
            pos = self.find(text)
            if pos:
                return pos
            time.sleep(interval)
        return None
    

    def record(self, duration: float = 10.0, fps: int = 5) -> dict:
        """录制屏幕视频(GIF) — duration秒, fps帧率"""
        import time
        frames = []
        start = time.time()
        interval = 1.0 / fps
        while time.time() - start < duration:
            frame = self.see()
            if frame.get("ok"):
                frames.append(frame.get("image", ""))
            time.sleep(interval)
        return {"ok": True, "frames": len(frames), "duration": duration, "fps": fps}

    def wait_until_gone(self, text: str, timeout: float = 30.0, interval: float = 0.5) -> bool:
        """等待屏幕上的文字消失"""
        import time
        start = time.time()
        while time.time() - start < timeout:
            if not self.find(text):
                return True
            time.sleep(interval)
        return False


    def to_image(self, filepath: str = None) -> dict:
        """保存截图为PNG文件"""
        import os, mss
        from PIL import Image
        path = filepath or os.path.expanduser('~/.gbt/screenshots/ai_view.png')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with mss.mss() as sct:
                frame = sct.grab(sct.monitors[1])
                img = Image.frombytes('RGB', frame.size, frame.bgra, 'raw', 'BGRX')
                img.save(path, format='PNG')
                return {'ok': True, 'file': path, 'size': os.path.getsize(path)}
        except Exception as e:
            return {'ok': False, 'error': str(e)[:100]}
    
    def to_gif(self, duration: float = 5.0, fps: int = 15, filepath: str = None, 
               annotate: callable = None) -> dict:
        """录制屏幕为GIF动图 — duration秒, fps帧率
        annotate(frame_index, pil_image) 可选标注回调
        """
        import os, time, io, mss
        from PIL import Image
        path = filepath or os.path.expanduser(f'~/.gbt/screenshots/ai_recording_{int(time.time())}.gif')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        frames = []
        interval = 1.0 / fps
        start = time.time()
        idx = 0
        
        old_mss = None
        try:
            with mss.mss() as sct:
                while time.time() - start < duration:
                    frame = sct.grab(sct.monitors[1])
                    img = Image.frombytes('RGB', frame.size, frame.bgra, 'raw', 'BGRX')
                    if annotate:
                        img = annotate(idx, img) or img
                    # Resize for GIF (keep reasonable size)
                    img = img.resize((img.width//2, img.height//2), Image.LANCZOS)
                    frames.append(img)
                    idx += 1
                    time.sleep(max(0, interval - 0.01))
        except:
            # Fallback to BetterCam if mss fails
            pass
        
        if frames:
            frames[0].save(path, save_all=True, append_images=frames[1:], 
                          optimize=True, duration=int(1000/fps), loop=0)
            return {'ok': True, 'file': path, 'frames': len(frames), 
                    'duration': duration, 'fps': fps, 'size': os.path.getsize(path)}
        return {'ok': False, 'error': 'no frames captured'}
    
    def to_annotated(self, filepath: str = None) -> dict:
        """截图并标注找到的所有文字位置"""
        import os, io, base64
        from PIL import Image, ImageDraw, ImageFont
        path = filepath or os.path.expanduser('~/.gbt/screenshots/ai_annotated.png')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        import mss
        try:
            with mss.mss() as sct:
                frame = sct.grab(sct.monitors[1])
                img = Image.frombytes('RGB', frame.size, frame.bgra, 'raw', 'BGRX')
        except Exception as e:
            return {'ok': False, 'error': str(e)[:100]}
        draw = ImageDraw.Draw(img)
        
        # OCR找文字
        text_result = self.read_all()
        if text_result.get('ok'):
            for block in text_result.get('text_blocks', []):
                x, y, w, h = block.get('x',0), block.get('y',0), block.get('w',0), block.get('h',0)
                if w > 0 and h > 0:
                    draw.rectangle([x, y, x+w, y+h], outline='#00d4aa', width=2)
        
        img.save(path)
        return {'ok': True, 'file': path, 'blocks': len(text_result.get('text_blocks',[])),
                'size': os.path.getsize(path)}

    @property
    def is_highspeed(self):
        """是否启用高速视觉(240Hz+)"""
        return HAS_BETTERCAM and _get_highspeed_eye() is not None
    
    @property
    def fps(self):
        """当前刷新率"""
        he = _get_highspeed_eye(); return he.fps if he and self.is_highspeed else 10

    # ── 后台视觉 · 人类级眼手并行 ──────────
    
    @property
    def latest(self) -> dict:
        """取最新帧 — 零阻塞，后台buffer即时返回。眼睛一直在看，手随时能动。"""
        global _frame_buffer
        if _frame_buffer is None or not _frame_buffer.is_running:
            return {"ok": False, "error": "not watching, call start_watching() first"}
        return _frame_buffer.latest
    
    @property
    def buffer_stats(self) -> dict:
        """帧缓冲状态 — 不自动启动"""
        global _frame_buffer
        if _frame_buffer is None:
            return {"running": False, "buffer_size": 0}
        return _frame_buffer.stats
    
    def start_watching(self, fps: int = 30):
        """开启后台持续视觉 — 此后eyes.latest即时可用"""
        buf = _get_buffer(fps)
        if not buf.is_running:
            buf.start()
        return {"ok": True, "fps": fps, "buffer_size": buf.stats["buffer_size"]}
    
    def stop_watching(self):
        """停止后台视觉"""
        global _frame_buffer
        if _frame_buffer:
            _frame_buffer.stop()
            _frame_buffer = None
        return {"ok": True}
    
    def watch(self, interval: float = 2.0, duration: float = 60.0):
        """持续监控屏幕 — 生成器, yield每次截图 (兼容旧API)"""
        start = time.time()
        while time.time() - start < duration:
            yield self.see()
            time.sleep(interval)
    
    # ── 电影模式 (Buffer驱动) ──────────────
    
    def movie(self, duration: float = 10.0, fps: int = 30, detect_scenes: bool = True) -> dict:
        """电影模式 — 从后台buffer采样, 不阻塞主线程
        先确保start_watching()已调用, 或自动启动buffer
        """
        fps = max(1, min(fps, 120))
        duration = max(0.1, duration)
        
        buf = _get_buffer(fps)
        if not buf.is_running:
            buf.start()
        
        # 从buffer采样 — 不重新采集, 不累积base64副本
        samples = []
        timestamps = []
        interval = 1.0 / fps
        start = time.time()
        last_ts = 0
        
        while time.time() - start < duration:
            current = buf.latest
            if current.get("ok") and current["timestamp"] - last_ts >= interval * 0.8:
                samples.append(current)
                timestamps.append(current["timestamp"] - start)
                last_ts = current["timestamp"]
            time.sleep(max(0, interval * 0.5))
        
        actual_fps = len(samples) / max(time.time() - start, 0.001)
        result = {
            "ok": True,
            "frames": len(samples),
            "duration": round(time.time() - start, 2),
            "fps_target": fps,
            "fps_actual": round(actual_fps, 1),
            "timestamps": [round(t, 3) for t in timestamps]
        }
        
        if detect_scenes and len(samples) > 1:
            scenes = self._detect_scenes(samples, timestamps)
            result["scene_changes"] = scenes
            result["scene_count"] = len(scenes) + 1
        
        return result
    
    def _detect_scenes(self, frames: list, timestamps: list, threshold: float = 0.15) -> list:
        """场景切换检测 — numpy像素级diff, 无hash捷径"""
        import io as _io
        from PIL import Image
        
        scenes = []
        prev_pixels = None
        
        for i, (frame_dict, ts) in enumerate(zip(frames, timestamps)):
            try:
                img_b64 = frame_dict.get("image", "")
                img = Image.open(_io.BytesIO(base64.b64decode(img_b64)))
                small = img.resize((64, 36))
                pixels = list(small.getdata())
                
                if i == 0:
                    prev_pixels = pixels
                    continue
                
                # 像素级差异率
                diff_count = sum(1 for p, c in zip(prev_pixels, pixels)
                               if abs(p[0]-c[0]) + abs(p[1]-c[1]) + abs(p[2]-c[2]) > 30)
                diff_rate = diff_count / max(len(prev_pixels), 1)
                
                if diff_rate > threshold:
                    scenes.append({
                        "frame_index": i,
                        "timestamp": round(ts, 3),
                        "diff_rate": round(diff_rate, 3)
                    })
                
                prev_pixels = pixels
            except:
                pass
        
        return scenes
    
    def wait_for_async(self, text: str, timeout: float = 30.0, check_interval: float = 0.1) -> Optional[tuple]:
        """等待文字出现 — 非阻塞, 从buffer取帧不卡手
        与旧wait_for不同: 不重新截图, 不time.sleep长间隔, 手可以同时操作
        """
        buf = _get_buffer()
        if not buf.is_running:
            buf.start()
        
        import pytesseract as _pt
        from PIL import Image
        import io as _io
        
        start = time.time()
        while time.time() - start < timeout:
            current = buf.latest
            if not current.get("ok"):
                time.sleep(check_interval)
                continue
            
            try:
                img = Image.open(_io.BytesIO(base64.b64decode(current["image"])))
                data = _pt.image_to_data(img, output_type=_pt.Output.DICT, lang='chi_sim+eng')
                for j in range(len(data['text'])):
                    if data['text'][j].strip() and text.lower() in data['text'][j].lower():
                        x = data['left'][j] + data['width'][j] // 2
                        y = data['top'][j] + data['height'][j] // 2
                        return (int(x), int(y))
            except:
                pass
            
            time.sleep(check_interval)
        
        return None
    
    def movie_record(self, duration: float = 10.0, fps: int = 30, output: str = None) -> dict:
        """录制屏幕为视频文件"""
        import os as _os
        
        if output is None:
            output = _os.path.expanduser(f'~/.gbt/recordings/movie_{int(time.time())}.mp4')
        _os.makedirs(_os.path.dirname(output), exist_ok=True)
        
        he = _get_highspeed_eye()
        if self.is_highspeed and he:
            return he.record(duration, fps, output)
        
        path = output.replace('.mp4', '.gif')
        return self.to_gif(duration, fps, path)
    
    def movie_analyze(self, duration: float = 5.0, fps: int = 5, question: str = "屏幕上在发生什么?") -> dict:
        """看电影+AI理解 — 从buffer采样→场景检测→关键帧AI分析"""
        movie = self.movie(duration, fps, detect_scenes=True)
        if not movie.get("ok"):
            return movie
        
        key_indices = [0]
        for sc in movie.get("scene_changes", []):
            key_indices.append(sc["frame_index"])
        key_indices = key_indices[:5]
        
        analyses = []
        for idx in key_indices:
            # 从buffer取帧, 不重新截
            frame = self.latest
            if frame.get("ok"):
                analysis = _call_cap("ai_vision", "describe", {
                    "image": frame.get("image", ""),
                    "question": question
                }, timeout=30)
                analyses.append({"frame_index": idx, "analysis": analysis})
        
        movie["keyframe_analyses"] = analyses
        movie["question"] = question
        return movie

    # ── 浏览原语 · 刷抖音/朋友圈核心 ──────
    
    def wait_for_stable(self, timeout: float = 5.0, threshold: float = 0.05, stable_frames: int = 3) -> dict:
        """等待屏幕稳定 — 用于滚动后等新内容加载完毕
        连续stable_frames帧变化率<threshold即认为稳定
        """
        buf = _get_buffer()
        if not buf.is_running:
            buf.start()
        
        from PIL import Image
        import io as _io
        
        start = time.time()
        stable_count = 0
        prev_pixels = None
        last_frame_id = -1
        
        while time.time() - start < timeout:
            current = buf.latest
            if not current.get("ok") or current["frame_id"] == last_frame_id:
                time.sleep(0.05)
                continue
            
            last_frame_id = current["frame_id"]
            try:
                img = Image.open(_io.BytesIO(base64.b64decode(current["image"])))
                small = img.resize((64, 36))
                pixels = list(small.getdata())
                
                if prev_pixels is None:
                    prev_pixels = pixels
                    continue
                
                diff_count = sum(1 for p, c in zip(prev_pixels, pixels)
                               if abs(p[0]-c[0]) + abs(p[1]-c[1]) + abs(p[2]-c[2]) > 30)
                diff_rate = diff_count / max(len(prev_pixels), 1)
                
                if diff_rate < threshold:
                    stable_count += 1
                    if stable_count >= stable_frames:
                        return {"ok": True, "stable": True, 
                                "elapsed": round(time.time() - start, 3),
                                "final_diff": round(diff_rate, 4)}
                else:
                    stable_count = 0
                
                prev_pixels = pixels
            except:
                pass
            
            time.sleep(0.05)
        
        return {"ok": True, "stable": False, "elapsed": round(time.time() - start, 3),
                "note": "timeout - screen still changing"}
    
    def capture_stable(self, timeout: float = 5.0) -> dict:
        """等待稳定后截取一帧干净画面 — 浏览用"""
        stable = self.wait_for_stable(timeout)
        frame = self.latest
        frame["stable"] = stable
        return frame
    
    def browse_screen(self, question: str = "这是什么内容? 描述一下") -> dict:
        """看当前屏幕内容并AI分析 — 浏览核心"""
        frame = self.latest
        if not frame.get("ok"):
            return {"ok": False, "error": "no frame available, call start_watching() first"}
        return _call_cap("ai_vision", "describe", {
            "image": frame.get("image", ""),
            "question": question
        }, timeout=30)


class Hands:
    """AI的手 — 键鼠原生操控, 直连pyautogui零延迟"""
    
    def move(self, x: int, y: int) -> dict:
        try:
            import pyautogui
            pyautogui.moveTo(x, y)
            return {"ok": True, "action": "move", "position": [x, y]}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}
    
    def click(self, x: int, y: int) -> dict:
        try:
            import pyautogui
            pyautogui.click(x, y)
            return {"ok": True, "action": "click", "position": [x, y]}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}
    
    def double_click(self, x: int, y: int) -> dict:
        try:
            import pyautogui
            pyautogui.doubleClick(x, y)
            return {"ok": True, "action": "double_click", "position": [x, y]}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}
    
    def right_click(self, x: int, y: int) -> dict:
        try:
            import pyautogui
            pyautogui.rightClick(x, y)
            return {"ok": True, "action": "right_click", "position": [x, y]}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}
    
    def type(self, text: str) -> dict:
        try:
            import pyautogui
            pyautogui.write(text, interval=0.03)
            return {"ok": True, "action": "type", "text_len": len(text)}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}
    
    def press(self, key: str) -> dict:
        try:
            import pyautogui
            pyautogui.press(key)
            return {"ok": True, "action": "press", "key": key}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}
    
    def hotkey(self, *keys) -> dict:
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return {"ok": True, "action": "hotkey", "keys": list(keys)}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}
    
    def drag(self, x1: int, y1: int, x2: int, y2: int) -> dict:
        try:
            import pyautogui
            pyautogui.moveTo(x1, y1)
            pyautogui.drag(x2 - x1, y2 - y1)
            return {"ok": True, "action": "drag", "from": [x1, y1], "to": [x2, y2]}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}
    
    def scroll(self, amount: int) -> dict:
        try:
            import pyautogui
            pyautogui.scroll(amount)
            return {"ok": True, "action": "scroll", "amount": amount}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    # ── 人类级眼手并行 ──────────────────────
    
    def move_to_text(self, text: str, timeout: float = 10.0) -> dict:
        """移动到屏幕上文字的位置并点击 (异步版: 不阻塞手)"""
        from brain.host_body import eyes
        pos = eyes.wait_for_async(text, timeout)
        if pos:
            self.move(pos[0], pos[1])
            self.click(pos[0], pos[1])
            return {"ok": True, "position": pos}
        return {"ok": False, "error": f"\u672a\u627e\u5230: {text}"}
    
    def look_and_click(self, text: str, timeout: float = 10.0) -> dict:
        """看→找→点: 一站式, 手眼并行不互斥"""
        from brain.host_body import eyes
        # 确保后台视觉在运行
        eyes.start_watching(fps=15)
        # 从buffer取帧找文字, 手随时可以同时操作
        pos = eyes.wait_for_async(text, timeout, check_interval=0.05)
        if not pos:
            return {"ok": False, "error": f"\u8d85\u65f6\u672a\u627e\u5230: {text}"}
        self.move(pos[0], pos[1])
        time.sleep(0.05)  # 短暂等待鼠标到位
        self.click(pos[0], pos[1])
        return {"ok": True, "text": text, "position": list(pos), "mode": "async_vision"}
    
    def look_and_type(self, text: str, input_text: str, timeout: float = 10.0) -> dict:
        """找输入框→点击→输入: 一站式"""
        result = self.look_and_click(text, timeout)
        if not result.get("ok"):
            return result
        self.type(input_text)
        return {"ok": True, "found": text, "typed": input_text, "position": result.get("position")}
    
    # ── 浏览原语 · 刷抖音/朋友圈核心 ──────
    
    def browse_scroll(self, direction: str = "down", amount: int = 3, 
                      question: str = "这是什么内容?", wait_stable: bool = True) -> dict:
        """浏览操作: 滚→等稳定→看→AI理解
        一次完整的浏览动作, 返回当前屏内容的AI分析
        """
        from brain.host_body import eyes
        
        # 1. 滚动
        scroll_amount = -abs(amount) if direction == "down" else abs(amount)
        self.scroll(scroll_amount)
        
        # 2. 等新内容加载稳定
        if wait_stable:
            stable = eyes.wait_for_stable(timeout=3.0)
        
        # 3. AI分析当前屏
        analysis = eyes.browse_screen(question)
        
        return {
            "ok": True,
            "action": "browse_scroll",
            "direction": direction,
            "stable": stable.get("stable", True) if wait_stable else None,
            "analysis": analysis
        }
    
    def browse_feed(self, count: int = 10, direction: str = "down", 
                    question: str = "这是什么内容? 简要描述", 
                    pause_on: str = None) -> list:
        """连续刷 feed — 抖音/朋友圈/微博自动浏览
        
        count: 刷多少屏
        direction: 滚动方向
        question: 每屏问AI什么问题
        pause_on: 如果AI回复包含此关键词则暂停(如"感兴趣"、"广告")
        
        返回每屏的分析结果列表
        """
        from brain.host_body import eyes
        
        # 确保后台视觉在运行
        eyes.start_watching(fps=15)
        
        results = []
        for i in range(count):
            result = self.browse_scroll(direction, amount=3, question=question)
            results.append(result)
            
            # 检查是否需要暂停
            if pause_on and result.get("analysis", {}).get("ok"):
                analysis_text = str(result["analysis"]).lower()
                if pause_on.lower() in analysis_text:
                    results.append({"paused": True, "reason": f"matched: {pause_on}", "at_index": i})
                    break
        
        return {
            "ok": True,
            "action": "browse_feed",
            "total": len(results),
            "results": results
        }
    
    def browse_and_interact(self, scroll_count: int = 5,
                            interact_text: str = "评论",
                            action: str = "click") -> dict:
        """浏览并互动 — 刷到内容→找到互动入口→操作
        如: 刷5屏→找到"评论"按钮→点击
        """
        from brain.host_body import eyes
        
        eyes.start_watching(fps=15)
        
        for i in range(scroll_count):
            # 先看当前屏有没有互动入口
            pos = eyes.wait_for_async(interact_text, timeout=1.0, check_interval=0.1)
            if pos:
                if action == "click":
                    self.click(pos[0], pos[1])
                elif action == "move":
                    self.move(pos[0], pos[1])
                return {"ok": True, "found_at_scroll": i, "position": list(pos), 
                        "action": action, "text": interact_text}
            
            # 没找到, 继续滚
            self.browse_scroll("down", amount=3, wait_stable=True, 
                             question="快速扫描: 有没有" + interact_text + "?")
        
        return {"ok": False, "error": f"浏览{scroll_count}屏后未找到: {interact_text}"}

    
    def type_and_enter(self, text: str) -> dict:
        """输入文字并按回车"""
        self.type(text)
        return self.press("enter")
    
    def select_all_copy(self) -> dict:
        """全选+复制 — 返回剪贴板内容"""
        self.hotkey("ctrl", "a")
        time.sleep(0.1)
        self.hotkey("ctrl", "c")
        time.sleep(0.1)
        try:
            import pyperclip
            return {"ok": True, "clipboard": pyperclip.paste()}
        except:
            return {"ok": True, "note": "copied, pyperclip unavailable"}
    
    def paste(self) -> dict:
        """粘贴"""
        return self.hotkey("ctrl", "v")
    
    def screenshot_region(self, x: int, y: int, w: int, h: int) -> dict:
        """截取屏幕区域"""
        from brain.host_body import eyes
        return eyes.see({"x": x, "y": y, "w": w, "h": h})


# 全局单例 — AI可以直接 import 使用
eyes = Eyes()
hands = Hands()
