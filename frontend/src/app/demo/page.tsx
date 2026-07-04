'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence, useInView } from 'framer-motion';
import {
  FileText, Bot, BarChart2, Palette, Zap, Copy, Check,
  Mail, AlertTriangle, Smartphone, Package, Upload, Code,
  MessageSquare,
} from 'lucide-react';

// ── Framer Motion variants ──────────────────────────────────────────────────
const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.09 } },
};
const item = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.25, 0.1, 0.25, 1] as const } },
};

// ── Data ────────────────────────────────────────────────────────────────────
const STEPS = [
  { label: 'Choose a Plan', icon: Zap },
  { label: 'Upload Docs', icon: Upload },
  { label: 'Customize Widget', icon: Palette },
  { label: 'Embed Code', icon: Code },
  { label: 'Live Chat', icon: MessageSquare },
  { label: 'Auto-Escalation', icon: AlertTriangle },
  { label: 'Analytics', icon: BarChart2 },
];

const STEP_DURATIONS = [3200, 3500, 3200, 3500, 5800, 4000, 4200];

interface ChatMsg { id: number; sender: 'ai' | 'user'; text: string; }

const CHAT_SCRIPT: Array<{ sender: 'ai' | 'user' | 'typing'; text?: string; delay: number }> = [
  { sender: 'ai', text: "Hi! I'm your AI assistant. How can I help today?", delay: 400 },
  { sender: 'user', text: "What's your return policy?", delay: 1300 },
  { sender: 'typing', delay: 950 },
  { sender: 'ai', text: "We offer a 30-day hassle-free return policy. Items must be unused and in original packaging. Email returns@company.com to begin.", delay: 1900 },
  { sender: 'user', text: "Do you ship internationally?", delay: 1400 },
  { sender: 'typing', delay: 780 },
  { sender: 'ai', text: "Yes! We ship to 45+ countries. International orders arrive in 7–14 business days. Costs are calculated at checkout.", delay: 1700 },
];

const EMBED_CODE = `<script
  src="https://cdn.taimako.ai/widget.js"
  data-widget-id="YOUR_WIDGET_ID"
  async>
</script>`;

const FEATURES = [
  { icon: FileText, title: 'Document-Powered AI', desc: 'Upload PDFs, TXT, Markdown. The AI answers from your knowledge base — no hallucinations, no generic replies.' },
  { icon: Bot, title: 'Multi-Agent System', desc: 'Greeting, retrieval, sentiment, and escalation agents collaborate behind every conversation automatically.' },
  { icon: AlertTriangle, title: 'Smart Escalation', desc: 'Negative sentiment triggers an automatic handoff to your team via email — with full conversation context included.' },
  { icon: BarChart2, title: 'Real-Time Analytics', desc: 'Sessions, intent distribution, geographic reach, and traffic sources — all in one clean dashboard.' },
  { icon: Smartphone, title: 'Web + WhatsApp', desc: 'One platform, two channels. Customers can seamlessly switch to WhatsApp from the chat widget.' },
  { icon: Package, title: 'AI Marketplace', desc: 'Let customers search and order products via chat. AI recommends, records orders, and notifies your team.' },
];

const TIERS = [
  { name: 'Spark', price: 'Free', popular: false, features: ['100 credits/mo', '50 sessions/day', '20 msg/session', '1 domain', '5 escalations/mo'] },
  { name: 'Nexus', price: '₦9,999/mo', popular: true, features: ['1,000 credits/mo', '500 sessions/day', '50 msg/session', '5 domains', '100 escalations/mo'] },
  { name: 'Flux', price: '₦49,999/mo', popular: false, features: ['10,000 credits/mo', '5,000 sessions/day', '100 msg/session', '10 domains', '500 escalations/mo'] },
];

// ── Counter hook ─────────────────────────────────────────────────────────────
function useCounter(target: number, active: boolean, duration = 1300) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!active) return;
    let raf: number;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      setValue(Math.round(target * ease));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, active, duration]);
  return active ? value : 0;
}

// ── Component ────────────────────────────────────────────────────────────────
export default function DemoPage() {
  const [scrolled, setScrolled] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
  const [showTyping, setShowTyping] = useState(false);
  const [typedCode, setTypedCode] = useState('');
  const [codeCopied, setCodeCopied] = useState(false);
  const [analyticsActive, setAnalyticsActive] = useState(false);
  const timeoutRefs = useRef<ReturnType<typeof setTimeout>[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const sessions = useCounter(1247, analyticsActive);
  const guests = useCounter(843, analyticsActive);
  const leads = useCounter(312, analyticsActive);

  const clearAll = useCallback(() => {
    timeoutRefs.current.forEach(clearTimeout);
    timeoutRefs.current = [];
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
  }, []);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', fn, { passive: true });
    return () => window.removeEventListener('scroll', fn);
  }, []);

  // Reset per step
  useEffect(() => {
    clearAll();
    setChatMessages([]);
    setShowTyping(false);
    setTypedCode('');
    setCodeCopied(false);
    setAnalyticsActive(false);
  }, [activeStep, clearAll]);

  // Auto-play
  useEffect(() => {
    if (!isAutoPlaying) return;
    const t = setTimeout(() => setActiveStep(s => (s + 1) % STEPS.length), STEP_DURATIONS[activeStep]);
    timeoutRefs.current.push(t);
    return () => clearTimeout(t);
  }, [isAutoPlaying, activeStep]);

  // Chat sim (step 4)
  useEffect(() => {
    if (activeStep !== 4) return;
    let msgId = 0;
    let delay = 0;
    for (const entry of CHAT_SCRIPT) {
      delay += entry.delay;
      if (entry.sender === 'typing') {
        const d = delay;
        timeoutRefs.current.push(setTimeout(() => setShowTyping(true), d));
      } else {
        const d = delay; const id = msgId++; const sender = entry.sender as 'ai' | 'user'; const text = entry.text!;
        timeoutRefs.current.push(setTimeout(() => { setShowTyping(false); setChatMessages(p => [...p, { id, sender, text }]); }, d));
      }
    }
  }, [activeStep]);

  // Typewriter (step 3)
  useEffect(() => {
    if (activeStep !== 3) return;
    let i = 0;
    intervalRef.current = setInterval(() => {
      i++;
      setTypedCode(EMBED_CODE.slice(0, i));
      if (i >= EMBED_CODE.length && intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
    }, 22);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [activeStep]);

  // Analytics (step 6)
  useEffect(() => {
    if (activeStep !== 6) return;
    timeoutRefs.current.push(setTimeout(() => setAnalyticsActive(true), 200));
  }, [activeStep]);

  // ── Step panels ─────────────────────────────────────────────────────────
  const renderPanel = useCallback(() => {
    switch (activeStep) {
      case 0:
        return (
          <div className="grid grid-cols-3 gap-3 w-full">
            {TIERS.map((tier, i) => (
              <motion.div key={tier.name} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1, duration: 0.4 }}
                style={{ border: tier.popular ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', background: 'var(--bg-secondary)', padding: 16, position: 'relative', boxShadow: tier.popular ? 'var(--shadow-glow)' : 'var(--shadow-sm)' }}>
                {tier.popular && <div style={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', background: 'var(--brand-accent)', color: '#fff', fontSize: 9, fontWeight: 800, padding: '3px 10px', borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap', letterSpacing: '0.04em' }}>MOST POPULAR</div>}
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 14, color: 'var(--text-primary)', marginBottom: 4 }}>{tier.name}</div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 16, color: 'var(--brand-primary)', marginBottom: 12 }}>{tier.price}</div>
                {tier.features.map(f => (
                  <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 6, fontSize: 11, color: 'var(--text-secondary)' }}>
                    <Check size={9} style={{ color: 'var(--brand-primary)', flexShrink: 0 }} />{f}
                  </div>
                ))}
              </motion.div>
            ))}
          </div>
        );

      case 1:
        return (
          <div className="w-full">
            <div style={{ border: '2px dashed var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 24, textAlign: 'center', marginBottom: 16, background: 'var(--bg-secondary)' }}>
              <Upload size={22} style={{ color: 'var(--brand-secondary)', margin: '0 auto 8px', display: 'block' }} />
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Drop files here or click to upload</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>PDF, TXT, MD supported</div>
            </div>
            <div className="flex flex-col gap-2">
              {['product-faq.pdf', 'return-policy.txt', 'shipping-guide.md'].map((file, i) => (
                <motion.div key={file} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 + i * 0.25 }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <FileText size={13} style={{ color: 'var(--brand-primary)' }} />
                    <span style={{ fontSize: 12, color: 'var(--text-primary)' }}>{file}</span>
                  </div>
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 + i * 0.25 }}
                    style={{ fontSize: 10, fontWeight: 700, color: '#fff', background: 'var(--brand-primary)', padding: '2px 8px', borderRadius: 'var(--radius-full)' }}>
                    Indexed
                  </motion.div>
                </motion.div>
              ))}
            </div>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.3 }} className="ai-shimmer"
              style={{ marginTop: 14, padding: '10px 16px', borderRadius: 'var(--radius-md)', textAlign: 'center', fontSize: 12, fontWeight: 600, color: 'var(--brand-primary)', border: '1px solid var(--border-subtle)' }}>
              ✓ Knowledge base ready — 3 documents indexed
            </motion.div>
          </div>
        );

      case 2:
        return (
          <div className="flex gap-4 w-full">
            <div className="flex-1 flex flex-col gap-3">
              {[
                { label: 'Brand Color', content: (
                  <div className="flex items-center gap-2">
                    <motion.div animate={{ backgroundColor: '#0E3F34' }} initial={{ backgroundColor: '#888888' }} transition={{ duration: 1.2, delay: 0.3 }} style={{ width: 28, height: 28, borderRadius: 6 }} />
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>#0E3F34</span>
                  </div>
                )},
                { label: 'Welcome Message', content: <div style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.45 }}>👋 Hi! Ask me anything about our products.</div> },
                { label: 'Channels', content: (
                  <div className="flex gap-2">
                    <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 'var(--radius-full)', background: '#0E3F3418', color: 'var(--brand-primary)', fontWeight: 600 }}>💬 Chat</span>
                    <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 'var(--radius-full)', background: '#25D36618', color: '#16a34a', fontWeight: 600 }}>📱 WhatsApp</span>
                  </div>
                )},
              ].map(({ label, content }) => (
                <div key={label} style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', padding: 12 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', marginBottom: 8 }}>{label}</div>
                  {content}
                </div>
              ))}
            </div>
            <motion.div initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.4 }}
              style={{ width: 155, flexShrink: 0, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', overflow: 'hidden', boxShadow: 'var(--shadow-lg)' }}>
              <div style={{ background: '#0E3F34', padding: '12px 12px 10px', color: '#fff' }}>
                <div style={{ fontSize: 11, fontWeight: 700 }}>AI Support</div>
                <div style={{ fontSize: 10, opacity: 0.7 }}>● Online</div>
              </div>
              <div style={{ padding: 10 }}>
                <div style={{ background: 'var(--bg-tertiary)', borderRadius: '8px 8px 8px 2px', padding: '7px 9px', fontSize: 11, color: 'var(--text-primary)', marginBottom: 8, lineHeight: 1.4 }}>👋 Hi! Ask me anything.</div>
                <div style={{ background: '#0E3F34', borderRadius: '8px 8px 2px 8px', padding: '7px 9px', fontSize: 11, color: '#fff', marginLeft: 'auto', maxWidth: '85%' }}>What are your hours?</div>
              </div>
              <div style={{ padding: '8px 10px', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ background: 'var(--bg-primary)', borderRadius: 'var(--radius-full)', padding: '5px 10px', fontSize: 10, color: 'var(--text-tertiary)' }}>Type a message…</div>
              </div>
            </motion.div>
          </div>
        );

      case 3:
        return (
          <div className="w-full">
            <div style={{ background: '#1e1e1e', borderRadius: 'var(--radius-lg)', overflow: 'hidden', marginBottom: 14 }}>
              <div style={{ padding: '8px 14px', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, color: '#888' }}>index.html</span>
                <button onClick={() => { navigator.clipboard?.writeText(EMBED_CODE); setCodeCopied(true); setTimeout(() => setCodeCopied(false), 2000); }}
                  style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, padding: '2px 6px' }}>
                  {codeCopied ? <><Check size={11} style={{ color: '#4ade80' }} />Copied!</> : <><Copy size={11} />Copy</>}
                </button>
              </div>
              <pre style={{ margin: 0, padding: '16px 14px', fontSize: 12, color: '#a8ff78', fontFamily: 'var(--font-mono)', lineHeight: 1.75, minHeight: 90, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {typedCode}<span style={{ animation: 'blink 1s step-end infinite' }}>▍</span>
              </pre>
            </div>
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.6 }}
              style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '11px 14px', background: '#0E3F3412', borderRadius: 'var(--radius-md)', border: '1px solid #0E3F3428' }}>
              <Check size={15} style={{ color: 'var(--brand-primary)', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--brand-primary)' }}>That&apos;s it — 1 line of code</div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Your AI widget is now live on all configured domains</div>
              </div>
            </motion.div>
          </div>
        );

      case 4:
        return (
          <div style={{ width: '100%', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', overflow: 'hidden', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ background: 'var(--brand-primary)', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={14} color="#fff" />
              </div>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#fff' }}>AI Support</div>
                <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.7)' }}>● Online</div>
              </div>
            </div>
            <div style={{ padding: '12px 14px', minHeight: 185, display: 'flex', flexDirection: 'column', gap: 9 }}>
              {chatMessages.map(msg => (
                <motion.div key={msg.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                  <div style={{ maxWidth: '80%', padding: '8px 12px', fontSize: 12, lineHeight: 1.45, borderRadius: msg.sender === 'user' ? '10px 10px 2px 10px' : '10px 10px 10px 2px', background: msg.sender === 'user' ? 'var(--brand-primary)' : 'var(--bg-tertiary)', color: msg.sender === 'user' ? '#fff' : 'var(--text-primary)' }}>
                    {msg.text}
                  </div>
                </motion.div>
              ))}
              {showTyping && (
                <div style={{ display: 'flex', gap: 4, padding: '9px 12px', background: 'var(--bg-tertiary)', borderRadius: '10px 10px 10px 2px', width: 52 }}>
                  {[0, 1, 2].map(i => (
                    <motion.span key={i} animate={{ y: [0, -4, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.16 }} style={{ display: 'block', width: 5, height: 5, borderRadius: '50%', background: 'var(--text-tertiary)' }} />
                  ))}
                </div>
              )}
            </div>
            <div style={{ padding: '10px 14px', borderTop: '1px solid var(--border-subtle)' }}>
              <div style={{ padding: '8px 12px', borderRadius: 'var(--radius-full)', border: '1px solid var(--border-subtle)', fontSize: 12, color: 'var(--text-tertiary)' }}>Ask a question…</div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="flex flex-col gap-3 w-full">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              style={{ padding: '10px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', textAlign: 'right' }}>
              <span style={{ background: 'var(--brand-primary)', color: '#fff', padding: '7px 12px', borderRadius: '10px 10px 2px 10px', display: 'inline-block', fontSize: 12, lineHeight: 1.4 }}>
                This is so frustrating — I need to speak to a human NOW!
              </span>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.65 }}
              style={{ padding: '12px 14px', background: '#fff8ed', border: '1px solid #fbbf2440', borderLeft: '3px solid var(--brand-accent)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <AlertTriangle size={15} style={{ color: 'var(--brand-accent)', flexShrink: 0, marginTop: 1 }} />
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--brand-accent)' }}>Sentiment Alert: Negative</div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>Escalating to human agent automatically</div>
              </div>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.35 }}
              style={{ padding: '12px 14px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: 10, boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#0E3F3412', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Mail size={14} style={{ color: 'var(--brand-primary)' }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>Email sent to support@company.com</div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Customer requests human support · just now</div>
              </div>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#fff', background: 'var(--brand-primary)', padding: '3px 8px', borderRadius: 'var(--radius-full)', flexShrink: 0 }}>Sent</div>
            </motion.div>
          </div>
        );

      case 6:
        return (
          <div className="flex flex-col gap-3 w-full">
            <div className="grid grid-cols-3 gap-3">
              {[{ label: 'Sessions', value: sessions }, { label: 'Guests', value: guests }, { label: 'Leads', value: leads }].map(m => (
                <div key={m.label} style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', padding: 12, textAlign: 'center' }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: 'var(--brand-primary)', lineHeight: 1 }}>{m.value.toLocaleString()}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>{m.label}</div>
                </div>
              ))}
            </div>
            <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', padding: 14 }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', marginBottom: 12 }}>Top Intents</div>
              {[{ label: 'Product Inquiry', pct: 38 }, { label: 'Shipping', pct: 24 }, { label: 'Returns', pct: 19 }, { label: 'Pricing', pct: 12 }].map((intent, i) => (
                <div key={intent.label} style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4 }}>
                    <span>{intent.label}</span><span style={{ fontWeight: 600 }}>{intent.pct}%</span>
                  </div>
                  <div style={{ height: 6, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                    <motion.div initial={{ width: 0 }} animate={{ width: analyticsActive ? `${intent.pct}%` : 0 }} transition={{ duration: 0.9, delay: 0.2 + i * 0.1, ease: 'easeOut' }}
                      style={{ height: '100%', background: 'var(--brand-primary)', borderRadius: 'var(--radius-full)' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      default: return null;
    }
  }, [activeStep, chatMessages, showTyping, typedCode, codeCopied, analyticsActive, sessions, guests, leads]);

  // ── Scroll-triggered section refs ───────────────────────────────────────
  const howRef = useRef(null);
  const howInView = useInView(howRef, { once: true, margin: '-80px 0px' });
  const featuresRef = useRef(null);
  const featuresInView = useInView(featuresRef, { once: true, margin: '-80px 0px' });
  const pricingRef = useRef(null);
  const pricingInView = useInView(pricingRef, { once: true, margin: '-80px 0px' });

  // ── JSX ─────────────────────────────────────────────────────────────────
  return (
    <>
      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        .demo-tab-btn:hover { background: var(--bg-tertiary) !important; }
      `}</style>

      <div style={{ background: 'var(--bg-primary)', minHeight: '100vh', overflowX: 'hidden' }}>

        {/* ── Navbar ───────────────────────────────────────────────── */}
        <motion.nav
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4 }}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50, height: 60,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '0 32px',
            background: scrolled ? 'rgba(244,241,236,0.92)' : 'transparent',
            backdropFilter: scrolled ? 'blur(12px)' : 'none',
            borderBottom: scrolled ? '1px solid var(--border-subtle)' : '1px solid transparent',
            transition: 'all 0.3s ease',
          }}
        >
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 20, color: 'var(--brand-primary)', letterSpacing: '-0.03em' }}>
            Taimako<span style={{ color: 'var(--brand-accent)' }}>.</span>AI
          </div>
          <Link href="/auth/signup"
            style={{ background: 'var(--brand-primary)', color: '#fff', padding: '8px 22px', borderRadius: 'var(--radius-full)', fontSize: 13, fontWeight: 600, textDecoration: 'none' }}>
            Get Started →
          </Link>
        </motion.nav>

        {/* ── Hero ──────────────────────────────────────────────────── */}
        <section style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', padding: '80px 32px 60px', maxWidth: 1100, margin: '0 auto', position: 'relative' }}>
          {/* bg blobs */}
          <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: '8%', right: '0%', width: 540, height: 540, borderRadius: '50%', background: 'radial-gradient(circle, rgba(143,175,164,0.2) 0%, transparent 68%)' }} />
            <div style={{ position: 'absolute', bottom: '12%', left: '-5%', width: 420, height: 420, borderRadius: '50%', background: 'radial-gradient(circle, rgba(212,106,76,0.1) 0%, transparent 70%)' }} />
          </div>

          <div className="flex flex-col lg:flex-row items-center gap-14 w-full" style={{ position: 'relative' }}>
            {/* Left */}
            <motion.div variants={container} initial="hidden" animate="visible" className="flex-1">
              <motion.div variants={item} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '5px 14px 5px 8px', borderRadius: 'var(--radius-full)', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', marginBottom: 24, fontSize: 12, color: 'var(--text-secondary)' }}>
                <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 0 3px #22c55e30' }} />
                Powered by Google Gemini 2.0 Flash
              </motion.div>

              <motion.h1 variants={item} style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'clamp(36px, 5vw, 58px)', lineHeight: 1.08, letterSpacing: '-0.03em', color: 'var(--text-primary)', margin: '0 0 20px' }}>
                Customer support<br />
                <span style={{ color: 'var(--brand-primary)' }}>that knows</span><br />
                your business.
              </motion.h1>

              <motion.p variants={item} style={{ fontSize: 16, color: 'var(--text-secondary)', lineHeight: 1.65, maxWidth: 480, margin: '0 0 32px' }}>
                Upload your documents. Customize your widget. Paste one line of code.
                Your AI answers customers from your own knowledge base — 24/7.
              </motion.p>

              <motion.div variants={item} className="flex flex-wrap gap-3" style={{ marginBottom: 28 }}>
                <Link href="/auth/signup" style={{ background: 'var(--brand-primary)', color: '#fff', padding: '13px 30px', borderRadius: 'var(--radius-full)', fontSize: 14, fontWeight: 700, textDecoration: 'none' }}>
                  Start for free
                </Link>
                <button onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
                  style={{ background: 'transparent', border: '1.5px solid var(--border-strong)', color: 'var(--text-primary)', padding: '13px 30px', borderRadius: 'var(--radius-full)', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
                  See how it works ↓
                </button>
              </motion.div>

              <motion.div variants={item} className="flex flex-wrap gap-5">
                {['3 min setup', 'No code required', 'Cancel anytime'].map(chip => (
                  <div key={chip} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: 'var(--text-secondary)' }}>
                    <Check size={11} style={{ color: 'var(--brand-primary)' }} />{chip}
                  </div>
                ))}
              </motion.div>
            </motion.div>

            {/* Right — floating widget */}
            <div className="hidden lg:block" style={{ width: 290, flexShrink: 0 }}>
              <motion.div animate={{ y: [0, -10, 0] }} transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
                style={{ background: 'var(--bg-secondary)', borderRadius: 20, border: '1px solid var(--border-subtle)', boxShadow: '0 24px 64px rgba(14,63,52,0.18), 0 0 0 1px rgba(14,63,52,0.04)', overflow: 'hidden' }}>
                <div style={{ background: 'var(--brand-primary)', padding: '16px 16px 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'rgba(255,255,255,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Bot size={18} color="#fff" /></div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#fff' }}>AI Support</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)' }}>● Typically replies instantly</div>
                  </div>
                </div>
                <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 10, minHeight: 175 }}>
                  {[
                    { sender: 'ai', text: '👋 Hi! How can I help you today?' },
                    { sender: 'user', text: 'What payment methods do you accept?' },
                    { sender: 'ai', text: 'We accept Visa, Mastercard, bank transfers, and Paystack. All secured.' },
                  ].map((m, i) => (
                    <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9 + i * 0.5 }}
                      style={{ display: 'flex', justifyContent: m.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                      <div style={{ maxWidth: '80%', padding: '8px 12px', fontSize: 12, lineHeight: 1.4, borderRadius: m.sender === 'user' ? '10px 10px 2px 10px' : '10px 10px 10px 2px', background: m.sender === 'user' ? 'var(--brand-primary)' : 'var(--bg-tertiary)', color: m.sender === 'user' ? '#fff' : 'var(--text-primary)' }}>
                        {m.text}
                      </div>
                    </motion.div>
                  ))}
                </div>
                <div style={{ padding: '10px 14px', borderTop: '1px solid var(--border-subtle)' }}>
                  <div style={{ padding: '8px 12px', borderRadius: 'var(--radius-full)', border: '1px solid var(--border-subtle)', fontSize: 12, color: 'var(--text-tertiary)', background: 'var(--bg-primary)' }}>Type a message…</div>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* ── How It Works ─────────────────────────────────────────── */}
        <section id="how-it-works" ref={howRef} style={{ padding: '80px 32px', maxWidth: 1100, margin: '0 auto' }}>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={howInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.5 }}
            style={{ textAlign: 'center', marginBottom: 56 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--brand-accent)', marginBottom: 10 }}>How it works</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'clamp(28px, 4vw, 42px)', letterSpacing: '-0.025em', color: 'var(--text-primary)', margin: '0 0 14px' }}>Up and running in three steps</h2>
            <p style={{ fontSize: 15, color: 'var(--text-secondary)', maxWidth: 480, margin: '0 auto' }}>No engineering team required. Just follow the steps and your AI support widget is live.</p>
          </motion.div>

          <div style={{ position: 'relative' }}>
            <div className="hidden md:block" style={{ position: 'absolute', top: 30, left: '16.67%', right: '16.67%', height: 2, background: 'var(--bg-tertiary)', zIndex: 0 }}>
              <motion.div initial={{ scaleX: 0 }} animate={howInView ? { scaleX: 1 } : {}} transition={{ duration: 0.9, ease: 'easeOut', delay: 0.3 }}
                style={{ height: '100%', background: 'var(--brand-primary)', transformOrigin: 'left', borderRadius: 2 }} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8" style={{ position: 'relative', zIndex: 1 }}>
              {[
                { step: '01', icon: Upload, title: 'Upload your docs', desc: 'Upload PDFs, TXT, or Markdown files. Our pipeline chunks, embeds, and indexes them into ChromaDB automatically.' },
                { step: '02', icon: Palette, title: 'Customize & embed', desc: "Set your brand color, welcome message, and copy one line of JavaScript into your site's <head>. Done." },
                { step: '03', icon: Bot, title: 'AI handles the rest', desc: 'Customers chat, the AI answers from your documents, and sentiment-aware escalation routes to a human when needed.' },
              ].map((s, i) => (
                <motion.div key={s.step} initial={{ opacity: 0, y: 32 }} animate={howInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.5, delay: 0.1 + i * 0.18 }}
                  style={{ textAlign: 'center', padding: '0 16px' }}>
                  <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'var(--brand-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', boxShadow: 'var(--shadow-glow)' }}>
                    <s.icon size={24} color="#fff" />
                  </div>
                  <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', color: 'var(--brand-accent)', marginBottom: 8 }}>STEP {s.step}</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 17, color: 'var(--text-primary)', marginBottom: 10 }}>{s.title}</div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.65 }}>{s.desc}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Interactive Demo ──────────────────────────────────────── */}
        <section style={{ background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)', padding: '80px 32px' }}>
          <div style={{ maxWidth: 1100, margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: 48 }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--brand-accent)', marginBottom: 10 }}>Interactive Demo</div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'clamp(26px, 4vw, 40px)', letterSpacing: '-0.025em', color: 'var(--text-primary)', margin: '0 0 10px' }}>See Taimako in action</h2>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>Click any step to explore, or watch the auto-play tour.</p>
            </div>

            <div className="flex flex-col lg:flex-row gap-8 items-start">
              {/* Tab list */}
              <div className="flex flex-row lg:flex-col overflow-x-auto lg:overflow-visible gap-1 lg:gap-1 pb-2 lg:pb-0" style={{ flexShrink: 0, width: '100%', maxWidth: 220 }}>
                {STEPS.map((step, i) => {
                  const Icon = step.icon;
                  const active = i === activeStep;
                  return (
                    <button key={step.label} className="demo-tab-btn" onClick={() => { setIsAutoPlaying(false); setActiveStep(i); }}
                      style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '10px 12px', borderRadius: 'var(--radius-md)', border: 'none', cursor: 'pointer', textAlign: 'left', whiteSpace: 'nowrap', flexShrink: 0, background: active ? '#0E3F3410' : 'transparent', borderLeft: `3px solid ${active ? 'var(--brand-primary)' : 'transparent'}`, transition: 'all 0.18s ease' }}>
                      <Icon size={13} style={{ color: active ? 'var(--brand-primary)' : 'var(--text-tertiary)', flexShrink: 0 }} />
                      <span style={{ fontSize: 12, fontWeight: active ? 700 : 500, color: active ? 'var(--brand-primary)' : 'var(--text-secondary)' }}>{step.label}</span>
                      {active && <motion.div layoutId="dot" style={{ marginLeft: 'auto', width: 6, height: 6, borderRadius: '50%', background: 'var(--brand-primary)', flexShrink: 0 }} />}
                    </button>
                  );
                })}
                <button onClick={() => setIsAutoPlaying(p => !p)}
                  style={{ marginTop: 12, padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', background: isAutoPlaying ? 'var(--brand-primary)' : 'transparent', color: isAutoPlaying ? '#fff' : 'var(--text-secondary)', fontSize: 11, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s', flexShrink: 0 }}>
                  {isAutoPlaying ? '⏸ Pause' : '▶ Auto-play'}
                </button>
              </div>

              {/* Panel */}
              <div className="flex-1" style={{ background: 'var(--bg-primary)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', padding: 24, minHeight: 340, boxShadow: 'var(--shadow-md)' }}>
                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--brand-accent)', marginBottom: 3 }}>Step {activeStep + 1} of {STEPS.length}</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 16, color: 'var(--text-primary)' }}>{STEPS[activeStep].label}</div>
                </div>
                {isAutoPlaying && (
                  <div style={{ height: 3, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-full)', marginBottom: 18, overflow: 'hidden' }}>
                    <motion.div key={activeStep} initial={{ width: '0%' }} animate={{ width: '100%' }} transition={{ duration: STEP_DURATIONS[activeStep] / 1000, ease: 'linear' }}
                      style={{ height: '100%', background: 'var(--brand-primary)', borderRadius: 'var(--radius-full)' }} />
                  </div>
                )}
                <AnimatePresence mode="wait">
                  <motion.div key={activeStep} initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -14 }} transition={{ duration: 0.28 }}>
                    {renderPanel()}
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </div>
        </section>

        {/* ── Features ─────────────────────────────────────────────── */}
        <section ref={featuresRef} style={{ padding: '80px 32px', maxWidth: 1100, margin: '0 auto' }}>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={featuresInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.5 }}
            style={{ textAlign: 'center', marginBottom: 48 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--brand-accent)', marginBottom: 10 }}>Everything you need</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'clamp(26px, 4vw, 40px)', letterSpacing: '-0.025em', color: 'var(--text-primary)', margin: 0 }}>Built for serious businesses</h2>
          </motion.div>
          <motion.div variants={container} initial="hidden" animate={featuresInView ? 'visible' : 'hidden'}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(f => (
              <motion.div key={f.title} variants={item} className="hover-lift"
                style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', padding: 24, boxShadow: 'var(--shadow-sm)' }}>
                <div style={{ width: 44, height: 44, borderRadius: 'var(--radius-md)', background: '#0E3F3410', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                  <f.icon size={20} style={{ color: 'var(--brand-primary)' }} />
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 15, color: 'var(--text-primary)', marginBottom: 8 }}>{f.title}</div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.65 }}>{f.desc}</div>
                <div style={{ width: 28, height: 3, borderRadius: 'var(--radius-full)', background: 'var(--brand-accent)', marginTop: 18 }} />
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* ── Pricing ──────────────────────────────────────────────── */}
        <section ref={pricingRef} style={{ background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-subtle)', padding: '80px 32px' }}>
          <div style={{ maxWidth: 900, margin: '0 auto' }}>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={pricingInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.5 }}
              style={{ textAlign: 'center', marginBottom: 48 }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--brand-accent)', marginBottom: 10 }}>Pricing</div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'clamp(26px, 4vw, 40px)', letterSpacing: '-0.025em', color: 'var(--text-primary)', margin: '0 0 12px' }}>Transparent pricing at every scale</h2>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', maxWidth: 400, margin: '0 auto' }}>Start free, upgrade as you grow. No hidden fees.</p>
            </motion.div>
            <motion.div variants={container} initial="hidden" animate={pricingInView ? 'visible' : 'hidden'}
              className="grid grid-cols-1 sm:grid-cols-3 gap-5 items-center">
              {TIERS.map(tier => (
                <motion.div key={tier.name} variants={item}
                  style={{ position: 'relative', borderRadius: 'var(--radius-lg)', padding: 28, background: tier.popular ? 'var(--brand-primary)' : 'var(--bg-primary)', border: tier.popular ? 'none' : '1px solid var(--border-subtle)', boxShadow: tier.popular ? '0 20px 48px rgba(14,63,52,0.28)' : 'var(--shadow-sm)', transform: tier.popular ? 'scale(1.05)' : 'scale(1)' }}>
                  {tier.popular && (
                    <div style={{ position: 'absolute', top: -14, left: '50%', transform: 'translateX(-50%)', background: 'var(--brand-accent)', color: '#fff', fontSize: 10, fontWeight: 800, padding: '4px 14px', borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap', letterSpacing: '0.04em' }}>
                      MOST POPULAR
                    </div>
                  )}
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18, color: tier.popular ? '#fff' : 'var(--text-primary)', marginBottom: 6 }}>{tier.name}</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 26, color: tier.popular ? '#fff' : 'var(--brand-primary)', marginBottom: 22, letterSpacing: '-0.02em' }}>{tier.price}</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
                    {tier.features.map(f => (
                      <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: tier.popular ? 'rgba(255,255,255,0.82)' : 'var(--text-secondary)' }}>
                        <div style={{ width: 16, height: 16, borderRadius: '50%', background: tier.popular ? 'rgba(255,255,255,0.18)' : '#0E3F3412', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                          <Check size={9} style={{ color: tier.popular ? '#fff' : 'var(--brand-primary)' }} />
                        </div>
                        {f}
                      </div>
                    ))}
                  </div>
                  <Link href="/auth/signup" style={{ display: 'block', textAlign: 'center', padding: '11px 0', borderRadius: 'var(--radius-full)', fontSize: 13, fontWeight: 700, textDecoration: 'none', background: tier.popular ? '#fff' : 'var(--brand-primary)', color: tier.popular ? 'var(--brand-primary)' : '#fff' }}>
                    Get started
                  </Link>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── CTA + Footer ─────────────────────────────────────────── */}
        <footer style={{ background: 'var(--brand-primary)', padding: '80px 32px 44px' }}>
          <div style={{ maxWidth: 680, margin: '0 auto', textAlign: 'center' }}>
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-60px 0px' }} transition={{ duration: 0.5 }}>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'clamp(28px, 4vw, 44px)', letterSpacing: '-0.025em', color: '#fff', margin: '0 0 16px', lineHeight: 1.1 }}>
                Ready to transform your<br />customer support?
              </h2>
              <p style={{ fontSize: 15, color: 'rgba(255,255,255,0.62)', marginBottom: 36, lineHeight: 1.65 }}>
                Join businesses using Taimako to deliver instant, document-grounded AI support.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link href="/auth/signup" style={{ background: '#fff', color: 'var(--brand-primary)', padding: '13px 32px', borderRadius: 'var(--radius-full)', fontSize: 14, fontWeight: 700, textDecoration: 'none' }}>
                  Start free today
                </Link>
                <Link href="/auth/login" style={{ background: 'rgba(255,255,255,0.1)', color: '#fff', border: '1px solid rgba(255,255,255,0.22)', padding: '13px 32px', borderRadius: 'var(--radius-full)', fontSize: 14, fontWeight: 600, textDecoration: 'none' }}>
                  Log in →
                </Link>
              </div>
            </motion.div>
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.12)', marginTop: 60, paddingTop: 28, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 16, color: '#fff', letterSpacing: '-0.02em' }}>
                Taimako<span style={{ color: 'var(--brand-accent)' }}>.</span>AI
              </div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.38)' }}>© 2026 Taimako. All rights reserved.</div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
