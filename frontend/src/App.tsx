import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AuthModal } from './components/auth/AuthModal';
import { Navbar } from './components/common/Navbar';
import { Footer } from './components/common/Footer';
import { LandingPage } from './pages/LandingPage';
import { checkSystemHealth } from './api/client';

export const App: React.FC = () => {
  const [backendOnline, setBackendOnline] = useState<boolean>(false);

  useEffect(() => {
    const probe = async () => {
      try {
        await checkSystemHealth();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }
    };
    probe();
    const interval = setInterval(probe, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100 font-sans selection:bg-blue-600 selection:text-white">
          <Navbar backendOnline={backendOnline} />
          <main className="flex-grow">
            <Routes>
              <Route path="/" element={<LandingPage />} />
            </Routes>
          </main>
          <Footer />
          <AuthModal />
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
