'use client';

import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Plus, Upload, Users, Trash2, Search } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import {
  WhatsAppContact,
  WhatsAppContactList,
  listWhatsAppContacts,
  createWhatsAppContact,
  deleteWhatsAppContact,
  uploadWhatsAppContactsCsv,
  importWhatsAppGuests,
  listWhatsAppContactLists,
  createWhatsAppContactList,
  deleteWhatsAppContactList,
  addWhatsAppContactListMembers,
} from '@/lib/api';

export default function WhatsAppContactsPage() {
  const [tab, setTab] = useState<'contacts' | 'lists'>('contacts');
  const [contacts, setContacts] = useState<WhatsAppContact[]>([]);
  const [lists, setLists] = useState<WhatsAppContactList[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [addOpen, setAddOpen] = useState(false);
  const [addForm, setAddForm] = useState({ phone: '', name: '', tags: '' });
  const [saving, setSaving] = useState(false);

  const [listModalOpen, setListModalOpen] = useState(false);
  const [listForm, setListForm] = useState({ name: '', description: '' });

  const [selectedContactIds, setSelectedContactIds] = useState<Set<string>>(new Set());
  const [assignListId, setAssignListId] = useState<string>('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [c, l] = await Promise.all([
        listWhatsAppContacts({ q: search || undefined, limit: 100 }),
        listWhatsAppContactLists(),
      ]);
      setContacts(c.items);
      setTotal(c.total);
      setLists(l);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!addForm.phone) return;
    setSaving(true);
    try {
      await createWhatsAppContact({
        phone: addForm.phone,
        name: addForm.name || undefined,
        tags: addForm.tags ? addForm.tags.split(',').map((t) => t.trim()) : undefined,
      });
      setMessage({ type: 'success', text: 'Contact added' });
      setAddForm({ phone: '', name: '', tags: '' });
      setAddOpen(false);
      await fetchAll();
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to add contact' });
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleCsv = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await uploadWhatsAppContactsCsv(file);
      setMessage({
        type: 'success',
        text: `Imported ${result.imported}, skipped ${result.skipped}${
          result.errors.length ? ` (${result.errors.length} errors)` : ''
        }`,
      });
      await fetchAll();
    } catch (err) {
      setMessage({ type: 'error', text: 'CSV upload failed' });
      console.error(err);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleImportGuests = async () => {
    try {
      const result = await importWhatsAppGuests({});
      setMessage({ type: 'success', text: `Imported ${result.imported} contact(s) from WhatsApp chats` });
      await fetchAll();
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to import from WhatsApp chats' });
      console.error(e);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this contact?')) return;
    try {
      await deleteWhatsAppContact(id);
      await fetchAll();
    } catch (e) {
      console.error(e);
    }
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selectedContactIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedContactIds(next);
  };

  const handleAssignToList = async () => {
    if (!assignListId || selectedContactIds.size === 0) return;
    try {
      await addWhatsAppContactListMembers(assignListId, Array.from(selectedContactIds));
      setMessage({ type: 'success', text: 'Contacts added to list' });
      setSelectedContactIds(new Set());
      setAssignListId('');
      await fetchAll();
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to add to list' });
      console.error(e);
    }
  };

  const handleCreateList = async () => {
    if (!listForm.name) return;
    try {
      await createWhatsAppContactList({ name: listForm.name, description: listForm.description || undefined });
      setListForm({ name: '', description: '' });
      setListModalOpen(false);
      await fetchAll();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteList = async (id: string) => {
    if (!confirm('Delete this list?')) return;
    try {
      await deleteWhatsAppContactList(id);
      await fetchAll();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">WhatsApp Contacts</h1>
          <p className="text-[var(--text-secondary)] mt-1">Manage contacts and lists for broadcast campaigns.</p>
        </div>
      </div>

      <div className="flex gap-2 border-b border-[var(--border-subtle)]">
        <button
          onClick={() => setTab('contacts')}
          className={`px-4 py-2 text-sm font-medium ${
            tab === 'contacts'
              ? 'border-b-2 border-[var(--brand-primary)] text-[var(--brand-primary)]'
              : 'text-[var(--text-secondary)]'
          }`}
        >
          Contacts ({total})
        </button>
        <button
          onClick={() => setTab('lists')}
          className={`px-4 py-2 text-sm font-medium ${
            tab === 'lists'
              ? 'border-b-2 border-[var(--brand-primary)] text-[var(--brand-primary)]'
              : 'text-[var(--text-secondary)]'
          }`}
        >
          Lists ({lists.length})
        </button>
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

      {tab === 'contacts' && (
        <>
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-2 flex-1 min-w-64">
              <Input
                placeholder="Search by name or phone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchAll()}
              />
              <Button variant="secondary" onClick={fetchAll}>
                <Search className="w-4 h-4" />
              </Button>
            </div>
            <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
              <Upload className="w-4 h-4" /> Upload CSV
            </Button>
            <input ref={fileInputRef} type="file" accept=".csv" className="hidden" onChange={handleCsv} />
            <Button variant="secondary" onClick={handleImportGuests}>
              <Users className="w-4 h-4" /> Import from Chats
            </Button>
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="w-4 h-4" /> Add Contact
            </Button>
          </div>

          {selectedContactIds.size > 0 && (
            <div className="flex items-center gap-2 p-3 bg-[var(--bg-tertiary)] rounded">
              <span className="text-sm">{selectedContactIds.size} selected</span>
              <select
                value={assignListId}
                onChange={(e) => setAssignListId(e.target.value)}
                className="px-2 py-1 border rounded text-sm"
              >
                <option value="">Add to list...</option>
                {lists.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
              <Button size="sm" onClick={handleAssignToList} disabled={!assignListId}>
                Add
              </Button>
            </div>
          )}

          <Card>
            {loading ? (
              <SkeletonLoader />
            ) : contacts.length === 0 ? (
              <div className="text-center py-12 text-[var(--text-secondary)]">No contacts yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-[var(--text-secondary)] border-b border-[var(--border-subtle)]">
                    <tr>
                      <th className="py-2 w-8"></th>
                      <th className="py-2">Phone</th>
                      <th className="py-2">Name</th>
                      <th className="py-2">Tags</th>
                      <th className="py-2">Source</th>
                      <th className="py-2">Opted In</th>
                      <th className="py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {contacts.map((c) => (
                      <tr key={c.id} className="border-b border-[var(--border-subtle)]">
                        <td className="py-3">
                          <input
                            type="checkbox"
                            checked={selectedContactIds.has(c.id)}
                            onChange={() => toggleSelect(c.id)}
                          />
                        </td>
                        <td className="py-3 font-mono">{c.phone_e164}</td>
                        <td className="py-3">{c.name || '-'}</td>
                        <td className="py-3 text-xs">{(c.tags || []).join(', ')}</td>
                        <td className="py-3 text-[var(--text-secondary)]">{c.source}</td>
                        <td className="py-3">{c.opted_in ? '✓' : '✗'}</td>
                        <td className="py-3 text-right">
                          <Button size="sm" variant="ghost" onClick={() => handleDelete(c.id)}>
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}

      {tab === 'lists' && (
        <>
          <div className="flex justify-end">
            <Button onClick={() => setListModalOpen(true)}>
              <Plus className="w-4 h-4" /> New List
            </Button>
          </div>
          <Card>
            {lists.length === 0 ? (
              <div className="text-center py-12 text-[var(--text-secondary)]">No lists yet.</div>
            ) : (
              <div className="space-y-2">
                {lists.map((l) => (
                  <div
                    key={l.id}
                    className="flex items-center justify-between p-3 border-b border-[var(--border-subtle)]"
                  >
                    <div>
                      <div className="font-medium text-[var(--text-primary)]">{l.name}</div>
                      <div className="text-sm text-[var(--text-secondary)]">
                        {l.member_count} member(s)
                        {l.description && ` · ${l.description}`}
                      </div>
                    </div>
                    <Button size="sm" variant="ghost" onClick={() => handleDeleteList(l.id)}>
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}

      <Modal isOpen={addOpen} onClose={() => setAddOpen(false)} title="Add Contact">
        <div className="space-y-4">
          <Input
            label="Phone (E.164 format)"
            placeholder="+2348012345678"
            value={addForm.phone}
            onChange={(e) => setAddForm({ ...addForm, phone: e.target.value })}
          />
          <Input
            label="Name (optional)"
            value={addForm.name}
            onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
          />
          <Input
            label="Tags (comma-separated, optional)"
            value={addForm.tags}
            onChange={(e) => setAddForm({ ...addForm, tags: e.target.value })}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAdd} loading={saving}>
              Add
            </Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={listModalOpen} onClose={() => setListModalOpen(false)} title="New Contact List">
        <div className="space-y-4">
          <Input
            label="List Name"
            value={listForm.name}
            onChange={(e) => setListForm({ ...listForm, name: e.target.value })}
          />
          <Input
            label="Description (optional)"
            value={listForm.description}
            onChange={(e) => setListForm({ ...listForm, description: e.target.value })}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setListModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateList}>Create</Button>
          </div>
        </div>
      </Modal>
    </motion.div>
  );
}
