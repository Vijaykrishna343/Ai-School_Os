import { Lock } from 'lucide-react';

export const ModulePlaceholderPage = ({
  title,
  phase,
  description,
}: {
  title: string;
  phase: string;
  description: string;
}) => (
  <div className="flex flex-col items-center justify-center p-12 text-center bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm min-h-[400px]">
    <div className="p-4 bg-brand-50 dark:bg-brand-950/60 rounded-3xl mb-4 text-brand-600 dark:text-brand-400">
      <Lock className="w-10 h-10" />
    </div>
    <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 rounded-full dark:bg-brand-950 dark:text-brand-300 mb-2">
      {phase}
    </span>
    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{title} Module</h2>
    <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-md">{description}</p>
    <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-800/60 rounded-2xl text-xs text-slate-600 dark:text-slate-300 max-w-lg border border-slate-100 dark:border-slate-800">
      Backend APIs are fully integrated & hardened. The UI interface for this feature will be enabled in {phase} as specified in the Phase 5 roadmap.
    </div>
  </div>
);
