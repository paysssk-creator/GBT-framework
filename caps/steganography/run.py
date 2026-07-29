# 开发者：自由的风
"""steganography/run.py — LSB隐写术"""
import sys, json
from pathlib import Path

def do_hide(params):
    carrier = params.get("carrier", params.get("image", ""))
    data = params.get("data", "")
    output = params.get("output", carrier + ".steg.png" if carrier else "output.png")
    if not carrier or not data: return {"ok": False, "error": "缺少carrier和data"}
    try:
        from PIL import Image
        img = Image.open(carrier).convert("RGB")
        pixels = list(img.getdata())
        binary = ''.join(format(ord(c), '08b') for c in data) + '00000000'
        if len(binary) > len(pixels) * 3:
            return {"ok": False, "error": "数据太大({}B > 容量{}B)".format(len(binary)//8, len(pixels)*3//8)}
        new_pixels = []
        idx = 0
        for r, g, b in pixels:
            nr = (r & 0xFE) | int(binary[idx]) if idx < len(binary) else r; idx += 1
            ng = (g & 0xFE) | int(binary[idx]) if idx < len(binary) else g; idx += 1
            nb = (b & 0xFE) | int(binary[idx]) if idx < len(binary) else b; idx += 1
            new_pixels.append((nr, ng, nb))
        Image.new("RGB", img.size).putdata(new_pixels).save(output)
        return {"ok": True, "cap": "steganography", "domain": "攻击域", "output": output, "data_len": len(data)}
    except ImportError:
        return {"ok": False, "error": "Pillow未安装"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_extract(params):
    image = params.get("image", "")
    if not image: return {"ok": False, "error": "缺少image"}
    try:
        from PIL import Image
        pixels = list(Image.open(image).convert("RGB").getdata())
        bits = []
        for r, g, b in pixels:
            bits.extend([str(r & 1), str(g & 1), str(b & 1)])
        chars = []
        for i in range(0, len(bits) - 7, 8):
            ch = chr(int(''.join(bits[i:i+8]), 2))
            if ch == '\x00': break
            chars.append(ch)
        data = ''.join(chars)
        return {"ok": True, "cap": "steganography", "action": "extract", "data": data[:5000], "len": len(data)}
    except ImportError:
        return {"ok": False, "error": "Pillow未安装"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

HANDLERS = {"hide": do_hide, "extract": do_extract}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "hide"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))
