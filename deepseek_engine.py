# deepseek_engine.py
"""
轻量版“DeepSeek”解析器（本地实现）
- 支持口语化自然语言解析（中文/英文）
- 支持从上传灵感图片中提取主色与基于关键词的款式建议（轻量识图）
返回结构化字典，供 app.py / ai_optimizer 使用。
"""

import re
from typing import Dict, Any
from PIL import Image

# 支持的预置品类（可扩展）
GARMENT_OPTIONS = [
    "连衣裙", "衬衫", "T恤", "裤子", "牛仔裤", "外套", "夹克", "旗袍", "半身裙", "风衣", "西装"
]

# 常用颜色词映射（可以扩充）
COLOR_MAP = {
    "白": "#FFFFFF", "白色": "#FFFFFF",
    "黑": "#000000", "黑色": "#000000",
    "红": "#FF0000", "红色": "#FF0000", "酒红": "#8B0000",
    "粉": "#FFB6C1", "粉色": "#FFB6C1",
    "蓝": "#007BFF", "蓝色": "#007BFF", "深蓝": "#003366",
    "绿": "#28A745", "绿色": "#28A745",
    "灰": "#6C757D", "米白": "#F5F5DC", "驼色": "#D2B48C",
    "beige": "#F5F5DC", "navy": "#001f3f"
}

RE_NUM = re.compile(r"(\d{2,3})")

def _extract_hex(text: str):
    m = re.search(r"(#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}))", text)
    if m:
        return m.group(1).upper()
    return None

def _color_from_words(text: str):
    t = text.lower()
    for k, v in COLOR_MAP.items():
        if k in t:
            return v
    return None

def _dominant_color_from_image(pil_img: Image.Image) -> str:
    """
    简单主色提取：缩小图像后统计最常见像素（不使用外部 kmeans）
    返回 HEX 字符串
    """
    try:
        small = pil_img.convert("RGB").resize((80, 80))
        # getcolors returns list of (count, (r,g,b))
        colors = small.getcolors(80 * 80)
        if not colors:
            return "#FFB6C1"
        colors.sort(key=lambda x: x[0], reverse=True)
        dominant = colors[0][1]
        return '#{:02X}{:02X}{:02X}'.format(*dominant)
    except Exception:
        return "#FFB6C1"

def _suggest_garment_from_text(text: str):
    t = text.lower()
    for g in GARMENT_OPTIONS:
        if g in t:
            return g
    # 英文匹配
    if "dress" in t:
        return "连衣裙"
    if "shirt" in t:
        return "衬衫"
    if "jacket" in t or "coat" in t:
        return "外套"
    if "pants" in t or "jeans" in t:
        return "裤子"
    return None

def _extract_measurements(text: str, fallback=None):
    if fallback is None:
        fallback = {"height":165, "bust":88, "waist":68, "hip":94}
    out = {}
    # 按关键词抓取
    for k in ["height","bust","waist","hip"]:
        pat = None
        if k=="height":
            pat = re.compile(r"(身高|height)[:：]?\s*(\d{2,3})", flags=re.I)
        elif k=="bust":
            pat = re.compile(r"(胸围|bust)[:：]?\s*(\d{2,3})", flags=re.I)
        elif k=="waist":
            pat = re.compile(r"(腰围|waist)[:：]?\s*(\d{2,3})", flags=re.I)
        else:
            pat = re.compile(r"(臀围|hip)[:：]?\s*(\d{2,3})", flags=re.I)
        m = pat.search(text)
        if m:
            try:
                out[k] = int(m.group(2))
            except:
                pass
    # fallback: 取所有数字的顺序
    if not all(k in out for k in ["height","bust","waist","hip"]):
        nums = RE_NUM.findall(text)
        if nums:
            if "height" not in out and len(nums)>=1:
                out["height"] = int(nums[0])
            if "bust" not in out and len(nums)>=2:
                out["bust"] = int(nums[1])
            if "waist" not in out and len(nums)>=3:
                out["waist"] = int(nums[2])
            if "hip" not in out and len(nums)>=4:
                out["hip"] = int(nums[3])
    # final fill
    for k,v in fallback.items():
        out.setdefault(k, v)
    return out

def parse_with_deepseek(user_text: str, inspiration_image: Any = None) -> Dict[str, Any]:
    """
    解析用户自然语言（优先）并结合灵感图片（可选）产出结构化参数。
    inspiration_image: PIL.Image 或 None
    返回 dict，保证包含关键字段。
    """
    try:
        text = (user_text or "").strip()
        low = text.lower()
        result = {
            "garment": "连衣裙",
            "fit": "Regular",
            "length": "Regular",
            "color": "#FFB6C1",
            "material": "纯棉",
            "height": 165,
            "bust": 88,
            "waist": 68,
            "hip": 94,
            "notes": text,
            "style_keywords": []
        }

        if not text and inspiration_image is None:
            return result

        # 1) color: hex in text -> explicit color; else color words; else extract from image
        hex_value = _extract_hex(text)
        if hex_value:
            result["color"] = hex_value
        else:
            word_color = _color_from_words(text)
            if word_color:
                result["color"] = word_color

        # 2) garment from text or image filename or basic heuristics
        g = _suggest_garment_from_text(text)
        if g:
            result["garment"] = g

        # 3) fit words
        if any(w in low for w in ["修身","slim","紧身"]):
            result["fit"] = "Slim"
        elif any(w in low for w in ["宽松","oversize","relaxed"]):
            result["fit"] = "Relaxed"
        else:
            # keep default
            pass

        # 4) material
        m = re.search(r"(真丝|丝绸|丝|棉|牛仔|牛仔布|羊毛|毛|麻|蕾丝|皮|皮革|涤纶|锦纶|丝绸)", text, flags=re.I)
        if m:
            result["material"] = m.group(0)

        # 5) measurements
        measures = _extract_measurements(text)
        result.update(measures)

        # 6) style keywords heuristics
        if any(w in low for w in ["飘逸","轻薄","透气"]):
            result["style_keywords"].append("light_floating")
        if any(w in low for w in ["正式","礼服","formal"]):
            result["style_keywords"].append("formal")
        if any(w in low for w in ["运动","运动风"]):
            result["style_keywords"].append("sporty")
        # include raw tokens like '荷叶边' '泡泡袖'
        decorations = []
        for deco in ["荷叶边","泡泡袖","吊带","露背","开叉","印花","刺绣","拼接","拉链","扣子","口袋","褶皱"]:
            if deco in text:
                decorations.append(deco)
        result["style_keywords"].extend(decorations)

        # 7) image-based augmentation (主色 + try to guess garment from ratio)
        if inspiration_image is not None:
            try:
                dom_color = _dominant_color_from_image(inspiration_image)
                if dom_color:
                    result["color"] = dom_color
                # try to guess garment by aspect ratio of main silhouette: tall ratio -> dress/coat; wide -> top/shorts
                w, h = inspiration_image.size
                if h / max(1, w) > 1.4:
                    # likely full-length photo -> dress/coat
                    if result.get("garment") == "连衣裙":
                        pass
                    else:
                        # if no strong garment from text, suggest dress/coat
                        if _suggest_garment_from_text(text) is None:
                            result["garment"] = "连衣裙"
                else:
                    if _suggest_garment_from_text(text) is None:
                        # short ratio -> top / pants
                        result["garment"] = "衬衫"
            except Exception:
                pass

        return result
    except Exception as e:
        # 任何异常回退到一个最小结构
        return {
            "garment": "连衣裙", "fit":"Regular", "length":"Regular",
            "color":"#FFB6C1","material":"纯棉","height":165,"bust":88,"waist":68,"hip":94,"notes": user_text or ""
        }