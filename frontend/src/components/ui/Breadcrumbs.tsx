import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items }) => {
  return (
    <nav className="flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500 mb-2">
      <Link to="/app/dashboard" className="flex items-center gap-1 hover:text-slate-700 dark:hover:text-slate-300 transition-colors">
        <Home className="w-3.5 h-3.5" />
        <span>Home</span>
      </Link>
      {items.map((item, idx) => (
        <React.Fragment key={idx}>
          <ChevronRight className="w-3 h-3 text-slate-300 dark:text-slate-600 shrink-0" />
          {item.href ? (
            <Link to={item.href} className="hover:text-slate-700 dark:hover:text-slate-300 transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className="font-semibold text-slate-700 dark:text-slate-200">{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};
