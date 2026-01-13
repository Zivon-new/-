# ============================================================
# text_cleaner.py  （修正版，兼容 Config）
# ============================================================

import re
from scripts.config import Config


# --------------------------
# 基础文本清洗
# --------------------------
def normalize_text(text: str):
    if text is None:
        return ""

    t = str(text).strip()

    # 替换常见分隔符为标准格式
    t = t.replace("—", "-").replace("–", "-").replace("~", "-")

    # 全角变半角
    res = []
    for char in t:
        code = ord(char)
        if 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        res.append(chr(code))
    return "".join(res)


# --------------------------
# 币种识别
# --------------------------
def detect_currency(text: str):
    if not text:
        return None

    for key, val in Config.CURRENCY_ALIAS.items():
        if key.upper() in text.upper():
            return val

    return None


# --------------------------
# 判断是否是价格行
# --------------------------
def is_price_line(text: str):
    """
    识别： 25/kg  18/KG  RMB 200  USD35  20 元/kg 等
    """
    if not text:
        return False

    text2 = normalize_text(text).upper()

    # 单价格式
    if re.search(r"\d+(\.\d+)?\s*/\s*(KG|CBM|件|吨|人|天)", text2):
        return True

    # 整单金额
    if re.search(r"(RMB|USD|CNY)\s*\d+", text2):
        return True

    # 例如 “25/kg + 5/kg”
    if "/" in text2 and any(c.isdigit() for c in text2):
        return True

    return False


# --------------------------
# 判断是否为货物行
# --------------------------
def is_goods_line(text: str):
    """
    例如：
        服务器 2台
        电视 5pcs
        空调 3 台 5000元
    """
    if not text:
        return False

    t = normalize_text(text)

    # 数量格式
    if re.search(r"\d+\s*(台|件|pcs|套|kg|公斤|CBM)", t, flags=re.IGNORECASE):
        return True

    # 有货名，有数量，有可能是货物行
    if any(x in t for x in ["货", "柜", "设备", "机器"]):
        if any(d.isdigit() for d in t):
            return True

    return False


# --------------------------
# 提取数字（用于价格、重量）
# --------------------------
def extract_number(text: str):
    """
    提取如 25/kg → 25
    """
    if not text:
        return None

    m = re.search(r"\d+(\.\d+)?", text)
    if m:
        return float(m.group(0))
    return None
