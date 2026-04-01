import os
import requests
import zipfile
from tqdm import tqdm

def download_file(url, filename):
    """Download file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress_bar.update(size)

def download_coco_dataset():
    """Download MS COCO dataset"""
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/images', exist_ok=True)
    os.makedirs('data/annotations', exist_ok=True)
    
    # URLs for COCO 2017 dataset
    urls = {
        'train_images': 'http://images.cocodataset.org/zips/train2017.zip',
        'val_images': 'http://images.cocodataset.org/zips/val2017.zip',
        'annotations': 'http://images.cocodataset.org/annotations/annotations_trainval2017.zip'
    }
    
    print("Downloading MS COCO Dataset...")
    print("Note: This will download ~25GB of data. It may take a while.")
    
    # Download annotations (smaller, download first)
    print("\n1. Downloading annotations...")
    if not os.path.exists('data/annotations/captions_train2017.json'):
        download_file(urls['annotations'], 'data/annotations.zip')
        print("Extracting annotations...")
        with zipfile.ZipFile('data/annotations.zip', 'r') as zip_ref:
            zip_ref.extractall('data/')
        os.remove('data/annotations.zip')
    else:
        print("Annotations already exist. Skipping.")
    
    # Download validation images (smaller dataset for faster training)
    print("\n2. Downloading validation images...")
    if not os.path.exists('data/images/val2017'):
        download_file(urls['val_images'], 'data/val2017.zip')
        print("Extracting validation images...")
        with zipfile.ZipFile('data/val2017.zip', 'r') as zip_ref:
            zip_ref.extractall('data/images/')
        os.remove('data/val2017.zip')
    else:
        print("Validation images already exist. Skipping.")
    
    # Optionally download training images (much larger)
    download_train = input("\nDownload training images? (20GB) [y/N]: ").lower() == 'y'
    if download_train:
        print("\n3. Downloading training images...")
        if not os.path.exists('data/images/train2017'):
            download_file(urls['train_images'], 'data/train2017.zip')
            print("Extracting training images...")
            with zipfile.ZipFile('data/train2017.zip', 'r') as zip_ref:
                zip_ref.extractall('data/images/')
            os.remove('data/train2017.zip')
        else:
            print("Training images already exist. Skipping.")
    
    print("\nDataset download complete!")
    print("Images location: data/images/")
    print("Annotations location: data/annotations/")

if __name__ == "__main__":
    download_coco_dataset()
