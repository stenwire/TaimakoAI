import React, { useState } from 'react';
import { CreditCard, Calendar, AlertTriangle, ShieldCheck } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { cancelSubscription, enableSubscription } from '@/lib/api';

interface SubscriptionOverviewProps {
  tier: string;
  status: string;
  lastPaymentDate: string | null;
  onUpdate: () => void;
}

export default function SubscriptionOverview({ tier, status, lastPaymentDate, onUpdate }: SubscriptionOverviewProps) {
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [enabling, setEnabling] = useState(false);
  const [error, setError] = useState('');

  const getStatusBadge = () => {
    switch (status?.toLowerCase()) {
      case 'active':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-700 border border-green-200 flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5" /> Active</span>;
      case 'non-renewing':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-700 border border-yellow-200 flex items-center gap-1.5 whitespace-nowrap"><AlertTriangle className="w-3.5 h-3.5" /> Cancelling at end of cycle</span>;
      case 'attention':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-700 border border-red-200 flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> Payment Action Required</span>;
      case 'cancelled':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-700 border border-gray-200">Cancelled</span>;
      case 'trial':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-700 border border-blue-200">Trial</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-700 border border-gray-200">{status || 'Unknown'}</span>;
    }
  };

  const handleCancelClick = async () => {
    setError('');
    setCancelling(true);
    try {
      await cancelSubscription('paystack');
      setCancelModalOpen(false);
      onUpdate();
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.detail || (err as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.message || 'Failed to cancel subscription.');
    } finally {
      setCancelling(false);
    }
  };

  const handleEnableClick = async () => {
    setError('');
    setEnabling(true);
    try {
      const res = await enableSubscription('paystack');
      if (res.data?.authorization_url) {
        window.location.href = res.data.authorization_url;
        return; // Redirecting, keep enabling state true
      }
      onUpdate();
      setEnabling(false);
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.detail || (err as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.message || 'Failed to enable auto-recharge.');
      setEnabling(false);
    }
  };

  const canCancel = status === 'active' || status === 'attention';

  return (
    <>
      <Card>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-4 flex-1">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-space font-semibold text-[var(--text-primary)] flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-[var(--brand-primary)]" />
                Current Plan
              </h3>
              {getStatusBadge()}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[13px] text-[var(--text-tertiary)] font-medium uppercase tracking-wider mb-1">Plan Tier</p>
                <p className="text-2xl font-space font-bold text-[var(--text-primary)] capitalize">
                  {tier || 'Spark'}
                </p>
              </div>
              <div>
                <p className="text-[13px] text-[var(--text-tertiary)] font-medium uppercase tracking-wider mb-1">Last Payment</p>
                <div className="flex items-center gap-1.5 text-[var(--text-secondary)] font-medium">
                  <Calendar className="w-4 h-4" />
                  {lastPaymentDate ? new Date(lastPaymentDate).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'N/A'}
                </div>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end justify-center self-stretch border-t md:border-t-0 md:border-l border-[var(--border-subtle)] pt-4 md:pt-0 md:pl-6">
            <div className="flex flex-col gap-3 w-full md:w-auto">
              {status === 'non-renewing' ? (
                <Button
                  variant="primary"
                  className="w-full justify-center md:w-auto whitespace-nowrap"
                  disabled={enabling}
                  loading={enabling}
                  onClick={handleEnableClick}
                >
                  Enable Auto-Recharge
                </Button>
              ) : (
                <Button
                  variant="secondary"
                  className="w-full justify-center md:w-40 border-red-200 text-red-600 hover:bg-red-50"
                  disabled={!canCancel}
                  onClick={() => setCancelModalOpen(true)}
                >
                  Cancel Plan
                </Button>
              )}
              {status === 'non-renewing' && (
                <p className="text-[11px] text-center text-[var(--text-tertiary)] max-w-[160px]">
                  Your plan will not auto recharge at the end of the billing cycle.
                </p>
              )}
            </div>
          </div>
        </div>
      </Card>

      <Modal
        isOpen={cancelModalOpen}
        onClose={() => !cancelling && setCancelModalOpen(false)}
        title="Cancel Subscription?"
      >
        <div className="space-y-4">
          <p className="text-[var(--text-secondary)] text-sm">
            Are you sure you want to cancel your <span className="font-semibold capitalize">{tier}</span> plan?
            You will retain access to your AI agents and features until the end of your current billing cycle.
          </p>

          {error && (
            <div className="p-3 bg-red-50 border border-red-100 rounded-md text-red-600 text-sm flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}

          <div className="flex gap-3 justify-end pt-4">
            <Button variant="secondary" onClick={() => setCancelModalOpen(false)} disabled={cancelling}>
              Keep Plan
            </Button>
            <Button
              variant="primary"
              className="bg-red-600 hover:bg-red-700 border-transparent shadow-[0_0_15px_rgba(220,38,38,0.3)]"
              onClick={handleCancelClick}
              loading={cancelling}
            >
              Yes, Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
