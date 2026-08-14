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
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />

      {/* Drawer */}
      <div className="relative flex-1 max-w-xs w-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col z-10 animate-in slide-in-from-left duration-200">
        <div className="flex items-center justify-between h-16 px-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-brand-600 text-white font-bold shadow-md shadow-brand-500/20">
              <Building2 className="w-5 h-5" />
            </div>
            <span className="font-bold text-sm tracking-tight text-slate-900 dark:text-slate-100">
              AI SCHOOL OS
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            aria-label="Close mobile menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {filteredNav.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300 font-semibold'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-200'
                )
              }
            >
              <span>{item.icon}</span>
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
};
