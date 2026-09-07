import { create } from 'zustand';
import { LanguageCode, getTranslation, formatCurrency, formatDate, formatNumber } from '@/i18n';

interface LanguageState {
  language: LanguageCode;
  setLanguage: (lang: LanguageCode) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  formatCurrency: (amount: number | string) => string;
  formatDate: (date: Date | string | null | undefined) => string;
  formatNumber: (val: number | string) => string;
}

const STORAGE_KEY = 'aischoolos_language';

const getInitialLanguage = (): LanguageCode => {
  if (typeof window !== 'undefined' && window.localStorage) {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'en' || saved === 'te') {
      return saved as LanguageCode;
    }
  }
  return 'en';
};

export const useLanguageStore = create<LanguageState>((set, get) => ({
  language: getInitialLanguage(),
  setLanguage: (lang: LanguageCode) => {
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem(STORAGE_KEY, lang);
    }
    set({ language: lang });
  },
  t: (key: string, params?: Record<string, string | number>) => {
    return getTranslation(key, get().language, params);
  },
  formatCurrency: (amount: number | string) => {
    return formatCurrency(amount, get().language);
  },
  formatDate: (date: Date | string | null | undefined) => {
    return formatDate(date, get().language);
  },
  formatNumber: (val: number | string) => {
    return formatNumber(val, get().language);
  },
}));
