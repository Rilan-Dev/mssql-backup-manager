import { cn } from '../lib/utils';

export default function StatCard({ icon: Icon, label, value, sub, gradient, className }) {
  return (
    <div className={cn(
      "relative overflow-hidden rounded-xl border bg-card p-5 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5 group",
      className
    )}>
      {/* Gradient accent */}
      {gradient && (
        <div className={cn("absolute top-0 left-0 right-0 h-0.5", gradient)} />
      )}
      
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
        </div>
        {Icon && (
          <div className="h-10 w-10 rounded-lg bg-muted/50 flex items-center justify-center group-hover:bg-primary/10 transition-colors">
            <Icon className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
        )}
      </div>
    </div>
  );
}
