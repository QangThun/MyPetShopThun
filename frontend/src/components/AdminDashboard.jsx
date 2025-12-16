import React, { useState, useEffect } from 'react';
import './AdminDashboard.css';

export default function AdminDashboard({ onLogout }) {
  const [stats, setStats] = useState({
    total_orders: 0,
    total_revenue: 0,
    today_orders: 0,
    today_revenue: 0,
    orders: []
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('date');

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/stats');
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Lỗi tải thống kê:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(num);
  };

  const filteredOrders = stats.orders
    .filter(order => {
      const searchLower = searchTerm.toLowerCase();
      return (
        order.name.toLowerCase().includes(searchLower) ||
        order.phone.includes(searchTerm) ||
        order.service.toLowerCase().includes(searchLower)
      );
    })
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.created_at) - new Date(a.created_at);
      } else if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      }
      return 0;
    });

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Đang tải...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <h1 className="header-title">🐾 Pet Spa</h1>
          <p className="header-subtitle">Quản lý đơn hàng</p>
        </div>
        <button className="logout-button" onClick={onLogout}>🚪</button>
      </div>

      {/* Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-info">
            <p className="stat-label">Tổng đơn</p>
            <p className="stat-value">{stats.total_orders}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-info">
            <p className="stat-label">Tổng thu</p>
            <p className="stat-value">{formatCurrency(stats.total_revenue)}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📅</div>
          <div className="stat-info">
            <p className="stat-label">Hôm nay</p>
            <p className="stat-value">{stats.today_orders}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-info">
            <p className="stat-label">Thu hôm nay</p>
            <p className="stat-value">{formatCurrency(stats.today_revenue)}</p>
          </div>
        </div>
      </div>

      {/* Orders Section */}
      <div className="orders-section">
        <div className="section-title">📋 Danh sách đơn hàng</div>

        {/* Search and Filter */}
        <div className="filters">
          <input
            type="text"
            className="search-input"
            placeholder="Tìm kiếm..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select
            className="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="date">Mới nhất</option>
            <option value="date-asc">Cũ nhất</option>
            <option value="name">Tên A-Z</option>
          </select>
        </div>

        {/* Orders List */}
        <div className="orders-list">
          {filteredOrders.length > 0 ? (
            filteredOrders.map((order, i) => (
              <div key={i} className="order-card">
                <div className="order-header">
                  <div className="order-name">👤 {order.name}</div>
                  <div className="order-price">{order.price}</div>
                </div>
                <div className="order-details">
                  <div className="detail-item">
                    <span className="detail-label">📞</span>
                    <span className="detail-value">{order.phone}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">🐕</span>
                    <span className="detail-value">{order.service}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">⏰</span>
                    <span className="detail-value">{order.time}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">📅</span>
                    <span className="detail-value">{order.created_at}</span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <p>Không tìm thấy đơn hàng</p>
            </div>
          )}
        </div>

        <div className="orders-count">
          {filteredOrders.length} / {stats.orders.length} đơn hàng
        </div>
      </div>
    </div>
  );
}
