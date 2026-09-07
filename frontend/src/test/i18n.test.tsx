import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { getTranslation, formatCurrency, formatDate, formatNumber, translationResources } from '@/i18n';
import { useLanguageStore } from '@/store/useLanguageStore';
import { LanguageSelector } from '@/components/ui/LanguageSelector';

describe('Phase 9.2 i18n Full Application Localization Test Suite', () => {
  beforeEach(() => {
    useLanguageStore.getState().setLanguage('en');
    localStorage.clear();
  });

  it('1. loads English translation keys accurately across all 15 modules', () => {
    expect(getTranslation('common.actions.save', 'en')).toBe('Save');
    expect(getTranslation('auth.title', 'en')).toContain('Sign In');
    expect(getTranslation('dashboard.title', 'en')).toBe('Administrative Command Center');
    expect(getTranslation('students.title', 'en')).toBe('Student Directory');
    expect(getTranslation('teachers.title', 'en')).toBe('Faculty & Staff Directory');
    expect(getTranslation('academics.title', 'en')).toBe('Academic Architecture Management');
    expect(getTranslation('attendance.status.present', 'en')).toBe('Present');
    expect(getTranslation('fees.status.paid', 'en')).toBe('Paid');
    expect(getTranslation('exams.title', 'en')).toBe('Examinations & Gradebook Operations');
    expect(getTranslation('timetable.title', 'en')).toBe('Timetable Operations & Schedules');
    expect(getTranslation('hostel.status.allocated', 'en')).toBe('Allocated');
    expect(getTranslation('events.categories.holiday', 'en')).toBe('Holiday');
    expect(getTranslation('leave.status.approved', 'en')).toBe('Approved');
    expect(getTranslation('communication.title', 'en')).toBe('Multi-Channel Communication Center');
  });

  it('2. loads Telugu translation keys accurately across all 15 modules', () => {
    expect(getTranslation('common.actions.save', 'te')).toBe('భద్రపరచు');
    expect(getTranslation('auth.title', 'te')).toContain('సైన్ ఇన్');
    expect(getTranslation('dashboard.title', 'te')).toContain('డాష్‌బోర్డ్');
    expect(getTranslation('students.title', 'te')).toBe('విద్యార్థుల వివరాలు');
    expect(getTranslation('teachers.title', 'te')).toBe('ఉపాధ్యాయులు & సిబ్బంది జాబితా');
    expect(getTranslation('academics.title', 'te')).toBe('విద్యా విషయాల నిర్మాణ నిర్వహణ');
    expect(getTranslation('attendance.status.present', 'te')).toBe('హాజరు');
    expect(getTranslation('fees.status.paid', 'te')).toBe('చెల్లించబడింది');
    expect(getTranslation('exams.title', 'te')).toBe('పరీక్షలు & మార్కుల నమోదు నిర్వహణ');
    expect(getTranslation('timetable.title', 'te')).toBe('సమయ పట్టిక (టైమ్‌టేబుల్) నిర్వహణ');
    expect(getTranslation('hostel.status.allocated', 'te')).toBe('కేటాయించబడింది');
    expect(getTranslation('events.categories.holiday', 'te')).toBe('సెలవు దినం');
    expect(getTranslation('leave.status.approved', 'te')).toBe('ఆమోదించబడింది');
    expect(getTranslation('communication.title', 'te')).toBe('సమాచార ప్రసార నియంత్రణ కేంద్రం');
  });

  it('3. checks recursive 100% translation key parity between English and Telugu', () => {
    const flattenKeys = (obj: any, prefix = ''): string[] => {
      let keys: string[] = [];
      for (const key in obj) {
        if (typeof obj[key] === 'object' && obj[key] !== null) {
          keys = keys.concat(flattenKeys(obj[key], prefix ? `${prefix}.${key}` : key));
        } else {
          keys.push(prefix ? `${prefix}.${key}` : key);
        }
      }
      return keys;
    };

    const enKeys = flattenKeys(translationResources.en);
    const teKeys = flattenKeys(translationResources.te);

    const missingInTe = enKeys.filter((k) => !teKeys.includes(k));
    const extraInTe = teKeys.filter((k) => !enKeys.includes(k));

    expect(missingInTe).toEqual([]);
    expect(extraInTe).toEqual([]);
    expect(enKeys.length).toBeGreaterThan(70);
  });

  it('4. interpolates single and double curly variables safely', () => {
    const resultSingle = getTranslation('common.pagination.showing', 'en', { start: 1, end: 10, total: 100 });
    expect(resultSingle).toContain('1 to 10 of 100');

    const resultTe = getTranslation('common.pagination.showing', 'te', { start: 1, end: 10, total: 100 });
    expect(resultTe).toContain('100');
  });

  it('5. formats currency values accurately for INR', () => {
    const enCurr = formatCurrency(2500, 'en');
    expect(enCurr).toContain('2,500');

    const teCurr = formatCurrency(2500, 'te');
    expect(teCurr).toContain('2,500');
  });

  it('6. formats date values accurately', () => {
    const formattedDate = formatDate('2026-08-25', 'en');
    expect(formattedDate).toContain('2026');
  });

  it('7. formats numbers accurately', () => {
    const formattedNum = formatNumber(12500, 'en');
    expect(formattedNum).toBe('12,500');
  });

  it('8. renders LanguageSelector component and changes language', () => {
    render(<LanguageSelector />);
    const select = screen.getByRole('combobox', { name: /select application language/i });
    expect(select).toBeInTheDocument();

    fireEvent.change(select, { target: { value: 'te' } });
    expect(useLanguageStore.getState().language).toBe('te');
  });
});
