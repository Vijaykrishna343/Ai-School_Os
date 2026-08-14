import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  UserCheck,
  BookOpen,
  TrendingUp,
  CalendarCheck,
  CreditCard,
  FileSpreadsheet,
  Clock,
  Building2,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useAuthStore } from '@/store/useAuthStore';

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
  permission?: string;
}

const navigationItems: NavItem[] = [
  { name: 'Dashboard', path: '/app/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { name: 'Students', path: '/app/students', icon: <GraduationCap className="w-5 h-5" />, permission: 'student.view' },
  { name: 'Teachers', path: '/app/teachers', icon: <UserCheck className="w-5 h-5" />, permission: 'teacher.view' },
  { name: 'Parents', path: '/app/parents', icon: <Users className="w-5 h-5" />, permission: 'parent.view' },
  { name: 'Academics', path: '/app/academics', icon: <BookOpen className="w-5 h-5" />, permission: 'academic_year.view' },
  { name: 'Progression', path: '/app/progression', icon: <TrendingUp className="w-5 h-5" />, permission: 'progression.view' },
  { name: 'Attendance', path: '/app/attendance', icon: <CalendarCheck className="w-5 h-5" />, permission: 'attendance.view' },
  { name: 'Fees & Payments', path: '/app/fees', icon: <CreditCard className="w-5 h-5" />, permission: 'fee.view' },
  { name: 'Exams & Reports', path: '/app/exams', icon: <FileSpreadsheet className="w-5 h-5" />, permission: 'exam.view' },
  { name: 'Timetable', path: '/app/timetable', icon: <Clock className="w-5 h-5" />, permission: 'timetable.view' },
];

export const MobileNav = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => {
  const { permissions } = useAuthStore();

  if (!isOpen) return null;

  const filteredNav = navigationItems.filter((item) => {
    if (!item.permission) return true;
    return permissions.includes(item.permission);
  });

  return (
    <div className="fixed inset-0 z-50 md:hidden flex">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-stone-950/70" onClick={onClose} />

      {/* Drawer */}
      <div className="relative flex-1 max-w-[240px] w-full bg-paper-dim dark:bg-stone-900 border-r border-divider dark:border-stone-800 flex flex-col z-10">
        {/* Brand Header */}
        <div className="flex items-center justify-between h-14 px-3 border-b border-divider dark:border-stone-800">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-7 h-7 bg-brand-500 text-white shrink-0">
              <Building2 className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-serif font-bold text-[11px] tracking-tight text-brand-500 dark:text-stone-100 leading-none">
                AI School OS
              </span>
              <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/50 leading-none mt-0.5">
                Academic OS · v1.0
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-ink-muted/50 hover:text-ink-muted dark:hover:text-stone-200"
            aria-label="Close mobile menu"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <nav className="flex-1 px-1 py-3 overflow-y-auto space-y-px">
          {filteredNav.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 text-xs font-medium transition-colors border-l-2',
                  isActive
                    ? 'bg-paper text-brand-500 dark:bg-stone-800 dark:text-brand-300 border-brand-500 font-semibold'
                    : 'border-transparent text-ink-muted hover:bg-paper hover:text-ink dark:text-stone-400 dark:hover:bg-stone-800/60 dark:hover:text-stone-200'
                )
              }
            >
              <span className="text-ink-muted/70">{item.icon}</span>
              <span className="tracking-tight">{item.name}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-3 py-3 border-t border-divider dark:border-stone-800">
          <p className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/40 leading-none">
            Vijaykrishna343 · Academic OS
          </p>
        </div>
      </div>
    </div>
  );
};
