'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import {
  MessageSquare,
  Phone,
  Clock,
  RotateCcw,
  Menu as MenuIcon,
  X,
  Send
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Types
interface WidgetConfig {
  public_widget_id: string;
  theme: string;
  primary_color: string;
  icon_url?: string;
  welcome_message?: string;
  initial_ai_message?: string;
  whatsapp_enabled?: boolean;
  whatsapp_number?: string;
}

interface Message {
  id: string;
  sender: 'guest' | 'ai';
  message_text: string;
  created_at: string;
}

interface GuestStartResponse {
  guest_id: string;
  widget_owner_id: string;
  status: string;
}

interface SessionHistory {
  id: string;
  created_at: string;
  last_message_at: string;
  origin: string;
  summary?: string;
}

import { BACKEND_URL } from '@/config';

export default function WidgetPage() {
  const params = useParams();
  const publicWidgetId = params.public_widget_id as string;

  const [config, setConfig] = useState<WidgetConfig | null>(null);
  const [guestId, setGuestId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [view, setView] = useState<'loading' | 'actions' | 'form' | 'chat'>('loading');
  const [showMenu, setShowMenu] = useState(false);
  const [history, setHistory] = useState<SessionHistory[]>([]);
  const [viewingHistory, setViewingHistory] = useState(false);

  const [formData, setFormData] = useState({ name: '', email: '', phone: '' });
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);

  // === CRITICAL: Listen for focus command from parent (widget.js) ===
  useEffect(() => {
    const handleFocusMessage = (event: MessageEvent) => {
      if (event.data.type === "TAIMAKO_WIDGET_FOCUS") {
        if (view === 'form' && nameInputRef.current) {
          nameInputRef.current.focus();
          nameInputRef.current.select();
        } else if (view === 'chat' && inputRef.current) {
          inputRef.current.focus();
        }
      }
    };

    window.addEventListener("message", handleFocusMessage);
    return () => window.removeEventListener("message", handleFocusMessage);
  }, [view]);

  // Re-focus chat input when clicking background
  const handleContainerClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (view === 'chat' && inputRef.current && !target.closest('button, input, textarea, a')) {
      inputRef.current.focus();
    }
  };

  // Load Config
  useEffect(() => {
    if (!publicWidgetId) return;

    fetch(`${BACKEND_URL}/widgets/config/${publicWidgetId}`)
      .then(res => {
        if (!res.ok) throw new Error('Config load failed');
        return res.json();
      })
      .then(data => {
        setConfig(data);
        const storedGuestId = localStorage.getItem(`taimako_guest_${publicWidgetId}`);
        if (storedGuestId) {
          setGuestId(storedGuestId);
          // On refresh, start FRESH (Clean Slate) even if we know the guest
          // So we do NOT load stored session or fetch messages.
          // So we do NOT load stored session or fetch messages.
          // Just go to 'chat' view with empty list.
          if (data.initial_ai_message && data.initial_ai_message.trim()) {
            setMessages([{
              id: "init-" + Date.now(),
              sender: 'ai',
              message_text: data.initial_ai_message,
              created_at: new Date().toISOString()
            }]);
          } else {
            setMessages([]);
          }
          setView('chat');
        } else {
          // If WhatsApp enabled, show actions choice first
          if (data.whatsapp_enabled) {
            setView('actions');
          } else {
            setView('form');
          }
        }
      })
      .catch(err => {
        console.error(err);
        setView('form');
      });
  }, [publicWidgetId]);

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleStartChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || (!formData.email && !formData.phone)) {
      setError("Please provide name and either email or phone.");
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      const payload = {
        name: formData.name,
        email: formData.email || null,
        phone: formData.phone || null,
      };

      const res = await fetch(`${BACKEND_URL}/widgets/guest/start/${publicWidgetId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Failed to start chat');

      const data: GuestStartResponse = await res.json();
      setGuestId(data.guest_id);
      localStorage.setItem(`taimako_guest_${publicWidgetId}`, data.guest_id);
      setView('chat');
      setSessionId(null); // Explicitly no session yet
      setSessionId(null); // Explicitly no session yet

      // Set initial message if available
      if (config?.initial_ai_message && config.initial_ai_message.trim()) {
        setMessages([{
          id: "init-" + Date.now(),
          sender: 'ai',
          message_text: config.initial_ai_message,
          created_at: new Date().toISOString()
        }]);
      } else {
        setMessages([]); // Clear messages
      }

      setTimeout(() => inputRef.current?.focus(), 300);
    } catch (err) {
      console.error(err);
      setError("Error starting chat. Please try again.");
      setTimeout(() => setError(null), 3000);
    }
  };

  const handleSendMessage = async (e: React.FormEvent | React.KeyboardEvent | React.MouseEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !guestId || sending) return;

    const userMsg: Message = {
      id: "temp-" + Date.now(),
      sender: 'guest',
      message_text: inputText,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setSending(true);
    scrollToBottom();

    try {
      let res;
      if (!sessionId) {
        // Collect Context
        const userAgent = navigator.userAgent;
        let browser = "Unknown";
        if (userAgent.indexOf("Chrome") > -1) browser = "Chrome";
        else if (userAgent.indexOf("Safari") > -1) browser = "Safari";
        else if (userAgent.indexOf("Firefox") > -1) browser = "Firefox";

        let os = "Unknown";
        if (userAgent.indexOf("Win") > -1) os = "Windows";
        else if (userAgent.indexOf("Mac") > -1) os = "macOS";
        else if (userAgent.indexOf("Android") > -1) os = "Android";
        else if (userAgent.indexOf("iPhone") > -1) os = "iOS";

        const isMobile = /Mobi|Android/i.test(userAgent);

        // Read URL params passed from widget.js
        // Since we are in an iframe, window.location.search should have them? 
        // Or better: use Next.js useSearchParams if available, but for simplicity:
        const urlParams = new URLSearchParams(window.location.search);

        const context = {
          device_type: isMobile ? "mobile" : "desktop",
          browser: browser,
          os: os,
          timezone: urlParams.get("tz") || Intl.DateTimeFormat().resolvedOptions().timeZone,
          referrer: urlParams.get("ref") || document.referrer,
          // UTMs could be parsed from 'loc' (the parent URL)
          // loc is the parent page URL
          // Let's rely on backend or just pass what we can. 
          // Parsing UTMs from 'loc' string:
        };

        const loc = urlParams.get("loc");
        if (loc) {
          try {
            const url = new URL(loc);
            const utmSource = url.searchParams.get("utm_source");
            const utmMedium = url.searchParams.get("utm_medium");
            const utmCampaign = url.searchParams.get("utm_campaign");
            if (utmSource) Object.assign(context, { utm_source: utmSource });
            if (utmMedium) Object.assign(context, { utm_medium: utmMedium });
            if (utmCampaign) Object.assign(context, { utm_campaign: utmCampaign });
          } catch (e) { }
        }

        // Start NEW session
        res = await fetch(`${BACKEND_URL}/widgets/guest/session/init/${publicWidgetId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            guest_id: guestId,
            message: userMsg.message_text,
            origin: viewingHistory ? "resumed" : "auto-start",
            context: context
          })
        });
      } else {
        // Continue existing session
        res = await fetch(`${BACKEND_URL}/widgets/chat/${publicWidgetId}/session/${sessionId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userMsg.message_text })
        });
      }

      if (!res.ok) throw new Error("Send failed");

      const data = await res.json();

      // If we got a session back (from init), store it
      // How do we get the session ID from init response? 
      // Checking backend... `process_chat_message` returns `WidgetChatResponse`.
      // `WidgetChatResponse` contains `message` (GuestMessageSchema) which has `session_id`!
      if (data.message && data.message.session_id) {
        setSessionId(data.message.session_id);
      }

      setMessages(prev => {
        const clean = prev.filter(m => m.id !== userMsg.id);
        return [...clean, data.message, data.response];
      });
      scrollToBottom();
    } catch (err) {
      console.error(err);
      setError("Failed to send message. Please try again.");
      setTimeout(() => setError(null), 3000);
    } finally {
      setSending(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleNewChat = () => {
    if (config?.initial_ai_message && config.initial_ai_message.trim()) {
      setMessages([{
        id: "init-" + Date.now(),
        sender: 'ai',
        message_text: config.initial_ai_message,
        created_at: new Date().toISOString()
      }]);
    } else {
      setMessages([]);
    }
    setSessionId(null);
    setViewingHistory(false);
    setShowMenu(false);
    // NOTE: We could track 'origin' here in a ref if needed to send 'manual'
    // For now, next message creates session.
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const handleHistoryClick = async () => {
    if (!guestId) return;
    try {
      const res = await fetch(`${BACKEND_URL}/widgets/sessions/${guestId}/history`);
      if (res.ok) {
        const response = await res.json();
        // Handle standardized response wrapper (data.data) or raw array
        const historyData = response.data || response;
        setHistory(Array.isArray(historyData) ? historyData : []);
        setViewingHistory(true);
        setShowMenu(false);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleResumeSession = async (sid: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/widgets/session/${sid}/messages`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
        setSessionId(sid);
        setViewingHistory(false);
        scrollToBottom();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleWhatsAppClick = () => {
    if (!config?.whatsapp_number) return;

    // Format message
    const businessName = config.welcome_message?.includes("Hi there!") ? "the team" : "us"; // Fallback logic, ideally we have business name
    // Actually we don't have business name in config, maybe just universal greeting
    const text = encodeURIComponent(`Hi, I would like to chat with you.`);

    // Open WhatsApp
    window.open(`https://wa.me/${config.whatsapp_number}?text=${text}`, '_blank');
  };

  const primaryColor = config?.primary_color || '#000000';

  if (!config && view === 'loading') {
    return <div className="p-4 text-center text-gray-600">Loading...</div>;
  }

  return (
    <div
      className="flex flex-col bg-white relative overflow-hidden"
      style={{
        height: '100dvh',
        touchAction: 'manipulation',
        transform: 'translateZ(0)',
        WebkitFontSmoothing: 'antialiased',
        '--primary-color': primaryColor,
      } as React.CSSProperties}
      onClick={handleContainerClick}
    >
      {/* Header */}
      <div className="bg-[var(--primary-color)] text-white p-4 flex items-center justify-between shadow-md shrink-0 z-10 transition-colors duration-300">
        <h1 className="text-lg font-semibold flex items-center gap-2">
          {view === 'actions' ? (
            <span className="flex items-center gap-2">👋 Welcome</span>
          ) : (
            <span className="flex items-center gap-2">
              {view === 'chat' && <MessageSquare className="w-5 h-5" />} Support
            </span>
          )}
        </h1>
        {(view === 'chat' || view === 'actions') && (
          <button onClick={() => setShowMenu(!showMenu)} className="p-1 hover:bg-white/10 rounded transition-colors">
            <MenuIcon className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Menu / Sidebar Overlay */}
      {showMenu && (
        <div className="absolute inset-0 bg-black/50 z-40 animate-in fade-in duration-200" onClick={() => setShowMenu(false)}>
          <div
            className="absolute top-0 right-0 bottom-0 w-64 bg-white shadow-xl z-50 flex flex-col animate-in slide-in-from-right duration-200"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
              <span className="font-semibold text-gray-700 flex items-center gap-2">
                <MenuIcon className="w-4 h-4" /> Menu
              </span>
              <button onClick={() => setShowMenu(false)} className="text-gray-500 hover:text-gray-700 p-1 rounded-full hover:bg-gray-200 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-2 space-y-1">
              <button
                onClick={handleNewChat}
                className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 flex items-center gap-3 text-gray-700 transition-colors"
              >
                <div className="bg-blue-100 p-2 rounded-full text-blue-600">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <span className="font-medium">New Chat</span>
              </button>

              {config?.whatsapp_enabled && (
                <button
                  onClick={() => {
                    handleWhatsAppClick();
                    setShowMenu(false);
                  }}
                  className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 flex items-center gap-3 text-gray-700 transition-colors"
                >
                  <div className="bg-green-100 p-2 rounded-full text-green-600">
                    <Phone className="w-4 h-4" />
                  </div>
                  <span className="font-medium">WhatsApp</span>
                </button>
              )}

              <button
                onClick={handleHistoryClick}
                className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 flex items-center gap-3 text-gray-700 transition-colors"
              >
                <div className="bg-purple-100 p-2 rounded-full text-purple-600">
                  <Clock className="w-4 h-4" />
                </div>
                <span className="font-medium">History</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Toast */}
      {error && (
        <div className="absolute top-16 left-4 right-4 bg-red-500 text-white text-sm px-4 py-2 rounded-lg shadow-lg z-50 animate-pulse pointer-events-none flex items-center gap-2">
          <span className="font-bold">!</span> {error}
        </div>
      )}

      {/* Actions View (New) */}
      {view === 'actions' && (
        <div className="flex-1 p-6 flex flex-col justify-center animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="text-center space-y-2 mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[var(--primary-color)] text-white shadow-lg mb-4">
              {config?.icon_url ? <img src={config.icon_url} className="w-10 h-10 object-contain" /> : <MessageSquare className="w-8 h-8" />}
            </div>
            <h2 className="text-2xl font-bold text-gray-900">How would you like to connect?</h2>
            <p className="text-gray-500 max-w-[80%] mx-auto">Choose the channel that works best for you.</p>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => setView('form')}
              className="w-full bg-[var(--primary-color)] text-white p-4 rounded-xl shadow-lg hover:brightness-90 transition-all transform hover:-translate-y-1 flex items-center justify-between group"
            >
              <div className="flex items-center gap-4">
                <div className="bg-white/20 p-2 rounded-lg">
                  <MessageSquare className="w-6 h-6" />
                </div>
                <div className="text-left">
                  <div className="font-bold">Chat with AI</div>
                  <div className="text-xs text-white/80">Instant responses</div>
                </div>
              </div>
              <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                <Send className="w-5 h-5" />
              </div>
            </button>

            <button
              onClick={handleWhatsAppClick}
              className="w-full bg-[#25D366] text-white p-4 rounded-xl shadow-lg hover:brightness-90 transition-all transform hover:-translate-y-1 flex items-center justify-between group"
            >
              <div className="flex items-center gap-4">
                <div className="bg-white/20 p-2 rounded-lg">
                  <Phone className="w-6 h-6" />
                </div>
                <div className="text-left">
                  <div className="font-bold">WhatsApp</div>
                  <div className="text-xs text-white/80">Drop a message</div>
                </div>
              </div>
              <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                <Send className="w-5 h-5 -rotate-45" />
              </div>
            </button>
          </div>

          <button
            onClick={() => setView('form')}
            className="mt-8 text-gray-400 text-sm hover:text-[var(--primary-color)] transition-colors underline decoration-dotted"
          >
            Continue to form &rarr;
          </button>
        </div>
      )}

      {/* Form View */}
      {view === 'form' && (
        <div className="flex-1 p-6 flex flex-col justify-center overflow-y-auto">
          <div className="flex justify-start mb-6">
            <div className="bg-white p-3 rounded-lg rounded-bl-none shadow-sm text-sm border border-gray-200 max-w-[80%]">
              {config?.welcome_message || "Hi there!"}
            </div>
          </div>

          <h2 className="text-xl font-bold mb-4 text-gray-800">Start a Conversation</h2>
          <p className="text-gray-600 mb-6">Please tell us a bit about yourself to get started.</p>

          <form onSubmit={handleStartChat} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                ref={nameInputRef}
                type="text"
                required
                autoFocus
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-black shadow-sm focus:border-[var(--primary-color)] focus:ring-2 focus:ring-[var(--primary-color)] focus:outline-none sm:text-sm transition-colors"
                value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-black shadow-sm focus:border-[var(--primary-color)] focus:ring-2 focus:ring-[var(--primary-color)] focus:outline-none sm:text-sm transition-colors"
                value={formData.email}
                onChange={e => setFormData({ ...formData, email: e.target.value })}
              />
            </div>

            <div className="text-center text-sm text-gray-500">- OR -</div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Phone</label>
              <input
                type="tel"
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-black shadow-sm focus:border-[var(--primary-color)] focus:ring-2 focus:ring-[var(--primary-color)] focus:outline-none sm:text-sm transition-colors"
                value={formData.phone}
                onChange={e => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 px-4 rounded-md shadow-sm text-sm font-medium text-white bg-[var(--primary-color)] hover:brightness-90 focus:outline-none focus:ring-4 focus:ring-[var(--primary-color)]/30 transition-all"
            >
              Start Chat
            </button>
          </form>
        </div>
      )}

      {/* History View */}
      {view === 'chat' && viewingHistory && (
        <div className="flex-1 overflow-y-auto bg-gray-50 p-4">
          <div className="flex items-center gap-2 mb-4">
            <button onClick={() => setViewingHistory(false)} className="text-gray-500 hover:text-black">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
            </button>
            <h2 className="font-semibold text-gray-800">History</h2>
          </div>

          <div className="space-y-3">
            {history.length === 0 ? (
              <div className="text-center text-gray-400 mt-10">No past conversations.</div>
            ) : (
              history.map(session => (
                <div
                  key={session.id}
                  onClick={() => handleResumeSession(session.id)}
                  className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 cursor-pointer hover:border-[var(--primary-color)] transition-colors"
                >
                  <div className="flex justify-between items-start mb-1">
                    <div className="font-medium text-gray-800 text-sm truncate max-w-[70%]">
                      {session.summary || "Conversation"}
                      {/* Fallback to date if no summary */}
                      {!session.summary && new Date(session.created_at).toLocaleDateString()}
                    </div>
                    <div className="text-xs text-gray-400 whitespace-nowrap">
                      {new Date(session.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 flex gap-2">
                    <span className={`px-1.5 py-0.5 rounded bg-gray-100 ${session.origin === 'manual' ? 'text-blue-600' : 'text-gray-600'}`}>
                      {session.origin}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Chat View */}
      {view === 'chat' && !viewingHistory && (
        <>
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.length === 0 && (
              <div className="text-center text-gray-400 mt-8 text-sm">
                Start a new conversation...
              </div>
            )}
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.sender === 'guest' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 text-sm shadow-sm ${msg.sender === 'guest'
                    ? 'bg-[var(--primary-color)] text-white rounded-br-none'
                    : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none'
                    }`}
                >
                  <div
                    className={`prose prose-sm max-w-none break-words
                      ${msg.sender === 'guest'
                        ? 'text-white prose-headings:text-white prose-strong:text-white prose-p:text-white prose-li:text-white prose-ul:text-white prose-ol:text-white prose-a:text-white/90 prose-a:underline prose-code:text-white prose-code:bg-white/20'
                        : 'text-gray-800 prose-headings:text-gray-800 prose-strong:text-gray-800 prose-p:text-gray-800 prose-li:text-gray-800 prose-ul:text-gray-800 prose-ol:text-gray-800 prose-a:text-blue-600 prose-a:underline prose-code:text-gray-800 prose-code:bg-gray-100'}
                      [&>ul]:list-disc [&>ul]:pl-4 [&>ol]:list-decimal [&>ol]:pl-4 [&>li]:my-0.5 [&>p]:my-1 [&:first-child]:mt-0 [&:last-child]:mb-0
                    `}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // Force paragraphs to have minimal margins for chat compactness
                        p: ({ node, ...props }) => <p className="mb-1 last:mb-0" {...props} />,
                        // Ensure lists are compact
                        ul: ({ node, ...props }) => <ul className="pl-4 mb-1 list-disc" {...props} />,
                        ol: ({ node, ...props }) => <ol className="pl-4 mb-1 list-decimal" {...props} />,
                        li: ({ node, ...props }) => <li className="mb-0.5" {...props} />
                      }}
                    >
                      {msg.message_text}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2 text-xs text-gray-500 italic animate-pulse">
                  Typing...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="bg-white border-t border-gray-200 p-4 shrink-0">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                className="flex-1 rounded-full border border-gray-300 px-4 py-2.5 text-sm focus:border-[var(--primary-color)] focus:ring-2 focus:ring-[var(--primary-color)]/30 focus:outline-none text-black transition-all"
                placeholder="Type a message..."
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSendMessage(e)}
                disabled={sending}
                autoComplete="off"
                autoFocus
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputText.trim() || sending}
                className="bg-[var(--primary-color)] text-white rounded-full p-3 hover:brightness-90 disabled:opacity-50 transition-all shadow-md"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            </div>
            <div className="text-center mt-2 text-xs text-gray-400">
              Powered by Taimako.AI
            </div>
          </div>
        </>
      )}
    </div>
  );
}