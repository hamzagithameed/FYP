import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const highlights = [
  {
    title: 'Generative handwriting',
    body: 'Create living, breathing strokes tailored to every note, brand, or signature.',
  },
  {
    title: 'Style transfer engine',
    body: 'Blend reference samples with AI diffusion to capture authentic pen pressure.',
  },
  {
    title: 'Realtime preview',
    body: 'Iterate instantly with adaptive layout guides, smart baselines, and exports.',
  },
];

export default function Landing({ theme, onToggleTheme, user }) {
  const navigate = useNavigate();

  const stats = useMemo(
    () => [
      { value: '120K+', label: 'Samples rendered' },
      { value: '38', label: 'Creator workflows' },
      { value: '210ms', label: 'Average response' },
    ],
    []
  );

  const actions = user
    ? [
        { label: 'Open studio', accent: 'primary', to: '/studio', type: 'route' },
        { label: 'Upload style', accent: 'ghost', to: '#upload', type: 'hash' },
      ]
    : [
        { label: 'Login', accent: 'outline', to: '/auth?mode=login', type: 'route' },
        { label: 'Sign up', accent: 'primary', to: '/auth?mode=signup', type: 'route' },
        { label: 'Upload style', accent: 'ghost', to: '#upload', type: 'hash' },
      ];

  const handleAction = (action) => {
    if (action.type === 'route') {
      navigate(action.to);
      return;
    }
    window.location.hash = action.to;
  };

  return (
    <div className={`page landing ${theme}`}>
      <div className="noise" />
      <header className="hero" id="top">
        <div className="hero__copy">
          <div className="pill">AI handwriting studio</div>
          <h1>
            Craft expressive
            <span> strokes that feel human.</span>
          </h1>
          <p>
            InkWave turns brief prompts into fully stylized handwriting systems.
            Prototype signatures, letterheads, or motion titles with cinematic control.
          </p>
          <div className="actions">
            {actions.map((action) => (
              <button
                key={action.label}
                className={`btn btn--${action.accent}`}
                onClick={() => handleAction(action)}
              >
                {action.label}
              </button>
            ))}
          </div>
          <div className="stats">
            {stats.map((stat) => (
              <div key={stat.label}>
                <strong>{stat.value}</strong>
                <span>{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
        <motion.div
          className="hero__visual"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, ease: 'easeOut' }}
        >
          <div className="orb">
            <div className="orb__ring" />
            <div className="orb__ring orb__ring--delay" />
            <p>Upload a sample, remix the motion, export the pen stroke story.</p>
          </div>
        </motion.div>
        <button
          className="theme-toggle"
          aria-label="Toggle color theme"
          onClick={onToggleTheme}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </header>

      <section className="intro" id="project">
        <div className="intro__header">
          <p>Project introduction</p>
          <h2>Design handwriting systems that scale from a napkin to a brand bible.</h2>
          <span>
            Built for motion designers, researchers, and studios exploring the outer edges of
            pen-based storytelling.
          </span>
        </div>
        <div className="intro__grid">
          {highlights.map((item, index) => (
            <motion.article
              key={item.title}
              className="card"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.6 }}
              transition={{ delay: index * 0.1, duration: 0.6 }}
            >
              <h3>{item.title}</h3>
              <p>{item.body}</p>
              <div className="card__bar" />
            </motion.article>
          ))}
        </div>
      </section>

      <section className="cta" id="upload">
        <motion.div
          className="cta__panel"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.5 }}
        >
          <h2>Ready to upload your handwriting?</h2>
          <p>
            Drop a few signatures or paragraphs, select a mood, and InkWave learns the motion,
            spacing, and micro-expressions in seconds.
          </p>
          <div className="actions">
            <button className="btn btn--primary" onClick={() => handleAction(actions[2])}>
              Upload
            </button>
            <button className="btn btn--outline">Preview styles</button>
          </div>
        </motion.div>
      </section>

      <footer>
        <span>© {new Date().getFullYear()} InkWave</span>
        <a href="#top">Back to top</a>
      </footer>
    </div>
  );
}

