from PIL import Image, ImageDraw, ImageFont
import os

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

def create_icon(size, out_path):
    # Creamy paper background
    img = Image.new("RGBA", (size, size), (248, 245, 238, 255)) # Cream Paper #F8F5EE
    draw = ImageDraw.Draw(img)
    
    margin = int(size * 0.08)
    corner_radius = int(size * 0.22)
    
    # Paper border
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner_radius,
        fill=(255, 255, 255, 255), # White matte
        outline=(229, 223, 211, 255), # Linen #E5DFD3
        width=max(2, int(size * 0.03))
    )
    
    # Draw Deep Oxblood lightning / emblem
    cx, cy = size // 2, size // 2
    scale = size / 100.0
    
    bolt_pts = [
        (cx + 4 * scale, cy - 28 * scale),
        (cx - 18 * scale, cy + 2 * scale),
        (cx - 2 * scale, cy + 2 * scale),
        (cx - 8 * scale, cy + 30 * scale),
        (cx + 20 * scale, cy - 4 * scale),
        (cx + 3 * scale, cy - 4 * scale),
        (cx + 12 * scale, cy - 28 * scale),
    ]
    
    draw.polygon(bolt_pts, fill=(155, 34, 38, 255)) # Oxblood #9B2226
    
    img.save(out_path, "PNG")
    print(f"Generated {out_path} ({size}x{size})")

for folder in [WEB_DIR, DOCS_DIR]:
    os.makedirs(folder, exist_ok=True)
    create_icon(192, os.path.join(folder, "icon-192.png"))
    create_icon(512, os.path.join(folder, "icon-512.png"))
