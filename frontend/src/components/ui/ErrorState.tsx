import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState = ({
  title = 'Something went wrong',
  message = 'An unexpected error occurred while processing your request.',
  onRetry,
}: ErrorStateProps) => (
  <div className="flex flex-col items-center justify-center p-8 text-center bg-red-50/50 dark:bg-red-950/20 rounded-2xl border border-red-100 dark:border-red-900/50">
    <div className="p-3 bg-red-100 dark:bg-red-900/50 rounded-2xl mb-4 text-red-600 dark:text-red-400">
      <AlertTriangle className="w-8 h-8" />
    </div>
    <h3 className="text-base font-semibold text-red-900 dark:text-red-200">{title}</h3>
    <p className="mt-1 text-sm text-red-600 dark:text-red-300 max-w-md">{message}</p>
    {onRetry && (
      <Button
        onClick={onRetry}
        variant="outline"
        size="sm"
        className="mt-4 border-red-300 text-red-700 hover:bg-red-100/50 dark:border-red-800 dark:text-red-200"
        leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
      >
        Try Again
      </Button>
    )}
  </div>
);
