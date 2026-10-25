import React, { useState } from 'react';
import { Activity, ArrowRight, Eye, EyeOff, LockKeyhole, Mail, ShieldCheck } from 'lucide-react';
import { login, register } from '../api';

export default function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    if (mode === 'register' && password !== confirmPassword) {
      setError('Those passwords do not match.');
      return;
    }
    if (password.length < 8) {
      setError('Use at least 8 characters for your password.');
      return;
    }
    setBusy(true);
    try {
      const response = mode === 'login'
        ? await login(email.trim(), password)
        : await register(email.trim(), password);
      const data = response.data;
      localStorage.setItem('alphaforge_token', data.access_token);
      localStorage.setItem('alphaforge_user', JSON.stringify(data.user));
      onAuthenticated(data.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not connect to AlphaForge. Check that the API is running and try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-orbit auth-orbit-one" />
      <div className="auth-orbit auth-orbit-two" />
      <section className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-mark"><Activity size={23} strokeWidth={2.5} /></div>
          <div><span>AlphaForge</span><b>AI</b><small>INVESTMENT INTELLIGENCE</small></div>
        </div>
        <div className="auth-eyebrow"><span className="auth-live-dot" /> PRIVATE RESEARCH WORKSPACE</div>
        <h1>{mode === 'login' ? 'Good to have you back.' : 'Build your edge.'}</h1>
        <p className="auth-subtitle">{mode === 'login' ? 'Sign in to pick up where your research left off.' : 'Create an account for your own watchlist, strategies, and research history.'}</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label htmlFor="auth-email">Email address</label>
          <div className="auth-input-wrap"><Mail size={18} /><input id="auth-email" type="email" autoComplete="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required maxLength={320} /></div>
          <div className="auth-label-row"><label htmlFor="auth-password">Password</label>{mode === 'register' && <span>8+ characters</span>}</div>
          <div className="auth-input-wrap"><LockKeyhole size={18} /><input id="auth-password" type={showPassword ? 'text' : 'password'} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder="Enter your password" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} maxLength={128} /><button className="auth-show-password" type="button" onClick={() => setShowPassword(v => !v)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>
          {mode === 'register' && <><label htmlFor="auth-confirm">Confirm password</label><div className="auth-input-wrap"><LockKeyhole size={18} /><input id="auth-confirm" type={showPassword ? 'text' : 'password'} autoComplete="new-password" placeholder="Enter it one more time" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required minLength={8} maxLength={128} /></div></>}
          {error && <div className="auth-error" role="alert">{error}</div>}
          <button className="auth-submit" type="submit" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in securely' : 'Create account'} {!busy && <ArrowRight size={18} />}</button>
        </form>
        <div className="auth-switch">{mode === 'login' ? "New to AlphaForge?" : 'Already have an account?'} <button type="button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></div>
        <div className="auth-security"><ShieldCheck size={16} /><span>Your workspace is private. Passwords are securely hashed and sessions expire after 7 days.</span></div>
      </section>
      <div className="auth-footer"><span>ALPHAFORGE AI</span><span>Research smarter. Decide with evidence.</span></div>
    </div>
  );
}
