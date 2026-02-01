import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

export interface SidebarItem {
  label: string;
  href: string;
  icon: LucideIcon;
  disabled?: boolean;
}


export interface SidebarSection {
  title?: string;
  items: SidebarItem[];
}

export interface SidebarProps {
  sections: SidebarSection[];
  collapsed?: boolean;
  onItemClick?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ sections, collapsed = false, onItemClick }) => {
  const pathname = usePathname();

  return (
    <div className="flex flex-col h-full py-6">
      {sections.map((section, sectionIndex) => (
        <div key={sectionIndex} className="mb-6">
          {section.title && !collapsed && (
            <h3 className="text-h3 px-4 mb-2">{section.title}</h3>
          )}
          <nav className="space-y-1 px-2">
            {section.items.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;

              if (item.disabled) {
                return (
                  <div
                    key={item.href}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2 rounded-[var(--radius-md)] transition-all duration-200 group relative',
                      'text-[14px] font-medium opacity-50 cursor-not-allowed bg-transparent text-[var(--text-tertiary)]',
                      collapsed ? 'justify-center' : ''
                    )}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0 text-[var(--text-tertiary)]" />
                    {!collapsed && <span>{item.label}</span>}
                    {collapsed && (
                      <div className="absolute left-14 bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                        {item.label} (Locked)
                      </div>
                    )}
                  </div>
                );
              }

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onItemClick}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-[var(--radius-md)] transition-all duration-200 group relative',
                    'text-[14px] font-medium',
                    collapsed ? 'justify-center' : '',
                    isActive
                      ? 'bg-[var(--brand-primary)] text-white shadow-[var(--shadow-glow)]'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]'
                  )}
                >
                  <Icon className={cn('w-5 h-5 flex-shrink-0 transition-colors', isActive ? 'text-white' : 'text-[var(--text-tertiary)] group-hover:text-[var(--text-primary)]')} />
                  {!collapsed && <span>{item.label}</span>}
                  {collapsed && (
                    <div className="absolute left-14 bg-[var(--brand-primary)] text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                      {item.label}
                    </div>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      ))}
    </div>
  );
};

export default Sidebar;
