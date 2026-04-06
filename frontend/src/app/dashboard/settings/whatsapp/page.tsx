'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, Save, AlertCircle, CheckCircle, Copy, Check, ExternalLink } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import { getAccessToken } from '@/lib/api';
import { BACKEND_URL } from '@/config';

interface WhatsAppSettings {
  whatsapp_enabled: boolean;
  whatsapp_number: string;
  whatsapp_phone_number_id: string;
  whatsapp_business_account_id: string;
  whatsapp_access_token: string;
  whatsapp_api_configured: boolean;
}

export default function WhatsAppSettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [copied, setCopied] = useState(false);

  const [formData, setFormData] = useState<WhatsAppSettings>({
    whatsapp_enabled: false,
    whatsapp_number: '',
    whatsapp_phone_number_id: '',
    whatsapp_business_account_id: '',
    whatsapp_access_token: '',
    whatsapp_api_configured: false,
  });

  const webhookUrl = `${BACKEND_URL}/whatsapp/webhook`;

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = getAccessToken();
      const res = await fetch(`${BACKEND_URL}/widgets/my-settings`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const responseData = await res.json();
        const data = responseData.data;
        setFormData({
          whatsapp_enabled: data.whatsapp_enabled || false,
          whatsapp_number: data.whatsapp_number || '',
          whatsapp_phone_number_id: data.whatsapp_phone_number_id || '',
          whatsapp_business_account_id: data.whatsapp_business_account_id || '',
          whatsapp_access_token: '',
          whatsapp_api_configured: data.whatsapp_api_configured || false,
        });
      }
    } catch (err) {
      console.error('Failed to load settings', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');
    setSaving(true);

    try {
      const token = getAccessToken();
      const body: Record<string, unknown> = {
        whatsapp_enabled: formData.whatsapp_enabled,
        whatsapp_number: formData.whatsapp_number,
        whatsapp_phone_number_id: formData.whatsapp_phone_number_id,
        whatsapp_business_account_id: formData.whatsapp_business_account_id,
      };

      // Only send access token if user entered a new one
      if (formData.whatsapp_access_token) {
        body.whatsapp_access_token = formData.whatsapp_access_token;
      }

      const res = await fetch(`${BACKEND_URL}/widgets/my-settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const responseData = await res.json();
        const data = responseData.data;
        setFormData((prev) => ({
          ...prev,
          whatsapp_api_configured: data.whatsapp_api_configured || false,
          whatsapp_access_token: '',
        }));
        setSuccess('WhatsApp settings saved successfully!');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Failed to save settings');
      }
    } catch {
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const copyWebhookUrl = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
        className="flex items-center gap-3"
      >
        <div className="p-3 bg-green-500/10 rounded-[var(--radius-squircle)]">
          <MessageSquare className="w-8 h-8 text-green-600" />
        </div>
        <div>
          <h1 className="text-h1 text-[var(--text-primary)]">WhatsApp Integration</h1>
          <p className="text-body text-[var(--text-secondary)] mt-1">
            Connect your WhatsApp Business number to receive and reply to messages with AI
          </p>
        </div>
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

      {/* Enable Toggle */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <Card>
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-space font-semibold text-[var(--text-primary)]">
                  WhatsApp Channel
                </h3>
                <p className="text-sm text-[var(--text-secondary)] mt-1">
                  Enable to process incoming WhatsApp messages through your AI agent
                </p>
              </div>
              <button
                onClick={() =>
                  setFormData((prev) => ({ ...prev, whatsapp_enabled: !prev.whatsapp_enabled }))
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  formData.whatsapp_enabled ? 'bg-green-500' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    formData.whatsapp_enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {formData.whatsapp_api_configured && (
              <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-3 rounded-[var(--radius-sm)]">
                <CheckCircle className="w-4 h-4" />
                <span>WhatsApp API credentials are configured</span>
              </div>
            )}
          </div>
        </Card>
      </motion.div>

      {/* Webhook URL */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.15 }}
      >
        <Card>
          <div className="space-y-4">
            <h3 className="text-lg font-space font-semibold text-[var(--brand-primary)] border-b border-[var(--border-subtle)] pb-2">
              Webhook Configuration
            </h3>
            <p className="text-sm text-[var(--text-secondary)]">
              Use this URL in your{' '}
              <span className="font-medium text-[var(--text-primary)]">
                Meta Developer Dashboard
              </span>{' '}
              as the webhook callback URL.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-[var(--radius-sm)] text-sm font-mono text-[var(--text-primary)] overflow-x-auto">
                {webhookUrl}
              </code>
              <Button variant="secondary" onClick={copyWebhookUrl} className="flex-shrink-0">
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* API Credentials */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <Card>
          <div className="space-y-4">
            <h3 className="text-lg font-space font-semibold text-[var(--brand-primary)] border-b border-[var(--border-subtle)] pb-2">
              WhatsApp API Credentials
            </h3>

            <Input
              label="WhatsApp Phone Number"
              placeholder="+234XXXXXXXXXX"
              value={formData.whatsapp_number}
              onChange={(e) => setFormData({ ...formData, whatsapp_number: e.target.value })}
            />

            <Input
              label="Phone Number ID"
              placeholder="From Meta Developer Dashboard"
              value={formData.whatsapp_phone_number_id}
              onChange={(e) =>
                setFormData({ ...formData, whatsapp_phone_number_id: e.target.value })
              }
            />

            <Input
              label="Business Account ID"
              placeholder="WhatsApp Business Account ID"
              value={formData.whatsapp_business_account_id}
              onChange={(e) =>
                setFormData({ ...formData, whatsapp_business_account_id: e.target.value })
              }
            />

            <Input
              label="Permanent Access Token"
              type="password"
              placeholder={
                formData.whatsapp_api_configured
                  ? 'Token saved. Enter a new value to update.'
                  : 'Paste your permanent access token'
              }
              value={formData.whatsapp_access_token}
              onChange={(e) =>
                setFormData({ ...formData, whatsapp_access_token: e.target.value })
              }
            />

            <p className="text-xs text-[var(--text-tertiary)]">
              The access token is write-only and will not be displayed after saving.
            </p>
          </div>
        </Card>
      </motion.div>

      {/* Setup Instructions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.25 }}
      >
        <Card>
          <div className="space-y-3">
            <h3 className="text-lg font-space font-semibold text-[var(--brand-primary)] border-b border-[var(--border-subtle)] pb-2">
              Setup Instructions
            </h3>
            <ol className="list-decimal list-inside space-y-2 text-sm text-[var(--text-secondary)]">
              <li>
                Go to the{' '}
                <span className="font-medium text-[var(--text-primary)]">
                  Meta Developer Dashboard
                </span>{' '}
                and create or select your app
              </li>
              <li>Add the WhatsApp product to your app</li>
              <li>
                Under <strong>WhatsApp &gt; Configuration</strong>, set the webhook callback URL to
                the URL shown above
              </li>
              <li>
                Set the verify token to the value configured in your backend environment (
                <code className="text-xs bg-[var(--bg-secondary)] px-1 py-0.5 rounded">
                  WHATSAPP_VERIFY_TOKEN
                </code>
                )
              </li>
              <li>Subscribe to the <strong>messages</strong> webhook field</li>
              <li>
                Copy your Phone Number ID, Business Account ID, and permanent access token into the
                fields above
              </li>
              <li>Enable the WhatsApp channel toggle and save</li>
            </ol>
          </div>
        </Card>
      </motion.div>

      {/* Save Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <Button
          variant="primary"
          onClick={handleSave}
          loading={saving}
          disabled={saving}
          className="w-full"
        >
          <Save className="w-4 h-4" />
          Save WhatsApp Settings
        </Button>
      </motion.div>
    </div>
  );
}
