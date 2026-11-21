import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string;
  role: 'citizen' | 'admin' | 'department_officer';
  is_active: boolean;
  created_at?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; full_name: string; phone_number?: string; role?: string }) => Promise<void>;
  demoLogin: (role: 'citizen' | 'admin') => Promise<void>;
  logout: () => void;
  isAuthModalOpen: boolean;
  authModalTab: 'login' | 'register' | 'demo';
  openAuthModal: (tab?: 'login' | 'register' | 'demo') => void;
  closeAuthModal: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('civiceye_token'));
  const [loading, setLoading] = useState<boolean>(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [authModalTab, setAuthModalTab] = useState<'login' | 'register' | 'demo'>('login');

  const openAuthModal = (tab: 'login' | 'register' | 'demo' = 'login') => {
    setAuthModalTab(tab);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const fetchCurrentUser = async () => {
    const savedToken = localStorage.getItem('civiceye_token');
    if (!savedToken) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const response = await apiClient.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.warn('Session expired or invalid token:', error);
      localStorage.removeItem('civiceye_token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password });
    const { access_token, user: loggedUser } = response.data;
    localStorage.setItem('civiceye_token', access_token);
    setToken(access_token);
    setUser(loggedUser);
    closeAuthModal();
  };

  const register = async (data: { email: string; password: string; full_name: string; phone_number?: string; role?: string }) => {
    const response = await apiClient.post('/auth/register', data);
    const { access_token, user: registeredUser } = response.data;
    localStorage.setItem('civiceye_token', access_token);
    setToken(access_token);
    setUser(registeredUser);
    closeAuthModal();
  };

  const demoLogin = async (role: 'citizen' | 'admin') => {
    const response = await apiClient.post('/auth/demo-login', { role });
    const { access_token, user: demoUser } = response.data;
    localStorage.setItem('civiceye_token', access_token);
    setToken(access_token);
    setUser(demoUser);
    closeAuthModal();
  };

  const logout = () => {
    localStorage.removeItem('civiceye_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        login,
        register,
        demoLogin,
        logout,
        isAuthModalOpen,
        authModalTab,
        openAuthModal,
        closeAuthModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
