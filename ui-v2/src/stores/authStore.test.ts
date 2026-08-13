import { describe, it, expect, vi, beforeEach } from 'vitest';

const signInWithPassword = vi.fn();
const signUp = vi.fn();
const signOut = vi.fn();
const getSession = vi.fn();

vi.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: () => getSession(),
      signInWithPassword: (args: unknown) => signInWithPassword(args),
      signUp: (args: unknown) => signUp(args),
      signOut: () => signOut(),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
    },
  },
}));

vi.mock('../lib/api', () => ({
  api: {
    me: vi.fn(async () => ({ user: { plan: 'free', subscription_status: 'inactive' } })),
  },
}));

import { useAuthStore } from './authStore';

beforeEach(() => {
  useAuthStore.setState({ user: null, loading: false, error: null });
  getSession.mockResolvedValue({ data: { session: null } });
});

describe('authStore', () => {
  it('signs in successfully', async () => {
    signInWithPassword.mockResolvedValue({ error: null });
    const err = await useAuthStore.getState().signIn('a@b.c', 'pw');
    expect(err).toBeNull();
    expect(signInWithPassword).toHaveBeenCalledWith({ email: 'a@b.c', password: 'pw' });
  });

  it('returns the error message on failed sign-in', async () => {
    signInWithPassword.mockResolvedValue({ error: { message: 'Invalid login credentials' } });
    const err = await useAuthStore.getState().signIn('a@b.c', 'bad');
    expect(err).toBe('Invalid login credentials');
    expect(useAuthStore.getState().error).toBe('Invalid login credentials');
  });

  it('signs out and clears the user', async () => {
    useAuthStore.setState({ user: { id: 'u1', email: 'a@b.c' } });
    await useAuthStore.getState().signOut();
    expect(signOut).toHaveBeenCalled();
    expect(useAuthStore.getState().user).toBeNull();
  });
});
