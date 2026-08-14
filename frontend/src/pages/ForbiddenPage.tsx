import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';

export const ForbiddenPage = ({
  requiredPermission,
  requiredRole,
}: {
  requiredPermission?: string;
  requiredRole?: string;
}) => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-white dark:bg-slate-900 rounded-3xl border border-red-100 dark:border-red-950/60 shadow-sm min-h-[400px]">
      <div className="p-4 bg-red-50 dark:bg-red-950/50 rounded-3xl mb-4 text-red-600 dark:text-red-400">
        <ShieldAlert className="w-12 h-12" />
      </div>
      <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">403 — Access Forbidden</h2>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-md">
        You do not have the required permissions to access this area.
      </p>
      {(requiredPermission || requiredRole) && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-950/40 rounded-xl text-xs font-mono text-red-700 dark:text-red-300">
          {requiredPermission && `Required Permission: ${requiredPermission}`}
          {requiredRole && `Required Role: ${requiredRole}`}
        </div>
      )}
      <Button
        onClick={() => navigate('/app/dashboard')}
        variant="secondary"
        size="md"
        className="mt-6"
        leftIcon={<ArrowLeft className="w-4 h-4" />}
      >
        Back to Dashboard
      </Button>
    </div>
  );
};
