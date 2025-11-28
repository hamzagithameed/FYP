import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';

// Prefer env var when available, otherwise fall back to local FastAPI default
const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  'http://localhost:8000';

export default function Studio({ theme, onToggleTheme, user, onLogout }) {
  const navigate = useNavigate();
  const [text, setText] = useState('InkWave brings your sentences to life.');
  const [samples, setSamples] = useState([]);
  const [samplePreview, setSamplePreview] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [generatedImageFile, setGeneratedImageFile] = useState(null);
  const [status, setStatus] = useState('Upload handwriting and convert any sentence.');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/auth?mode=signup', { replace: true });
    }
  }, [user, navigate]);

  const persona = useMemo(
    () => ({
      name: user?.name || 'InkWave Creator',
      email: user?.email || 'new@inkwave.app',
    }),
    [user]
  );

  useEffect(
    () => () => {
      if (samplePreview?.url) URL.revokeObjectURL(samplePreview.url);
    },
    [samplePreview]
  );

  const handleSampleUpload = (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;

    // Accumulate files across multiple selections so user can add 1 by 1
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
        // Clean up Python tracebacks and technical details
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
    const data = resultImage;
    const anchor = document.createElement('a');
    anchor.href = data;
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
    <div className={`page page--studio ${theme}`}>
      <div className="noise" />
      <div className="studio">
        <header className="studio__header">
          <div>
            <p>Welcome back</p>
            <h1>Ready to generate your handwriting?</h1>
          </div>
          <div className="studio__actions">
            <Link to="/" className="ghost-link">
              ← Back to landing
            </Link>
            <button className="theme-toggle" onClick={onToggleTheme} aria-label="Toggle theme">
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            {user && (
              <button className="ghost-link" onClick={onLogout}>
                Sign out
              </button>
            )}
          </div>
        </header>

        <div className="studio__layout">
          <motion.section
            className="studio__panel"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <h2>1. Enter your text</h2>
            <label className="field">
              <span>Paragraph or sentence</span>
              <textarea
                value={text}
                onChange={(event) => setText(event.target.value)}
                rows={4}
                placeholder="Type any paragraph or sentence to convert to handwriting..."
              />
            </label>

            <h2>2. Upload handwriting samples</h2>
            <label className="upload">
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleSampleUpload}
              />
              <div>
                <strong>Drop at least five images or click to browse</strong>
                <span>High-contrast scans or photos of your handwriting work best.</span>
              </div>
            </label>
            {samplePreview && (
              <div className="sample-preview">
                <span>
                  {samplePreview.name}
                  {samplePreview.count > 1 ? `  (+${samplePreview.count - 1} more)` : ''}
                </span>
                <img src={samplePreview.url} alt="Handwriting sample preview" />
              </div>
            )}

            <button
              className="btn btn--primary"
              onClick={handleGenerate}
              disabled={isGenerating || !text.trim()}
            >
              {isGenerating ? 'Converting to handwriting…' : 'Convert to handwriting'}
            </button>
            <p className="hint">{status}</p>
          </motion.section>

          <motion.section
            className="studio__panel studio__panel--preview"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <div className="preview">
              <div className="preview__label">
                <span>{persona.name}</span>
                <span>{persona.email}</span>
              </div>
              {resultImage ? (
                <img src={resultImage} alt="Handwriting result" className="preview__image" />
              ) : (
                <>
                  <p className="preview__text">
                    {text || 'Your handwriting preview will appear here.'}
                  </p>
                  <div className="preview__signature">/ / InkWave engine / /</div>
                </>
              )}
              {samplePreview?.url && !resultImage && (
                <img src={samplePreview.url} alt="" className="preview__sample" />
              )}
            </div>

            <div className="studio__download">
              <button
                className="btn btn--outline"
                onClick={downloadImage}
                disabled={isGenerating || !resultImage}
              >
                Download image
              </button>
              <button
                className="btn btn--outline"
                onClick={downloadPdf}
                disabled={isGenerating || isDownloadingPdf || !generatedImageFile}
              >
                {isDownloadingPdf ? 'Building PDF…' : 'Download PDF'}
              </button>
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
}

