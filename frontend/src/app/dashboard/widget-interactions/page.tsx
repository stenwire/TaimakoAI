'use client';

import { useState, useEffect } from 'react';
import { getAccessToken, generateFollowUp } from '@/lib/api';
import Card from '@/components/ui/Card';
import Modal from '@/components/ui/Modal';
import { User, MessageSquare, Clock, Smartphone, RefreshCw, RotateCcw, Sparkles, ChevronLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { BACKEND_URL } from '@/config';

interface GuestVisitor {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  created_at: string;
}

interface Session {
  id: string;
  created_at: string;
  last_message_at: string;
  origin: 'manual' | 'auto-start' | 'resumed';
  summary?: string;
  summary_generated_at?: string;
  top_intent?: string;
}

interface Message {
  id: string;
  sender: 'guest' | 'ai';
  message_text: string;
  created_at: string;
}

export default function WidgetInteractionsPage() {
  const [guests, setGuests] = useState<GuestVisitor[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal State
  const [selectedGuest, setSelectedGuest] = useState<GuestVisitor | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);

  useEffect(() => {
    fetchGuests();
  }, []);

  const fetchGuests = async () => {
    try {
      const token = getAccessToken();
      const res = await fetch(`${BACKEND_URL}/widgets/guests`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setGuests(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadSessions = async (guest: GuestVisitor) => {
    setSelectedGuest(guest);
    setLoadingSessions(true);
    setSessions([]);
    setSelectedSessionId(null);
    setMessages([]);

    try {
      const token = getAccessToken();
      const res = await fetch(`${BACKEND_URL}/widgets/sessions/${guest.id}/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        // Automatically select first session if exists
        if (data.length > 0) {
          loadSessionTranscript(data[0].id);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSessions(false);
    }
  };

  const [analyzing, setAnalyzing] = useState(false);

  const analyzeSession = async (sessionId: string) => {
    setAnalyzing(true);
    try {
      const token = getAccessToken();
      const res = await fetch(`${BACKEND_URL}/widgets/session/${sessionId}/analyze`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const updatedSession = await res.json();
        // Update local state
        setSessions(prev => prev.map(s => s.id === sessionId ? updatedSession : s));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzing(false);
    }
  };

  // Follow-up Logic
  const [followUpType, setFollowUpType] = useState('email');
  const [followUpInfo, setFollowUpInfo] = useState('');
  const [generatingFollowUp, setGeneratingFollowUp] = useState(false);
  const [followUpResult, setFollowUpResult] = useState('');

  const handleGenerateFollowUp = async () => {
    if (!selectedSessionId) return;
    setGeneratingFollowUp(true);
    try {
      const res = await generateFollowUp(selectedSessionId, followUpType, followUpInfo);
      if (res.data?.content) setFollowUpResult(res.data.content);
    } catch (e) { console.error(e); } finally { setGeneratingFollowUp(false); }
  };

  const loadSessionTranscript = async (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setLoadingMessages(true);
    setFollowUpResult(''); // Clear previous result
    setFollowUpInfo('');   // Clear previous info
    try {
      const token = getAccessToken();
      const res = await fetch(`${BACKEND_URL}/widgets/session/${sessionId}/messages`, { // New endpoint for session msgs
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setMessages(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMessages(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    });
  };

  const getOriginBadge = (origin: string) => {
    switch (origin) {
      case 'manual':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"><Smartphone className="w-3 h-3 mr-1" /> Manual</span>;
      case 'auto-start':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800"><RefreshCw className="w-3 h-3 mr-1" /> Auto</span>;
      case 'resumed':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800"><RotateCcw className="w-3 h-3 mr-1" /> Resumed</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">{origin}</span>;
    }
  };

  if (loading) return <div className="p-8">Loading visitors...</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Guest Interactions</h1>
        <p className="text-gray-500 mt-2">View visitors who have interacted with your chat widget.</p>
      </div>

      <Card className="overflow-hidden">
        {guests.length === 0 ? (
          <div className="p-12 text-center text-gray-400">
            <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p>No interactions yet.</p>
          </div>
        ) : (
          <div className="flex flex-col">
            {/* Header - Desktop Only */}
            <div className="hidden lg:grid grid-cols-12 gap-4 px-6 py-4 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wider">
              <div className="col-span-4">Visitor</div>
              <div className="col-span-4">Contact</div>
              <div className="col-span-3">First Seen</div>
              <div className="col-span-1 text-right">Action</div>
            </div>

            {/* List */}
            <div className="divide-y divide-gray-200">
              {guests.map((guest) => (
                <div key={guest.id} className="flex flex-col lg:grid lg:grid-cols-12 gap-4 px-6 py-4 hover:bg-gray-50 transition-colors">

                  {/* Visitor Name */}
                  <div className="lg:col-span-4 flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm">
                      {guest.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{guest.name}</div>
                      <div className="lg:hidden text-xs text-gray-500 mt-0.5">ID: {guest.id.substring(0, 8)}</div>
                    </div>
                  </div>

                  {/* Contact */}
                  <div className="lg:col-span-4 flex items-center text-sm text-gray-900">
                    <span className="lg:hidden w-20 text-gray-500 text-xs uppercase mr-2">Contact:</span>
                    {guest.email || guest.phone || '-'}
                  </div>

                  {/* Date */}
                  <div className="lg:col-span-3 flex items-center text-sm text-gray-500">
                    <span className="lg:hidden w-20 text-gray-500 text-xs uppercase mr-2">Seen:</span>
                    {formatDate(guest.created_at)}
                  </div>

                  {/* Action */}
                  <div className="lg:col-span-1 flex items-center justify-start lg:justify-end mt-2 lg:mt-0">
                    <button
                      onClick={() => loadSessions(guest)}
                      className="w-full lg:w-auto px-4 py-2 lg:px-0 lg:py-0 bg-indigo-50 lg:bg-transparent text-indigo-600 rounded-md lg:rounded-none text-sm font-medium hover:text-indigo-900 hover:bg-indigo-100 transition-colors text-center"
                    >
                      View History
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Guest Sessions & Chat Modal */}
      {selectedGuest && (
        <Modal
          isOpen={!!selectedGuest}
          onClose={() => setSelectedGuest(null)}
          title={`History for ${selectedGuest.name}`}
          className="max-w-5xl w-full h-[90vh] lg:h-auto overflow-hidden flex flex-col"
        >
          <div className="flex-1 flex flex-col lg:flex-row border rounded-md overflow-hidden bg-white h-[600px] lg:h-[600px] w-full relative">

            {/* Sidebar: Sessions List */}
            {/* Hidden on mobile if session selected */}
            <div className={`flex-col bg-gray-50 w-full lg:w-1/3 border-r border-gray-200 transition-all absolute lg:relative inset-0 z-10 lg:z-0 ${selectedSessionId ? 'hidden lg:flex' : 'flex'}`}>
              <div className="p-3 border-b border-gray-200 bg-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider flex justify-between items-center">
                <span>Sessions</span>
                <span className="text-[10px] font-normal normal-case bg-white px-2 py-0.5 rounded border border-gray-200">{sessions.length} total</span>
              </div>

              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {loadingSessions ? (
                  <div className="flex flex-col items-center justify-center h-40 space-y-3">
                    <RefreshCw className="w-5 h-5 animate-spin text-gray-300" />
                    <span className="text-gray-400 text-sm">Loading sessions...</span>
                  </div>
                ) : sessions.length === 0 ? (
                  <div className="text-center p-8 text-gray-400 text-sm bg-white rounded border border-dashed border-gray-200 m-2">
                    <Clock className="w-8 h-8 mx-auto mb-2 opacity-20" />
                    No sessions found.
                  </div>
                ) : (
                  sessions.map(session => (
                    <div
                      key={session.id}
                      onClick={() => loadSessionTranscript(session.id)}
                      className={`p-3 rounded-md cursor-pointer border transition-all active:scale-[0.98] ${selectedSessionId === session.id
                        ? 'bg-white border-indigo-500 shadow-sm ring-1 ring-indigo-500 z-10'
                        : 'bg-white border-gray-200 hover:border-indigo-300 hover:shadow-sm'
                        }`}
                    >
                      <div className="flex justify-between items-start mb-1.5">
                        <div className="text-xs text-gray-500 flex items-center font-medium">
                          <Clock className="w-3 h-3 mr-1.5" />
                          {new Date(session.created_at).toLocaleDateString()}
                        </div>
                        {getOriginBadge(session.origin)}
                      </div>
                      <div className="text-sm font-medium text-gray-800 line-clamp-2" title={session.summary || "No summary"}>
                        {session.summary || "Start of conversation..."}
                      </div>
                      {session.top_intent && (
                        <div className="mt-2 text-[10px] inline-block px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded border border-gray-200">
                          {session.top_intent}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Main: Transcript */}
            {/* Hidden on mobile if NO session selected */}
            <div className={`flex-col bg-white w-full lg:w-2/3 transition-all absolute lg:relative inset-0 z-20 lg:z-0 ${selectedSessionId ? 'flex' : 'hidden lg:flex'}`}>
              <div className="p-3 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50 flex items-center justify-between h-12 flex-shrink-0">
                <div className="flex items-center gap-3">
                  {/* Mobile Back Button */}
                  <button
                    onClick={() => setSelectedSessionId(null)}
                    className="lg:hidden p-1.5 -ml-1.5 hover:bg-gray-200 rounded-md text-gray-600 transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span>Transcript</span>
                </div>
                {selectedSessionId && (
                  <span className="text-[10px] text-gray-400 font-mono bg-white px-1.5 py-0.5 rounded border border-gray-200">
                    ID: {selectedSessionId.slice(0, 8)}
                  </span>
                )}
              </div>

              {/* Analysis Section */}
              {selectedSessionId && (
                <div className="flex-shrink-0 border-b border-gray-200 bg-gray-50/30 max-h-[30vh] overflow-y-auto">
                  <div className="p-4">
                    <div className="flex justify-between items-center mb-3">
                      <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-purple-600" />
                        Analysis
                      </h3>
                      <button
                        onClick={() => analyzeSession(selectedSessionId)}
                        disabled={analyzing}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-white border shadow-sm transition-all
                                ${analyzing ? 'opacity-50 cursor-not-allowed' : 'hover:bg-purple-50 hover:border-purple-200'}
                                border-gray-200
                            `}
                      >
                        {analyzing ? (
                          <RefreshCw className="w-3 h-3 animate-spin text-purple-600" />
                        ) : (
                          <Sparkles className="w-3 h-3 text-purple-600" />
                        )}
                        <span className="text-purple-700">
                          {analyzing ? 'Analyzing...' : 'Analyze Session'}
                        </span>
                      </button>
                    </div>

                    {sessions.find(s => s.id === selectedSessionId)?.summary ? (
                      <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-sm space-y-2">
                        <p className="text-sm text-gray-700 leading-relaxed">
                          {sessions.find(s => s.id === selectedSessionId)?.summary}
                        </p>
                        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gray-100">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-700 border border-purple-100">
                            Intent: {sessions.find(s => s.id === selectedSessionId)?.top_intent || "General"}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-gray-400 italic text-center py-2">
                        Click analyze to generate insights for this session.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Follow-up Section */}
              {selectedSessionId && (
                <div className="flex-shrink-0 border-b border-gray-200 bg-gray-50/30">
                  <div className="p-4">
                    <details className="group">
                      <summary className="list-none flex justify-between items-center cursor-pointer text-sm font-semibold text-gray-800">
                        <span className="flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-blue-600" />
                          Generate Follow-up
                        </span>
                        <div className="text-xs text-gray-400 group-open:hidden">Click to expand</div>
                      </summary>

                      <div className="mt-3 space-y-3">
                        <div className="flex flex-col sm:flex-row gap-2 items-start">
                          <select
                            value={followUpType}
                            onChange={e => setFollowUpType(e.target.value)}
                            className="w-full sm:w-auto text-sm border border-gray-300 rounded-md p-2 bg-white"
                          >
                            <option value="email">Email</option>
                            <option value="transcript">Transcript</option>
                          </select>
                          <input
                            type="text"
                            placeholder="Extra instructions..."
                            className="w-full sm:flex-1 text-sm border border-gray-300 rounded-md p-2"
                            value={followUpInfo}
                            onChange={e => setFollowUpInfo(e.target.value)}
                          />
                          <button
                            onClick={handleGenerateFollowUp}
                            disabled={generatingFollowUp}
                            className="w-full sm:w-auto px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
                          >
                            {generatingFollowUp ? 'Generating...' : 'Generate'}
                          </button>
                        </div>
                        {followUpResult && (
                          <div className="mt-2">
                            <textarea
                              readOnly
                              value={followUpResult}
                              className="w-full text-sm p-3 border border-gray-200 rounded-md bg-white shadow-sm font-mono h-32"
                            />
                          </div>
                        )}
                      </div>
                    </details>
                  </div>
                </div>
              )}

              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/30">
                {loadingMessages ? (
                  <div className="h-full flex flex-col items-center justify-center space-y-2 text-gray-400">
                    <RefreshCw className="w-6 h-6 animate-spin" />
                    <span>Loading transcript...</span>
                  </div>
                ) : !selectedSessionId ? (
                  <div className="h-full flex flex-col items-center justify-center text-gray-400 text-center p-8">
                    <MessageSquare className="w-12 h-12 mb-4 opacity-10" />
                    <p>Select a session to view the conversation history.</p>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-gray-400">No messages in this session.</div>
                ) : (
                  messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.sender === 'guest' ? 'justify-start' : 'justify-end'}`}>
                      <div
                        className={`max-w-[85%] sm:max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-sm ${msg.sender === 'guest'
                          ? 'bg-white text-gray-800 border border-gray-200 rounded-tl-none'
                          : 'bg-indigo-600 text-white rounded-tr-none'
                          }`}
                      >
                        <div
                          className={`prose prose-sm max-w-none break-words
                            ${msg.sender === 'guest'
                              ? 'text-gray-800 prose-headings:text-gray-800 prose-p:text-gray-800 prose-a:text-blue-600'
                              : 'text-white prose-headings:text-white prose-p:text-white prose-a:text-white/90'
                            }
                          `}
                        >
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.message_text}
                          </ReactMarkdown>
                        </div>
                        <p className={`text-[10px] mt-1.5 text-right ${msg.sender === 'guest' ? 'text-gray-400' : 'text-white/70'}`}>
                          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            {/* Only show Close on desktop, mobile has back button inside */}
            <button
              onClick={() => setSelectedGuest(null)}
              className="w-full lg:w-auto px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
