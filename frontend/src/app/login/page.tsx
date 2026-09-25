'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import api from '@/lib/api';
import { Icons } from '@/components/icons';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('admin@acmeglobal.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const { data } = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen gradient-navy flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 25% 25%, rgba(224, 190, 98, 0.1) 0%, transparent 50%),
                           radial-gradient(circle at 75% 75%, rgba(29, 78, 216, 0.1) 0%, transparent 50%)`
        }}></div>
      </div>

      <div className="relative z-10 w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-white rounded-2xl shadow-xl mb-6">
            <span className="text-4xl font-bold text-ink">P</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">PayPilot Global</h1>
          <div className="flex items-center justify-center gap-3 mt-4">
            <div className="h-px w-12 bg-gold"></div>
            <span className="text-gold-text text-sm font-semibold uppercase tracking-wider">
              Enterprise Payroll
            </span>
            <div className="h-px w-12 bg-gold"></div>
          </div>
        </div>

        {/* Login Card */}
        <Card className="shadow-2xl">
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-ink mb-1">Welcome back</h2>
              <p className="text-sm text-text-muted">Sign in to your payroll dashboard</p>
            </div>

            {error && (
              <div className="bg-danger-bg border border-danger/20 rounded-lg p-3 flex items-center gap-2">
                <Icons.alert className="text-danger" size={16} />
                <p className="text-sm text-danger">{error}</p>
              </div>
            )}

            <Input
              label="Email address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@acmeglobal.com"
              required
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />

            <Button type="submit" className="w-full" size="lg" isLoading={loading}>
              Sign In
            </Button>

            <div className="gold-line my-6"></div>

            <div className="text-center space-y-2">
              <p className="text-xs text-text-muted font-semibold uppercase tracking-wider">
                Demo Credentials
              </p>
              <div className="bg-canvas-subtle rounded-lg p-3 text-left">
                <p className="text-2xs text-text-muted">Admin</p>
                <p className="text-xs text-ink font-mono">admin@acmeglobal.com</p>
              </div>
            </div>
          </form>
        </Card>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-blue-200/50 text-xs">
            Secured by BMONI Embedded · Bank-grade encryption
          </p>
        </div>
      </div>
    </div>
  );
}
