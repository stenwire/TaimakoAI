'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { LayoutDashboard, Building2, FileText, MessageSquare, LogOut, Menu, X, Settings, Users, AlertTriangle, Bot } from 'lucide-react';
import Sidebar, { SidebarSection } from '@/components/ui/Sidebar';
import { useAuth } from '@/contexts/AuthContext';
import { useBusiness, BusinessProvider } from '@/contexts/BusinessContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import Button from '@/components/ui/Button';

function DashboardLayoutInner({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const { isApiKeySet, isLoading, refreshBusinessProfile } = useBusiness();

  // Check for API key status on mount and when user changes
  useEffect(() => {
    if (user) {
      refreshBusinessProfile();
    }
  }, [user, refreshBusinessProfile]);

  // Redirect if locked and trying to access other pages
  useEffect(() => {
    if (!isLoading && !isApiKeySet) {
      if (pathname !== '/dashboard/business') {
        router.push('/dashboard/business');
      }
    }
  }, [isApiKeySet, isLoading, pathname, router]);

  const apiKeyMissing = !isApiKeySet;
  const checkingKey = isLoading;

  const baseSidebarSections = [
    {
      items: [
        { label: 'Overview', href: '/dashboard', icon: LayoutDashboard },
        { label: 'Sessions', href: '/dashboard/sessions', icon: MessageSquare },
        { label: 'Analytics', href: '/dashboard/analytics', icon: Building2 },
        { label: 'Knowledge Base', href: '/dashboard/documents', icon: FileText },
        { label: 'Widget', href: '/dashboard/widget-settings', icon: Settings },
        { label: 'Human Handoff', href: '/dashboard/handoff', icon: Users },
        { label: 'Test Agent', href: '/dashboard/chat', icon: Bot },
        { label: 'Settings', href: '/dashboard/business', icon: Settings },
      ],
    },
  ];

  // Apply lockout to sidebar
  const sidebarSections: SidebarSection[] = baseSidebarSections.map(section => ({
    ...section,
    items: section.items.map(item => ({
      ...item,
      disabled: apiKeyMissing && item.href !== '/dashboard/business'
    }))
  }));

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[var(--bg-secondary)] flex font-sans">

        {/* Mobile Header */}
        <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-[var(--bg-primary)] border-b border-[var(--border-subtle)] px-4 py-3 flex items-center justify-between">
          <h1 className="text-h2 font-space tracking-tight text-[var(--brand-primary)] font-bold">Taimako</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 hover:bg-[var(--bg-secondary)] rounded-[var(--radius-sm)] transition-colors text-[var(--text-primary)]"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Sidebar - Desktop */}
        <div className={sidebarCollapsed ? "hidden lg:block w-16 transition-all duration-300 relative z-40" : "hidden lg:block w-60 transition-all duration-300 relative z-40"}>
          <div className="fixed top-0 left-0 h-full bg-[var(--bg-primary)] border-r border-[var(--border-subtle)]">
            <div className="h-full flex flex-col w-full">
              {/* Sidebar Header */}
              <div className="p-6 border-b border-[var(--border-subtle)] flex items-center justify-between">
                {!sidebarCollapsed && (
                  <h1 className="text-xl font-space font-bold text-[var(--brand-primary)] tracking-tight">Taimako</h1>
                )}
                <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)} className="p-1 hover:bg-[var(--bg-tertiary)] rounded text-[var(--text-secondary)]">
                  {sidebarCollapsed ? <Menu className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
                </button>
              </div>

              {/* Sidebar Navigation */}
              <div className="flex-1 overflow-y-auto w-full">
                <Sidebar sections={sidebarSections} collapsed={sidebarCollapsed} />
              </div>

              {/* Sidebar Footer */}
              <div className="p-4 border-t border-[var(--border-subtle)]">
                <div className="flex flex-col gap-2">
                  {!sidebarCollapsed && <div className="px-2 text-xs text-[var(--text-tertiary)] uppercase font-bold tracking-wider">User</div>}
                  <div className={`flex items-center gap-3 px-2 ${sidebarCollapsed ? 'justify-center' : ''}`}>
                    <div className="w-8 h-8 rounded-full bg-[var(--brand-secondary)] flex items-center justify-center text-white font-bold text-xs">
                      {user?.name?.[0] || 'U'}
                    </div>
                    {!sidebarCollapsed && (
                      <div className="flex-1 overflow-hidden">
                        <div className="text-sm font-medium text-[var(--text-primary)] truncate">{user?.name}</div>
                        <div className="text-xs text-[var(--text-tertiary)] truncate">Online</div>
                      </div>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    className={`w-full ${sidebarCollapsed ? 'justify-center px-0' : 'justify-start'} mt-2 text-[var(--text-secondary)] hover:text-[var(--status-error)] hover:bg-[var(--bg-tertiary)]`}
                    onClick={logout}
                  >
                    <LogOut className="w-4 h-4" />
                    {!sidebarCollapsed && <span className="ml-2">Logout</span>}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Sidebar */}
        {mobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-50 bg-black/40 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)}>
            <div
              className="w-72 h-full bg-[var(--bg-primary)] border-r border-[var(--border-subtle)] shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="h-full flex flex-col">
                <div className="p-6 border-b border-[var(--border-subtle)] flex justify-between items-center">
                  <h1 className="text-2xl font-space font-bold text-[var(--brand-primary)]">Taimako</h1>
                  <button onClick={() => setMobileMenuOpen(false)}><X className="w-6 h-6 text-[var(--text-secondary)]" /></button>
                </div>

                <div className="flex-1 overflow-y-auto">
                  <Sidebar sections={sidebarSections} />
                </div>

                <div className="p-6 border-t border-[var(--border-subtle)]">
                  <Button onClick={logout} variant="ghost" className="w-full justify-start text-[var(--text-secondary)]">
                    <LogOut className="w-5 h-5 mr-3" /> Logout
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0 transition-all duration-300">

          {/* Missing Key Warning Banner */}
          {apiKeyMissing && !checkingKey && (
            <div className="bg-[var(--warning-bg)] border-l-4 border-[var(--warning)] p-4 sticky top-0 z-30 shadow-md">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <AlertTriangle className="h-5 w-5 text-[var(--warning)]" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-[var(--warning-text)]">
                    <span className="font-bold">Action Required: </span>
                    You must set your Google Gemini API Key in <span className="font-bold cursor-pointer underline" onClick={() => router.push('/dashboard/business')}>Settings</span> to use the AI features. Access to other pages is restricted until configured.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className={`h-full ${apiKeyMissing ? '' : 'pt-16 lg:pt-0'}`}>
            {/* If blocked, mobile header might overlap if we don't account for paddingTop. 
                 The original had pt-16 lg:pt-0. If we add banner, we shift content down. 
                 Actually, just keep original padding. Content is children.
             */}
            <div className="pt-16 lg:pt-0 h-full">
              <main className="p-4 lg:p-8 h-full overflow-y-auto">
                <div className="max-w-[1440px] mx-auto w-full h-full">
                  {children}
                </div>
              </main>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <BusinessProvider>
      <DashboardLayoutInner>{children}</DashboardLayoutInner>
    </BusinessProvider>
  );
}
