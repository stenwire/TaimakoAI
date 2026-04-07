import React, { useState } from 'react';
import { Check, Loader2 } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { initializeSubscription, upgradeSubscription } from '@/lib/api';

export interface PlanData {
  id: number;
  plan_code: string;
  name: string;
  price: number;
  currency: string;
  interval: string;
  tier: number;
  features: string[];
}

interface PlanPricingGridProps {
  plans: PlanData[];
  currentTier: string;
  hasSavedCard: boolean;
  onPlanChangeStarted: () => void;
  onPlanChangeSuccess: () => void;
  onPlanChangeError: (err: string) => void;
}

export default function PlanPricingGrid({
  plans,
  currentTier,
  hasSavedCard,
  onPlanChangeStarted,
  onPlanChangeError
}: PlanPricingGridProps) {

  const [processingId, setProcessingId] = useState<number | null>(null);

  const handleSelectPlan = async (planId: number, planName: string) => {
    setProcessingId(planId);
    onPlanChangeStarted();

    try {
      let res;
      if (hasSavedCard) {
        // Upgrade flow using saved card
        res = await upgradeSubscription(planId, 'paystack') as { data?: { authorization_url?: string } };
      } else {
        // Checkout flow for new card / initial sub
        res = await initializeSubscription(planId, 'paystack') as { data?: { authorization_url?: string } };
      }

      if (res.data?.authorization_url) {
        window.location.href = res.data.authorization_url;
      } else {
        throw new Error("No authorization URL returned");
      }
    } catch (err: unknown) {
      onPlanChangeError((err as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.detail || (err as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.message || `Failed to process plan change to ${planName}.`);
    } finally {
      // If redirecting, component unmounts; keep loading otherwise
      setProcessingId(null);
    }
  };

  const getActionLabel = (plan: PlanData) => {
    if (processingId === plan.id) return <Loader2 className="w-5 h-5 animate-spin mx-auto" />;
    if (plan.name.toLowerCase() === currentTier?.toLowerCase()) return "Recharge Plan";
    if (plan.price === 0) return "Included";
    if (hasSavedCard) return "Switch to Plan"; // Seamless
    return "Upgrade Now"; // Needs checkout
  };

  const renderPrice = (price: number, currency: string, interval: string) => {
    if (price === 0) return <span className="text-3xl font-space font-bold text-[var(--text-primary)]">Free</span>;
    // Format NGN 1000000 -> 10,000 / month
    // Paystack returns price in kobo/cents usually, but let's assume raw amount represents major currency if formatted by backend, actually Paystack uses kobo. Assuming backend divides by 100 before sending, or if not we format it raw. If backend returns 10000 for N10,000, we format the number.
    const formatted = new Intl.NumberFormat('en-NG', { style: 'currency', currency: currency || 'NGN', maximumFractionDigits: 0 }).format(price);

    return (
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-space font-bold text-[var(--text-primary)]">{formatted}</span>
        <span className="text-sm font-medium text-[var(--text-tertiary)]">/{interval.toLowerCase() === 'annually' ? 'yr' : 'mo'}</span>
      </div>
    );
  };

  const currentPlanObj = plans.find(p => p.name.toLowerCase() === currentTier?.toLowerCase());
  const currentPlanTier = currentPlanObj?.tier ?? 0;

  // Filter plans to only show current and higher plans
  const displayPlans = plans
    .filter(plan => plan.tier >= currentPlanTier)
    .sort((a, b) => a.tier - b.tier);

  const isMaxPlan = displayPlans.length === 1 && displayPlans[0].name.toLowerCase() === currentTier?.toLowerCase();

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {displayPlans.map((plan) => {
          const isCurrent = plan.name.toLowerCase() === currentTier?.toLowerCase();
          const isRecommended = plan.name.toLowerCase() === 'ignite' && !isCurrent;

          return (
            <Card
              key={plan.id}
              className={`relative flex flex-col h-full overflow-hidden transition-all duration-300 ${isCurrent ? 'ring-2 ring-[var(--brand-primary)] shadow-[var(--shadow-glow)]' : isRecommended ? 'ring-1 ring-blue-300 shadow-md' : 'hover:shadow-md'}`}
            >
              {isCurrent && (
                <div className="absolute top-0 right-0 bg-[var(--brand-primary)] text-white text-[10px] font-bold uppercase tracking-wider py-1 px-3 rounded-bl-lg">
                  Active
                </div>
              )}
              {isRecommended && (
                <div className="absolute top-0 right-0 bg-blue-500 text-white text-[10px] font-bold uppercase tracking-wider py-1 px-3 rounded-bl-lg">
                  Recommended
                </div>
              )}

              <div className="mb-6 flex-1">
                <h3 className="text-xl font-space font-bold text-[var(--text-primary)] capitalize mb-2">{plan.name}</h3>
                <p className="text-sm text-[var(--text-secondary)] mb-6 h-10">
                  {plan.price === 0 ? "Perfect for testing the platform." : "For growing businesses needing AI automation at scale."}
                </p>

                <div className="mb-6 pb-6 border-b border-[var(--border-subtle)]">
                  {renderPrice(plan.price, plan.currency, plan.interval)}
                </div>

                <ul className="space-y-4">
                  {(Array.isArray(plan.features) ? plan.features : []).map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-sm text-[var(--text-secondary)]">
                      <span className="p-0.5 bg-green-100 rounded-full flex-shrink-0 mt-0.5">
                        <Check className="w-3 h-3 text-green-600" />
                      </span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-auto pt-6">
                <Button
                  variant={isCurrent ? "secondary" : "primary"}
                  className={`w-full justify-center py-2.5 ${isCurrent ? 'border-[var(--brand-primary)] text-[var(--brand-primary)] hover:bg-[var(--brand-primary)]/10' : ''}`}
                  disabled={processingId !== null}
                  onClick={() => handleSelectPlan(plan.id, plan.name)}
                >
                  {getActionLabel(plan)}
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {isMaxPlan && (
        <div className="mt-8 p-6 bg-[var(--brand-primary)]/5 border border-[var(--brand-primary)]/20 rounded-xl text-center">
          <h3 className="text-xl font-space font-bold text-[var(--text-primary)] mb-2">Looking for More Power?</h3>
          <p className="text-[var(--text-secondary)] mb-6 max-w-2xl mx-auto">
            You are currently on our highest standard plan. If you need custom integration,
            higher volume limits, or dedicated SLAs, let&apos;s talk about an Enterprise plan.
          </p>
          <Button
            variant="primary"
            className="mx-auto"
            onClick={() => window.location.href = "mailto:stephen@dubem.xyz?subject=Enquiry about Custom Enterprise Plan"}
          >
            Contact Sales for Custom Plan
          </Button>
        </div>
      )}
    </div>
  );
}
