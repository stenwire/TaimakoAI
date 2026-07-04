import React from 'react';
import Loader from '@/components/ui/Loader';

export default function Loading() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-[var(--bg-primary)]">
      <Loader />
    </div>
  );
}
