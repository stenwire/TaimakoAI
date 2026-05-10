'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Plus } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import {
  WhatsAppCampaign,
  WhatsAppTemplate,
  WhatsAppContactList,
  listWhatsAppCampaigns,
  createWhatsAppCampaign,
  listWhatsAppTemplates,
  listWhatsAppContactLists,
} from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-gray-200 text-gray-700',
  SCHEDULED: 'bg-blue-100 text-blue-800',
  SENDING: 'bg-yellow-100 text-yellow-800',
  COMPLETED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-gray-100 text-gray-500',
  FAILED: 'bg-red-100 text-red-800',
};

export default function WhatsAppCampaignsPage() {
  const [campaigns, setCampaigns] = useState<WhatsAppCampaign[]>([]);
  const [templates, setTemplates] = useState<WhatsAppTemplate[]>([]);
  const [lists, setLists] = useState<WhatsAppContactList[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [form, setForm] = useState({
    name: '',
    template_id: '',
    audience_type: 'LIST',
    list_id: '',
    ad_hoc_phones: '',
    min_sessions: '1',
    schedule: 'now',
    scheduled_at: '',
  });
  const [variableInputs, setVariableInputs] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [c, t, l] = await Promise.all([
        listWhatsAppCampaigns({ limit: 100 }),
        listWhatsAppTemplates(),
        listWhatsAppContactLists(),
      ]);
      setCampaigns(c.items);
      setTemplates(t.filter((x) => x.status === 'APPROVED'));
      setLists(l);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const selectedTemplate = templates.find((t) => t.id === form.template_id);

  const handleCreate = async () => {
    if (!form.name || !form.template_id) return;
    setSaving(true);
    try {
      let audience_ref: Record<string, unknown> = {};
      if (form.audience_type === 'LIST') {
        audience_ref = { list_id: form.list_id };
      } else if (form.audience_type === 'ADHOC') {
        audience_ref = {
          phones: form.ad_hoc_phones.split(/[\s,\n]+/).filter(Boolean),
        };
      } else if (form.audience_type === 'GUESTS_FILTER') {
        audience_ref = { min_sessions: parseInt(form.min_sessions || '1', 10) };
      }

      const variable_mapping: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(variableInputs)) {
        if (value.startsWith('@')) {
          variable_mapping[key] = { type: 'field', field: value.slice(1) };
        } else {
          variable_mapping[key] = { type: 'literal', value };
        }
      }

      const scheduledAt =
        form.schedule === 'later' && form.scheduled_at
          ? new Date(form.scheduled_at).toISOString()
          : null;

      await createWhatsAppCampaign({
        name: form.name,
        template_id: form.template_id,
        audience_type: form.audience_type,
        audience_ref,
        variable_mapping,
        scheduled_at: scheduledAt,
        send_now: form.schedule === 'now',
      });
      setMessage({ type: 'success', text: 'Campaign created' });
      setCreateOpen(false);
      setForm({
        name: '',
        template_id: '',
        audience_type: 'LIST',
        list_id: '',
        ad_hoc_phones: '',
        min_sessions: '1',
        schedule: 'now',
        scheduled_at: '',
      });
      setVariableInputs({});
      await fetchAll();
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to create campaign' });
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">WhatsApp Campaigns</h1>
          <p className="text-[var(--text-secondary)] mt-1">Broadcast templated messages to contact lists.</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="w-4 h-4" /> New Campaign
        </Button>
      </div>

      {message && (
        <div
          className={`p-3 rounded text-sm ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      <Card>
        {loading ? (
          <SkeletonLoader />
        ) : campaigns.length === 0 ? (
          <div className="text-center py-12 text-[var(--text-secondary)]">
            No campaigns yet. Create one to broadcast a template to your contacts.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-[var(--text-secondary)] border-b border-[var(--border-subtle)]">
                <tr>
                  <th className="py-2">Name</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Recipients</th>
                  <th className="py-2">Sent</th>
                  <th className="py-2">Delivered</th>
                  <th className="py-2">Read</th>
                  <th className="py-2">Failed</th>
                  <th className="py-2">Scheduled</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c) => (
                  <tr key={c.id} className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-tertiary)]">
                    <td className="py-3">
                      <Link
                        href={`/dashboard/whatsapp/campaigns/${c.id}`}
                        className="font-medium text-[var(--brand-primary)] hover:underline"
                      >
                        {c.name}
                      </Link>
                    </td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          STATUS_COLORS[c.status] || 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3">{c.total_recipients}</td>
                    <td className="py-3">{c.sent_count}</td>
                    <td className="py-3">{c.delivered_count}</td>
                    <td className="py-3">{c.read_count}</td>
                    <td className="py-3">{c.failed_count}</td>
                    <td className="py-3 text-xs text-[var(--text-secondary)]">
                      {c.scheduled_at ? new Date(c.scheduled_at).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal isOpen={createOpen} onClose={() => setCreateOpen(false)} title="New Campaign">
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
          <Input
            label="Campaign Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />

          <Select
            label="Template (APPROVED only)"
            options={[
              { label: 'Select a template...', value: '' },
              ...templates.map((t) => ({ label: `${t.name} (${t.language})`, value: t.id })),
            ]}
            value={form.template_id}
            onChange={(e) => {
              const id = e.target.value;
              setForm({ ...form, template_id: id });
              const tpl = templates.find((t) => t.id === id);
              const initial: Record<string, string> = {};
              (tpl?.variables || []).forEach((k) => (initial[k] = ''));
              setVariableInputs(initial);
            }}
          />

          {selectedTemplate && (
            <div className="p-3 bg-[var(--bg-tertiary)] rounded text-sm">
              <div className="font-mono whitespace-pre-wrap">{selectedTemplate.body_text}</div>
            </div>
          )}

          {selectedTemplate?.variables?.length ? (
            <div className="space-y-2">
              <div className="text-sm font-medium text-[var(--text-secondary)]">
                Variables (prefix with @ for contact field, e.g. @name)
              </div>
              {selectedTemplate.variables.map((v) => (
                <Input
                  key={v}
                  label={`{{${v}}}`}
                  placeholder="Literal value or @name"
                  value={variableInputs[v] || ''}
                  onChange={(e) => setVariableInputs({ ...variableInputs, [v]: e.target.value })}
                />
              ))}
            </div>
          ) : null}

          <Select
            label="Audience Type"
            options={[
              { label: 'Contact List', value: 'LIST' },
              { label: 'WhatsApp Chat Guests', value: 'GUESTS_FILTER' },
              { label: 'Paste Phone Numbers', value: 'ADHOC' },
            ]}
            value={form.audience_type}
            onChange={(e) => setForm({ ...form, audience_type: e.target.value })}
          />

          {form.audience_type === 'LIST' && (
            <Select
              label="List"
              options={[
                { label: 'Select a list...', value: '' },
                ...lists.map((l) => ({ label: `${l.name} (${l.member_count})`, value: l.id })),
              ]}
              value={form.list_id}
              onChange={(e) => setForm({ ...form, list_id: e.target.value })}
            />
          )}

          {form.audience_type === 'ADHOC' && (
            <div>
              <label className="block text-[13px] font-medium text-[var(--text-secondary)] mb-2">
                Phone Numbers (one per line, E.164 format)
              </label>
              <textarea
                className="w-full px-3 py-2 text-sm border border-[var(--border-subtle)] rounded bg-[var(--bg-primary)]"
                rows={5}
                value={form.ad_hoc_phones}
                onChange={(e) => setForm({ ...form, ad_hoc_phones: e.target.value })}
                placeholder="+2348012345678&#10;+2347098765432"
              />
            </div>
          )}

          {form.audience_type === 'GUESTS_FILTER' && (
            <Input
              label="Minimum sessions per guest"
              type="number"
              value={form.min_sessions}
              onChange={(e) => setForm({ ...form, min_sessions: e.target.value })}
            />
          )}

          <Select
            label="Schedule"
            options={[
              { label: 'Send now', value: 'now' },
              { label: 'Schedule for later', value: 'later' },
            ]}
            value={form.schedule}
            onChange={(e) => setForm({ ...form, schedule: e.target.value })}
          />

          {form.schedule === 'later' && (
            <Input
              label="Scheduled at"
              type="datetime-local"
              value={form.scheduled_at}
              onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
            />
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} loading={saving}>
              Create Campaign
            </Button>
          </div>
        </div>
      </Modal>
    </motion.div>
  );
}
