import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Database,
  Link2,
  HardDrive,
  Terminal,
  Settings,
  ChevronLeft,
  ChevronRight,
  Server,
  Zap,
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/connections', label: 'Connections', icon: Link2 },
  { path: '/backups', label: 'Backups', icon: HardDrive },
  { path: '/query', label: 'Query Tool', icon: Terminal },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ collapsed, onToggle }) {
  const { connection } = useAuth();
  const location = useLocation();

  return (
    <aside className={cn(
      "fixed top-0 left-0 h-full z-30 flex flex-col border-r bg-card/80 backdrop-blur-xl transition-all duration-300",
      collapsed ? "w-[72px]" : "w-[260px]"
    )}>
      {/* Logo */}
      <div className={cn(
        "flex items-center h-16 px-4 border-b gap-3",
        collapsed && "justify-center"
      )}>
        <div className="flex items-center justify-center h-9 w-9 rounded-lg gradient-primary flex-shrink-0">
          <Database className="h-5 w-5 text-white" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <h1 className="font-bold text-sm leading-tight">MSSQL Backup</h1>
            <p className="text-[10px] text-muted-foreground font-medium">Manager v2.0</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || 
            (item.path === '/dashboard' && location.pathname.startsWith('/database/'));

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group relative",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
                collapsed && "justify-center px-0"
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 rounded-r-full gradient-primary" />
              )}
              <Icon className={cn("h-4.5 w-4.5 flex-shrink-0", isActive && "text-primary")} />
              {!collapsed && (
                <span className="animate-fade-in truncate">{item.label}</span>
              )}
              {/* Tooltip for collapsed */}
              {collapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded-md shadow-lg border opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                  {item.label}
                </div>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Connection Status */}
      {connection && !collapsed && (
        <div className="px-3 py-3 border-t animate-fade-in">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 text-xs">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse flex-shrink-0" />
            <div className="min-w-0">
              <p className="font-medium text-foreground truncate">{connection.host}</p>
              <p className="text-muted-foreground truncate">{connection.user}:{connection.port}</p>
            </div>
          </div>
        </div>
      )}

      {connection && collapsed && (
        <div className="px-3 py-3 border-t flex justify-center">
          <div className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" title={`${connection.host} (${connection.user})`} />
        </div>
      )}

      {/* Collapse Toggle */}
      <div className="px-3 py-3 border-t">
        <button
          onClick={onToggle}
          className={cn(
            "flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors",
            collapsed && "justify-center"
          )}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span className="animate-fade-in">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
