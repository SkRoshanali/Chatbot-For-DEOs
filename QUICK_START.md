# Quick Start Guide - Image Caption Generator

## ✅ Application is Running!

Your Image Caption Generator is now live at:
- **http://localhost:5000**
- **http://127.0.0.1:5000**

## 📸 Sample Images Available

Sample images have been created in the `sample_images/` folder:
- red_square.jpg
- blue_circle.jpg
- green_triangle.jpg
- yellow_star.jpg
- purple_gradient.jpg

## 🚀 How to Use

### Option 1: Web Interface (Currently Running)
1. Open http://localhost:5000 in your browser
2. Click the upload box or drag & drop an image
3. Select number of captions (1-10)
4. Click "Generate Captions"
5. View the generated captions!

### Option 2: Use Your Own Images
- Upload any image from your computer (PNG, JPG, JPEG, GIF, BMP)
- Maximum file size: 16MB
- The app will analyze and generate captions

### Option 3: Use Sample Images
- Navigate to `sample_images/` folder
- Upload any of the pre-created images to test

## 🎯 Current Demo Mode

**Offline Demo** - No internet or training required!
- Uses image analysis (colors, brightness, composition)
- Generates descriptive captions instantly
- Perfect for testing the interface

## 🔥 Upgrade to Full AI Model

For AI-powered captions with deep learning:

### Step 1: Install Dependencies
```bash
pip install tensorflow requests tqdm
```

### Step 2: Download COCO Dataset
```bash
python download_coco.py
```

### Step 3: Train the Model
```bash
python train_coco.py --images 1000 --epochs 10
```

### Step 4: Run Full App
```bash
python app.py
```

## 📁 Project Structure

```
├── offline_demo.py          ← Currently running (simple demo)
├── app.py                   ← Full AI version (requires training)
├── sample_images/           ← Test images
├── templates/index.html     ← Web interface
├── static/
│   ├── style.css           ← Styling
│   ├── script.js           ← Frontend logic
│   └── uploads/            ← Uploaded images
└── models/                  ← Trained models (after training)
```

## 🛑 Stop the Server

Press `Ctrl+C` in the terminal to stop the server

## 💡 Tips

- The current demo generates captions based on image properties
- For real AI captions, train the full model with COCO dataset
- Sample images are great for testing the interface
- You can upload your own photos to see how it works!

## 🎨 Features

✓ Drag & drop image upload
✓ Generate 5+ captions per image
✓ Beautiful responsive web interface
✓ Real-time caption generation
✓ Support for multiple image formats
✓ No internet required (offline mode)

Enjoy testing your Image Caption Generator! 🎉
