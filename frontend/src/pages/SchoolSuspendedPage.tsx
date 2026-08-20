import { AlertTriangle, Mail } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/store/useAuthStore';

export const SchoolSuspendedPage = () => {
  const { logout } = useAuthStore();

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6 text-center">
      <div className="max-w-md w-full bg-slate-800 border border-slate-700/80 rounded-3xl p-8 shadow-2xl">
        <div className="w-16 h-16 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-center justify-center mx-auto mb-6 text-amber-400">
          <AlertTriangle className="w-8 h-8" />
        </div>

        <h1 className="text-2xl font-bold text-white mb-2">School Access Suspended</h1>
        <p className="text-sm text-slate-400 mb-6 leading-relaxed">
          Your school&apos;s AI School OS account access is currently suspended or inactive. Please contact your school administrator or platform support to restore access.
        </p>

        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-4 text-xs text-slate-300 mb-6 font-mono text-left space-y-1">
          <div><span className="text-slate-500">Status:</span> <span className="text-amber-400 font-semibold">SUSPENDED</span></div>
          <div><span className="text-slate-500">Support Email:</span> support@aischoolos.com</div>
        </div>

        <div className="flex flex-col gap-3">
          <Button
            onClick={() => window.location.href = "mailto:support@aischoolos.com"}
            variant="primary"
            className="w-full justify-center"
            leftIcon={<Mail className="w-4 h-4" />}
          >
            Contact Platform Support
          </Button>

          <Button
            onClick={() => logout()}
            variant="outline"
            className="w-full justify-center text-slate-400 border-slate-700 hover:text-white"
          >
            Sign Out
          </Button>
        </div>
      </div>
    </div>
  );
};
