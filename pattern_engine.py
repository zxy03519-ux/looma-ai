# pattern_engine.py
import os
import json
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import ezdxf
import io

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _hex_to_rgb(hexstr):
    if not hexstr:
        return (255, 182, 193)
    h = hexstr.lstrip('#')
    if len(h) == 3:
        h = ''.join([c*2 for c in h])
    try:
        r = int(h[0:2], 16); g = int(h[2:4], 16); b = int(h[4:6], 16)
        return (r, g, b)
    except (ValueError, TypeError):
        return (255, 182, 193)

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
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((w - tw - 12, h - th - 12), text, fill=(0,0,0,120), font=font)
        draw.text((int(w*0.05), int(h*0.1)), text, fill=(0,0,0,30), font=font)
        combined = Image.alpha_composite(img.convert('RGBA'), overlay)
        return combined.convert('RGB')
    except Exception:
        return img

def generate_friendly_preview(data: dict, output_path=None):
    color = data.get("color") or "#FFB6C1"
    garment = data.get("garment", "设计")
    material = data.get("material", "面料")
    bust = float(data.get("bust") or 88)
    height = float(data.get("height") or 165)
    shoulder = float(data.get("shoulder") or 38)
    torso = float(data.get("torso_length") or 40)
    neck_type = data.get("neck_type", "圆领")
    sleeve_length = data.get("sleeve_length", "长袖")
    sleeve_width = float(data.get("sleeve_width") or 24)
    hem_depth = float(data.get("hem_depth") or 12)

    fig_w, fig_h = 6, 9
    dpi = 160
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    ax = fig.add_axes([0,0,1,1])
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 9)
    ax.axis('off')
    ax.add_patch(patches.Rectangle((0,0),6,9, facecolor="#FFF", zorder=0))

    rgb = _hex_to_rgb(color)
    facecolor = (rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)

    main_x, main_y = 1, 1.2
    main_w, main_h = 4, 6.2
    body = patches.FancyBboxPatch((main_x, main_y), main_w, main_h,
                                 boxstyle="round,pad=0.08",
                                 linewidth=1.2, edgecolor="#222", facecolor=facecolor, zorder=2)
    ax.add_patch(body)

    if "裙" in str(garment) or "dress" in str(garment).lower():
        skirt = patches.Polygon([[main_x, main_y],[main_x+main_w, main_y],[main_x+main_w + 0.8, main_y - hem_depth/10.0],[main_x-0.8, main_y - hem_depth/10.0]],
                                closed=True, facecolor=facecolor, edgecolor="#222", linewidth=1.2, zorder=2)
        ax.add_patch(skirt)

    if neck_type == "圆领":
        neck = patches.Arc((main_x+main_w/2, main_y+main_h-0.2), 1.2, 0.6, theta1=200, theta2=340, edgecolor="#111", linewidth=1.5, zorder=4)
        ax.add_patch(neck)

    ax.plot([main_x, main_x+main_w], [main_y+main_h*0.6, main_y+main_h*0.6], linestyle='--', color='#333', linewidth=1, zorder=5)
    ax.plot([main_x, main_x+main_w], [main_y+main_h*0.35, main_y+main_h*0.35], linestyle='--', color='#333', linewidth=1, zorder=5)
    ax.text(3, 8.6, f"{garment} · {material} · {neck_type}", ha='center', fontsize=16, fontweight='bold', color="#111", zorder=6)
    ax.text(3, 0.5, f"胸围参考: {int(bust)}cm    身高参考: {int(height)}cm    肩宽: {shoulder}cm", ha='center', fontsize=10, color="#333", zorder=6)

    buf = io.BytesIO()
    plt.savefig(buf, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    buf.seek(0)
    pil_img = Image.open(buf).convert('RGB')
    pil_img = _add_watermark_pil(pil_img, "张小鱼原创")
    preview_path = output_path or os.path.join(OUTPUT_DIR, "preview.png")
    pil_img.save(preview_path, format="PNG")
    return preview_path

def generate_dxf(data: dict, output_path=None):
    garment = data.get("garment", "design")
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, f"{garment}_pattern.dxf")
    try:
        bust = float(data.get("bust") or 88)
        waist = float(data.get("waist") or 68)
        hip = float(data.get("hip") or 94)
        height = float(data.get("height") or 165)
        shoulder = float(data.get("shoulder") or 38)
        torso = float(data.get("torso_length") or 40)
        seam = float(data.get("seam") or 1.5)
        ease = float(data.get("ease") or 4.0)
        sleeve_width = float(data.get("sleeve_width") or 24.0)
        sleeve_cap = float(data.get("sleeve_cap_height") or 10.0)
        sleeve_len_option = data.get("sleeve_length", "长袖")
    except (TypeError, ValueError):
        bust, waist, hip, height, shoulder, torso = 88, 68, 94, 165, 38, 40
        seam, ease, sleeve_width, sleeve_cap = 1.5, 4.0, 24.0, 10.0
        sleeve_len_option = "长袖"

    front_w = (bust / 4.0) + (ease / 4.0) + seam
    body_h = torso
    doc = ezdxf.new(dxfversion="R2010")
    try:
        doc.header["$INSUNITS"] = 6
    except Exception:
        pass
    msp = doc.modelspace()

    x0, y0 = 0.0, 0.0
    pts_front = [(x0, y0), (x0 + front_w, y0), (x0 + front_w, y0 + body_h), (x0, y0 + body_h)]
    msp.add_lwpolyline(pts_front, close=True, dxfattribs={"layer": "CUT"})
    seam_offset = seam
    pts_front_seam = [(x0 + seam_offset, y0 + seam_offset),
                      (x0 + front_w - seam_offset, y0 + seam_offset),
                      (x0 + front_w - seam_offset, y0 + body_h - seam_offset),
                      (x0 + seam_offset, y0 + body_h - seam_offset)]
    msp.add_lwpolyline(pts_front_seam, close=True, dxfattribs={"layer": "SEAM"})

    gap = 5.0
    bx0 = x0 + front_w + gap
    pts_back = [(bx0, y0), (bx0 + front_w, y0), (bx0 + front_w, y0 + body_h), (bx0, y0 + body_h)]
    msp.add_lwpolyline(pts_back, close=True, dxfattribs={"layer": "CUT"})
    msp.add_text("BACK_PIECE", dxfattribs={"height": 1.8, "insert": (bx0 + front_w/4, y0 + body_h + 1)})

    sleeve_x = 0
    sleeve_y = y0 - (sleeve_cap + 10.0)
    sleeve_len_map = {"无袖": 0.0, "短袖": 22.0, "七分袖": 45.0, "长袖": 60.0}
    slen_cm = sleeve_len_map.get(sleeve_len_option, 60.0)
    sleeve_h = max(sleeve_cap, slen_cm / 3.0)
    sleeve_w = sleeve_width / 2.0 + seam
    pts_sleeve = [(sleeve_x, sleeve_y), (sleeve_x + sleeve_w, sleeve_y), (sleeve_x + sleeve_w, sleeve_y + sleeve_h), (sleeve_x, sleeve_y + sleeve_h)]
    msp.add_lwpolyline(pts_sleeve, close=True, dxfattribs={"layer": "CUT"})
    msp.add_text("SLEEVE_PIECE", dxfattribs={"height": 1.8, "insert": (sleeve_x + sleeve_w/8, sleeve_y + sleeve_h + 1)})

    legend_x = bx0 + front_w + 4
    legend_y = y0 + body_h
    msp.add_text(f"garment: {garment}", dxfattribs={"height": 1.8, "insert": (legend_x, legend_y)})
    msp.add_text(f"material: {data.get('material','')}", dxfattribs={"height": 1.8, "insert": (legend_x, legend_y - 2)})
    msp.add_text(f"seam: {seam:.2f} cm", dxfattribs={"height": 1.8, "insert": (legend_x, legend_y - 4)})
    msp.add_text(f"ease: {ease:.2f} cm", dxfattribs={"height": 1.8, "insert": (legend_x, legend_y - 6)})

    doc.saveas(output_path)
    return output_path

def generate_pattern(data: dict):
    preview_path = generate_friendly_preview(data, output_path=os.path.join(OUTPUT_DIR, "preview.png"))
    dxf_path = generate_dxf(data, output_path=os.path.join(OUTPUT_DIR, f"{data.get('garment','design')}_pattern.dxf"))
    json_path = os.path.join(OUTPUT_DIR, f"{data.get('garment','design')}_design.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"status":"success", "preview": preview_path, "dxf": dxf_path, "json": json_path}
