import numpy as np
import tensorflow as tf
from PIL import Image
from data_loader import DataLoader

def generate_caption(image_path, encoder_path='encoder_model.h5', model_path='caption_model.h5', max_length=40):
    """Generate caption for a given image"""
    # Load models
    encoder = tf.keras.models.load_model(encoder_path)
    model = tf.keras.models.load_model(model_path)
    
    # Load vocabulary
    word_to_idx = np.load('word_to_idx.npy', allow_pickle=True).item()
    idx_to_word = np.load('idx_to_word.npy', allow_pickle=True).item()
    
    # Preprocess image
    data_loader = DataLoader(max_length=max_length)
    img = data_loader.preprocess_image(image_path)
    
    # Extract features
    features = encoder.predict(np.expand_dims(img, axis=0), verbose=0)
    
    # Generate caption
    caption = ['<start>']
    for _ in range(max_length):
        sequence = [word_to_idx.get(word, 0) for word in caption]
        sequence = tf.keras.preprocessing.sequence.pad_sequences([sequence], maxlen=max_length, padding='post')
        
        prediction = model.predict([features, sequence], verbose=0)
        predicted_idx = np.argmax(prediction[0])
        predicted_word = idx_to_word.get(predicted_idx, '')
        
        if predicted_word == '<end>' or predicted_word == '':
            break
        
        caption.append(predicted_word)
    
    final_caption = ' '.join(caption[1:])
    return final_caption

if __name__ == "__main__":
    # Example usage
    image_path = 'test_image.jpg'
    caption = generate_caption(image_path)
    print(f"Generated caption: {caption}")
