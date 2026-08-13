import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../stores/authStore';

export const SignIn: React.FC = () => {
  const { signIn, signUp, loading, error } = useAuthStore();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const submit = async () => {
    const err = mode === 'signin' ? await signIn(email, password) : await signUp(email, password);
    if (err) return;
    if (mode === 'signin') setEmail(''), setPassword('');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-md px-6 py-20"
    >
      <div className="glass rounded-2xl p-8 shadow-xl">
        <h2 className="font-display text-2xl font-bold">
          {mode === 'signin' ? 'Sign in' : 'Create your account'}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload your comics and unlock insight reports.
        </p>

        <div className="mt-6 flex flex-col gap-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            aria-label="Email"
            className="rounded-xl border border-input bg-background/60 px-4 py-3 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            aria-label="Password"
            className="rounded-xl border border-input bg-background/60 px-4 py-3 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <button
            onClick={submit}
            disabled={loading || !email || !password}
            className="rounded-xl bg-gradient-to-r from-primary to-accent px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition hover:opacity-90 disabled:opacity-50"
          >
            {loading ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Sign up'}
          </button>
          <button
            onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            {mode === 'signin' ? 'Need an account? Sign up' : 'Already have an account? Sign in'}
          </button>
        </div>
      </div>
    </motion.div>
  );
};
