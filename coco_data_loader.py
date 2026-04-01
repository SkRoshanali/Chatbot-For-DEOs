import json
import os
import numpy as np
from PIL import Image
import tensorflow as tf
from collections import defaultdict
import pickle

class COCODataLoader:
    def __init__(self, annotation_file, image_dir, max_length=40, vocab_size=10000):
        self.annotation_file = annotation_file
        self.image_dir = image_dir
        self.max_length = max_length
        self.target_vocab_size = vocab_size
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.vocab_size = 0
        self.image_to_captions = defaultdict(list)
        
    def load_annotations(self):
        """Load COCO annotations"""
        print("Loading COCO annotations...")
        with open(self.annotation_file, 'r') as f:
            data = json.load(f)
        
        # Map image IDs to filenames
        image_id_to_filename = {}
        for img in data['images']:
            image_id_to_filename[img['id']] = img['file_name']
        
        # Map images to captions
        for ann in data['annotations']:
            image_id = ann['image_id']
            caption = ann['caption']
            filename = image_id_to_filename.get(image_id)
            if filename:
                self.image_to_captions[filename].append(caption)
        
        print(f"Loaded {len(self.image_to_captions)} images with captions")
        return self.image_to_captions
    
    def build_vocabulary(self, captions_list):
        """Build vocabulary from captions with frequency-based filtering"""
        print("Building vocabulary...")
        word_freq = defaultdict(int)
        
        for captions in captions_list:
            for caption in captions:
                for word in caption.lower().split():
                    word_freq[word] += 1
        
        # Sort by frequency and take top words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_words = [word for word, freq in sorted_words[:self.target_vocab_size - 3]]
        
        # Build vocabulary
        self.word_to_idx = {word: idx + 1 for idx, word in enumerate(top_words)}
        self.word_to_idx['<pad>'] = 0
        self.word_to_idx['<start>'] = len(self.word_to_idx)
        self.word_to_idx['<end>'] = len(self.word_to_idx)
        self.word_to_idx['<unk>'] = len(self.word_to_idx)
        
        self.idx_to_word = {idx: word for word, idx in self.word_to_idx.items()}
        self.vocab_size = len(self.word_to_idx)
        
        print(f"Vocabulary size: {self.vocab_size}")
        return self.vocab_size
    
    def preprocess_image(self, image_path):
        """Load and preprocess image for InceptionV3"""
        img = Image.open(image_path).convert('RGB')
        img = img.resize((299, 299))
        img = np.array(img) / 255.0
        return img
    
    def encode_caption(self, caption):
        """Convert caption to sequence of indices"""
        tokens = ['<start>'] + caption.lower().split() + ['<end>']
        sequence = [self.word_to_idx.get(word, self.word_to_idx['<unk>']) for word in tokens]
        return sequence
    
    def decode_caption(self, sequence):
        """Convert sequence of indices back to caption"""
        words = []
        for idx in sequence:
            if idx == self.word_to_idx['<end>'] or idx == 0:
                break
            if idx != self.word_to_idx['<start>']:
                words.append(self.idx_to_word.get(idx, '<unk>'))
        return ' '.join(words)
    
    def get_train_data(self, num_images=None):
        """Get training data"""
        image_paths = []
        all_captions = []
        
        items = list(self.image_to_captions.items())
        if num_images:
            items = items[:num_images]
        
        for filename, captions in items:
            image_path = os.path.join(self.image_dir, filename)
            if os.path.exists(image_path):
                image_paths.append(image_path)
                all_captions.append(captions)
        
        return image_paths, all_captions
    
    def save_vocabulary(self, filepath='data/vocabulary.pkl'):
        """Save vocabulary to file"""
        vocab_data = {
            'word_to_idx': self.word_to_idx,
            'idx_to_word': self.idx_to_word,
            'vocab_size': self.vocab_size,
            'max_length': self.max_length
        }
        with open(filepath, 'wb') as f:
            pickle.dump(vocab_data, f)
        print(f"Vocabulary saved to {filepath}")
    
    def load_vocabulary(self, filepath='data/vocabulary.pkl'):
        """Load vocabulary from file"""
        with open(filepath, 'rb') as f:
            vocab_data = pickle.load(f)
        self.word_to_idx = vocab_data['word_to_idx']
        self.idx_to_word = vocab_data['idx_to_word']
        self.vocab_size = vocab_data['vocab_size']
        self.max_length = vocab_data['max_length']
        print(f"Vocabulary loaded from {filepath}")
