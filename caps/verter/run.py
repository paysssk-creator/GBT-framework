# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""verter/run.py — 万能转换器：单位换算/进制转换/颜色转换/数字格式化/实时汇率，零外部依赖"""
import sys, json, math, re


# ═══════════════════════════════════════════
# 1. unit — 单位换算
# ═══════════════════════════════════════════

# ─── 长度 (基准: 米) ───
_LENGTH = {
    "nm": 1e-9, "μm": 1e-6, "um": 1e-6, "mm": 1e-3, "cm": 1e-2,
    "dm": 1e-1, "m": 1, "km": 1e3,
    "in": 0.0254, "inch": 0.0254, "ft": 0.3048, "foot": 0.3048, "feet": 0.3048,
    "yd": 0.9144, "yard": 0.9144, "mile": 1609.344, "mi": 1609.344,
    "nmi": 1852, "海里": 1852,
    "尺": 1/3, "寸": 0.1/3, "丈": 10/3, "里": 500,
}

# ─── 重量 (基准: 克) ───
_WEIGHT = {
    "mg": 1e-3, "g": 1, "kg": 1e3, "t": 1e6, "ton": 1e6,
    "oz": 28.3495, "lb": 453.592, "lbs": 453.592, "pound": 453.592,
    "st": 6350.29, "stone": 6350.29,
    "斤": 500, "两": 50, "钱": 5,
    "ct": 0.2,  # 克拉
}

# ─── 温度 (特殊处理) ───
# ─── 存储 (基准: 字节) ───
_STORAGE = {
    "b": 1, "byte": 1, "bytes": 1,
    "kb": 1024, "kib": 1024,
    "mb": 1024**2, "mib": 1024**2,
    "gb": 1024**3, "gib": 1024**3,
    "tb": 1024**4, "tib": 1024**4,
    "pb": 1024**5, "pib": 1024**5,
}

# ─── 时间 (基准: 秒) ───
_TIME = {
    "ns": 1e-9, "μs": 1e-6, "us": 1e-6, "ms": 1e-3,
    "s": 1, "sec": 1, "second": 1, "seconds": 1,
    "min": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hour": 3600, "hours": 3600,
    "d": 86400, "day": 86400, "days": 86400,
    "w": 604800, "week": 604800, "weeks": 604800,
    "mo": 2592000, "month": 2592000, "months": 2592000,
    "y": 31536000, "year": 31536000, "years": 31536000,
}

# ─── 面积 (基准: 平方米) ───
_AREA = {
    "mm²": 1e-6, "mm2": 1e-6, "cm²": 1e-4, "cm2": 1e-4,
    "dm²": 1e-2, "dm2": 1e-2, "m²": 1, "m2": 1,
    "km²": 1e6, "km2": 1e6,
    "ha": 1e4, "公顷": 1e4, "亩": 2000/3,
    "sqft": 0.092903, "sqm": 1,
    "acre": 4046.86, "英亩": 4046.86,
}

# ─── 体积 (基准: 升) ───
_VOLUME = {
    "ml": 1e-3, "cl": 1e-2, "dl": 1e-1, "l": 1, "litre": 1, "liter": 1,
    "m³": 1000, "m3": 1000, "cm³": 1e-3, "cm3": 1e-3,
    "gal": 3.78541, "gallon": 3.78541,  # US gallon
    "ukgal": 4.54609,  # UK gallon
    "qt": 0.946353, "quart": 0.946353,
    "pt": 0.473176, "pint": 0.473176,
    "floz": 0.0295735,  # US fluid ounce
    "cup": 0.236588,
    "tsp": 0.00492892, "tbsp": 0.0147868,
}

# ─── 速度 (基准: m/s) ───
_SPEED = {
    "m/s": 1, "km/h": 1/3.6, "kmh": 1/3.6,
    "mph": 0.44704, "mile/h": 0.44704,
    "knot": 0.514444, "kn": 0.514444, "节": 0.514444,
    "ft/s": 0.3048, "fts": 0.3048,
    "c": 299792458,  # 光速
}

# ─── 压强 (基准: Pa) ───
_PRESSURE = {
    "pa": 1, "kpa": 1e3, "mpa": 1e6, "gpa": 1e9,
    "bar": 1e5, "mbar": 100,
    "atm": 101325,
    "mmhg": 133.322, "torr": 133.322,
    "psi": 6894.76,
}

# ─── 分类映射 ───
_UNIT_FAMILIES = {
    "length": _LENGTH, "weight": _WEIGHT, "storage": _STORAGE,
    "time": _TIME, "area": _AREA, "volume": _VOLUME,
    "speed": _SPEED, "pressure": _PRESSURE,
    "temperature": None,  # 特殊处理
}

# 构建单位→家族映射
_UNIT_TO_FAMILY = {}
for _fam_name, _fam_dict in _UNIT_FAMILIES.items():
    if _fam_dict is not None:
        for _ukey in _fam_dict:
            _UNIT_TO_FAMILY[_ukey] = _fam_name

# 温度别名也加入映射
for _tk in ["c", "°c", "celsius", "摄氏", "摄氏度", "f", "°f", "fahrenheit", "华氏", "华氏度",
            "k", "kelvin", "开尔文", "开氏", "开"]:
    _UNIT_TO_FAMILY[_tk.lower()] = "temperature"


def _temp_convert(value: float, from_unit: str, to_unit: str, precision: int = 6) -> float:
    """温度特殊转换: C→F→K"""
    # 先转 Celsius
    fu = from_unit[0]
    if fu == "f":
        c = (value - 32) * 5 / 9
    elif fu == "k":
        c = value - 273.15
    else:
        c = value

    # 从 Celsius 转到目标
    tu = to_unit[0]
    if tu == "f":
        return round(c * 9 / 5 + 32, precision)
    elif tu == "k":
        return round(c + 273.15, precision)
    else:
        return round(c, precision)


def do_unit(params: dict) -> dict:
    value = params.get("value", 0)
    from_u = (params.get("from", "") or "").strip().lower()
    to_u = (params.get("to", "") or "").strip().lower()

    if from_u == to_u:
        return {"ok": True, "value": value, "from": from_u, "to": to_u, "result": value}

    # 智能缩写匹配
    from_family = _UNIT_TO_FAMILY.get(from_u)
    to_family = _UNIT_TO_FAMILY.get(to_u)

    if not from_family:
        return {"ok": False, "error": f"未知来源单位: {from_u}"}
    if not to_family:
        return {"ok": False, "error": f"未知目标单位: {to_u}"}
    if from_family != to_family:
        return {"ok": False, "error": f"单位类型不匹配: {from_family} vs {to_family}"}

    try:
        v = float(value)
    except (ValueError, TypeError):
        return {"ok": False, "error": f"非数字: {value}"}

    if from_family == "temperature":
        result = _temp_convert(v, from_u, to_u)
    else:
        family = _UNIT_FAMILIES[from_family]
        # 通过基准单位转换
        base_val = v * family[from_u]
        result = base_val / family[to_u]
        # 对微小浮点误差做智能四舍五入
        if abs(result) < 1e-10:
            result = 0.0
        elif abs(result) >= 1:
            result = round(result, 10)

    return {"ok": True, "value": v, "from": from_u, "to": to_u, "result": result}


# ═══════════════════════════════════════════
# 2. base — 进制转换
# ═══════════════════════════════════════════

_VALID_BASES = {2, 8, 10, 16, 36}
_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def do_base(params: dict) -> dict:
    value = str(params.get("value", "0")).strip()
    from_base = params.get("from", 10)
    to_base = params.get("to", 10)

    try:
        from_base = int(from_base)
        to_base = int(to_base)
    except (ValueError, TypeError):
        return {"ok": False, "error": "进制必须是整数"}

    if from_base not in _VALID_BASES:
        return {"ok": False, "error": f"来源进制不支持，可用: {sorted(_VALID_BASES)}"}
    if to_base not in _VALID_BASES:
        return {"ok": False, "error": f"目标进制不支持，可用: {sorted(_VALID_BASES)}"}

    # 解析小数部分
    frac_part = ""
    int_part = value.upper().lstrip("-+")
    neg = value.startswith("-")

    if "." in int_part:
        int_part, frac_part = int_part.split(".", 1)

    # 字符串转十进制整数
    try:
        dec_int = int(int_part, from_base) if int_part else 0
    except ValueError:
        return {"ok": False, "error": f"'{value}' 不是合法的 {from_base} 进制数"}

    # 小数部分转十进制
    dec_frac = 0.0
    if frac_part:
        try:
            for i, ch in enumerate(frac_part, 1):
                digit = _DIGITS.index(ch)
                if digit >= from_base:
                    raise ValueError
                dec_frac += digit * (from_base ** -i)
        except (ValueError, IndexError):
            return {"ok": False, "error": f"'{value}' 不是合法的 {from_base} 进制数"}

    dec_val = dec_int + dec_frac
    if neg:
        dec_val = -dec_val

    # 转目标进制
    out_neg = dec_val < 0
    n = int(abs(dec_val))
    frac = abs(dec_val) - n

    if n == 0:
        out_int = "0"
    else:
        out_int = ""
        while n > 0:
            out_int = _DIGITS[n % to_base] + out_int
            n //= to_base

    # 小数部分 (最多15位)
    out_frac = ""
    if frac > 0:
        seen = set()
        for _ in range(20):
            frac *= to_base
            digit = int(frac)
            out_frac += _DIGITS[digit]
            frac -= digit
            if frac == 0:
                break
            # 循环小数检测
            key = round(frac, 10)
            if key in seen:
                break
            seen.add(key)

    result = ("-" if out_neg else "") + out_int
    if out_frac:
        result += "." + out_frac

    return {"ok": True, "value": value, "from": from_base, "to": to_base, "result": result, "decimal": dec_val}


# ═══════════════════════════════════════════
# 3. color — 颜色转换
# ═══════════════════════════════════════════

_HEX_RE = re.compile(r"^#?([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
_RGB_RE = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)")
_HSL_RE = re.compile(r"hsla?\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*(?:,\s*([\d.]+)\s*)?\)")


def _hex_to_rgb(hex_str: str) -> tuple:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
    return r, g, b, a


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple:
    rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
    mx = max(rn, gn, bn)
    mn = min(rn, gn, bn)
    l = (mx + mn) / 2

    if mx == mn:
        h = s = 0.0
    else:
        delta = mx - mn
        s = delta / (2 - mx - mn) if l > 0.5 else delta / (mx + mn)

        if mx == rn:
            h = ((gn - bn) / delta) % 6
        elif mx == gn:
            h = (bn - rn) / delta + 2
        else:
            h = (rn - gn) / delta + 4
        h *= 60

    return round(h, 1), round(s * 100, 1), round(l * 100, 1)


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple:
    s /= 100
    l /= 100
    h /= 360

    if s == 0:
        v = round(l * 255)
        return v, v, v

    def _hue2rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q

    r = round(_hue2rgb(p, q, h + 1/3) * 255)
    g = round(_hue2rgb(p, q, h) * 255)
    b = round(_hue2rgb(p, q, h - 1/3) * 255)
    return r, g, b


def _parse_color_string(val: str) -> dict:
    """Parse a color from string format: hex, rgb(), hsl(), or named."""
    val = val.strip()
    # hex
    if _HEX_RE.match(val):
        r, g, b, a = _hex_to_rgb(val)
        h, s, l = _rgb_to_hsl(r, g, b)
        return {"hex": _rgb_to_hex(r, g, b), "rgb": f"rgb({r},{g},{b})",
                "hsl": f"hsl({h},{s}%,{l}%)", "r": r, "g": g, "b": b, "h": h, "s": s, "l": l}
    # rgb()
    m = _RGB_RE.match(val)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        h, s, l = _rgb_to_hsl(r, g, b)
        return {"hex": _rgb_to_hex(r, g, b), "rgb": f"rgb({r},{g},{b})",
                "hsl": f"hsl({h},{s}%,{l}%)", "r": r, "g": g, "b": b, "h": h, "s": s, "l": l}
    # hsl()
    m = _HSL_RE.match(val)
    if m:
        h, s, l = int(m.group(1)), int(m.group(2)), int(m.group(3))
        r, g, b = _hsl_to_rgb(h, s, l)
        return {"hex": _rgb_to_hex(r, g, b), "rgb": f"rgb({r},{g},{b})",
                "hsl": f"hsl({h},{s}%,{l}%)", "r": r, "g": g, "b": b, "h": h, "s": s, "l": l}
    return None


_COLOR_NAMES = {
    "red": "#FF0000", "green": "#008000", "blue": "#0000FF", "white": "#FFFFFF",
    "black": "#000000", "yellow": "#FFFF00", "cyan": "#00FFFF", "magenta": "#FF00FF",
    "gray": "#808080", "grey": "#808080", "orange": "#FFA500", "purple": "#800080",
    "pink": "#FFC0CB", "brown": "#A52A2A", "navy": "#000080", "teal": "#008080",
    "lime": "#00FF00", "maroon": "#800000", "olive": "#808000", "silver": "#C0C0C0",
    "aqua": "#00FFFF", "gold": "#FFD700", "coral": "#FF7F50", "indigo": "#4B0082",
    "violet": "#EE82EE", "turquoise": "#40E0D0", "salmon": "#FA8072", "plum": "#DDA0DD",
    "crimson": "#DC143C", "chocolate": "#D2691E", "tomato": "#FF6347",
}


def do_color(params: dict) -> dict:
    action = (params.get("action", "") or "").strip().lower()

    # --- parse: 智能解析任意颜色字符串 ---
    if action == "parse":
        val = params.get("value", params.get("color", ""))
        if not val:
            return {"ok": False, "error": "缺少颜色值"}
        # 命名颜色
        if val.lower() in _COLOR_NAMES:
            val = _COLOR_NAMES[val.lower()]
        result = _parse_color_string(val)
        if result:
            result["ok"] = True
            return result
        return {"ok": False, "error": f"无法解析颜色: {val}"}

    # --- hex2rgb ---
    if action == "hex2rgb":
        hex_val = params.get("value", params.get("hex", "")).strip()
        if not hex_val:
            return {"ok": False, "error": "缺少 hex 参数"}
        try:
            r, g, b, a = _hex_to_rgb(hex_val)
            return {"ok": True, "hex": _rgb_to_hex(r, g, b), "r": r, "g": g, "b": b,
                    "rgb": f"rgb({r},{g},{b})", "css": f"#{r:02X}{g:02X}{b:02X}"}
        except Exception as e:
            return {"ok": False, "error": f"无效HEX: {hex_val}, {e}"}

    # --- rgb2hex ---
    if action == "rgb2hex":
        r = params.get("r", params.get("red", 0))
        g = params.get("g", params.get("green", 0))
        b = params.get("b", params.get("blue", 0))
        try:
            r, g, b = int(r), int(g), int(b)
            for v in (r, g, b):
                if not 0 <= v <= 255:
                    return {"ok": False, "error": f"RGB值超出0-255范围: {r},{g},{b}"}
            return {"ok": True, "hex": _rgb_to_hex(r, g, b), "css": f"#{r:02X}{g:02X}{b:02X}",
                    "r": r, "g": g, "b": b, "rgb": f"rgb({r},{g},{b})"}
        except (ValueError, TypeError) as e:
            return {"ok": False, "error": f"无效RGB值: {e}"}

    # --- hex2hsl ---
    if action == "hex2hsl":
        hex_val = params.get("value", params.get("hex", "")).strip()
        if not hex_val:
            return {"ok": False, "error": "缺少 hex 参数"}
        try:
            r, g, b, a = _hex_to_rgb(hex_val)
            h, s, l = _rgb_to_hsl(r, g, b)
            return {"ok": True, "hex": _rgb_to_hex(r, g, b), "h": h, "s": s, "l": l,
                    "hsl": f"hsl({h},{s}%,{l}%)", "css": f"hsl({h},{s}%,{l}%)"}
        except Exception as e:
            return {"ok": False, "error": f"无效HEX: {hex_val}, {e}"}

    # --- rgb2hsl ---
    if action == "rgb2hsl":
        r = params.get("r", params.get("red", 0))
        g = params.get("g", params.get("green", 0))
        b = params.get("b", params.get("blue", 0))
        try:
            r, g, b = int(r), int(g), int(b)
            for v in (r, g, b):
                if not 0 <= v <= 255:
                    return {"ok": False, "error": f"RGB值超出0-255范围"}
            h, s, l = _rgb_to_hsl(r, g, b)
            hex_v = _rgb_to_hex(r, g, b)
            return {"ok": True, "hex": hex_v, "rgb": f"rgb({r},{g},{b})",
                    "h": h, "s": s, "l": l, "hsl": f"hsl({h},{s}%,{l}%)",
                    "css": f"hsl({h},{s}%,{l}%)"}
        except (ValueError, TypeError) as e:
            return {"ok": False, "error": f"无效RGB值: {e}"}

    # --- hsl2rgb ---
    if action == "hsl2rgb":
        h = params.get("h", params.get("hue", 0))
        s = params.get("s", params.get("saturation", 0))
        l = params.get("l", params.get("lightness", 0))
        try:
            h, s, l = float(h), float(s), float(l)
            if not 0 <= h <= 360:
                return {"ok": False, "error": "H需在0-360之间"}
            if not 0 <= s <= 100 or not 0 <= l <= 100:
                return {"ok": False, "error": "S和L需在0-100之间"}
            r, g, b = _hsl_to_rgb(h, s, l)
            hex_v = _rgb_to_hex(r, g, b)
            return {"ok": True, "hex": hex_v, "rgb": f"rgb({r},{g},{b})",
                    "r": r, "g": g, "b": b, "h": h, "s": s, "l": l,
                    "hsl": f"hsl({h},{s}%,{l}%)", "css": f"rgb({r},{g},{b})"}
        except (ValueError, TypeError) as e:
            return {"ok": False, "error": f"无效HSL值: {e}"}

    # 默认：智能parse
    val = params.get("value", params.get("color", ""))
    if val:
        if val.lower() in _COLOR_NAMES:
            val = _COLOR_NAMES[val.lower()]
        result = _parse_color_string(val)
        if result:
            result["ok"] = True
            return result
    return {"ok": False, "error": f"未知action: {action}，可用: hex2rgb, rgb2hex, hex2hsl, rgb2hsl, hsl2rgb, parse"}


# ═══════════════════════════════════════════
# 4. number — 数字格式化
# ═══════════════════════════════════════════

_CN_NUM = "零一二三四五六七八九"
_CN_UNIT = ["", "十", "百", "千"]
_CN_BIG = ["", "万", "亿", "万亿", "兆"]
_CN_DEC = "角分"


def _cn_upper_section(n: int) -> str:
    """四位以内中文大写"""
    if n == 0:
        return "零"
    digits = []
    has_zero = False
    for i in range(4):
        d = n % 10
        n //= 10
        if d == 0:
            if digits and digits[-1] != "零":
                has_zero = True
        else:
            if has_zero and digits:
                digits.append("零")
                has_zero = False
            digits.append(_CN_UNIT[i])
            digits.append(_CN_NUM[d])
    digits.reverse()
    result = "".join(digits)
    # 十→一十
    if result == "一十":
        result = "十"
    elif result.startswith("一十"):
        result = result[1:]
    # 去尾零
    result = result.rstrip("零")
    return result or "零"


def _num_to_cn_upper(n: int) -> str:
    """整数→中文大写"""
    if n == 0:
        return "零"
    neg = n < 0
    n = abs(n)
    sections = []
    while n > 0:
        sections.append(n % 10000)
        n //= 10000
    result = ""
    for i, sec in enumerate(sections):
        if sec == 0:
            continue
        sec_str = _cn_upper_section(sec)
        result = sec_str + _CN_BIG[i] + result
    if neg:
        result = "负" + result
    return result


def _num_to_cn_money(n: float) -> str:
    """金额→中文大写"""
    neg = n < 0
    n = abs(n)
    int_part = int(n)
    frac_part = round((n - int_part) * 100)

    result = _num_to_cn_upper(int_part) + "元"

    if frac_part == 0:
        result += "整"
    else:
        jiao = frac_part // 10
        fen = frac_part % 10
        if jiao > 0:
            result += _CN_NUM[jiao] + "角"
        if fen > 0:
            result += _CN_NUM[fen] + "分"
    if neg:
        result = "负" + result
    return result


_ROMAN_MAP = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]

_ROMAN_REV = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000,
              "IV": 4, "IX": 9, "XL": 40, "XC": 90, "CD": 400, "CM": 900}


def _to_roman(n: int) -> str:
    """整数→罗马数字 (1-3999)"""
    if n < 1 or n > 3999:
        raise ValueError("罗马数字范围: 1-3999")
    result = ""
    for val, sym in _ROMAN_MAP:
        while n >= val:
            result += sym
            n -= val
    return result


def _from_roman(s: str) -> int:
    """罗马数字→整数"""
    s = s.upper().strip()
    total = 0
    i = 0
    while i < len(s):
        if i + 1 < len(s) and s[i:i+2] in _ROMAN_REV:
            total += _ROMAN_REV[s[i:i+2]]
            i += 2
        elif s[i] in _ROMAN_REV:
            total += _ROMAN_REV[s[i]]
            i += 1
        else:
            raise ValueError(f"非法罗马数字字符: {s[i]}")
    return total


def do_number(params: dict) -> dict:
    action = (params.get("action", "") or "").strip().lower()
    val = params.get("value", 0)

    try:
        v = float(val)
    except (ValueError, TypeError):
        return {"ok": False, "error": f"非数字: {val}"}

    # --- comma: 千分位 ---
    if action == "comma":
        dec = params.get("decimals")
        if dec is not None:
            v = round(v, int(dec))
            dec = int(dec)
        if v == int(v) and dec is None:
            int_s = f"{int(v):,}"
            return {"ok": True, "value": v, "result": int_s, "formatted": int_s}
        elif dec is not None:
            fmt = f"{{:,.{dec}f}}"
            s = fmt.format(v)
            return {"ok": True, "value": v, "result": s, "formatted": s}
        else:
            s = f"{v:,}"
            return {"ok": True, "value": v, "result": s, "formatted": s}

    # --- cn_upper: 中文大写 ---
    if action == "cn_upper":
        try:
            iv = int(v)
            if v != iv:
                # 有小数 → 按金额处理
                s = _num_to_cn_money(v)
            else:
                s = _num_to_cn_upper(iv)
            return {"ok": True, "value": v, "result": s, "cn_upper": s}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # --- scientific: 科学计数 ---
    if action == "scientific":
        dec = params.get("decimals", 6)
        try:
            dec = int(dec)
        except (ValueError, TypeError):
            dec = 6
        s = f"{v:.{dec}e}"
        return {"ok": True, "value": v, "result": s, "scientific": s}

    # --- percent: 百分比 ---
    if action == "percent":
        dec = params.get("decimals", 2)
        try:
            dec = int(dec)
        except (ValueError, TypeError):
            dec = 2
        pct = v * 100
        s = f"{pct:.{dec}f}%"
        return {"ok": True, "value": v, "result": s, "percent": s, "pct_value": pct}

    # --- round: 保留小数 ---
    if action == "round":
        dec = params.get("decimals", 2)
        try:
            dec = int(dec)
        except (ValueError, TypeError):
            dec = 2
        rv = round(v, dec)
        return {"ok": True, "value": v, "result": rv, "rounded": rv, "decimals": dec}

    # --- filesize: 文件大小 ---
    if action == "filesize":
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        size = abs(v)
        idx = 0
        while size >= 1024 and idx < len(units) - 1:
            size /= 1024
            idx += 1
        sign = "-" if v < 0 else ""
        dec = params.get("decimals", 2)
        try:
            dec = int(dec)
        except (ValueError, TypeError):
            dec = 2
        s = f"{sign}{size:.{dec}f} {units[idx]}"
        return {"ok": True, "value": v, "result": s, "size": size, "unit": units[idx]}

    # --- roman: 罗马数字 ---
    if action == "roman":
        try:
            iv = int(v)
            if iv != v:
                return {"ok": False, "error": "罗马数字仅支持整数"}
            s = _to_roman(iv)
            return {"ok": True, "value": v, "result": s, "roman": s}
        except ValueError as e:
            return {"ok": False, "error": str(e)}

    # --- from_roman: 罗马数字→整数 ---
    if action == "from_roman":
        try:
            s = str(params.get("roman", params.get("value", ""))).strip()
            if not s:
                return {"ok": False, "error": "缺少roman参数"}
            iv = _from_roman(s)
            return {"ok": True, "value": s, "result": iv, "integer": iv}
        except ValueError as e:
            return {"ok": False, "error": str(e)}

    return {"ok": False, "error": f"未知action: {action}，可用: comma, cn_upper, scientific, percent, round, filesize, roman, from_roman"}


# ═══════════════════════════════════════════
# 5. currency — 实时汇率 (固定表)
# ═══════════════════════════════════════════

# 以 USD 为基准的汇率表 (近似值, 2025)
_CURRENCY_RATES = {
    "usd": 1.0, "美元": 1.0, "$": 1.0,
    "cny": 7.25, "rmb": 7.25, "人民币": 7.25, "元": 7.25, "¥": 7.25, "￥": 7.25,
    "eur": 0.92, "欧元": 0.92, "€": 0.92,
    "jpy": 155.0, "日元": 155.0, "円": 155.0,
    "gbp": 0.79, "英镑": 0.79, "£": 0.79,
    "hkd": 7.82, "港币": 7.82, "港元": 7.82,
    "krw": 1380.0, "韩元": 1380.0, "₩": 1380.0,
    "aud": 1.55, "澳元": 1.55,
    "cad": 1.38, "加元": 1.38,
    "chf": 0.90, "瑞士法郎": 0.90,
    "sgd": 1.35, "新加坡元": 1.35,
    "inr": 84.5, "印度卢比": 84.5,
    "rub": 95.0, "俄罗斯卢布": 95.0, "卢布": 95.0,
    "brl": 5.65, "巴西雷亚尔": 5.65,
    "zar": 18.2, "南非兰特": 18.2,
    "try": 33.5, "土耳其里拉": 33.5,
    "mxn": 18.8, "墨西哥比索": 18.8,
    "thb": 35.5, "泰铢": 35.5, "泰币": 35.5,
    "twd": 32.5, "新台币": 32.5, "台币": 32.5,
    "myr": 4.65, "马来西亚林吉特": 4.65,
    "php": 58.0, "菲律宾比索": 58.0,
    "idr": 16200.0, "印尼盾": 16200.0,
    "vnd": 25200.0, "越南盾": 25200.0,
    "aed": 3.67, "阿联酋迪拉姆": 3.67,
    "sar": 3.75, "沙特里亚尔": 3.75,
    "nok": 10.8, "挪威克朗": 10.8,
    "sek": 10.6, "瑞典克朗": 10.6,
    "dkk": 6.88, "丹麦克朗": 6.88,
    "nzd": 1.72, "新西兰元": 1.72,
    "pln": 3.95, "波兰兹罗提": 3.95,
}


def do_currency(params: dict) -> dict:
    value = params.get("value", 0)
    from_cur = (params.get("from", "") or "").strip().lower()
    to_cur = (params.get("to", "") or "").strip().lower()

    try:
        v = float(value)
    except (ValueError, TypeError):
        return {"ok": False, "error": f"非数字: {value}"}

    if from_cur == to_cur:
        return {"ok": True, "value": v, "from": from_cur, "to": to_cur, "result": v}

    if from_cur not in _CURRENCY_RATES:
        return {"ok": False, "error": f"不支持的来源货币: {from_cur}", "supported": sorted(set(_CURRENCY_RATES.keys()))}
    if to_cur not in _CURRENCY_RATES:
        return {"ok": False, "error": f"不支持的目标货币: {to_cur}", "supported": sorted(set(_CURRENCY_RATES.keys()))}

    # 先转USD再转目标
    usd_val = v / _CURRENCY_RATES[from_cur]
    result = usd_val * _CURRENCY_RATES[to_cur]
    result = round(result, 4)

    return {"ok": True, "value": v, "from": from_cur, "to": to_cur, "result": result}


# ═══════════════════════════════════════════
# Handler 注册
# ═══════════════════════════════════════════

HANDLERS = {
    "unit":     do_unit,
    "base":     do_base,
    "color":    do_color,
    "number":   do_number,
    "currency": do_currency,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ""
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
    else:
        result = {
            "ok": False,
            "error": f"未知工具: {action}",
            "available": list(HANDLERS.keys()),
        }
    print(json.dumps(result, ensure_ascii=False, default=str))
