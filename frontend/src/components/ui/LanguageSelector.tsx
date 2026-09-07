import React from 'react';
import { useLanguageStore } from '@/store/useLanguageStore';
import { SUPPORTED_LANGUAGES, LanguageCode } from '@/i18n';
import { Globe } from 'lucide-react';

export const LanguageSelector: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { language, setLanguage } = useLanguageStore();

  return (
    <div className={`flex items-center space-x-1 ${className}`}>
      <Globe className="w-4 h-4 text-muted dark:text-stone-400 shrink-0" />
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value as LanguageCode)}
        className="bg-transparent text-xs font-semibold text-ink dark:text-stone-200 border border-stone-200 dark:border-stone-800 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-brand-500 cursor-pointer"
        aria-label="Select Application Language"
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} className="bg-white dark:bg-stone-900 text-ink dark:text-stone-100">
            {lang.nativeName} ({lang.code.toUpperCase()})
          </option>
        ))}
      </select>
    </div>
  );
};
