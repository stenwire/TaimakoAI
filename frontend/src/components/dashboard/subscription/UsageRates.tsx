import React from 'react';
import Card from '@/components/ui/Card';
import { Bot, Users, Zap } from 'lucide-react';
import { motion } from 'framer-motion';

interface UsageRatesProps {
  tier: string;
  allocatedAiResponses: number;
  usedAiResponses: number;
  allocatedEscalations: number;
  usedEscalations: number;
  planFeatures: Record<string, any> | null;
}

export default function UsageRates({ tier, allocatedAiResponses, usedAiResponses, allocatedEscalations, usedEscalations, planFeatures }: UsageRatesProps) {
  const totalCredits = allocatedAiResponses || 0;
  const isUnlimitedCredits = totalCredits === -1 || totalCredits > 99999;

  const creditsUsed = usedAiResponses || 0;
  const creditsPercent = isUnlimitedCredits || totalCredits === 0 ? 0 : Math.min(100, Math.round((creditsUsed / totalCredits) * 100));

  const maxEscalations = allocatedEscalations || 0;
  const totalEscalationsUsed = usedEscalations || 0;

  const isUnlimitedEscalations = maxEscalations >= 99999;
  const escalationsPercent = isUnlimitedEscalations || maxEscalations === 0 ? 0 : Math.min(100, Math.round((totalEscalationsUsed / maxEscalations) * 100));

  const isNearLimit = !isUnlimitedCredits && creditsPercent > 85;

  return (
    <Card className="h-full">
      <h3 className="text-lg font-space font-semibold text-[var(--text-primary)] border-b border-[var(--border-subtle)] pb-3 mb-5 flex items-center gap-2">
        <Zap className="w-5 h-5 text-yellow-500" />
        Plan Usage Rates
      </h3>

      <div className="space-y-6">
        {/* AI Agent Responses */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-1.5">
              <Bot className="w-4 h-4" /> AI Responses
            </span>
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              {isUnlimitedCredits ? 'Unlimited' : `${creditsUsed.toLocaleString()} / ${totalCredits.toLocaleString()}`}
            </span>
          </div>

          <div className="w-full h-2 by-[var(--bg-tertiary)] bg-gray-100 rounded-full overflow-hidden relative">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${isUnlimitedCredits ? 100 : creditsPercent}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className={`absolute top-0 left-0 h-full rounded-full ${isUnlimitedCredits ? 'bg-gradient-to-r from-blue-400 to-indigo-500' : isNearLimit ? 'bg-red-500' : 'bg-gradient-to-r from-[var(--brand-primary)] to-[var(--brand-secondary)]'}`}
            />
          </div>

          {!isUnlimitedCredits && isNearLimit && (
            <p className="text-[11px] text-red-500 mt-1.5 font-medium animate-pulse">Running low on credits. Upgrade to avoid interruption.</p>
          )}
        </div>

        {/* Human Escalations */}
        <div className={`pt-4 border-t border-[var(--border-subtle)] ${maxEscalations === 0 ? 'opacity-50' : ''}`}>
          <div className="flex justify-between items-center text-sm md:text-base mb-2">
            <span className="text-[var(--text-secondary)] flex items-center gap-2">
              <Users className="w-4 h-4" />
              Human Escalations
            </span>
            <span className="font-space font-medium text-[var(--text-primary)]">
              {maxEscalations === 0 ? 'N/A' : (isUnlimitedEscalations ? totalEscalationsUsed.toLocaleString() : `${totalEscalationsUsed.toLocaleString()} / ${maxEscalations.toLocaleString()}`)}
            </span>
          </div>
          {maxEscalations === 0 ? (
            <p className="text-[11px] text-[var(--text-tertiary)] mt-1 font-medium">Upgrade plan to unlock Human Handoff</p>
          ) : (
            <p className="text-[11px] text-[var(--text-tertiary)] mt-1 font-medium">Team escalations included</p>
          )}
        </div>
      </div>
    </Card>
  );
}
