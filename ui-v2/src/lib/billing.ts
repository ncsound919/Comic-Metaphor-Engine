export interface BillingUser {
  plan?: string;
  subscription_status?: string;
}

export const ACTIVE_STATUSES = ['active', 'trialing'];

export function isActivePlan(user: BillingUser | null | undefined): boolean {
  return (
    user?.plan === 'creator' &&
    (user.subscription_status === 'active' || user.subscription_status === 'trialing')
  );
}
