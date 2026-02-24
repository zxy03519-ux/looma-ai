# app.py
import streamlit as st
import os
import io
import zipfile
from PIL import Image
import streamlit.components.v1 as components

from ui_theme import apply_theme, show_brand_header, show_watermark
from deepseek_engine import parse_with_deepseek, GARMENT_OPTIONS
from pattern_engine import generate_pattern
from ai_optimizer import optimize

# =============================
# 页面配置
# =============================
st.set_page_config(page_title="Looma AI - 张小鱼原创", layout="wide")

apply_theme()
show_brand_header()
show_watermark()

st.markdown("---")

# =============================
# 初始化 session_state
# =============================
defaults = {
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
    "neck_type": "圆领",
    "sleeve_length": "长袖",
    "sleeve_width": 24.0,
    "sleeve_cap_height": 10.0,
    "seam": 1.5,
    "ease": 4.0,
    "hem_depth": 12.0,
    "ai_locked_fields": set(),
    "ai_suggestions": []
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================
# 实时解析函数
# =============================
def auto_parse():
    text = st.session_state.notes_input.strip()
    if len(text) < 5:
        return

    parsed = parse_with_deepseek(text)

    mapping = {
        "garment": "garment",
        "color": "color_picker",
        "material": "material_input",
        "height": "height",
        "bust": "bust",
        "waist": "waist",
        "hip": "hip",
        "shoulder": "shoulder",
        "torso_length": "torso_length"
    }

    for parsed_key, widget_key in mapping.items():
        if parsed.get(parsed_key) is not None:
            st.session_state[widget_key] = parsed[parsed_key]
            st.session_state.ai_locked_fields.add(widget_key)

# =============================
# 左侧输入区
# =============================
left, right = st.columns([1, 1.4])

with left:

    st.subheader("📝 设计描述（自动解析）")

    st.text_area(
        "输入你的设计想法",
        key="notes_input",
        height=120,
        on_change=auto_parse
    )

    if st.button("🔓 解锁所有参数"):
        st.session_state.ai_locked_fields = set()

    st.markdown("---")

    garment = st.selectbox(
        "服装品类",
        GARMENT_OPTIONS,
        key="garment",
        disabled="garment" in st.session_state.ai_locked_fields
    )

    st.color_picker(
        "颜色",
        key="color_picker",
        disabled="color_picker" in st.session_state.ai_locked_fields
    )

    st.text_input(
        "面料",
        key="material_input",
        disabled="material_input" in st.session_state.ai_locked_fields
    )

    st.markdown("### 📏 尺寸参数")

    st.number_input("身高", 100, 220, key="height",
                    disabled="height" in st.session_state.ai_locked_fields)

    st.number_input("胸围", 50, 150, key="bust",
                    disabled="bust" in st.session_state.ai_locked_fields)

    st.number_input("腰围", 40, 140, key="waist",
                    disabled="waist" in st.session_state.ai_locked_fields)

    st.number_input("臀围", 50, 160, key="hip",
                    disabled="hip" in st.session_state.ai_locked_fields)

# =============================
# 职业参数
# =============================
with right:

    st.subheader("🔧 职业参数")

    st.selectbox("领型",
                 ["圆领", "V领", "立领", "方领", "无领"],
                 key="neck_type")

    st.selectbox("袖长",
                 ["无袖", "短袖", "七分袖", "长袖"],
                 key="sleeve_length")

    st.number_input("袖肥度", 10.0, 60.0,
                    key="sleeve_width")

    st.number_input("松量", 0.0, 15.0,
                    key="ease")

# =============================
# AI 优化提示系统
# =============================
def generate_suggestions(data):

    warnings = []

    if data["ease"] < 1:
        warnings.append("松量过小，可能影响舒适度")

    if data["bust"] - data["waist"] < 5:
        warnings.append("胸腰差过小，版型可能不明显")

    if data["shoulder"] > 50:
        warnings.append("肩宽数值较大，请确认测量方式")

    return warnings

# =============================
# 生成按钮
# =============================
st.markdown("---")
generate_clicked = st.button("🚀 生成设计", use_container_width=True)

if generate_clicked:

    design_input = {k: st.session_state[k] for k in [
        "garment","color_picker","material_input",
        "height","bust","waist","hip",
        "shoulder","torso_length",
        "neck_type","sleeve_length",
        "sleeve_width","sleeve_cap_height",
        "seam","ease","hem_depth"
    ]}

    optimized = optimize(design_input, "智能模式")

    st.session_state.ai_suggestions = generate_suggestions(optimized)

    res = generate_pattern(optimized)

    if res and os.path.exists(res["preview"]):
        st.image(res["preview"], use_container_width=True)

    if st.session_state.ai_suggestions:
        st.warning("⚠ AI 优化建议")
        for w in st.session_state.ai_suggestions:
            st.write("•", w)

st.markdown("---")
st.markdown("© 张小鱼原创 · Looma AI")
