# app.py
import streamlit as st
import os
import io
import zipfile
from PIL import Image
import streamlit.components.v1 as components
from datetime import datetime

from ui_theme import apply_theme, show_brand_header, show_watermark
from deepseek_engine import parse_with_deepseek, GARMENT_OPTIONS
from pattern_engine import generate_pattern
from ai_optimizer import optimize

# ------------------------
# 页面配置与主题
# ------------------------
st.set_page_config(page_title="Looma AI - 张小鱼原创", layout="wide")
apply_theme()
show_brand_header()
show_watermark()
st.markdown("---")

# ------------------------
# 初始化 session_state（默认值）
# ------------------------
_defaults = {
    "mobile_mode": False,
    "parsed_cache": None,           # 缓存 AI 解析结果（用于安全填充）
    "ai_locked_fields": [],         # 被 AI 填写且锁定的字段（list）
    "ai_suggestions": [],

    # 基本字段默认（会成为 widget 的初始值）
    "notes_input": "",
    "garment": GARMENT_OPTIONS[0],
    "color_picker": "#FF4B4B",
    "material_input": "纯棉",
    "height": 165,
    "bust": 88,
    "waist": 68,
    "hip": 94,
    "shoulder": 38.0,
    "torso_length": 40.0,
    # 职业字段默认
    "neck_type": "圆领",
    "sleeve_length": "长袖",
    "sleeve_width": 24.0,
    "sleeve_cap_height": 10.0,
    "seam": 1.5,
    "ease": 4.0,
    "hem_depth": 12.0,
    # mode persistence
    "mode_select": "智能模式（新手）"
}

for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ------------------------
# 如果 parsed_cache 存在，先应用到 session_state（在创建 widget 之前）
# ------------------------
if st.session_state.get("parsed_cache"):
    parsed = st.session_state["parsed_cache"]
    mapping = {
        "garment": "garment",
        "color": "color_picker",
        "material": "material_input",
        "height": "height",
        "bust": "bust",
        "waist": "waist",
        "hip": "hip",
        "shoulder": "shoulder",
        "torso_length": "torso_length",
        "neck_type": "neck_type",
        "sleeve_length": "sleeve_length",
        "sleeve_width": "sleeve_width",
        "sleeve_cap_height": "sleeve_cap_height",
        "seam": "seam",
        "ease": "ease",
        "hem_depth": "hem_depth"
    }
    for pkey, skey in mapping.items():
        if parsed.get(pkey) is not None:
            try:
                st.session_state[skey] = parsed[pkey]
            except Exception:
                pass
            # 记录锁定（以 list 存储）
            if skey not in st.session_state["ai_locked_fields"]:
                st.session_state["ai_locked_fields"].append(skey)
    # 清空缓存
    st.session_state["parsed_cache"] = None

# ------------------------
# 顶部控件：手机开关与模式（手机强制智能）
# ------------------------
col_top1, col_top2 = st.columns([1, 4])
with col_top1:
    st.session_state["mobile_mode"] = st.checkbox("📱 手机优化模式", value=st.session_state["mobile_mode"])
with col_top2:
    if st.session_state["mobile_mode"]:
        st.info("📱 手机模式已启用（优先智能模式、移动友好布局）")

# 模式选择：手机强制智能，桌面可选
if st.session_state["mobile_mode"]:
    current_mode = "智能模式（新手）"
    st.session_state["mode_select"] = current_mode
else:
    current_mode = st.radio("选择模式", ["智能模式（新手）", "职业模式（设计师/打版师）"],
                           index=0 if st.session_state.get("mode_select", "").startswith("智能") else 1,
                           key="mode_select", horizontal=True)

st.markdown("---")

# ------------------------
# 辅助函数
# ------------------------
def _get_uploaded_image_from_state():
    """从 session_state['uploader'] 中读取 PIL.Image（如果存在）"""
    f = st.session_state.get("uploader")
    if not f:
        return None
    try:
        # f 是 UploadedFile-like
        f.seek(0)
        img = Image.open(f)
        return img
    except Exception:
        return None

def _apply_parsed_to_cache_and_rerun(parsed):
    """把解析结果放入 parsed_cache 并触发 rerun（st.rerun）"""
    st.session_state["parsed_cache"] = parsed
    # 使用新版 API
    st.rerun()

def generate_suggestions(data):
    """生成简单的 AI 优化建议（可扩展）"""
    warns = []
    if data.get("ease", 0) < 1:
        warns.append("松量 (ease) 过小，可能导致活动受限，建议 >= 2 cm。")
    if data.get("bust", 0) < 70:
        warns.append("胸围较小，请确认是否成人尺码或单位。")
    if data.get("shoulder", 0) > 50:
        warns.append("肩宽数值较大，请确认测量方式或单位。")
    if abs(data.get("bust",0) - data.get("waist",0)) < 5:
        warns.append("胸腰差过小，版型可能不明显，可考虑增加腰身或改版型。")
    return warns

# ------------------------
# 布局：移动端单列 / 桌面两列
# ------------------------
if st.session_state["mobile_mode"]:
    col_main = st.container()
    col_side = st.container()
else:
    col_main, col_side = st.columns([1, 1.4])

# ------------------------
# 主列：上传、文本、基础字段（使用 session_state keys）
# ------------------------
with col_main:
    st.subheader("📥 灵感图片（可选）")
    # 使用 key 'uploader'，文件会存放在 session_state['uploader']
    st.file_uploader("上传灵感图片（jpg/png）", type=["jpg", "jpeg", "png"], key="uploader")
    uploaded_img = _get_uploaded_image_from_state()
    if uploaded_img:
        st.image(uploaded_img, use_column_width=True, caption="灵感图预览")

    st.markdown("### 🎨 口语化描述（实时解析）")

    # on_change 回调：当文本框内容改变并失去焦点时触发解析
    def _on_notes_change():
        txt = st.session_state.get("notes_input", "").strip()
        if len(txt) < 3:
            return
        insp = _get_uploaded_image_from_state()
        try:
            parsed = parse_with_deepseek(txt, inspiration_image=insp)
        except Exception:
            parsed = parse_with_deepseek(txt)
        _apply_parsed_to_cache_and_rerun(parsed)

    st.text_area("请用口语描述你的想法（示例：酒红色真丝连衣裙，修身，胸围86，长袖）",
                 key="notes_input", on_change=_on_notes_change, height=140)

    st.markdown("")
    if st.button("✨ 解析并填充表单（手动）"):
        txt = st.session_state.get("notes_input", "").strip()
        if not txt and not _get_uploaded_image_from_state():
            st.error("请先输入描述或上传灵感图片以供解析。")
        else:
            insp = _get_uploaded_image_from_state()
            try:
                parsed = parse_with_deepseek(txt, inspiration_image=insp)
            except Exception:
                parsed = parse_with_deepseek(txt)
            _apply_parsed_to_cache_and_rerun(parsed)

    st.markdown("---")
    if st.button("🔓 解锁所有由 AI 填写的字段（允许手动编辑）"):
        st.session_state["ai_locked_fields"] = []
        st.success("已解锁所有字段，可手动编辑。")

    st.markdown("### 基本信息（被 AI 填写的字段将被锁定）")

    # 下面所有 widget 都要使用与 parsed mapping 对应的 key 名（便于 parsed_cache 应用）
    garment = st.selectbox("服装品类", GARMENT_OPTIONS, key="garment",
                           disabled=("garment" in st.session_state["ai_locked_fields"]))
    color_picker = st.color_picker("颜色", key="color_picker",
                                   disabled=("color_picker" in st.session_state["ai_locked_fields"]))
    material_input = st.text_input("面料", key="material_input",
                                   disabled=("material_input" in st.session_state["ai_locked_fields"]))

    st.markdown("#### 客户尺寸（可选）")
    height = st.number_input("身高 (cm)", 100, 220, key="height",
                             disabled=("height" in st.session_state["ai_locked_fields"]))
    bust = st.number_input("胸围 (cm)", 50, 150, key="bust",
                          disabled=("bust" in st.session_state["ai_locked_fields"]))
    waist = st.number_input("腰围 (cm)", 40, 140, key="waist",
                           disabled=("waist" in st.session_state["ai_locked_fields"]))
    hip = st.number_input("臀围 (cm)", 50, 160, key="hip",
                         disabled=("hip" in st.session_state["ai_locked_fields"]))
    shoulder = st.number_input("肩宽 (cm)", 20.0, 60.0, key="shoulder",
                              disabled=("shoulder" in st.session_state["ai_locked_fields"]))
    torso_length = st.number_input("上半身长度 (cm)", 20.0, 60.0, key="torso_length",
                                  disabled=("torso_length" in st.session_state["ai_locked_fields"]))

# ------------------------
# 侧栏 / 右列：职业参数 + 生成
# ------------------------
with col_side:
    st.subheader("🔧 职业参数（高级）")
    expanded = False if st.session_state["mobile_mode"] else True
    with st.expander("展开 / 编辑 职业参数", expanded=expanded):
        neck_type = st.selectbox("领型", ["圆领", "V领", "立领", "方领", "无领"], key="neck_type")
        sleeve_length = st.selectbox("袖长", ["无袖", "短袖", "七分袖", "长袖"], key="sleeve_length")
        sleeve_width = st.number_input("袖肥度 (cm)", 10.0, 60.0, key="sleeve_width")
        sleeve_cap_height = st.number_input("袖山高度 (cm)", 4.0, 18.0, key="sleeve_cap_height")
        seam = st.number_input("缝份 Seam (cm)", 0.0, 4.0, key="seam")
        ease = st.number_input("整体松量 Ease (cm)", 0.0, 15.0, key="ease")
        hem_depth = st.number_input("下摆深度 / 裙摆高度 (cm)", 0.0, 80.0, key="hem_depth")

    st.markdown("---")
    # 生成按钮（桌面/手机都显示）
    if st.button("🚀 生成设计与打版（2D）", use_container_width=True):
        design_input = {
            "garment": st.session_state.get("garment"),
            "color": st.session_state.get("color_picker"),
            "material": st.session_state.get("material_input"),
            "height": st.session_state.get("height"),
            "bust": st.session_state.get("bust"),
            "waist": st.session_state.get("waist"),
            "hip": st.session_state.get("hip"),
            "shoulder": st.session_state.get("shoulder"),
            "torso_length": st.session_state.get("torso_length"),
            "neck_type": st.session_state.get("neck_type"),
            "sleeve_length": st.session_state.get("sleeve_length"),
            "sleeve_width": st.session_state.get("sleeve_width"),
            "sleeve_cap_height": st.session_state.get("sleeve_cap_height"),
            "seam": st.session_state.get("seam"),
            "ease": st.session_state.get("ease"),
            "hem_depth": st.session_state.get("hem_depth"),
            "notes": st.session_state.get("notes_input")
        }

        mode_for_opt = "智能模式" if st.session_state["mobile_mode"] else st.session_state.get("mode_select", "智能模式（新手）")

        try:
            optimized = optimize(design_input, mode_for_opt)
        except Exception as e:
            st.error(f"参数优化失败：{e}")
            optimized = design_input

        # suggestions
        st.session_state["ai_suggestions"] = generate_suggestions(optimized)

        # generate pattern
        try:
            res = generate_pattern(optimized)
        except Exception as e:
            st.exception(f"生成图纸失败：{e}")
            res = None

        if res:
            st.success("✅ 生成成功，向下查看预览与下载")
            # 自动滚动到页面底部
            components.html("<script>window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });</script>", height=0)

            preview_path = res.get("preview")
            if preview_path and os.path.exists(preview_path):
                st.image(preview_path, use_column_width=True, caption="2D 成品预览 · 张小鱼原创")

            # 打包 ZIP
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zf:
                if preview_path and os.path.exists(preview_path):
                    zf.write(preview_path, os.path.basename(preview_path))
                if res.get("dxf") and os.path.exists(res["dxf"]):
                    zf.write(res["dxf"], os.path.basename(res["dxf"]))
                if res.get("json") and os.path.exists(res["json"]):
                    zf.write(res["json"], os.path.basename(res["json"]))
            zip_buf.seek(0)
            st.download_button("⬇️ 下载完整文件包 (PNG + DXF + JSON)", zip_buf.read(),
                               file_name=f"{design_input.get('garment','design')}_{datetime.now().strftime('%Y%m%d')}.zip",
                               use_container_width=True)

            # show suggestions
            if st.session_state.get("ai_suggestions"):
                st.warning("⚠ AI 优化建议（请核对）")
                for s in st.session_state["ai_suggestions"]:
                    st.write("•", s)

st.markdown("---")
st.markdown("© 张小鱼原创 · Looma AI 2026")
