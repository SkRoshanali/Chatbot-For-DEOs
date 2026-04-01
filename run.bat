@echo off
echo ========================================
echo Image Caption Generator - Setup Script
echo ========================================
echo.

echo Step 1: Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies!
    pause
    exit /b 1
)
echo.

echo Step 2: Creating directories...
if not exist "data" mkdir data
if not exist "models" mkdir models
if not exist "static\uploads" mkdir static\uploads
echo.

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run: python download_coco.py (to download dataset)
echo 2. Run: python train_coco.py (to train the model)
echo 3. Run: python app.py (to start web interface)
echo.
pause
