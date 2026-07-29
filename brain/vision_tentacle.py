# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/vision_tentacle.py -- 视觉触手 · 亿万传输通道 v1.0
==========================================================
一根触手 = 一种"看"的方式。不是只有OCR。

传输通道:
  📸 屏幕直采    — mss 实时截屏 → base64
  📋 剪贴板      — 从剪贴板读取图片
  🌐 URL下载     — HTTP/HTTPS 远程图片
  📁 本地文件    — 任意路径图片文件
  🎥 视频帧      — 视频逐帧采集
  📷 摄像头      — 实时摄像头捕获
  🖥 窗口截图    — 指定窗口截图
  🔗 Base64直传  — 直接接收base64图片数据
  📦 压缩包      — zip/tar内图片提取
  🌊 流式传输    — WebSocket/pipe 实时流

每根触手: 采集 → 预处理 → OCR → 皮层分析 → 结构化输出
"""
import sys, os, json, base64, io, time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

VISION_CACHE = Path.home() / ".gbt" / "vision"
VISION_CACHE.mkdir(parents=True, exist_ok=True)


class VisionTentacle:
    """视觉触手 — 一根触手一种传输通道"""

    def __init__(self):
        self._last_result = None
        self._capture_count = 0

    # ═══════════════ 传输通道 ═══════════════

    def from_screen(self) -> dict:
        """📸 屏幕直采 — mss 实时截屏"""
        try:
            from brain.host_body import eyes
            screen = eyes.see()
            if not screen.get("ok"):
                return {"ok": False, "channel": "screen", "error": screen.get("error", "capture failed")}
            img_data = base64.b64decode(screen["image"])
            return {
                "ok": True,
                "channel": "screen",
                "size": screen.get("size", [0, 0]),
                "image_base64": screen["image"],
                "image_bytes": img_data,
                "format": "PNG",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {"ok": False, "channel": "screen", "error": str(e)[:200]}

    def from_clipboard(self) -> dict:
        """📋 剪贴板 — 读取剪贴板中的图片"""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is None:
                return {"ok": False, "channel": "clipboard", "error": "no image in clipboard"}
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            return {
                "ok": True,
                "channel": "clipboard",
                "size": list(img.size),
                "image_base64": base64.b64encode(img_bytes).decode(),
                "image_bytes": img_bytes,
                "format": "PNG",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {"ok": False, "channel": "clipboard", "error": str(e)[:200]}

    def from_url(self, url: str, timeout: int = 30) -> dict:
        """🌐 URL下载 — HTTP/HTTPS 远程图片"""
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "GBT-VisionTentacle/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                img_bytes = resp.read()
                content_type = resp.headers.get("Content-Type", "")
            # Validate it's an image
            from PIL import Image
            img = Image.open(io.BytesIO(img_bytes))
            buf = io.BytesIO()
            fmt = img.format or "PNG"
            img.save(buf, format=fmt)
            img_bytes = buf.getvalue()
            return {
                "ok": True,
                "channel": "url",
                "source": url,
                "size": list(img.size),
                "image_base64": base64.b64encode(img_bytes).decode(),
                "image_bytes": img_bytes,
                "format": fmt,
                "content_type": content_type,
                "file_size": len(img_bytes),
                "timestamp": time.time(),
            }
        except Exception as e:
            return {"ok": False, "channel": "url", "source": url, "error": str(e)[:200]}

    def from_file(self, filepath: str) -> dict:
        """📁 本地文件 — 任意路径图片文件"""
        try:
            fp = Path(filepath)
            if not fp.exists():
                return {"ok": False, "channel": "file", "source": filepath, "error": "file not found"}
            img_bytes = fp.read_bytes()
            from PIL import Image
            img = Image.open(io.BytesIO(img_bytes))
            buf = io.BytesIO()
            fmt = img.format or fp.suffix.upper().lstrip(".") or "PNG"
            img.save(buf, format=fmt)
            img_bytes = buf.getvalue()
            return {
                "ok": True,
                "channel": "file",
                "source": str(fp.absolute()),
                "size": list(img.size),
                "image_base64": base64.b64encode(img_bytes).decode(),
                "image_bytes": img_bytes,
                "format": fmt,
                "file_size": len(img_bytes),
                "filename": fp.name,
                "timestamp": time.time(),
            }
        except Exception as e:
            return {"ok": False, "channel": "file", "source": filepath, "error": str(e)[:200]}

    def from_video_frame(self, video_path: str, frame_index: int = 0) -> dict:
        """🎥 视频帧 — 从视频文件中提取指定帧"""
        try:
            import subprocess, tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            # Use ffmpeg to extract frame
            r = subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", video_path,
                "-vf", f"select=eq(n\\,{frame_index})",
                "-vframes", "1", tmp.name
            ], capture_output=True, timeout=30)
            if r.returncode != 0:
                return {"ok": False, "channel": "video_frame", "source": video_path, "error": "ffmpeg failed"}
            result = self.from_file(tmp.name)
            result["channel"] = "video_frame"
            result["source"] = video_path
            result["frame_index"] = frame_index
            os.unlink(tmp.name)
            return result
        except FileNotFoundError:
            return {"ok": False, "channel": "video_frame", "source": video_path, "error": "ffmpeg not installed"}
        except Exception as e:
            return {"ok": False, "channel": "video_frame", "source": video_path, "error": str(e)[:200]}

    def from_camera(self, camera_index: int = 0) -> dict:
        """📷 摄像头 — 实时摄像头捕获一帧"""
        try:
            import cv2
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                return {"ok": False, "channel": "camera", "error": f"camera {camera_index} not available"}
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return {"ok": False, "channel": "camera", "error": "failed to read frame"}
            import numpy as np
            from PIL import Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            img_bytes = buf.getvalue()
            return {
                "ok": True,
                "channel": "camera",
                "camera_index": camera_index,
                "size": list(img.size),
                "image_base64": base64.b64encode(img_bytes).decode(),
                "image_bytes": img_bytes,
                "format": "JPEG",
                "timestamp": time.time(),
            }
        except ImportError:
            return {"ok": False, "channel": "camera", "error": "opencv-python not installed"}
        except Exception as e:
            return {"ok": False, "channel": "camera", "error": str(e)[:200]}

    def from_window(self, window_title: str = "") -> dict:
        """🖥 窗口截图 — 指定窗口截图（需要pygetwindow）"""
        try:
            import pygetwindow as gw
            from PIL import ImageGrab
            if window_title:
                windows = [w for w in gw.getAllWindows() if window_title.lower() in w.title.lower()]
                if not windows:
                    return {"ok": False, "channel": "window", "error": f"window '{window_title}' not found"}
                win = windows[0]
            else:
                win = gw.getActiveWindow()
            if win is None:
                return {"ok": False, "channel": "window", "error": "no active window"}
            bbox = (win.left, win.top, win.right, win.bottom)
            img = ImageGrab.grab(bbox)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            return {
                "ok": True,
                "channel": "window",
                "window_title": win.title,
                "size": list(img.size),
                "image_base64": base64.b64encode(img_bytes).decode(),
                "image_bytes": img_bytes,
                "format": "PNG",
                "timestamp": time.time(),
            }
        except ImportError:
            return {"ok": False, "channel": "window", "error": "pygetwindow not installed"}
        except Exception as e:
            return {"ok": False, "channel": "window", "error": str(e)[:200]}

    def from_base64(self, b64_data: str) -> dict:
        """🔗 Base64直传 — 直接接收base64图片数据"""
        try:
            img_bytes = base64.b64decode(b64_data)
            from PIL import Image
            img = Image.open(io.BytesIO(img_bytes))
            buf = io.BytesIO()
            fmt = img.format or "PNG"
            img.save(buf, format=fmt)
            img_bytes = buf.getvalue()
            return {
                "ok": True,
                "channel": "base64",
                "size": list(img.size),
                "image_base64": base64.b64encode(img_bytes).decode(),
                "image_bytes": img_bytes,
                "format": fmt,
                "timestamp": time.time(),
            }
        except Exception as e:
            return {"ok": False, "channel": "base64", "error": str(e)[:200]}

    def from_directory(self, dirpath: str, pattern: str = "*") -> list:
        """📂 批量目录 — 扫描目录下所有图片"""
        results = []
        dp = Path(dirpath)
        if not dp.exists():
            return [{"ok": False, "channel": "directory", "error": "directory not found"}]
        exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".ico"}
        for f in sorted(dp.rglob(pattern)):
            if f.suffix.lower() in exts:
                r = self.from_file(str(f))
                results.append(r)
        return results

    # ═══════════════ 处理管道 ═══════════════

    def _ocr(self, img_bytes: bytes, lang: str = "chi_sim+eng") -> dict:
        """OCR 文字识别"""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(img, lang=lang, config="--psm 6")
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang=lang)
            blocks = []
            for i in range(len(data["text"])):
                t = data["text"][i].strip()
                if t and int(data["conf"][i]) > 30:
                    blocks.append({
                        "text": t,
                        "x": data["left"][i],
                        "y": data["top"][i],
                        "w": data["width"][i],
                        "h": data["height"][i],
                        "conf": int(data["conf"][i]),
                    })
            return {
                "ok": True,
                "text": text.strip(),
                "blocks": blocks,
                "block_count": len(blocks),
                "lang": lang,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def _analyze(self, img_bytes: bytes) -> dict:
        """皮层分析 — 三层视觉结构"""
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(img_bytes))
            w, h = img.size
            # Basic visual analysis
            from collections import Counter
            pixels = list(img.getdata())
            color_sample = pixels[::max(1, len(pixels) // 1000)]

            # Dominant colors
            if img.mode == "RGBA":
                rgb_pixels = [(r, g, b) for r, g, b, a in color_sample]
            elif img.mode == "RGB":
                rgb_pixels = list(color_sample)
            else:
                rgb_pixels = [(0, 0, 0)] * len(color_sample)

            color_counter = Counter(rgb_pixels)
            dominant = color_counter.most_common(5)

            # Brightness
            brightness = sum(r + g + b for r, g, b in rgb_pixels) / max(1, len(rgb_pixels)) / 3

            # Edge density (simple)
            try:
                img_gray = img.convert("L")
                edges = img_gray.filter(__import__("PIL.ImageFilter").ImageFilter.FIND_EDGES)
                edge_data = list(edges.getdata())
                edge_density = sum(1 for p in edge_data if p > 30) / max(1, len(edge_data))
            except:
                edge_density = 0

            return {
                "ok": True,
                "size": [w, h],
                "mode": img.mode,
                "dominant_colors": [{"rgb": list(c), "count": n} for c, n in dominant],
                "brightness": round(brightness, 1),
                "edge_density": round(edge_density, 3),
                "aspect_ratio": round(w / h, 2) if h > 0 else 0,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def process(self, capture_result: dict, do_ocr: bool = True, do_analyze: bool = True) -> dict:
        """完整处理管道: 采集 → OCR → 皮层分析"""
        if not capture_result.get("ok"):
            return capture_result

        result = dict(capture_result)
        img_bytes = capture_result.get("image_bytes")

        if img_bytes and do_ocr:
            result["ocr"] = self._ocr(img_bytes)

        if img_bytes and do_analyze:
            result["analysis"] = self._analyze(img_bytes)

        # Remove raw bytes from output (too large), keep base64
        result.pop("image_bytes", None)


        self._last_result = result
        self._capture_count += 1
        return result

    def devour(self, capture_result: dict) -> dict:
        """视觉吞噬 - 从看到的画面中吸收知识"""
        devoured = []
        ocr_data = capture_result.get("ocr", {})
        if ocr_data.get("ok") and ocr_data.get("text"):
            text = ocr_data["text"]
            # 吞噬URL
            import re
            urls = re.findall(r'https?://[^\s]+', text)
            for url in urls[:5]:
                devoured.append({"type": "url", "value": url[:120]})
            # 吞噬代码片段
            code_blocks = re.findall(r'(def |class |import |from |async |await )\S+', text)
            for cb in code_blocks[:5]:
                devoured.append({"type": "code", "value": cb[:80]})
            # 吞噬关键词
            keywords = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
            from collections import Counter
            for kw, cnt in Counter(keywords).most_common(5):
                if cnt >= 2:
                    devoured.append({"type": "keyword", "value": kw, "count": cnt})
        return {"ok": True, "devoured": len(devoured), "items": devoured[:10]}

    def save(self, result: dict, prefix: str = "vision") -> Optional[Path]:
        """保存采集结果到缓存"""
        if not result.get("ok") or "image_base64" not in result:
            return None
        ts = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{result.get('channel','?')}_{ts}.png"
        filepath = VISION_CACHE / filename
        img_bytes = base64.b64decode(result["image_base64"])
        filepath.write_bytes(img_bytes)
        return filepath


# ═══════════════ 全局触手 ═══════════════

_vision: Optional[VisionTentacle] = None


def get_vision() -> VisionTentacle:
    global _vision
    if _vision is None:
        _vision = VisionTentacle()
    return _vision


def see(channel: str = "screen", **kwargs) -> dict:
    """快捷: 通过指定通道"看"
    
    channel options:
      screen    - 屏幕直采
      clipboard - 剪贴板
      url       - 远程URL (需传 url=)
      file      - 本地文件 (需传 filepath=)
      camera    - 摄像头
      window    - 窗口截图 (可选 window_title=)
      base64    - Base64直传 (需传 b64_data=)
    """
    v = get_vision()

    channels = {
        "screen": lambda: v.from_screen(),
        "clipboard": lambda: v.from_clipboard(),
        "url": lambda: v.from_url(kwargs.get("url", "")),
        "file": lambda: v.from_file(kwargs.get("filepath", "")),
        "camera": lambda: v.from_camera(kwargs.get("camera_index", 0)),
        "window": lambda: v.from_window(kwargs.get("window_title", "")),
        "base64": lambda: v.from_base64(kwargs.get("b64_data", "")),
    }

    if channel not in channels:
        return {"ok": False, "error": f"unknown channel: {channel}. Available: {list(channels.keys())}"}

    capture = channels[channel]()
    return v.process(capture)


def see_all() -> dict:
    """全通道视觉 — 同时从所有可用通道采集"""
    v = get_vision()
    results = {}

    # Screen (always try first)
    results["screen"] = v.process(v.from_screen())

    # Clipboard
    try:
        clip = v.from_clipboard()
        if clip.get("ok"):
            results["clipboard"] = v.process(clip)
    except:
        pass

    return {
        "ok": True,
        "timestamp": time.time(),
        "channels": list(results.keys()),
        "results": results,
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="GBT 视觉触手 — 亿万传输通道")
    p.add_argument("--channel", default="screen",
                   choices=["screen", "clipboard", "url", "file", "camera", "window", "base64", "all"],
                   help="传输通道")
    p.add_argument("--url", help="远程图片URL")
    p.add_argument("--file", dest="filepath", help="本地图片路径")
    p.add_argument("--window-title", help="窗口标题")
    p.add_argument("--b64", dest="b64_data", help="Base64图片数据")
    p.add_argument("--no-ocr", action="store_true", help="跳过OCR")
    p.add_argument("--save", action="store_true", help="保存到缓存")
    args = p.parse_args()

    v = get_vision()

    if args.channel == "all":
        result = see_all()
        print(json.dumps({k: {"ok": v.get("ok"), "channel": v.get("channel")}
                          for k, v in result.get("results", {}).items()},
                         ensure_ascii=False, indent=2))
    else:
        kwargs = {}
        if args.url:
            kwargs["url"] = args.url
        if args.filepath:
            kwargs["filepath"] = args.filepath
        if args.window_title:
            kwargs["window_title"] = args.window_title
        if args.b64_data:
            kwargs["b64_data"] = args.b64_data

        result = see(args.channel, **kwargs)
        do_ocr = not args.no_ocr

        if result.get("ok"):
            ch = result.get("channel", "?")
            sz = result.get("size", [0, 0])
            print(f"Channel: {ch} | {sz[0]}x{sz[1]}px")

            ocr_data = result.get("ocr", {})
            if ocr_data.get("ok"):
                print(f"OCR: {ocr_data.get('block_count', 0)} blocks")
                lines = [l for l in ocr_data.get("text", "").split(chr(10)) if l.strip()]
                for line in lines[:10]:
                    print(f"  {line[:120]}")

            analysis = result.get("analysis", {})
            if analysis.get("ok"):
                print(f"Analysis: {analysis.get('mode')} | brightness={analysis.get('brightness')} | edges={analysis.get('edge_density')}")

            if args.save:
                saved = v.save(result)
                if saved:
                    print(f"Saved: {saved}")
        else:
            print(f"FAIL [{result.get('channel')}]: {result.get('error')}")
