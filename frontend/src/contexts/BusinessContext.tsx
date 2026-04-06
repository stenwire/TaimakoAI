'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { getBusinessProfile } from '@/lib/api';
import type { BusinessProfile } from '@/lib/types';

interface BusinessContextType {
  businessProfile: BusinessProfile | null;
  isLoading: boolean;
  refreshBusinessProfile: () => Promise<void>;
}

const BusinessContext = createContext<BusinessContextType | undefined>(undefined);

export function BusinessProvider({ children }: { children: ReactNode }) {
  const [businessProfile, setBusinessProfile] = useState<BusinessProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshBusinessProfile = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await getBusinessProfile();
      if (response.data) {
        setBusinessProfile(response.data);
      } else {
        setBusinessProfile(null);
      }
    } catch (error) {
      console.error("Failed to fetch business profile:", error);
      setBusinessProfile(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <BusinessContext.Provider value={{ businessProfile, isLoading, refreshBusinessProfile }}>
      {children}
    </BusinessContext.Provider>
  );
}

export function useBusiness() {
  const context = useContext(BusinessContext);
  if (context === undefined) {
    throw new Error('useBusiness must be used within a BusinessProvider');
  }
  return context;
}
