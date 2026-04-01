import numpy as np
from predict_multiple import CaptionGenerator
from coco_data_loader import COCODataLoader
import os
from tqdm import tqdm

def calculate_bleu(reference, candidate):
    """Simple BLEU-1 score calculation"""
    ref_words = set(reference.lower().split())
    cand_words = candidate.lower().split()
    
    if len(cand_words) == 0:
        return 0.0
    
    matches = sum(1 for word in cand_words if word in ref_words)
    return matches / len(cand_words)

def evaluate_model(num_samples=100):
    """Evaluate model on validation set"""
    print("Loading model and data...")
    
    # Load data
    data_loader = COCODataLoader(
        'data/annotations/captions_val2017.json',
        'data/images/val2017'
    )
    data_loader.load_annotations()
    
    # Get test samples
    image_paths, all_captions = data_loader.get_train_data(num_images=num_samples)
    
    # Load generator
    generator = CaptionGenerator()
    
    print(f"\nEvaluating on {len(image_paths)} images...")
    
    bleu_scores = []
    
    for i, (img_path, ref_captions) in enumerate(tqdm(zip(image_paths, all_captions))):
        try:
            # Generate caption
            generated = generator.generate_multiple_captions(img_path, num_captions=1)[0]
            
            # Calculate BLEU with all reference captions
            scores = [calculate_bleu(ref, generated) for ref in ref_captions]
            bleu_scores.append(max(scores))
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            continue
    
    avg_bleu = np.mean(bleu_scores)
    
    print(f"\n{'='*50}")
    print(f"Evaluation Results")
    print(f"{'='*50}")
    print(f"Samples evaluated: {len(bleu_scores)}")
    print(f"Average BLEU-1 score: {avg_bleu:.4f}")
    print(f"Min BLEU: {min(bleu_scores):.4f}")
    print(f"Max BLEU: {max(bleu_scores):.4f}")
    print(f"{'='*50}")
    
    return avg_bleu

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate caption model')
    parser.add_argument('--samples', type=int, default=100, help='Number of samples to evaluate')
    
    args = parser.parse_args()
    
    evaluate_model(num_samples=args.samples)
