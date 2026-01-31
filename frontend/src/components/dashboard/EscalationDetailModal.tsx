import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, CheckCircle, User, Bot, Clock, AlertTriangle } from 'lucide-react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { getEscalationDetails, resolveEscalation } from '@/lib/api';
import type { EscalationDetail, EscalationMessage } from '@/lib/types';
import SkeletonLoader from '@/components/ui/SkeletonLoader';

interface EscalationDetailModalProps {
  escalationId: string | null;
  onClose: () => void;
  onResolve: () => void;
}

export default function EscalationDetailModal({ escalationId, onClose, onResolve }: EscalationDetailModalProps) {
  const [detail, setDetail] = useState<EscalationDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (escalationId) {
      fetchDetail(escalationId);
    } else {
      setDetail(null);
    }
  }, [escalationId]);

  const fetchDetail = async (id: string) => {
    setLoading(true);
    setError('');
    try {
      const data = await getEscalationDetails(id);
      setDetail(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load escalation details');
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!escalationId) return;
    setResolving(true);
    try {
      await resolveEscalation(escalationId);
      onResolve();
      onClose();
    } catch (err) {
      console.error(err);
      setError('Failed to resolve escalation');
    } finally {
      setResolving(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'text-green-500 bg-green-500/10';
      case 'negative': return 'text-red-500 bg-red-500/10';
      default: return 'text-gray-500 bg-gray-500/10';
    }
  };

  return (
    <Modal
      isOpen={!!escalationId}
      onClose={onClose}
      title="Escalation Details"
      className="max-w-2xl"
    >
      <div className="space-y-6">
        {loading ? (
          <div className="space-y-4">
            <SkeletonLoader variant="text" count={2} />
            <SkeletonLoader variant="rectangle" className="h-48" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-8 text-[var(--error)]">
            <AlertTriangle className="w-8 h-8 mb-2" />
            <p>{error}</p>
            <Button variant="secondary" size="sm" onClick={() => escalationId && fetchDetail(escalationId)} className="mt-4">
              Retry
            </Button>
          </div>
        ) : detail ? (
          <>
            {/* Header Info */}
            <div className="bg-[var(--bg-secondary)] p-4 rounded-[var(--radius-md)] space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-medium text-[var(--text-secondary)] uppercase tracking-wider">Summary</h3>
                  <p className="text-[var(--text-primary)] mt-1 font-medium">{detail.summary}</p>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium uppercase ${getSentimentColor(detail.sentiment)}`}>
                  {detail.sentiment}
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs text-[var(--text-tertiary)] pt-2 border-t border-[var(--border-subtle)]">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {formatDate(detail.created_at)}
                </span>
                <span className="flex items-center gap-1">
                  <span className={`w-2 h-2 rounded-full ${detail.status === 'resolved' ? 'bg-green-500' : detail.status === 'in_progress' ? 'bg-blue-500' : 'bg-yellow-500'}`} />
                  {detail.status.replace('_', ' ')}
                </span>
              </div>
            </div>

            {/* Chat Thread */}
            <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
              <h3 className="text-sm font-medium text-[var(--text-secondary)] sticky top-0 bg-[var(--bg-primary)] py-2 z-10">Conversation History</h3>
              {detail.messages.map((msg) => (
                <div key={msg.id} className={`flex gap-3 ${msg.sender === 'user' ? 'flex-row' : 'flex-row-reverse'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.sender === 'user' ? 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]' : 'bg-[var(--brand-primary)] text-white'}`}>
                    {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>
                  <div className={`flex-1 p-3 rounded-[var(--radius-md)] text-sm ${msg.sender === 'user' ? 'bg-[var(--bg-secondary)] text-[var(--text-primary)]' : 'bg-[var(--brand-primary)]/10 text-[var(--text-primary)] border border-[var(--brand-primary)]/20'}`}>
                    <p>{msg.message}</p>
                    <p className="text-[10px] text-[var(--text-tertiary)] mt-1 text-right">{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-[var(--border-subtle)] flex justify-end gap-3">
              <Button variant="secondary" onClick={onClose}>
                Close
              </Button>
              {detail.status !== 'resolved' && (
                <Button onClick={handleResolve} loading={resolving}>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Mark as Resolved
                </Button>
              )}
            </div>
          </>
        ) : null}
      </div>
    </Modal>
  );
}
