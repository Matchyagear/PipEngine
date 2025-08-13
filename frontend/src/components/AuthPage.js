import React, { useState } from 'react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const AuthPage = ({ onAuth }) => {
  const [mode, setMode] = useState('login'); // 'login' | 'register' | 'reset'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === 'reset') {
        alert('Password reset email would be sent here (backend email provider required).');
        return;
      }
      const resp = await fetch(`${API_BASE_URL}/api/auth/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await resp.json();
      if (!resp.ok) {
        alert(data.detail || 'Authentication failed');
        return;
      }
      onAuth(data, { remember });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
          {mode === 'login' ? 'Login' : mode === 'register' ? 'Create Account' : 'Reset Password'}
        </h2>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm mb-1 text-gray-700 dark:text-gray-300">Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required className="w-full border rounded px-3 py-2 bg-white dark:bg-gray-700" />
          </div>
          {mode !== 'reset' && (
            <div>
              <label className="block text-sm mb-1 text-gray-700 dark:text-gray-300">Password</label>
              <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required className="w-full border rounded px-3 py-2 bg-white dark:bg-gray-700" />
            </div>
          )}
          {mode !== 'reset' && (
            <label className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-300">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
              <span>Remember me</span>
            </label>
          )}
          <button disabled={loading} className={`w-full py-2 rounded text-white ${loading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'}`}>
            {loading ? 'Please wait…' : mode === 'login' ? 'Login' : mode === 'register' ? 'Sign up' : 'Send reset link'}
          </button>
        </form>
        <div className="flex justify-between text-sm mt-4">
          <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')} className="text-blue-600">{mode === 'login' ? 'Create account' : 'Have an account? Login'}</button>
          <button onClick={() => setMode('reset')} className="text-blue-600">Forgot password?</button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;


