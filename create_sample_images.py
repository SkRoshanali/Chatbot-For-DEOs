"""
Create sample images locally without downloading
"""
from PIL import Image, ImageDraw, ImageFont
import os
import random

def create_sample_images():
    """Generate sample images locally"""
    print("Creating sample images locally...\n")
    
    os.makedirs('sample_images', exist_ok=True)
    
    samples = [
        ('Red Square', (220, 20, 60), 'red_square.jpg'),
        ('Blue Circle', (30, 144, 255), 'blue_circle.jpg'),
        ('Green Triangle', (50, 205, 50), 'green_triangle.jpg'),
        ('Yellow Star', (255, 215, 0), 'yellow_star.jpg'),
        ('Purple Gradient', (147, 112, 219), 'purple_gradient.jpg'),
    ]
    
    for name, color, filename in samples:
        filepath = os.path.join('sample_images', filename)
        
        # Create image
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw shape
        if 'square' in filename.lower():
            draw.rectangle([200, 150, 600, 450], fill=color, outline='black', width=3)
        elif 'circle' in filename.lower():
            draw.ellipse([200, 150, 600, 450], fill=color, outline='black', width=3)
        elif 'triangle' in filename.lower():
            draw.polygon([400, 150, 200, 450, 600, 450], fill=color, outline='black')
        elif 'star' in filename.lower():
            # Simple star shape
            points = [400, 150, 450, 300, 600, 300, 480, 400, 520, 550, 400, 450, 280, 550, 320, 400, 200, 300, 350, 300]
            draw.polygon(points, fill=color, outline='black')
        else:
            # Gradient effect
            for i in range(600):
                shade = tuple(max(0, c - i//3) for c in color)
                draw.line([(0, i), (800, i)], fill=shade)
        
        # Add text
        try:
            draw.text((400, 500), name, fill='black', anchor='mm')
        except:
            pass
        
        img.save(filepath, 'JPEG')
        print(f"✓ Created {filename}")
    
    print(f"\nSample images created in 'sample_images/' folder")

if __name__ == "__main__":
    create_sample_images()
