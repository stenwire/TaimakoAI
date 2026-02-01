'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowLeft, MessageSquare, Clock, MapPin, Smartphone,
  ChevronRight, Sparkles, Star, Loader2
} from 'lucide-react';
import Button from '@/components/ui/Button';
import { getGuestSessions, getGuests, toggleLeadStatus } from '@/lib/api';
import { GuestSession, Guest } from '@/lib/types';
import { cn } from '@/lib/utils';

export default function GuestSessionsList() {
  const router = useRouter();
  const params = useParams();
  const guestId = params.guestId as string;

  const [sessions, setSessions] = useState<GuestSession[]>([]);
  const [guest, setGuest] = useState<Guest | null>(null);
  const [loading, setLoading] = useState(true);
  const [togglingLead, setTogglingLead] = useState(false);

  useEffect(() => {
    async function loadData() {
      if (!guestId) return;
      try {
        const [sessionsData, guestsData] = await Promise.all([
          getGuestSessions(guestId),
          getGuests()
        ]);
        setSessions(sessionsData);
        // Find the current guest from the list
        const currentGuest = guestsData.find((g: Guest) => g.id === guestId);
        if (currentGuest) {
          setGuest(currentGuest);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [guestId]);

  const handleToggleLead = async () => {
    if (!guest) return;
    setTogglingLead(true);
    try {
      const updatedGuest = await toggleLeadStatus(guest.id, !guest.is_lead);
      setGuest(updatedGuest);
    } catch (error) {
      console.error('Failed to toggle lead status:', error);
    } finally {
      setTogglingLead(false);
    }
  };

  return (
    <div className="max-w-[1200px] mx-auto h-[calc(100vh-140px)] flex flex-col">
      <div className="mb-6 flex-shrink-0 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <Button variant="secondary" onClick={() => router.back()} className="rounded-full px-3">
            <ArrowLeft className="w-5 h-5 text-[var(--text-secondary)]" />
          </Button>
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-space font-bold text-[var(--brand-primary)]">
                {guest?.name || 'Guest History'}
              </h1>
              {guest?.is_lead && (
                <span className="px-3 py-1 text-sm font-semibold bg-[var(--status-success)]/10 text-[var(--status-success)] rounded-full border border-[var(--status-success)]/20">
                  Lead
                </span>
              )}
            </div>
            <p className="text-[var(--text-secondary)]">View past conversations for this guest.</p>
          </div>
        </div>

        {guest && (
          <button
            onClick={handleToggleLead}
            disabled={togglingLead}
            className={cn(
              "flex items-center justify-center w-full md:w-auto gap-2 px-4 py-2 text-sm font-medium rounded-full transition-all",
              guest.is_lead
                ? "bg-[var(--status-success)]/10 text-[var(--status-success)] hover:bg-[var(--status-success)]/20 border border-[var(--status-success)]/20"
                : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--border-subtle)] border border-[var(--border-subtle)]"
            )}
          >
            {togglingLead ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Star className={cn("w-4 h-4", guest.is_lead && "fill-current")} />
            )}
            {guest.is_lead ? "Lead" : "Mark as Lead"}
          </button>
        )}
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
