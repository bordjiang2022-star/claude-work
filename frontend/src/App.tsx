// 主应用组件
import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/hooks/useAuthStore';
import { LoginPage } from '@/pages/LoginPage';
import { TranslatePage } from '@/pages/TranslatePage';
import { apiService } from '@/services/api';

const App: React.FC = () => {
  const { isAuthenticated, fetchCurrentUser } = useAuthStore();

  useEffect(() => {
    // 尝试从localStorage恢复登录状态
    const token = apiService.getToken();
    if (token) {
      fetchCurrentUser();
    }
  }, [fetchCurrentUser]);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/" /> : <LoginPage />}
        />
        <Route
          path="/"
          element={isAuthenticated ? <TranslatePage /> : <Navigate to="/login" />}
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
