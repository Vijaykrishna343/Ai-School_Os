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
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useAuthStore } from '@/store/useAuthStore';

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
  permission?: string;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    title: 'Overview',
    items: [
      { name: 'Dashboard', path: '/app/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    ],
  },
  {
    title: 'Academic Architecture',
    items: [
      { name: 'Academics', path: '/app/academics', icon: <BookOpen className="w-4 h-4" />, permission: 'academic_year.view' },
      { name: 'Progression', path: '/app/progression', icon: <TrendingUp className="w-4 h-4" />, permission: 'progression.view' },
    ],
  },
  {
    title: 'Registrar',
    items: [
      { name: 'Student Registry', path: '/app/students', icon: <GraduationCap className="w-4 h-4" />, permission: 'student.view' },
      { name: 'Faculty Directory', path: '/app/teachers', icon: <UserCheck className="w-4 h-4" />, permission: 'teacher.view' },
      { name: 'Guardian Directory', path: '/app/parents', icon: <Users className="w-4 h-4" />, permission: 'parent.view' },
    ],
  },
  {
    title: 'Operations',
    items: [
      { name: 'Attendance', path: '/app/attendance', icon: <CalendarCheck className="w-4 h-4" />, permission: 'attendance.view' },
      { name: 'Fees & Payments', path: '/app/fees', icon: <CreditCard className="w-4 h-4" />, permission: 'fee.view' },
      { name: 'Exams & Reports', path: '/app/exams', icon: <FileSpreadsheet className="w-4 h-4" />, permission: 'exam.view' },
      { name: 'Timetable', path: '/app/timetable', icon: <Clock className="w-4 h-4" />, permission: 'timetable.view' },
    ],
  },
];

export const Sidebar = ({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) => {
  const { permissions } = useAuthStore();

  const renderGroup = (group: NavGroup) => {
    const filteredItems = group.items.filter((item) => {
      if (!item.permission) return true;
      return permissions.includes(item.permission);
    });

    if (filteredItems.length === 0) return null;

    return (
      <div key={group.title} className="space-y-1">
        {!collapsed && (
          <h3 className="px-3 text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-slate-500 mt-4 mb-2">
            {group.title}
          </h3>
        )}
        <div className="space-y-0.5">
          {filteredItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-sm text-xs font-medium transition-all group border-l-2',
                  isActive
                    ? 'bg-slate-100 dark:bg-slate-800 text-brand-500 dark:text-brand-400 border-brand-500 font-semibold'
                    : 'border-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-200'
                )
              }
            >
              <span className="shrink-0 text-slate-500 group-hover:text-slate-900 dark:group-hover:text-slate-200">
                {item.icon}
              </span>
              {!collapsed && <span className="truncate">{item.name}</span>}
            </NavLink>
          ))}
        </div>
      </div>
    );
  };

  return (
    <aside
      className={clsx(
        'hidden md:flex flex-col border-r border-slate-200 bg-[#fcf9f8] dark:border-slate-800 dark:bg-slate-900 transition-all duration-300 select-none shrink-0',
        collapsed ? 'w-20' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex items-center justify-center w-8 h-8 rounded-sm bg-brand-500 text-white shrink-0">
            <Building2 className="w-5 h-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="font-bold text-xs tracking-tight text-slate-900 dark:text-slate-100">
                AI SCHOOL OS
              </span>
              <span className="text-[9px] uppercase font-bold text-slate-400 tracking-wider">
                Academic OS
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="p-1 rounded-sm text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-2 py-4 space-y-4 overflow-y-auto">
        {navGroups.map(renderGroup)}
      </nav>

      {/* Footer info */}
      {!collapsed && (
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 text-[10px] text-slate-400 text-center font-mono">
          SYSTEM_VER_1.0.0
        </div>
      )}
    </aside>
  );
};
