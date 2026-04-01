const uploadBox = document.getElementById('uploadBox');
const imageInput = document.getElementById('imageInput');
const generateBtn = document.getElementById('generateBtn');
const numCaptions = document.getElementById('numCaptions');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const previewImage = document.getElementById('previewImage');
const captionsList = document.getElementById('captionsList');
const newImageBtn = document.getElementById('newImageBtn');
const retryBtn = document.getElementById('retryBtn');
const errorMessage = document.getElementById('errorMessage');

let selectedFile = null;

// Upload box click
uploadBox.addEventListener('click', () => {
    imageInput.click();
});

// File selection
imageInput.addEventListener('change', (e) => {
    handleFileSelect(e.target.files[0]);
});

// Drag and drop
uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.classList.add('dragover');
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.classList.remove('dragover');
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.classList.remove('dragover');
    handleFileSelect(e.dataTransfer.files[0]);
});

function handleFileSelect(file) {
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        showError('Please select a valid image file');
        return;
    }
    
    selectedFile = file;
    generateBtn.disabled = false;
    
    // Show preview in upload box
    const reader = new FileReader();
    reader.onload = (e) => {
        uploadBox.innerHTML = `
            <img src="${e.target.result}" style="max-width: 100%; max-height: 300px; border-radius: 10px;">
            <p style="margin-top: 15px; color: #667eea; font-weight: 600;">✓ Image selected</p>
        `;
    };
    reader.readAsDataURL(file);
}

// Generate captions
generateBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    hideAllSections();
    loadingSection.style.display = 'block';
    
    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('num_captions', numCaptions.value);
    
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        displayResults(data);
    } catch (error) {
        showError('Failed to generate captions. Please try again.');
    }
});

function displayResults(data) {
    hideAllSections();
    
    previewImage.src = data.image;
    
    captionsList.innerHTML = '';
    data.captions.forEach((caption, index) => {
        const captionItem = document.createElement('div');
        captionItem.className = 'caption-item';
        captionItem.style.animationDelay = `${index * 0.1}s`;
        captionItem.innerHTML = `
            <span class="caption-number">Caption ${index + 1}:</span>
            <span class="caption-text">${caption}</span>
        `;
        captionsList.appendChild(captionItem);
    });
    
    resultsSection.style.display = 'block';
}

function showError(message) {
    hideAllSections();
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
}

function hideAllSections() {
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
}

function resetUpload() {
    selectedFile = null;
    imageInput.value = '';
    generateBtn.disabled = true;
    uploadBox.innerHTML = `
        <div class="upload-content">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <p class="upload-text">Click to upload or drag and drop</p>
            <p class="upload-hint">PNG, JPG, JPEG, GIF, BMP (max 16MB)</p>
        </div>
    `;
    hideAllSections();
}

newImageBtn.addEventListener('click', resetUpload);
retryBtn.addEventListener('click', resetUpload);
