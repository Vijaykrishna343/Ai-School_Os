import React from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import { ForbiddenPage } from '@/pages/ForbiddenPage';

export interface PermissionRouteProps {
  permission: string;
  children: React.ReactNode;
}

export const PermissionRoute = ({ permission, children }: PermissionRouteProps) => {
  const { permissions } = useAuthStore();

  const hasPermission = permissions.includes(permission);

  if (!hasPermission) {
    return <ForbiddenPage requiredPermission={permission} />;
  }

  return <>{children}</>;
};
