import enCommon from './locales/en/common.json';
import enNav from './locales/en/navigation.json';
import enStudents from './locales/en/students.json';
import enAuth from './locales/en/auth.json';
import enDashboard from './locales/en/dashboard.json';
import enAttendance from './locales/en/attendance.json';
import enFees from './locales/en/fees.json';
import enHostel from './locales/en/hostel.json';
import enEvents from './locales/en/events.json';
import enLeave from './locales/en/leave.json';
import enCommunication from './locales/en/communication.json';
import enTeachers from './locales/en/teachers.json';
import enAcademics from './locales/en/academics.json';
import enExams from './locales/en/exams.json';
import enTimetable from './locales/en/timetable.json';

import teCommon from './locales/te/common.json';
import teNav from './locales/te/navigation.json';
import teStudents from './locales/te/students.json';
import teAuth from './locales/te/auth.json';
import teDashboard from './locales/te/dashboard.json';
import teAttendance from './locales/te/attendance.json';
import teFees from './locales/te/fees.json';
import teHostel from './locales/te/hostel.json';
import teEvents from './locales/te/events.json';
import teLeave from './locales/te/leave.json';
import teCommunication from './locales/te/communication.json';
import teTeachers from './locales/te/teachers.json';
import teAcademics from './locales/te/academics.json';
import teExams from './locales/te/exams.json';
import teTimetable from './locales/te/timetable.json';

export type LanguageCode = 'en' | 'te';

export interface LanguageOption {
  code: LanguageCode;
  name: string;
  nativeName: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
];

export const translationResources: Record<LanguageCode, Record<string, any>> = {
  en: {
    common: enCommon,
    navigation: enNav,
    students: enStudents,
    auth: enAuth,
    dashboard: enDashboard,
    attendance: enAttendance,
    fees: enFees,
    hostel: enHostel,
    events: enEvents,
    leave: enLeave,
    communication: enCommunication,
    teachers: enTeachers,
    academics: enAcademics,
    exams: enExams,
    timetable: enTimetable,
  },
  te: {
    common: teCommon,
    navigation: teNav,
    students: teStudents,
    auth: teAuth,
    dashboard: teDashboard,
    attendance: teAttendance,
    fees: teFees,
    hostel: teHostel,
    events: teEvents,
    leave: teLeave,
    communication: teCommunication,
    teachers: teTeachers,
    academics: teAcademics,
    exams: teExams,
    timetable: teTimetable,
  },
};

/**
 * Resolves translation key using dot notation (e.g., 'common.actions.save' or 'students.title').
 * Falls back to English if key is missing in target language.
 */
export function getTranslation(
  key: string,
  language: LanguageCode = 'en',
  params?: Record<string, string | number>
): string {
  const parts = key.split('.');
  
  // Try primary language
  let result: any = translationResources[language];
  for (const part of parts) {
    if (result && typeof result === 'object' && part in result) {
      result = result[part];
    } else {
      result = null;
      break;
    }
  }

  // Fallback to English if missing
  if (result === null && language !== 'en') {
    result = translationResources.en;
    for (const part of parts) {
      if (result && typeof result === 'object' && part in result) {
        result = result[part];
      } else {
        result = null;
        break;
      }
    }
  }

  if (typeof result !== 'string') {
    return key; // Safe fallback key
  }

  // Variable Interpolation (e.g. {count} or {{count}})
  if (params) {
    let interpolated = result;
    for (const [paramKey, paramVal] of Object.entries(params)) {
      interpolated = interpolated
        .replace(new RegExp(`\\{\\{${paramKey}\\}\\}`, 'g'), String(paramVal))
        .replace(new RegExp(`\\{${paramKey}\\}`, 'g'), String(paramVal));
    }
    return interpolated;
  }

  return result;
}

/**
 * Locale-aware Currency Formatter (INR default)
 */
export function formatCurrency(amount: number | string, language: LanguageCode = 'en'): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '₹0';
  const locale = language === 'te' ? 'te-IN' : 'en-IN';
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(num);
}

/**
 * Locale-aware Date Formatter
 */
export function formatDate(dateVal: Date | string | null | undefined, language: LanguageCode = 'en'): string {
  if (!dateVal) return '';
  const d = typeof dateVal === 'string' ? new Date(dateVal) : dateVal;
  if (isNaN(d.getTime())) return String(dateVal);
  const locale = language === 'te' ? 'te-IN' : 'en-IN';
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(d);
}

/**
 * Locale-aware Number Formatter
 */
export function formatNumber(val: number | string, language: LanguageCode = 'en'): string {
  const num = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(num)) return '0';
  const locale = language === 'te' ? 'te-IN' : 'en-IN';
  return new Intl.NumberFormat(locale).format(num);
}
