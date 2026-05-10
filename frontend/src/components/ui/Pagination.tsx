import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onPageChange: (offset: number) => void;
  className?: string;
}

function buildPageList(currentPage: number, pageCount: number): (number | 'ellipsis')[] {
  if (pageCount <= 7) {
    return Array.from({ length: pageCount }, (_, i) => i + 1);
  }

  const pages: (number | 'ellipsis')[] = [1];

  const start = Math.max(2, currentPage - 1);
  const end = Math.min(pageCount - 1, currentPage + 1);

  if (start > 2) pages.push('ellipsis');
  for (let i = start; i <= end; i++) pages.push(i);
  if (end < pageCount - 1) pages.push('ellipsis');

  pages.push(pageCount);
  return pages;
}

const Pagination: React.FC<PaginationProps> = ({
  total,
  limit,
  offset,
  onPageChange,
  className,
}) => {
  if (total === 0) return null;

  const pageCount = Math.max(1, Math.ceil(total / limit));
  const currentPage = Math.floor(offset / limit) + 1;
  const rangeStart = offset + 1;
  const rangeEnd = Math.min(offset + limit, total);

  const goTo = (page: number) => {
    const next = Math.min(Math.max(1, page), pageCount);
    onPageChange((next - 1) * limit);
  };

  const baseBtn =
    'inline-flex items-center justify-center min-w-9 h-9 px-3 text-sm font-medium rounded-[var(--radius-sm)] border transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]/20';
  const inactive =
    'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border-subtle)] hover:bg-[var(--bg-secondary)]';
  const active =
    'bg-[var(--brand-primary)] text-white border-[var(--brand-primary)] cursor-default';
  const disabled = 'opacity-40 pointer-events-none';

  const pages = buildPageList(currentPage, pageCount);

  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-4',
        className,
      )}
    >
      <div className="text-xs text-[var(--text-tertiary)]">
        Showing <span className="font-medium text-[var(--text-secondary)]">{rangeStart}</span>
        {'–'}
        <span className="font-medium text-[var(--text-secondary)]">{rangeEnd}</span> of{' '}
        <span className="font-medium text-[var(--text-secondary)]">{total}</span>
      </div>

      <nav className="flex items-center gap-1" aria-label="Pagination">
        <button
          type="button"
          onClick={() => goTo(currentPage - 1)}
          aria-label="Previous page"
          className={cn(baseBtn, inactive, currentPage === 1 && disabled)}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {pages.map((p, i) =>
          p === 'ellipsis' ? (
            <span
              key={`e${i}`}
              className="inline-flex items-center justify-center min-w-9 h-9 px-2 text-sm text-[var(--text-tertiary)]"
            >
              …
            </span>
          ) : (
            <button
              key={p}
              type="button"
              onClick={() => goTo(p)}
              aria-current={p === currentPage ? 'page' : undefined}
              className={cn(baseBtn, p === currentPage ? active : inactive)}
            >
              {p}
            </button>
          ),
        )}

        <button
          type="button"
          onClick={() => goTo(currentPage + 1)}
          aria-label="Next page"
          className={cn(baseBtn, inactive, currentPage === pageCount && disabled)}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </nav>
    </div>
  );
};

export default Pagination;
