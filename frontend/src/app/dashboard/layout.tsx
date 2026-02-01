'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { LayoutDashboard, Building2, FileText, MessageSquare, LogOut, Menu, X, Settings, Users, AlertTriangle, Bot, AlignLeft, ChevronLeft, ChevronRight } from 'lucide-react';
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
        { label: 'Escalations', href: '/dashboard/handoff', icon: Users },
        { label: 'Playground', href: '/dashboard/chat', icon: Bot },
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
      <div className="flex h-screen bg-[var(--bg-secondary)] font-sans overflow-hidden">

        {/* Mobile Header */}
        <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-[var(--bg-primary)] border-b border-[var(--border-subtle)] px-4 py-3 flex items-center justify-between h-16">
          <h1 className="text-xl font-space tracking-tight text-[var(--brand-primary)] font-bold">Taimako</h1>
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 hover:bg-[var(--bg-secondary)] rounded-[var(--radius-sm)] transition-colors text-[var(--text-primary)]"
            aria-label="Open Menu"
          >
            <AlignLeft className="w-6 h-6" />
          </button>
        </div>

        {/* Sidebar - Desktop */}
        <aside
          className={`hidden lg:flex flex-col border-r border-[var(--border-subtle)] bg-[var(--bg-primary)] transition-all duration-300 ease-in-out relative z-40 ${sidebarCollapsed ? 'w-16' : 'w-64'
            }`}
        >
          {/* Sidebar Header */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-[var(--border-subtle)] flex-shrink-0">
            {!sidebarCollapsed && (
              <h1 className="text-xl font-space font-bold text-[var(--brand-primary)] tracking-tight truncate">Taimako</h1>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className={`p-1.5 hover:bg-[var(--bg-tertiary)] rounded-md text-[var(--text-secondary)] transition-colors ${sidebarCollapsed ? 'mx-auto' : ''}`}
              aria-label={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            >
              {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          {/* Sidebar Navigation */}
          <div className="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
            <Sidebar sections={sidebarSections} collapsed={sidebarCollapsed} />
          </div>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-[var(--border-subtle)] flex-shrink-0">
            <div className="flex flex-col gap-2">
              <div className={`flex items-center gap-3 px-2 ${sidebarCollapsed ? 'justify-center' : ''}`}>
                <div className="w-8 h-8 rounded-full bg-[var(--brand-secondary)] flex items-center justify-center text-white font-bold text-xs flex-shrink-0 ring-2 ring-white">
                  {user?.name?.[0] || user?.email?.[0] || 'U'}
                </div>
                {!sidebarCollapsed && (
                  <div className="flex-1 overflow-hidden min-w-0">
                    <div className="text-sm font-medium text-[var(--text-primary)] truncate" title={user?.name}>{user?.name || 'User'}</div>
                    <div className="text-xs text-[var(--text-tertiary)] truncate" title={user?.email}>{user?.email}</div>
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
        </aside>

        {/* Mobile Sidebar Overlay */}
        {mobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-[60]">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity opacity-100"
              onClick={() => setMobileMenuOpen(false)}
            />

            {/* Drawer */}
            <div
              className="absolute top-0 left-0 bottom-0 w-72 bg-[var(--bg-primary)] shadow-2xl transform transition-transform duration-300 ease-out translate-x-0"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex flex-col h-full">
                <div className="h-16 flex items-center justify-between px-6 border-b border-[var(--border-subtle)]">
                  <h1 className="text-xl font-space font-bold text-[var(--brand-primary)]">Taimako</h1>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-2 -mr-2 text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-md"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                  <Sidebar sections={sidebarSections} onItemClick={() => setMobileMenuOpen(false)} />
                </div>

                <div className="p-6 border-t border-[var(--border-subtle)]">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-full bg-[var(--brand-secondary)] flex items-center justify-center text-white font-bold text-sm ring-2 ring-white">
                      {user?.name?.[0] || user?.email?.[0] || 'U'}
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <div className="text-sm font-medium text-[var(--text-primary)] truncate">{user?.name || 'User'}</div>
                      <div className="text-xs text-[var(--text-tertiary)] truncate">{user?.email}</div>
                    </div>
                  </div>
                  <Button onClick={logout} variant="ghost" className="w-full justify-start text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]">
                    <LogOut className="w-5 h-5 mr-3" /> Logout
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col min-w-0 bg-[var(--bg-secondary)] overflow-hidden relative">

          {/* Missing Key Warning */}
          {apiKeyMissing && !checkingKey && (
            <div className="bg-[var(--warning-bg)] border-l-4 border-[var(--warning)] p-4 shadow-sm z-30 flex-shrink-0">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <AlertTriangle className="h-5 w-5 text-[var(--warning)]" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-[var(--warning-text)]">
                    <span className="font-bold">Action Required: </span>
                    You must set your Google Gemini API Key in <span className="font-bold cursor-pointer underline hover:text-opacity-80" onClick={() => router.push('/dashboard/business')}>Settings</span> to use AI features.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto scroll-smooth">
            <div className="pt-16 lg:pt-0 min-h-full">
              <div className="p-4 lg:p-8 max-w-[1600px] mx-auto w-full">
                {children}
              </div>
            </div>
          </div>
        </main>
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
