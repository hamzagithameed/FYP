import { useState } from 'react';
import { motion } from 'framer-motion';

const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  'http://localhost:8000';

export default function DetectText() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [detectedText, setDetectedText] = useState('');
  const [status, setStatus] = useState('Upload a handwriting image to detect text.');
  const [isDetecting, setIsDetecting] = useState(false);

  const handleImageUpload = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setStatus('Please upload a valid image file.');
      return;
    }

    setSelectedImage(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target.result);
    };
    reader.readAsDataURL(file);

    setDetectedText('');
    setStatus('Image uploaded. Click "Detect Text" to analyze.');
  };

  const handleDetect = async () => {
    if (!selectedImage) {
      setStatus('Please upload an image first.');
      return;
    }

    setIsDetecting(true);
    setStatus('Analyzing handwriting...');

    try {
      const formData = new FormData();
      formData.append('image', selectedImage);

      const response = await fetch(`${API_BASE_URL}/api/detect`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to detect text.');
      }

      const data = await response.json();
      setDetectedText(data.detected_text);
      setStatus('✓ Text detected successfully!');
    } catch (error) {
      console.error(error);
      let message = 'Something went wrong while detecting text.';
      
      if (error?.message === 'Failed to fetch') {
        message = `Could not reach server at ${API_BASE_URL}. Please make sure the backend is running.`;
      } else if (error?.message) {
        message = error.message;
      }
      
      setStatus(message);
      setDetectedText('');
    } finally {
      setIsDetecting(false);
    }
  };

  const handleCopyText = () => {
    if (!detectedText) return;
    navigator.clipboard.writeText(detectedText);
    setStatus('✓ Text copied to clipboard!');
  };

  const handleClear = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setDetectedText('');
    setStatus('Upload a handwriting image to detect text.');
  };

  return (
    <div className="generation-page">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="generation-header"
      >
        <h1>🔍 Text Detection</h1>
        <p>Upload a handwriting image and detect the text using AI</p>
      </motion.div>

      <div className="generation-grid">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="generation-input-section"
        >
          <div className="input-card">
            <h2>1. Upload handwriting image</h2>
            <label className="upload-area">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                disabled={isDetecting}
                style={{ display: 'none' }}
              />
              <div className="upload-content">
                <span className="upload-icon">📷</span>
                <p className="upload-text">
                  Drop an image or click to browse
                </p>
                <p className="upload-hint">
                  Upload a clear photo or scan of handwritten text
                </p>
              </div>
            </label>

            {imagePreview && (
              <div className="sample-preview">
                <img src={imagePreview} alt="Uploaded handwriting" />
                <p className="sample-count">
                  {selectedImage?.name || 'Image uploaded'}
                </p>
              </div>
            )}

            <button
              className="btn btn--primary btn--large"
              onClick={handleDetect}
              disabled={isDetecting || !selectedImage}
            >
              {isDetecting ? (
                <>
                  <span className="spinner"></span> Detecting...
                </>
              ) : (
                <>🔍 Detect Text</>
              )}
            </button>

            {(imagePreview || detectedText) && (
              <button
                className="btn btn--outline btn--large"
                onClick={handleClear}
                disabled={isDetecting}
                style={{ marginTop: '0.75rem' }}
              >
                🔄 Clear & Start Over
              </button>
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="generation-output-section"
        >
          <div className="output-card">
            <h2>Detected Text</h2>
            {detectedText ? (
              <div className="result-container">
                <div className="detected-text-display">
                  <p className="detected-text">{detectedText}</p>
                </div>
                <div className="result-actions">
                  <button
                    className="btn btn--outline"
                    onClick={handleCopyText}
                    disabled={isDetecting}
                  >
                    📋 Copy Text
                  </button>
                </div>
              </div>
            ) : (
              <div className="result-placeholder">
                <span className="placeholder-icon">🔍</span>
                <p>Detected text will appear here</p>
              </div>
            )}
          </div>

          <div className="status-card">
            <p className="status-text">{status}</p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
