// User types
export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

// Business Profile types
export interface BusinessProfile {
  id: string;
  user_id: string;
  business_name: string;
  description: string;
  website: string;
  custom_agent_instruction: string;
  intents?: string[];
  logo_url?: string;
  is_api_key_set?: boolean;
  is_escalation_enabled?: boolean;
  escalation_emails?: string[];
  created_at: string;
  updated_at: string;
}


export interface CreateBusinessProfileData {
  business_name: string;
  description: string;
  website: string;
  custom_agent_instruction: string;
  intents?: string[];
  logo_url?: string;
  gemini_api_key?: string;
}

export interface UpdateBusinessProfileData {
  business_name?: string;
  description?: string;
  website?: string;
  custom_agent_instruction?: string;
  intents?: string[];
  logo_url?: string;
  gemini_api_key?: string;
  is_escalation_enabled?: boolean;
  escalation_emails?: string[];
}

// Document types
export interface Document {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  error_message?: string;
}

export interface ProcessedDocument {
  filename: string;
  chunks_created: number;
  status: 'success' | 'error';
}

// Chat types
export interface Message {
  role: 'user' | 'agent';
  content: string;
  sources?: string[];
  timestamp?: string;
}

export interface ChatResponse {
  response: string;
  sources: string[];
}

// Escalation types
export interface Escalation {
  id: string;
  business_id: string;
  session_id: string;
  status: 'pending' | 'in_progress' | 'resolved';
  summary: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  created_at: string;
}

export interface EscalationMessage {
  id: string;
  sender: 'user' | 'agent';
  message: string;
  created_at: string;
}

export interface EscalationDetail extends Escalation {
  messages: EscalationMessage[];
}

// Auth types
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface SignupData {
  email: string;
  password: string;
  name: string;
}

export interface LoginData {
  email: string;
  password: string;
}

// API Response wrapper
export interface ApiResponse<T> {
  status: 'success' | 'error';
  message?: string;
  data?: T;
}
// Widget types
export interface WidgetSettings {
  public_widget_id: string;
  theme: string;
  primary_color: string;
  icon_url?: string;
  welcome_message?: string;
  initial_ai_message?: string;
  send_initial_message_automatically?: boolean;
  whatsapp_enabled?: boolean;
  whatsapp_number?: string;
  max_messages_per_session?: number;
  max_sessions_per_day?: number;
  whitelisted_domains?: string[];
}

export interface UpdateWidgetSettings {
  theme?: string;
  primary_color?: string;
  icon_url?: string;
  welcome_message?: string;
  initial_ai_message?: string;
  send_initial_message_automatically?: boolean;
  whatsapp_enabled?: boolean;
  whatsapp_number?: string;
  max_messages_per_session?: number;
  max_sessions_per_day?: number;
  whitelisted_domains?: string[];
}

export interface AnalyticsOverview {
  total_sessions: number;
  total_guests: number;
  leads_captured: number;
  avg_session_duration: number;
  returning_guests_percentage: number;
}

export interface IntentStat {
  intent: string;
  count: number;
}

export interface TrafficSource {
  source: string;
  count: number;
}

export interface Session {
  id: string;
  guest_name: string;
  guest_email: string | null;
  created_at: string;
  session_duration: number;
  top_intent: string | null;
  summary: string | null;
  status: 'active' | 'closed';
}

export interface SessionMessage {
  id: string;
  role: 'user' | 'ai';
  content: string; // The backend returns full content as string? Or just message_text
  created_at: string;
}

export interface GuestDetails {
  id: string;
  name: string;
  email: string | null;
  location: string | null;
}

export interface SessionDetail {
  id: string;
  guest: GuestDetails;
  created_at: string;
  top_intent: string | null;
  summary: string | null;
  sentiment_score: number | null;
  messages: SessionMessage[];
}

export interface LocationStat {
  country: string;
  city: string;
  count: number;
}

export interface Guest {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  is_lead: boolean;
  created_at: string;
  // last_seen_at? backend has it but schema might only return created_at?
  // GuestUserResponse in widget.py: id, name, email, phone, created_at.
}

export interface GuestSession {
  id: string;
  created_at: string;
  last_message_at: string;
  origin: string;
  summary: string | null;
  top_intent: string | null;
  country?: string | null;
  city?: string | null;
  device_type?: string | null;
  os?: string | null;
}
