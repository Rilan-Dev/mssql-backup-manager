import { Database } from 'lucide-react';
import { cn } from '../../lib/utils';

export function Spinner({ className, size = 'md' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className={cn("flex items-center justify-center", className)}>
      <div className={cn("relative", sizeClasses[size])}>
        <div className={cn(
          "absolute inset-0 rounded-full border-2 border-muted-foreground/20",
        )} />
        <div className={cn(
          "absolute inset-0 rounded-full border-2 border-transparent border-t-primary animate-spin",
        )} />
      </div>
    </div>
  );
}

export function PageLoader({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4 animate-fade-in">
      <div className="relative">
        <Database className="h-10 w-10 text-primary animate-pulse" />
      </div>
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
