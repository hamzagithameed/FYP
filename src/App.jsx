import { useEffect, useState } from 'react';
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import Landing from './pages/Landing.jsx';
import AuthPage from './pages/Auth.jsx';
import Studio from './pages/Studio.jsx';
import DashboardLayout from './components/DashboardLayout.jsx';
import GenerateWord from './pages/GenerateWord.jsx';
import GenerateSentence from './pages/GenerateSentence.jsx';
import GenerateStylized from './pages/GenerateStylized.jsx';
import DetectText from './pages/DetectText.jsx';

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
          <Route
            path="/dashboard"
            element={
              <DashboardLayout
                theme={theme}
                onToggleTheme={toggleTheme}
                user={user}
                onLogout={handleLogout}
              />
            }
          >
            <Route index element={<Navigate to="/dashboard/word" replace />} />
            <Route path="word" element={<GenerateWord />} />
            <Route path="sentence" element={<GenerateSentence />} />
            <Route path="stylized" element={<GenerateStylized />} />
            <Route path="detect" element={<DetectText />} />
          </Route>
        </Routes>
      </div>
    </BrowserRouter>
  );
}

