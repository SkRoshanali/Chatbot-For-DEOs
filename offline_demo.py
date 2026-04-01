"""
Offline demo - No downloads, no training, works immediately!
Uses simple image analysis to generate captions
"""
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import os
import base64
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def analyze_image(image_path):
    """Analyze image properties to generate captions"""
    img = Image.open(image_path)
    img_array = np.array(img)
    
    # Get image properties
    width, height = img.size
    aspect_ratio = width / height
    
    # Analyze colors
    if len(img_array.shape) == 3:
        avg_color = img_array.mean(axis=(0, 1))
        r, g, b = avg_color[:3]
    else:
        r = g = b = img_array.mean()
    
    # Determine dominant color
    if r > g and r > b:
        dominant_color = "red"
    elif g > r and g > b:
        dominant_color = "green"
    elif b > r and b > g:
        dominant_color = "blue"
    elif r > 150 and g > 150 and b > 150:
        dominant_color = "bright"
    elif r < 100 and g < 100 and b < 100:
        dominant_color = "dark"
    else:
        dominant_color = "colorful"
    
    # Determine brightness
    brightness = (r + g + b) / 3
    if brightness > 180:
        brightness_desc = "bright"
    elif brightness > 100:
        brightness_desc = "well-lit"
    else:
        brightness_desc = "dark"
    
    # Determine orientation
    if aspect_ratio > 1.3:
        orientation = "landscape"
    elif aspect_ratio < 0.7:
        orientation = "portrait"
    else:
        orientation = "square"
    
    return {
        'dominant_color': dominant_color,
        'brightness': brightness_desc,
        'orientation': orientation,
        'size': f"{width}x{height}",
        'aspect_ratio': aspect_ratio
    }

def generate_captions(image_path, num_captions=5):
    """Generate captions based on image analysis"""
    props = analyze_image(image_path)
    
    captions = [
        f"a {props['brightness']} {props['orientation']} image",
        f"an image with {props['dominant_color']} tones",
        f"a {props['dominant_color']} colored photograph",
        f"a {props['brightness']} photo in {props['orientation']} format",
        f"an image showing {props['dominant_color']} and {props['brightness']} elements",
        f"a {props['orientation']} composition with {props['dominant_color']} hues",
        f"a photograph featuring {props['dominant_color']} colors",
    ]
    
    return captions[:num_captions]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
        captions = generate_captions(filepath, num_captions)
        
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
    print("Image Caption Generator - Offline Demo")
    print("="*60)
    print("\n✓ No downloads required!")
    print("✓ No training needed!")
    print("✓ Works immediately!")
    print("\nOpen your browser and go to:")
    print("  http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
