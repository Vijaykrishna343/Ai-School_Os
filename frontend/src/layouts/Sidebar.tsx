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
  ShieldCheck,
  UserCog,
  Upload,
  Bell,
  Shield,
  FileText,
  Bus,
  UserPlus,
  Package,
  BarChart3,
  Presentation,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useAuthStore } from '@/store/useAuthStore';
import { useLanguageStore } from '@/store/useLanguageStore';

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
    title: 'Platform',
    items: [
      { name: 'Platform Admin', path: '/app/platform', icon: <ShieldCheck className="w-4 h-4" /> },
      { name: 'School Directory', path: '/app/schools', icon: <Building2 className="w-4 h-4" /> },
    ],
  },
  {
    title: 'Overview',
    items: [
      { name: 'Dashboard', path: '/app/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
      { name: 'Teacher Cockpit', path: '/app/teacher-cockpit', icon: <Presentation className="w-4 h-4" />, permission: 'teacher_cockpit.view' },
      { name: 'Executive BI & Reports', path: '/app/reports', icon: <BarChart3 className="w-4 h-4" />, permission: 'reports.view' },
    ],
  },
  {
    title: 'Academic Architecture',
    items: [
      { name: 'Academics', path: '/app/academics', icon: <BookOpen className="w-4 h-4" />, permission: 'academic_year.view' },
      { name: 'Progression', path: '/app/progression', icon: <TrendingUp className="w-4 h-4" />, permission: 'progression_matrix.view' },
    ],
  },
  {
    title: 'Registrar',
    items: [
      { name: 'Admissions Pipeline', path: '/app/admissions', icon: <UserPlus className="w-4 h-4" />, permission: 'admissions.view' },
      { name: 'Student Registry', path: '/app/students', icon: <GraduationCap className="w-4 h-4" />, permission: 'student.view' },
      { name: 'Faculty Directory', path: '/app/teachers', icon: <UserCheck className="w-4 h-4" />, permission: 'teacher.view' },
      { name: 'Guardian Directory', path: '/app/parents', icon: <Users className="w-4 h-4" />, permission: 'parent.view' },
      { name: 'Bulk Data Import', path: '/app/import', icon: <Upload className="w-4 h-4" />, permission: 'student.create' },
    ],
  },
  {
    title: 'Operations',
    items: [
      { name: 'Attendance', path: '/app/attendance', icon: <CalendarCheck className="w-4 h-4" />, permission: 'attendance.view' },
      { name: 'Reception Desk', path: '/app/reception', icon: <UserCheck className="w-4 h-4" />, permission: 'visitors.view' },
      { name: 'Staff Leave', path: '/app/staff-leave', icon: <UserCheck className="w-4 h-4" />, permission: 'staff_leave.view' },
      { name: 'Events & Calendar', path: '/app/events', icon: <CalendarCheck className="w-4 h-4" />, permission: 'events.view' },
      { name: 'Hostel Management', path: '/app/hostel', icon: <Building2 className="w-4 h-4" />, permission: 'hostel.view' },
      { name: 'Transport Fleet', path: '/app/transport', icon: <Bus className="w-4 h-4" />, permission: 'transport.view' },
      { name: 'Library & Books', path: '/app/library', icon: <BookOpen className="w-4 h-4" />, permission: 'library.view' },
      { name: 'Inventory & Assets', path: '/app/inventory', icon: <Package className="w-4 h-4" />, permission: 'inventory.view' },
      { name: 'Homework', path: '/app/homework', icon: <BookOpen className="w-4 h-4" />, permission: 'homework.view' },
      { name: 'Document Vault', path: '/app/documents', icon: <FileText className="w-4 h-4" />, permission: 'documents.view' },
      { name: 'Fees & Payments', path: '/app/fees', icon: <CreditCard className="w-4 h-4" />, permission: 'fees.view' },
      { name: 'Exams & Reports', path: '/app/exams', icon: <FileSpreadsheet className="w-4 h-4" />, permission: 'exam.view' },
      { name: 'Timetable', path: '/app/timetable', icon: <Clock className="w-4 h-4" />, permission: 'timetable.view' },
      { name: 'Communications', path: '/app/notifications', icon: <Bell className="w-4 h-4" />, permission: 'school.view' },
    ],
  },
  {
    title: 'System Administration',
    items: [
      { name: 'People & Access', path: '/app/people', icon: <Users className="w-4 h-4" />, permission: 'user.view' },
      { name: 'User Management', path: '/app/users', icon: <UserCog className="w-4 h-4" />, permission: 'user.view' },
      { name: 'Roles & Access', path: '/app/roles', icon: <ShieldCheck className="w-4 h-4" />, permission: 'role.view' },
      { name: 'Audit Trail', path: '/app/audit-logs', icon: <Shield className="w-4 h-4" />, permission: 'school.view' },
      { name: 'School Profile', path: '/app/settings', icon: <Building2 className="w-4 h-4" />, permission: 'school.view' },
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
  const { user, permissions, roles } = useAuthStore();
  const { t } = useLanguageStore();
  const isSuperAdmin = user?.is_super_admin || roles?.some((r: any) => r.name === 'Super Admin' || r.name === 'SUPER_ADMIN');


  const renderGroup = (group: NavGroup) => {
    const filteredItems = group.items.filter((item) => {
      if (!item.permission) return true;
      if (item.permission === 'platform.view') return isSuperAdmin;
      if (isSuperAdmin) return true;
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
          {filteredItems.map((item) => {
            const keyMap: Record<string, string> = {
              '/app/dashboard': 'navigation.menu.dashboard',
              '/app/students': 'navigation.menu.students',
              '/app/teachers': 'navigation.menu.teachers',
              '/app/academics': 'navigation.menu.academics',
              '/app/progression': 'navigation.menu.progression',
              '/app/attendance': 'navigation.menu.attendance',
              '/app/staff-leave': 'navigation.menu.staff_leave',
              '/app/events': 'navigation.menu.events',
              '/app/hostel': 'navigation.menu.hostel',
              '/app/homework': 'navigation.menu.homework',
              '/app/documents': 'navigation.menu.documents',
              '/app/fees': 'navigation.menu.fees',
              '/app/exams': 'navigation.menu.exams',
              '/app/timetable': 'navigation.menu.timetable',
              '/app/notifications': 'navigation.menu.communication',
              '/app/people': 'navigation.menu.roles',
              '/app/audit-logs': 'navigation.menu.audit_log',
              '/app/settings': 'navigation.menu.settings',
            };
            const localizedName = keyMap[item.path] ? t(keyMap[item.path]) : item.name;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                title={collapsed ? localizedName : undefined}
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
                {!collapsed && <span className="truncate tracking-tight">{localizedName}</span>}
              </NavLink>
            );
          })}
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
