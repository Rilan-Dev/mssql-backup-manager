import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Sun, Moon, LogOut, Server } from 'lucide-react';

const pageTitles = {
  '/dashboard': 'Dashboard',
  '/connections': 'Connections',
  '/backups': 'Backups',
  '/query': 'Query Tool',
  '/settings': 'Settings',
};

export default function Navbar() {
  const { connection, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Determine page title
  let pageTitle = pageTitles[location.pathname] || '';
  if (location.pathname.startsWith('/database/')) {
    const dbName = decodeURIComponent(location.pathname.split('/database/')[1]);
    pageTitle = `Database: ${dbName}`;
  }

  return (
    <header className="sticky top-0 z-20 h-16 border-b bg-card/80 backdrop-blur-xl flex items-center justify-between px-6">
      {/* Left: Page Title */}
      <div>
        <h1 className="text-lg font-semibold">{pageTitle}</h1>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Server info */}
        {connection && (
          <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full">
            <Server className="h-3.5 w-3.5" />
            <span className="font-medium text-foreground">{connection.host}:{connection.port}</span>
            <span>•</span>
            <span>{connection.user}</span>
          </div>
        )}

        {/* Theme toggle */}
        <Button variant="ghost" size="icon" onClick={toggleTheme} className="h-9 w-9">
          {theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>

        {/* Disconnect */}
        <Button variant="outline" size="sm" onClick={handleLogout} className="gap-2">
          <LogOut className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Disconnect</span>
        </Button>
      </div>
    </header>
  );
}
