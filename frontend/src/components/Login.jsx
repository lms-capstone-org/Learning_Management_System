import React, { useState } from 'react';
import { signInWithPopup, signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { auth, googleProvider } from '../firebase';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (err) {
      setError("Google login failed. Try again.");
    }
  };

  const handleEmailAuth = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        await createUserWithEmailAndPassword(auth, email, password);
      } else {
        await signInWithEmailAndPassword(auth, email, password);
      }
    } catch (err) {
      // Firebase error codes
      if (err.code === 'auth/user-not-found' 
          || err.code === 'auth/wrong-password'
          || err.code === 'auth/invalid-credential') {
        setError("Invalid email or password.");
      } else if (err.code === 'auth/email-already-in-use') {
        setError("Email already registered. Please login.");
      } else if (err.code === 'auth/weak-password') {
        setError("Password must be at least 6 characters.");
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: '#f3f4f6'
    }}>
      <div style={{
        background: 'white',
        padding: '2.5rem',
        borderRadius: '12px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        width: '100%',
        maxWidth: '400px'
      }}>
        <h1 style={{ textAlign: 'center', marginBottom: '0.5rem' }}>🎓 LMS</h1>
        <p style={{ textAlign: 'center', color: '#6b7280', marginBottom: '2rem' }}>
          {isRegister ? 'Create your account' : 'Sign in to continue'}
        </p>

        {/* Email/Password Form */}
        <form onSubmit={handleEmailAuth}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.4rem', fontWeight: 500 }}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
              style={{
                width: '100%', padding: '0.6rem 0.8rem', border: '1px solid #d1d5db',
                borderRadius: '6px', fontSize: '1rem', boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.4rem', fontWeight: 500 }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Min. 6 characters"
              style={{
                width: '100%', padding: '0.6rem 0.8rem', border: '1px solid #d1d5db',
                borderRadius: '6px', fontSize: '1rem', boxSizing: 'border-box'
              }}
            />
          </div>

          {error && (
            <p style={{ color: '#ef4444', fontSize: '0.875rem', marginBottom: '1rem' }}>
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '0.75rem', background: '#4f46e5', color: 'white',
              border: 'none', borderRadius: '6px', fontSize: '1rem', cursor: 'pointer',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        {/* Toggle Register/Login */}
        <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
          {isRegister ? 'Already have an account?' : "Don't have an account?"}
          <button
            onClick={() => { setIsRegister(!isRegister); setError(''); }}
            style={{
              background: 'none', border: 'none', color: '#4f46e5',
              cursor: 'pointer', fontWeight: 600, marginLeft: '4px'
            }}
          >
            {isRegister ? 'Sign In' : 'Register'}
          </button>
        </p>

        {/* Divider */}
        <div style={{ display: 'flex', alignItems: 'center', margin: '1.5rem 0' }}>
          <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #e5e7eb' }} />
          <span style={{ padding: '0 0.75rem', color: '#9ca3af', fontSize: '0.875rem' }}>OR</span>
          <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #e5e7eb' }} />
        </div>

        {/* Google Login */}
        <button
          onClick={handleGoogleLogin}
          style={{
            width: '100%', padding: '0.75rem', background: 'white', color: '#374151',
            border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '1rem',
            cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
          }}
        >
          <svg width="18" height="18" viewBox="0 0 48 48">
            <path fill="#4285F4" d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z" />
          </svg>
          Continue with Google
        </button>
      </div>
    </div>
  );
}

export default Login;