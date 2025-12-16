import React, { useState } from 'react';
import './Login.css';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!username || !password) {
      setError('Vui lòng nhập tên đăng nhập và mật khẩu');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch('http://127.0.0.1:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      
      if (res.ok) {
        const data = await res.json();
        onLogin(data.role);
      } else {
        setError('Sai tên đăng nhập hoặc mật khẩu!');
      }
    } catch (e) {
      setError('Lỗi kết nối Server! Vui lòng kiểm tra Backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="login-container">
      <div className="login-content">
        <div className="login-header">
          <div className="login-icon">🐾</div>
          <h1 className="login-title">Pet Lovers Spa</h1>
          <p className="login-subtitle">Chăm sóc thú cưng của bạn với tình yêu</p>
        </div>

        <form className="login-form" onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
          <div className="form-group">
            <label htmlFor="username" className="form-label">Tên đăng nhập</label>
            <input
              id="username"
              className="form-input"
              type="text"
              placeholder="Nhập tên đăng nhập"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                setError('');
              }}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">Mật khẩu</label>
            <input
              id="password"
              className="form-input"
              type="password"
              placeholder="Nhập mật khẩu"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError('');
              }}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="login-button"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? 'Đang đăng nhập...' : 'Đăng Nhập'}
          </button>
        </form>

        <div className="login-credentials">
          <p className="credentials-title">Demo Credentials:</p>
          <div className="credentials-list">
            <div className="credential-item">
              <span className="credential-label">Khách:</span>
              <span className="credential-value">khachhang / 123</span>
            </div>
            <div className="credential-item">
              <span className="credential-label">Admin:</span>
              <span className="credential-value">admin / admin123</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
