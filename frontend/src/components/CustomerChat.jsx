import React, { useState, useRef, useEffect } from 'react';
import './Chat.css';

export default function CustomerChat({ onLogout }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '👋 Chào bạn! Em Mimi rất vui được giúp bạn. Bạn cần dịch vụ gì nào?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [services, setServices] = useState(null);
  const [selectedServices, setSelectedServices] = useState([]);
  const [orderSummary, setOrderSummary] = useState(null);
  const [showOrderConfirm, setShowOrderConfirm] = useState(false);
  const [showInfoForm, setShowInfoForm] = useState(false);
  const [customerInfo, setCustomerInfo] = useState({ name: '', phone: '', petName: '', petType: '', time: '' });
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Fetch services on component mount
    const fetchServices = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/services');
        const data = await res.json();
        setServices(data.services);
      } catch (error) {
        console.error('Error fetching services:', error);
      }
    };
    fetchServices();
  }, []);

  const [currentServiceKey, setCurrentServiceKey] = useState(null);

  // Handle main service selection - show sub-services
  const handleServiceSelect = (serviceKey) => {
    setCurrentServiceKey(serviceKey);
  };

  // Handle sub-service selection
  const handleSubServiceSelect = (serviceKey, subServiceId) => {
    const subService = services[serviceKey]?.sub_services?.find(s => s.id === subServiceId);
    const message = `${subService?.name || ''}`;

    const updatedServices = [...selectedServices, {
      service: serviceKey,
      subService: subServiceId,
      name: subService?.name,
      price: subService?.price
    }];

    setSelectedServices(updatedServices);
    setCurrentServiceKey(null);

    const userMessage = { role: 'user', content: message };
    setMessages([...messages, userMessage]);
    setInput('');
    sendMessage(message, [...messages, userMessage], updatedServices);
  };

  // Go back to main services
  const handleBackToServices = () => {
    setCurrentServiceKey(null);
  };

  // Send chat message
  const sendMessage = async (messageText = null, msgHistory = null, updatedServices = null) => {
    const textToSend = messageText || input;
    if (!textToSend.trim()) return;

    const currentServices = updatedServices !== null ? updatedServices : selectedServices;

    // Check if user is trying to confirm order via chat
    const textLower = textToSend.toLowerCase();
    const confirmKeywords = ['chốt', 'xác nhận', 'confirm', 'ok', 'được', 'vâng', 'ổn', 'phòng thường', 'phòng vip', 'phòng thg'];
    const isConfirmingViaChat = confirmKeywords.some(keyword => textLower.includes(keyword)) && currentServices.length > 0;

    // If confirming via chat, show form for customer to fill info
    if (isConfirmingViaChat) {
      const userMessage = { role: 'user', content: textToSend };
      setMessages([...messages, userMessage]);

      setLoading(true);
      try {
        const historyForBackend = [...messages, userMessage].filter(msg => msg.role && msg.content).map(msg => ({
          role: msg.role,
          content: msg.content
        }));

        // Extract services from chat history
        const res = await fetch('http://127.0.0.1:8000/api/extract-services', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            history: historyForBackend
          }),
        });

        const data = await res.json();
        const extractedServices = data.services || [];

        // Merge button-selected services with chat-extracted services
        const allServices = [...currentServices];

        // Add extracted services that aren't already in button selections
        extractedServices.forEach(extracted => {
          const alreadyExists = currentServices.some(
            btn => btn.name === extracted.name
          );
          if (!alreadyExists) {
            allServices.push(extracted);
          }
        });

        if (allServices.length > 0) {
          // Show form with merged services (buttons + chat mentions)
          setSelectedServices(allServices);
          setShowInfoForm(true);
        } else {
          // No services found anywhere
          alert('Không tìm thấy dịch vụ nào được chọn. Vui lòng chọn hoặc nêu rõ dịch vụ.');
        }
      } catch (error) {
        console.error('Error extracting services:', error);
        alert('Lỗi xử lý. Vui lòng thử lại.');
      } finally {
        setLoading(false);
      }
      return;
    }

    const userMessage = msgHistory ? null : { role: 'user', content: textToSend };
    const newMsgs = msgHistory || [...messages, userMessage];
    if (!msgHistory) setMessages(newMsgs);

    if (!messageText) setInput('');
    setLoading(true);

    try {
      const historyForBackend = newMsgs.filter(msg => msg.role && msg.content).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const res = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          history: historyForBackend,
          selected_services: selectedServices
        }),
      });

      const data = await res.json();
      const botMessage = {
        role: 'assistant',
        content: data.reply
      };

      const updatedMessages = [...newMsgs, botMessage];
      setMessages(updatedMessages);

      // Update services list
      if (data.services) {
        setServices(data.services);
      }

      if (data.order_data) {
        // Show order summary for confirmation
        setOrderSummary(data.order_data);
        setShowOrderConfirm(true);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages([...newMsgs, {
        role: 'assistant',
        content: '❌ Lỗi kết nối. Vui lòng thử lại.'
      }]);
    } finally {
      setLoading(false);
    }
  };


  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleConfirmOrder = () => {
    const confirmMessage = '✅ Em xác nhận chốt đơn này!';
    const userMessage = { role: 'user', content: confirmMessage };
    setMessages([...messages, userMessage]);
    setShowOrderConfirm(false);
    setOrderSummary(null);
    setSelectedServices([]);

    sendMessage(confirmMessage, [...messages, userMessage]);
  };

  const handleCancelOrder = () => {
    const cancelMessage = '❌ Em muốn hủy đơn này';
    setShowOrderConfirm(false);
    setOrderSummary(null);
    setMessages([...messages, { role: 'user', content: cancelMessage }]);
  };

  const handleInfoFormSubmit = async () => {
    if (!customerInfo.name.trim() || !customerInfo.phone.trim() || !customerInfo.petName.trim() || !customerInfo.petType.trim() || !customerInfo.time.trim()) {
      alert('Vui lòng điền đầy đủ thông tin');
      return;
    }

    // Check if any services are selected
    if (selectedServices.length === 0) {
      alert('Vui lòng chọn ít nhất một dịch vụ từ danh sách bên dưới');
      return;
    }

    setShowInfoForm(false);
    setLoading(true);

    try {
      // Calculate total price from selected services
      const totalPrice = selectedServices.reduce((sum, service) => {
        // Extract numeric value before 'k', handling prices like "150k/ngày"
        const match = service.price.match(/(\d+(?:\.\d+)?)\s*k/i);
        const price = match ? parseFloat(match[1]) : 0;
        return sum + price;
      }, 0);

      const orderSummaryData = {
        name: customerInfo.name,
        phone: customerInfo.phone,
        petName: customerInfo.petName,
        petType: customerInfo.petType,
        service: selectedServices.map(s => s.name).join('\n'),
        services: selectedServices,
        time: customerInfo.time,
        price: Math.round(totalPrice * 10) / 10 + 'k'
      };

      setOrderSummary(orderSummaryData);
      setShowOrderConfirm(true);
    } catch (error) {
      console.error('Error:', error);
      alert('Có lỗi xảy ra');
    } finally {
      setLoading(false);
    }
  };

  const handleFinalConfirm = async () => {
    if (!orderSummary) return;

    setLoading(true);

    try {
      const historyForBackend = messages.filter(msg => msg.role && msg.content).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Send order details to backend for processing
      const res = await fetch('http://127.0.0.1:8000/api/confirm-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order: orderSummary,
          history: historyForBackend
        }),
      });

      const data = await res.json();

      if (data.success) {
        const successMessage = {
          role: 'assistant',
          content: data.reply || '✅ Cảm ơn bạn! Đơn hàng đã được xác nhận. Chúng tôi sẽ liên hệ với bạn sớm!'
        };

        // Build service breakdown
        const serviceBreakdown = selectedServices
          .map(s => `  🐕 ${s.name}: ${s.price}`)
          .join('\n');

        const receiptMessage = {
          role: 'assistant',
          content: `📋 HÓA ĐƠN ĐẶT HÀNG\n━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 Khách hàng: ${orderSummary.name}\n📞 SĐT: ${orderSummary.phone}\n🐕 Thú cưng: ${orderSummary.petName} (${orderSummary.petType})\n⏰ Giờ hẹn: ${orderSummary.time}\n\n📌 CHI TIẾT DỊCH VỤ:\n${serviceBreakdown}\n\n💰 TỔNG CỘNG: ${orderSummary.price}\n━━━━━━━━━━━━━━━━━━━━━━━━━\n✨ Cảm ơn bạn đã tin tưởng Pet Lovers Spa!`
        };

        setMessages([...messages, successMessage, receiptMessage]);
        setShowOrderConfirm(false);
        setOrderSummary(null);
        setSelectedServices([]);
        setCustomerInfo({ name: '', phone: '', petName: '', petType: '', time: '' });
      } else {
        alert('Lỗi khi xác nhận đơn hàng: ' + (data.reply || 'Vui lòng thử lại'));
      }
    } catch (error) {
      console.error('Error confirming order:', error);
      alert('Có lỗi xảy ra khi xác nhận đơn hàng. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-wrapper">
        {/* Header */}
        <div className="chat-header">
          <div className="header-left">
            <div className="header-icon">🐾</div>
            <div className="header-info">
              <h2 className="header-title">Pet Lovers Spa</h2>
              <p className="header-status">Mimi Online</p>
            </div>
          </div>

          <button className="logout-button" onClick={onLogout} title="Đăng xuất">
            🚪
          </button>
        </div>

        {/* Messages Area */}
        <div className="messages-area">
          {messages.map((msg, i) => (
            <div key={i} className={`message-wrapper ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}>
              <div className="message-bubble">
                {msg.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-wrapper assistant-message">
              <div className="message-bubble loading-message">
                <span className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Service Selection UI - Always visible except during confirmation */}
        {services && !showOrderConfirm && !showInfoForm && (
          <div className="service-selection">
            {!currentServiceKey ? (
              <>
                <div className="service-title">Chọn dịch vụ:</div>
                <div className="service-buttons">
                  {Object.entries(services).map(([key, service]) => (
                    <button
                      key={key}
                      className="service-btn"
                      onClick={() => handleServiceSelect(key)}
                    >
                      {service.icon} {service.name}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <>
                <div className="service-header">
                  <button className="back-btn" onClick={handleBackToServices}>
                    ← Quay lại
                  </button>
                  <div className="service-title">{services[currentServiceKey]?.name}</div>
                </div>
                <div className="sub-services-list">
                  {services[currentServiceKey]?.sub_services?.map((subService) => (
                    <button
                      key={subService.id}
                      className="sub-service-btn"
                      onClick={() => handleSubServiceSelect(currentServiceKey, subService.id)}
                    >
                      <span className="sub-service-name">{subService.name}</span>
                      <span className="sub-service-price">{subService.price}</span>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Customer Info Form Modal */}
        {showInfoForm && !showOrderConfirm && (
          <div className="order-modal-overlay">
            <div className="order-modal">
              <div className="order-modal-header">📝 Thông Tin Khách Hàng</div>

              {/* Display Selected Services */}
              {selectedServices.length > 0 && (
                <div className="order-details-summary">
                  <div className="summary-item">
                    <span className="summary-label">🛎️ Dịch vụ đã chốt:</span>
                  </div>
                  {selectedServices.map((service, idx) => (
                    <div key={idx} className="summary-item">
                      <span className="summary-label">  • {service.name}</span>
                      <span className="summary-value">{service.price}</span>
                    </div>
                  ))}
                  <div className="summary-item total">
                    <span className="summary-label">💰 Tổng cộng:</span>
                    <span className="summary-value">
                      {Math.round(selectedServices.reduce((sum, s) => {
                        const match = s.price.match(/(\d+(?:\.\d+)?)\s*k/i);
                        return sum + (match ? parseFloat(match[1]) : 0);
                      }, 0) * 10) / 10}k
                    </span>
                  </div>
                </div>
              )}

              <div className="info-form">
                <div className="form-group">
                  <label className="form-label">👤 Tên của bạn</label>
                  <input
                    type="text"
                    className="form-input"
                    value={customerInfo.name}
                    onChange={(e) => setCustomerInfo({ ...customerInfo, name: e.target.value })}
                    placeholder="Nhập tên..."
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">📞 Số điện thoại</label>
                  <input
                    type="tel"
                    className="form-input"
                    value={customerInfo.phone}
                    onChange={(e) => setCustomerInfo({ ...customerInfo, phone: e.target.value })}
                    placeholder="Nhập SĐT..."
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">🐕 Tên thú cưng</label>
                  <input
                    type="text"
                    className="form-input"
                    value={customerInfo.petName}
                    onChange={(e) => setCustomerInfo({ ...customerInfo, petName: e.target.value })}
                    placeholder="Tên của thú cưng..."
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">🐶 Loại thú cưng</label>
                  <input
                    type="text"
                    className="form-input"
                    value={customerInfo.petType}
                    onChange={(e) => setCustomerInfo({ ...customerInfo, petType: e.target.value })}
                    placeholder="VD: Chó, Mèo..."
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">⏰ Giờ hẹn</label>
                  <input
                    type="text"
                    className="form-input"
                    value={customerInfo.time}
                    onChange={(e) => setCustomerInfo({ ...customerInfo, time: e.target.value })}
                    placeholder="VD: 14:00 Chiều nay"
                  />
                </div>
              </div>
              <div className="order-modal-actions">
                <button className="btn-confirm" onClick={handleInfoFormSubmit}>
                  ✅ Tiếp Tục
                </button>
                <button className="btn-cancel" onClick={() => setShowInfoForm(false)}>
                  ❌ Hủy
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Order Confirmation Modal */}
        {showOrderConfirm && orderSummary && (
          <div className="order-modal-overlay">
            <div className="order-modal">
              <div className="order-modal-header">📋 Xác Nhận Đơn Hàng</div>
              <div className="order-details-summary">
                <div className="summary-item">
                  <span className="summary-label">👤 Tên:</span>
                  <span className="summary-value">{orderSummary.name}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">📞 SĐT:</span>
                  <span className="summary-value">{orderSummary.phone}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">🐕 Thú cưng:</span>
                  <span className="summary-value">{orderSummary.petName} ({orderSummary.petType})</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">🛎️ Dịch vụ:</span>
                  <span className="summary-value services-list">
                    {orderSummary.services?.map((service, idx) => (
                      <div key={idx}>• {service.name}</div>
                    ))}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">⏰ Giờ hẹn:</span>
                  <span className="summary-value">{orderSummary.time}</span>
                </div>
                <div className="summary-item total">
                  <span className="summary-label">💰 Tổng giá:</span>
                  <span className="summary-value">{orderSummary.price}</span>
                </div>
              </div>
              <div className="order-modal-actions">
                <button className="btn-confirm" onClick={handleFinalConfirm} disabled={loading}>
                  {loading ? '⏳ Đang xử lý...' : '✅ Xác Nhận'}
                </button>
                <button className="btn-cancel" onClick={handleCancelOrder} disabled={loading}>
                  ❌ Hủy
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Input Area */}
        {!showOrderConfirm && !showInfoForm && (
          <div className="input-area">
            <textarea
              className="message-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Nhập tin nhắn của bạn..."
              disabled={loading}
              rows="1"
            />

            <button
              className="send-button"
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              title="Gửi tin nhắn"
            >
              {loading ? '...' : '➤'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
