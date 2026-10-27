"""
Helper script to generate the local SystemScope branding logo using Pillow.
Demonstrates Pillow's drawing and rendering capabilities.
"""

import os
from PIL import Image, ImageDraw


def generate_systemscope_logo(output_path: str = "assets/logo.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    size = (512, 512)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base dark glowing circular badge
    center = (256, 256)
    radius = 240
    # Outer subtle glow
    for r in range(240, 210, -5):
        alpha = int(40 * ((r - 210) / 30))
        draw.ellipse([256 - r, 256 - r, 256 + r, 256 + r], fill=(15, 23, 42, alpha))

    # Inner badge background (Slate-950)
    draw.ellipse([256 - 220, 256 - 220, 256 + 220, 256 + 220], fill=(10, 15, 30, 255), outline=(56, 189, 248, 180), width=6)
    
    # Outer decorative radar rings
    draw.ellipse([256 - 170, 256 - 170, 256 + 170, 256 + 170], outline=(30, 41, 59, 200), width=3)
    draw.ellipse([256 - 120, 256 - 120, 256 + 120, 256 + 120], outline=(51, 65, 85, 180), width=2)
    draw.ellipse([256 - 70, 256 - 70, 256 + 70, 256 + 70], outline=(71, 85, 105, 160), width=2)

    # Crosshair scope axes
    draw.line([(256, 40), (256, 472)], fill=(56, 189, 248, 70), width=2)
    draw.line([(40, 256), (472, 256)], fill=(56, 189, 248, 70), width=2)

    # Futuristic dynamic telemetry waveform (ECG / Activity pulse)
    pulse_points = [
        (80, 256),
        (140, 256),
        (170, 256),
        (190, 210),
        (210, 310),
        (230, 150),
        (260, 360),
        (280, 220),
        (300, 280),
        (320, 256),
        (432, 256),
    ]

    # Glowing pulse shadow
    for w in [8, 5]:
        draw.line(pulse_points, fill=(6, 182, 212, 100), width=w, joint="curve")
    # Crisp cyan pulse line
    draw.line(pulse_points, fill=(56, 189, 248, 255), width=4, joint="curve")

    # Center target glow dot
    draw.ellipse([256 - 8, 256 - 8, 256 + 8, 256 + 8], fill=(99, 102, 241, 255), outline=(255, 255, 255, 255), width=2)

    # Save initial high-res image
    img.save(output_path, "PNG")
    print(f"Generated logo at: {output_path}")


if __name__ == "__main__":
    generate_systemscope_logo()
