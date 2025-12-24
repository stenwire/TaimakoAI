'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowLeft, MessageSquare, Clock, MapPin, Smartphone,
  ChevronRight, Sparkles
} from 'lucide-react';
import Button from '@/components/ui/Button';
import { getGuestSessions } from '@/lib/api';
import { GuestSession } from '@/lib/types';
import { cn } from '@/lib/utils';

export default function GuestSessionsList() {
  const router = useRouter();
  const params = useParams();
  const guestId = params.guestId as string;

  const [sessions, setSessions] = useState<GuestSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSessions() {
      if (!guestId) return;
      try {
        const data = await getGuestSessions(guestId);
        setSessions(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadSessions();
  }, [guestId]);

  return (
    <div className="max-w-[1200px] mx-auto h-[calc(100vh-140px)] flex flex-col">
      <div className="mb-6 flex-shrink-0 flex items-center gap-4">
        <Button variant="secondary" onClick={() => router.back()} className="rounded-full px-3">
          <ArrowLeft className="w-5 h-5 text-[var(--text-secondary)]" />
        </Button>
        <div>
          <h1 className="text-2xl font-space font-bold text-[var(--brand-primary)]">Guest History</h1>
          <p className="text-[var(--text-secondary)]">View past conversations for this guest.</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pb-10">
        {loading ? (
          <div className="p-12 text-center text-[var(--text-tertiary)]">Loading history...</div>
        ) : sessions.length === 0 ? (
          <div className="p-12 text-center text-[var(--text-tertiary)]">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-20" />
            <p>No chat history found for this guest.</p>
          </div>
        ) : (
          sessions.map(session => (
            <div
              key={session.id}
              onClick={() => router.push(`/dashboard/sessions/${guestId}/${session.id}`)}
              className="bg-white p-6 rounded-[var(--radius-lg)] border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] hover:shadow-md transition-all cursor-pointer group relative overflow-hidden"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg",
                    session.top_intent ? "bg-[var(--brand-primary)]/10 text-[var(--brand-primary)]" : "bg-[var(--bg-secondary)] text-[var(--text-tertiary)]"
                  )}>
                    {session.top_intent ? <Sparkles className="w-5 h-5" /> : <MessageSquare className="w-5 h-5" />}
                  </div>
                  <div>
                    <h3 className="font-semibold text-[var(--text-primary)] text-lg">
                      {session.top_intent || "General Conversation"}
                    </h3>
                    <span className="text-xs text-[var(--text-tertiary)] flex items-center mt-1">
                      <Clock className="w-3 h-3 mr-1" />
                      {new Date(session.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className={cn(
                  "px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide",
                  session.origin === 'auto-start' ? "bg-blue-50 text-blue-600 border border-blue-100" : "bg-gray-50 text-gray-600 border border-gray-100"
                )}>
                  {session.origin}
                </div>
              </div>

              {session.summary && (
                <div className="bg-[var(--bg-tertiary)]/30 p-4 rounded-lg mb-4 text-sm text-[var(--text-secondary)] leading-relaxed italic border border-[var(--border-subtle)]/50">
                  &quot;{session.summary}&quot;
                </div>
              )}

              <div className="flex items-center justify-between text-xs text-[var(--text-tertiary)] pt-4 border-t border-[var(--border-subtle)]">
                <div className="flex gap-4">
                  {/* Placeholders for metadata not yet in list view, but ready for layout */}
                  <span className="flex items-center">
                    <MapPin className="w-3.5 h-3.5 mr-1" />
                    {session.city && session.country ? `${session.city}, ${session.country}` : (session.country || "Unknown Location")}
                  </span>
                  <span className="flex items-center">
                    <Smartphone className="w-3.5 h-3.5 mr-1" />
                    {session.device_type ? (session.os ? `${session.device_type} (${session.os})` : session.device_type) : "Unknown Device"}
                  </span>
                </div>
                <span className="text-[var(--brand-primary)] font-medium group-hover:underline flex items-center">
                  View Details <ChevronRight className="w-4 h-4 ml-1" />
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
