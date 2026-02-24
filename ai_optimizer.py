# ai_optimizer.py
def material_to_seam(material: str):
    m = str(material or "").lower()
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
    params = dict(design_params or {})

    def _safe_float(value, default):
        try:
            if value is None or value == "":
                return float(default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    for k, d in [("height", 165), ("bust", 88), ("waist", 68), ("hip", 94), ("shoulder", 0), ("torso_length", 0)]:
        params[k] = _safe_float(params.get(k), d)

    if params.get("shoulder", 0) <= 0:
        params["shoulder"] = suggest_shoulder(params.get("bust", 88))
    if params.get("torso_length", 0) <= 0:
        params["torso_length"] = suggest_torso_length(params.get("height", 165))

    mat = params.get("material", "")
    params["seam"] = _safe_float(params.get("seam"), material_to_seam(mat))
    if "智能" in mode:
        fit = params.get("fit", "Regular")
        if "slim" in str(fit).lower() or "修身" in str(fit):
            params["ease"] = _safe_float(params.get("ease"), 2.0)
        elif "relax" in str(fit).lower() or "宽松" in str(fit):
            params["ease"] = _safe_float(params.get("ease"), 8.0)
        else:
            params["ease"] = _safe_float(params.get("ease"), 4.0)
    else:
        params["ease"] = _safe_float(params.get("ease"), 4.0)

    params["sleeve_length"] = params.get("sleeve_length") or "长袖"
    params["sleeve_width"] = _safe_float(params.get("sleeve_width"), 24.0)
    params["sleeve_cap_height"] = _safe_float(params.get("sleeve_cap_height"), 10.0)
    params["neck_type"] = params.get("neck_type") or "圆领"
    params["hem_depth"] = _safe_float(params.get("hem_depth"), 12.0)
    params.setdefault("render", {"roughness": 0.6, "specular": 0.1})
    params["status"] = "optimized"
    return params
