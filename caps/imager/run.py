# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""imager/run.py — 图片处理工具：压缩/缩放/格式转换/信息/裁剪/水印"""
import sys, json, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

_sandbox = Path(__file__).parent.parent.parent


def _resolve(path: str) -> Path:
    """将相对路径或绝对路径解析为沙箱内的绝对路径"""
    p = Path(path)
    if p.is_absolute():
        return p
    return (_sandbox / p).resolve()


def _resolve_output(params: dict, input_path: Path, extension: str = None) -> Path:
    """确定输出路径：显式output > 自动生成 _out 后缀"""
    out = params.get("output", "")
    if out:
        return _resolve(out)
    stem = input_path.stem
    ext = extension or input_path.suffix
    return input_path.with_stem(f"{stem}_out").with_suffix(ext)


def _ok(**kwargs) -> dict:
    return {"ok": True, **kwargs}


def _err(msg: str) -> dict:
    return {"ok": False, "error": msg}


# ─── compress: 图片压缩 ───
def do_compress(params: dict) -> dict:
    input_path = _resolve(params.get("input", ""))
    if not input_path.exists():
        return _err(f"文件不存在: {input_path}")

    quality = params.get("quality", 75)
    try:
        quality = int(quality)
    except (ValueError, TypeError):
        return _err("quality 必须是整数")
    quality = max(10, min(95, quality))

    try:
        img = Image.open(input_path)
    except Exception as e:
        return _err(f"无法打开图片: {e}")

    output_path = _resolve_output(params, input_path, input_path.suffix)
    # 压缩：如果是RGBA的JPEG需转RGB
    fmt = output_path.suffix.lower().lstrip(".")
    save_kwargs = {}
    if fmt in ("jpg", "jpeg"):
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        save_kwargs["optimize"] = True
        save_kwargs["quality"] = quality
    elif fmt == "png":
        save_kwargs["optimize"] = True
    elif fmt == "webp":
        save_kwargs["quality"] = quality
    else:
        save_kwargs["quality"] = quality

    img.save(output_path, **save_kwargs)
    in_size = input_path.stat().st_size
    out_size = output_path.stat().st_size
    ratio = f"{(out_size / in_size * 100):.1f}%" if in_size > 0 else "N/A"

    return _ok(
        input=str(input_path),
        output=str(output_path),
        input_size=in_size,
        output_size=out_size,
        ratio=ratio,
        quality=quality,
    )


# ─── resize: 缩放 ───
def do_resize(params: dict) -> dict:
    input_path = _resolve(params.get("input", ""))
    if not input_path.exists():
        return _err(f"文件不存在: {input_path}")

    try:
        img = Image.open(input_path)
    except Exception as e:
        return _err(f"无法打开图片: {e}")

    ow, oh = img.size
    ratio = params.get("ratio", None)
    width = params.get("width", None)
    height = params.get("height", None)

    if ratio is not None:
        try:
            ratio = float(ratio)
        except (ValueError, TypeError):
            return _err("ratio 必须是数字")
        new_w = int(ow * ratio)
        new_h = int(oh * ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    elif width is not None and height is not None:
        try:
            new_w, new_h = int(width), int(height)
        except (ValueError, TypeError):
            return _err("width/height 必须是整数")
        img = img.resize((new_w, new_h), Image.LANCZOS)
    elif width is not None:
        try:
            new_w = int(width)
        except (ValueError, TypeError):
            return _err("width 必须是整数")
        new_h = int(oh * new_w / ow)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    elif height is not None:
        try:
            new_h = int(height)
        except (ValueError, TypeError):
            return _err("height 必须是整数")
        new_w = int(ow * new_h / oh)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    else:
        return _err("请提供 width/height 或 ratio")

    output_path = _resolve_output(params, input_path, input_path.suffix)
    img.save(output_path)

    return _ok(
        input=str(input_path),
        output=str(output_path),
        original_size=[ow, oh],
        new_size=[img.width, img.height],
    )


# ─── convert: 格式转换 ───
def do_convert(params: dict) -> dict:
    input_path = _resolve(params.get("input", ""))
    if not input_path.exists():
        return _err(f"文件不存在: {input_path}")

    target = params.get("format", "").lower().lstrip(".")
    if not target:
        target = Path(params.get("output", "")).suffix.lower().lstrip(".")
    if target not in ("png", "jpg", "jpeg", "webp", "bmp"):
        return _err("格式必须是 png/jpg/webp/bmp 之一")

    try:
        img = Image.open(input_path)
    except Exception as e:
        return _err(f"无法打开图片: {e}")

    ext = ".jpg" if target == "jpeg" else f".{target}"
    output_path = _resolve_output(params, input_path, ext)

    # RGBA → RGB for JPEG
    if ext in (".jpg", ".jpeg") and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    fmt = "JPEG" if target in ("jpg", "jpeg") else target.upper()

    save_kwargs = {}
    if target in ("jpg", "jpeg"):
        save_kwargs["quality"] = params.get("quality", 92)
        save_kwargs["optimize"] = True
    elif target == "png":
        save_kwargs["optimize"] = True
    elif target == "webp":
        save_kwargs["quality"] = params.get("quality", 80)

    img.save(output_path, format=fmt, **save_kwargs)

    return _ok(
        input=str(input_path),
        output=str(output_path),
        from_format=input_path.suffix.lower().lstrip("."),
        to_format=ext.lstrip("."),
        size=[img.width, img.height],
    )


# ─── info: 图片信息 ───
def do_info(params: dict) -> dict:
    input_path = _resolve(params.get("input", ""))
    if not input_path.exists():
        return _err(f"文件不存在: {input_path}")

    try:
        img = Image.open(input_path)
    except Exception as e:
        return _err(f"无法打开图片: {e}")

    file_size = input_path.stat().st_size

    return _ok(
        path=str(input_path),
        width=img.width,
        height=img.height,
        size=[img.width, img.height],
        format=img.format or input_path.suffix.upper().lstrip("."),
        mode=img.mode,
        file_size=file_size,
        file_size_human=_fmt_size(file_size),
    )


# ─── crop: 裁剪 ───
def do_crop(params: dict) -> dict:
    input_path = _resolve(params.get("input", ""))
    if not input_path.exists():
        return _err(f"文件不存在: {input_path}")

    try:
        x, y, w, h = int(params["x"]), int(params["y"]), int(params["w"]), int(params["h"])
    except (KeyError, ValueError, TypeError) as e:
        return _err(f"x/y/w/h 参数缺失或非整数: {e}")

    try:
        img = Image.open(input_path)
    except Exception as e:
        return _err(f"无法打开图片: {e}")

    # 裁剪区域校正（负值/超出视为合法则由PIL报错）
    region = (x, y, x + w, y + h)
    try:
        cropped = img.crop(region)
    except Exception as e:
        return _err(f"裁剪失败: {e}")

    output_path = _resolve_output(params, input_path, input_path.suffix)
    cropped.save(output_path)

    return _ok(
        input=str(input_path),
        output=str(output_path),
        original_size=[img.width, img.height],
        crop_region={"x": x, "y": y, "w": w, "h": h},
        new_size=[cropped.width, cropped.height],
    )


# ─── watermark: 文字水印 ───
def do_watermark(params: dict) -> dict:
    input_path = _resolve(params.get("input", ""))
    if not input_path.exists():
        return _err(f"文件不存在: {input_path}")

    text = params.get("text", "Watermark")
    position = params.get("position", "br").lower()
    if position not in ("tl", "tr", "bl", "br", "center"):
        return _err("position 必须是 tl/tr/bl/br/center")

    try:
        img = Image.open(input_path)
    except Exception as e:
        return _err(f"无法打开图片: {e}")

    # 确保 RGBA 以便支持透明度
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # 字体
    font_size = params.get("font_size", None)
    if font_size is not None:
        try:
            font_size = int(font_size)
        except (ValueError, TypeError):
            return _err("font_size 必须是整数")
    else:
        font_size = max(16, min(img.width, img.height) // 20)

    # 颜色解析
    color_hex = params.get("color", "#ffffff")
    try:
        color = _hex_to_rgba(color_hex)
    except Exception:
        return _err(f"颜色格式错误: {color_hex}，请用 #RRGGBB")

    opacity = params.get("opacity", None)
    if opacity is not None:
        try:
            opacity = int(opacity)
        except (ValueError, TypeError):
            return _err("opacity 必须是整数 0-255")
        color = (*color[:3], max(0, min(255, opacity)))

    # 字体加载
    font = _load_font(font_size)

    # 水印图层
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 测量文字尺寸
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = 20

    # 定位
    if position == "tl":
        pos = (margin, margin)
    elif position == "tr":
        pos = (img.width - tw - margin, margin)
    elif position == "bl":
        pos = (margin, img.height - th - margin)
    elif position == "br":
        pos = (img.width - tw - margin, img.height - th - margin)
    else:  # center
        pos = ((img.width - tw) // 2, (img.height - th) // 2)

    draw.text(pos, text, fill=color, font=font)

    # 合并
    result = Image.alpha_composite(img, overlay)

    output_path = _resolve_output(params, input_path, input_path.suffix)
    if output_path.suffix.lower() in (".jpg", ".jpeg"):
        result = result.convert("RGB")
    result.save(output_path)

    return _ok(
        input=str(input_path),
        output=str(output_path),
        text=text,
        position=position,
        font_size=font_size,
        color=color_hex,
        size=[result.width, result.height],
    )


# ─── 工具函数 ───
def _fmt_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _hex_to_rgba(hex_str: str) -> tuple:
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    elif len(h) == 8:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))
    raise ValueError(f"无效的十六进制颜色: {hex_str}")


def _load_font(size: int):
    """加载字体，回退到默认字体"""
    # 尝试常见系统字体
    font_paths = []
    if sys.platform == "win32":
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",      # 黑体
            "C:/Windows/Fonts/arial.ttf",
        ]
    else:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ─── Handler 注册 ───
handlers = {
    "compress":  do_compress,
    "resize":    do_resize,
    "convert":   do_convert,
    "info":      do_info,
    "crop":      do_crop,
    "watermark": do_watermark,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ""
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = handlers.get(action)
    if handler:
        result = handler(params)
    else:
        result = {
            "ok": False,
            "error": f"未知操作: {action}",
            "available": list(handlers.keys()),
        }
    print(json.dumps(result, ensure_ascii=False, default=str))
