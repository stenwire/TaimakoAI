'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Mail, Lock, User, AlertCircle } from 'lucide-react';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

export default function SignupPage() {
  const router = useRouter();
  const { signup } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError('');

    if (!validateForm()) return;

    setLoading(true);
    try {
      await signup(formData);
    } catch (error: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const err = error as any;
      setApiError(err.response?.data?.message || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FAFBFC] via-[#FFFFFF] to-[#F5F7F9] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="mb-4">
              <Image
                src="/logo.png"
                alt="Taimako Logo"
                width={64}
                height={64}
                className="w-16 h-16"
              />
            </div>
            <span className="text-h1 text-[var(--text-primary)]">Taimako</span>
          </div>
          <h1 className="text-h2 text-[var(--text-primary)] mb-2">Create your account</h1>
          <p className="text-small text-[var(--text-secondary)]">
            Start building your AI-powered customer experience
          </p>
        </div>

        {/* Signup Form */}
        <div className="attio-card">
          <div className="p-6">
            {apiError && (
              <div className="mb-4 p-3 bg-[var(--error-bg)] border border-[var(--error)] rounded-[var(--radius-sm)] flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-[var(--error)] flex-shrink-0 mt-0.5" />
                <p className="text-small text-[var(--error)]">{apiError}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <User className="absolute left-3 top-[38px] w-5 h-5 text-[var(--text-tertiary)]" />
                <Input
                  label="Full Name"
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  error={errors.name}
                  className="pl-10"
                />
              </div>

              <div className="relative">
                <Mail className="absolute left-3 top-[38px] w-5 h-5 text-[var(--text-tertiary)]" />
                <Input
                  label="Email"
                  type="email"
                  placeholder="you@company.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  error={errors.email}
                  className="pl-10"
                />
              </div>

              <div className="relative">
                <Lock className="absolute left-3 top-[38px] w-5 h-5 text-[var(--text-tertiary)]" />
                <Input
                  label="Password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  error={errors.password}
                  className="pl-10"
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                loading={loading}
                disabled={loading}
              >
                Create Account
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-small text-[var(--text-secondary)]">
                Already have an account?{' '}
                <Link
                  href="/auth/login"
                  className="text-[var(--brand-primary)] hover:text-[var(--brand-primary-hover)] font-medium transition-colors"
                >
                  Log in
                </Link>
              </p>
            </div>
          </div>
        </div>

        {/* Back to Home */}
        <div className="mt-6 text-center">
          <button
            onClick={() => router.push('/')}
            className="text-small text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
          >
            ← Back to home
          </button>
        </div>
      </motion.div>
    </div>
  );
}
