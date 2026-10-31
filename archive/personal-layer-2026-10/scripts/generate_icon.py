"""Generate app icon for the launcher .app bundle."""
import math
from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
CENTER = SIZE // 2
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# --- Background: rounded rectangle with gradient-like effect ---
# Base color: deep navy-purple
for i in range(20):
    shrink = i * 2
    r = 180 - shrink
    # Gradient from #1a1a4e (top) to #2d1b69 (bottom)
    red = 26 + i * 1
    green = 26 + i * 0
    blue = 78 + i * 3
    draw.rounded_rectangle(
        [shrink, shrink, SIZE - shrink, SIZE - shrink],
        radius=160 - i * 2,
        fill=(red, green, blue, 255),
    )

# --- Neo4j-inspired graph nodes (3 connected nodes) ---
# Node positions (triangle arrangement)
nodes = [
    (CENTER, CENTER - 180),      # Top
    (CENTER - 200, CENTER + 140), # Bottom-left
    (CENTER + 200, CENTER + 140), # Bottom-right
]
node_radius = 70
edge_color = (100, 200, 255, 180)
node_colors = [
    (0, 188, 212, 255),   # Cyan - top
    (76, 175, 80, 255),   # Green - bottom-left
    (255, 152, 0, 255),   # Orange - bottom-right
]

# Draw edges (connections)
for i in range(len(nodes)):
    for j in range(i + 1, len(nodes)):
        x1, y1 = nodes[i]
        x2, y2 = nodes[j]
        for w in range(6, 0, -1):
            alpha = 60 + w * 20
            draw.line([(x1, y1), (x2, y2)], fill=(*edge_color[:3], min(alpha, 255)), width=w)

# Draw nodes (circles with glow)
for (cx, cy), color in zip(nodes, node_colors):
    # Glow
    for r in range(node_radius + 30, node_radius, -2):
        alpha = max(0, 80 - (r - node_radius) * 3)
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(color[0], color[1], color[2], alpha),
        )
    # Solid node
    draw.ellipse(
        [cx - node_radius, cy - node_radius, cx + node_radius, cy + node_radius],
        fill=color,
    )
    # Inner highlight
    highlight_r = node_radius - 15
    draw.ellipse(
        [cx - highlight_r, cy - highlight_r + 5, cx + highlight_r - 10, cy],
        fill=(255, 255, 255, 60),
    )

# --- Center heart icon (support/care symbol) ---
heart_cx, heart_cy = CENTER, CENTER - 180
heart_size = 28

def draw_heart(draw, cx, cy, size, fill):
    """Draw a simple heart shape."""
    points = []
    for t_deg in range(0, 360, 2):
        t = math.radians(t_deg)
        x = size * 16 * math.sin(t) ** 3
        y = -size * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        points.append((cx + x / 16, cy + y / 16 + size * 0.3))
    draw.polygon(points, fill=fill)

draw_heart(draw, heart_cx, heart_cy, heart_size, (255, 255, 255, 230))

# --- Shield icon on bottom-left node (safety) ---
sx, sy = nodes[1]
shield_w, shield_h = 32, 40
draw.polygon(
    [(sx, sy - shield_h), (sx + shield_w, sy - shield_h // 2),
     (sx + shield_w, sy + shield_h // 4), (sx, sy + shield_h),
     (sx - shield_w, sy + shield_h // 4), (sx - shield_w, sy - shield_h // 2)],
    fill=(255, 255, 255, 230),
)

# --- People icon on bottom-right node (network) ---
px, py = nodes[2]
# Head
draw.ellipse([px - 12, py - 22, px + 12, py - 2], fill=(255, 255, 255, 230))
# Body
draw.arc([px - 20, py - 5, px + 20, py + 25], start=0, end=180, fill=(255, 255, 255, 230), width=4)

# --- Text label at bottom ---
jp_font = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
try:
    font_large = ImageFont.truetype(jp_font, 100)
    font_sub = ImageFont.truetype(jp_font, 52)
except (IOError, OSError):
    font_large = ImageFont.load_default()
    font_sub = font_large

# "親なき後" text
text_main = "親なき後"
bbox = draw.textbbox((0, 0), text_main, font=font_large)
tw = bbox[2] - bbox[0]
draw.text(
    (CENTER - tw // 2, SIZE - 280),
    text_main,
    fill=(255, 255, 255, 240),
    font=font_large,
)

# "支援DB" subtitle
text_sub = "支援DB"
bbox2 = draw.textbbox((0, 0), text_sub, font=font_sub)
tw2 = bbox2[2] - bbox2[0]
draw.text(
    (CENTER - tw2 // 2, SIZE - 165),
    text_sub,
    fill=(200, 200, 255, 200),
    font=font_sub,
)

img.save("/tmp/app_icon_1024.png")
print("Icon generated: /tmp/app_icon_1024.png")
