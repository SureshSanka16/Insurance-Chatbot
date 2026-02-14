import React, { useState, useEffect } from 'react';
import { Dashboard } from './views/Dashboard';
import { Claims } from './views/Claims';
import { Documents } from './views/Documents';
import { FraudDetection } from './views/FraudDetection';
import { Settings } from './views/Settings';
import { Analytics } from './views/Analytics';
import { UserDashboard } from './views/UserDashboard';
import { Copilot } from './components/Copilot';
import { GlobalSearch } from './components/GlobalSearch';
import { VantageLogo } from './components/Branding';
import { NavItem, UserRole } from './types';
import { CURRENT_USER } from './constants';
import {
  LayoutDashboard,
  FileText,
  ShieldAlert,
  Files,
  Settings as SettingsIcon,
  LogOut,
  Menu,
  Moon,
  Sun,
  Bell,
  TrendingUp,
  User,
  Pin,
  PinOff,
  ArrowLeft
}
  from 'lucide-react';
import { cn, Toast, Breadcrumbs, Input, Button } from './components/UIComponents';
import { createPolicy, fetchPolicies } from './src/api/endpoints';
import { AnimatePresence, motion, LayoutGroup } from 'framer-motion';

// Generate a consistent color based on the name string
const getAvatarColor = (name: string): string => {
    const colors = [
        'bg-gradient-to-br from-rose-500 to-pink-600',
        'bg-gradient-to-br from-orange-500 to-amber-600',
        'bg-gradient-to-br from-emerald-500 to-teal-600',
        'bg-gradient-to-br from-blue-500 to-indigo-600',
        'bg-gradient-to-br from-violet-500 to-purple-600',
        'bg-gradient-to-br from-cyan-500 to-sky-600',
        'bg-gradient-to-br from-fuchsia-500 to-pink-600',
        'bg-gradient-to-br from-lime-500 to-green-600',
    ];
    const charSum = name.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
    return colors[charSum % colors.length];
};

const InitialAvatar = ({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' | 'lg' }) => {
    const initial = name?.charAt(0)?.toUpperCase() || '?';
    const bgColor = getAvatarColor(name || 'User');
    const sizeClasses = {
        sm: 'w-8 h-8 text-sm',
        md: 'w-10 h-10 text-base',
        lg: 'w-24 h-24 text-4xl'
    };
    
    return (
        <div className={cn(
            sizeClasses[size],
            bgColor,
            'rounded-full flex items-center justify-center font-bold text-white shadow-md shrink-0 ring-2 ring-white dark:ring-white/10'
        )}>
            <span className="drop-shadow-sm">{initial}</span>
        </div>
    );
};

// --- LOGIN COMPONENT (2-Step Authentication) ---
const LoginScreen = ({ onLogin }: { onLogin: (role: UserRole) => void }) => {
  const [selectedRole, setSelectedRole] = useState<UserRole>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const formData = new FormData(e.target as HTMLFormElement);
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;

    try {
      // Import login function
      const { login } = await import('./src/api/endpoints');
      const user = await login(email, password);

      // Update CURRENT_USER with backend data
      CURRENT_USER.id = user.id;
      CURRENT_USER.name = user.name;
      CURRENT_USER.email = user.email;
      CURRENT_USER.role = user.role;
      CURRENT_USER.avatar = user.avatar;

      // Success - login with selected role
      if (selectedRole) onLogin(selectedRole);
    } catch (err: any) {
      console.error('Login failed:', err);
      setError(err.response?.data?.detail || 'Invalid email or password');
      setIsLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const formData = new FormData(e.target as HTMLFormElement);
    const name = formData.get('name') as string;
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;

    try {
      // Import register function
      const { register } = await import('./src/api/endpoints');
      await register({ name, email, password, role: selectedRole || 'User' });

      // Auto-login after registration
      const { login } = await import('./src/api/endpoints');
      const user = await login(email, password);

      // Update CURRENT_USER with backend data
      CURRENT_USER.id = user.id;
      CURRENT_USER.name = user.name;
      CURRENT_USER.email = user.email;
      CURRENT_USER.role = user.role;
      CURRENT_USER.avatar = user.avatar;

      // Success
      if (selectedRole) onLogin(selectedRole);
    } catch (err: any) {
      let errorMsg = 'Registration failed.';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Handle Pydantic validation errors (array of objects)
          errorMsg = detail.map((e: any) => `${e.loc[1]}: ${e.msg}`).join('\n');
        } else if (typeof detail === 'object') {
          errorMsg = JSON.stringify(detail);
        } else {
          errorMsg = String(detail);
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(`Error:\n${errorMsg}`);
      setIsLoading(false);
    }
  };

  // Step 2: Email & Password Form (Login or Register)
  if (selectedRole) {
    return (
      <div className="h-screen w-full bg-[#F2F4F7] dark:bg-[#020617] text-gray-900 dark:text-white flex items-center justify-center overflow-hidden relative font-sans selection:bg-orange-500/30 transition-colors duration-500">
        {/* Background Effects */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] bg-orange-400/20 dark:bg-orange-500/10 rounded-full blur-[120px] animate-float" />
          <div className="absolute bottom-[-20%] right-[-10%] w-[70%] h-[70%] bg-blue-400/20 dark:bg-blue-600/10 rounded-full blur-[120px] animate-float" style={{ animationDelay: '2s' }} />
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          className="w-full max-w-md p-8 mx-4 rounded-[40px] bg-white/70 dark:bg-white/5 border border-white/60 dark:border-white/10 backdrop-blur-2xl shadow-2xl relative z-10"
        >
          <button
            onClick={() => { setSelectedRole(null); setShowRegister(false); setError(null); }}
            className="absolute top-8 left-8 text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors p-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-full -ml-2"
          >
            <ArrowLeft size={24} />
          </button>

          <div className="text-center mb-10 mt-2">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className={cn("w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl transition-all duration-500",
                selectedRole === 'Admin' ? "bg-orange-500 shadow-orange-500/30" : "bg-blue-600 shadow-blue-600/30"
              )}>
              {selectedRole === 'Admin' ? <ShieldAlert size={40} className="text-white" /> : <User size={40} className="text-white" />}
            </motion.div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              {showRegister ? 'Create Account' : 'Welcome Back'}
            </h2>
            <p className="text-gray-500">
              {showRegister
                ? `Register for ${selectedRole === 'Admin' ? 'Admin Portal' : 'Policy Holder'} access`
                : `Sign in to access the ${selectedRole === 'Admin' ? 'Admin Portal' : 'Policy Holder Dashboard'}`
              }
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-2xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {showRegister ? (
            <form onSubmit={handleRegisterSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Full Name</label>
                <Input
                  name="name"
                  type="text"
                  placeholder="John Doe"
                  className="bg-white dark:bg-black/20 border-gray-200 dark:border-white/10 text-gray-900 dark:text-white h-14"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Email Address</label>
                <Input
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  className="bg-white dark:bg-black/20 border-gray-200 dark:border-white/10 text-gray-900 dark:text-white h-14"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Password</label>
                <Input
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  className="bg-white dark:bg-black/20 border-gray-200 dark:border-white/10 text-gray-900 dark:text-white h-14"
                  required
                  minLength={6}
                />
              </div>
              <Button
                type="submit"
                isLoading={isLoading}
                className={cn("w-full h-14 text-lg font-bold mt-4 border-0 shadow-lg transition-transform active:scale-[0.98]",
                  selectedRole === 'Admin'
                    ? "bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 shadow-orange-500/20"
                    : "bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 shadow-blue-500/20"
                )}
              >
                Create Account
              </Button>
              <div className="text-center mt-4">
                <button
                  type="button"
                  onClick={() => { setShowRegister(false); setError(null); }}
                  className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  Already have an account? <span className="font-bold">Sign In</span>
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleLoginSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Email Address</label>
                <Input
                  name="email"
                  type="email"
                  defaultValue={selectedRole === 'Admin' ? "admin@vantage.ai" : "james@gmail.com"}
                  className="bg-white dark:bg-black/20 border-gray-200 dark:border-white/10 text-gray-900 dark:text-white h-14"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Password</label>
                <Input
                  name="password"
                  type="password"
                  defaultValue="password123"
                  className="bg-white dark:bg-black/20 border-gray-200 dark:border-white/10 text-gray-900 dark:text-white h-14"
                  required
                />
              </div>
              <Button
                type="submit"
                isLoading={isLoading}
                className={cn("w-full h-14 text-lg font-bold mt-4 border-0 shadow-lg transition-transform active:scale-[0.98]",
                  selectedRole === 'Admin'
                    ? "bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 shadow-orange-500/20"
                    : "bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 shadow-blue-500/20"
                )}
              >
                Sign In
              </Button>
              <div className="text-center mt-4">
                <button
                  type="button"
                  onClick={() => { setShowRegister(true); setError(null); }}
                  className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  Don't have an account? <span className="font-bold">Register</span>
                </button>
              </div>
            </form>
          )}
        </motion.div>
      </div>
    );
  }

  // Step 1: Role Selection
  return (
    <div className="h-screen w-full bg-[#F2F4F7] dark:bg-[#020617] text-gray-900 dark:text-white flex items-center justify-center overflow-hidden relative font-sans selection:bg-orange-500/30 transition-colors duration-500">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] bg-orange-400/20 dark:bg-orange-500/10 rounded-full blur-[120px] animate-float" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[70%] h-[70%] bg-blue-400/20 dark:bg-blue-600/10 rounded-full blur-[120px] animate-float" style={{ animationDelay: '2s' }} />
      </div>

      <div className="z-10 w-full max-w-5xl px-8">
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <VantageLogo size={80} className="mx-auto mb-6" />
            <h1 className="text-6xl md:text-7xl font-bold tracking-tighter mb-4 bg-clip-text text-transparent bg-gradient-to-r from-gray-900 via-gray-700 to-gray-500 dark:from-white dark:via-white dark:to-white/50">
              Vantage
            </h1>
            <p className="text-xl text-gray-500 dark:text-gray-400 font-light max-w-2xl mx-auto leading-relaxed">
              The intelligent operating system for modern insurance claims.
            </p>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Admin Card - Orange */}
          <motion.button
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            onClick={() => setSelectedRole('Admin')}
            className="group relative h-[320px] rounded-[40px] p-8 text-left overflow-hidden transition-all duration-500 hover:scale-[1.02] border border-white/60 dark:border-white/5 bg-gradient-to-br from-white/80 to-white/40 dark:from-orange-500/10 dark:to-orange-600/5 shadow-xl shadow-orange-500/10 dark:shadow-none"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-orange-50 to-white opacity-0 group-hover:opacity-100 dark:from-orange-500/20 dark:to-transparent transition-opacity duration-500" />

            <div className="relative z-10 h-full flex flex-col justify-between">
              <div className="w-16 h-16 rounded-2xl bg-orange-500 flex items-center justify-center text-white shadow-lg shadow-orange-500/30 group-hover:scale-110 transition-transform duration-500">
                <ShieldAlert size={32} />
              </div>
              <div>
                <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Admin Portal</h3>
                <p className="text-gray-500 dark:text-orange-200/60 font-medium">Claims adjudication, fraud detection, and analytics.</p>
              </div>
              <div className="w-full h-1 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-orange-500 w-1/3 group-hover:w-full transition-all duration-700 ease-out" />
              </div>
            </div>
          </motion.button>

          {/* User Card - Blue */}
          <motion.button
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            onClick={() => setSelectedRole('User')}
            className="group relative h-[320px] rounded-[40px] p-8 text-left overflow-hidden transition-all duration-500 hover:scale-[1.02] border border-white/60 dark:border-white/5 bg-gradient-to-br from-white/80 to-white/40 dark:from-blue-600/10 dark:to-blue-700/5 shadow-xl shadow-blue-500/10 dark:shadow-none"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-white opacity-0 group-hover:opacity-100 dark:from-blue-600/20 dark:to-transparent transition-opacity duration-500" />

            <div className="relative z-10 h-full flex flex-col justify-between">
              <div className="w-16 h-16 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-600/30 group-hover:scale-110 transition-transform duration-500">
                <User size={32} />
              </div>
              <div>
                <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Policy Holder</h3>
                <p className="text-gray-500 dark:text-blue-200/60 font-medium">Manage policies, file claims, and track status.</p>
              </div>
              <div className="w-full h-1 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-blue-600 w-1/3 group-hover:w-full transition-all duration-700 ease-out" />
              </div>
            </div>
          </motion.button>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isDarkMode, setIsDarkMode] = useState(false); // Default to light mode to showcase changes

  // Smart Sidebar State
  const [isSidebarPinned, setIsSidebarPinned] = useState(true);
  const [isSidebarHovered, setIsSidebarHovered] = useState(false);

  const [notifications, setNotifications] = useState<string[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [toast, setToast] = useState<{ msg: string, type: 'success' | 'error' } | null>(null);

  // Auth State
  const [userRole, setUserRole] = useState<UserRole>(null);

  // Navigation State from Search
  const [targetClaimId, setTargetClaimId] = useState<string | undefined>(undefined);

  // Computed state for Sidebar
  const isSidebarOpen = isSidebarPinned || isSidebarHovered;

  // Initialize Theme
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  // Determine theme colors based on role
  const themeStyles = userRole === 'User' ? {
    '--primary': '#2563EB', // Blue 600
    '--primary-hover': '#1D4ED8', // Blue 700
    '--primary-ring': 'rgba(37, 99, 235, 0.2)',
    '--shadow-color': 'rgba(37, 99, 235, 0.2)'
  } as React.CSSProperties : {
    '--primary': '#F97316', // Orange 500
    '--primary-hover': '#EA580C', // Orange 600
    '--primary-ring': 'rgba(249, 115, 22, 0.2)',
    '--shadow-color': 'rgba(249, 115, 22, 0.2)'
  } as React.CSSProperties;

  const handleGlobalSearchNavigate = (type: 'claim' | 'document' | 'user', id: string) => {
    if (type === 'claim') {
      setTargetClaimId(id);
      setActiveTab('claims');
    } else if (type === 'document') {
      setActiveTab('documents');
    } else if (type === 'user') {
      setActiveTab('settings');
    }
  };

  const addNotification = (msg: string) => {
    setNotifications(prev => [msg, ...prev]);
    setShowNotifications(true);
    setTimeout(() => setShowNotifications(false), 5000);
  };

  const handleLogin = async (role: UserRole) => {
    setUserRole(role);

    // Auto-create policy for new users (if none exist)
    if (role === 'User') {
      try {
        setToast({ msg: `Welcome back, ${CURRENT_USER.name}`, type: 'success' });
      } catch (err) {
        console.error("Failed to check policies", err);
        setToast({ msg: `Welcome back, ${CURRENT_USER.name}`, type: 'success' });
      }
    } else {
      setToast({ msg: `Welcome back, ${CURRENT_USER.name}`, type: 'success' });
    }

    // Initialize role-based notifications
    if (role === 'Admin') {
      setNotifications([
        "System Update Scheduled for 02:00 AM",
        "High Risk Transaction Alert: Policy #POL-9982",
        "New Policy Application Pending Approval",
        "Quarterly Compliance Report Ready"
      ]);
    } else {
      // Welcome notification for users
      setNotifications([
        "Welcome to Vantage Insurance!"
      ]);
    }

    setActiveTab('dashboard'); // Reset tab
  };

  const handleLogout = () => {
    // Reset user state instantly without confirmation for smoother onboarding flow
    setUserRole(null);
    CURRENT_USER.role = null;
    CURRENT_USER.name = 'Guest';
    setActiveTab('dashboard'); // Reset active tab
    setToast({ msg: "Signed out successfully", type: 'success' });
  };

  // ADMIN NAV
  const ADMIN_NAV: NavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={22} strokeWidth={1.5} /> },
    { id: 'claims', label: 'Claims Queue', icon: <FileText size={22} strokeWidth={1.5} /> },
    { id: 'analytics', label: 'Analytics', icon: <TrendingUp size={22} strokeWidth={1.5} /> },
    { id: 'documents', label: 'Documents', icon: <Files size={22} strokeWidth={1.5} /> },
    { id: 'fraud', label: 'Fraud Detection', icon: <ShieldAlert size={22} strokeWidth={1.5} /> },
    { id: 'settings', label: 'Settings', icon: <SettingsIcon size={22} strokeWidth={1.5} /> },
  ];

  // USER NAV
  const USER_NAV: NavItem[] = [
    { id: 'dashboard', label: 'My Policies', icon: <LayoutDashboard size={22} strokeWidth={1.5} /> },
    { id: 'settings', label: 'My Profile', icon: <User size={22} strokeWidth={1.5} /> },
  ];

  const NAV_ITEMS = userRole === 'Admin' ? ADMIN_NAV : USER_NAV;

  // Horizontal slide variants for page transitions ("Slider" effect)
  const pageVariants = {
    initial: { opacity: 0, x: 20 },
    in: { opacity: 1, x: 0 },
    out: { opacity: 0, x: -20 }
  };

  const pageTransition = {
    type: "spring" as const,
    stiffness: 300,
    damping: 30
  };

  // Breadcrumbs Logic
  const getBreadcrumbs = () => {
    const activeItem = NAV_ITEMS.find(item => item.id === activeTab);
    return [
      { label: 'Vantage' },
      { label: userRole === 'Admin' ? 'Admin Portal' : 'User Portal' },
      { label: activeItem?.label || 'Overview' }
    ];
  };

  // RENDER LOGIN IF NO ROLE
  if (!userRole) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div
      className="flex flex-col h-screen w-full overflow-hidden transition-colors duration-500 ease-in-out"
      style={themeStyles}
    >
      {/* Admin Mode Banner */}
      {userRole === 'Admin' && (
        <div className="w-full bg-[#F97316] text-white py-2 px-8 flex items-center justify-center gap-3 shrink-0 z-[60] shadow-md border-b border-orange-600/50">
          <ShieldAlert size={16} strokeWidth={3} className="animate-pulse" />
          <span className="text-[10px] sm:text-xs font-black uppercase tracking-[0.2em]">ADMIN PORTAL: You are viewing with elevated privileges</span>
        </div>
      )}

      <div className={cn(
        "flex flex-1 w-full overflow-hidden selection:bg-[var(--primary)]/30 relative",
        "bg-[#F8FAFC] dark:bg-[#000000] text-[#1E293B] dark:text-[#F8FAFC]",
        "transition-colors duration-500 ease-in-out"
      )}>

        {/* Toast */}
        <AnimatePresence>
          {toast && <Toast message={toast.msg} type={toast.type} onClose={() => setToast(null)} />}
        </AnimatePresence>

        {/* Background Gradients & Logo */}
        <div className="absolute inset-0 pointer-events-none opacity-100 dark:opacity-30 z-0 overflow-hidden transition-opacity duration-500">
          {/* Light Mode: Softer, warmer gradients */}
          <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-[var(--primary)] rounded-full blur-[120px] opacity-10 dark:opacity-20 transition-all duration-500" />
          <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] bg-[var(--primary-hover)] rounded-full blur-[120px] opacity-10 dark:opacity-20 transition-all duration-500" />

          {/* Faded Center Logo */}
          <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] dark:opacity-[0.04]">
            <VantageLogo size={800} variant={userRole === 'User' ? 'blue' : 'orange'} className="text-gray-900 dark:text-white animate-spin-slow transition-colors duration-500" />
          </div>
        </div>

        {/* Floating Smart Sidebar - Using updated glassmorphism */}
        <motion.aside
          initial={false}
          animate={{
            width: isSidebarOpen ? 280 : 88,
          }}
          transition={{ type: "spring", stiffness: 400, damping: 40 }}
          onMouseEnter={() => setIsSidebarHovered(true)}
          onMouseLeave={() => setIsSidebarHovered(false)}
          className={cn(
            "flex flex-col h-[calc(100%-2rem)] m-4 rounded-[32px] z-50 overflow-hidden",
            "bg-white/80 dark:bg-[#1C1C1E]/60 backdrop-blur-[40px] border border-white/60 dark:border-white/5 shadow-ceramic dark:shadow-2xl",
            "transition-all duration-500 ease-in-out"
          )}
        >
          <div className="p-8 flex items-center justify-between min-h-[88px] relative">
            <AnimatePresence>
              {isSidebarOpen && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="flex items-center gap-3 absolute left-8"
                >
                  <div className="relative">
                    <VantageLogo size={36} variant={userRole === 'User' ? 'blue' : 'orange'} />
                  </div>
                  <span className="font-semibold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-[var(--primary)] to-[var(--primary-hover)] whitespace-nowrap">Vantage</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Collapsed Logo */}
            <motion.div
              animate={{ opacity: isSidebarOpen ? 0 : 1, scale: isSidebarOpen ? 0.8 : 1 }}
              className="absolute left-0 right-0 mx-auto flex justify-center"
            >
              <VantageLogo size={36} variant={userRole === 'User' ? 'blue' : 'orange'} />
            </motion.div>
          </div>

          <nav className="flex-1 px-4 space-y-2 mt-4 overflow-y-auto custom-scrollbar overflow-x-hidden">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={cn(
                  "flex items-center gap-4 w-full p-3.5 rounded-[24px] transition-all duration-300 group relative overflow-hidden",
                  activeTab === item.id
                    ? "bg-white dark:bg-white/10 shadow-lg shadow-[var(--shadow-color)] text-[var(--primary)] dark:text-white backdrop-blur-md"
                    : "text-gray-500 dark:text-gray-400 hover:bg-white/60 dark:hover:bg-white/5",
                  !isSidebarOpen && "justify-center px-0"
                )}
              >
                {activeTab === item.id && (
                  <motion.div
                    layoutId="sidebar-indicator"
                    className="absolute left-0 w-1.5 h-5 bg-[var(--primary)] rounded-r-full"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  />
                )}

                <div className={cn("shrink-0 z-10 transition-transform duration-300", activeTab === item.id && "scale-110")}>
                  {item.icon}
                </div>
                <AnimatePresence mode="wait">
                  {isSidebarOpen && (
                    <motion.span
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                      className="font-medium text-[15px] whitespace-nowrap"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
            ))}
          </nav>

          <div className="p-6">
            <div className={cn(
              "flex items-center gap-4 p-3 rounded-[24px] transition-all duration-300 overflow-hidden backdrop-blur-sm",
              "bg-white/50 border border-white/40 dark:bg-white/5 dark:border-white/5",
              !isSidebarOpen && "justify-center p-2 bg-transparent border-0"
            )}>
              <InitialAvatar name={CURRENT_USER.name} size="md" />
              <AnimatePresence>
                {isSidebarOpen && (
                  <motion.div
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className="flex-1 min-w-0"
                  >
                    <p className="text-sm font-semibold truncate text-gray-900 dark:text-white transition-colors duration-300">{CURRENT_USER.name}</p>
                    <p className="text-xs text-gray-500 truncate transition-colors duration-300">{CURRENT_USER.role}</p>
                  </motion.div>
                )}
              </AnimatePresence>
              <AnimatePresence>
                {isSidebarOpen && (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={handleLogout}
                    className="text-gray-400 hover:text-[#F43F5E] transition-colors p-2 hover:bg-[#F43F5E]/10 rounded-full shrink-0"
                    title="Sign Out"
                  >
                    <LogOut size={18} />
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col h-full relative overflow-hidden z-10">
          {/* Header - Elevated z-index to 70 to ensure search results overlap content and sidebar */}
          <header className="h-24 flex items-center justify-between px-8 z-[70] shrink-0">
            <div className="flex items-center gap-6 flex-1">
              <button
                onClick={() => setIsSidebarPinned(!isSidebarPinned)}
                className={cn(
                  "p-3 rounded-full transition-all duration-300 hover:shadow-lg backdrop-blur-md",
                  isSidebarPinned
                    ? "bg-white/80 dark:bg-white/10 text-[var(--primary)] shadow-sm"
                    : "text-gray-400 hover:bg-white/60 dark:hover:bg-white/5"
                )}
                title={isSidebarPinned ? "Unpin Sidebar (Auto-Collapse)" : "Pin Sidebar (Keep Open)"}
              >
                {isSidebarPinned ? <Pin size={20} className="fill-current" /> : <PinOff size={20} />}
              </button>

              {/* Breadcrumbs & Search */}
              <div className="flex-1 max-w-2xl flex flex-col justify-center">
                <Breadcrumbs items={getBreadcrumbs()} />
                <GlobalSearch onNavigate={handleGlobalSearchNavigate} />
              </div>
            </div>

            <div className="flex items-center gap-4 pl-8 relative">
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                className="p-3 rounded-full bg-white/60 dark:bg-white/10 shadow-sm border border-white/40 dark:border-white/5 text-gray-500 hover:scale-110 transition-all duration-300 backdrop-blur-md"
              >
                {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
              </button>
              <div className="relative">
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  className="relative p-3 rounded-full bg-white/60 dark:bg-white/10 shadow-sm border border-white/40 dark:border-white/5 text-gray-500 hover:scale-110 transition-all duration-300 backdrop-blur-md"
                >
                  <Bell size={20} />
                  {notifications.length > 0 && <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-[#F43F5E] rounded-full ring-2 ring-white dark:ring-[#0F172A] animate-pulse"></span>}
                </button>
                <AnimatePresence>
                  {showNotifications && (
                    <motion.div
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      className="absolute right-0 mt-4 w-80 bg-white dark:bg-[#1C1C1E]/80 backdrop-blur-2xl border border-white/60 dark:border-white/5 shadow-2xl rounded-[24px] p-2 z-[80] origin-top-right overflow-hidden transition-colors duration-300"
                    >
                      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider px-4 py-3 bg-gray-50/50 dark:bg-white/5 mb-1 transition-colors duration-300">Notifications</h4>
                      {notifications.length === 0 ? (
                        <p className="text-sm text-gray-500 p-4 text-center">No new notifications</p>
                      ) : (
                        <div className="max-h-[300px] overflow-y-auto">
                          {notifications.map((n, i) => (
                            <div key={i} className="p-4 hover:bg-black/5 dark:hover:bg-white/5 rounded-2xl text-sm border-b border-gray-100 dark:border-white/5 last:border-0 transition-colors duration-300 mx-1">
                              {n}
                            </div>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </header>

          {/* Viewport - Removing 'p-4' to allow views to handle full padding */}
          <div className="flex-1 overflow-auto relative scroll-smooth">
            <div className="max-w-[1920px] mx-auto w-full h-full">
              <LayoutGroup>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab}
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                    className="h-full w-full"
                  >
                    {userRole === 'Admin' ? (
                      <>
                        {activeTab === 'dashboard' && <Dashboard onNavigate={(tab) => setActiveTab(tab)} />}
                        {activeTab === 'claims' && <Claims initialClaimId={targetClaimId} onAddNotification={addNotification} />}
                        {activeTab === 'analytics' && <Analytics />}
                        {activeTab === 'documents' && <Documents />}
                        {activeTab === 'fraud' && <FraudDetection />}
                        {activeTab === 'settings' && <Settings onLogout={handleLogout} />}
                      </>
                    ) : (
                      <>
                        {activeTab === 'dashboard' && <UserDashboard />}
                        {activeTab === 'settings' && <Settings onLogout={handleLogout} />}
                      </>
                    )}
                  </motion.div>
                </AnimatePresence>
              </LayoutGroup>
            </div>
          </div>

          {/* Global Copilot - Hidden for Admin Portal */}
          {userRole !== 'Admin' && <Copilot />}
        </main>
      </div>
    </div>
  );
}