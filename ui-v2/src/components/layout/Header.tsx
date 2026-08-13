import React from 'react';
import { motion } from 'framer-motion';
import { useUIStore } from '../../stores/uiStore';
import { useAuthStore } from '../../stores/authStore';

export type AppView = 'home' | 'browse' | 'result' | 'pricing' | 'account' | 'auth';

interface HeaderProps {
  onLogoClick: () => void;
  onNavigate: (view: AppView) => void;
  activeView: AppView;
}

export const Header: React.FC<HeaderProps> = ({ onLogoClick, onNavigate, activeView }) => {
  const { theme, setTheme } = useUIStore();
  const { user, signOut } = useAuthStore();

  const navBtn = (view: AppView, label: string) => (
    <button
      onClick={() => onNavigate(view)}
      className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
        activeView === view ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
      }`}
    >
      {label}
    </button>
  );

  return (
    <motion.header
      className="sticky top-0 z-40 w-full glass border-b border-border/60"
      initial={{ y: -60 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-6 px-6">
        <button onClick={onLogoClick} className="flex items-center gap-3">
          <motion.div
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/30"
            whileHover={{ scale: 1.06, rotate: -3 }}
            whileTap={{ scale: 0.95 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
              <path d="M12 2l2.4 7.2H22l-6.2 4.6 2.4 7.2L12 16.4 5.8 21l2.4-7.2L2 9.2h7.6z" />
            </svg>
          </motion.div>
          <span className="font-display text-base font-bold tracking-tight">
            Comic Metaphor
          </span>
        </button>

        <nav className="ml-4 flex items-center gap-1">
          {navBtn('home', 'Home')}
          {navBtn('browse', 'Vault')}
          {user && navBtn('account', 'Studio')}
        </nav>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          {user ? (
            <>
              <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-secondary/70 px-3 py-1 text-xs text-muted-foreground">
                {user.plan === 'creator' ? 'Creator' : 'Free'}
              </span>
              <button
                onClick={() => onNavigate('pricing')}
                className="rounded-lg border border-border px-3 py-2 text-sm font-medium text-muted-foreground transition hover:border-primary hover:text-primary"
              >
                Upgrade
              </button>
              <button
                onClick={signOut}
                className="rounded-lg border border-border px-3 py-2 text-sm font-medium text-muted-foreground transition hover:border-primary hover:text-primary"
              >
                Sign out
              </button>
            </>
          ) : (
            <button
              onClick={() => onNavigate('auth')}
              className="rounded-lg bg-gradient-to-r from-primary to-accent px-4 py-2 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition hover:opacity-90"
            >
              Sign in
            </button>
          )}
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            aria-label="Toggle theme"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-muted-foreground transition hover:border-primary hover:text-primary"
          >
            <motion.div
              initial={false}
              animate={{ rotate: theme === 'dark' ? 0 : 180 }}
              transition={{ duration: 0.3 }}
            >
              {theme === 'dark' ? (
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
              )}
            </motion.div>
          </button>
        </div>
      </div>
    </motion.header>
  );
};
