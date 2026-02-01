'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  ArrowLeft, CheckCircle, User, Bot, Clock, AlertTriangle, MapPin, Mail, Phone
} from 'lucide-react';
import Button from '@/components/ui/Button';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import { getEscalationDetails, resolveEscalation } from '@/lib/api';
import type { EscalationDetail } from '@/lib/types';
import { cn } from '@/lib/utils';
import Markdown from '@/components/ui/Markdown';

// Helper component to avoid hydration mismatches with dates
const FormattedDate = ({ date }: { date: string }) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <span className="opacity-0">Loading...</span>; // Render same structure but invisible or simple placeholder
  }

  return (
    <span>
      {new Date(date).toLocaleString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      })}
    </span>
  );
};

const FormattedTime = ({ date }: { date: string }) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <span>
      {new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
    </span>
  );
};

export default function EscalationDetailPage() {
  const router = useRouter();
  const params = useParams();
  const escalationId = params.escalationId as string;

  const [detail, setDetail] = useState<EscalationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (escalationId) {
      fetchDetail(escalationId);
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
      await fetchDetail(escalationId);
    } catch (err) {
      console.error(err);
      setError('Failed to resolve escalation');
    } finally {
      setResolving(false);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'text-green-600 bg-green-50 border-green-200';
      case 'negative': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'resolved': return 'bg-green-500';
      case 'in_progress': return 'bg-blue-500';
      default: return 'bg-yellow-500';
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 p-6">
        <SkeletonLoader variant="text" count={2} />
        <SkeletonLoader variant="rectangle" className="h-48" />
        <SkeletonLoader variant="rectangle" className="h-96" />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="max-w-4xl mx-auto h-[calc(100vh-100px)] flex flex-col items-center justify-center">
        <AlertTriangle className="w-12 h-12 text-[var(--error)] mb-4" />
        <p className="text-[var(--text-primary)] text-lg mb-4">{error || 'Escalation not found'}</p>
        <Button variant="secondary" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-100px)] flex flex-col">
      {/* Header */}
      <div className="mb-6 flex-shrink-0 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="secondary" onClick={() => router.back()} className="rounded-full px-3">
            <ArrowLeft className="w-5 h-5 text-[var(--text-secondary)]" />
          </Button>
          <div>
            <h1 className="text-2xl font-space font-bold text-[var(--brand-primary)] flex items-center gap-3">
              Escalation Details
              <span className={cn(
                "text-xs px-2.5 py-0.5 rounded-full border font-normal",
                getSentimentColor(detail.sentiment)
              )}>
                {detail.sentiment}
              </span>
            </h1>
            <div className="flex items-center gap-4 text-sm text-[var(--text-secondary)] mt-1">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" /> <FormattedDate date={detail.created_at} />
              </span>
              <span className="flex items-center gap-1">
                <span className={`w-2 h-2 rounded-full ${getStatusColor(detail.status)}`} />
                {detail.status.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          {detail.status !== 'resolved' && (
            <Button onClick={handleResolve} loading={resolving}>
              <CheckCircle className="w-4 h-4 mr-2" />
              Mark as Resolved
            </Button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 bg-white rounded-[var(--radius-lg)] border border-[var(--border-subtle)] shadow-sm overflow-hidden flex flex-col">
        {/* Summary, Sentiment & Intent Section */}
        <div className="p-4 bg-[var(--bg-tertiary)]/20 border-b border-[var(--border-subtle)]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Summary */}
            <div>
              <h3 className="text-xs font-bold text-[var(--brand-primary)] uppercase tracking-wider mb-1">Summary</h3>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{detail.summary || 'No summary available'}</p>
            </div>

            {/* Detected Intent */}
            <div>
              <h3 className="text-xs font-bold text-[var(--brand-primary)] uppercase tracking-wider mb-1">Detected Intent</h3>
              <span className="inline-block text-xs font-medium px-2 py-0.5 bg-[var(--brand-primary)]/10 text-[var(--brand-primary)] rounded-full">
                {detail.top_intent ? detail.top_intent.replace(/_/g, ' ') : 'Unknown Intent'}
              </span>
            </div>
          </div>
        </div>

        {/* Guest Details Section */}
        <div className="p-4 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]/30">
          <h3 className="text-xs font-bold text-[var(--brand-primary)] uppercase tracking-wider mb-3">Guest Information</h3>
          {/* Fixed responsive grid to prevent overlapping, added overflow control */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-[var(--brand-primary)] flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-[var(--text-tertiary)]">Name</p>
                <p className="text-sm font-medium text-[var(--text-primary)] truncate" title={detail.guest?.name}>
                  {detail.guest?.name || 'Guest User'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center flex-shrink-0">
                <Mail className="w-4 h-4 text-[var(--text-secondary)]" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-[var(--text-tertiary)]">Email</p>
                <p className="text-sm font-medium text-[var(--text-primary)] truncate" title={detail.guest?.email || ''}>
                  {detail.guest?.email || 'Not provided'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center flex-shrink-0">
                <Phone className="w-4 h-4 text-[var(--text-secondary)]" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-[var(--text-tertiary)]">Phone</p>
                <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                  {detail.guest?.phone || 'Not provided'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center flex-shrink-0">
                <MapPin className="w-4 h-4 text-[var(--text-secondary)]" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-[var(--text-tertiary)]">Location</p>
                <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                  {detail.guest?.location || 'Unknown'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Conversation Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[var(--bg-secondary)]/30">
          <h3 className="text-xs font-bold text-[var(--brand-primary)] uppercase tracking-wider sticky top-0 bg-[var(--bg-secondary)]/60 py-2 backdrop-blur-sm z-10 text-center border-b border-[var(--border-subtle)]/50 mb-4">
            Conversation History
          </h3>
          {detail.messages.map((msg) => {
            // Corrected check: message is from user if sender is 'user' or 'guest'
            const isUser = msg.sender === 'user' || msg.sender === 'guest';

            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "flex gap-4 max-w-[85%]",
                  isUser ? "ml-auto flex-row-reverse" : "mr-auto flex-row"
                )}
              >
                <div className={cn(
                  "w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm text-white",
                  isUser ? "bg-[var(--brand-primary)]" : "bg-[var(--brand-accent)]"
                )}>
                  {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                </div>
                <div>
                  <div className={cn(
                    "p-4 rounded-2xl shadow-sm text-sm leading-relaxed",
                    isUser
                      ? "bg-[var(--brand-primary)] text-white rounded-tr-none"
                      : "bg-white text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-tl-none"
                  )}>
                    <Markdown
                      content={msg.message}
                      variant={isUser ? 'inverted' : 'default'}
                    />
                  </div>
                  <div className={cn(
                    "text-[10px] text-[var(--text-tertiary)] mt-1",
                    isUser ? "text-right" : "text-left"
                  )}>
                    <FormattedTime date={msg.created_at} />
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
