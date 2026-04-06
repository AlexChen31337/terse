#!/usr/bin/env python3
"""
Create a fallback cover image for the technical article.
Given the ComfyUI server is down, we'll create a synthetic image
that matches the cyberpunk aesthetic of the requested prompt.
"""

from PIL import Image, ImageDraw, ImageFilter
import math
import random
import os

OUTPUT_DIR = "/home/bowen/.openclaw/workspace/tmp"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "zimage_cover.png")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_cover_image(width=768, height=1024):
    """Create a cover image with cyberpunk aesthetic"""

    # Create image with dark background
    img = Image.new('RGB', (width, height), color=(10, 15, 30))
    draw = ImageDraw.Draw(img, 'RGBA')

    # Create gradient-like effect by drawing multiple transparent rectangles
    # Blue and purple gradient background
    for y in range(height):
        # Calculate color based on position (gradient from dark blue to purple)
        ratio = y / height
        r = int(20 + ratio * 80)  # 20 -> 100
        g = int(15 + ratio * 50)  # 15 -> 65
        b = int(50 + ratio * 100)  # 50 -> 150

        # Also add some purple tint
        purple_ratio = (math.sin(y / height * math.pi) + 1) / 2
        r = int(r + purple_ratio * 40)
        g = int(g * (1 - purple_ratio * 0.5))
        b = int(b + purple_ratio * 50)

        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Draw some glowing nodes and connections (representing the OAuth/agent connection)
    random.seed(42)  # Use seed for reproducibility

    # Central area nodes
    nodes = [
        (width // 4, height // 3, "cloud/oauth"),
        (width * 3 // 4, height // 3, "agent"),
        (width // 2, height * 2 // 3, "connection"),
    ]

    # Draw luminous data stream paths between nodes
    for i in range(len(nodes) - 1):
        x1, y1, _ = nodes[i]
        x2, y2, _ = nodes[i + 1]

        # Draw path with gradient effect
        steps = 30
        for step in range(steps):
            t = step / steps
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)

            # Pulsing glow effect
            glow_strength = 255 * (1 - abs(t - 0.5) * 2) * 0.8
            radius = int(15 + 10 * math.sin(t * math.pi))

            # Draw glow circles along the path
            for r in range(radius, 0, -3):
                alpha = int(glow_strength * (1 - r / radius) / 2)
                draw.ellipse(
                    [(x - r, y - r), (x + r, y + r)],
                    fill=(100, 150, 255, alpha)
                )

    # Draw central nodes with glow effect
    for node_x, node_y, label in nodes:
        # Draw glowing aura
        for radius in range(80, 0, -5):
            alpha = int(255 * (1 - radius / 80) * 0.15)
            color = (150, 100, 255, alpha)
            draw.ellipse(
                [(node_x - radius, node_y - radius),
                 (node_x + radius, node_y + radius)],
                fill=color
            )

        # Draw bright core
        draw.ellipse(
            [(node_x - 20, node_y - 20),
             (node_x + 20, node_y + 20)],
            fill=(200, 150, 255, 255)
        )

        draw.ellipse(
            [(node_x - 12, node_y - 12),
             (node_x + 12, node_y + 12)],
            fill=(230, 200, 255, 255)
        )

    # Add neural network-style connections
    num_particles = 100
    random.seed(42)
    for _ in range(num_particles):
        # Random particle positions
        px = random.randint(width // 6, width * 5 // 6)
        py = random.randint(height // 4, height * 3 // 4)

        # Determine color based on position
        brightness = int((px / width) * 100 + (py / height) * 155)
        brightness = max(100, min(255, brightness))

        # Draw small glowing particles
        for r in range(8, 0, -2):
            alpha = int(brightness * (1 - r / 8) * 0.4)
            draw.ellipse(
                [(px - r, py - r), (px + r, py + r)],
                fill=(100 + brightness // 3, 100 + brightness // 4, brightness, alpha)
            )

    # Add some tech-aesthetic line patterns
    line_color = (100, 150, 200, 60)
    for i in range(5):
        y_pos = height // 5 * (i + 1)
        # Draw dotted line
        for x in range(0, width, 40):
            draw.line([(x, y_pos), (x + 20, y_pos)], fill=line_color, width=2)

    # Apply slight blur for ethereal glow effect
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

    # Add some subtle noise/texture
    pixels = img.load()
    for y in range(height):
        for x in range(0, width, 8):
            noise = random.randint(-10, 10)
            try:
                r, g, b = pixels[x, y]
                pixels[x, y] = (
                    max(0, min(255, r + noise)),
                    max(0, min(255, g + noise)),
                    max(0, min(255, b + noise))
                )
            except:
                pass

    return img

def main():
    print("="*60)
    print("Creating Fallback Cover Image (ComfyUI Server Unavailable)")
    print("="*60)
    print(f"Image dimensions: 768x1024")
    print(f"Theme: Cyberpunk OAuth/Agent Connection")
    print()

    # Create the image
    print("Generating cover image...")
    img = create_cover_image(768, 1024)

    # Save the image
    print(f"Saving to: {OUTPUT_FILE}")
    img.save(OUTPUT_FILE, quality=95)

    # Verify the file was created
    if os.path.exists(OUTPUT_FILE):
        file_size = os.path.getsize(OUTPUT_FILE)
        print()
        print("="*60)
        print("SUCCESS!")
        print(f"Fallback cover image created and saved to:")
        print(f"  {OUTPUT_FILE}")
        print(f"File size: {file_size} bytes")
        print("="*60)
        return True
    else:
        print("ERROR: Failed to create image file")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
