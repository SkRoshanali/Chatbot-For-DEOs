"""
Download sample images for testing
"""
import os
import requests
from PIL import Image
import io

def download_sample_images():
    """Download sample images from public sources"""
    os.makedirs('static/samples', exist_ok=True)
    
    # Sample images from Unsplash (free to use)
    sample_urls = {
        'dog.jpg': 'https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=800',
        'cat.jpg': 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800',
        'beach.jpg': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800',
        'city.jpg': 'https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=800',
        'food.jpg': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800',
        'nature.jpg': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800',
    }
    
    print("Downloading sample images...")
    
    for filename, url in sample_urls.items():
        filepath = os.path.join('static/samples', filename)
        
        if os.path.exists(filepath):
            print(f"✓ {filename} already exists")
            continue
        
        try:
            print(f"Downloading {filename}...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            img = Image.open(io.BytesIO(response.content))
            img = img.convert('RGB')
            img.save(filepath, 'JPEG', quality=85)
            
            print(f"✓ {filename} downloaded")
        except Exception as e:
            print(f"✗ Failed to download {filename}: {e}")
    
    print("\nSample images ready in static/samples/")

if __name__ == "__main__":
    download_sample_images()
