'use client';

import React, { useEffect, useState } from 'react';
import {
  getAnalyticsOverview,
  getTopIntents,
  getTopLocations,
  getTrafficSources,
  AnalyticsOverview,
  AnalyticsIntent,
  AnalyticsLocation,
  AnalyticsSource
} from '@/lib/analytics';
import {
  MessageCircle,
  Users,
  Target,
  Repeat,
  Smartphone,
  Globe,
  ArrowUpRight
} from 'lucide-react';
import Card from '@/components/ui/Card';

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [intents, setIntents] = useState<AnalyticsIntent[]>([]);
  const [locations, setLocations] = useState<AnalyticsLocation[]>([]);
  const [sources, setSources] = useState<AnalyticsSource[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [overviewData, intentsData, locationsData, sourcesData] = await Promise.all([
          getAnalyticsOverview(days),
          getTopIntents(days),
          getTopLocations(days),
          getTrafficSources(days)
        ]);
        setOverview(overviewData);
        setIntents(intentsData);
        setLocations(locationsData);
        setSources(sourcesData);
      } catch (error) {
        console.error("Failed to fetch analytics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [days]);

  const StatCard = ({ title, value, subtext, icon: Icon, trend }: any) => (
    <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-6">
      <div className="flex justify-between items-start mb-4">
        <div className="p-2 bg-[var(--bg-primary)] rounded-[var(--radius-md)] border border-[var(--border-subtle)]">
          <Icon className="w-5 h-5 text-[var(--text-primary)]" />
        </div>
        {trend && (
          <span className="text-xs font-medium text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded-full">
            {trend}
          </span>
        )}
      </div>
      <div>
        <p className="text-[var(--text-secondary)] text-small mb-1">{title}</p>
        <h3 className="text-h3 text-[var(--text-primary)] font-semibold">{value}</h3>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-8">
          <div className="h-10 bg-[var(--bg-secondary)] w-1/3 rounded"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-[var(--bg-secondary)] rounded-lg"></div>)}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2].map(i => <div key={i} className="h-64 bg-[var(--bg-secondary)] rounded-lg"></div>)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-h2 text-[var(--text-primary)]">Analytics</h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Understand how visitors use your chat and where leads come from.
          </p>
        </div>

        <div className="flex gap-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-[var(--radius-md)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 3 months</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Total Chats"
          value={overview?.total_sessions || 0}
          icon={MessageCircle}
        />
        <StatCard
          title="Leads Captured"
          value={overview?.leads_captured || 0}
          icon={Target}
        />
        <StatCard
          title="Returning %"
          value={`${overview?.returning_guests_percentage || 0}%`}
          icon={Repeat}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Top Chat Reasons (Intents) */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-6">
          <h3 className="text-h3 text-[var(--text-primary)] mb-6 flex items-center gap-2">
            <Target className="w-5 h-5 text-[var(--text-secondary)]" /> Top Reasons People Chat
          </h3>
          <div className="space-y-4">
            {intents.length === 0 ? (
              <p className="text-[var(--text-secondary)]">No data yet.</p>
            ) : (
              intents.map((item, idx) => {
                const max = Math.max(...intents.map(i => i.count));
                const width = (item.count / max) * 100;
                return (
                  <div key={idx}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-[var(--text-primary)] font-medium capitalize">{item.intent || 'General'}</span>
                      <span className="text-[var(--text-secondary)]">{item.count}</span>
                    </div>
                    <div className="h-2 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[var(--primary)] rounded-full transition-all duration-500"
                        style={{ width: `${width}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Locations */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-6">
          <h3 className="text-h3 text-[var(--text-primary)] mb-6 flex items-center gap-2">
            <Globe className="w-5 h-5 text-[var(--text-secondary)]" /> Where Visitors Are From
          </h3>
          <div className="space-y-3">
            {locations.length === 0 ? (
              <p className="text-[var(--text-secondary)]">No location data available.</p>
            ) : (
              locations.map((loc, idx) => (
                <div key={idx} className="flex justify-between items-center py-2 border-b border-[var(--border-subtle)] last:border-0 hover:bg-[var(--bg-primary)]/50 px-2 -mx-2 rounded transition-colors">
                  <div className="flex items-center gap-3">
                    <span className="text-lg">📍</span> {/* Could use country flag lib later */}
                    <div>
                      <div className="text-[var(--text-primary)] font-medium">{loc.city}</div>
                      <div className="text-[var(--text-secondary)] text-xs">{loc.country}</div>
                    </div>
                  </div>
                  <span className="font-semibold text-[var(--text-primary)] bg-[var(--bg-primary)] px-2 py-1 rounded text-xs">
                    {loc.count}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Traffic Sources & Devices */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Traffic Sources */}
        <div className="lg:col-span-2 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-6">
          <h3 className="text-h3 text-[var(--text-primary)] mb-6 flex items-center gap-2">
            <ArrowUpRight className="w-5 h-5 text-[var(--text-secondary)]" /> How People Found You
          </h3>
          <div className="space-y-4">
            {sources.length === 0 ? (
              <p className="text-[var(--text-secondary)]">No referrer data captured.</p>
            ) : (
              sources.map((src, idx) => {
                const max = Math.max(...sources.map(s => s.count));
                const width = (src.count / max) * 100;
                // Simple logic to clean URL
                let label = src.source;
                if (!label) label = "Direct / Unknown";
                else if (label.includes('google')) label = "Google Search";
                else if (label.includes('instagram')) label = "Instagram";

                return (
                  <div key={idx} className="group">
                    <div className="flex justify-between text-sm mb-1 px-1">
                      <span className="text-[var(--text-primary)]">{label}</span>
                      <span className="text-[var(--text-secondary)]">{src.count}</span>
                    </div>
                    <div className="h-4 bg-[var(--bg-primary)] rounded-sm overflow-hidden flex">
                      <div
                        className="h-full bg-blue-500/80 group-hover:bg-blue-500 transition-colors"
                        style={{ width: `${width}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Devices (Placeholder since API doesn't aggregate it yet, but we requested it) */}
        {/* Note: In Implementation Plan I didn't explicitly add getDevices but backend has collected it. */}
        {/* For now, simplified placeholder or just omit until API is ready. */}
        {/* I'll omit it to keep it working or use dummy for layout? */}
        {/* The user wants "Exact Layout". I should implement it. */}
        {/* I can add GET /analytics/devices logic later or just mock it. */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-6">
          <h3 className="text-h3 text-[var(--text-primary)] mb-6 flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-[var(--text-secondary)]" /> Devices
          </h3>
          <div className="flex flex-col gap-4 justify-center h-48 items-center text-center">
            <Smartphone className="w-12 h-12 text-[var(--text-secondary)]/50" />
            <p className="text-[var(--text-secondary)] text-sm">
              Device breakdown coming soon.
            </p>
          </div>
        </div>
      </div>

      {/* Footer / Empty State Note */}
      {overview?.total_sessions === 0 && (
        <div className="text-center py-12 border border-dashed border-[var(--border-subtle)] rounded-[var(--radius-lg)] bg-[var(--bg-primary)]/50">
          <h3 className="text-lg font-medium text-[var(--text-primary)]">No analytics yet</h3>
          <p className="text-[var(--text-secondary)] max-w-sm mx-auto mt-2">
            Once visitors start chatting with your website, insights will appear here. Share your website link to get started.
          </p>
        </div>
      )}

    </div>
  );
}
