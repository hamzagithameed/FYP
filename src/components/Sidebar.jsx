import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

export default function Sidebar({ user, onLogout, theme }) {
  const location = useLocation();

  const navItems = [
    {
      path: '/dashboard/word',
      label: 'Generate Word',
      icon: '✍️',
      description: 'Single word generation'
    },
    {
      path: '/dashboard/sentence',
      label: 'Generate Sentence',
      icon: '📝',
      description: 'Full sentence generation'
    },
    {
      path: '/dashboard/stylized',
      label: 'Stylized Handwriting',
      icon: '🎨',
      description: 'Custom style generation'
    },
    {
      path: '/dashboard/detect',
      label: 'Text Detection',
      icon: '🔍',
      description: 'Detect text from image'
    }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <Link to="/" className="sidebar__logo">
          <span className="logo-icon">✨</span>
          <span className="logo-text">InkWave</span>
        </Link>
      </div>

      <div className="sidebar__user">
        <div className="user-avatar">
          {user?.name?.charAt(0).toUpperCase() || 'U'}
        </div>
        <div className="user-info">
          <p className="user-name">{user?.name || 'User'}</p>
          <p className="user-email">{user?.email || 'user@inkwave.app'}</p>
        </div>
      </div>

      <nav className="sidebar__nav">
        <p className="nav-label">Generation Tools</p>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${isActive ? 'nav-item--active' : ''}`}
            >
              <span className="nav-item__icon">{item.icon}</span>
              <div className="nav-item__content">
                <span className="nav-item__label">{item.label}</span>
                <span className="nav-item__description">{item.description}</span>
              </div>
              {isActive && (
                <motion.div
                  className="nav-item__indicator"
                  layoutId="activeIndicator"
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar__footer">
        <button onClick={onLogout} className="btn btn--ghost btn--full">
          <span>🚪</span> Logout
        </button>
      </div>
    </aside>
  );
}
