import { useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function DashboardLayout({ theme, onToggleTheme, user, onLogout }) {
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/auth?mode=signup', { replace: true });
    }
  }, [user, navigate]);

  if (!user) return null;

  return (
    <div className={`dashboard ${theme}`}>
      <div className="noise" />
      <Sidebar user={user} onLogout={onLogout} theme={theme} />
      <main className="dashboard__main">
        <div className="dashboard__header">
          <button 
            className="theme-toggle" 
            onClick={onToggleTheme} 
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
        <div className="dashboard__content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
