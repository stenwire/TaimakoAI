'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Building2, Save, Edit2, AlertCircle, CheckCircle } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import { getBusinessProfile, createBusinessProfile, updateBusinessProfile } from '@/lib/api';
import { useBusiness } from '@/contexts/BusinessContext';
import type { BusinessProfile, CreateBusinessProfileData } from '@/lib/types';

export default function BusinessProfilePage() {
  const [profile, setProfile] = useState<BusinessProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [personality, setPersonality] = useState('custom');

  // Get the refresh function from context to update global API key state
  const { refreshBusinessProfile } = useBusiness();

  const [formData, setFormData] = useState<CreateBusinessProfileData>({
    business_name: '',
    description: '',
    website: '',
    custom_agent_instruction: '',
    logo_url: '',
    gemini_api_key: ''
  });

  const personalityPresets = {
    professional: "You represent {business_name}. Be polite, concise, and professional. Focus on accuracy and provide clear answers based on the knowledge base.",
    sales: "You are a sales assistant for {business_name}. Your goal is to convert leads. Be persuasive, enthusiastic, and proactive in asking for contact details if the user shows interest.",
    support: "You are a support agent for {business_name}. Be empathetic, patient, and solution-oriented. Apologize for issues and guide the user step-by-step.",
    custom: ""
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const response = await getBusinessProfile();
      // Backend now returns success with data: null if not found
      if (response.data) {
        setProfile(response.data);
        setFormData({
          business_name: response.data.business_name,
          description: response.data.description,
          website: response.data.website,
          custom_agent_instruction: response.data.custom_agent_instruction,
          logo_url: response.data.logo_url || '',
          gemini_api_key: '' // Never return API key
        });
      } else {
        // No profile found, start in edit mode
        setEditing(true);
      }
    } catch (error: unknown) {
      console.error(error);
      // Fallback for legacy 404 behavior if any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const err = error as any;
      if (err.response?.status === 404) {
        setEditing(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePersonalityChange = (key: string) => {
    setPersonality(key);
    if (key !== 'custom') {
      const template = personalityPresets[key as keyof typeof personalityPresets].replace('{business_name}', formData.business_name || 'our business');
      setFormData(prev => ({ ...prev, custom_agent_instruction: template }));
    }
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');
    setSaving(true);

    try {
      if (profile) {
        const response = await updateBusinessProfile(formData);
        setProfile(response.data!);
        setSuccess('Business profile updated successfully!');
      } else {
        const response = await createBusinessProfile(formData);
        setProfile(response.data!);
        setSuccess('Business profile created successfully!');
      }
      setEditing(false);
      // Refresh local profile data
      await fetchProfile();
      // Refresh global context to update sidebar/lockout state immediately
      await refreshBusinessProfile();
      setTimeout(() => setSuccess(''), 3000);
    } catch (error: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const err = error as any;
      setError(err.response?.data?.message || 'Failed to save business profile');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (profile) {
      setFormData({
        business_name: profile.business_name,
        description: profile.description,
        website: profile.website,
        custom_agent_instruction: profile.custom_agent_instruction,
        logo_url: profile.logo_url || '',
        gemini_api_key: ''
      });
      setEditing(false);
    }
    setError('');
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <SkeletonLoader variant="rectangle" className="h-32" />
        <SkeletonLoader variant="text" count={5} />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="p-3 bg-[var(--brand-primary)]/10 rounded-[var(--radius-squircle)]">
            <Building2 className="w-8 h-8 text-[var(--brand-primary)]" />
          </div>
          <div>
            <h1 className="text-h1 text-[var(--text-primary)]">Business Profile</h1>
            <p className="text-body text-[var(--text-secondary)] mt-1">
              Configure your business details and AI agent behavior
            </p>
          </div>
        </div>
        {profile && !editing && (
          <Button variant="secondary" onClick={() => setEditing(true)}>
            <Edit2 className="w-4 h-4" />
            Edit
          </Button>
        )}
      </motion.div>

      {/* Notifications */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-[var(--error-bg)] border border-[var(--error)] rounded-[var(--radius-md)] flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 text-[var(--error)] flex-shrink-0 mt-0.5" />
          <p className="text-small text-[var(--error)]">{error}</p>
        </motion.div>
      )}

      {success && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-[var(--success-bg)] border border-[var(--success)] rounded-[var(--radius-md)] flex items-start gap-3"
        >
          <CheckCircle className="w-5 h-5 text-[var(--success)] flex-shrink-0 mt-0.5" />
          <p className="text-small text-[var(--success)]">{success}</p>
        </motion.div>
      )}

      {/* Profile Form */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <Card>
          <div className="space-y-8">
            {/* Business Details Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-space font-semibold text-[var(--brand-primary)] border-b border-[var(--border-subtle)] pb-2">Business Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Business Name"
                  placeholder="Acme Support"
                  value={formData.business_name}
                  onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                  disabled={!editing}
                />
                <Input
                  label="Website"
                  type="url"
                  placeholder="https://acme.com"
                  value={formData.website}
                  onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                  disabled={!editing}
                />
              </div>

              {/* Logo URL and API Key Row - Aligned */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Logo URL"
                  type="url"
                  placeholder="https://acme.com/logo.png"
                  value={formData.logo_url || ''}
                  onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                  disabled={!editing}
                />

                {/* API Key Input + Validation */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-[var(--text-secondary)] text-[13px] font-medium">
                      Google Gemini API Key
                    </label>
                    {profile?.is_api_key_set && !editing && (
                      <span className="text-[12px] font-medium text-green-600 bg-green-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Key Set
                      </span>
                    )}
                    {(!profile || !profile.is_api_key_set) && !editing && (
                      <span className="text-[12px] font-medium text-red-600 bg-red-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> Not Set
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="flex-1">
                      <input
                        type="password"
                        placeholder={profile?.is_api_key_set && !editing ? "••••••••••••••••" : "AIzaSy..."}
                        value={formData.gemini_api_key || ''}
                        onChange={(e) => setFormData({ ...formData, gemini_api_key: e.target.value })}
                        disabled={!editing}
                        className="w-full px-3 py-2 text-[14px] bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-sm)] placeholder:text-[var(--text-tertiary)] focus-ring transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
                      />
                    </div>

                    {/* Test Button with Spinner */}
                    {editing && (
                      <Button
                        onClick={async () => {
                          const key = formData.gemini_api_key;
                          if (!key) {
                            setError("Please enter a key to test");
                            return;
                          }
                          setTesting(true);
                          setError('');
                          try {
                            const { validateApiKey } = await import('@/lib/api');
                            await validateApiKey(key);
                            setSuccess("API Key is valid!");
                            setTimeout(() => setSuccess(''), 3000);
                          } catch (e) {
                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                            const err = e as any;
                            setError(`Invalid Key: ${err.response?.data?.detail || err.message}`);
                          } finally {
                            setTesting(false);
                          }
                        }}
                        type="button"
                        variant="secondary"
                        className="h-[38px]"
                        disabled={!formData.gemini_api_key || testing}
                        loading={testing}
                      >
                        {testing ? '' : 'Test'}
                      </Button>
                    )}
                  </div>
                  <p className="text-[11px] text-[var(--text-tertiary)] mt-1">
                    Required for the AI agent to function.
                  </p>
                </div>
              </div>
              <div>
                <label className="block text-[var(--text-secondary)] text-[13px] font-medium mb-2">
                  Description
                </label>
                <textarea
                  placeholder="Customer support for Acme products"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  disabled={!editing}
                  rows={3}
                  className="w-full px-3 py-2 text-[14px] bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-sm)] placeholder:text-[var(--text-tertiary)] focus-ring transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
                />
              </div>
            </div>

            {/* Agent Configuration Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-space font-semibold text-[var(--brand-primary)] border-b border-[var(--border-subtle)] pb-2 flex justify-between items-center">
                Agent Configuration
                {editing && (
                  <div className="flex gap-2">
                    {['professional', 'sales', 'support'].map(p => (
                      <button
                        key={p}
                        onClick={() => handlePersonalityChange(p)}
                        className={`px-3 py-1 text-xs rounded-full border transition-all ${personality === p ? 'bg-[var(--brand-primary)] text-white border-[var(--brand-primary)]' : 'border-[var(--border-strong)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'}`}
                      >
                        {p.charAt(0).toUpperCase() + p.slice(1)} Mode
                      </button>
                    ))}
                  </div>
                )}
              </h3>

              <div>
                <label className="block text-[var(--text-secondary)] text-[13px] font-medium mb-2">
                  Custom Agent Instructions
                </label>
                <textarea
                  placeholder="Always be professional and mention our 24/7 support availability..."
                  value={formData.custom_agent_instruction}
                  onChange={(e) => {
                    setFormData({ ...formData, custom_agent_instruction: e.target.value });
                    setPersonality('custom');
                  }}
                  disabled={!editing}
                  rows={6}
                  className="w-full px-3 py-2 text-[14px] bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-sm)] placeholder:text-[var(--text-tertiary)] focus-ring transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed font-mono text-xs"
                />
                <p className="text-[12px] text-[var(--text-tertiary)] mt-2">
                  These instructions will override default behaviors. Select a mode above to start with a template.
                </p>
              </div>
            </div>

            {editing && (
              <div className="flex gap-3 pt-4 border-t border-[var(--border-subtle)]">
                <Button
                  variant="primary"
                  onClick={handleSave}
                  loading={saving}
                  disabled={saving}
                  className="flex-1"
                >
                  <Save className="w-4 h-4" />
                  {profile ? 'Save Changes' : 'Create Profile'}
                </Button>
                {profile && (
                  <Button
                    variant="secondary"
                    onClick={handleCancel}
                    disabled={saving}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                )}
              </div>
            )}
          </div>
        </Card>
      </motion.div>
    </div>
  );
}
