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

# ========== 基本配置 ==========
st.set_page_config(page_title="Looma AI - 张小鱼原创", layout="wide")
apply_theme()
show_brand_header()
show_watermark()
st.markdown("---")

# ========== 手机模式开关 ==========
if "mobile_mode" not in st.session_state:
    st.session_state.mobile_mode = False

col_top1, col_top2 = st.columns([1, 5])
with col_top1:
    st.session_state.mobile_mode = st.toggle("📱 手机优化模式", value=st.session_state.mobile_mode)
with col_top2:
    if st.session_state.mobile_mode:
        st.info("已启用手机优化模式（自动使用智能解析并折叠高级职业参数）", icon="📱")

st.markdown("---")

# ========== 模式逻辑（手机强制智能） ==========
if st.session_state.mobile_mode:
    current_mode = "智能模式（新手）"
else:
    current_mode = st.radio("选择模式", ["智能模式（新手）", "职业模式（设计师/打版师）"], horizontal=True)

# ========== 布局 ==========
if st.session_state.mobile_mode:
    left = st.container()
    right = st.container()
else:
    left, right = st.columns([1, 1.4])

# ========== 左侧 / 顶部：基础输入（使用 session_state keys） ==========
with left:
    st.subheader("📥 灵感照片（可选）")
    insp_file = st.file_uploader("上传灵感图片（jpg/png）", type=["jpg", "jpeg", "png"], key="uploader")
    insp_image = None
    if insp_file:
        try:
            insp_image = Image.open(insp_file)
            st.image(insp_image, caption="灵感图预览", use_column_width=True)
        except Exception:
            st.error("无法读取图片，请确认文件格式。")

    st.markdown("### 🎨 基本信息（AI解析可填充）")

    # NOTE: 使用 key 参数，方便被 parse 按钮通过 session_state 修改
    garment = st.selectbox("服装品类", GARMENT_OPTIONS, index=0, key="garment")
    color_picker = st.color_picker("颜色", value="#FF4B4B", key="color_picker")
    material_input = st.text_input("面料（自由输入）", value="纯棉", key="material_input")
    notes_input = st.text_area("设计描述 / 想法（口语化）", height=120, placeholder="例如：酒红色真丝连衣裙，修身，飘逸下摆...", key="notes_input")

    st.markdown("#### 📏 客户尺寸（可选，AI解析会尝试填充）")
    colA, colB = st.columns(2)
    with colA:
        height = st.number_input("身高 (cm)", 100, 220, value=165, key="height")
        bust = st.number_input("胸围 (cm)", 50, 150, value=88, key="bust")
        shoulder = st.number_input("肩宽 (cm)", 30.0, 60.0, value=38.0, step=0.5, key="shoulder")
    with colB:
        waist = st.number_input("腰围 (cm)", 40, 140, value=68, key="waist")
        hip = st.number_input("臀围 (cm)", 50, 160, value=94, key="hip")
        torso_length = st.number_input("上半身长度 (cm)", 25.0, 60.0, value=40.0, step=0.5, key="torso_length")

    st.markdown("")

    # ========== 解析并填充按钮 ==========
    # 当点此按钮时，调用 parse_with_deepseek，并把结果写入 st.session_state（从而更新页面上的控件）
    if st.button("✨ 解析并填充表单（AI）", key="parse_and_fill"):
        user_text = st.session_state.get("notes_input", "").strip()
        # 若用户没写文本但上传了图片，也允许用图片解析
        if not user_text and insp_image is None:
            st.error("请先输入描述或上传灵感图片，AI 才能解析填充表单。")
        else:
            try:
                parsed = parse_with_deepseek(user_text, inspiration_image=insp_image)
                # 将解析结果写回 session_state 对应的 keys（尽量安全取值）
                if parsed.get("garment"):
                    st.session_state["garment"] = parsed.get("garment")
                if parsed.get("color"):
                    # color_picker expects hex; ensure valid fallback
                    st.session_state["color_picker"] = parsed.get("color")
                if parsed.get("material"):
                    st.session_state["material_input"] = parsed.get("material")
                # measurements
                for m in ["height", "bust", "waist", "hip", "shoulder", "torso_length"]:
                    if parsed.get(m) is not None:
                        try:
                            st.session_state[m] = float(parsed.get(m))
                        except:
                            pass
                # professional params (may be absent)
                if parsed.get("neck_type"):
                    st.session_state["neck_type"] = parsed.get("neck_type")
                if parsed.get("sleeve_length"):
                    st.session_state["sleeve_length"] = parsed.get("sleeve_length")
                if parsed.get("sleeve_width"):
                    try:
                        st.session_state["sleeve_width"] = float(parsed.get("sleeve_width"))
                    except:
                        pass
                if parsed.get("sleeve_cap_height"):
                    try:
                        st.session_state["sleeve_cap_height"] = float(parsed.get("sleeve_cap_height"))
                    except:
                        pass
                if parsed.get("seam"):
                    try:
                        st.session_state["seam"] = float(parsed.get("seam"))
                    except:
                        pass
                if parsed.get("ease"):
                    try:
                        st.session_state["ease"] = float(parsed.get("ease"))
                    except:
                        pass
                if parsed.get("hem_depth"):
                    try:
                        st.session_state["hem_depth"] = float(parsed.get("hem_depth"))
                    except:
                        pass

                st.success("AI 已解析并填充表单（如有） — 请在表单核对后点击「立即生成设计」")
                # 重新渲染页面以反映 session_state 的变化
                st.experimental_rerun()
            except Exception as e:
                st.error(f"解析失败：{e}")

# ========== 右侧 / 下方：职业参数（折叠） ==========
with right:
    st.subheader("🔧 职业高级参数（展开可编辑）")
    collapsed_default = True if st.session_state.mobile_mode else False
    with st.expander("展开职业参数（高级）", expanded=not collapsed_default):
        neck_type = st.selectbox("领型", ["圆领", "V领", "立领", "方领", "无领"], key="neck_type")
        sleeve_length = st.selectbox("袖长", ["无袖", "短袖", "七分袖", "长袖"], key="sleeve_length")
        sleeve_width = st.number_input("袖肥度 (cm)", 10.0, 60.0, value=st.session_state.get("sleeve_width", 24.0), key="sleeve_width")
        sleeve_cap_height = st.number_input("袖山高度 (cm)", 4.0, 18.0, value=st.session_state.get("sleeve_cap_height", 10.0), key="sleeve_cap_height")
        seam = st.number_input("缝份 Seam (cm)", 0.0, 4.0, value=st.session_state.get("seam", 1.5), key="seam")
        ease = st.number_input("整体松量 Ease (cm)", 0.0, 15.0, value=st.session_state.get("ease", 4.0), key="ease")
        hem_depth = st.number_input("下摆深度/裙摆高度 (cm)", 5.0, 60.0, value=st.session_state.get("hem_depth", 12.0), key="hem_depth")

# ========== 生成按钮 ==========
st.markdown("###")
generate_clicked = st.button("🚀 立即生成设计（核对表单后点击）", use_container_width=True)

# ========== 生成逻辑 ==========
if generate_clicked:
    # 组合最终输入（优先使用 session_state 的值）
    design_input = {
        "garment": st.session_state.get("garment", garment),
        "color": st.session_state.get("color_picker", color_picker),
        "material": st.session_state.get("material_input", material_input),
        "height": st.session_state.get("height", height),
        "bust": st.session_state.get("bust", bust),
        "waist": st.session_state.get("waist", waist),
        "hip": st.session_state.get("hip", hip),
        "shoulder": st.session_state.get("shoulder", shoulder),
        "torso_length": st.session_state.get("torso_length", torso_length),
        "notes": st.session_state.get("notes_input", notes_input),
        # professional
        "neck_type": st.session_state.get("neck_type", "圆领"),
        "sleeve_length": st.session_state.get("sleeve_length", "长袖"),
        "sleeve_width": st.session_state.get("sleeve_width", 24.0),
        "sleeve_cap_height": st.session_state.get("sleeve_cap_height", 10.0),
        "seam": st.session_state.get("seam", 1.5),
        "ease": st.session_state.get("ease", 4.0),
        "hem_depth": st.session_state.get("hem_depth", 12.0)
    }

    # 优化/补齐参数
    try:
        optimized = optimize(design_input, current_mode)
    except Exception as e:
        st.error(f"优化失败：{e}")
        optimized = design_input

    # 生成图纸
    try:
        res = generate_pattern(optimized)
    except Exception as e:
        st.exception(f"生成失败：{e}")
        res = None

    if res:
        st.success("✅ 生成完成 — 向下滚动查看预览与下载")
        # 自动滚动到页面底部（预览区域）
        components.html("<script>window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });</script>", height=0)

        # 显示预览
        if res.get("preview") and os.path.exists(res["preview"]):
            st.image(res["preview"], caption="2D 成品预览 · 张小鱼原创", use_column_width=True)

        # 打包并下载
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

        st.download_button("⬇️ 下载完整文件包 (PNG + DXF + JSON)", zip_buffer.read(), file_name=f"{design_input.get('garment','design')}_package.zip", use_container_width=True)

st.markdown("---")
st.markdown("© 张小鱼原创 · Looma AI 2026")
