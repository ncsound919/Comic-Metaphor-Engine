import { describe, it, expect } from 'vitest';
import { isActivePlan } from '../billing';

describe('isActivePlan', () => {
  it('returns true for an active creator subscription', () => {
    expect(isActivePlan({ plan: 'creator', subscription_status: 'active' })).toBe(true);
  });

  it('returns true for a trialing creator', () => {
    expect(isActivePlan({ plan: 'creator', subscription_status: 'trialing' })).toBe(true);
  });

  it('returns false when free', () => {
    expect(isActivePlan({ plan: 'free', subscription_status: 'active' })).toBe(false);
  });

  it('returns false when canceled', () => {
    expect(isActivePlan({ plan: 'creator', subscription_status: 'canceled' })).toBe(false);
  });

  it('returns false for null', () => {
    expect(isActivePlan(null)).toBe(false);
  });
});
