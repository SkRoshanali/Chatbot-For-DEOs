import requests
from PIL import Image
import io
import os

def download_sample_images():
    """Download free sample images"""
    print("Downloading sample images...\n")
    
    # Using placeholder images (these are free to use)
    samples = [
        ('https://picsum.photos/800/600?random=1', 'sample1.jpg'),
        ('https://picsum.photos/800/600?random=2', 'sample2.jpg'),
        ('https://picsum.photos/800/600?random=3', 'sample3.jpg'),
        ('https://picsum.photos/800/600?random=4', 'sample4.jpg'),
        ('https://picsum.photos/800/600?random=5', 'sample5.jpg'),
    ]
    
    os.makedirs('sample_images', exist_ok=True)
    
    for url, filename in samples:
        filepath = os.path.join('sample_images', filename)
        try:
            print(f"Downloading {filename}...", end=' ')
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                img = img.convert('RGB')
                img.save(filepath, 'JPEG')
                print("✓")
            else:
                print("✗")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print(f"\nSample images saved in 'sample_images/' folder")
    print("You can use these images to test the application!")

if __name__ == "__main__":
    download_sample_images()
