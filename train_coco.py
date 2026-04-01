import numpy as np
import tensorflow as tf
from coco_data_loader import COCODataLoader
from model import ImageCaptionModel
import os
from tqdm import tqdm

def extract_features(encoder, image_paths, batch_size=32):
    """Extract features from images in batches"""
    print("Extracting image features...")
    features = []
    
    for i in tqdm(range(0, len(image_paths), batch_size)):
        batch_paths = image_paths[i:i+batch_size]
        batch_images = []
        
        for img_path in batch_paths:
            try:
                img = tf.keras.preprocessing.image.load_img(img_path, target_size=(299, 299))
                img = tf.keras.preprocessing.image.img_to_array(img)
                img = img / 255.0
                batch_images.append(img)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                batch_images.append(np.zeros((299, 299, 3)))
        
        batch_images = np.array(batch_images)
        batch_features = encoder.predict(batch_images, verbose=0)
        features.extend(batch_features)
    
    return np.array(features)

def prepare_training_data(image_features, all_captions, data_loader):
    """Prepare training sequences"""
    print("Preparing training sequences...")
    X_images, X_captions, y = [], [], []
    
    for i, captions in enumerate(tqdm(all_captions)):
        for caption in captions:
            encoded = data_loader.encode_caption(caption)
            for j in range(1, len(encoded)):
                X_images.append(image_features[i])
                X_captions.append(encoded[:j])
                y.append(encoded[j])
    
    X_images = np.array(X_images)
    X_captions = tf.keras.preprocessing.sequence.pad_sequences(
        X_captions, maxlen=data_loader.max_length, padding='post'
    )
    y = np.array(y)
    
    return X_images, X_captions, y

def train_model(num_images=5000, epochs=20, batch_size=64):
    """Train the image caption model on COCO dataset"""
    
    # Initialize data loader
    annotation_file = 'data/annotations/captions_val2017.json'
    image_dir = 'data/images/val2017'
    
    if not os.path.exists(annotation_file):
        print("Error: COCO dataset not found. Please run download_coco.py first.")
        return
    
    data_loader = COCODataLoader(annotation_file, image_dir, max_length=40, vocab_size=10000)
    
    # Load annotations
    data_loader.load_annotations()
    
    # Get training data
    image_paths, all_captions = data_loader.get_train_data(num_images=num_images)
    print(f"Using {len(image_paths)} images for training")
    
    # Build vocabulary
    vocab_size = data_loader.build_vocabulary(all_captions)
    
    # Save vocabulary
    os.makedirs('models', exist_ok=True)
    data_loader.save_vocabulary('models/vocabulary.pkl')
    
    # Build model
    print("Building model...")
    caption_model = ImageCaptionModel(vocab_size, data_loader.max_length)
    encoder = caption_model.build_encoder()
    model = caption_model.build_model()
    
    # Compile model
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print(model.summary())
    
    # Extract image features
    image_features = extract_features(encoder, image_paths, batch_size=32)
    
    # Prepare training data
    X_images, X_captions, y = prepare_training_data(image_features, all_captions, data_loader)
    
    print(f"Training samples: {len(X_images)}")
    print(f"Image features shape: {X_images.shape}")
    print(f"Caption sequences shape: {X_captions.shape}")
    print(f"Target shape: {y.shape}")
    
    # Callbacks
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        'models/caption_model_best.h5',
        monitor='val_loss',
        save_best_only=True,
        verbose=1
    )
    
    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True
    )
    
    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=0.00001,
        verbose=1
    )
    
    # Train model
    print("\nStarting training...")
    history = model.fit(
        [X_images, X_captions],
        y,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.2,
        callbacks=[checkpoint, early_stop, reduce_lr],
        verbose=1
    )
    
    # Save final model
    model.save('models/caption_model_final.h5')
    encoder.save('models/encoder_model.h5')
    
    print("\nTraining complete!")
    print("Models saved in 'models/' directory")
    
    return model, encoder, data_loader, history

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train Image Caption Model on COCO')
    parser.add_argument('--images', type=int, default=5000, help='Number of images to use')
    parser.add_argument('--epochs', type=int, default=20, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=64, help='Batch size')
    
    args = parser.parse_args()
    
    train_model(num_images=args.images, epochs=args.epochs, batch_size=args.batch_size)
