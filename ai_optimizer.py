# ai_optimizer.py
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
    if bust <= 0:
        return 38.0
    return round(max(34.0, min(48.0, bust * 0.24)), 1)

def suggest_torso_length(height: float):
    if height <= 0:
        return 40.0
    return round(max(28.0, min(50.0, height * 0.24)), 1)

def optimize(design_params: dict, mode: str = "智能模式"):
    params = dict(design_params)
    for k in ["height","bust","waist","hip","shoulder","torso_length"]:
        try:
            if k in params and params[k] is not None:
                params[k] = float(params.get(k) or 0)
        except:
            params[k] = 0.0
    if not params.get("shoulder"):
        params["shoulder"] = suggest_shoulder(params.get("bust", 88))
    if not params.get("torso_length"):
        params["torso_length"] = suggest_torso_length(params.get("height", 165))
    mat = params.get("material", "")
    params["seam"] = float(params.get("seam", material_to_seam(mat)))
    if "智能" in mode:
        fit = params.get("fit", "Regular")
        if "slim" in str(fit).lower() or "修身" in str(fit):
            params["ease"] = float(params.get("ease", 2.0))
        elif "relax" in str(fit).lower() or "宽松" in str(fit):
            params["ease"] = float(params.get("ease", 8.0))
        else:
            params["ease"] = float(params.get("ease", 4.0))
        params.setdefault("sleeve_length", params.get("sleeve_length", "长袖"))
        params.setdefault("sleeve_width", float(params.get("sleeve_width", 24.0)))
        params.setdefault("sleeve_cap_height", float(params.get("sleeve_cap_height", 10.0)))
        params.setdefault("neck_type", params.get("neck_type", "圆领"))
        params.setdefault("hem_depth", params.get("hem_depth", 12.0))
    else:
        params.setdefault("ease", float(params.get("ease", 4.0)))
        params.setdefault("sleeve_length", params.get("sleeve_length", "长袖"))
        params.setdefault("sleeve_width", float(params.get("sleeve_width", 24.0)))
        params.setdefault("sleeve_cap_height", float(params.get("sleeve_cap_height", 10.0)))
        params.setdefault("neck_type", params.get("neck_type", "圆领"))
        params.setdefault("hem_depth", float(params.get("hem_depth", 12.0)))
    params.setdefault("render", {"roughness": 0.6, "specular": 0.1})
    params["status"] = "optimized"
    return params
