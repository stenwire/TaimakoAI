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
  created_at: string;
  updated_at: string;
}

export interface CreateBusinessProfileData {
  business_name: string;
  description: string;
  website: string;
  custom_agent_instruction: string;
  intents?: string[];
}

export interface UpdateBusinessProfileData {
  business_name?: string;
  description?: string;
  website?: string;
  custom_agent_instruction?: string;
  intents?: string[];
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
}
