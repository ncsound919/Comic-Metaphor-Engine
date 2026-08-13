import { create } from 'zustand';
import { supabase } from '../lib/supabase';
import { api } from '../lib/api';

export interface AuthUser {
  id: string;
  email?: string;
  plan?: string;
  subscription_status?: string;
}

interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  init: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<string | null>;
  signUp: (email: string, password: string) => Promise<string | null>;
  signOut: () => Promise<void>;
  refreshPlan: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  loading: false,
  error: null,

  init: async () => {
    if (!supabase) return;
    const { data } = await supabase.auth.getSession();
    set({ user: data.session ? { id: data.session.user.id, email: data.session.user.email } : null });
    supabase.auth.onAuthStateChange((_event, session) => {
      set({ user: session ? { id: session.user.id, email: session.user.email } : null });
    });
    if (get().user) await get().refreshPlan();
  },

  signIn: async (email, password) => {
    if (!supabase) {
      set({ error: 'Supabase is not configured (set VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY).' });
      return 'Supabase is not configured';
    }
    set({ loading: true, error: null });
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    set({ loading: false });
    if (error) {
      set({ error: error.message });
      return error.message;
    }
    await get().refreshPlan();
    return null;
  },

  signUp: async (email, password) => {
    if (!supabase) {
      set({ error: 'Supabase is not configured (set VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY).' });
      return 'Supabase is not configured';
    }
    set({ loading: true, error: null });
    const { error } = await supabase.auth.signUp({ email, password });
    set({ loading: false });
    if (error) {
      set({ error: error.message });
      return error.message;
    }
    return null;
  },

  signOut: async () => {
    if (supabase) await supabase.auth.signOut();
    set({ user: null });
  },

  refreshPlan: async () => {
    if (!supabase) return;
    const session = await supabase.auth.getSession();
    const token = session.data.session?.access_token;
    if (!token) return;
    try {
      const { user } = await api.me(token);
      set((s) =>
        s.user
          ? { user: { ...s.user, plan: user.plan, subscription_status: user.subscription_status } }
          : {}
      );
    } catch {
      // keep existing user; plan refresh is best-effort
    }
  },
}));
