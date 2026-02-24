# pattern_engine.py
"""
增强版 pattern_engine：
- 使用职业参数绘制更精确的 2D 预览（Matplotlib + PIL 水印）
- 生成 DXF：前片/后片/袖子按输入尺寸绘制，并在 DXF 中加注释尺寸文字
单位：cm（请在打版前确认并按需要换算）
"""

import os
import io
import json
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import ezdxf

def _hex_to_rgb(hexstr):
    h = hexstr.lstrip('#')
    if len(h) == 3:
        h = ''.join([c*2 for c in h])
    r = int(h[0:2], 16); g = int(h[2:4], 16); b = int(h[4:6], 16)
    return (r, g, b)

def _add_watermark_pil(img: Image.Image, text="张小鱼原创"):
    try:
        overlay = Image.new('RGBA', img.size, (255,255,255,0))
        draw = ImageDraw.Draw(overlay)
        w, h = img.size
        fontsize = max(14, int(min(w,h) / 22))
        try:
            font = ImageFont.truetype("msyh.ttf", fontsize)
        except Exception:
            font = ImageFont.load_default()
        # small label bottom-right
        tw, th = draw.textsize(text, font=font)
        draw.text((w - tw - 12, h - th - 12), text, fill=(0,0,0,120), font=font)
        # faint diagonal watermark
        draw.text((int(w*0.05), int(h*0.1)), text, fill=(0,0,0,30), font=font)
        combined = Image.alpha_composite(img.convert('RGBA'), overlay)
        return combined.convert('RGB')
    except Exception:
        return img

def generate_friendly_preview(data: dict, output_path="output/preview.png"):
    """
    更细化 2D 预览：根据 neck_type, sleeve_length, sleeve_width, shoulder, torso_length 等绘制近似成衣效果
    注意：此为示意图（非完全技术打版渲染）
    """
    os.makedirs("output", exist_ok=True)
    color = data.get("color", "#FF6B6B")
    garment = data.get("garment", "连衣裙")
    material = data.get("material", "面料")
    bust = float(data.get("bust", 88))
    height = float(data.get("height", 165))
    shoulder = float(data.get("shoulder", 38))
    torso = float(data.get("torso_length", 40))
    fit = data.get("fit", "Regular")
    neck_type = data.get("neck_type", "圆领")
    sleeve_length = data.get("sleeve_length", "长袖")
    sleeve_width = float(data.get("sleeve_width", 24))
    hem_depth = float(data.get("hem_depth", 12))

    # create matplotlib canvas
    fig_w, fig_h = 6, 9
    dpi = 160
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    ax = fig.add_axes([0,0,1,1])
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 9)
    ax.axis('off')
    ax.add_patch(patches.Rectangle((0,0),6,9, facecolor="#FFFFFF", zorder=0))

    rgb = _hex_to_rgb(color)
    facecolor = (rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)

    # body box (use torso length scaled to canvas)
    main_x, main_y = 1, 1.2
    main_w, main_h = 4, 6.2
    body = patches.FancyBboxPatch((main_x, main_y), main_w, main_h,
                                 boxstyle="round,pad=0.08",
                                 linewidth=1.2, edgecolor="#222", facecolor=facecolor, zorder=2)
    ax.add_patch(body)

    # shoulder indicator (draw small trapezoid top)
    # shoulder proportion scaled for display
    sh = max(2.0, min(4.0, (shoulder / 50.0) * 4.0))
    ax.add_patch(patches.Polygon([[main_x, main_y+main_h],[main_x+sh*0.5, main_y+main_h-0.3],
                                  [main_x+main_w-sh*0.5, main_y+main_h-0.3],[main_x+main_w, main_y+main_h]],
                                 closed=True, facecolor=facecolor, edgecolor="#222", zorder=3))

    # neck rendering
    if neck_type == "圆领":
        neck = patches.Arc((main_x+main_w/2, main_y+main_h-0.2), 1.2, 0.6, theta1=200, theta2=340, edgecolor="#111", linewidth=1.5, zorder=4)
        ax.add_patch(neck)
    elif neck_type == "V 领":
        ax.plot([main_x+main_w/2 - 0.5, main_x+main_w/2, main_x+main_w/2 + 0.5],
                [main_y+main_h-0.2, main_y+main_h-0.8, main_y+main_h-0.2],
                color="#111", linewidth=1.6, zorder=4)
    elif neck_type == "立领":
        ax.add_patch(patches.Rectangle((main_x+main_w/2 - 0.4, main_y+main_h-0.2), 0.8, 0.25, facecolor="#EEE", edgecolor="#111", zorder=4))

    # sleeve rendering based on sleeve_length
    # map sleeve length to display length
    sleeve_map = {"无袖":0.0, "短袖":1.2, "七分袖":2.5, "长袖":3.5}
    slen = sleeve_map.get(sleeve_length, 3.5)
    # left sleeve polygon
    left_slee = patches.Polygon([[main_x, main_y+main_h*0.9],
                                 [main_x - slen, main_y+main_h*0.9 - slen*0.3],
                                 [main_x - slen, main_y+main_h*0.9 - slen*0.3 - 0.2],
                                 [main_x, main_y+main_h*0.9 - 0.1]],
                                closed=True, facecolor=facecolor, edgecolor="#222", zorder=2)
    right_slee = patches.Polygon([[main_x+main_w, main_y+main_h*0.9],
                                  [main_x+main_w + slen, main_y+main_h*0.9 - slen*0.3],
                                  [main_x+main_w + slen, main_y+main_h*0.9 - slen*0.3 - 0.2],
                                  [main_x+main_w, main_y+main_h*0.9 - 0.1]],
                                 closed=True, facecolor=facecolor, edgecolor="#222", zorder=2)
    if slen > 0:
        ax.add_patch(left_slee)
        ax.add_patch(right_slee)

    # skirt or pant differences
    if "裙" in garment or "dress" in garment.lower():
        skirt = patches.Polygon([[main_x, main_y],[main_x+main_w, main_y],[main_x+main_w + 0.8, main_y - hem_depth/10.0],[main_x-0.8, main_y - hem_depth/10.0]],
                                closed=True, facecolor=facecolor, edgecolor="#222", linewidth=1.2, zorder=2)
        ax.add_patch(skirt)
    elif "裤" in garment or "pants" in garment.lower() or "jeans" in garment.lower():
        leg_w = main_w*0.42
        ax.add_patch(patches.Rectangle((main_x, main_y-0.2), leg_w, main_h*0.55, facecolor=facecolor, edgecolor="#222", zorder=2))
        ax.add_patch(patches.Rectangle((main_x+main_w-leg_w, main_y-0.2), leg_w, main_h*0.55, facecolor=facecolor, edgecolor="#222", zorder=2))

    # structure lines and labels
    ax.plot([main_x, main_x+main_w], [main_y+main_h*0.6, main_y+main_h*0.6], linestyle='--', color='#333', linewidth=1, zorder=5)
    ax.plot([main_x, main_x+main_w], [main_y+main_h*0.35, main_y+main_h*0.35], linestyle='--', color='#333', linewidth=1, zorder=5)
    ax.text(3, 8.6, f"{garment} · {material} · {neck_type}", ha='center', fontsize=16, fontweight='bold', color="#111", zorder=6)
    ax.text(3, 0.5, f"胸围适配: {int(bust)}cm    身高参考: {int(height)}cm    肩宽: {shoulder}cm", ha='center', fontsize=10, color="#333", zorder=6)

    # save to buffer, add watermark via PIL
    buf = io.BytesIO()
    plt.savefig(buf, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    buf.seek(0)
    pil_img = Image.open(buf).convert('RGB')
    pil_img = _add_watermark_pil(pil_img, "张小鱼原创")
    preview_path = os.path.join("output", "preview.png")
    pil_img.save(preview_path, format="PNG")
    return preview_path

def generate_dxf(data: dict, output_path=None):
    """
    更精确 DXF 布局：
    - 前片 / 后片 为矩形示意，尺寸基于胸围/腰/臀/身长等
    - 袖子按袖长/袖肥度绘制
    - 在 DXF 中添加文字标注（名称、关键尺寸、缝份）
    单位：cm（图上标注也以 cm 表示）
    """
    os.makedirs("output", exist_ok=True)
    garment = data.get("garment", "design")
    if output_path is None:
        output_path = os.path.join("output", f"{garment}_pattern.dxf")
    try:
        bust = float(data.get("bust", 88))
        waist = float(data.get("waist", 68))
        hip = float(data.get("hip", 94))
        height = float(data.get("height", 165))
        shoulder = float(data.get("shoulder", 38))
        torso = float(data.get("torso_length", 40))
        # professional params
        seam = float(data.get("seam", 1.5))
        ease = float(data.get("ease", 4.0))
        sleeve_width = float(data.get("sleeve_width", 24.0))
        sleeve_cap = float(data.get("sleeve_cap_height", 10.0))
        sleeve_len = data.get("sleeve_length", "长袖")
        neck_type = data.get("neck_type", "圆领")
    except Exception:
        # fallback defaults
        bust, waist, hip, height, shoulder, torso = 88, 68, 94, 165, 38, 40
        seam, ease, sleeve_width, sleeve_cap = 1.5, 4.0, 24.0, 10.0
        sleeve_len, neck_type = "长袖", "圆领"

    # compute quarter-front width (cm)
    front_w = (bust / 4.0) + (ease / 4.0) + seam
    body_h = torso  # 用 torso（肩点到腰）作为裁片主体高度参考
    # skirt/pants extension
    lower_extension = max(0, (height * 0.6) - body_h)  # roughly skirt length if any

    doc = ezdxf.new(dxfversion="R2010")
    # try set units (optional) - 4 corresponds to Millimeters in DXF INSUNITS; we keep coord units as cm
    try:
        doc.header["$INSUNITS"] = 6  # 6 => centimeters (DXF INSUNITS: 6 = centimeters) if supported
    except Exception:
        pass
    msp = doc.modelspace()

    # Draw front piece at origin (0,0)
    x0, y0 = 0.0, 0.0
    pts_front = [(x0, y0), (x0 + front_w, y0), (x0 + front_w, y0 + body_h), (x0, y0 + body_h)]
    msp.add_lwpolyline(pts_front, close=True, dxfattribs={"layer": "CUT"})
    # label front
    msp.add_text("FRONT_PIECE", dxfattribs={"height": 2.5, "insert": (x0 + front_w/4, y0 + body_h + 1)})

    # add seam allowance polyline (offset inside)
    seam_offset = seam
    pts_front_seam = [(x0 + seam_offset, y0 + seam_offset),
                      (x0 + front_w - seam_offset, y0 + seam_offset),
                      (x0 + front_w - seam_offset, y0 + body_h - seam_offset),
                      (x0 + seam_offset, y0 + body_h - seam_offset)]
    msp.add_lwpolyline(pts_front_seam, close=True, dxfattribs={"layer": "SEAM"})

    # Draw back piece offset to the right
    gap = 5.0
    bx0 = x0 + front_w + gap
    pts_back = [(bx0, y0), (bx0 + front_w, y0), (bx0 + front_w, y0 + body_h), (bx0, y0 + body_h)]
    msp.add_lwpolyline(pts_back, close=True, dxfattribs={"layer": "CUT"})
    msp.add_text("BACK_PIECE", dxfattribs={"height": 2.5, "insert": (bx0 + front_w/4, y0 + body_h + 1)})

    # Draw sleeve piece below
    sx0 = 0.0
    sy0 = y0 - (sleeve_cap + 10.0)  # place below with some gap
    # sleeve length mapping to approximate cm
    sleeve_len_cm_map = {"无袖": 0.0, "短袖": 22.0, "七分袖": 45.0, "长袖": 60.0}
    slen_cm = sleeve_len_cm_map.get(sleeve_len, 60.0)
    sleeve_h = sleeve_cap
    sleeve_w = sleeve_width / 2.0 + seam  # half sleeve (one piece) width approximation

    pts_sleeve = [(sx0, sy0), (sx0 + sleeve_w, sy0), (sx0 + sleeve_w, sy0 + sleeve_h), (sx0, sy0 + sleeve_h)]
    msp.add_lwpolyline(pts_sleeve, close=True, dxfattribs={"layer": "CUT"})
    msp.add_text("SLEEVE_PIECE", dxfattribs={"height": 2.2, "insert": (sx0 + sleeve_w/8, sy0 + sleeve_h + 1)})

    # Add dimension-like text annotations (simple)
    def add_label(x, y, txt):
        msp.add_text(txt, dxfattribs={"height": 1.8, "insert": (x, y)})

    add_label(x0 + front_w / 2, y0 - 2.0, f"胸围/4 + ease/4 + seam = {front_w:.2f} cm")
    add_label(bx0 + front_w / 2, y0 - 2.0, f"后片宽 = {front_w:.2f} cm")
    add_label(sx0 + sleeve_w / 2, sy0 - 2.0, f"袖长(近似) = {slen_cm:.1f} cm, 袖肥 = {sleeve_width:.1f} cm")

    # Add small legend block with key parameters
    legend_x = bx0 + front_w + 4
    legend_y = y0 + body_h
    msp.add_text(f"garment: {garment}", dxfattribs={"height": 1.8, "insert": (legend_x, legend_y)})
    msp.add_text(f"material: {data.get('material','')}", dxfattribs={"height": 1.8, "insert": (legend_x, legend_y - 2)})
    msp.add_text(f"neck: {neck_type}", dxfattribs={"height": 1.8, "insert": (legend_x, legend_y - 4)})
    msp.add_text(f"seam: {seam:.2f} cm", dxfattribs={"height": 1.8, "insert": (legend_x, legend_y - 6)})
    msp.add_text(f"ease: {ease:.2f} cm", dxfattribs={"height": 1.8, "insert": (legend_x, legend_y - 8)})

    doc.saveas(output_path)
    return output_path

def generate_pattern(data: dict):
    """
    主调用：生成 preview.png 与更精确的 pattern.dxf，并返回路径字典
    """
    os.makedirs("output", exist_ok=True)
    # ensure some default values exist
    data.setdefault("bust", 88)
    data.setdefault("waist", 68)
    data.setdefault("hip", 94)
    data.setdefault("height", 165)
    # generate preview
    preview = generate_friendly_preview(data, output_path="output/preview.png")
    # generate dxf
    dxf = generate_dxf(data, output_path=os.path.join("output", f"{data.get('garment','design')}_pattern.dxf"))
    # save json
    json_path = os.path.join("output", f"{data.get('garment','design')}_design.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"status":"success", "preview": preview, "dxf": dxf, "json": json_path}