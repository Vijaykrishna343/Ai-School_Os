import React from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import { ForbiddenPage } from '@/pages/ForbiddenPage';

export interface RoleRouteProps {
  roleCode: string;
  children: React.ReactNode;
}

export const RoleRoute = ({ roleCode, children }: RoleRouteProps) => {
  const { roles } = useAuthStore();

  const hasRole = roles.some((r) => r.code === roleCode || r.name.toLowerCase() === roleCode.toLowerCase());

  if (!hasRole) {
    return <ForbiddenPage requiredRole={roleCode} />;
  }

  return <>{children}</>;
};
