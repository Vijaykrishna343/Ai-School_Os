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
    <header className="h-12 px-4 md:px-5 border-b border-divider bg-paper dark:border-stone-800 dark:bg-stone-950 flex items-center justify-between shrink-0 select-none">
      {/* Left: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onOpenMobileNav}
          className="md:hidden p-1 text-ink-muted hover:text-ink dark:hover:text-stone-200"
          aria-label="Open mobile menu"
        >
          <Menu className="w-4 h-4" />
        </button>
        {/* Structural left border rule on desktop */}
        <h1 className="text-sm font-serif font-semibold text-brand-500 dark:text-stone-100 tracking-tight truncate">
          {getPageTitle()}
        </h1>
      </div>

      {/* Right: Tenant Indicator, Theme Toggle & User Menu */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Tenant School Indicator */}
        {user?.school_id && (
          <div className="hidden lg:flex items-center gap-1.5 px-2 py-1 border border-divider dark:border-stone-700 text-ink-muted dark:text-stone-400">
            <Building className="w-3 h-3 text-brand-500/60" />
            <span className="font-mono text-[10px] tracking-wider uppercase truncate max-w-[120px]">
              {user.school_id.slice(0, 8)}
            </span>
          </div>
        )}

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-1.5 text-ink-muted hover:text-ink dark:text-stone-400 dark:hover:text-stone-200 transition-colors"
          aria-label="Toggle dark mode"
        >
          {theme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
        </button>

        {/* User Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 py-1 px-1.5 hover:bg-paper-dim dark:hover:bg-stone-800 transition-colors focus:outline-none border border-transparent hover:border-divider"
          >
            <div className="w-6 h-6 bg-brand-500 text-white flex items-center justify-center font-bold text-[10px]">
              {user?.first_name ? user.first_name[0].toUpperCase() : 'U'}
            </div>
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-[11px] font-semibold text-ink dark:text-stone-100 leading-none">
                {user?.first_name} {user?.last_name || ''}
              </span>
              <span className="text-[9px] font-mono text-ink-muted dark:text-stone-400 truncate max-w-[100px] leading-none mt-0.5">
                {user?.email}
              </span>
            </div>
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-1 w-52 bg-paper dark:bg-stone-900 border border-divider dark:border-stone-700 py-1 z-50 shadow-[0_2px_8px_rgba(0,0,0,0.08)]">
              <div className="px-3 py-2 border-b border-divider dark:border-stone-800">
                <p className="text-[11px] font-semibold text-ink dark:text-stone-100 leading-none">
                  {user?.first_name} {user?.last_name || ''}
                </p>
                <p className="text-[10px] font-mono text-ink-muted dark:text-stone-400 truncate mt-0.5">{user?.email}</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => { setDropdownOpen(false); }}
                  className="w-full text-left px-3 py-1.5 text-[11px] text-ink dark:text-stone-300 hover:bg-paper-dim dark:hover:bg-stone-800 flex items-center gap-2"
                >
                  <UserIcon className="w-3.5 h-3.5 text-ink-muted" /> User Profile
                </button>
                <button
                  onClick={() => { setDropdownOpen(false); logout(); }}
                  className="w-full text-left px-3 py-1.5 text-[11px] text-red-700 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center gap-2 font-medium"
                >
                  <LogOut className="w-3.5 h-3.5 text-red-500" /> Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
