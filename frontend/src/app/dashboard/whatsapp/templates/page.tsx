'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Download, Send as SendIcon, Trash2, RefreshCw, Pencil } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Textarea from '@/components/ui/Textarea';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import {
  WhatsAppTemplate,
  listWhatsAppTemplates,
  createWhatsAppTemplate,
  updateWhatsAppTemplate,
  submitWhatsAppTemplate,
  importWhatsAppTemplates,
  deleteWhatsAppTemplate,
} from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-gray-200 text-gray-700',
  PENDING: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  PAUSED: 'bg-orange-100 text-orange-800',
  DISABLED: 'bg-gray-100 text-gray-500',
};

const CATEGORIES = [
  { label: 'Marketing', value: 'MARKETING' },
  { label: 'Utility', value: 'UTILITY' },
  { label: 'Authentication', value: 'AUTHENTICATION' },
];

export default function WhatsAppTemplatesPage() {
  const [templates, setTemplates] = useState<WhatsAppTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [form, setForm] = useState({
    name: '',
    category: 'MARKETING',
    language: 'en_US',
    body_text: '',
    footer: '',
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const data = await listWhatsAppTemplates();
      setTemplates(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm({ name: '', category: 'MARKETING', language: 'en_US', body_text: '', footer: '' });
    setEditingId(null);
  };

  const openCreate = () => {
    resetForm();
    setCreateOpen(true);
  };

  const openEdit = (t: WhatsAppTemplate) => {
    setForm({
      name: t.name,
      category: t.category,
      language: t.language,
      body_text: t.body_text,
      footer: t.footer || '',
    });
    setEditingId(t.id);
    setCreateOpen(true);
  };

  const handleSave = async () => {
    if (!form.name || !form.body_text) return;
    setSaving(true);
    setMessage(null);
    try {
      if (editingId) {
        await updateWhatsAppTemplate(editingId, {
          name: form.name,
          category: form.category,
          language: form.language,
          body_text: form.body_text,
          footer: form.footer || null,
        });
        setMessage({ type: 'success', text: 'Template updated' });
      } else {
        await createWhatsAppTemplate({
          name: form.name,
          category: form.category,
          language: form.language,
          body_text: form.body_text,
          footer: form.footer || null,
        });
        setMessage({ type: 'success', text: 'Template draft created' });
      }
      resetForm();
      setCreateOpen(false);
      await fetchTemplates();
    } catch (e) {
      const detail =
        (e as { response?: { data?: { detail?: string; message?: string } } })
          ?.response?.data?.detail ??
        (e as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setMessage({
        type: 'error',
        text: detail || (editingId ? 'Failed to update template' : 'Failed to create template'),
      });
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleSubmitToMeta = async (id: string) => {
    try {
      await submitWhatsAppTemplate(id);
      setMessage({ type: 'success', text: 'Submitted to Meta for approval' });
      await fetchTemplates();
    } catch (e) {
      const detail =
        (e as { response?: { data?: { detail?: string; message?: string } } })
          ?.response?.data?.detail ??
        (e as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setMessage({ type: 'error', text: detail || 'Failed to submit to Meta' });
      console.error(e);
    }
  };

  const handleImport = async () => {
    setImporting(true);
    try {
      const imported = await importWhatsAppTemplates();
      setMessage({ type: 'success', text: `Imported ${imported.length} template(s)` });
      await fetchTemplates();
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to import templates' });
      console.error(e);
    } finally {
      setImporting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this template?')) return;
    try {
      await deleteWhatsAppTemplate(id);
      await fetchTemplates();
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to delete template' });
      console.error(e);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">WhatsApp Templates</h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Draft templates in-app or import approved ones from Meta.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleImport} loading={importing}>
            <Download className="w-4 h-4" /> Import from Meta
          </Button>
          <Button onClick={openCreate}>
            <Plus className="w-4 h-4" /> New Template
          </Button>
        </div>
      </div>

      {message && (
        <div
          className={`p-3 rounded text-sm ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800'
              : 'bg-red-50 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      <Card>
        {loading ? (
          <SkeletonLoader />
        ) : templates.length === 0 ? (
          <div className="text-center py-12 text-[var(--text-secondary)]">
            No templates yet. Create a draft or import from Meta to get started.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-[var(--text-secondary)] border-b border-[var(--border-subtle)]">
                <tr>
                  <th className="py-2">Name</th>
                  <th className="py-2">Category</th>
                  <th className="py-2">Language</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Source</th>
                  <th className="py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {templates.map((t) => (
                  <tr key={t.id} className="border-b border-[var(--border-subtle)]">
                    <td className="py-3 font-medium text-[var(--text-primary)]">{t.name}</td>
                    <td className="py-3">{t.category}</td>
                    <td className="py-3">{t.language}</td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          STATUS_COLORS[t.status] || 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {t.status}
                      </span>
                    </td>
                    <td className="py-3 text-[var(--text-secondary)]">{t.source}</td>
                    <td className="py-3 text-right">
                      <div className="flex gap-2 justify-end">
                        {t.status === 'DRAFT' && (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openEdit(t)}
                            >
                              <Pencil className="w-3 h-3" /> Edit
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => handleSubmitToMeta(t.id)}
                            >
                              <SendIcon className="w-3 h-3" /> Submit
                            </Button>
                          </>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDelete(t.id)}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal
        isOpen={createOpen}
        onClose={() => {
          setCreateOpen(false);
          resetForm();
        }}
        title={editingId ? 'Edit Template' : 'New Template'}
      >
        <div className="space-y-4">
          <Input
            label="Template Name (lowercase, no spaces)"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
            placeholder="my_promo_template"
          />
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Category"
              options={CATEGORIES}
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            />
            <Input
              label="Language"
              value={form.language}
              onChange={(e) => setForm({ ...form, language: e.target.value })}
              placeholder="en_US"
            />
          </div>
          <Textarea
            label="Body (use {{1}}, {{2}}, ... for variables)"
            rows={5}
            value={form.body_text}
            onChange={(e) => setForm({ ...form, body_text: e.target.value })}
            placeholder="Hi {{1}}, your order {{2}} is ready for pickup."
          />
          <Input
            label="Footer (optional)"
            value={form.footer}
            onChange={(e) => setForm({ ...form, footer: e.target.value })}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="ghost"
              onClick={() => {
                setCreateOpen(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleSave} loading={saving}>
              {editingId ? 'Save Changes' : 'Create Draft'}
            </Button>
          </div>
        </div>
      </Modal>
    </motion.div>
  );
}
