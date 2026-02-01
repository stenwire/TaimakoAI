
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

interface MarkdownProps {
  content: string;
  variant?: 'default' | 'inverted' | 'widget-user';
  className?: string;
}

export default function Markdown({ content, variant = 'default', className }: MarkdownProps) {
  return (
    <div className={cn(
      "prose prose-sm max-w-none break-words",
      // Color variants
      variant === 'inverted' && "prose-invert text-white",
      variant === 'widget-user' && "prose-invert text-white prose-headings:text-white prose-p:text-white prose-strong:text-white prose-a:text-white/90",
      variant === 'default' && "text-[var(--text-primary)] prose-headings:text-[var(--text-primary)] prose-strong:text-[var(--text-primary)]",
      className
    )}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ node, ...props }) => <p className="mb-1 last:mb-0" {...props} />,
          ul: ({ node, ...props }) => <ul className="pl-4 mb-2 list-disc" {...props} />,
          ol: ({ node, ...props }) => <ol className="pl-4 mb-2 list-decimal" {...props} />,
          li: ({ node, ...props }) => <li className="mb-0.5" {...props} />,
          a: ({ node, ...props }) => <a className="underline hover:text-blue-500 transition-colors" target="_blank" rel="noopener noreferrer" {...props} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
