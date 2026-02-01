'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Users, Flag, Plus, CheckCircle2, Search, MessageSquare, Clock, X, Mail } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Tabs from '@/components/ui/Tabs';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import { getBusinessProfile, getEscalations, updateBusinessProfile } from '@/lib/api';
import { useToast } from '@/contexts/ToastContext';
import type { Escalation } from '@/lib/types';



export default function HandoffPage() {
  const router = useRouter();
  const { success, error: toastError } = useToast();


  // Escalation List State
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loadingEscalations, setLoadingEscalations] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Configuration State


  // Escalation Settings State (moved from business settings)
  const [isEscalationEnabled, setIsEscalationEnabled] = useState(false);
  const [escalationEmails, setEscalationEmails] = useState<string[]>([]);
  const [newEmail, setNewEmail] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchBusinessAndEscalations();
  }, []);

  const fetchBusinessAndEscalations = async () => {
    try {
      setLoadingEscalations(true);
      const profileRes = await getBusinessProfile();
      if (profileRes.data?.id) {

        setIsEscalationEnabled(profileRes.data.is_escalation_enabled || false);
        setEscalationEmails(profileRes.data.escalation_emails || []);
        const escRes = await getEscalations(profileRes.data.id);
        setEscalations(escRes || []);
      }
    } catch (error) {
      console.error("Failed to load data", error);
    } finally {
      setLoadingEscalations(false);
    }
  };

  const handleSaveConfig = async () => {
    setSaving(true);
    try {
      await updateBusinessProfile({
        is_escalation_enabled: isEscalationEnabled,
        escalation_emails: escalationEmails
      });
      success("Configuration saved successfully!");
    } catch (e) {
      toastError("Failed to save configuration");
    } finally {
      setSaving(false);
    }
  };

  const addEmail = () => {
    if (newEmail && !escalationEmails.includes(newEmail)) {
      // Basic email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (emailRegex.test(newEmail)) {
        setEscalationEmails([...escalationEmails, newEmail]);
        setNewEmail('');
      } else {
        toastError("Please enter a valid email address");
      }
    }
  };

  const removeEmail = (email: string) => {
    setEscalationEmails(escalationEmails.filter(e => e !== email));
  };

  // Rule management


  // Filtered escalations
  const filteredEscalations = escalations.filter(e => {
    if (filterStatus === 'all') return true;
    return e.status === filterStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'resolved': return 'text-green-600 bg-green-50 border-green-200';
      case 'in_progress': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'pending': return 'text-amber-600 bg-amber-50 border-amber-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const handleEscalationClick = (escalationId: string) => {
    router.push(`/dashboard/handoff/${escalationId}`);
  };

  const RequestsView = (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-4 md:items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--text-tertiary)] w-4 h-4" />
          <input
            type="text"
            placeholder="Search escalations..."
            className="w-full pl-10 pr-4 py-2 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-md)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]/20"
          />
        </div>
        <div className="flex gap-2">
          <select
            className="flex-1 md:flex-none bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-md)] px-3 py-2 text-sm focus:outline-none"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
          <Button variant="secondary" onClick={fetchBusinessAndEscalations} className="flex-1 md:flex-none justify-center">
            Refresh
          </Button>
        </div>
      </div>

      {loadingEscalations ? (
        <div className="space-y-4">
          <SkeletonLoader variant="rectangle" className="h-24" />
          <SkeletonLoader variant="rectangle" className="h-24" />
          <SkeletonLoader variant="rectangle" className="h-24" />
        </div>
      ) : filteredEscalations.length === 0 ? (
        <div className="text-center py-12 px-4 rounded-[var(--radius-lg)] border-2 border-dashed border-[var(--border-subtle)]">
          <div className="w-12 h-12 bg-[var(--bg-tertiary)] rounded-full flex items-center justify-center mx-auto mb-3">
            <CheckCircle2 className="w-6 h-6 text-[var(--text-tertiary)]" />
          </div>
          <h3 className="text-lg font-medium text-[var(--text-primary)]">No escalations found</h3>
          <p className="text-[var(--text-secondary)]">Good job! Everything seems to be running smoothly.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredEscalations.map((esc) => (
            <motion.div
              key={esc.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-md)] p-4 hover:shadow-sm transition-shadow cursor-pointer"
              onClick={() => handleEscalationClick(esc.id)}
            >
              <div className="flex justify-between items-start">
                <div className="flex gap-3">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${esc.sentiment === 'negative' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'}`}>
                    <Flag className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-medium text-[var(--text-primary)]">{esc.summary || "No summary available"}</h3>
                    <div className="flex items-center gap-3 mt-1 text-xs text-[var(--text-tertiary)]">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(esc.created_at).toLocaleString()}</span>
                      <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" /> Session: {esc.session_id.slice(0, 8)}...</span>
                    </div>
                  </div>
                </div>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(esc.status)}`}>
                  {esc.status.replace('_', ' ')}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );

  const ConfigurationView = (
    <div className="space-y-6">
      {/* Escalation Settings (moved from Business Settings) */}
      <Card>
        <h2 className="text-lg font-space font-semibold text-[var(--brand-primary)] border-b border-[var(--border-subtle)] pb-2 mb-4">
          Escalation Settings
        </h2>
        <div className="space-y-6">
          {/* Enable Toggle */}
          <div className="flex items-center justify-between p-4 bg-[var(--bg-secondary)] rounded-[var(--radius-md)] border border-[var(--border-subtle)]">
            <div>
              <h4 className="font-medium text-[var(--text-primary)]">Enable Human Escalation</h4>
              <p className="text-xs text-[var(--text-tertiary)]">Allow users to request a human agent</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={isEscalationEnabled}
                onChange={(e) => setIsEscalationEnabled(e.target.checked)}
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--brand-primary)]"></div>
            </label>
          </div>

          {/* Escalation Emails */}
          {isEscalationEnabled && (
            <div className="animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="flex items-center gap-2 mb-2">
                <Mail className="w-4 h-4 text-[var(--text-secondary)]" />
                <label className="text-sm font-medium text-[var(--text-secondary)]">Escalation Emails</label>
              </div>
              <div className="space-y-3">
                <div className="flex gap-2">
                  <Input
                    placeholder="support@example.com"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addEmail();
                      }
                    }}
                  />
                  <Button
                    variant="secondary"
                    onClick={addEmail}
                    disabled={!newEmail}
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {escalationEmails.map((email) => (
                    <div
                      key={email}
                      className="group flex items-center gap-2 px-3 py-1.5 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-full text-sm text-[var(--text-secondary)] hover:border-[var(--brand-primary)] hover:text-[var(--brand-primary)] transition-all"
                    >
                      <span>{email}</span>
                      <button
                        onClick={() => removeEmail(email)}
                        className="w-4 h-4 rounded-full flex items-center justify-center hover:text-[var(--error)] text-[var(--text-tertiary)] transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                  {escalationEmails.length === 0 && (
                    <p className="text-xs text-[var(--text-tertiary)] py-1">No emails configured. Add emails to receive escalation notifications.</p>
                  )}
                </div>
              </div>
              <p className="text-[12px] text-[var(--text-tertiary)] mt-2">
                These emails will receive notifications when a conversation is escalated.
              </p>
            </div>
          )}
        </div>
      </Card>



      <div className="flex justify-end pt-4">
        <Button size="lg" onClick={handleSaveConfig} loading={saving}>
          <CheckCircle2 className="w-4 h-4 mr-2" />
          Save Configuration
        </Button>
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-[var(--brand-accent)]/10 rounded-[var(--radius-squircle)]">
          <Users className="w-8 h-8 text-[var(--brand-accent)]" />
        </div>
        <div>
          <h1 className="text-h1 text-[var(--text-primary)]">Escalations</h1>
          <p className="text-body text-[var(--text-secondary)] mt-1">
            Manage escalation requests and configure handoff rules.
          </p>
        </div>
      </div>

      <Tabs
        defaultTab="requests"
        tabs={[
          { id: 'requests', label: 'Escalation Requests', content: RequestsView },
          { id: 'configuration', label: 'Configuration', content: ConfigurationView }
        ]}
      />
    </div>
  );
}
