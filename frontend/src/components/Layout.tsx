import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { LayoutDashboard, CheckCircle, Database, FileText, BarChart3, ShieldCheck, LogOut, Settings, User } from 'lucide-react';

export const Layout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Verify', path: '/verify', icon: CheckCircle },
    { name: 'Assets', path: '/assets', icon: Database },
    { name: 'Verifications', path: '/verifications', icon: ShieldCheck },
    { name: 'Blockchain', path: '/blockchain', icon: Database },
    { name: 'Reports', path: '/reports', icon: FileText },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Audit Logs', path: '/audit-logs', icon: FileText },
  ];

  return (
    <div className="flex min-h-screen text-slate-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 glass-panel border-r border-glass-border m-4 p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-3 px-2 mb-8">
            <ShieldCheck className="w-8 h-8 text-blue-400" />
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              TrustLens
            </h1>
          </div>
          
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                    isActive 
                      ? 'bg-blue-500/20 border border-blue-400/30 text-blue-300' 
                      : 'hover:bg-glass-hover text-slate-300 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="mt-8 border-t border-glass-border pt-4 space-y-2">
          <Link
            to="/profile"
            className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-glass-hover text-slate-300 hover:text-white transition-all"
          >
            <User className="w-5 h-5" />
            <span className="font-medium truncate">{user?.email || 'Profile'}</span>
          </Link>
          <Link
            to="/settings"
            className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-glass-hover text-slate-300 hover:text-white transition-all"
          >
            <Settings className="w-5 h-5" />
            <span className="font-medium">Settings</span>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-all text-left"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col p-4 pl-0">
        <header className="glass-panel border-b border-glass-border px-8 py-4 mb-4 flex justify-between items-center rounded-2xl">
          <h2 className="text-lg font-semibold text-slate-200">
            {navItems.find(i => location.pathname.startsWith(i.path))?.name || 'Overview'}
          </h2>
          <div className="flex items-center gap-4">
            <span className="px-3 py-1 bg-slate-800/50 rounded-full text-sm font-medium border border-slate-700">
              {user?.roles?.includes('admin') ? 'Admin' : 'User'}
            </span>
          </div>
        </header>

        <div className="flex-1 overflow-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
