# ui_theme.py
import streamlit as st

def apply_theme(primary_color="#111111", secondary_color="#FF6B6B", bg_color="#FFFFFF"):
    css = f"""
    <style>
    .stApp {{ background-color: {bg_color}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft Yahei', Arial; }}
    .app-title {{ display:flex; align-items:center; gap:12px; padding:6px 0; }}
    .brand-badge {{ font-size:13px; font-weight:700; color:{primary_color}; background: rgba(0,0,0,0.03); padding:6px 10px; border-radius:8px; }}
    .stButton>button, button[data-baseweb="button"] {{ background: linear-gradient(135deg, {primary_color}, {secondary_color}) !important; color: white !important; border-radius: 10px !important; height: 48px !important; font-weight: 700 !important; font-size: 16px !important; }}
    .css-1d391kg, .css-18e3th9, .css-1offfwp {{ padding-top: 6px !important; padding-bottom: 6px !important; }}
    .zhangxiaoyu-watermark {{ position: fixed; right: 14px; bottom: 14px; opacity: 0.10; font-size: 12px; font-weight: 800; transform: rotate(-12deg); color: {primary_color}; pointer-events: none; }}
    @media (max-width: 600px) {{
        .stApp {{ font-size: 16px; }}
        .brand-badge {{ font-size:12px; padding:6px 8px; }}
        .stButton>button {{ height:54px !important; font-size:18px !important; }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def show_brand_header(title="Looma AI 定制系统 · 张小鱼原创", subtitle="千人千面 · 口语化定制"):
    st.markdown(f"""
    <div class="app-title">
      <div style="width:48px; height:48px; border-radius:10px; background:linear-gradient(135deg,#FF6B6B,#FFB199); display:flex; align-items:center; justify-content:center; color:white; font-weight:900;">ZX</div>
      <div>
        <div style="font-size:18px; font-weight:800;">{title}</div>
        <div style="font-size:12px; color: #666;">{subtitle}</div>
      </div>
      <div style="margin-left:auto;"><span class="brand-badge">张小鱼原创</span></div>
    </div>
    """, unsafe_allow_html=True)

def show_watermark():
    st.markdown('<div class="zhangxiaoyu-watermark">张小鱼原创</div>', unsafe_allow_html=True)
