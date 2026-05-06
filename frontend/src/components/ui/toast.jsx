import { useToast } from '../../context/ToastContext';
import { X, CheckCircle2, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { useEffect, useState } from 'react';

const iconMap = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

const colorMap = {
  success: 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400',
  error: 'border-rose-500/50 bg-rose-500/10 text-rose-400',
  info: 'border-blue-500/50 bg-blue-500/10 text-blue-400',
  warning: 'border-amber-500/50 bg-amber-500/10 text-amber-400',
};

const progressMap = {
  success: 'bg-emerald-500',
  error: 'bg-rose-500',
  info: 'bg-blue-500',
  warning: 'bg-amber-500',
};

function ToastItem({ toast: t, onRemove }) {
  const [progress, setProgress] = useState(100);
  const Icon = iconMap[t.type] || Info;

  useEffect(() => {
    if (t.duration <= 0) return;
    const interval = 50;
    const step = (interval / t.duration) * 100;
    const timer = setInterval(() => {
      setProgress(prev => {
        const next = prev - step;
        if (next <= 0) {
          clearInterval(timer);
          return 0;
        }
        return next;
      });
    }, interval);
    return () => clearInterval(timer);
  }, [t.duration]);

  return (
    <div className={`relative overflow-hidden rounded-lg border ${colorMap[t.type]} p-4 pr-10 shadow-lg animate-slide-in-right min-w-[320px] max-w-[420px]`}>
      <button
        onClick={() => onRemove(t.id)}
        className="absolute top-3 right-3 text-muted-foreground hover:text-foreground transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
      <div className="flex items-start gap-3">
        <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          {t.title && <p className="font-semibold text-sm">{t.title}</p>}
          {t.message && <p className="text-sm opacity-90 mt-0.5">{t.message}</p>}
        </div>
      </div>
      {t.duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-black/10">
          <div
            className={`h-full ${progressMap[t.type]} transition-all duration-100 ease-linear`}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}

export function ToastContainer() {
  const { toasts, removeToast } = useToast();

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map(t => (
        <ToastItem key={t.id} toast={t} onRemove={removeToast} />
      ))}
    </div>
  );
}
