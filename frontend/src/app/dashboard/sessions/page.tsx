'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Users, Search, ChevronRight, Mail, Phone, Calendar, Star, Loader2
} from 'lucide-react';
import Card from '@/components/ui/Card';
import { getGuests, toggleLeadStatus } from '@/lib/api';
import { Guest } from '@/lib/types';
import { cn } from '@/lib/utils';

export default function SessionsGuestList() {
  const router = useRouter();
  const [guests, setGuests] = useState<Guest[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [togglingId, setTogglingId] = useState<string | null>(null);

  useEffect(() => {
    async function loadGuests() {
      try {
        const data = await getGuests();
        setGuests(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadGuests();
  }, []);

  const handleToggleLead = async (e: React.MouseEvent, guest: Guest) => {
    e.stopPropagation(); // Prevent row click navigation
    setTogglingId(guest.id);
    try {
      const updatedGuest = await toggleLeadStatus(guest.id, !guest.is_lead);
      setGuests(prev => prev.map(g => g.id === guest.id ? updatedGuest : g));
    } catch (error) {
      console.error('Failed to toggle lead status:', error);
    } finally {
      setTogglingId(null);
    }
  };

  const filteredGuests = guests.filter(g =>
    (g.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (g.email?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-[1600px] mx-auto h-[calc(100vh-140px)] flex flex-col">
      <div className="mb-6 flex-shrink-0 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-space font-bold text-[var(--brand-primary)]">Customer Sessions</h1>
          <p className="text-[var(--text-secondary)]">Browse interactions by customer.</p>
        </div>
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
          <input
            type="text"
            placeholder="Search customers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white border border-[var(--border-subtle)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]/20 focus:border-[var(--brand-primary)]"
          />
        </div>
      </div>

      <div className="flex-1 bg-white rounded-[var(--radius-lg)] border border-[var(--border-subtle)] shadow-sm overflow-hidden flex flex-col">
        {/* Header Row - Hidden on Mobile */}
        <div className="hidden lg:grid grid-cols-12 gap-4 p-4 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]/50 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
          <div className="col-span-4 pl-2">Customer</div>
          <div className="col-span-3">Contact Info</div>
          <div className="col-span-2">First Seen</div>
          <div className="col-span-2 text-center">Lead Status</div>
          <div className="col-span-1 text-right pr-4">Action</div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-12 text-center text-[var(--text-tertiary)]">Loading customers...</div>
          ) : filteredGuests.length === 0 ? (
            <div className="p-12 text-center text-[var(--text-tertiary)] flex flex-col items-center">
              <Users className="w-12 h-12 mb-3 opacity-20" />
              <p>No customers found matching your search.</p>
            </div>
          ) : (
            filteredGuests.map(guest => (
              <div
                key={guest.id}
                onClick={() => router.push(`/dashboard/sessions/${guest.id}`)}
                className="flex flex-col lg:grid lg:grid-cols-12 gap-3 lg:gap-4 p-4 border-b border-[var(--border-subtle)] hover:bg-[var(--bg-primary)] transition-colors cursor-pointer group items-start lg:items-center"
              >
                {/* Customer Info */}
                <div className="w-full lg:col-span-4 lg:pl-2 flex items-center justify-between lg:justify-start gap-3">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-10 h-10 rounded-full text-white flex items-center justify-center font-bold shadow-sm",
                      guest.is_lead ? "bg-[var(--status-success)]" : "bg-[var(--brand-primary)]"
                    )}>
                      {(guest.name || 'A').charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-[var(--text-primary)]">{guest.name || "Anonymous Guest"}</h3>
                        {guest.is_lead && (
                          <span className="lg:hidden px-2 py-0.5 text-xs font-semibold bg-[var(--status-success)]/10 text-[var(--status-success)] rounded-full border border-[var(--status-success)]/20">
                            Lead
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[var(--text-tertiary)] font-mono truncate max-w-[150px]">{guest.id.substring(0, 8)}...</p>
                    </div>
                  </div>
                  {/* Chevron for Mobile only */}
                  <ChevronRight className="w-5 h-5 text-[var(--text-tertiary)] lg:hidden" />
                </div>

                {/* Contact Info */}
                <div className="w-full lg:col-span-3 space-y-1 pl-[52px] lg:pl-0">
                  {guest.email && (
                    <div className="flex items-center text-sm text-[var(--text-secondary)]">
                      <Mail className="w-3.5 h-3.5 mr-2 text-[var(--text-tertiary)]" /> {guest.email}
                    </div>
                  )}
                  {guest.phone && (
                    <div className="flex items-center text-sm text-[var(--text-secondary)]">
                      <Phone className="w-3.5 h-3.5 mr-2 text-[var(--text-tertiary)]" /> {guest.phone}
                    </div>
                  )}
                  {!guest.email && !guest.phone && <span className="text-xs text-[var(--text-tertiary)] italic">No contact info</span>}
                </div>

                {/* Date */}
                <div className="w-full lg:col-span-2 text-sm text-[var(--text-secondary)] flex items-center pl-[52px] lg:pl-0">
                  <Calendar className="w-3.5 h-3.5 mr-2 text-[var(--text-tertiary)]" />
                  {new Date(guest.created_at).toLocaleDateString()}
                </div>

                {/* Lead Toggle & Desktop Status */}
                <div className="w-full lg:col-span-2 flex justify-start lg:justify-center pl-[52px] lg:pl-0 mt-2 lg:mt-0">
                  <div className="flex items-center gap-2">
                    {/* Desktop Lead Badge */}
                    {guest.is_lead && (
                      <span className="hidden lg:inline-block px-2 py-0.5 text-xs font-semibold bg-[var(--status-success)]/10 text-[var(--status-success)] rounded-full border border-[var(--status-success)]/20">
                        Lead
                      </span>
                    )}

                    <button
                      onClick={(e) => handleToggleLead(e, guest)}
                      disabled={togglingId === guest.id}
                      className={cn(
                        "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-all",
                        guest.is_lead
                          ? "bg-[var(--status-success)]/10 text-[var(--status-success)] hover:bg-[var(--status-success)]/20 border border-[var(--status-success)]/20"
                          : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--border-subtle)] border border-[var(--border-subtle)]"
                      )}
                    >
                      {togglingId === guest.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Star className={cn("w-3.5 h-3.5", guest.is_lead && "fill-current")} />
                      )}
                      {guest.is_lead ? "Lead" : "Mark as Lead"}
                    </button>
                  </div>
                </div>

                {/* Desktop Chevron */}
                <div className="hidden lg:flex col-span-1 justify-end pr-4">
                  <button className="p-2 rounded-full hover:bg-[var(--border-subtle)] text-[var(--text-tertiary)] group-hover:text-[var(--brand-primary)] transition-colors">
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
