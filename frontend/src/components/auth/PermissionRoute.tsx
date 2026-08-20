import React from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import { ForbiddenPage } from '@/pages/ForbiddenPage';

export interface PermissionRouteProps {
  permission: string;
  children: React.ReactNode;
}

export const PermissionRoute = ({ permission, children }: PermissionRouteProps) => {
  const { user, permissions, roles } = useAuthStore();

  const isSuperAdmin = user?.is_super_admin || roles?.some((r: any) => r.name === 'Super Admin' || r.name === 'SUPER_ADMIN');
  const hasPermission =
    isSuperAdmin ||
    permissions.includes('*') ||
    permissions.includes(permission) ||
    (permission.includes('.') && permissions.includes(`${permission.split('.')[0]}.*`));


  if (!hasPermission) {
    return <ForbiddenPage requiredPermission={permission} />;
  }

  return <>{children}</>;
};

