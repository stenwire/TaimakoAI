'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { motion } from 'framer-motion';
import { CreditCard, AlertCircle, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useSearchParams, useRouter } from 'next/navigation';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import SubscriptionOverview from '@/components/dashboard/subscription/SubscriptionOverview';
import UsageRates from '@/components/dashboard/subscription/UsageRates';
import PlanPricingGrid, { PlanData } from '@/components/dashboard/subscription/PlanPricingGrid';
import { getBusinessProfile, getPublicPlans, verifySubscriptionTransaction } from '@/lib/api';

interface SubscriptionData {
  subscription_tier?: string;
  subscription_status?: string;
  last_payment_date?: string | null;
  allocated_ai_responses?: number;
  used_ai_responses?: number;
  allocated_escalations?: number;
  used_escalations?: number;
  allocated_messages_per_session?: number;
  allocated_daily_sessions?: number;
  allocated_whitelisted_domains?: number;
  plan_name?: string;
  plan_code?: string;
  plan_price?: number;
  plan_currency?: string;
  plan_interval?: string;
  plan_features?: Record<string, unknown>;
}

function SubscriptionPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [subData, setSubData] = useState<SubscriptionData | null>(null);
  const [plans, setPlans] = useState<PlanData[]>([]);
  const [isPricingOpen, setIsPricingOpen] = useState(false);

  const fetchSubscriptionData = async (showLoader = true) => {
    if (showLoader) setLoading(true);
    setError('');

    try {
      const [businessRes, plansRes] = await Promise.all([
        getBusinessProfile(),
        getPublicPlans()
      ]);

      setSubData(businessRes.data as SubscriptionData);
      setPlans(plansRes.data as PlanData[]);

    } catch (err: unknown) {
      console.error("Failed to load subscription data", err);
      const castedErr = err as { response?: { status?: number } };
      // Don't show extreme error if it just means no business profile yet
      if (castedErr.response?.status !== 404) {
        setError("Failed to load subscription details. Please try again.");
      }
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscriptionData(true);

    // Check for Paystack callback reference
    const reference = searchParams.get('reference');

    if (reference) {
      setSuccess('Payment successful! Verifying your subscription...');
      // Remove query params silently
      router.replace('/dashboard/settings/subscription', { scroll: false });

      // Verify transaction immediately with backend to skip webhook delay
      verifySubscriptionTransaction(reference)
        .then(() => {
          setSuccess('Subscription verified and updated!');
          fetchSubscriptionData(false);
          // clear success message after 5 seconds
          setTimeout(() => setSuccess(''), 5000);
        })
        .catch((err) => {
          console.error("Verification error", err);
          setError('Verification processing... Please refresh in a moment.');

          // Fallback to polling in case verify failed but webhook works
          let attempts = 0;
          const interval = setInterval(async () => {
            attempts++;
            await fetchSubscriptionData(false);
            if (attempts >= 5) clearInterval(interval);
          }, 4000);
        });
    }
  }, [searchParams, router]);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <SkeletonLoader variant="rectangle" className="h-[200px]" />
          <SkeletonLoader variant="rectangle" className="h-[200px]" />
        </div>
        <SkeletonLoader variant="rectangle" className="h-[400px]" />
      </div>
    );
  }

  // Determine actual state logic from backend data
  const currentTier = subData?.subscription_tier || 'spark';
  const hasSavedCard = !!subData?.last_payment_date; // proxy for having an auth code active

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="p-3 bg-[var(--brand-primary)]/10 rounded-[var(--radius-squircle)]">
            <CreditCard className="w-8 h-8 text-[var(--brand-primary)]" />
          </div>
          <div>
            <h1 className="text-h1 text-[var(--text-primary)]">Subscription & Billing</h1>
            <p className="text-body text-[var(--text-secondary)] mt-1">
              Manage your plan, usage limits, and billing details
            </p>
          </div>
        </div>
      </motion.div>

      {/* Notifications */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-[var(--error-bg)] border border-[var(--error)] rounded-[var(--radius-md)] flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 text-[var(--error)] flex-shrink-0 mt-0.5" />
          <p className="text-small text-[var(--error)]">{error}</p>
        </motion.div>
      )}

      {success && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-[var(--success-bg)] border border-[var(--success)] rounded-[var(--radius-md)] flex items-start gap-3"
        >
          <CheckCircle className="w-5 h-5 text-[var(--success)] flex-shrink-0 mt-0.5" />
          <p className="text-small text-[var(--success)]">{success}</p>
        </motion.div>
      )}

      {/* Top Section: Overview & Usage */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-6">
        <SubscriptionOverview
          tier={subData?.subscription_tier || ''}
          status={subData?.subscription_status || ''}
          lastPaymentDate={subData?.last_payment_date || null}
          onUpdate={fetchSubscriptionData}
        />
        <UsageRates
          tier={subData?.subscription_tier || ''}
          allocatedAiResponses={subData?.allocated_ai_responses || 0}
          usedAiResponses={subData?.used_ai_responses || 0}
          allocatedEscalations={subData?.allocated_escalations || 0}
          usedEscalations={subData?.used_escalations || 0}
          planFeatures={subData?.plan_features || null}
        />
      </div>

      {/* Lower Section: Pricing Grid */}
      <div className="pt-6 border-t border-[var(--border-subtle)]">
        <button
          onClick={() => setIsPricingOpen(!isPricingOpen)}
          className="w-full flex items-center justify-between py-4 text-left group"
        >
          <h2 className="text-2xl font-space font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors">
            Ready to scale your AI agent?
          </h2>
          <div className="p-2 rounded-full bg-[var(--bg-secondary)] group-hover:bg-[var(--brand-primary)]/10 transition-colors">
            {isPricingOpen ? (
              <ChevronUp className="w-6 h-6 text-[var(--text-secondary)] group-hover:text-[var(--brand-primary)]" />
            ) : (
              <ChevronDown className="w-6 h-6 text-[var(--text-secondary)] group-hover:text-[var(--brand-primary)]" />
            )}
          </div>
        </button>

        {isPricingOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-6"
          >
            <PlanPricingGrid
              plans={plans}
              currentTier={currentTier}
              hasSavedCard={hasSavedCard}
              onPlanChangeStarted={() => { setError(''); setSuccess(''); }}
              onPlanChangeSuccess={() => {
                setSuccess('Subscription upgraded successfully!');
                fetchSubscriptionData();
                setTimeout(() => setSuccess(''), 5000);
              }}
              onPlanChangeError={(err) => setError(err)}
            />
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default function SubscriptionPage() {
  return (
    <Suspense fallback={<SkeletonLoader variant="rectangle" className="h-[200px]" />}>
      <SubscriptionPageContent />
    </Suspense>
  );
}
