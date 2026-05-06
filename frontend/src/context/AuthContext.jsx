
import { createContext, useContext, useState, useEffect } from 'react';
import { saveConnection, getCurrentConnection, clearCurrentConnection } from '../lib/storage';
import { apiRequest } from '../lib/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [connection, setConnection] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = getCurrentConnection();
    if (stored) {
      setConnection(stored);
    }
    setLoading(false);
  }, []);

  const login = async (config) => {
    const response = await apiRequest('/api/connect', {
      method: 'POST',
      body: { config },
    });
    setConnection(config);
    saveConnection(config);
    return response;
  };

  const logout = () => {
    setConnection(null);
    clearCurrentConnection();
  };

  const fetchDefaults = async () => {
    try {
      const data = await apiRequest('/api/defaults', { method: 'GET' });
      return data;
    } catch {
      return { source: 'none', config: null };
    }
  };

  // Helper for authenticated API calls
  const apiCall = async (endpoint, method = 'POST', body = null) => {
    if (!connection) throw new Error("Not connected");
    return apiRequest(endpoint, { method, body, connection });
  };

  return (
    <AuthContext.Provider value={{ connection, loading, login, logout, apiCall, fetchDefaults }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
