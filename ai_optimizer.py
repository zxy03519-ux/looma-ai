# ai_optimizer.py
"""
参数优化器（增强版）
- 对职业模式新增参数做默认/容错补齐
- 智能模式会尝试根据款式/面料/尺寸给出合理默认（包括领型、袖长度、肩宽建议等）
"""

def material_to_seam(material: str):
    m = (material or "").lower()
    if "丝" in m or "丝绸" in m:
        return 1.0
    if "牛仔" in m or "denim" in m:
        return 1.8
    if "棉" in m:
        return 1.5
    if "羊毛" in m or "毛" in m:
        return 1.6
    return 1.5

def suggest_shoulder(bust: float):
    # 一个简单的启发式：肩宽约为胸围的 0.22~0.26（粗略）
    if bust <= 0:
        return 38.0
    return round(max(34.0, min(48.0, bust * 0.24)), 1)

def suggest_torso_length(height: float):
    # 建议上身长度 = 身高 * 0.24 (粗略)
    if height <= 0:
        return 40.0
    return round(max(28.0, min(50.0, height * 0.24)), 1)

def optimize(design_params: dict, mode: str = "智能模式"):
    """
    输入：design_params（来自解析器或职业表单）
    mode: "智能模式" | "职业模式"
    返回：补全/优化后的参数字典
    """
    params = dict(design_params)  # shallow copy

    # 确保存在基本数值字段
    for k in ["height","bust","waist","hip","shoulder","torso_length"]:
        try:
            if k in params:
                params[k] = float(params.get(k) or 0)
        except:
            params[k] = 0.0

    # 设置推荐肩宽/上半身长度（若缺失或为 0）
    if not params.get("shoulder"):
        params["shoulder"] = suggest_shoulder(params.get("bust", 88))
    if not params.get("torso_length"):
        params["torso_length"] = suggest_torso_length(params.get("height", 165))

    # 材质驱动缝份
    mat = params.get("material", "")
    params["seam"] = float(params.get("seam", material_to_seam(mat)))

    # 智能模式：自动建议职业参数（若缺失）
    if "智能" in mode:
        # fit driven ease
        fit = params.get("fit", "Regular")
        if "slim" in str(fit).lower() or "修身" in str(fit):
            params["ease"] = float(params.get("ease", 2.0))
        elif "relax" in str(fit).lower() or "宽松" in str(fit):
            params["ease"] = float(params.get("ease", 8.0))
        else:
            params["ease"] = float(params.get("ease", 4.0))
        # sleeve defaults if not provided
        params.setdefault("sleeve_length", params.get("sleeve_length", "长袖"))
        params.setdefault("sleeve_width", float(params.get("sleeve_width", 24.0)))
        params.setdefault("sleeve_cap_height", float(params.get("sleeve_cap_height", 10.0)))
        params.setdefault("neck_type", params.get("neck_type", "圆领"))
        params.setdefault("hem_depth", params.get("hem_depth", 12.0))
    else:
        # 职业模式：尊重输入，但做基本补齐
        params.setdefault("ease", float(params.get("ease", 4.0)))
        params.setdefault("sleeve_length", params.get("sleeve_length", "长袖"))
        params.setdefault("sleeve_width", float(params.get("sleeve_width", 24.0)))
        params.setdefault("sleeve_cap_height", float(params.get("sleeve_cap_height", 10.0)))
        params.setdefault("neck_type", params.get("neck_type", "圆领"))
        params.setdefault("hem_depth", float(params.get("hem_depth", 12.0)))

    # 渲染/预览相关（2D 可用）
    params.setdefault("render", {
        "roughness": 0.6,
        "specular": 0.1
    })

    params["status"] = "optimized"
    return params