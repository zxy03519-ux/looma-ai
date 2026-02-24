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
# 页面基础配置
# =============================
st.set_page_config(
    page_title="Looma AI - 张小鱼原创",
    layout="wide"
)

apply_theme()
show_brand_header()
show_watermark()

st.markdown("---")


# =============================
# 手机模式开关
# =============================
if "mobile_mode" not in st.session_state:
    st.session_state.mobile_mode = False

st.session_state.mobile_mode = st.toggle(
    "📱 手机优化模式",
    value=st.session_state.mobile_mode
)

# =============================
# 模式逻辑（稳定版）
# =============================
if st.session_state.mobile_mode:
    current_mode = "智能模式（新手）"
    st.info("📱 手机模式已启用智能模式")
else:
    current_mode = st.radio(
        "选择模式",
        ["智能模式（新手）", "职业模式（设计师/打版师）"],
        horizontal=True
    )

st.markdown("---")


# =============================
# 布局控制
# =============================
if st.session_state.mobile_mode:
    left = st.container()
    right = st.container()
else:
    left, right = st.columns([1, 1.4])


# =============================
# 左侧：基础输入
# =============================
with left:

    st.subheader("📥 灵感照片（可选）")
    insp_file = st.file_uploader(
        "上传灵感图片",
        type=["jpg", "jpeg", "png"]
    )

    insp_image = None
    if insp_file:
        try:
            insp_image = Image.open(insp_file)
            st.image(insp_image, use_container_width=True)
        except:
            st.error("图片读取失败")

    st.divider()

    st.subheader("🎨 基本信息")

    garment = st.selectbox("服装品类", GARMENT_OPTIONS)
    color_picker = st.color_picker("颜色", "#FF4B4B")
    material_input = st.text_input("面料", "纯棉")

    notes_input = st.text_area(
        "设计描述 / 想法表达",
        height=120,
        placeholder="例如：酒红色真丝连衣裙，修身，飘逸下摆..."
    )

    st.markdown("### 📏 客户尺寸")

    colA, colB = st.columns(2)
    with colA:
        height = st.number_input("身高", 100, 220, 165)
        bust = st.number_input("胸围", 50, 150, 88)
        shoulder = st.number_input("肩宽", 30.0, 60.0, 38.0, step=0.5)
    with colB:
        waist = st.number_input("腰围", 40, 140, 68)
        hip = st.number_input("臀围", 50, 160, 94)
        torso_length = st.number_input("上半身长", 25.0, 60.0, 40.0, step=0.5)


# =============================
# 右侧：职业参数
# =============================
with right:

    st.subheader("🔧 职业打版参数")

    with st.expander("展开职业高级参数", expanded=False):

        neck_type = st.selectbox(
            "领型",
            ["圆领", "V领", "立领", "方领", "无领"]
        )

        sleeve_length = st.selectbox(
            "袖长",
            ["无袖", "短袖", "七分袖", "长袖"]
        )

        sleeve_width = st.number_input(
            "袖肥度",
            10.0, 60.0, 24.0, step=0.5
        )

        sleeve_cap_height = st.number_input(
            "袖山高度",
            4.0, 18.0, 10.0, step=0.1
        )

        seam = st.number_input(
            "缝份",
            0.0, 4.0, 1.5, step=0.1
        )

        ease = st.number_input(
            "松量",
            0.0, 15.0, 4.0, step=0.1
        )

        hem_depth = st.number_input(
            "下摆深度",
            5.0, 60.0, 12.0, step=0.5
        )


# =============================
# 生成按钮
# =============================
st.markdown("###")
generate_clicked = st.button(
    "🚀 立即生成设计",
    use_container_width=True
)


# =============================
# 生成逻辑
# =============================
if generate_clicked:

    user_text = notes_input.strip()
    if not user_text:
        user_text = f"{color_picker} {material_input} {garment}"

    # -------- 智能模式 --------
    if current_mode.startswith("智能"):

        parsed = parse_with_deepseek(
            user_text,
            inspiration_image=insp_image
        )

        parsed.update({
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
            "notes": notes_input
        })

        design_input = parsed

    # -------- 职业模式 --------
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
            "notes": notes_input
        }

    # 优化参数
    try:
        optimized = optimize(design_input, current_mode)
    except Exception as e:
        st.error(f"优化失败: {e}")
        optimized = design_input

    # 生成图纸
    try:
        res = generate_pattern(optimized)
    except Exception as e:
        st.exception(f"生成失败: {e}")
        res = None

    if res:

        st.success("✅ 生成完成")

        components.html(
            """
            <script>
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
            </script>
            """,
            height=0
        )

        if os.path.exists(res.get("preview", "")):
            st.image(
                res["preview"],
                caption="2D 成品示意图 · 张小鱼原创",
                use_container_width=True
            )

        # 打包下载
        preview_path = res.get("preview")
        dxf_path = res.get("dxf")
        json_path = res.get("json")

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zf:
            if preview_path and os.path.exists(preview_path):
                zf.write(preview_path, os.path.basename(preview_path))
            if dxf_path and os.path.exists(dxf_path):
                zf.write(dxf_path, os.path.basename(dxf_path))
            if json_path and os.path.exists(json_path):
                zf.write(json_path, os.path.basename(json_path))

        zip_buffer.seek(0)

        st.download_button(
            "⬇️ 下载完整文件包",
            zip_buffer.read(),
            file_name="looma_design_package.zip",
            use_container_width=True
        )

st.markdown("---")
st.markdown("© 2026 张小鱼原创 · Looma AI")
