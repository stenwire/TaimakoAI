'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Send, Bot, User, Sparkles, RotateCcw } from 'lucide-react';
import Button from '@/components/ui/Button';
import { chatWithAgent } from '@/lib/api';
import type { Message } from '@/lib/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const hasMessages = messages.length > 0;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await chatWithAgent(userMessage);
      setMessages((prev) => [
        ...prev,
        {
          role: 'agent',
          content: response.response,
          sources: response.sources
        }
      ]);
    } catch (error) {
      console.error('Chat failed:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'agent', content: 'Sorry, I encountered an error processing your request.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setInput('');
  };

  // Sample questions for the initial state
  const sampleQuestions = [
    "What services do you offer?",
    "How can I contact support?",
    "Tell me about your pricing"
  ];

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col max-w-5xl mx-auto">
      {/* Header - Always visible */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-4 flex-shrink-0"
      >
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-[var(--brand-accent)] to-[var(--brand-primary)] rounded-xl shadow-lg">
            <MessageSquare className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">Test Your AI Agent</h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Preview how your customers will experience your AI agent
            </p>
          </div>
        </div>
        {hasMessages && (
          <Button
            variant="ghost"
            onClick={handleReset}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            New Chat
          </Button>
        )}
      </motion.div>

      {/* Main Chat Container */}
      <div className="flex-1 bg-[var(--bg-primary)] rounded-2xl border border-[var(--border-subtle)] shadow-sm overflow-hidden flex flex-col min-h-0">

        {/* Empty State - Centered content with input */}
        {!hasMessages ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="text-center max-w-lg"
            >
              {/* Icon */}
              <div className="mx-auto w-20 h-20 bg-gradient-to-br from-[var(--brand-accent)]/20 to-[var(--brand-primary)]/20 rounded-2xl flex items-center justify-center mb-6">
                <Sparkles className="w-10 h-10 text-[var(--brand-accent)]" />
              </div>

              {/* Title */}
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-3">
                Test Your AI Agent
              </h2>
              <p className="text-[var(--text-secondary)] mb-8">
                Ask questions to see how your AI agent responds to your customers
              </p>

              {/* Sample Questions */}
              <div className="flex flex-wrap justify-center gap-2 mb-8">
                {sampleQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInput(question)}
                    className="px-4 py-2 text-sm bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-full border border-[var(--border-subtle)] transition-all duration-200 hover:shadow-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>

              {/* Initial Input - Prominent design */}
              <form onSubmit={handleSubmit} className="w-full max-w-xl mx-auto">
                <div className="relative">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask something your customers would ask..."
                    className="w-full px-5 py-4 pr-14 text-base bg-[var(--bg-secondary)] text-[var(--text-primary)] border-2 border-[var(--border-subtle)] rounded-2xl placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--brand-accent)] focus:ring-4 focus:ring-[var(--brand-accent)]/10 transition-all duration-200"
                  />
                  <button
                    type="submit"
                    disabled={!input.trim() || loading}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-[var(--brand-primary)] hover:bg-[var(--brand-primary)]/90 disabled:bg-[var(--bg-tertiary)] disabled:cursor-not-allowed text-white rounded-xl transition-all duration-200 shadow-sm"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        ) : (
          <>
            {/* Messages Area - Scrollable */}
            <div
              ref={messagesContainerRef}
              className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0"
            >
              <AnimatePresence initial={false}>
                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                    className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    {/* Avatar */}
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm ${msg.role === 'user'
                          ? 'bg-[var(--brand-primary)]'
                          : 'bg-gradient-to-br from-[var(--brand-accent)] to-[var(--brand-primary)]'
                        }`}
                    >
                      {msg.role === 'user' ? (
                        <User className="w-4 h-4 text-white" />
                      ) : (
                        <Bot className="w-4 h-4 text-white" />
                      )}
                    </div>

                    {/* Message Bubble */}
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                          ? 'bg-[var(--brand-primary)] text-white rounded-tr-md'
                          : 'bg-[var(--bg-secondary)] text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-tl-md'
                        }`}
                    >
                      {msg.role === 'agent' ? (
                        <div className="prose prose-sm max-w-none break-words text-[var(--text-primary)] [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      )}

                      {/* Sources */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-[var(--border-subtle)]">
                          <p className="text-[11px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">
                            Sources
                          </p>
                          <div className="space-y-1.5">
                            {msg.sources.slice(0, 2).map((source, idx) => (
                              <div
                                key={idx}
                                className="text-[11px] text-[var(--text-secondary)] bg-[var(--bg-primary)] p-2 rounded-lg border border-[var(--border-subtle)] line-clamp-2"
                              >
                                {source.slice(0, 120)}...
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Loading Indicator */}
              {loading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-3"
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--brand-accent)] to-[var(--brand-primary)] flex items-center justify-center flex-shrink-0 shadow-sm">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-[var(--bg-secondary)] rounded-2xl rounded-tl-md px-4 py-3 border border-[var(--border-subtle)]">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 bg-[var(--text-tertiary)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-[var(--text-tertiary)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-[var(--text-tertiary)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Fixed Input Area - Only shown when there are messages */}
            <div className="flex-shrink-0 border-t border-[var(--border-subtle)] p-4 bg-[var(--bg-primary)]">
              <form onSubmit={handleSubmit} className="flex gap-3 items-center">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-3 text-sm bg-[var(--bg-secondary)] text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-xl placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--brand-accent)] focus:ring-2 focus:ring-[var(--brand-accent)]/10 transition-all duration-200"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || loading}
                  className="p-3 bg-[var(--brand-primary)] hover:bg-[var(--brand-primary)]/90 disabled:bg-[var(--bg-tertiary)] disabled:cursor-not-allowed text-white rounded-xl transition-all duration-200 shadow-sm flex-shrink-0"
                >
                  {loading ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
