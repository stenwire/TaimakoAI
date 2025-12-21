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
  ApiResponse
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
    const originalRequest = error.config as any;

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
        } catch (refreshError) {
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

export default api;

