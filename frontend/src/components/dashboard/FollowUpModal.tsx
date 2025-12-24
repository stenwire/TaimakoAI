'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Wand2 } from 'lucide-react';
import Button from '@/components/ui/Button';

interface FollowUpModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (context: string) => Promise<string | void>;
  loading: boolean;
}

export default function FollowUpModal({ isOpen, onClose, onSubmit, loading }: FollowUpModalProps) {
  const [context, setContext] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!context.trim()) return;
    const res = await onSubmit(context);
    if (typeof res === 'string') {
      setResult(res);
    } else {
      // If void, assuming error or handled externally, but let's reset to allow close
      onClose();
    }
  };

  const handleClose = () => {
    setContext('');
    setResult(null);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-white rounded-[var(--radius-lg)] shadow-2xl z-50 overflow-hidden border border-[var(--border-subtle)]"
          >
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[var(--brand-primary)]/10 rounded-lg">
                    <Wand2 className="w-5 h-5 text-[var(--brand-primary)]" />
                  </div>
                  <h3 className="text-lg font-space font-bold text-[var(--text-primary)]">
                    {result ? 'Draft Generated' : 'Generate Follow-up'}
                  </h3>
                </div>
                <button
                  onClick={handleClose}
                  className="text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {result ? (
                <div className="space-y-4">
                  <div className="bg-[var(--bg-secondary)] p-4 rounded-lg border border-[var(--border-subtle)] max-h-[300px] overflow-y-auto text-sm text-[var(--text-primary)] whitespace-pre-wrap">
                    {result}
                  </div>
                  <div className="flex justify-end gap-3">
                    <Button variant="secondary" onClick={handleClose}>Close</Button>
                    <Button
                      variant="primary"
                      onClick={() => {
                        navigator.clipboard.writeText(result);
                        setCopied(true);
                        setTimeout(() => setCopied(false), 2000);
                      }}
                    >
                      {copied ? 'Copied!' : 'Copy to Clipboard'}
                    </Button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmit}>
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                      Additional Context
                    </label>
                    <textarea
                      value={context}
                      onChange={(e) => setContext(e.target.value)}
                      placeholder="E.g., Offer a 15% discount code 'WELCOME15' and mention our new features..."
                      className="w-full h-32 px-4 py-3 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]/20 focus:border-[var(--brand-primary)] resize-none placeholder:text-[var(--text-tertiary)]"
                      autoFocus
                    />
                    <p className="text-xs text-[var(--text-tertiary)] mt-2">
                      Our AI will use this context along with the session history to draft a personalized email.
                    </p>
                  </div>

                  <div className="flex justify-end gap-3">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={handleClose}
                      disabled={loading}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="primary"
                      loading={loading}
                      disabled={!context.trim() || loading}
                      className="bg-[var(--brand-primary)] text-white hover:bg-[var(--brand-primary)]/90 hover:text-white"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      Generate Draft
                    </Button>
                  </div>
                </form>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
