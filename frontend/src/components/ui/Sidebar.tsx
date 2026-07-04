import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

export interface SidebarSubItem {
  label: string;
  href: string;
  disabled?: boolean;
}

export interface SidebarItem {
  label: string;
  href: string;
  icon: LucideIcon;
  disabled?: boolean;
  subItems?: SidebarSubItem[];
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
  const [expandedItems, setExpandedItems] = React.useState<Record<string, boolean>>({});

  const toggleExpand = (href: string) => {
    setExpandedItems(prev => ({ ...prev, [href]: !prev[href] }));
  };

  // Auto-expand if a subitem is active on mount
  React.useEffect(() => {
    sections.forEach(sec => {
      sec.items.forEach(item => {
        if (item.subItems?.some(sub => pathname.startsWith(sub.href))) {
          setExpandedItems(prev => ({ ...prev, [item.href]: true }));
        }
      });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  return (
    <div className="flex flex-col h-full py-6">
      {sections.map((section, sectionIndex) => (
        <div key={sectionIndex} className="mb-6">
          {section.title && !collapsed && (
            <h3 className="text-h3 px-4 mb-2">{section.title}</h3>
          )}
          <nav className="space-y-1 px-2">
            {section.items.map((item) => {
              const isDirectlyActive = pathname === item.href && !item.subItems?.length;
              const hasActiveSubItem = item.subItems?.some(sub => pathname.startsWith(sub.href));
              const isActive = isDirectlyActive || hasActiveSubItem;
              const isExpanded = expandedItems[item.href] || false;
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
                <div key={item.href} className="flex flex-col">
                  {item.subItems?.length ? (
                    <button
                      onClick={() => toggleExpand(item.href)}
                      className={cn(
                        'flex items-center justify-between gap-3 px-3 py-2 rounded-[var(--radius-md)] transition-all duration-200 group relative',
                        'text-[14px] font-medium w-full text-left',
                        collapsed ? 'justify-center' : '',
                        isActive && !isExpanded
                          ? 'bg-[var(--brand-primary)] text-white shadow-[var(--shadow-glow)]'
                          : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]'
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <Icon className={cn('w-5 h-5 flex-shrink-0 transition-colors', isActive && !isExpanded ? 'text-white' : 'text-[var(--text-tertiary)] group-hover:text-[var(--text-primary)]')} />
                        {!collapsed && <span>{item.label}</span>}
                      </div>
                      {!collapsed && (
                        <div className="flex-shrink-0">
                          {isExpanded ? (
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--text-tertiary)]"><polyline points="18 15 12 9 6 15"></polyline></svg>
                          ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--text-tertiary)]"><polyline points="6 9 12 15 18 9"></polyline></svg>
                          )}
                        </div>
                      )}
                      {collapsed && (
                        <div className="absolute left-14 bg-[var(--brand-primary)] text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                          {item.label} (Nested)
                        </div>
                      )}
                    </button>
                  ) : (
                    <Link
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
                  )}

                  {/* SubItems rendering */}
                  {(item.subItems?.length ?? 0) > 0 && isExpanded && !collapsed && (
                    <div className="flex flex-col mt-1 space-y-1 relative before:absolute before:left-[21px] before:top-0 before:bottom-0 before:w-px before:bg-[var(--border-subtle)]">
                      {item.subItems?.map(subItem => {
                        const isSubActive = pathname.startsWith(subItem.href);
                        if (subItem.disabled) {
                          return (
                            <div key={subItem.href} className="pl-10 pr-3 py-2 text-[13px] font-medium text-[var(--text-tertiary)] opacity-50 cursor-not-allowed flex items-center gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-tertiary)]" />
                              {subItem.label}
                            </div>
                          );
                        }
                        return (
                          <Link
                            key={subItem.href}
                            href={subItem.href}
                            onClick={onItemClick}
                            className={cn(
                              'pl-10 pr-3 py-2 text-[13px] font-medium rounded-[var(--radius-md)] transition-all flex items-center gap-2 relative',
                              isSubActive
                                ? 'text-[var(--brand-primary)] bg-[var(--brand-primary)]/10 font-semibold'
                                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'
                            )}
                          >
                            <span className={cn(
                              "w-1.5 h-1.5 rounded-full transition-colors",
                              isSubActive ? "bg-[var(--brand-primary)]" : "bg-transparent group-hover:bg-[var(--border-strong)]"
                            )} />
                            {subItem.label}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        </div>
      ))}
    </div>
  );
};

export default Sidebar;
