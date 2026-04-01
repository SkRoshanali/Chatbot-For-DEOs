import tensorflow as tf
from tensorflow.keras.applications import InceptionV3
from tensorflow.keras.layers import Dense, LSTM, Embedding, Dropout, Add, Input
from tensorflow.keras.models import Model

class ImageCaptionModel:
    def __init__(self, vocab_size, max_length, embedding_dim=256, units=512):
        self.vocab_size = vocab_size
        self.max_length = max_length
        self.embedding_dim = embedding_dim
        self.units = units
        self.model = None
        self.encoder = None
        
    def build_encoder(self):
        """Build image feature extractor using InceptionV3"""
        base_model = InceptionV3(weights='imagenet', include_top=False)
        base_model.trainable = False
        
        image_input = Input(shape=(299, 299, 3))
        x = base_model(image_input)
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        x = Dense(self.embedding_dim, activation='relu')(x)
        
        self.encoder = Model(inputs=image_input, outputs=x)
        return self.encoder
    
    def build_model(self):
        """Build complete caption generation model"""
        # Image feature input
        image_input = Input(shape=(self.embedding_dim,))
        image_features = Dropout(0.5)(image_input)
        image_features = Dense(self.units, activation='relu')(image_features)
        
        # Caption sequence input
        caption_input = Input(shape=(self.max_length,))
        caption_embedding = Embedding(self.vocab_size, self.embedding_dim, mask_zero=True)(caption_input)
        caption_embedding = Dropout(0.5)(caption_embedding)
        caption_lstm = LSTM(self.units)(caption_embedding)
        
        # Combine image and caption features
        decoder = Add()([image_features, caption_lstm])
        decoder = Dense(self.units, activation='relu')(decoder)
        output = Dense(self.vocab_size, activation='softmax')(decoder)
        
        self.model = Model(inputs=[image_input, caption_input], outputs=output)
        return self.model
