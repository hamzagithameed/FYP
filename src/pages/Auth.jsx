import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

const tabs = [
  { id: 'login', label: 'Login' },
  { id: 'signup', label: 'Sign up' },
];

const hints = [
  'Your handwriting vectors stay encrypted in your space.',
  'Switch between pen, brush, or stylus rendering in one click.',
  'All previews sync with the landing experience instantly.',
];

const loginFields = [
  { name: 'email', label: 'Email', type: 'email', placeholder: 'you@mail.com' },
  { name: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
];

const signupFields = [
  { name: 'name', label: 'Full name', type: 'text', placeholder: 'Alex Rivera' },
  ...loginFields,
];

export default function AuthPage({ theme, onToggleTheme, onAuthSuccess }) {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const defaultTab = params.get('mode') === 'signup' ? 'signup' : 'login';
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const formFields = activeTab === 'signup' ? signupFields : loginFields;

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setParams({ mode: tab }, { replace: true });
  };

  const hint = useMemo(() => hints[Math.floor(Math.random() * hints.length)], [activeTab]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());

    setIsSubmitting(true);
    setFeedback({
      type: 'info',
      message: activeTab === 'login' ? 'Signing you in…' : 'Creating your workspace…',
    });

    try {
      const endpoint = activeTab === 'login' ? '/auth/login' : '/auth/signup';
      const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      let data;
      try {
        data = await response.json();
      } catch (e) {
        throw new Error('Server error. Please try again.');
      }

      if (!response.ok) {
        // Handle validation errors
        if (response.status === 422 && data.detail) {
          const errors = Array.isArray(data.detail) 
            ? data.detail.map(err => err.msg).join(', ')
            : data.detail;
          throw new Error(errors);
        }
        throw new Error(data.detail || 'Authentication failed');
      }

      // Store token and user data
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('inkwave-user', JSON.stringify(data.user));

      setIsSubmitting(false);
      setFeedback({
        type: 'success',
        message:
          activeTab === 'login'
            ? 'Logged in. Routing you to the dashboard.'
            : 'Account created. Redirecting to dashboard.',
      });

      // Call onAuthSuccess with user data
      if (typeof onAuthSuccess === 'function') {
        onAuthSuccess(data.user);
      }

      // Redirect to dashboard
      setTimeout(() => {
        navigate('/dashboard');
      }, 500);
    } catch (error) {
      console.error('Auth error:', error);
      setIsSubmitting(false);
      setFeedback({
        type: 'error',
        message: error.message || 'Something went wrong. Please try again.',
      });
    }
  };

  return (
    <div className={`page page--auth ${theme}`}>
      <div className="noise" />
      <div className="auth">
        <nav className="auth__nav">
          <Link to="/" className="ghost-link">
            ← Back to landing
          </Link>
          <button className="theme-toggle" onClick={onToggleTheme} aria-label="Toggle theme">
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </nav>

        <motion.div
          className="auth__panel"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="auth__header">
            <p>Welcome to InkWave</p>
            <h1>Sign in and keep crafting expressive handwriting systems.</h1>
          </div>

          <div className="auth__tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`auth__tab ${activeTab === tab.id ? 'is-active' : ''}`}
                onClick={() => handleTabChange(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <form className="auth__form" onSubmit={handleSubmit}>
            {formFields.map((field) => (
              <label key={field.name} className="field">
                <span>{field.label}</span>
                <input
                  type={field.type}
                  name={field.name}
                  placeholder={field.placeholder}
                  required
                  disabled={isSubmitting}
                />
              </label>
            ))}
            {activeTab === 'signup' && (
              <label className="field checkbox">
                <input type="checkbox" name="terms" required disabled={isSubmitting} /> I agree to
                the creator terms.
              </label>
            )}

            <button type="submit" className="btn btn--primary btn--full" disabled={isSubmitting}>
              {isSubmitting ? 'Please wait…' : activeTab === 'login' ? 'Login' : 'Create account'}
            </button>

            {feedback && (
              <div className={`feedback feedback--${feedback.type}`} role="status" aria-live="polite">
                {feedback.message}
              </div>
            )}
          </form>
        </motion.div>

        <motion.div
          className="auth__aside"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <h3>Why InkWave?</h3>
          <p>{hint}</p>
          <ul>
            <li>Import PDFs, SVGs, or live pen captures.</li>
            <li>Link straight to the upload canvas.</li>
            <li>Protect every stroke with creator controls.</li>
          </ul>
          <Link to="/" className="btn btn--outline btn--full">
            Explore landing
          </Link>
        </motion.div>
      </div>
    </div>
  );
}

