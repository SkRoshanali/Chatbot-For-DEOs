"""
Quick start script - Downloads sample images and trains a small model for demo
"""
import os
import requests
from PIL import Image
import io

def download_sample_images():
    """Download sample images for testing"""
    print("Downloading sample images...")
    
    os.makedirs('sample_images', exist_ok=True)
    
    # Sample image URLs (free to use)
    sample_urls = [
        ('https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=800', 'dog.jpg'),
        ('https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800', 'cat.jpg'),
        ('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800', 'mountain.jpg'),
        ('https://images.unsplash.com/photo-1551963831-b3b1ca40c98e?w=800', 'breakfast.jpg'),
        ('https://images.unsplash.com/photo-1511919884226-fd3cad34687c?w=800', 'beach.jpg'),
    ]
    
    for url, filename in sample_urls:
        filepath = os.path.join('sample_images', filename)
        if os.path.exists(filepath):
            print(f"✓ {filename} already exists")
            continue
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                img = img.convert('RGB')
                img.save(filepath)
                print(f"✓ Downloaded {filename}")
            else:
                print(f"✗ Failed to download {filename}")
        except Exception as e:
            print(f"✗ Error downloading {filename}: {e}")
    
    print(f"\nSample images saved in 'sample_images/' folder")

def create_demo_data():
    """Create minimal training data for quick demo"""
    print("\nCreating demo training data...")
    
    # Create a small dataset with sample captions
    demo_data = {
        'dog.jpg': [
            'a dog sitting on grass',
            'a brown dog outdoors',
            'a pet dog in nature'
        ],
        'cat.jpg': [
            'a cat looking at camera',
            'an orange cat indoors',
            'a cute cat portrait'
        ],
        'mountain.jpg': [
            'mountains under blue sky',
            'scenic mountain landscape',
            'mountain peaks in nature'
        ],
        'breakfast.jpg': [
            'breakfast food on table',
            'delicious meal with fruits',
            'healthy breakfast plate'
        ],
        'beach.jpg': [
            'beach with ocean waves',
            'sandy beach and blue water',
            'tropical beach scene'
        ]
    }
    
    return demo_data

def main():
    print("=" * 60)
    print("Image Caption Generator - Quick Start")
    print("=" * 60)
    print()
    
    # Step 1: Install dependencies
    print("Step 1: Checking dependencies...")
    try:
        import tensorflow
        import flask
        import numpy
        from PIL import Image
        print("✓ All dependencies installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease run: pip install -r requirements.txt")
        return
    
    # Step 2: Download sample images
    print("\nStep 2: Setting up sample images...")
    download_sample_images()
    
    # Step 3: Create directories
    print("\nStep 3: Creating directories...")
    os.makedirs('models', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    print("✓ Directories created")
    
    # Step 4: Instructions
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("\nOption A - Quick Demo (No training needed):")
    print("  1. Run: python demo_pretrained.py")
    print("     (Uses a simple rule-based caption generator)")
    print()
    print("Option B - Full Training:")
    print("  1. Download COCO dataset: python download_coco.py")
    print("  2. Train model: python train_coco.py --images 1000 --epochs 10")
    print("  3. Start web app: python app.py")
    print()
    print("Option C - Test with sample images:")
    print("  Sample images are in 'sample_images/' folder")
    print("  You can use these for testing once model is trained")
    print()

if __name__ == "__main__":
    main()
