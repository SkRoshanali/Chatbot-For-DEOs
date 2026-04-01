"""
Simple demo using pre-trained InceptionV3 - No training required!
"""
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.inception_v3 import InceptionV3, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image as keras_image
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load model
print("Loading InceptionV3 model...")
model = InceptionV3(weights='imagenet')
print("Model loaded!")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_captions_from_classification(image_path, num_captions=5):
    """Generate captions using image classification"""
    # Load and preprocess
    img = keras_image.load_img(image_path, target_size=(299, 299))
    img_array = keras_image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    
    # Predict
    predictions = model.predict(img_array, verbose=0)
    decoded = decode_predictions(predictions, top=10)[0]
    
    # Generate captions
    captions = []
    objects = [pred[1].replace('_', ' ') for pred in decoded[:5]]
    confidence = decoded[0][2] * 100
    
    templates = [
        f"a photo of a {objects[0]}",
        f"an image showing a {objects[0]}",
        f"a {objects[0]} with {confidence:.1f}% confidence",
        f"this picture contains a {objects[0]}",
        f"a scene with a {objects[0]}"
    ]
    
    if len(objects) > 1:
        templates.append(f"detected: {objects[0]} and {objects[1]}")
    
    if len(objects) > 2:
        templates.append(f"objects in image: {', '.join(objects[:3])}")
    
    return templates[:num_captions]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        num_captions = int(request.form.get('num_captions', 5))
        captions = generate_captions_from_classification(filepath, num_captions)
        
        with open(filepath, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'captions': captions,
            'image': f"data:image/jpeg;base64,{img_data}",
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'model_loaded': True})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Image Caption Generator - Simple Demo")
    print("="*60)
    print("\nUsing pre-trained InceptionV3 for quick testing")
    print("No training required!")
    print("\nOpen your browser and go to:")
    print("  http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
