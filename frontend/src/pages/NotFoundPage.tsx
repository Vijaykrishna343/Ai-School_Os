import { FileQuestion, Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';

export const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm min-h-[400px]">
      <div className="p-4 bg-slate-100 dark:bg-slate-800 rounded-3xl mb-4 text-slate-500 dark:text-slate-400">
        <FileQuestion className="w-12 h-12" />
      </div>
      <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">404 — Page Not Found</h2>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-md">
        The route you are looking for does not exist or has been moved.
      </p>
      <Button
        onClick={() => navigate('/app/dashboard')}
        variant="primary"
        size="md"
        className="mt-6"
        leftIcon={<Home className="w-4 h-4" />}
      >
        Go to Dashboard
      </Button>
    </div>
  );
};
