import { useState } from 'react';
import { motion } from 'framer-motion';

const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  'http://localhost:8000';

export default function GenerateWord() {
  const [text, setText] = useState('');
  const [resultImage, setResultImage] = useState(null);
  const [generatedImageFile, setGeneratedImageFile] = useState(null);
  const [status, setStatus] = useState('Enter a single word to generate handwriting.');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const handleGenerate = async () => {
    const word = text.trim();
    if (!word) {
      setStatus('Please enter a word to generate.');
      return;
    }

    if (word.split(' ').length > 1) {
      setStatus('Please enter only a single word. Use "Generate Sentence" for multiple words.');
      return;
    }

    setIsGenerating(true);
    setStatus('Generating handwriting for your word...');

    try {
      const response = await fetch(`${API_BASE_URL}/api/word`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: word }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to generate word.');
      }

      const data = await response.json();
      const imageData = `data:image/png;base64,${data.image_base64}`;
      setResultImage(imageData);

      // Convert base64 to blob for PDF generation
      const blob = await (await fetch(imageData)).blob();
      const file = new File([blob], data.filename, { type: 'image/png' });
      setGeneratedImageFile(file);

      setStatus(`Successfully generated: "${data.text}"`);
    } catch (error) {
      console.error(error);
      setStatus(error.message || 'Something went wrong. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadImage = () => {
    if (!resultImage) return;
    const anchor = document.createElement('a');
    anchor.href = resultImage;
    anchor.download = `inkwave-word-${text.trim()}.png`;
    anchor.click();
    setStatus('Image downloaded successfully.');
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
        <h1>✍️ Generate Word</h1>
        <p>Generate handwriting for a single word using the default style</p>
      </motion.div>

      <div className="generation-grid">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="generation-input-section"
        >
          <div className="input-card">
            <h2>1. Enter your word</h2>
            <input
              type="text"
              className="text-input"
              placeholder="Enter a single word..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
              disabled={isGenerating}
            />
            <p className="input-hint">
              💡 Tip: Enter only one word. For multiple words, use "Generate Sentence"
            </p>

            <button
              className="btn btn--primary btn--large"
              onClick={handleGenerate}
              disabled={isGenerating || !text.trim()}
            >
              {isGenerating ? (
                <>
                  <span className="spinner"></span> Generating...
                </>
              ) : (
                <>✨ Generate Handwriting</>
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
                <span className="placeholder-icon">✍️</span>
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
