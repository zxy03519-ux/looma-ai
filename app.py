# app.py
import streamlit as st
import os
import io
import zipfile
from PIL import Image
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from ui_theme import apply_theme, show_brand_header, show_watermark
from deepseek_engine import parse_with_deepseek, GARMENT_OPTIONS
from pattern_engine import generate_pattern
from ai_optimizer import optimize

st.set_page_config(
    page_title="Looma AI - 张小鱼原创（工业增强版）",
    layout="wide"
)

# =====================================================
# 主题系统
# =====================================================

if "ui" not in st.session_state:
    st.session_state.ui = {
        "primary": "#111111",
        "secondary": "#FF6B6B",
        "bg": "#FFFFFF"
    }

col_theme = st.columns([1, 2, 1])
with col_theme[0]:
    primary = st.color_picker("主题主色", st.session_state.ui["primary"])
with col_theme[2]:
    secondary = st.color_picker("主题辅色", st.session_state.ui["secondary"])

st.session_state.ui["primary"] = primary
st.session_state.ui["secondary"] = secondary

apply_theme(primary_color=primary,
            secondary_color=secondary,
            bg_color=st.session_state.ui["bg"])

show_brand_header()
show_watermark()

st.markdown("---")

# =====================================================
# 模式选择
# =====================================================

mode = st.radio(
    "选择模式",
    ["智能模式（新手）", "职业模式（设计师/打版师）"],
    horizontal=True
)

# =====================================================
# 主布局
# =====================================================

left, right = st.columns([1, 1.5])

# =====================================================
# 左侧输入区
# =====================================================

with left:

    st.subheader("📥 灵感照片（AI识图辅助）")

    insp_file = st.file_uploader(
        "上传灵感图片（jpg/png）",
        type=["jpg", "jpeg", "png"]
    )

    insp_image = None
    if insp_file:
        insp_image = Image.open(insp_file)
        st.image(insp_image, caption="灵感图预览", use_container_width=True)

    st.divider()

    st.subheader("🎨 设计基础信息")

    garment = st.selectbox("服装品类", GARMENT_OPTIONS)
    color_picker = st.color_picker("颜色", "#FF6B6B")
    material_input = st.text_input("面料", "纯棉")

    notes_input = st.text_area(
        "设计描述",
        height=120,
        placeholder="例如：酒红色真丝长裙，修身，轻薄飘逸，带荷叶边。"
    )

    st.divider()

    st.subheader("📏 客户尺寸")

    height = st.number_input("身高", 100, 220, 165)
    bust = st.number_input("胸围", 50, 150, 88)
    waist = st.number_input("腰围", 40, 140, 68)
    hip = st.number_input("臀围", 50, 160, 94)
    shoulder = st.number_input("肩宽", 30.0, 60.0, 38.0)
    torso_length = st.number_input("上半身长度", 25.0, 60.0, 40.0)

# =====================================================
# 右侧职业增强参数
# =====================================================

with right:

    if "职业" in mode:

        st.subheader("🧵 版型结构参数")

        neck_type = st.selectbox(
            "领型",
            ["圆领", "V 领", "立领", "方领", "无领"]
        )

        sleeve_length = st.selectbox(
            "袖长",
            ["无袖", "短袖", "七分袖", "长袖"]
        )

        sleeve_width = st.number_input("袖肥度", 10.0, 60.0, 24.0)
        sleeve_cap_height = st.number_input("袖山高度", 4.0, 18.0, 10.0)

        st.divider()

        st.subheader("📐 工艺控制")

        seam = st.number_input("缝份", 0.0, 4.0, 1.5)
        ease = st.number_input("松量", 0.0, 15.0, 4.0)
        hem_depth = st.number_input("下摆深度", 5.0, 60.0, 12.0)

        advanced_toggle = st.toggle("开启高级工业结构")

    else:
        st.info("智能模式已隐藏复杂职业参数")

# =====================================================
# 参数合法性检测
# =====================================================

def validate_measurements():
    if waist > bust + 10:
        st.warning("⚠️ 腰围明显大于胸围，请确认是否输入错误")
    if shoulder > bust:
        st.warning("⚠️ 肩宽异常，请检查")

validate_measurements()

st.markdown("---")

# =====================================================
# 生成逻辑
# =====================================================

generate_clicked = st.button("🚀 生成设计与工业打版")

if generate_clicked:

    user_text = notes_input.strip()
    if not user_text:
        user_text = f"{garment} {color_picker} {material_input}"

    if "智能" in mode:

        parsed = parse_with_deepseek(user_text,
                                     inspiration_image=insp_image)

        parsed.update({
            "garment": garment,
            "color": color_picker,
            "material": material_input,
            "height": height,
            "bust": bust,
            "waist": waist,
            "hip": hip,
            "shoulder": shoulder,
            "torso_length": torso_length
        })

        design_input = parsed

    else:

        design_input = {
            "garment": garment,
            "color": color_picker,
            "material": material_input,
            "height": height,
            "bust": bust,
            "waist": waist,
            "hip": hip,
            "shoulder": shoulder,
            "torso_length": torso_length,
            "neck_type": neck_type,
            "sleeve_length": sleeve_length,
            "sleeve_width": sleeve_width,
            "sleeve_cap_height": sleeve_cap_height,
            "seam": seam,
            "ease": ease,
            "hem_depth": hem_depth,
            "advanced": advanced_toggle
        }

    optimized = optimize(design_input, mode)

    result = generate_pattern(optimized)

    if result:

        st.success("✅ 生成成功")

        if os.path.exists(result["preview"]):
            st.image(result["preview"],
                     caption="2D 成品预览 · 张小鱼原创",
                     use_column_width=True)

        # ZIP 导出
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in result.values():
                if os.path.exists(file):
                    zf.write(file, os.path.basename(file))

        zip_buffer.seek(0)

        st.download_button(
            "⬇️ 下载完整工业包",
            zip_buffer.read(),
            file_name=f"{garment}_{datetime.now().strftime('%Y%m%d')}.zip"
        )

st.markdown("---")
st.markdown("© 张小鱼原创 · Looma AI 工业增强系统 2026")