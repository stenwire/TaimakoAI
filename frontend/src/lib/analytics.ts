import api from './api';

export interface AnalyticsOverview {
  total_sessions: number;
  total_guests: number;
  leads_captured: number;
  avg_session_duration: number;
  returning_guests_percentage: number;
}

export interface AnalyticsIntent {
  intent: string;
  count: number;
}

export interface AnalyticsLocation {
  country: string;
  city: string;
  count: number;
}

export interface AnalyticsSource {
  source: string;
  count: number;
}

export const getAnalyticsOverview = async (days: number = 30): Promise<AnalyticsOverview> => {
  const response = await api.get('/analytics/overview', { params: { days } });
  return response.data;
};

export const getTopIntents = async (days: number = 30): Promise<AnalyticsIntent[]> => {
  const response = await api.get('/analytics/intents', { params: { days } });
  return response.data;
};

export const getTopLocations = async (days: number = 30): Promise<AnalyticsLocation[]> => {
  const response = await api.get('/analytics/locations', { params: { days } });
  return response.data;
};

export const getTrafficSources = async (days: number = 30): Promise<AnalyticsSource[]> => {
  const response = await api.get('/analytics/sources', { params: { days } });
  return response.data;
};
