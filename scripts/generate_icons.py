from PIL import Image, ImageDraw, ImageFont
import os

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

def create_icon(size, out_path):
    # Create dark surface
    img = Image.new("RGBA", (size, size), (15, 23, 42, 255)) # Slate-900
    draw = ImageDraw.Draw(img)
    
    # Draw rounded-corner rect or circular emerald ring
    margin = int(size * 0.08)
    corner_radius = int(size * 0.22)
    
    # Rounded border
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner_radius,
        fill=(2, 6, 23, 255), # Slate-950
        outline=(16, 185, 129, 255), # Emerald-500
        width=max(2, int(size * 0.03))
    )
    
    # Draw a stylized lightning bolt / "D" monogram in emerald
    # Draw geometric lightning bolt polygon
    cx, cy = size // 2, size // 2
    scale = size / 100.0
    
    # Lightning bolt coordinates centered
    bolt_pts = [
        (cx + 4 * scale, cy - 28 * scale),
        (cx - 18 * scale, cy + 2 * scale),
        (cx - 2 * scale, cy + 2 * scale),
        (cx - 8 * scale, cy + 30 * scale),
        (cx + 20 * scale, cy - 4 * scale),
        (cx + 3 * scale, cy - 4 * scale),
        (cx + 12 * scale, cy - 28 * scale),
    ]
    
    draw.polygon(bolt_pts, fill=(16, 185, 129, 255))
    
    img.save(out_path, "PNG")
    print(f"Generated {out_path} ({size}x{size})")

for folder in [WEB_DIR, DOCS_DIR]:
    os.makedirs(folder, exist_ok=True)
    create_icon(192, os.path.join(folder, "icon-192.png"))
    create_icon(512, os.path.join(folder, "icon-512.png"))
