
import React, { useRef, useState, useEffect } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronDown, ChevronRight, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- Primitives ---

export const Spinner = ({ className }: { className?: string }) => (
  <Loader2 className={cn("animate-spin transition-colors duration-300", className)} />
);

export const Skeleton = ({ className }: { className?: string }) => (
  <div className={cn("animate-pulse bg-gray-200 dark:bg-white/10 rounded-xl transition-colors duration-300", className)} />
);

export const Breadcrumbs = ({ items }: { items: { label: string; id?: string }[] }) => (
  <nav className="flex items-center text-sm text-gray-500 dark:text-gray-400 mb-4 transition-colors duration-300">
    {items.map((item, index) => (
      <div key={index} className="flex items-center">
        {index > 0 && <ChevronRight size={14} className="mx-2 opacity-50" />}
        <span className={cn(
          "font-medium transition-colors duration-300",
          index === items.length - 1
            ? "text-gray-900 dark:text-white"
            : "hover:text-gray-700 dark:hover:text-gray-300"
        )}>
          {item.label}
        </span>
      </div>
    ))}
  </nav>
);

export const Tabs = ({ tabs, activeTab, onChange, className }: { tabs: { id: string; label: string; icon?: React.ReactNode }[]; activeTab: string; onChange: (id: string) => void; className?: string }) => {
  return (
    <div className={cn("flex gap-2 p-1 bg-white/60 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/5 w-fit backdrop-blur-sm transition-all duration-300 shadow-sm", className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            "relative px-4 py-2 text-xs font-bold rounded-lg transition-all duration-300 flex items-center gap-2 z-10",
            activeTab === tab.id
              ? "text-gray-900 dark:text-white"
              : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          )}
        >
          {activeTab === tab.id && (
            <motion.div
              layoutId="activeTab"
              className="absolute inset-0 bg-white dark:bg-white/10 rounded-lg shadow-[0_2px_8px_rgba(0,0,0,0.08)] border border-gray-100 dark:border-white/10 -z-10 transition-colors duration-300"
              transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
            />
          )}
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  );
};

export const Toast = ({ message, type = 'success', onClose }: { message: string; type?: 'success' | 'error'; onClose: () => void }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.9 }}
      className={cn(
        "fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-3 px-6 py-4 rounded-2xl shadow-xl backdrop-blur-xl border transition-colors duration-300",
        type === 'success'
          ? "bg-white/90 border-emerald-500/30 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-400"
          : "bg-white/90 border-rose-500/30 text-rose-700 dark:bg-rose-500/10 dark:border-rose-500/20 dark:text-rose-400"
      )}
    >
      {type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
      <span className="font-semibold text-sm">{message}</span>
    </motion.div>
  );
};

// --- Existing Components ---

export const Button = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success', size?: 'sm' | 'md' | 'lg', isLoading?: boolean }>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const variants = {
      primary: 'bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white shadow-lg shadow-[var(--shadow-color)] border border-transparent active:scale-[0.98]',
      secondary: 'bg-white dark:bg-white/10 text-slate-700 dark:text-white border border-gray-200 dark:border-white/20 hover:bg-gray-50 dark:hover:bg-white/20 backdrop-blur-md shadow-sm',
      ghost: 'hover:bg-gray-100 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300',
      danger: 'bg-[#F43F5E] hover:bg-[#E11D48] text-white shadow-lg shadow-rose-500/20',
      success: 'bg-[#10B981] hover:bg-[#059669] text-white shadow-lg shadow-emerald-500/20'
    };
    const sizes = {
      sm: 'px-3 py-1.5 text-xs font-medium',
      md: 'px-5 py-2.5 text-sm font-semibold tracking-tight',
      lg: 'px-8 py-3.5 text-base font-semibold'
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'rounded-full transition-all duration-300 ease-out flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading && <Spinner className="w-4 h-4" />}
        {children}
      </button>
    );
  }
);

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement> & { error?: string }>(({ className, error, ...props }, ref) => (
  <div className="relative group w-full">
    <input
      ref={ref}
      className={cn(
        "w-full px-4 py-3 rounded-2xl border outline-none transition-all duration-300 backdrop-blur-md shadow-sm",
        // Light Mode: Clearer white background, subtle border, nice shadow
        "bg-white/70 border-gray-200 focus:bg-white focus:border-[var(--primary)]/50 focus:ring-4 focus:ring-[var(--primary)]/10 text-gray-900 placeholder:text-gray-400 hover:bg-white",
        // Dark Mode
        "dark:bg-black/20 dark:border-white/10 dark:focus:bg-black/40 dark:text-white dark:hover:bg-black/30",
        error
          ? "border-rose-500 focus:ring-rose-500/20"
          : "",
        "text-sm font-medium",
        className
      )}
      {...props}
    />
    {error && <p className="absolute -bottom-5 left-2 text-[10px] font-bold text-rose-500 animate-in slide-in-from-top-1 transition-all duration-300">{error}</p>}
  </div>
));

export const TextArea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(({ className, ...props }, ref) => (
  <div className="relative group w-full">
    <textarea
      ref={ref}
      className={cn(
        "w-full px-4 py-3 rounded-2xl border outline-none transition-all duration-300 resize-none backdrop-blur-md shadow-sm",
        "bg-white/70 border-gray-200 focus:bg-white focus:border-[var(--primary)]/50 focus:ring-4 focus:ring-[var(--primary)]/10 text-gray-900 placeholder:text-gray-400 hover:bg-white",
        "dark:bg-black/20 dark:border-white/10 dark:focus:bg-black/40 dark:text-white dark:hover:bg-black/30",
        "text-sm font-medium",
        className
      )}
      {...props}
    />
  </div>
));

export const Select = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(({ className, ...props }, ref) => (
  <div className="relative group w-full">
    <select
      ref={ref}
      className={cn(
        "w-full px-4 py-3 pr-10 rounded-2xl border outline-none transition-all duration-300 appearance-none cursor-pointer backdrop-blur-md shadow-sm",
        "bg-white/70 border-gray-200 focus:bg-white focus:border-[var(--primary)]/50 focus:ring-4 focus:ring-[var(--primary)]/10 text-gray-900",
        "dark:bg-black/20 dark:border-white/10 dark:focus:bg-black/40 dark:text-white",
        "hover:bg-white dark:hover:bg-black/30",
        "text-sm font-medium",
        className
      )}
      {...props}
    />
    <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400 group-hover:text-gray-600 transition-colors duration-300" />
  </div>
));

export const Card: React.FC<{ children?: React.ReactNode; className?: string; noPadding?: boolean } & React.HTMLAttributes<HTMLDivElement>> = ({ children, className, noPadding = false, ...props }) => {
  const divRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!divRef.current) return;
    const div = divRef.current;
    const rect = div.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const handleFocus = () => {
    setOpacity(1);
  };

  const handleBlur = () => {
    setOpacity(0);
  };

  return (
    <div
      ref={divRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleFocus}
      onMouseLeave={handleBlur}
      {...props}
      className={cn(
        // Light Mode: Ceramic Glass Look - High opacity, soft blur, specific border, warm shadow
        "relative bg-white/80 backdrop-blur-[40px] border border-white/60 shadow-ceramic",
        // Dark Mode: Deep Glass
        "dark:bg-[#1e1e1e]/60 dark:backdrop-blur-2xl dark:border-white/5 dark:shadow-xl dark:shadow-black/20",
        // Layout & Clipping
        "rounded-[32px] transition-all duration-500 ease-in-out overflow-hidden group",
        !noPadding && "p-8",
        className
      )}
    >
      {/* Spotlight Effect */}
      <div
        className="pointer-events-none absolute -inset-px opacity-0 transition duration-300 group-hover:opacity-100 z-0"
        style={{
          background: `radial-gradient(600px circle at ${position.x}px ${position.y}px, var(--primary-ring), transparent 40%)`,
        }}
      />

      {/* Optional Noise Texture or Inner Sheen for Light Mode */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent pointer-events-none opacity-50 dark:opacity-0" />

      {/* Removing h-full from the inner content wrapper to allow the card to wrap tightly around its children unless h-full is explicitly requested in className */}
      <div className="relative z-10 w-full">{children}</div>
    </div>
  );
};

export const Badge: React.FC<{ children?: React.ReactNode; variant?: 'default' | 'success' | 'warning' | 'danger' | 'info', className?: string }> = ({ children, variant = 'default', className }) => {
  const styles = {
    default: 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800/80 dark:text-gray-300 dark:border-gray-700',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20',
    warning: 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20',
    danger: 'bg-rose-50 text-rose-700 border-rose-100 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20',
    info: 'bg-blue-50 text-blue-700 border-blue-100 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20'
  };
  return (
    <span className={cn(
      "px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border backdrop-blur-md whitespace-nowrap transition-colors duration-300",
      styles[variant],
      className
    )}>
      {children}
    </span>
  );
};

export const Modal: React.FC<{ isOpen: boolean; onClose: () => void; title: string; children: React.ReactNode; size?: 'sm' | 'md' | 'lg' | 'xl' }> = ({ isOpen, onClose, title, children, size = 'md' }) => {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-3xl',
    xl: 'max-w-5xl h-[85vh]'
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-gray-900/20 dark:bg-black/40 backdrop-blur-md transition-colors duration-500"
          />
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className={cn(
              "w-full bg-white dark:bg-[#1C1C1E]/90 backdrop-blur-2xl rounded-[32px] shadow-2xl overflow-hidden relative z-10 border border-white/50 dark:border-white/10 flex flex-col transition-colors duration-500",
              sizeClasses[size]
            )}
          >
            <div className="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center shrink-0 transition-colors duration-300 bg-gray-50/50 dark:bg-transparent">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white tracking-tight transition-colors duration-300">{title}</h2>
              <button onClick={onClose} className="p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors duration-300 text-gray-500"><X size={20} /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-white/50 dark:bg-transparent">
              {children}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
