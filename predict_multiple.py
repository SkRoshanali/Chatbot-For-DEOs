import numpy as np
import tensorflow as tf
from PIL import Image
from coco_data_loader import COCODataLoader
import os

class CaptionGenerator:
    def __init__(self, encoder_path='models/encoder_model.h5', 
                 model_path='models/caption_model_best.h5',
                 vocab_path='models/vocabulary.pkl'):
        """Initialize caption generator"""
        print("Loading models...")
        self.encoder = tf.keras.models.load_model(encoder_path)
        self.model = tf.keras.models.load_model(model_path)
        
        # Load vocabulary
        self.data_loader = COCODataLoader('', '', max_length=40)
        self.data_loader.load_vocabulary(vocab_path)
        
        print("Models loaded successfully!")
    
    def preprocess_image(self, image_path):
        """Preprocess image for model"""
        img = Image.open(image_path).convert('RGB')
        img = img.resize((299, 299))
        img = np.array(img) / 255.0
        return img
    
    def generate_caption_beam_search(self, image_path, beam_width=5, max_length=40):
        """Generate caption using beam search for better quality"""
        # Extract features
        img = self.preprocess_image(image_path)
        features = self.encoder.predict(np.expand_dims(img, axis=0), verbose=0)
        
        # Initialize beam
        start_token = self.data_loader.word_to_idx['<start>']
        end_token = self.data_loader.word_to_idx['<end>']
        
        # Beam: list of (sequence, score)
        beam = [([start_token], 0.0)]
        
        for _ in range(max_length):
            candidates = []
            
            for sequence, score in beam:
                if sequence[-1] == end_token:
                    candidates.append((sequence, score))
                    continue
                
                # Prepare input
                padded_seq = tf.keras.preprocessing.sequence.pad_sequences(
                    [sequence], maxlen=max_length, padding='post'
                )
                
                # Predict next word
                prediction = self.model.predict([features, padded_seq], verbose=0)
                
                # Get top k predictions
                top_indices = np.argsort(prediction[0])[-beam_width:]
                
                for idx in top_indices:
                    new_sequence = sequence + [idx]
                    new_score = score - np.log(prediction[0][idx] + 1e-10)
                    candidates.append((new_sequence, new_score))
            
            # Select top beam_width candidates
            beam = sorted(candidates, key=lambda x: x[1])[:beam_width]
            
            # Check if all beams ended
            if all(seq[-1] == end_token for seq, _ in beam):
                break
        
        # Return best sequence
        best_sequence = beam[0][0]
        caption = self.data_loader.decode_caption(best_sequence)
        return caption
    
    def generate_multiple_captions(self, image_path, num_captions=5, temperature=0.7):
        """Generate multiple diverse captions using sampling"""
        captions = []
        
        # Extract features once
        img = self.preprocess_image(image_path)
        features = self.encoder.predict(np.expand_dims(img, axis=0), verbose=0)
        
        start_token = self.data_loader.word_to_idx['<start>']
        end_token = self.data_loader.word_to_idx['<end>']
        max_length = self.data_loader.max_length
        
        for i in range(num_captions):
            sequence = [start_token]
            
            for _ in range(max_length):
                padded_seq = tf.keras.preprocessing.sequence.pad_sequences(
                    [sequence], maxlen=max_length, padding='post'
                )
                
                prediction = self.model.predict([features, padded_seq], verbose=0)[0]
                
                # Apply temperature for diversity
                if i == 0:
                    # First caption: greedy (most likely)
                    predicted_idx = np.argmax(prediction)
                else:
                    # Other captions: sample with temperature
                    prediction = np.log(prediction + 1e-10) / temperature
                    exp_preds = np.exp(prediction)
                    prediction = exp_preds / np.sum(exp_preds)
                    predicted_idx = np.random.choice(len(prediction), p=prediction)
                
                if predicted_idx == end_token:
                    break
                
                sequence.append(predicted_idx)
            
            caption = self.data_loader.decode_caption(sequence)
            if caption and caption not in captions:
                captions.append(caption)
        
        return captions

def generate_captions_for_image(image_path, num_captions=5):
    """Generate multiple captions for an image"""
    generator = CaptionGenerator()
    
    print(f"\nGenerating {num_captions} captions for: {image_path}")
    print("-" * 60)
    
    captions = generator.generate_multiple_captions(image_path, num_captions=num_captions)
    
    for i, caption in enumerate(captions, 1):
        print(f"{i}. {caption}")
    
    return captions

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate multiple captions for an image')
    parser.add_argument('image_path', type=str, help='Path to image file')
    parser.add_argument('--num_captions', type=int, default=5, help='Number of captions to generate')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file not found: {args.image_path}")
    else:
        generate_captions_for_image(args.image_path, args.num_captions)
