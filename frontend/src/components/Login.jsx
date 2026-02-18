import React from 'react';
import { signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '../firebase';

function Login() {
  const handleLogin = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (error) {
      console.error("Login failed:", error);
      alert("Login failed. Check console.");
    }
  };

  return (
    <div className="login-container" style={{ textAlign: "center", marginTop: "100px" }}>
      <h1>🎓 LMS Capstone</h1>
      <p>Sign in to access your dashboard</p>
      <button 
        onClick={handleLogin} 
        style={{ 
          padding: "12px 24px", 
          fontSize: "16px", 
          cursor: "pointer", 
          backgroundColor: "#4285F4", 
          color: "white", 
          border: "none", 
          borderRadius: "5px" 
        }}
      >
        Sign in with Google
      </button>
    </div>
  );
}

export default Login;