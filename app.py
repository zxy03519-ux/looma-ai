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

# ========== 页面基础配置 ==========
st.set_page_config(page_title="Looma AI - 张小鱼原创", layout="wide", initial_sidebar_state="auto")
apply_theme()  # 使用 ui_theme 的样式
show_brand_header()
show_watermark()

# ========== 手机优化开关（显著） ==========
if "mobile_mode" not in st.session_state:
    st.session_state.mobile_mode = False

# 在顶部显示大开关（便于移动端触达）
col_a, col_b = st.columns([1, 5])
with col_a:
    st.session_state.mobile_mode = st.toggle("📱 手机优化模式", value=st.session_state.mobile_mode)
with col_b:
    if st.session_state.mobile_mode:
        st.info("已启用手机优化模式 — 页面将单列显示并隐藏复杂职业参数。", icon="📱")

st.markdown("---")

# ========== 布局：手机模式为单列（上下堆叠），桌面模式为两列 ==========
if st.session_state.mobile_mode:
    left = st.container()
    right = st.container()
else:
    left, right = st.columns([1, 1.5])

# ========== 左侧（或顶部）基础输入 ==========
with left:
    st.subheader("📥 灵感照片（可选）")
    insp_file = st.file_uploader("上传灵感图片（jpg/png）", type=["jpg", "jpeg", "png"])
    insp_image = None
    if insp_file:
        try:
            insp_image = Image.open(insp_file)
            st.image(insp_image, caption="灵感图预览", use_column_width=True)
        except Exception:
            st.error("无法读取图片，请确认文件格式。")

    st.markdown("### 🎨 基本信息")
    # 合并为一个表单，避免重复渲染控件
    with st.form("design_form", clear_on_submit=False):
        garment = st.selectbox("服装品类", GARMENT_OPTIONS)
        color_picker = st.color_picker("颜色", "#FF6B6B")
        material_input = st.text_input("面料（自由输入）", "纯棉")
        notes_input = st.text_area("设计描述 / 想法（口语化）", height=100, placeholder="例如：酒红色真丝连衣裙，修身，飘逸下摆...")
        st.markdown("#### 📏 客户尺寸（可选）")
        col1, col2 = st.columns(2)
        with col1:
            height = st.number_input("身高 (cm)", 100, 220, 165)
            bust = st.number_input("胸围 (cm)", 50, 150, 88)
            shoulder = st.number_input("肩宽 (cm)", 30.0, 60.0, 38.0, step=0.5)
        with col2:
            waist = st.number_input("腰围 (cm)", 40, 140, 68)
            hip = st.number_input("臀围 (cm)", 50, 160, 94)
            torso_length = st.number_input("上半身长度 (cm)", 25.0, 60.0, 40.0, step=0.5)

        # 手机端隐藏复杂职业参数（但用户可在右侧展开）
        submitted = st.form_submit_button("保存输入（下一步生成或切换到职业参数）")

# ========== 右侧（或下方）职业参数，使用 expander 折叠，移动端默认折叠 ==========
with right:
    st.subheader("🔧 职业参数（专业）")
    collapsed_by_default = True if st.session_state.mobile_mode else False
    with st.expander("展开职业参数（高级）", expanded=not collapsed_by_default):
        neck_type = st.selectbox("领型", ["圆领", "V 领", "立领", "方领", "无领"])
        sleeve_length = st.selectbox("袖长", ["无袖", "短袖", "七分袖", "长袖"])
        sleeve_width = st.number_input("袖肥度 (cm)", 10.0, 60.0, 24.0, step=0.5)
        sleeve_cap_height = st.number_input("袖山高度 (cm)", 4.0, 18.0, 10.0, step=0.1)
        seam = st.number_input("缝份 Seam (cm)", 0.0, 4.0, 1.5, step=0.1)
        ease = st.number_input("整体松量 Ease (cm)", 0.0, 15.0, 4.0, step=0.1)
        hem_depth = st.number_input("下摆深度/裙摆高度 (cm)", 5.0, 60.0, 12.0, step=0.5)

    # 在职业参数下方给出“立即生成”入口，方便桌面直达
    if not st.session_state.mobile_mode:
        if st.button("🚀 生成设计与打版（桌面）", use_container_width=True):
            st.experimental_rerun()

# ========== 生成按钮（单列大按钮，便于手机点按） ==========
st.markdown("###")
generate_clicked = st.button("🚀 立即生成设计（手机/桌面均适用）", use_container_width=True)

# ========== 生成逻辑 ==========
if generate_clicked:
    # 组合用户输入，优先使用表单保存值
    user_text = (notes_input or "").strip()
    if not user_text:
        user_text = f"{color_picker} {material_input} {garment}"

    # 若手机模式强制智能解析（更友好）
    if st.session_state.mobile_mode or "智能" in st.radio(" ", ["智能模式（隐式）","职业模式（隐式）"], index=0, hidden=True):
        parsed = parse_with_deepseek(user_text, inspiration_image=insp_image)
        # 覆盖并补全
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
            "notes": notes_input or ""
        })
        # 如果用户展开职业参数且填写了值，则覆盖
        try:
            # only override if user opened expander and set values
            parsed["neck_type"] = neck_type
            parsed["sleeve_length"] = sleeve_length
            parsed["sleeve_width"] = sleeve_width
            parsed["sleeve_cap_height"] = sleeve_cap_height
            parsed["seam"] = seam
            parsed["ease"] = ease
            parsed["hem_depth"] = hem_depth
        except Exception:
            pass
        design_input = parsed
    else:
        # 职业模式（如果用户想要完全手动）
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
            "notes": notes_input or "",
            "neck_type": neck_type,
            "sleeve_length": sleeve_length,
            "sleeve_width": sleeve_width,
            "sleeve_cap_height": sleeve_cap_height,
            "seam": seam,
            "ease": ease,
            "hem_depth": hem_depth
        }

    # 优化与补齐
    try:
        optimized = optimize(design_input, "智能模式" if st.session_state.mobile_mode else "职业模式")
    except Exception as e:
        st.error(f"优化参数失败：{e}")
        optimized = design_input

    # 生成 pattern（返回 preview/dxf/json 路径）
    try:
        res = generate_pattern(optimized)
    except Exception as e:
        st.exception(f"生成打版失败：{e}")
        res = None

    if res:
        st.success("✅ 生成完成 — 向下滑动查看预览与下载")
        # 自动滚到下方预览
        components.html("<script>window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });</script>", height=0)

        # 显示预览（全宽）
        if os.path.exists(res.get("preview", "")):
            st.image(res["preview"], use_column_width=True, caption="2D 成品预览 · 张小鱼原创")

        # 下载区域精简（手机友好）
        preview_path = res.get("preview")
        dxf_path = res.get("dxf")
        json_path = res.get("json")

        # 生成 ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            if preview_path and os.path.exists(preview_path):
                zf.write(preview_path, os.path.basename(preview_path))
            if dxf_path and os.path.exists(dxf_path):
                zf.write(dxf_path, os.path.basename(dxf_path))
            if json_path and os.path.exists(json_path):
                zf.write(json_path, os.path.basename(json_path))
        zip_buffer.seek(0)

        st.download_button("⬇️ 下载完整文件包 (PNG + DXF + JSON)", zip_buffer.read(), file_name=f"{optimized.get('garment','design')}_package.zip", use_container_width=True)

st.markdown("---")
st.markdown("© 张小鱼原创 · Looma AI 2026")
