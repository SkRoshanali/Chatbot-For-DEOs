"""
Demo script to test caption generation on sample images
"""
from predict_multiple import generate_captions_for_image
import os

def run_demo():
    """Run demo with sample images"""
    print("=" * 60)
    print("Image Caption Generator - Demo")
    print("=" * 60)
    
    # Check if models exist
    if not os.path.exists('models/caption_model_best.h5'):
        print("\nError: Model not found!")
        print("Please train the model first using: python train_coco.py")
        return
    
    # Get image path from user
    image_path = input("\nEnter path to image file: ").strip()
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return
    
    num_captions = input("Number of captions to generate (default 5): ").strip()
    num_captions = int(num_captions) if num_captions else 5
    
    # Generate captions
    try:
        captions = generate_captions_for_image(image_path, num_captions=num_captions)
        
        print("\n" + "=" * 60)
        print("Caption generation complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError generating captions: {e}")
        print("Make sure the model is trained and image path is correct.")

if __name__ == "__main__":
    run_demo()
