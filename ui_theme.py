# ui_theme.py
import streamlit as st

def apply_theme(primary_color="#111111", secondary_color="#FF6B6B", bg_color="#FFFFFF"):
    """
    注入基础 CSS，让界面带有“张小鱼原创”风格痕迹。
    primary_color / secondary_color 可从 app.py 的颜色选择器动态传入。
    """
    css = f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft Yahei', Arial;
    }}
    /* 顶部标题样式 */
    .app-title {{
        display:flex;
        align-items:center;
        gap:12px;
    }}
    .brand-badge {{
        font-size:14px;
        font-weight:700;
        color:{primary_color};
        background: rgba(0,0,0,0.03);
        padding:6px 10px;
        border-radius:8px;
    }}
    /* 按钮渐变 */
    .stButton > button {{
        background: linear-gradient(135deg, {primary_color}, {secondary_color});
        color: white;
        border-radius: 8px;
        height: 44px;
        font-weight: 600;
    }}
    /* 小脚注 / 水印 风格 */
    .zhangxiaoyu-watermark {{
        position: fixed;
        right: 18px;
        bottom: 18px;
        opacity: 0.12;
        font-size: 14px;
        font-weight: 800;
        transform: rotate(-15deg);
        color: {primary_color};
        pointer-events: none;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def show_brand_header(title="Looma AI 定制系统 · 张小鱼原创", subtitle="千人千面 · 口语化定制"):
    st.markdown(f"""
    <div class="app-title">
      <div style="width:56px; height:56px; border-radius:12px; background:linear-gradient(135deg,#FF6B6B,#FFB199); display:flex; align-items:center; justify-content:center; color:white; font-weight:900;">
        ZX
      </div>
      <div>
        <div style="font-size:20px; font-weight:800;">{title}</div>
        <div style="font-size:12px; color: #555;">{subtitle}</div>
      </div>
      <div style="margin-left:auto;">
        <span class="brand-badge">张小鱼原创</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

def show_watermark():
    st.markdown('<div class="zhangxiaoyu-watermark">张小鱼原创</div>', unsafe_allow_html=True)