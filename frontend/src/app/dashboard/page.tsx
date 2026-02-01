'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Users, Clock, MessageSquare, Target, ArrowUp, ArrowDown, MapPin, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getAnalyticsOverview, getTopIntents, getTopLocations, getTrafficSources } from '@/lib/api';
import { AnalyticsOverview, IntentStat, TrafficSource, LocationStat } from '@/lib/types';

// --- Components ---

const MetricCard = ({ title, value, delta, label, icon: Icon, delay, className }: { title: string, value: string, delta?: string, label: string, icon: React.ElementType, delay: number, className?: string }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    className={cn("bg-white p-6 rounded-[var(--radius-lg)] border border-[var(--border-subtle)] shadow-[var(--shadow-sm)] flex flex-col justify-between h-full hover:shadow-[var(--shadow-md)] transition-shadow", className)}
  >
    <div className="flex justify-between items-start mb-4">
      <div className="p-2 bg-[var(--bg-tertiary)] rounded-lg">
        <Icon className="w-5 h-5 text-[var(--text-tertiary)]" />
      </div>
      {delta && (
        <div className={cn("flex items-center text-xs font-medium px-2 py-1 rounded-full", delta.startsWith('+') ? "bg-[var(--status-success)]/10 text-[var(--status-success)]" : "bg-[var(--status-error)]/10 text-[var(--status-error)]")}>
          {delta.startsWith('+') ? <ArrowUp className="w-3 h-3 mr-1" /> : <ArrowDown className="w-3 h-3 mr-1" />}
          {delta}
        </div>
      )}
    </div>
    <div>
      <h3 className="text-[32px] font-space font-semibold text-[var(--brand-primary)] tracking-tight mb-1">{value}</h3>
      <p className="text-sm text-[var(--text-secondary)]">{label}</p>
    </div>
  </motion.div>
);

const IntentDonut = ({ intents }: { intents: IntentStat[] }) => {
  const COLORS = ['#0E3F34', '#D46A4C', '#8FAFA4', '#E2E0DD', '#F9FAFB'];
  const total = intents.reduce((acc, curr) => acc + curr.count, 0) || 1;
  let cumulative = 0;

  return (
    <div className="flex flex-col lg:flex-row items-center gap-8 h-full">
      <div className="relative w-40 h-40 flex-shrink-0">
        <svg viewBox="0 0 100 100" className="transform -rotate-90 w-full h-full">
          {intents.length > 0 ? intents.map((intent, i) => {
            const value = (intent.count / total) * 100;
            const start = cumulative;
            cumulative += value;
            const dashArray = `${value} ${100 - value}`;
            const offset = 100 - start;
            return (
              <circle
                key={i}
                cx="50" cy="50" r="40"
                fill="transparent"
                stroke={COLORS[i % COLORS.length]}
                strokeWidth="12"
                strokeDasharray={dashArray}
                strokeDashoffset={offset}
                className="hover:opacity-80 transition-opacity cursor-pointer"
              />
            );
          }) : (
            <circle cx="50" cy="50" r="40" fill="transparent" stroke="#E5E7EB" strokeWidth="12" />
          )}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center flex-col">
          <span className="text-2xl font-bold text-[var(--brand-primary)]">{intents.reduce((a, b) => a + b.count, 0)}</span>
          <span className="text-xs text-[var(--text-tertiary)]">Intents</span>
        </div>
      </div>
      <div className="space-y-3 flex-1">
        {intents.slice(0, 5).map((intent, i) => (
          <div key={intent.intent} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
              <span className="text-[var(--text-secondary)] truncate max-w-[120px]" title={intent.intent}>{intent.intent}</span>
            </div>
            <span className="font-medium text-[var(--text-primary)]">{Math.round((intent.count / total) * 100)}%</span>
          </div>
        ))}
        {intents.length === 0 && <p className="text-sm text-[var(--text-tertiary)]">No intent data yet.</p>}
      </div>
    </div>
  );
};

export default function DashboardOverview() {
  const [metrics, setMetrics] = useState<AnalyticsOverview | null>(null);
  const [intents, setIntents] = useState<IntentStat[]>([]);
  const [locations, setLocations] = useState<LocationStat[]>([]);
  const [sources, setSources] = useState<TrafficSource[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [m, i, l, s] = await Promise.all([
          getAnalyticsOverview(),
          getTopIntents(),
          getTopLocations(),
          getTrafficSources()
        ]);
        setMetrics(m as AnalyticsOverview);
        setIntents(i);
        setLocations(l);
        setSources(s);
      } catch (e) {
        console.error("Failed to load dashboard data", e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <div className="p-8">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-2xl font-space font-bold text-[var(--brand-primary)]">Overview</h1>
        <p className="text-[var(--text-secondary)]">Welcome back. Here&apos;s what&apos;s happening today.</p>
      </div>

      <div className="flex overflow-x-auto snap-x snap-mandatory gap-4 pb-4 -mx-4 px-4 md:grid md:grid-cols-2 lg:grid-cols-4 md:pb-0 md:mx-0 md:px-0 scrollbar-hide">
        <MetricCard
          title="Total Sessions"
          value={metrics?.total_sessions.toLocaleString() || "0"}
          label="Total Sessions"
          icon={MessageSquare}
          delay={0.1}
          className="min-w-[280px] snap-center md:min-w-0"
        />
        <MetricCard
          title="Unique Guests"
          value={metrics?.total_guests.toLocaleString() || "0"}
          label="Unique Guests"
          icon={Users}
          delay={0.2}
          className="min-w-[280px] snap-center md:min-w-0"
        />
        <MetricCard
          title="Leads Captured"
          value={metrics?.leads_captured.toLocaleString() || "0"}
          label="Leads Captured"
          icon={Target}
          delay={0.3}
          className="min-w-[280px] snap-center md:min-w-0"
        />
        <MetricCard
          title="Avg Duration"
          value={`${metrics ? Math.floor(metrics.avg_session_duration / 60) : 0}m ${metrics ? metrics.avg_session_duration % 60 : 0}s`}
          label="Avg Session Duration"
          icon={Clock}
          delay={0.4}
          className="min-w-[280px] snap-center md:min-w-0"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-auto lg:h-[320px]">
        <div className="lg:col-span-8 bg-white p-6 rounded-[var(--radius-lg)] border border-[var(--border-subtle)] shadow-[var(--shadow-sm)]">
          <h3 className="text-lg font-space font-semibold text-[var(--brand-primary)] mb-6">Intent Distribution</h3>
          <IntentDonut intents={intents} />
        </div>

        <div className="lg:col-span-4 bg-[var(--brand-primary)] text-white p-6 rounded-[var(--radius-lg)] shadow-[var(--shadow-glow)] flex flex-col justify-between relative overflow-hidden">
          <div className="relative z-10">
            <h3 className="text-lg font-space font-semibold text-white/90">Returning Guests</h3>
            <p className="text-sm text-white/70 mt-1">Guests engaging more than once</p>
          </div>

          <div className="relative z-10 mt-8">
            <div className="text-[48px] font-space font-bold tracking-tight">{metrics?.returning_guests_percentage || 0}%</div>
            <div className="flex items-center text-sm text-[var(--brand-secondary)] mt-2">
              <RefreshCw className="w-4 h-4 mr-2" />
              <span>Retention Rate</span>
            </div>
          </div>

          <div className="absolute top-0 right-0 w-48 h-48 bg-white/5 rounded-full blur-3xl transform translate-x-12 -translate-y-12" />
          <div className="absolute bottom-0 right-0 w-32 h-32 bg-[var(--brand-accent)]/20 rounded-full blur-2xl transform translate-x-8 translate-y-8" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-6 bg-white p-6 rounded-[var(--radius-lg)] border border-[var(--border-subtle)] shadow-[var(--shadow-sm)] flex flex-col">
          <h3 className="text-lg font-space font-semibold text-[var(--brand-primary)] mb-4">Top Locations</h3>
          <div className="space-y-4 flex-1">
            {locations.map((loc: LocationStat) => (
              <div key={`${loc.country}-${loc.city}`} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-[var(--text-secondary)] font-medium flex items-center">
                    <MapPin className="w-3 h-3 mr-2 text-[var(--text-tertiary)]" />
                    {loc.city ? `${loc.city}, ` : ''}{loc.country}
                  </span>
                  <span className="font-mono text-[var(--text-primary)]">{loc.count}</span>
                </div>
                <div className="h-1.5 w-full bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(loc.count / (locations[0]?.count || 1)) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-[var(--brand-primary)] rounded-full"
                  />
                </div>
              </div>
            ))}
            {locations.length === 0 && <p className="text-sm text-[var(--text-tertiary)]">No location data yet.</p>}
          </div>
        </div>

        <div className="lg:col-span-6 bg-white p-6 rounded-[var(--radius-lg)] border border-[var(--border-subtle)] shadow-[var(--shadow-sm)] flex flex-col">
          <h3 className="text-lg font-space font-semibold text-[var(--brand-primary)] mb-4">Traffic Sources</h3>
          <div className="grid grid-cols-2 gap-4 flex-1">
            {sources.map((item, i) => (
              <div key={item.source} className="p-4 bg-[var(--bg-tertiary)]/30 rounded-[var(--radius-md)] flex flex-col justify-center">
                <div className={`w-2 h-2 rounded-full mb-3 bg-[var(--brand-primary)]`} />
                <div className="text-[24px] font-space font-bold text-[var(--text-primary)]">{item.count}</div>
                <div className="text-xs text-[var(--text-secondary)] uppercase tracking-wider font-bold truncate" title={item.source || 'Direct'}>{item.source || 'Direct'}</div>
              </div>
            ))}
            {sources.length === 0 && <p className="text-sm text-[var(--text-tertiary)]">No traffic data yet.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
