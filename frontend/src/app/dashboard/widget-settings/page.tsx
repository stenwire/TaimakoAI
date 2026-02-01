'use client';

import { useState, useEffect } from 'react';
import { Sparkles, Check, Copy, Plus, X, Phone, MessageSquare, Send } from 'lucide-react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
import Select from '@/components/ui/Select';
import Card from '@/components/ui/Card';
import { getAccessToken, getBusinessProfile, updateBusinessProfile, generateIntents } from '@/lib/api';
import { useToast } from '@/contexts/ToastContext';
import { BusinessProfile } from '@/lib/types';
import { cn } from '@/lib/utils';
import { BACKEND_URL, FRONTEND_URL } from '@/config';



interface WidgetSettings {
  primary_color?: string;
  theme?: string;
  icon_url?: string;
  public_widget_id?: string;
  welcome_message?: string;
  initial_ai_message?: string;
  send_initial_message_automatically?: boolean;
  whatsapp_enabled?: boolean;
  whatsapp_number?: string;
  max_messages_per_session?: number;
  max_sessions_per_day?: number;
  whitelisted_domains?: string[];
  is_active?: boolean;
}

type Tab = 'business' | 'appearance' | 'installation';

export default function WidgetSettingsPage() {
  const [settings, setSettings] = useState<WidgetSettings | null>(null);
  const { success, error } = useToast();
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [business, setBusiness] = useState<BusinessProfile | null>(null);
  const [generatingIntents, setGeneratingIntents] = useState(false);
  const [businessUpdating, setBusinessUpdating] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('business');

  const [copied, setCopied] = useState(false);
  const [newDomain, setNewDomain] = useState('');

  useEffect(() => {
    fetchSettings();
    fetchBusiness();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = getAccessToken();
      const res = await fetch(`${BACKEND_URL}/widgets/my-settings`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const responseData = await res.json();
        setSettings(responseData.data);
      }
    } catch (err) {
      console.error("Failed to load settings", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBusiness = async () => {
    try {
      const res = await getBusinessProfile();
      if (res.status === 'success' && res.data) setBusiness(res.data);
    } catch (e) { console.error(e); }
  }

  const handleUpdate = async () => {
    setUpdating(true);
    if (!settings) return;
    try {
      const token = getAccessToken();
      const res = await fetch(`${BACKEND_URL}/widgets/my-settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          primary_color: settings.primary_color,
          theme: settings.theme,
          icon_url: settings.icon_url,
          welcome_message: settings.welcome_message,
          initial_ai_message: settings.initial_ai_message,
          send_initial_message_automatically: settings.send_initial_message_automatically,
          whatsapp_enabled: settings.whatsapp_enabled,
          whatsapp_number: settings.whatsapp_number,
          max_messages_per_session: settings.max_messages_per_session,
          max_sessions_per_day: settings.max_sessions_per_day,
          whitelisted_domains: settings.whitelisted_domains,
          is_active: settings.is_active
        }),
      });
      if (res.ok) {
        const responseData = await res.json();
        setSettings(responseData.data);
        success("Appearance settings saved successfully!");
      } else {
        error("Failed to save settings");
      }
    } catch (err) {
      console.error(err);
      error("Error saving settings");
    } finally {
      setUpdating(false);
    }
  };

  const handleBusinessUpdate = async () => {
    if (!business) return;
    setBusinessUpdating(true);
    try {
      await updateBusinessProfile({
        description: business.description,
        intents: business.intents
      });
      success("Business profile updated!");
    } catch (e) {
      error("Failed to update business profile");
    } finally {
      setBusinessUpdating(false);
    }
  }

  const handleGenerateIntents = async () => {
    if (!business?.description) {
      error("Please enter a business description first");
      return;
    }
    setGeneratingIntents(true);
    try {
      const res = await generateIntents();
      if (res.data?.intents) {
        setBusiness({ ...business, intents: res.data.intents });
        success("Intents generated!");
      }
    } catch (e) { error("Generaton failed"); } finally { setGeneratingIntents(false); }
  }

  const copyEmbedCode = () => {
    if (!settings?.public_widget_id) return;
    const code = `<!-- Taimako.AI Chat Widget -->
<script>
  (function() {
      var s = document.createElement("script");
      s.src = "${FRONTEND_URL}/widget.js";
      s.async = true;
      s.dataset.widgetId = "${settings.public_widget_id}";
      document.head.appendChild(s);
  })();
</script>`;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const tabs: { id: Tab, label: string }[] = [
    { id: 'business', label: 'Business Context' },
    { id: 'appearance', label: 'Appearance & Behavior' },
    { id: 'installation', label: 'Installation' },
  ];

  return (
    <div className="max-w-[1600px] mx-auto h-[calc(100vh-140px)] flex flex-col">
      <div className="mb-6 flex-shrink-0">
        <h1 className="text-2xl font-space font-bold text-[var(--brand-primary)]">Widget Customization</h1>
        <p className="text-[var(--text-secondary)] mt-1">Customize your chat widget&apos;s appearance, behavior, and business knowledge.</p>
      </div>

      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-8 h-full pb-10">
        {/* Settings Form - Left Panel (Scrollable) */}
        <div className="lg:col-span-7 flex flex-col h-full bg-white rounded-[var(--radius-lg)] border border-[var(--border-subtle)] overflow-hidden shadow-sm">
          {/* Tabs Header */}
          <div className="flex border-b border-[var(--border-subtle)] px-6 pt-4 gap-6 bg-[var(--bg-secondary)]/30 overflow-x-auto scrollbar-hide">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "pb-3 text-sm font-medium transition-all relative",
                  activeTab === tab.id
                    ? "text-[var(--brand-primary)] font-bold"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                )}
              >
                {tab.label}
                {activeTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--brand-primary)] rounded-t-full" />
                )}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-8">
            {activeTab === 'business' && (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-lg font-space font-bold text-[var(--text-primary)]">Business Context</h2>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">Define how the AI understands your business to answer customer queries.</p>
                  </div>
                  <Button
                    onClick={handleBusinessUpdate}
                    loading={businessUpdating}
                    className="whitespace-nowrap px-6 shrink-0"
                  >
                    Save Context
                  </Button>
                </div>

                <div className="space-y-6">
                  <Textarea
                    label="Business Description"
                    placeholder="Describe your business, products, services, and key policies..."
                    rows={8}
                    value={business?.description || ''}
                    readOnly
                    className="bg-[var(--bg-secondary)] text-[var(--text-secondary)] cursor-not-allowed"
                  />
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <label className="text-sm font-medium text-[var(--text-secondary)]">Detected Intents</label>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={handleGenerateIntents}
                        loading={generatingIntents}
                        disabled={!business?.description}
                      >
                        <Sparkles className="w-3 h-3 mr-1.5" />
                        Generate with AI
                      </Button>
                    </div>
                    <div className="space-y-3">
                      {[0, 1, 2, 3, 4].map(i => (
                        <Input
                          key={i}
                          placeholder={`Intent ${i + 1} (e.g., Check Pricing, Return Policy)`}
                          value={business?.intents?.[i] || ''}
                          onChange={e => {
                            if (!business) return;
                            const newIntents = [...(business.intents || [])];
                            newIntents[i] = e.target.value;
                            setBusiness({ ...business, intents: newIntents });
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'appearance' && (
              <div className="space-y-8 animate-in fade-in duration-300">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-lg font-space font-bold text-[var(--text-primary)]">Appearance & Behavior</h2>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">Customize the look and feel of the chat widget.</p>
                  </div>
                  <Button
                    onClick={handleUpdate}
                    loading={updating}
                    className="whitespace-nowrap px-6"
                  >
                    Save Changes
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="md:col-span-2 bg-[var(--bg-secondary)] p-6 rounded-[var(--radius-md)] border border-[var(--border-subtle)] flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-[var(--text-primary)]">Widget Status</h3>
                      <p className="text-sm text-[var(--text-secondary)] mt-1">
                        {settings?.is_active ? 'Widget is currently active and visible on your site.' : 'Widget is disabled and hidden from your site.'}
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.is_active ?? true}
                        onChange={(e) => settings && setSettings({ ...settings, is_active: e.target.checked })}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 dark:peer-focus:ring-green-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-[var(--brand-primary)]"></div>
                    </label>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Primary Brand Color</label>
                    <div className="flex gap-3 items-center">
                      <div className="relative w-12 h-10 rounded-[var(--radius-md)] overflow-hidden border border-[var(--border-subtle)] shadow-sm flex-shrink-0">
                        <input
                          type="color"
                          value={settings?.primary_color || "#0E3F34"}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => settings && setSettings({ ...settings, primary_color: e.target.value })}
                          className="absolute -top-2 -left-2 w-16 h-16 cursor-pointer border-none p-0"
                        />
                      </div>
                      <Input
                        value={settings?.primary_color || "#0E3F34"}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => settings && setSettings({ ...settings, primary_color: e.target.value })}
                        className="font-mono"
                      />
                    </div>
                  </div>

                  <Select
                    label="Theme Mode"
                    value={settings?.theme || "light"}
                    onChange={(e) => settings && setSettings({ ...settings, theme: e.target.value })}
                    options={[
                      { label: 'Light Mode', value: 'light' },
                      { label: 'Dark Mode', value: 'dark' }
                    ]}
                  />
                </div>

                <Input
                  label="Launcher Icon URL"
                  placeholder="https://example.com/icon.png"
                  value={settings?.icon_url || ""}
                  onChange={(e) => settings && setSettings({ ...settings, icon_url: e.target.value })}
                />

                <div className="border-t border-[var(--border-subtle)] pt-8 space-y-6">
                  <h3 className="text-sm font-bold text-[var(--brand-primary)] uppercase tracking-wider">Messages</h3>

                  <div className="space-y-6">
                    <Input
                      label="Welcome Message"
                      placeholder="Hi there! 👋"
                      value={settings?.welcome_message || ""}
                      onChange={(e) => settings && setSettings({ ...settings, welcome_message: e.target.value })}
                    />

                    <div className="space-y-3">
                      <Input
                        label="Initial AI Response"
                        placeholder="How can I help you today?"
                        value={settings?.initial_ai_message || ""}
                        onChange={(e) => settings && setSettings({ ...settings, initial_ai_message: e.target.value })}
                      />

                      <label className="flex items-center gap-3 p-4 bg-[var(--bg-secondary)] rounded-[var(--radius-md)] border border-[var(--border-subtle)] cursor-pointer hover:border-[var(--brand-primary)] transition-colors">
                        <input
                          type="checkbox"
                          checked={settings?.send_initial_message_automatically ?? true}
                          onChange={(e) => settings && setSettings({ ...settings, send_initial_message_automatically: e.target.checked })}
                          className="h-4 w-4 text-[var(--brand-primary)] border-[var(--border-strong)] rounded focus:ring-[var(--brand-primary)]"
                        />
                        <div>
                          <span className="block text-sm font-medium text-[var(--text-primary)]">Auto-send Initial Response</span>
                          <span className="block text-xs text-[var(--text-secondary)] mt-0.5">If unchecked, the AI waits for the user to type first.</span>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="border-t border-[var(--border-subtle)] pt-8 space-y-6">
                  <h3 className="text-sm font-bold text-[var(--brand-primary)] uppercase tracking-wider">WhatsApp Integration</h3>
                  <div className="space-y-4">
                    <label className="flex items-center gap-3 p-4 bg-[var(--bg-secondary)] rounded-[var(--radius-md)] border border-[var(--border-subtle)] cursor-pointer hover:border-[var(--brand-primary)] transition-colors">
                      <input
                        type="checkbox"
                        checked={settings?.whatsapp_enabled ?? false}
                        onChange={(e) => settings && setSettings({ ...settings, whatsapp_enabled: e.target.checked })}
                        className="h-4 w-4 text-[var(--brand-primary)] border-[var(--border-strong)] rounded focus:ring-[var(--brand-primary)]"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Phone className="w-4 h-4 text-green-600" />
                          <span className="block text-sm font-medium text-[var(--text-primary)]">Enable WhatsApp Integration</span>
                        </div>
                        <span className="block text-xs text-[var(--text-secondary)] mt-0.5">Allow customers to chat with you via WhatsApp.</span>
                      </div>
                    </label>

                    {settings?.whatsapp_enabled && (
                      <div className="animate-in fade-in slide-in-from-top-2 duration-200">
                        <Input
                          label="WhatsApp Number"
                          placeholder="e.g. 15551234567"
                          value={settings?.whatsapp_number || ""}
                          onChange={(e) => {
                            if (!settings) return;
                            // Only allow numbers
                            const val = e.target.value.replace(/[^0-9]/g, '');
                            setSettings({ ...settings, whatsapp_number: val });
                          }}
                          className="font-mono"
                        />
                        <p className="text-xs text-[var(--text-tertiary)] mt-1.5 flex items-center gap-1">
                          <span className="text-[var(--brand-primary)]">*</span> Enter numbers only, including country code (no + or spaces).
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="border-t border-[var(--border-subtle)] pt-8 space-y-6">
                  <h3 className="text-sm font-bold text-[var(--brand-primary)] uppercase tracking-wider">Limits & Security</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Input
                      label="Max Messages / Session"
                      type="number"
                      value={settings?.max_messages_per_session || 50}
                      onChange={(e) => settings && setSettings({ ...settings, max_messages_per_session: parseInt(e.target.value) })}
                    />
                    <Input
                      label="Max Sessions / Day"
                      type="number"
                      value={settings?.max_sessions_per_day || 5}
                      onChange={(e) => settings && setSettings({ ...settings, max_sessions_per_day: parseInt(e.target.value) })}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Whitelisted Domains</label>
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <Input
                        placeholder="https://example.com"
                        value={newDomain}
                        onChange={(e) => setNewDomain(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            if (newDomain && settings) {
                              const current = settings.whitelisted_domains || [];
                              if (!current.includes(newDomain)) {
                                setSettings({ ...settings, whitelisted_domains: [...current, newDomain] });
                                setNewDomain('');
                              }
                            }
                          }
                        }}
                      />
                      <Button
                        variant="secondary"
                        onClick={() => {
                          if (newDomain && settings) {
                            const current = settings.whitelisted_domains || [];
                            if (!current.includes(newDomain)) {
                              setSettings({ ...settings, whitelisted_domains: [...current, newDomain] });
                              setNewDomain('');
                            }
                          }
                        }}
                        disabled={!newDomain}
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {(settings?.whitelisted_domains || []).map((domain) => (
                        <div
                          key={domain}
                          className="group flex items-center gap-2 px-3 py-1.5 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-full text-sm text-[var(--text-secondary)] hover:border-[var(--brand-primary)] hover:text-[var(--brand-primary)] transition-all"
                        >
                          <span>{domain}</span>
                          <button
                            onClick={() => {
                              if (settings) {
                                const current = settings.whitelisted_domains || [];
                                setSettings({ ...settings, whitelisted_domains: current.filter(d => d !== domain) });
                              }
                            }}
                            className="w-4 h-4 rounded-full flex items-center justify-center hover:text-[var(--error)] text-[var(--text-tertiary)] transition-colors opacity-0 group-hover:opacity-100"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                      {(!settings?.whitelisted_domains || settings.whitelisted_domains.length === 0) && (
                        <p className="text-xs text-[var(--text-tertiary)] py-1">No domains whitelisted. Widget will work on all domains (not recommended).</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'installation' && (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-lg font-space font-bold text-[var(--text-primary)]">Installation</h2>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">Add the widget to your website.</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <p className="text-sm text-[var(--text-secondary)]">
                    Copy the code snippet below and paste it into the <code>&lt;head&gt;</code> tag of every page where you want the chat widget to appear.
                  </p>

                  <div className="relative group">
                    <div className="bg-[#1e1e1e] text-gray-300 p-6 rounded-[var(--radius-md)] text-xs font-mono overflow-x-auto whitespace-pre leading-relaxed shadow-inner border border-gray-800">
                      {`<!-- Taimako.AI Chat Widget -->
<script>
  (function() {
      var s = document.createElement("script");
      s.src = "${FRONTEND_URL}/widget.js";
      s.async = true;
      s.dataset.widgetId = "${settings?.public_widget_id || 'YOUR_WIDGET_ID'}";
      document.head.appendChild(s);
  })();
</script>`}
                    </div>
                    <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button size="sm" variant="secondary" onClick={copyEmbedCode} className="bg-white/10 hover:bg-white/20 text-white border-none backdrop-blur-sm">
                        {copied ? <Check className="w-3 h-3 mr-1.5" /> : <Copy className="w-3 h-3 mr-1.5" />}
                        {copied ? "Copied" : "Copy"}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Preview - Right Panel */}
        <div className="lg:col-span-5 hidden lg:block h-full min-h-0">
          <div className="bg-[var(--bg-tertiary)]/50 backdrop-blur-sm border border-[var(--border-subtle)] rounded-[var(--radius-lg)] h-full flex flex-col overflow-hidden shadow-[var(--shadow-md)]">
            <div className="p-4 border-b border-[var(--border-subtle)] bg-white/80 backdrop-blur-sm flex justify-center items-center shrink-0">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" /> Live Preview
              </span>
            </div>

            <div className="flex-1 relative bg-[var(--bg-secondary)] overflow-hidden flex items-end justify-end p-8">
              {/* Subtle Grid Background */}
              <div className="absolute inset-0 opacity-[0.03]"
                style={{
                  backgroundImage: `linear-gradient(#000 1px, transparent 1px), linear-gradient(90deg, #000 1px, transparent 1px)`,
                  backgroundSize: '20px 20px'
                }}
              />

              {/* Mock Widget */}
              <div className="relative flex flex-col items-end space-y-4 max-h-full w-full pointer-events-none">

                {/* Chat Window or Actions View */}
                {settings?.whatsapp_enabled ? (
                  // ACTIONS VIEW PREVIEW
                  <div className="w-[360px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-500 transform origin-bottom-right ring-1 ring-black/5 shrink-0 max-h-[calc(100%-80px)]">
                    {/* Header */}
                    <div className="h-14 flex items-center px-5 justify-between text-white shadow-sm z-10 shrink-0 mb-0" style={{ backgroundColor: settings?.primary_color || '#0E3F34' }}>
                      <div className="flex items-center gap-3">
                        <span className="font-space font-bold tracking-tight text-md">👋 Welcome</span>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 p-6 flex flex-col justify-center bg-white">
                      <div className="text-center space-y-2 mb-6">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full text-white shadow-lg mb-2" style={{ backgroundColor: settings?.primary_color || '#0E3F34' }}>
                          {business?.logo_url ? <img src={business.logo_url} className="w-8 h-8 object-contain" alt="" /> : <MessageSquare className="w-6 h-6" />}
                        </div>
                        <h2 className="text-xl font-bold text-gray-900 leading-tight">How would you like to connect?</h2>
                      </div>

                      <div className="space-y-3">
                        <div className="w-full bg-[var(--primary-color)] text-white p-3.5 rounded-xl shadow-md flex items-center justify-between opacity-90" style={{ backgroundColor: settings?.primary_color || '#0E3F34' }}>
                          <div className="flex items-center gap-3">
                            <div className="bg-white/20 p-1.5 rounded-lg">
                              <MessageSquare className="w-5 h-5" />
                            </div>
                            <div className="text-left">
                              <div className="font-bold text-sm">Chat with AI</div>
                              <div className="text-[10px] text-white/80">Instant responses</div>
                            </div>
                          </div>
                          <Send className="w-4 h-4" />
                        </div>

                        <div className="w-full bg-[#25D366] text-white p-3.5 rounded-xl shadow-md flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="bg-white/20 p-1.5 rounded-lg">
                              <Phone className="w-5 h-5" />
                            </div>
                            <div className="text-left">
                              <div className="font-bold text-sm">WhatsApp</div>
                              <div className="text-[10px] text-white/80">Drop a message</div>
                            </div>
                          </div>
                          <Send className="w-4 h-4 -rotate-45" />
                        </div>
                      </div>

                      <div className="mt-6 text-center">
                        <span className="text-gray-400 text-xs border-b border-dotted border-gray-400">Continue to form</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  // CHAT VIEW PREVIEW
                  <div className="w-[360px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-500 transform origin-bottom-right ring-1 ring-black/5 shrink-0 max-h-[calc(100%-80px)]">
                    {/* Header */}
                    <div className="h-14 flex items-center px-5 justify-between text-white shadow-sm z-10 shrink-0" style={{ backgroundColor: settings?.primary_color || '#0E3F34' }}>
                      <div className="flex items-center gap-3">
                        <div className="relative">
                          <div className="w-2 h-2 rounded-full bg-green-400 border border-white/20" />
                          <div className="absolute inset-0 w-2 h-2 rounded-full bg-green-400 animate-ping opacity-75" />
                        </div>
                        <span className="font-space font-bold tracking-tight text-md">Support</span>
                      </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 bg-[#F9FAFB] p-5 flex flex-col gap-3 overflow-y-auto min-h-0">
                      {/* Welcome Message */}
                      {settings?.welcome_message && (
                        <div className="bg-white p-3.5 rounded-2xl rounded-bl-none shadow-sm text-[13px] border border-gray-100 self-start max-w-[85%] text-gray-700 leading-relaxed animate-in fade-in slide-in-from-left-2 duration-300">
                          {settings.welcome_message}
                        </div>
                      )}

                      {/* User Message */}
                      <div className="p-3.5 rounded-2xl rounded-br-none shadow-sm text-[13px] text-white self-end max-w-[85%] leading-relaxed animate-in fade-in slide-in-from-right-2 duration-300 delay-150" style={{ backgroundColor: settings?.primary_color || '#0E3F34' }}>
                        I have a question about pricing.
                      </div>

                      {/* AI Message */}
                      <div className="bg-white p-3.5 rounded-2xl rounded-bl-none shadow-sm text-[13px] border border-gray-100 self-start max-w-[85%] text-gray-700 leading-relaxed animate-in fade-in slide-in-from-left-2 duration-300 delay-300">
                        {settings?.initial_ai_message || "How can I help you today?"}
                      </div>
                    </div>

                    {/* Footer */}
                    <div className="p-3 bg-white border-t border-gray-100 shrink-0">
                      <div className="h-10 bg-gray-50 rounded-full w-full border border-gray-200 flex items-center px-4 text-gray-400 text-sm">
                        Type a message...
                      </div>
                    </div>
                  </div>
                )}

                {/* Launcher */}
                <div className="w-14 h-14 rounded-full shadow-xl flex items-center justify-center text-white cursor-pointer hover:scale-105 transition-transform active:scale-95 ring-4 ring-white/30 shrink-0" style={{ backgroundColor: settings?.primary_color || '#0E3F34' }}>
                  {settings?.icon_url ? (
                    <img src={settings.icon_url} className="w-7 h-7 object-contain" alt="Widget Icon" />
                  ) : (
                    <MessageSquare strokeWidth={2} className="w-7 h-7" />
                  )}
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>
    </div >
  );
}
