'use client';

import React, { useEffect, useState } from 'react';
import Tabs from '@/components/ui/Tabs';
import { Activity, Users, Globe, Target } from 'lucide-react';
import Card from '@/components/ui/Card';
import { getTopIntents, getTopLocations, getTrafficSources, getAnalyticsOverview } from '@/lib/api';
import { IntentStat, TrafficSource, AnalyticsOverview, LocationStat } from '@/lib/types';

// TrendChart Component
const TrendChart = ({ days, setDays }: { days: number, setDays: (d: number) => void }) => {
  const [chartData, setChartData] = React.useState<{ date: string; label: string; count: number }[]>([]);
  const [max, setMax] = React.useState(0);

  useEffect(() => {
    async function load() {
      try {
        const apiData = await import('@/lib/api').then(m => m.getTrafficTrend(days));

        // Fill in missing days
        const filledData = [];
        const today = new Date();
        for (let i = days - 1; i >= 0; i--) {
          const d = new Date(today);
          d.setDate(d.getDate() - i);
          const dateStr = d.toISOString().split('T')[0];
          const found = apiData.find(item => item.date === dateStr);
          filledData.push({
            date: dateStr,
            label: `${d.getDate()}/${d.getMonth() + 1}`, // D/M format
            count: found ? found.count : 0
          });
        }

        setChartData(filledData);
        setMax(Math.max(...filledData.map(d => d.count), 1));
      } catch (e) { console.error(e); }
    }
    load();
  }, [days]);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="text-xs text-[var(--text-tertiary)]">Sessions per day</div>
        <div className="flex gap-2">
          {[7, 14, 30].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`text-xs px-2 py-1 rounded transition-colors ${days === d ? 'bg-[var(--brand-primary)] text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'}`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>
      <div className="h-48 flex items-end gap-1 pt-4 border-b border-[var(--border-subtle)] pb-1 overflow-x-auto">
        {chartData.map((item) => (
          <div key={item.date} className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end min-w-[8px]">
            <div
              className="w-full bg-[var(--brand-primary)]/80 rounded-t-sm hover:bg-[var(--brand-primary)] transition-all min-w-[4px] relative"
              style={{ height: `${(item.count / max) * 100}%` }}
            >
              {/* Zero state helper: if count is 0, show a tiny pixel line so it's not invisible? OR just empty. Let's leave empty but hoverable if needed? No, height 0 is invisible. */}
              {item.count > 0 && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block bg-black text-white text-[10px] py-1 px-2 rounded whitespace-nowrap z-10">
                  {item.date}: {item.count} sessions
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      {/* X-Axis Labels (Show sparse labels) */}
      <div className="flex justify-between text-[10px] text-[var(--text-tertiary)] px-1">
        {chartData.filter((_, i) => i % Math.ceil(days / 5) === 0).map(item => (
          <span key={item.date}>{item.label}</span>
        ))}
      </div>
    </div>
  );
};

export default function AnalyticsPage() {
  const [intents, setIntents] = useState<IntentStat[]>([]);
  const [locations, setLocations] = useState<LocationStat[]>([]);
  const [sources, setSources] = useState<TrafficSource[]>([]);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trendDays, setTrendDays] = useState(14); // State for trend filter
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [i, l, s, o] = await Promise.all([
          getTopIntents(),
          getTopLocations(),
          getTrafficSources(),
          getAnalyticsOverview()
        ]);
        setIntents(i);
        setLocations(l);
        setSources(s);
        setOverview(o as AnalyticsOverview);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <div className="p-8">Loading analytics...</div>;

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-2xl font-space font-bold text-[var(--brand-primary)]">Analytics</h1>
        <p className="text-[var(--text-secondary)]">Deep insights into your customer interactions.</p>
      </div>

      <Tabs
        tabs={[
          {
            id: 'engagement',
            label: 'Engagement',
            content: (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card title="Traffic Trend" subtitle="Daily sessions volume">
                  <TrendChart days={trendDays} setDays={setTrendDays} />
                </Card>
                <Card title="Avg Session Duration" subtitle="Distribution of chat lengths">
                  <div className="h-64 flex items-center justify-center text-[var(--text-tertiary)] bg-[var(--bg-tertiary)]/30 rounded-lg border border-dashed border-[var(--border-subtle)]">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-[var(--brand-primary)]">{overview ? Math.floor(overview.avg_session_duration / 60) : 0}m {overview ? overview.avg_session_duration % 60 : 0}s</div>
                      <p className="mt-2 text-sm">Average across {overview?.total_sessions} sessions</p>
                    </div>
                  </div>
                </Card>
              </div>
            )
          },
          {
            id: 'intent',
            label: 'Intent Intelligence',
            content: (
              <div className="space-y-6">
                <Card title="Top Intents" subtitle="Most frequent conversation topics">
                  <div className="space-y-4">
                    {intents.map(i => (
                      <div key={i.intent} className="flex justify-between items-center p-3 bg-[var(--bg-secondary)] rounded-md">
                        <span className="font-medium">{i.intent}</span>
                        <span className="font-mono bg-white px-2 py-1 rounded text-xs border border-[var(--border-subtle)]">{i.count}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )
          },
          {
            id: 'geo',
            label: 'Geography',
            content: (
              <Card title="Global Reach" subtitle="Sessions by country">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {locations.map((loc: LocationStat) => (
                    <div key={loc.country} className="p-4 bg-[var(--bg-secondary)] rounded-lg text-center">
                      <div className="text-lg font-bold">{loc.country}</div>
                      <div className="text-sm text-[var(--text-secondary)]">{loc.city || 'Unknown City'}</div>
                      <div className="mt-2 font-mono text-xl">{loc.count}</div>
                    </div>
                  ))}
                </div>
              </Card>
            )
          },
          {
            id: 'acquisition',
            label: 'Acquisition',
            content: (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="col-span-3">
                  <h3 className="font-space font-bold mb-4">Traffic Sources</h3>
                  <div className="grid grid-cols-1 gap-4">
                    {sources.map(s => (
                      <div key={s.source} className="p-4 border border-[var(--border-subtle)] rounded-lg">
                        <div className="text-sm text-[var(--text-secondary)] uppercase break-all">{s.source || 'Direct'}</div>
                        <div className="text-2xl font-bold mt-1">{s.count}</div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )
          }
        ]}
      />
    </div>
  );
}
