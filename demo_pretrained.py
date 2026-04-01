"""
Demo with pre-trained InceptionV3 for quick testing without full training
Uses image classification to generate descriptive captions
"""
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.inception_v3 import InceptionV3, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import os

class SimpleCaptionGenerator:
    def __init__(self):
        print("Loading InceptionV3 model...")
        self.model = InceptionV3(weights='imagenet')
        print("Model loaded!")
        
        # Caption templates
        self.templates = [
            "a photo of {objects}",
            "an image showing {objects}",
            "{objects} in the picture",
            "this image contains {objects}",
            "a scene with {objects}"
        ]
    
    def generate_captions(self, image_path, num_captions=5):
        """Generate captions using image classification"""
        # Load and preprocess image
        img = image.load_img(image_path, target_size=(299, 299))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        # Predict
        predictions = self.model.predict(img_array, verbose=0)
        decoded = decode_predictions(predictions, top=10)[0]
        
        # Generate captions
        captions = []
        
        # Get top objects
        objects = [pred[1].replace('_', ' ') for pred in decoded[:5]]
        
        # Generate diverse captions
        for i in range(min(num_captions, len(self.templates))):
            if i < len(objects):
                obj_list = ', '.join(objects[:i+1]) if i > 0 else objects[0]
                caption = self.templates[i].format(objects=obj_list)
                captions.append(caption)
        
        # Add more specific captions
        if len(captions) < num_captions:
            captions.append(f"a {objects[0]} with {decoded[0][2]*100:.1f}% confidence")
        
        if len(captions) < num_captions:
            captions.append(f"detected objects: {', '.join(objects[:3])}")
        
        return captions

def demo_with_samples():
    """Run demo with sample images"""
    print("=" * 60)
    print("Image Caption Generator - Quick Demo")
    print("(Using pre-trained InceptionV3 for classification-based captions)")
    print("=" * 60)
    print()
    
    generator = SimpleCaptionGenerator()
    
    # Check for sample images
    sample_dir = 'sample_images'
    if not os.path.exists(sample_dir):
        print(f"Sample images not found. Run: python quick_start.py")
        return
    
    images = [f for f in os.listdir(sample_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if not images:
        print("No images found in sample_images/")
        return
    
    print(f"Found {len(images)} sample images\n")
    
    for img_file in images:
        img_path = os.path.join(sample_dir, img_file)
        print(f"\n{'='*60}")
        print(f"Image: {img_file}")
        print(f"{'='*60}")
        
        try:
            captions = generator.generate_captions(img_path, num_captions=5)
            
            for i, caption in enumerate(captions, 1):
                print(f"{i}. {caption}")
        
        except Exception as e:
            print(f"Error processing {img_file}: {e}")
    
    print(f"\n{'='*60}")
    print("Demo complete!")
    print("Note: These are classification-based captions.")
    print("For better captions, train the full model with COCO dataset.")
    print(f"{'='*60}")

if __name__ == "__main__":
    demo_with_samples()
