import numpy as np
import tensorflow as tf
from model import ImageCaptionModel
from data_loader import DataLoader

def train_model(image_paths, captions, epochs=20, batch_size=32):
    """Train the image caption model"""
    # Initialize data loader
    data_loader = DataLoader(max_length=40)
    vocab_size = data_loader.build_vocabulary(captions)
    
    print(f"Vocabulary size: {vocab_size}")
    
    # Build model
    caption_model = ImageCaptionModel(vocab_size, data_loader.max_length)
    encoder = caption_model.build_encoder()
    model = caption_model.build_model()
    
    # Compile model
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("Model built successfully")
    print(f"Training on {len(image_paths)} images")
    
    # Extract image features
    print("Extracting image features...")
    image_features = []
    for img_path in image_paths:
        img = data_loader.preprocess_image(img_path)
        features = encoder.predict(np.expand_dims(img, axis=0), verbose=0)
        image_features.append(features[0])
    
    image_features = np.array(image_features)
    
    # Prepare training data
    X_images, X_captions, y = [], [], []
    
    for i, caption in enumerate(captions):
        encoded = data_loader.encode_caption(caption)
        for j in range(1, len(encoded)):
            X_images.append(image_features[i])
            X_captions.append(encoded[:j])
            y.append(encoded[j])
    
    X_images = np.array(X_images)
    X_captions = tf.keras.preprocessing.sequence.pad_sequences(X_captions, maxlen=data_loader.max_length, padding='post')
    y = np.array(y)
    
    print(f"Training samples: {len(X_images)}")
    
    # Train model
    history = model.fit(
        [X_images, X_captions],
        y,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.2,
        verbose=1
    )
    
    # Save model and vocabulary
    model.save('caption_model.h5')
    encoder.save('encoder_model.h5')
    np.save('word_to_idx.npy', data_loader.word_to_idx)
    np.save('idx_to_word.npy', data_loader.idx_to_word)
    
    print("Training complete. Models saved.")
    return model, encoder, data_loader

if __name__ == "__main__":
    # Example usage
    sample_images = ['image1.jpg', 'image2.jpg']
    sample_captions = ['a dog playing in the park', 'a cat sitting on a chair']
    
    train_model(sample_images, sample_captions, epochs=10)
