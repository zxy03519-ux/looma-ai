# deepseek_engine.py
import re
from typing import Dict, Any
from PIL import Image

GARMENT_OPTIONS = [
    "连衣裙", "衬衫", "T恤", "裤子", "牛仔裤", "外套", "夹克", "旗袍", "半身裙", "风衣", "西装", "裙子", "长裤", "短裤"
]

# 扩展颜色词（中英）
COLOR_MAP = {
    "白": "#FFFFFF","白色":"#FFFFFF","雪白":"#FFFFFF",
    "黑": "#000000","黑色":"#000000",
    "红": "#FF0000","红色":"#FF0000","酒红":"#8B0000","深红":"#990000",
    "粉": "#FFB6C1","粉色":"#FFB6C1",
    "蓝": "#007BFF","蓝色":"#007BFF","藏青":"#001f3f","深蓝":"#003366",
    "绿":"#28A745","绿色":"#28A745",
    "黄":"#FFD700","黄色":"#FFD700",
    "灰":"#6C757D","米白":"#F5F5DC","驼色":"#D2B48C",
    "beige":"#F5F5DC","navy":"#001f3f","black":"#000000","white":"#FFFFFF",
    "red":"#FF0000","pink":"#FFC0CB","green":"#28A745","blue":"#007BFF"
}

UNIT_PATTERNS = re.compile(r"(\d{1,3}(?:\.\d+)?)(\s?(?:cm|厘米|mm|毫米|inch|in|英寸|\"))?", flags=re.I)
RE_NUM = re.compile(r"(\d{2,3})")

STYLE_KEYWORDS = [
    "荷叶边","泡泡袖","吊带","露背","开叉","印花","刺绣","拼接","拉链","扣子","口袋","褶皱",
    "宽松","修身","紧身","高腰","低腰","中腰","A字","公主线","收腰","无袖","短袖","七分袖",
    "长袖","立体裁剪","褶皱","荷叶","花边","拼布","丝绸","真丝","棉","牛仔","羊毛","皮革","蕾丝"
]

MEASURE_KEYWORDS = {
    "height": ["身高", "height"],
    "bust": ["胸围", "胸围:", "bust", "bust:"],
    "waist": ["腰围", "腰围:", "waist"],
    "hip": ["臀围", "臀围:", "hip"],
    "shoulder": ["肩宽", "肩宽:"],
    "torso_length": ["上半身长", "上身长", "肩到腰", "肩到腰长"]
}

def _extract_hex(text: str):
    # 先匹配 6 位，再匹配 3 位，避免 #123456 被错误截断为 #123
    m = re.search(r"(#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3}))", text)
    if m:
        return m.group(1).upper()
    return None

def _color_from_words(text: str):
    t = text.lower()
    # 优先匹配更长词条，避免“深蓝”被“蓝”提前命中
    for k in sorted(COLOR_MAP.keys(), key=len, reverse=True):
        v = COLOR_MAP[k]
        if k in t:
            return v
    return None

def _dominant_color_from_image(pil_img: Image.Image) -> str:
    try:
        small = pil_img.convert("RGB").resize((80, 80))
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
    if "dress" in t or "连衣" in t:
        return "连衣裙"
    if "shirt" in t or "衬衫" in t:
        return "衬衫"
    if "jacket" in t or "coat" in t or "夹克" in t or "外套" in t:
        return "外套"
    if "pants" in t or "jeans" in t or "裤" in t:
        return "裤子"
    return None

def _parse_measurements_with_units(text: str):
    """
    查找带单位的数值（如 86cm, 34in, 170cm）并尝试归类到 height/bust/waist/hip/shoulder.
    返回字典，单位统一转换为 cm（若找到 inch 则乘以 2.54）。
    """
    out = {}
    # first, explicit patterns like "胸围86cm", "腰围: 68cm"
    for key, kws in MEASURE_KEYWORDS.items():
        for kw in kws:
            pat = re.compile(rf"{kw}\s*[:：]?\s*(\d{{1,3}}(?:\.\d+)?)(\s?(cm|厘米|mm|毫米|inch|in|英寸|\"))?", flags=re.I)
            m = pat.search(text)
            if m:
                val = float(m.group(1))
                unit = m.group(3)
                if unit and unit.lower() in ["inch","in","英寸","\""]:
                    val = round(val * 2.54, 1)
                elif unit and unit.lower() in ["mm","毫米"]:
                    val = round(val / 10.0, 1)
                out[key] = int(round(val))
    # fallback: find digit sequence occurrences and heuristically assign
    if not out.get("height") or not out.get("bust"):
        all_nums = re.findall(r"\d{2,3}(?:\.\d+)?(?:\s?(?:cm|厘米|mm|毫米|inch|in|英寸|\"))?", text)
        nums = []
        for s in all_nums:
            m = re.match(r"(\d{2,3}(?:\.\d+)?)(\s?(cm|厘米|mm|毫米|inch|in|英寸|\"))?", s)
            if m:
                val = float(m.group(1))
                unit = m.group(3)
                if unit and unit.lower() in ["inch","in","英寸","\""]:
                    val = round(val * 2.54, 1)
                elif unit and unit.lower() in ["mm","毫米"]:
                    val = round(val / 10.0, 1)
                nums.append(int(round(val)))
        # heuristic: first->height, second->bust, third->waist, fourth->hip
        if nums:
            if "height" not in out and len(nums) >= 1:
                out["height"] = nums[0]
            if "bust" not in out and len(nums) >= 2:
                out["bust"] = nums[1]
            if "waist" not in out and len(nums) >= 3:
                out["waist"] = nums[2]
            if "hip" not in out and len(nums) >= 4:
                out["hip"] = nums[3]
    return out

def _extract_style_keywords(text: str):
    found = []
    for kw in STYLE_KEYWORDS:
        if kw in text:
            found.append(kw)
    return found

def _extract_fabric(text: str):
    # 优先匹配长词，避免“牛仔布”被“牛仔”提前吞掉
    m = re.search(r"(真丝|丝绸|牛仔布|牛仔|羊毛|羊绒|丝绒|皮革|涤纶|锦纶|蕾丝|棉|麻|丝|毛|皮)", text, flags=re.I)
    if m:
        return m.group(0)
    return None

def parse_with_deepseek(user_text: str, inspiration_image: Any = None) -> Dict[str, Any]:
    try:
        text = (user_text or "").strip()
        low = text.lower()
        result: Dict[str, Any] = {
            "garment": None,
            "fit": "Regular",
            "length": "Regular",
            "color": None,
            "material": None,
            "height": None,
            "bust": None,
            "waist": None,
            "hip": None,
            "shoulder": None,
            "torso_length": None,
            "neck_type": None,
            "sleeve_length": None,
            "notes": text,
            "style_keywords": []
        }

        if not text and inspiration_image is None:
            return result

        # hex color direct
        hex_value = _extract_hex(text)
        if hex_value:
            result["color"] = hex_value
        else:
            # color words
            word_color = _color_from_words(text)
            if word_color:
                result["color"] = word_color

        # try image dominant color (override if present)
        if inspiration_image is not None:
            try:
                dom_color = _dominant_color_from_image(inspiration_image)
                if dom_color:
                    result["color"] = dom_color
                w, h = inspiration_image.size
                # naive: tall image probably dress / long garment
                if h / max(1, w) > 1.4 and not result.get("garment"):
                    result["garment"] = "连衣裙"
                elif not result.get("garment"):
                    result["garment"] = "衬衫"
            except Exception:
                pass

        # garment from text
        g = _suggest_garment_from_text(text)
        if g:
            result["garment"] = g

        # fit
        if any(w in low for w in ["修身", "slim", "紧身"]):
            result["fit"] = "Slim"
        elif any(w in low for w in ["宽松", "oversize", "relaxed"]):
            result["fit"] = "Relaxed"

        # fabric
        mat = _extract_fabric(text)
        if mat:
            result["material"] = mat

        # style keywords
        result["style_keywords"] = _extract_style_keywords(text)

        # measurements parsing
        measures = _parse_measurements_with_units(text)
        result.update(measures)

        # sleeve/neck inference
        if "v领" in low or "v 领" in low or "v-neck" in low:
            result["neck_type"] = "V领"
        if any(w in text for w in ["无袖", "strap", "吊带"]):
            result["sleeve_length"] = "无袖"
        elif any(w in text for w in ["短袖", "short sleeve"]):
            result["sleeve_length"] = "短袖"
        elif any(w in text for w in ["七分袖"]):
            result["sleeve_length"] = "七分袖"
        elif any(w in text for w in ["长袖", "long sleeve"]):
            result["sleeve_length"] = "长袖"

        # final safe defaults
        for k in ["height", "bust", "waist", "hip", "shoulder", "torso_length"]:
            if result.get(k) is None:
                # leave None to allow optimizer to fill defaults
                result[k] = None

        return result
    except Exception:
        return {
            "garment": None, "fit":"Regular", "length":"Regular",
            "color":None,"material":None,"height":None,"bust":None,"waist":None,"hip":None,"notes": user_text or ""
        }
