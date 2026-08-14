import { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Sun,
  Moon,
  LogOut,
  User as UserIcon,
  Building,
  Menu,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { useThemeStore } from '@/store/useThemeStore';

export const TopHeader = ({ onOpenMobileNav }: { onOpenMobileNav: () => void }) => {
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const location = useLocation();

  const getPageTitle = () => {
    const path = location.pathname;
    if (path.includes('/dashboard')) return 'Administrative Command Center';
    if (path.includes('/students')) return 'Student Registry';
    if (path.includes('/teachers')) return 'Faculty Directory';
    if (path.includes('/parents')) return 'Guardian Directory';
    if (path.includes('/academics')) return 'Academic Architecture';
    if (path.includes('/progression')) return 'Academic Progression & Rollover';
    if (path.includes('/attendance')) return 'Daily Attendance Registry';
    if (path.includes('/fees')) return 'Financial Operations';
    if (path.includes('/exams')) return 'Examinations & Reports';
    if (path.includes('/timetable')) return 'Timetable Operations';
    return 'AI School OS';
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-16 px-4 md:px-6 border-b border-slate-200 bg-[#fcf9f8] dark:border-slate-800 dark:bg-slate-900 flex items-center justify-between shrink-0 select-none">
      {/* Left: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileNav}
          className="md:hidden p-2 rounded-sm text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
          aria-label="Open mobile menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="text-lg font-bold font-serif text-slate-900 dark:text-slate-100 tracking-tight">
          {getPageTitle()}
        </h1>
      </div>

      {/* Right: Tenant Indicator, Theme Toggle & User Menu */}
      <div className="flex items-center gap-3">
        {/* Tenant School Indicator */}
        {user?.school_id && (
          <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-sm border border-slate-200 text-slate-700 text-xs font-mono dark:bg-slate-800 dark:text-slate-300">
            <Building className="w-3.5 h-3.5 text-brand-500 dark:text-brand-400" />
            <span className="truncate max-w-[150px]">SCHOOL_ID: {user.school_id.slice(0, 8)}</span>
          </div>
        )}

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 transition-colors"
          aria-label="Toggle dark mode"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {/* User Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 p-1.5 rounded-sm hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus:outline-none"
          >
            <div className="w-8 h-8 rounded-sm bg-brand-500 text-white flex items-center justify-center font-bold text-xs shadow-sm">
              {user?.first_name ? user.first_name[0].toUpperCase() : 'U'}
            </div>
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                {user?.first_name} {user?.last_name || ''}
              </span>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-[120px]">
                {user?.email}
              </span>
            </div>
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-900 rounded-sm shadow-sm border border-slate-200 dark:border-slate-800 py-1.5 z-50 animate-in fade-in slide-in-from-top-2">
              <div className="px-4 py-2 border-b border-slate-100 dark:border-slate-800">
                <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {user?.first_name} {user?.last_name || ''}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user?.email}</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => {
                    setDropdownOpen(false);
                  }}
                  className="w-full text-left px-4 py-2 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2"
                >
                  <UserIcon className="w-4 h-4 text-slate-400" /> User Profile
                </button>
                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    logout();
                  }}
                  className="w-full text-left px-4 py-2 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center gap-2 font-medium"
                >
                  <LogOut className="w-4 h-4 text-red-500" /> Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
