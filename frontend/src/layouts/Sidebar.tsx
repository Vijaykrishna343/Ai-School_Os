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
      <div key={group.title} className="space-y-0">
        {!collapsed && (
          <h3 className="px-3 text-[9px] font-mono uppercase tracking-widest text-ink-muted/60 dark:text-stone-600 mt-5 mb-1 select-none">
            {group.title}
          </h3>
        )}
        <div className="space-y-px">
          {filteredItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              title={collapsed ? item.name : undefined}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 text-xs font-medium transition-colors border-l-2',
                  isActive
                    ? 'bg-paper text-brand-500 dark:bg-stone-800 dark:text-brand-300 border-brand-500 font-semibold'
                    : 'border-transparent text-ink-muted hover:bg-paper hover:text-ink dark:text-stone-400 dark:hover:bg-stone-800/60 dark:hover:text-stone-200'
                )
              }
            >
              <span className="shrink-0 text-ink-muted/70">
                {item.icon}
              </span>
              {!collapsed && <span className="truncate tracking-tight">{item.name}</span>}
            </NavLink>
          ))}
        </div>
      </div>
    );
  };

  return (
    <aside
      className={clsx(
        'hidden md:flex flex-col border-r border-divider bg-paper-dim dark:border-stone-800 dark:bg-stone-900 transition-all duration-300 select-none shrink-0',
        collapsed ? 'w-[52px]' : 'w-60'
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-14 px-3 border-b border-divider dark:border-stone-800">
        <div className="flex items-center gap-2.5 overflow-hidden min-w-0">
          <div className="flex items-center justify-center w-7 h-7 rounded-none bg-brand-500 text-white shrink-0">
            <Building2 className="w-4 h-4" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate min-w-0">
              <span className="font-serif font-bold text-[11px] tracking-tight text-brand-500 dark:text-stone-100 leading-none">
                AI School OS
              </span>
              <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/50 leading-none mt-0.5">
                Academic OS · v1.0
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="p-1 text-ink-muted/50 hover:text-ink-muted dark:hover:text-stone-200 shrink-0"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-1 py-3 overflow-y-auto">
        {navGroups.map(renderGroup)}
      </nav>

      {/* Footer info */}
      {!collapsed && (
        <div className="px-3 py-3 border-t border-divider dark:border-stone-800">
          <p className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/40 leading-none">
            Vijaykrishna343 · Academic OS
          </p>
        </div>
      )}
    </aside>
  );
};
