import React from 'react';
import { cn } from '@/lib/utils';

interface LoaderProps {
  className?: string;
}

const Loader: React.FC<LoaderProps> = ({ className }) => {
  return (
    <div className={cn("loader", className)} role="status" aria-label="Loading" />
  );
};

export default Loader;
