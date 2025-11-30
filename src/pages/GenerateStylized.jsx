import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';

const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  'http://localhost:8000';

export default function GenerateStylized() {
  const [text, setText] = useState('InkWave brings your sentences to life.');
  const [samples, setSamples] = useState([]);
  const [samplePreview, setSamplePreview] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [generatedImageFile, setGeneratedImageFile] = useState(null);
  const [status, setStatus] = useState('Upload handwriting and convert any sentence.');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  useEffect(
    () => () => {
      if (samplePreview?.url) URL.revokeObjectURL(samplePreview.url);
    },
    [samplePreview]
  );

  const handleSampleUpload = (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;

    setSamples((previous) => {
      const merged = [...previous, ...files];

      const first = merged[0];
      const previewUrl = first ? URL.createObjectURL(first) : null;
      if (previewUrl && first) {
        setSamplePreview({
          name: first.name,
          url: previewUrl,
          count: merged.length,
        });
      }

      if (merged.length < 5) {
        setStatus(
          `You have uploaded ${merged.length} image(s). Please upload at least five handwriting images before converting.`
        );
      } else {
        setStatus('Samples ready. Click "Convert to handwriting" to generate.');
      }

      return merged;
    });

    setResultImage(null);
    setGeneratedImageFile(null);
  };

  const handleGenerate = async () => {
    if (samples.length < 5) {
      setStatus('Please upload at least five handwriting images before converting.');
      return;
    }
    if (!text.trim()) {
      setStatus('Please enter some text to convert.');
      return;
    }

    setIsGenerating(true);
    setStatus('Processing your text and handwriting samples...');

    try {
      const formData = new FormData();
      formData.append('text', text);
      samples.forEach((file) => formData.append('samples', file));

      const response = await fetch(`${API_BASE_URL}/api/stylized`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = 'Failed to generate handwriting.';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = `Server error (${response.status}). Please check if the backend is running.`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      const base64 = data.image_base64;
      const filename = data.filename || 'handwriting.png';

      if (!base64) {
        throw new Error('API did not return an image.');
      }

      const dataUrl = `data:image/png;base64,${base64}`;
      setResultImage(dataUrl);
      setStatus('✓ Handwriting generated successfully! You can now download as image or PDF.');

      const byteCharacters = atob(base64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i += 1) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'image/png' });
      const fileForPdf = new File([blob], filename, { type: 'image/png' });
      setGeneratedImageFile(fileForPdf);
    } catch (error) {
      console.error('Generation error:', error);
      let message = 'Something went wrong while generating handwriting.';
      
      if (error?.message === 'Failed to fetch') {
        message = `Could not reach handwriting server at ${API_BASE_URL}. Please make sure the backend is running.`;
      } else if (error?.message) {
        const cleanMessage = error.message
          .replace(/Traceback \(most recent call last\):.*?(?=\w+Error:)/gs, '')
          .replace(/File ".*?", line \d+, in .*?\n/g, '')
          .replace(/ModuleNotFoundError: No module named '.*?'/g, 'Missing required dependencies on server')
          .replace(/ImportError:.*?/g, 'Server configuration issue')
          .trim();
        message = cleanMessage || 'Server processing error occurred.';
      }
      
      setStatus(message);
      setResultImage(null);
      setGeneratedImageFile(null);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadImage = async () => {
    if (!resultImage) return;
    const anchor = document.createElement('a');
    anchor.href = resultImage;
    anchor.download = 'inkwave-handwriting.png';
    anchor.click();
  };

  const downloadPdf = async () => {
    if (!generatedImageFile) {
      setStatus('Generate handwriting first, then download as PDF.');
      return;
    }
    setIsDownloadingPdf(true);
    setStatus('Building PDF via backend…');

    try {
      const formData = new FormData();
      formData.append('sentence', text);
      formData.append('images', generatedImageFile);

      const response = await fetch(`${API_BASE_URL}/convert/pdf`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to generate PDF.');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'inkwave-handwriting.pdf';
      anchor.click();
      URL.revokeObjectURL(url);
      setStatus('PDF downloaded successfully.');
    } catch (error) {
      console.error(error);
      setStatus(error.message || 'Something went wrong while generating the PDF.');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  return (
    <div className="generation-page">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="generation-header"
      >
        <h1>🎨 Stylized Handwriting</h1>
        <p>Generate handwriting using your own custom handwriting style</p>
      </motion.div>

      <div className="generation-grid">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="generation-input-section"
        >
          <div className="input-card">
            <h2>1. Enter your text</h2>
            <textarea
              className="text-input text-input--textarea"
              placeholder="Enter your sentence or paragraph..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={isGenerating}
              rows={4}
            />

            <h2>2. Upload handwriting samples</h2>
            <label className="upload-area">
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleSampleUpload}
                disabled={isGenerating}
                style={{ display: 'none' }}
              />
              <div className="upload-content">
                <span className="upload-icon">📁</span>
                <p className="upload-text">
                  Drop at least five images or click to browse
                </p>
                <p className="upload-hint">
                  High-contrast scans or photos of your handwriting work best.
                </p>
              </div>
            </label>

            {samplePreview && (
              <div className="sample-preview">
                <img src={samplePreview.url} alt="Sample preview" />
                <p className="sample-count">
                  {samplePreview.count} image{samplePreview.count !== 1 ? 's' : ''} uploaded
                </p>
              </div>
            )}

            <button
              className="btn btn--primary btn--large"
              onClick={handleGenerate}
              disabled={isGenerating || samples.length < 5 || !text.trim()}
            >
              {isGenerating ? (
                <>
                  <span className="spinner"></span> Generating...
                </>
              ) : (
                <>✨ Convert to Handwriting</>
              )}
            </button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="generation-output-section"
        >
          <div className="output-card">
            <h2>Generated Handwriting</h2>
            {resultImage ? (
              <div className="result-container">
                <img src={resultImage} alt="Generated handwriting" className="result-image" />
                <div className="result-actions">
                  <button
                    className="btn btn--outline"
                    onClick={downloadImage}
                    disabled={isGenerating}
                  >
                    📥 Download Image
                  </button>
                  <button
                    className="btn btn--outline"
                    onClick={downloadPdf}
                    disabled={isGenerating || isDownloadingPdf}
                  >
                    {isDownloadingPdf ? 'Building PDF…' : '📄 Download PDF'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="result-placeholder">
                <span className="placeholder-icon">🎨</span>
                <p>Your generated handwriting will appear here</p>
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
