'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, Bell, Flag, Plus, Trash2, CheckCircle2, Search, Filter, MessageSquare, Clock } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Tabs from '@/components/ui/Tabs';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import EscalationDetailModal from '@/components/dashboard/EscalationDetailModal';
import { getBusinessProfile, getEscalations } from '@/lib/api';
import type { Escalation } from '@/lib/types';

interface HandoffRule {
  id: string;
  condition: string;
  value: string;
  action: string;
}

export default function HandoffPage() {
  const [activeTab, setActiveTab] = useState('requests');
  const [businessId, setBusinessId] = useState<string | null>(null);

  // Escalation List State
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loadingEscalations, setLoadingEscalations] = useState(false);
  const [selectedEscalationId, setSelectedEscalationId] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Configuration State
  const [rules, setRules] = useState<HandoffRule[]>([
    { id: '1', condition: 'sentiment_below', value: '0.3', action: 'notify_email' },
    { id: '2', condition: 'intent_equals', value: 'billing_dispute', action: 'assign_team' }
  ]);
  const [emailAlerts, setEmailAlerts] = useState<string[]>(['support@acme.com']);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchBusinessAndEscalations();
  }, []);

  const fetchBusinessAndEscalations = async () => {
    try {
      setLoadingEscalations(true);
      // We need business ID first. In a real app, this might be in context.
      // Assuming getBusinessProfile returns the ID.
      const profileRes = await getBusinessProfile();
      if (profileRes.data?.id) {
        setBusinessId(profileRes.data.id);
        const escRes = await getEscalations(profileRes.data.id);
        setEscalations(escRes || []);
      }
    } catch (error) {
      console.error("Failed to load data", error);
    } finally {
      setLoadingEscalations(false);
    }
  };

  const handleSaveConfig = () => {
    setSaving(true);
    setTimeout(() => setSaving(false), 1000);
  };

  // Rule management
  const addRule = () => {
    setRules([...rules, { id: Date.now().toString(), condition: 'intent_equals', value: '', action: 'notify_email' }]);
  };
  const removeRule = (id: string) => setRules(rules.filter(r => r.id !== id));
  const updateRule = (id: string, field: keyof HandoffRule, val: string) => {
    setRules(rules.map(r => r.id === id ? { ...r, [field]: val } : r));
  };

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

  const RequestsView = (
    <div className="space-y-6">
      <div className="flex gap-4 items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--text-tertiary)] w-4 h-4" />
          <input
            type="text"
            placeholder="Search escalations..."
            className="w-full pl-10 pr-4 py-2 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-md)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]/20"
          />
        </div>
        <select
          className="bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-md)] px-3 py-2 text-sm focus:outline-none"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
        </select>
        <Button variant="secondary" onClick={fetchBusinessAndEscalations}>
          Refresh
        </Button>
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
              onClick={() => setSelectedEscalationId(esc.id)}
            >
              <div className="flex justify-between items-start">
                <div className="flex gap-3">
                  <div className={`mt-1 p-2 rounded-full ${esc.sentiment === 'negative' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'}`}>
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
      {/* Global Settings */}
      <Card>
        <h2 className="text-lg font-space font-semibold text-[var(--brand-primary)] border-b border-[var(--border-subtle)] pb-2 mb-4">Availability & Sensitivity</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-[var(--bg-secondary)] rounded-[var(--radius-md)] border border-[var(--border-subtle)]">
            <div>
              <h4 className="font-medium text-[var(--text-primary)]">Strict Handoff Mode</h4>
              <p className="text-xs text-[var(--text-tertiary)]">Immediately escalate if AI confidence is low</p>
            </div>
            <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
              <input type="checkbox" name="toggle" id="toggle" className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer border-[var(--border-strong)]" />
              <label htmlFor="toggle" className="toggle-label block overflow-hidden h-6 rounded-full bg-[var(--border-strong)] cursor-pointer"></label>
            </div>
          </div>
        </div>
      </Card>

      {/* Rules Engine */}
      <Card>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-lg font-space font-semibold text-[var(--brand-primary)]">Escalation Rules</h2>
            <p className="text-sm text-[var(--text-secondary)]">Define triggers for automatic handoff</p>
          </div>
          <Button size="sm" variant="secondary" onClick={addRule}>
            <Plus className="w-4 h-4 mr-1" /> Add Rule
          </Button>
        </div>

        <div className="space-y-3">
          {rules.map((rule) => (
            <div key={rule.id} className="grid grid-cols-12 gap-3 items-center p-3 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-md)]">
              <div className="col-span-1 flex justify-center">
                <div className="p-2 bg-[var(--bg-tertiary)] rounded-full">
                  <Flag className="w-4 h-4 text-[var(--brand-accent)]" />
                </div>
              </div>
              <div className="col-span-3">
                <select
                  className="w-full text-sm bg-transparent border-none focus:ring-0 font-medium"
                  value={rule.condition}
                  onChange={(e) => updateRule(rule.id, 'condition', e.target.value)}
                >
                  <option value="intent_equals">If Intent is...</option>
                  <option value="sentiment_below">If Sentiment &lt;</option>
                  <option value="confidence_below">If Confidence &lt;</option>
                  <option value="word_match">If message contains...</option>
                </select>
              </div>
              <div className="col-span-4">
                <input
                  type="text"
                  className="w-full text-sm bg-[var(--bg-secondary)] px-3 py-2 rounded-[var(--radius-sm)] border border-[var(--border-subtle)]"
                  value={rule.value}
                  placeholder="Value..."
                  onChange={(e) => updateRule(rule.id, 'value', e.target.value)}
                />
              </div>
              <div className="col-span-3">
                <select
                  className="w-full text-sm bg-transparent border-none focus:ring-0 text-[var(--text-secondary)]"
                  value={rule.action}
                  onChange={(e) => updateRule(rule.id, 'action', e.target.value)}
                >
                  <option value="notify_email">Send Email Alert</option>
                  <option value="assign_team">Assign to Team</option>
                  <option value="mark_priority">Mark as Priority</option>
                </select>
              </div>
              <div className="col-span-1 flex justify-end">
                <button onClick={() => removeRule(rule.id)} className="text-[var(--text-tertiary)] hover:text-[var(--status-error)] transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
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
          <h1 className="text-h1 text-[var(--text-primary)]">Human Handoff</h1>
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

      <EscalationDetailModal
        escalationId={selectedEscalationId}
        onClose={() => setSelectedEscalationId(null)}
        onResolve={() => {
          fetchBusinessAndEscalations(); // Refresh list after resolve
        }}
      />
    </div>
  );
}
