'use client';

import { useState, useEffect } from 'react';
import { getAccessToken, generateFollowUp } from '@/lib/api';
import Card from '@/components/ui/Card';
import Modal from '@/components/ui/Modal';
import { User, MessageSquare, Clock, Smartphone, RefreshCw, RotateCcw, Sparkles } from 'lucide-react';

const BACKEND_URL = 'http://localhost:8000'; // Env var

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
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Visitor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">First Seen</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {guests.map((guest) => (
                <tr key={guest.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xs">
                        {guest.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{guest.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{guest.email || guest.phone || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(guest.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => loadSessions(guest)}
                      className="text-indigo-600 hover:text-indigo-900 font-medium"
                    >
                      View History
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Guest Sessions & Chat Modal */}
      {selectedGuest && (
        <Modal
          isOpen={!!selectedGuest}
          onClose={() => setSelectedGuest(null)}
          title={`History for ${selectedGuest.name}`}
          className="max-w-5xl w-full"
        >
          <div className="h-[600px] flex border rounded-md overflow-hidden bg-white">
            {/* Sidebar: Sessions List */}
            <div className="w-1/3 border-r bg-gray-50 flex flex-col">
              <div className="p-3 border-b bg-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Sessions
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {loadingSessions ? (
                  <div className="text-center p-4 text-gray-400 text-sm">Loading sessions...</div>
                ) : sessions.length === 0 ? (
                  <div className="text-center p-4 text-gray-400 text-sm">No sessions found.</div>
                ) : (
                  sessions.map(session => (
                    <div
                      key={session.id}
                      onClick={() => loadSessionTranscript(session.id)}
                      className={`p-3 rounded-md cursor-pointer border transition-colors ${selectedSessionId === session.id
                        ? 'bg-white border-indigo-500 shadow-sm ring-1 ring-indigo-500'
                        : 'bg-white border-gray-200 hover:border-indigo-300'
                        }`}
                    >
                      <div className="flex justify-between items-start mb-1 h-5">
                        <div className="text-xs text-gray-500 flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {new Date(session.created_at).toLocaleDateString()}
                        </div>
                        {getOriginBadge(session.origin)}
                      </div>
                      <div className="text-sm font-medium text-gray-800 truncate" title={session.summary || "No summary"}>
                        {session.summary || "Conversation"}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Main: Transcript */}
            <div className="w-2/3 flex flex-col bg-white">
              <div className="p-3 border-b text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50 flex justify-between">
                <span>Transcript</span>
                {selectedSessionId && <span className="text-gray-400 font-normal">Session ID: {selectedSessionId.slice(0, 8)}...</span>}
              </div>

              {/* Analysis Section */}
              {selectedSessionId && (
                <div className="p-4 border-b bg-gray-50/50">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-purple-600" />
                      Analysis
                    </h3>
                    <button
                      onClick={() => analyzeSession(selectedSessionId)}
                      disabled={analyzing}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-white border shadow-sm transition-all
                                ${analyzing ? 'opacity-50 cursor-not-allowed' : 'hover:bg-purple-50 hover:border-purple-200'}
                                bg-gradient-to-r from-transparent via-transparent to-transparent
                                hover:from-purple-500/10 hover:via-pink-500/10 hover:to-orange-500/10
                                border-transparent ring-1 ring-gray-200 hover:ring-purple-300
                            `}
                    >
                      {analyzing ? (
                        <RefreshCw className="w-3 h-3 animate-spin text-purple-600" />
                      ) : (
                        <Sparkles className="w-3 h-3 text-purple-600" />
                      )}
                      <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-pink-600">
                        {analyzing ? 'Analyzing...' : 'Analyze Session'}
                      </span>
                    </button>
                  </div>

                  {sessions.find(s => s.id === selectedSessionId)?.summary ? (
                    <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm space-y-2">
                      <div>
                        <span className="text-xs font-bold text-gray-500 uppercase">Summary</span>
                        <p className="text-sm text-gray-800 mt-1">
                          {sessions.find(s => s.id === selectedSessionId)?.summary}
                        </p>
                      </div>
                      <div className="flex items-center justify-between pt-2 border-t border-gray-50">
                        <div>
                          <span className="text-xs font-bold text-gray-500 uppercase mr-2">Top Intent</span>
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                            {sessions.find(s => s.id === selectedSessionId)?.top_intent || "General"}
                          </span>
                        </div>
                        {sessions.find(s => s.id === selectedSessionId)?.summary_generated_at && (
                          <div className="text-[10px] text-gray-400">
                            Generated: {new Date(sessions.find(s => s.id === selectedSessionId)!.summary_generated_at!).toLocaleString()}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-gray-400 italic">
                      Click analyze to generate insights for this session.
                    </div>
                  )}
                </div>
              )}

              {/* Follow-up Section */}
              {selectedSessionId && (
                <div className="p-4 border-b bg-gray-50/50">
                  <h3 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                    Generate Follow-up
                  </h3>
                  <div className="space-y-3">
                    <div className="flex gap-2 items-start">
                      <select
                        value={followUpType}
                        onChange={e => setFollowUpType(e.target.value)}
                        className="text-sm border border-gray-300 rounded-md p-2 bg-white focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="email">Email</option>
                        <option value="transcript">Transcript</option>
                      </select>
                      <input
                        type="text"
                        placeholder="Any extra info to include?"
                        className="flex-1 text-sm border border-gray-300 rounded-md p-2 focus:ring-indigo-500 focus:border-indigo-500"
                        value={followUpInfo}
                        onChange={e => setFollowUpInfo(e.target.value)}
                      />
                      <button
                        onClick={handleGenerateFollowUp}
                        disabled={generatingFollowUp}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 whitespace-nowrap transition-colors"
                      >
                        {generatingFollowUp ? 'Generating...' : 'Generate'}
                      </button>
                    </div>
                    {followUpResult && (
                      <div className="mt-2 animate-in fade-in zoom-in duration-200">
                        <label className="block text-xs font-medium text-gray-500 mb-1">Generated Result</label>
                        <textarea
                          readOnly
                          value={followUpResult}
                          className="w-full text-sm p-3 border border-gray-200 rounded-md bg-white shadow-sm focus:ring-indigo-500 focus:border-indigo-500 font-mono"
                          rows={6}
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {loadingMessages ? (
                  <div className="h-full flex items-center justify-center text-gray-400">Loading transcript...</div>
                ) : !selectedSessionId ? (
                  <div className="h-full flex items-center justify-center text-gray-400">Select a session to view details.</div>
                ) : messages.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-gray-400">No messages in this session.</div>
                ) : (
                  messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.sender === 'guest' ? 'justify-start' : 'justify-end'}`}>
                      <div
                        className={`max-w-[80%] rounded-lg px-3 py-2 text-sm shadow-sm ${msg.sender === 'guest'
                          ? 'bg-gray-100 text-gray-800 border border-gray-200'
                          : 'bg-indigo-600 text-white'
                          }`}
                      >
                        <p>{msg.message_text}</p>
                        <p className="text-[10px] opacity-70 mt-1 min-w-[60px] text-right">
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
            <button
              onClick={() => setSelectedGuest(null)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm font-medium"
            >
              Close
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
