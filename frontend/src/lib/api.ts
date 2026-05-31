import axios, { AxiosError } from 'axios';
import type {
  AuthTokens,
  SignupData,
  LoginData,
  BusinessProfile,
  CreateBusinessProfileData,
  UpdateBusinessProfileData,
  ChatResponse,
  ProcessedDocument,
  Document,
  ApiResponse,
  AnalyticsOverview,
  IntentStat,
  LocationStat,
  TrafficSource,
  Session,
  SessionDetail,
  Guest,
  GuestSession,
  Escalation,
  EscalationDetail,
  Product,
  CreateProductData,
  UpdateProductData,
} from './types';

import { BACKEND_URL } from '../config';

const API_BASE_URL = BACKEND_URL;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export const setTokens = (tokens: AuthTokens) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }
};

export const getAccessToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
};

export const getRefreshToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }
  return null;
};

export const clearTokens = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
};

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const originalRequest = error.config as any; // Using any to access potential internal state, safe in this context

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          // Note: Implement refresh endpoint when available
          // const response = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken });
          // setTokens(response.data.data);
          // return api(originalRequest);

          // For now, just clear tokens and redirect to login
          clearTokens();
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
        } catch {
          clearTokens();
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
        }
      }
    }

    return Promise.reject(error);
  }
);

// Authentication endpoints
export const signup = async (data: SignupData): Promise<ApiResponse<AuthTokens>> => {
  const response = await api.post('/auth/signup', data);
  if (response.data.data) {
    setTokens(response.data.data);
  }
  return response.data;
};

export const login = async (data: LoginData): Promise<ApiResponse<AuthTokens>> => {
  const response = await api.post('/auth/login', data);
  if (response.data.data) {
    setTokens(response.data.data);
  }
  return response.data;
};

export const logout = () => {
  clearTokens();
};

// Business Profile endpoints
export const createBusinessProfile = async (
  data: CreateBusinessProfileData
): Promise<ApiResponse<BusinessProfile>> => {
  const response = await api.post('/business', data);
  return response.data;
};

export const getBusinessProfile = async (): Promise<ApiResponse<BusinessProfile>> => {
  const response = await api.get('/business');
  return response.data;
};

export const updateBusinessProfile = async (
  data: UpdateBusinessProfileData
): Promise<ApiResponse<BusinessProfile>> => {
  const response = await api.put('/business', data);
  return response.data;
};

export const generateIntents = async (): Promise<ApiResponse<{ intents: string[] }>> => {
  const response = await api.post('/business/generate-intents');
  return response.data;
};

export const generateFollowUp = async (
  sessionId: string,
  type: string,
  extraInfo: string
): Promise<ApiResponse<{ content: string }>> => {
  const response = await api.post('/analytics/followup', {
    session_id: sessionId,
    type,
    extra_info: extraInfo
  });
  return response.data;
};

// Document endpoints
export const uploadDocuments = async (files: File[]): Promise<ApiResponse<{ files: string[] }>> => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': undefined, // Let browser set Content-Type with multipart boundary
    },
  });
  return response.data;
};

export const listDocuments = async (): Promise<Document[]> => {
  const response = await api.get('/documents');
  return response.data.data || response.data;
};

export const deleteDocument = async (id: string): Promise<ApiResponse<null>> => {
  const response = await api.delete(`/documents/${id}`);
  return response.data;
};

export const processDocuments = async (): Promise<ProcessedDocument[]> => {
  const response = await api.post('/rag/process');
  return response.data.data || response.data;
};

// Chat endpoint
export const chatWithAgent = async (message: string): Promise<ChatResponse> => {
  const response = await api.post('/chat', { message });
  return response.data.data || response.data;
};

// Analytics & Sessions
export const getAnalyticsOverview = async (days: number = 30): Promise<ApiResponse<AnalyticsOverview> | AnalyticsOverview> => {
  // Note: The backend returns raw dict for overview, not wrapped in ApiResponse envelope currently in code, let's verify.
  // Looking at analytics.py: return {...} directly. So it's raw JSON.
  const response = await api.get(`/analytics/overview?days=${days}`);
  return response.data.data;
};

export const getTopIntents = async (days: number = 30): Promise<IntentStat[]> => {
  const response = await api.get(`/analytics/intents?days=${days}`);
  return response.data.data;
};

export const getTopLocations = async (days: number = 30): Promise<LocationStat[]> => {
  const response = await api.get(`/analytics/locations?days=${days}`);
  return response.data.data; // array of objects
};

export const getTrafficSources = async (days: number = 30): Promise<TrafficSource[]> => {
  const response = await api.get(`/analytics/sources?days=${days}`);
  return response.data.data;
};

export const getTrafficTrend = async (days: number = 30): Promise<{ date: string; count: number }[]> => {
  const response = await api.get(`/analytics/trend?days=${days}`);
  return response.data.data;
};

export const getSessions = async (limit: number = 20, offset: number = 0): Promise<Session[]> => {
  const response = await api.get(`/analytics/sessions?limit=${limit}&offset=${offset}`);
  // Handle standardized response
  const data = response.data.data || response.data;
  return Array.isArray(data) ? data : [];
};

export const getSession = async (sessionId: string): Promise<SessionDetail> => {
  const response = await api.get(`/widgets/session/${sessionId}`);
  return response.data.data;
};

// Widget/Guest endpoints for 3-pane view
export const getGuests = async (
  params: { q?: string; limit?: number; offset?: number } = {},
): Promise<Paginated<Guest>> => {
  const response = await api.get('/widgets/guests', { params });
  return response.data.data;
};

export const getGuest = async (guestId: string): Promise<Guest> => {
  const response = await api.get(`/widgets/guests/${guestId}`);
  return response.data.data;
};

export const getGuestSessions = async (
  guestId: string,
  params: { limit?: number; offset?: number } = {},
): Promise<Paginated<GuestSession>> => {
  const response = await api.get(`/widgets/sessions/${guestId}/history`, { params });
  return response.data.data;
};

export const analyzeSession = async (sessionId: string): Promise<GuestSession> => {
  const response = await api.post(`/widgets/session/${sessionId}/analyze`);
  return response.data.data || response.data;
};

export const toggleLeadStatus = async (guestId: string, isLead: boolean): Promise<Guest> => {
  const response = await api.put(`/widgets/guests/${guestId}/lead`, { is_lead: isLead });
  return response.data.data;
};

// Escalation endpoints
export const getEscalations = async (
  businessId: string,
  params: { status?: string; limit?: number; offset?: number } = {},
): Promise<Paginated<Escalation>> => {
  const response = await api.get('/escalations', {
    params: { business_id: businessId, ...params },
  });
  return response.data.data;
};

export const getEscalationDetails = async (escalationId: string): Promise<EscalationDetail> => {
  const response = await api.get(`/escalations/${escalationId}`);
  return response.data.data;
};

export const resolveEscalation = async (escalationId: string): Promise<{ status: string }> => {
  const response = await api.post(`/escalations/${escalationId}/resolve`);
  return response.data.data;
};

// Subscription endpoints
export const initializeSubscription = async (planId: number, provider: string = 'paystack'): Promise<ApiResponse<{ authorization_url: string; access_code: string; reference: string }>> => {
  const response = await api.post('/subscription/initialize', { plan_id: planId, provider });
  return response.data;
};

export const cancelSubscription = async (provider: string = 'paystack'): Promise<ApiResponse<null>> => {
  const response = await api.post('/subscription/cancel', { provider });
  return response.data;
};

export const upgradeSubscription = async (newPlanId: number, provider: string = 'paystack'): Promise<ApiResponse<unknown>> => {
  const response = await api.post('/subscription/upgrade', { new_plan_id: newPlanId, provider });
  return response.data;
};

export const enableSubscription = async (provider: string = 'paystack'): Promise<ApiResponse<{ authorization_url?: string; access_code?: string; reference?: string } | null>> => {
  const response = await api.post('/subscription/enable', { provider });
  return response.data;
};

export const verifySubscriptionTransaction = async (reference: string, provider: string = 'paystack'): Promise<ApiResponse<unknown>> => {
  const response = await api.post('/subscription/verify', { reference, provider });
  return response.data;
};

export const getPublicPlans = async (): Promise<ApiResponse<unknown>> => {
  const response = await api.get('/public/plans');
  return response.data;
};

// ---------------- WhatsApp Broadcast ----------------

export interface WhatsAppTemplate {
  id: string;
  business_id: string;
  meta_template_id: string | null;
  name: string;
  category: string;
  language: string;
  header: Record<string, unknown> | null;
  body_text: string;
  footer: string | null;
  buttons: unknown[] | null;
  variables: string[] | null;
  status: string;
  rejection_reason: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface WhatsAppContact {
  id: string;
  business_id: string;
  phone_e164: string;
  name: string | null;
  tags: string[] | null;
  source: string;
  opted_in: boolean;
  last_contacted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WhatsAppContactList {
  id: string;
  business_id: string;
  name: string;
  description: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface WhatsAppCampaign {
  id: string;
  business_id: string;
  name: string;
  template_id: string;
  audience_type: string;
  audience_ref: Record<string, unknown> | null;
  variable_mapping: Record<string, unknown> | null;
  status: string;
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  total_recipients: number;
  sent_count: number;
  delivered_count: number;
  read_count: number;
  failed_count: number;
  created_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface WhatsAppCampaignMessage {
  id: string;
  campaign_id: string;
  contact_phone: string;
  variables_snapshot: Record<string, string> | null;
  meta_message_id: string | null;
  status: string;
  error_code: string | null;
  error_message: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// Templates

export const listWhatsAppTemplates = async (): Promise<WhatsAppTemplate[]> => {
  const res = await api.get('/whatsapp/templates');
  return res.data.data || [];
};

export const createWhatsAppTemplate = async (payload: {
  name: string;
  category: string;
  language: string;
  body_text: string;
  header?: Record<string, unknown> | null;
  footer?: string | null;
  buttons?: unknown[] | null;
}): Promise<WhatsAppTemplate> => {
  const res = await api.post('/whatsapp/templates', payload);
  return res.data.data;
};

export const updateWhatsAppTemplate = async (
  id: string,
  payload: {
    name?: string;
    category?: string;
    language?: string;
    body_text?: string;
    header?: Record<string, unknown> | null;
    footer?: string | null;
    buttons?: unknown[] | null;
  }
): Promise<WhatsAppTemplate> => {
  const res = await api.patch(`/whatsapp/templates/${id}`, payload);
  return res.data.data;
};

export const submitWhatsAppTemplate = async (id: string): Promise<WhatsAppTemplate> => {
  const res = await api.post(`/whatsapp/templates/${id}/submit`);
  return res.data.data;
};

export const importWhatsAppTemplates = async (): Promise<WhatsAppTemplate[]> => {
  const res = await api.post('/whatsapp/templates/import');
  return res.data.data || [];
};

export const deleteWhatsAppTemplate = async (id: string): Promise<void> => {
  await api.delete(`/whatsapp/templates/${id}`);
};

// Contacts

export const listWhatsAppContacts = async (
  params: { q?: string; limit?: number; offset?: number } = {},
): Promise<Paginated<WhatsAppContact>> => {
  const res = await api.get('/whatsapp/contacts', { params });
  return res.data.data;
};

export const createWhatsAppContact = async (payload: {
  phone: string;
  name?: string;
  tags?: string[];
  opted_in?: boolean;
}): Promise<WhatsAppContact> => {
  const res = await api.post('/whatsapp/contacts', payload);
  return res.data.data;
};

export const updateWhatsAppContact = async (
  id: string,
  payload: { name?: string; tags?: string[]; opted_in?: boolean },
): Promise<WhatsAppContact> => {
  const res = await api.patch(`/whatsapp/contacts/${id}`, payload);
  return res.data.data;
};

export const deleteWhatsAppContact = async (id: string): Promise<void> => {
  await api.delete(`/whatsapp/contacts/${id}`);
};

export const uploadWhatsAppContactsCsv = async (
  file: File,
): Promise<{ imported: number; skipped: number; errors: string[] }> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/whatsapp/contacts/csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data.data;
};

export const importWhatsAppGuests = async (
  payload: { min_sessions?: number; last_seen_after?: string } = {},
): Promise<{ imported: number }> => {
  const res = await api.post('/whatsapp/contacts/import-guests', payload);
  return res.data.data;
};

// Contact Lists

export const listWhatsAppContactLists = async (): Promise<WhatsAppContactList[]> => {
  const res = await api.get('/whatsapp/contact-lists');
  return res.data.data || [];
};

export const createWhatsAppContactList = async (payload: {
  name: string;
  description?: string;
}): Promise<WhatsAppContactList> => {
  const res = await api.post('/whatsapp/contact-lists', payload);
  return res.data.data;
};

export const updateWhatsAppContactList = async (
  id: string,
  payload: { name?: string; description?: string },
): Promise<WhatsAppContactList> => {
  const res = await api.patch(`/whatsapp/contact-lists/${id}`, payload);
  return res.data.data;
};

export const deleteWhatsAppContactList = async (id: string): Promise<void> => {
  await api.delete(`/whatsapp/contact-lists/${id}`);
};

export const addWhatsAppContactListMembers = async (
  listId: string,
  contactIds: string[],
): Promise<WhatsAppContactList> => {
  const res = await api.post(`/whatsapp/contact-lists/${listId}/members`, {
    contact_ids: contactIds,
  });
  return res.data.data;
};

export const removeWhatsAppContactListMembers = async (
  listId: string,
  contactIds: string[],
): Promise<WhatsAppContactList> => {
  const res = await api.delete(`/whatsapp/contact-lists/${listId}/members`, {
    data: { contact_ids: contactIds },
  });
  return res.data.data;
};

// Campaigns

export const listWhatsAppCampaigns = async (
  params: { status?: string; limit?: number; offset?: number } = {},
): Promise<Paginated<WhatsAppCampaign>> => {
  const res = await api.get('/whatsapp/campaigns', { params });
  return res.data.data;
};

export const createWhatsAppCampaign = async (payload: {
  name: string;
  template_id: string;
  audience_type: string;
  audience_ref: Record<string, unknown>;
  variable_mapping: Record<string, unknown>;
  scheduled_at?: string | null;
  send_now?: boolean;
}): Promise<WhatsAppCampaign> => {
  const res = await api.post('/whatsapp/campaigns', payload);
  return res.data.data;
};

export const getWhatsAppCampaign = async (id: string): Promise<WhatsAppCampaign> => {
  const res = await api.get(`/whatsapp/campaigns/${id}`);
  return res.data.data;
};

export const listWhatsAppCampaignMessages = async (
  id: string,
  params: { status?: string; limit?: number; offset?: number } = {},
): Promise<Paginated<WhatsAppCampaignMessage>> => {
  const res = await api.get(`/whatsapp/campaigns/${id}/messages`, { params });
  return res.data.data;
};

export const sendWhatsAppCampaign = async (
  id: string,
  scheduledAt?: string | null,
): Promise<WhatsAppCampaign> => {
  const res = await api.post(`/whatsapp/campaigns/${id}/send`, {
    scheduled_at: scheduledAt ?? null,
  });
  return res.data.data;
};

export const cancelWhatsAppCampaign = async (id: string): Promise<WhatsAppCampaign> => {
  const res = await api.post(`/whatsapp/campaigns/${id}/cancel`);
  return res.data.data;
};

// ---------------- Product Catalogue ----------------

export const listProducts = async (
  params: { q?: string; category?: string; limit?: number; offset?: number } = {},
): Promise<Product[] | Paginated<Product>> => {
  const res = await api.get('/products', { params });
  return res.data.data;
};

export const getProduct = async (id: string): Promise<Product> => {
  const res = await api.get(`/products/${id}`);
  return res.data.data;
};

export const createProduct = async (data: CreateProductData): Promise<Product> => {
  const res = await api.post('/products', data);
  return res.data.data;
};

export const updateProduct = async (id: string, data: UpdateProductData): Promise<Product> => {
  const res = await api.put(`/products/${id}`, data);
  return res.data.data;
};

export const deleteProduct = async (id: string): Promise<void> => {
  await api.delete(`/products/${id}`);
};

export const bulkUploadProducts = async (
  file: File,
): Promise<{ imported: number; updated: number; errors: string[] }> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/products/bulk', formData, {
    headers: { 'Content-Type': undefined },
  });
  return res.data.data;
};

export default api;
