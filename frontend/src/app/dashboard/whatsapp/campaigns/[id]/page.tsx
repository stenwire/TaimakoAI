'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowLeft, XCircle, Send as SendIcon } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import {
  WhatsAppCampaign,
  WhatsAppCampaignMessage,
  getWhatsAppCampaign,
  listWhatsAppCampaignMessages,
  cancelWhatsAppCampaign,
  sendWhatsAppCampaign,
} from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-gray-200 text-gray-700',
  SCHEDULED: 'bg-blue-100 text-blue-800',
  SENDING: 'bg-yellow-100 text-yellow-800',
  COMPLETED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-gray-100 text-gray-500',
  FAILED: 'bg-red-100 text-red-800',
  QUEUED: 'bg-gray-100 text-gray-700',
  SENT: 'bg-blue-100 text-blue-800',
  DELIVERED: 'bg-green-100 text-green-800',
  READ: 'bg-emerald-100 text-emerald-800',
};

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const campaignId = params?.id as string;

  const [campaign, setCampaign] = useState<WhatsAppCampaign | null>(null);
  const [messages, setMessages] = useState<WhatsAppCampaignMessage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!campaignId) return;
    fetchCampaign();
    const interval = setInterval(() => {
      // poll while sending
      if (campaign?.status === 'SENDING' || campaign?.status === 'SCHEDULED') {
        fetchCampaign();
      }
    }, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, campaign?.status]);

  const fetchCampaign = async () => {
    try {
      const [c, m] = await Promise.all([
        getWhatsAppCampaign(campaignId),
        listWhatsAppCampaignMessages(campaignId, { limit: 500 }),
      ]);
      setCampaign(c);
      setMessages(m.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Cancel this campaign?')) return;
    await cancelWhatsAppCampaign(campaignId);
    await fetchCampaign();
  };

  const handleSendNow = async () => {
    await sendWhatsAppCampaign(campaignId);
    await fetchCampaign();
  };

  if (loading || !campaign) {
    return <SkeletonLoader />;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div>
        <Link
          href="/dashboard/whatsapp/campaigns"
          className="inline-flex items-center gap-1 text-sm text-[var(--text-secondary)] hover:text-[var(--brand-primary)]"
        >
          <ArrowLeft className="w-4 h-4" /> Back to campaigns
        </Link>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">{campaign.name}</h1>
          <div className="flex items-center gap-2 mt-2">
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                STATUS_COLORS[campaign.status] || 'bg-gray-100 text-gray-700'
              }`}
            >
              {campaign.status}
            </span>
            <span className="text-sm text-[var(--text-secondary)]">
              Created {new Date(campaign.created_at).toLocaleString()}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          {campaign.status === 'DRAFT' && (
            <Button onClick={handleSendNow}>
              <SendIcon className="w-4 h-4" /> Send Now
            </Button>
          )}
          {(campaign.status === 'SCHEDULED' || campaign.status === 'SENDING') && (
            <Button variant="secondary" onClick={handleCancel}>
              <XCircle className="w-4 h-4" /> Cancel
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4">
        <Card>
          <div className="text-xs text-[var(--text-secondary)] uppercase">Recipients</div>
          <div className="text-2xl font-bold mt-1">{campaign.total_recipients}</div>
        </Card>
        <Card>
          <div className="text-xs text-[var(--text-secondary)] uppercase">Sent</div>
          <div className="text-2xl font-bold mt-1 text-blue-600">{campaign.sent_count}</div>
        </Card>
        <Card>
          <div className="text-xs text-[var(--text-secondary)] uppercase">Delivered</div>
          <div className="text-2xl font-bold mt-1 text-green-600">{campaign.delivered_count}</div>
        </Card>
        <Card>
          <div className="text-xs text-[var(--text-secondary)] uppercase">Read</div>
          <div className="text-2xl font-bold mt-1 text-emerald-600">{campaign.read_count}</div>
        </Card>
        <Card>
          <div className="text-xs text-[var(--text-secondary)] uppercase">Failed</div>
          <div className="text-2xl font-bold mt-1 text-red-600">{campaign.failed_count}</div>
        </Card>
      </div>

      <Card title="Recipients">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-[var(--text-secondary)] border-b border-[var(--border-subtle)]">
              <tr>
                <th className="py-2">Phone</th>
                <th className="py-2">Status</th>
                <th className="py-2">Sent</th>
                <th className="py-2">Delivered</th>
                <th className="py-2">Read</th>
                <th className="py-2">Error</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((m) => (
                <tr key={m.id} className="border-b border-[var(--border-subtle)]">
                  <td className="py-3 font-mono">{m.contact_phone}</td>
                  <td className="py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        STATUS_COLORS[m.status] || 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td className="py-3 text-xs">{m.sent_at ? new Date(m.sent_at).toLocaleTimeString() : '-'}</td>
                  <td className="py-3 text-xs">{m.delivered_at ? new Date(m.delivered_at).toLocaleTimeString() : '-'}</td>
                  <td className="py-3 text-xs">{m.read_at ? new Date(m.read_at).toLocaleTimeString() : '-'}</td>
                  <td className="py-3 text-xs text-red-600">{m.error_message || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}
