'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowLeft, Sparkles, Wand2, Calendar, Users, Send, Bot, User as UserIcon
} from 'lucide-react';
import { motion } from 'framer-motion';
import Button from '@/components/ui/Button';
import FollowUpModal from '@/components/dashboard/FollowUpModal';
import { getSession, analyzeSession, generateFollowUp } from '@/lib/api';
import { SessionDetail } from '@/lib/types';
import { cn } from '@/lib/utils';
import Markdown from '@/components/ui/Markdown';

export default function SessionDetailPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;
  const guestId = params.guestId as string;

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [generatingFollowUp, setGeneratingFollowUp] = useState(false);

  useEffect(() => {
    async function loadDetail() {
      if (!sessionId) return;
      try {
        const data = await getSession(sessionId);
        setSession(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadDetail();
  }, [sessionId]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      await analyzeSession(sessionId);
      const updated = await getSession(sessionId);
      setSession(updated);
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFollowUpSubmit = async (context: string) => {
    setGeneratingFollowUp(true);
    try {
      const res = await generateFollowUp(sessionId, "email", context);
      return res.data?.content;
    } catch (e) {
      console.error(e);
      // Let modal handle error or just log it
    } finally {
      setGeneratingFollowUp(false);
    }
  };

  if (loading) return <div className="p-12 text-center text-[var(--text-tertiary)]">Loading session details...</div>;
  if (!session) return <div className="p-12 text-center text-[var(--text-tertiary)]">Session not found.</div>;

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-100px)] flex flex-col">
      {/* Header */}
      <div className="mb-6 flex-shrink-0 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="secondary" onClick={() => router.back()} className="rounded-full px-3">
            <ArrowLeft className="w-5 h-5 text-[var(--text-secondary)]" />
          </Button>
          <div>
            <h1 className="text-2xl font-space font-bold text-[var(--brand-primary)] flex items-center gap-2">
              Session Detail
              {session.sentiment_score !== null && (
                <span className={cn(
                  "text-xs px-2 py-0.5 rounded-full border font-normal",
                  session.sentiment_score > 0 ? "border-green-200 bg-green-50 text-green-700" : "border-red-200 bg-red-50 text-red-700"
                )}>
                  Sentiment: {session.sentiment_score.toFixed(2)}
                </span>
              )}
            </h1>
            <div className="flex items-center gap-3 text-sm text-[var(--text-secondary)] mt-1">
              <span className="flex items-center"><Calendar className="w-3.5 h-3.5 mr-1" /> {new Date(session.created_at).toLocaleString()}</span>
              {session.guest.location && <span className="flex items-center"><Users className="w-3.5 h-3.5 mr-1" /> {session.guest.location}</span>}
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={handleAnalyze}
            disabled={analyzing}
            className="flex items-center gap-2"
          >
            {analyzing ? <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" /> : <Sparkles className="w-4 h-4 text-[var(--brand-accent)]" />}
            Run Analysis
          </Button>
          <Button
            className="bg-[var(--brand-primary)] text-white hover:bg-[var(--brand-primary)]/90 hover:text-white"
            onClick={() => setIsModalOpen(true)}
          >
            <Wand2 className="w-4 h-4 mr-2" />
            Generate Follow-up
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 bg-white rounded-[var(--radius-lg)] border border-[var(--border-subtle)] shadow-sm overflow-hidden flex flex-col">
        {session.summary && (
          <div className="p-4 bg-[var(--bg-tertiary)]/20 border-b border-[var(--border-subtle)]">
            <h3 className="text-xs font-bold text-[var(--brand-primary)] uppercase tracking-wider mb-1">AI Summary</h3>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed italic">{session.summary}</p>
            {session.top_intent && (
              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs font-semibold text-[var(--brand-primary)] uppercase tracking-wider">Detected Intent:</span>
                <span className="text-xs font-medium px-2 py-0.5 bg-[var(--brand-primary)]/10 text-[var(--brand-primary)] rounded-full">
                  {session.top_intent}
                </span>
              </div>
            )}
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[var(--bg-secondary)]/30">
          {session.messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex gap-4 max-w-[85%]",
                msg.role === 'user' ? "ml-auto flex-row-reverse" : ""
              )}
            >
              <div className={cn(
                "w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm text-white",
                msg.role === 'user' ? "bg-[var(--brand-primary)]" : "bg-[var(--brand-accent)]"
              )}>
                {msg.role === 'user' ? <UserIcon className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>
              <div>
                <div className={cn(
                  "p-4 rounded-2xl shadow-sm text-sm leading-relaxed",
                  msg.role === 'user'
                    ? "bg-[var(--brand-primary)] text-white rounded-tr-none"
                    : "bg-white text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-tl-none"
                )}>
                  {/* Use Markdown component for safe HTML rendering */}
                  <Markdown
                    content={msg.content}
                    variant={msg.role === 'user' ? 'inverted' : 'default'}
                  />
                </div>
                <div className={cn(
                  "text-[10px] text-[var(--text-tertiary)] mt-1",
                  msg.role === 'user' ? "text-right" : "text-left"
                )}>
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      <FollowUpModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleFollowUpSubmit}
        loading={generatingFollowUp}
      />
    </div>
  );
}
