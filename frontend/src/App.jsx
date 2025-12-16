import { useState } from 'react'
import Login from './components/Login'
import AdminDashboard from './components/AdminDashboard'
import CustomerChat from './components/CustomerChat'
import './App.css'

function App() {
  const [role, setRole] = useState(null)

  const handleLogin = (userRole) => {
    setRole(userRole)
  }

  const handleLogout = () => {
    setRole(null)
  }

  return (
    <>
      {!role ? (
        <Login onLogin={handleLogin} />
      ) : role === 'admin' ? (
        <AdminDashboard onLogout={handleLogout} />
      ) : (
        <CustomerChat onLogout={handleLogout} />
      )}
    </>
  )
}

export default App
