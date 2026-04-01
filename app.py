from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from predict_multiple import CaptionGenerator
import base64
from PIL import Image
import io
import glob

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SAMPLE_FOLDER'] = 'static/samples'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SAMPLE_FOLDER'], exist_ok=True)

# Initialize caption generator (lazy loading)
caption_generator = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_generator():
    """Lazy load the caption generator"""
    global caption_generator
    if caption_generator is None:
        try:
            caption_generator = CaptionGenerator()
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    return caption_generator

@app.route('/')
def index():
    # Get sample images
    sample_images = []
    sample_dir = app.config['SAMPLE_FOLDER']
    
    if os.path.exists(sample_dir):
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            sample_images.extend([
                os.path.basename(f) for f in glob.glob(os.path.join(sample_dir, ext))
            ])
    
    return render_template('index.html', sample_images=sample_images)

@app.route('/generate', methods=['POST'])
def generate_captions():
    """Generate captions for uploaded or sample image"""
    filepath = None
    
    # Check if it's a sample image
    if 'sample_image' in request.form:
        sample_name = request.form['sample_image']
        filepath = os.path.join(app.config['SAMPLE_FOLDER'], sample_name)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Sample image not found'}), 400
    
    # Check if it's an uploaded image
    elif 'image' in request.files:
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
    
    else:
        return jsonify({'error': 'No image provided'}), 400
    
    try:
        
        # Get number of captions to generate
        num_captions = int(request.form.get('num_captions', 5))
        num_captions = max(1, min(num_captions, 10))  # Limit between 1-10
        
        # Generate captions
        generator = get_generator()
        if generator is None:
            return jsonify({'error': 'Model not loaded. Please train the model first.'}), 500
        
        captions = generator.generate_multiple_captions(filepath, num_captions=num_captions)
        
        # Get image as base64 for display
        with open(filepath, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'captions': captions,
            'image': f"data:image/jpeg;base64,{img_data}",
            'filename': os.path.basename(filepath)
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    generator = get_generator()
    model_loaded = generator is not None
    
    return jsonify({
        'status': 'healthy',
        'model_loaded': model_loaded
    })

if __name__ == '__main__':
    print("Starting Image Caption Generator Web App...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
