'use client';

import React, { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { LayoutDashboard, Building2, FileText, MessageSquare, LogOut, Menu, X, Settings, Users } from 'lucide-react';
import Sidebar from '@/components/ui/Sidebar';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import Button from '@/components/ui/Button';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const sidebarSections = [
    {
      items: [
        { label: 'Overview', href: '/dashboard', icon: LayoutDashboard },
        { label: 'Business Profile', href: '/dashboard/business', icon: Building2 },
        { label: 'Documents', href: '/dashboard/documents', icon: FileText },
        { label: 'Chat', href: '/dashboard/chat', icon: MessageSquare },
        { label: 'Analytics', href: '/dashboard/analytics', icon: LayoutDashboard }, // Using LayoutDashboard or similar
        { label: 'Interactions', href: '/dashboard/widget-interactions', icon: Users },
        { label: 'Widget Settings', href: '/dashboard/widget-settings', icon: Settings },
      ],
    },
  ];

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[var(--bg-secondary)] flex">
        {/* Mobile Header */}
        <div className="lg:hidden fixed top-0 left-0 right-0 z-20 bg-[var(--bg-primary)] border-b border-[var(--border-subtle)] px-4 py-3 flex items-center justify-between">
          <h1 className="text-h2 text-[var(--text-primary)]">Agentic CX</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 hover:bg-[var(--bg-secondary)] rounded-[var(--radius-sm)] transition-colors"
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6 text-[var(--text-primary)]" />
            ) : (
              <Menu className="w-6 h-6 text-[var(--text-primary)]" />
            )}
          </button>
        </div>

        {/* Sidebar - Desktop */}
        <div className="hidden lg:block">
          <div className="fixed top-0 left-0 h-full">
            <div className="h-full flex flex-col">
              {/* Sidebar Header */}
              <div className="p-6 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
                <h1 className="text-h2 text-[var(--text-primary)]">Agentic CX</h1>
                <p className="text-small text-[var(--text-secondary)] mt-1">
                  {user?.name || 'User'}
                </p>
              </div>

              {/* Sidebar Navigation */}
              <div className="flex-1 overflow-y-auto">
                <Sidebar sections={sidebarSections} collapsed={sidebarCollapsed} />
              </div>

              {/* Sidebar Footer */}
              <div className="p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={logout}
                >
                  <LogOut className="w-5 h-5" />
                  {!sidebarCollapsed && <span>Logout</span>}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Sidebar */}
        {mobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-30 bg-black/40" onClick={() => setMobileMenuOpen(false)}>
            <div
              className="w-64 h-full bg-[var(--bg-secondary)] border-r border-[var(--border-subtle)]"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="h-full flex flex-col">
                <div className="p-6 border-b border-[var(--border-subtle)]">
                  <h1 className="text-h2 text-[var(--text-primary)]">Agentic CX</h1>
                  <p className="text-small text-[var(--text-secondary)] mt-1">
                    {user?.name || 'User'}
                  </p>
                </div>

                <div className="flex-1 overflow-y-auto">
                  <Sidebar sections={sidebarSections} />
                </div>

                <div className="p-4 border-t border-[var(--border-subtle)]">
                  <Button
                    variant="ghost"
                    className="w-full justify-start"
                    onClick={() => {
                      logout();
                      setMobileMenuOpen(false);
                    }}
                  >
                    <LogOut className="w-5 h-5" />
                    <span>Logout</span>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 lg:ml-60">
          <div className="pt-16 lg:pt-0">
            <main className="p-4 lg:p-8">
              {children}
            </main>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
