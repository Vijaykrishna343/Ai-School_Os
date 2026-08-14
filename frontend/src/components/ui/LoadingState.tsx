// LoadingState: institutional retrieval indicator
// Avoids generic spinner centers in favor of a compact operational message
import React from 'react';

export const LoadingState = ({ message = 'Retrieving records...' }: { message?: string }) => (
  <div className="flex flex-col items-center justify-center py-12 px-6 text-center min-h-[200px]">
    {/* Compact triple-dot pulse pattern — no oversized spinner */}
    <div className="flex items-center gap-1 mb-4" aria-hidden="true">
      <span className="w-1.5 h-1.5 rounded-none bg-brand-500/60 dark:bg-brand-400/60 animate-bounce [animation-delay:-0.3s]" />
      <span className="w-1.5 h-1.5 rounded-none bg-brand-500/60 dark:bg-brand-400/60 animate-bounce [animation-delay:-0.15s]" />
      <span className="w-1.5 h-1.5 rounded-none bg-brand-500/60 dark:bg-brand-400/60 animate-bounce" />
    </div>
    <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 leading-none">
      {message}
    </p>
  </div>
);
