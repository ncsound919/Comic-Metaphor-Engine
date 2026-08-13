import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../stores/authStore';
import { api } from '../../lib/api';
import { supabase } from '../../lib/supabase';

export const Pricing: React.FC = () => {
  const { user } = useAuthStore();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const subscribe = async () => {
    if (!supabase) {
      setError('Billing requires a deployed backend — run locally in dev mode first.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const session = await supabase.auth.getSession();
      const token = session.data.session?.access_token;
      if (!token) throw new Error('You must be signed in first.');
      const { url } = await api.billingCheckout(token);
      window.location.href = url;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not start checkout');
      setBusy(false);
    }
  };

  const manage = async () => {
    if (!supabase) return;
    setBusy(true);
    setError(null);
    try {
      const session = await supabase.auth.getSession();
      const token = session.data.session?.access_token;
      if (!token) throw new Error('You must be signed in first.');
      const { url } = await api.billingPortal(token);
      window.location.href = url;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not open the portal');
      setBusy(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-5xl px-6 py-16"
    >
      <div className="text-center">
        <h2 className="font-display text-3xl font-bold">Simple pricing</h2>
        <p className="mt-2 text-muted-foreground">
          Browse the metaphor library free forever. Upload your own comics for $1/month.
        </p>
      </div>

      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <div className="glass rounded-2xl p-8">
          <h3 className="text-lg font-semibold">Free</h3>
          <p className="mt-1 text-sm text-muted-foreground">Explore the vault</p>
          <p className="mt-4 text-3xl font-bold">$0</p>
          <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
            <li>Browse all 6+ metaphor protocols</li>
            <li>Generate sample lessons</li>
            <li>Semantic search</li>
          </ul>
          <div className="mt-6 rounded-xl bg-secondary/60 px-4 py-3 text-sm text-muted-foreground">
            {user ? 'You are on the free plan' : 'Sign in to start'}
          </div>
        </div>

        <div className="relative rounded-2xl border-2 border-primary bg-gradient-to-b from-primary/10 to-transparent p-8 shadow-xl">
          <span className="absolute -top-3 left-6 rounded-full bg-gradient-to-r from-primary to-accent px-3 py-1 text-xs font-semibold text-primary-foreground">
            Popular
          </span>
          <h3 className="text-lg font-semibold">Creator</h3>
          <p className="mt-1 text-sm text-muted-foreground">Upload your comics</p>
          <p className="mt-4 text-3xl font-bold">
            $1<span className="text-sm font-normal text-muted-foreground"> /month</span>
          </p>
          <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
            <li>Unlimited comic uploads (PDF, TXT, MD, EPUB)</li>
            <li>Insight reports: themes, mappings, scored lessons</li>
            <li>Saved upload history</li>
            <li>Cancel anytime</li>
          </ul>
          {user?.plan === 'creator' ? (
            <button
              onClick={manage}
              disabled={busy}
              className="mt-6 w-full rounded-xl border border-border px-6 py-3 text-sm font-semibold transition hover:border-primary hover:text-primary disabled:opacity-50"
            >
              {busy ? 'Opening portal…' : 'Manage subscription'}
            </button>
          ) : (
            <button
              onClick={subscribe}
              disabled={busy}
              className="mt-6 w-full rounded-xl bg-gradient-to-r from-primary to-accent px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition hover:opacity-90 disabled:opacity-50"
            >
              {busy ? 'Redirecting…' : user ? 'Subscribe — $1/mo' : 'Sign in to subscribe'}
            </button>
          )}
          {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
        </div>
      </div>
    </motion.div>
  );
};
