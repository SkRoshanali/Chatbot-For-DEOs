import numpy as np
from PIL import Image
import tensorflow as tf

class DataLoader:
    def __init__(self, max_length=40):
        self.max_length = max_length
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.vocab_size = 0
        
    def preprocess_image(self, image_path):
        """Load and preprocess image for InceptionV3"""
        img = Image.open(image_path).convert('RGB')
        img = img.resize((299, 299))
        img = np.array(img) / 255.0
        return img
    
    def build_vocabulary(self, captions):
        """Build vocabulary from captions"""
        words = set()
        for caption in captions:
            words.update(caption.lower().split())
        
        self.word_to_idx = {word: idx + 1 for idx, word in enumerate(sorted(words))}
        self.word_to_idx['<start>'] = len(self.word_to_idx) + 1
        self.word_to_idx['<end>'] = len(self.word_to_idx) + 1
        self.word_to_idx['<pad>'] = 0
        
        self.idx_to_word = {idx: word for word, idx in self.word_to_idx.items()}
        self.vocab_size = len(self.word_to_idx)
        
        return self.vocab_size
    
    def encode_caption(self, caption):
        """Convert caption to sequence of indices"""
        tokens = ['<start>'] + caption.lower().split() + ['<end>']
        sequence = [self.word_to_idx.get(word, 0) for word in tokens]
        
        # Pad sequence
        if len(sequence) < self.max_length:
            sequence += [0] * (self.max_length - len(sequence))
        else:
            sequence = sequence[:self.max_length]
        
        return np.array(sequence)
    
    def decode_caption(self, sequence):
        """Convert sequence of indices back to caption"""
        words = [self.idx_to_word.get(idx, '') for idx in sequence if idx != 0]
        caption = ' '.join(words).replace('<start>', '').replace('<end>', '').strip()
        return caption
