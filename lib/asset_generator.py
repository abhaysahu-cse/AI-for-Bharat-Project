# lib/asset_generator.py
"""
Automatic placeholder asset generator.
Creates missing assets (logo, placeholder images) on startup.
"""

import os
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

def ensure_assets_exist():
    """
    Ensure all required assets exist. Create placeholders if missing.
    This prevents crashes when assets are missing.
    """
    # Ensure assets directory exists
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR, exist_ok=True)
    
    # Create logo.png if missing
    logo_path = os.path.join(ASSETS_DIR, "logo.png")
    if not os.path.exists(logo_path) or os.path.getsize(logo_path) == 0:
        create_logo_placeholder(logo_path)
    
    # Create placeholder_image.png if missing
    placeholder_path = os.path.join(ASSETS_DIR, "placeholder_image.png")
    if not os.path.exists(placeholder_path) or os.path.getsize(placeholder_path) == 0:
        create_image_placeholder(placeholder_path)

def create_logo_placeholder(path: str):
    """Create a simple logo placeholder"""
    try:
        # Create 200x200 image with gradient
        img = Image.new('RGB', (200, 200), color='#1f77b4')
        draw = ImageDraw.Draw(img)
        
        # Draw simple "BS" text
        try:
            # Try to use default font
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            font = ImageFont.load_default()
        
        # Draw text in center
        text = "BS"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((200 - text_width) // 2, (200 - text_height) // 2)
        draw.text(position, text, fill='white', font=font)
        
        # Save
        img.save(path, 'PNG')
        print(f"✓ Created logo placeholder: {path}")
    except Exception as e:
        print(f"⚠ Failed to create logo placeholder: {e}")

def create_image_placeholder(path: str):
    """Create a simple image placeholder"""
    try:
        # Create 400x300 image
        img = Image.new('RGB', (400, 300), color='#cccccc')
        draw = ImageDraw.Draw(img)
        
        # Draw border
        draw.rectangle([10, 10, 390, 290], outline='#666666', width=3)
        
        # Draw text
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        text = "Image Preview"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((400 - text_width) // 2, (300 - text_height) // 2)
        draw.text(position, text, fill='#666666', font=font)
        
        # Save
        img.save(path, 'PNG')
        print(f"✓ Created image placeholder: {path}")
    except Exception as e:
        print(f"⚠ Failed to create image placeholder: {e}")

# Auto-run on import
if __name__ != "__main__":
    try:
        ensure_assets_exist()
    except Exception as e:
        print(f"⚠ Asset generation failed: {e}")
