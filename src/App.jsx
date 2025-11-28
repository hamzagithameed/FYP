import { useEffect, useState } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Landing from './pages/Landing.jsx';
import AuthPage from './pages/Auth.jsx';
import Studio from './pages/Studio.jsx';

export default function App() {
  const prefersDark =
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-color-scheme: dark)').matches;

  const [theme, setTheme] = useState(() => {
    const saved = typeof window !== 'undefined' && localStorage.getItem('dp-theme');
    return saved || (prefersDark ? 'dark' : 'light');
  });
  const [user, setUser] = useState(() => {
    const stored =
      typeof window !== 'undefined' && localStorage.getItem('inkwave-user');
    return stored ? JSON.parse(stored) : null;
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('dp-theme', theme);
  }, [theme]);

  useEffect(() => {
    if (user) {
      localStorage.setItem('inkwave-user', JSON.stringify(user));
    } else {
      localStorage.removeItem('inkwave-user');
    }
  }, [user]);

  const toggleTheme = () => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  const handleAuthSuccess = (payload) => setUser(payload);
  const handleLogout = () => setUser(null);

  return (
    <BrowserRouter>
      <div className="app-root">
        <Routes>
          <Route
            path="/"
            element={
              <Landing theme={theme} onToggleTheme={toggleTheme} user={user} />
            }
          />
          <Route
            path="/auth"
            element={
              <AuthPage
                theme={theme}
                onToggleTheme={toggleTheme}
                onAuthSuccess={handleAuthSuccess}
                user={user}
              />
            }
          />
          <Route
            path="/studio"
            element={
              <Studio
                theme={theme}
                onToggleTheme={toggleTheme}
                user={user}
                onLogout={handleLogout}
              />
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

