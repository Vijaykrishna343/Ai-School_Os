import { Loader2 } from 'lucide-react';

export const LoadingState = ({ message = 'Loading AI School OS...' }: { message?: string }) => (
  <div className="flex flex-col items-center justify-center p-12 text-center min-h-[200px]">
    <Loader2 className="w-8 h-8 animate-spin text-brand-600 dark:text-brand-400 mb-3" />
    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">{message}</p>
  </div>
);
