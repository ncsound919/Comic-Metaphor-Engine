# Comic Metaphor Engine — SaaS runbook

Deployment guide for the $1/mo Creator plan (Supabase Auth + Storage + Postgres, Stripe billing, Vercel serverless).

## Supabase

1. Create a project at https://supabase.com. Note the project URL, anon key, and service role key.
2. Run the SQL below in the SQL editor.
3. Create a Storage bucket named `comics` (public: false).

```sql
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  supabase_uid uuid unique references auth.users(id),
  email text,
  stripe_customer_id text,
  plan text default 'free',
  subscription_status text default 'inactive',
  current_period_end timestamptz,
  created_at timestamptz default now()
);

create table if not exists comics (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id),
  filename text,
  storage_path text,
  size_bytes bigint,
  page_count int,
  status text default 'processing',
  error text,
  created_at timestamptz default now()
);

create table if not exists insights (
  id uuid primary key default gen_random_uuid(),
  comic_id uuid references comics(id),
  user_id uuid references users(id),
  report jsonb,
  created_at timestamptz default now()
);
```

## Stripe

Uses the same live Stripe account as Uplift Justice (credentials live in
`01_Platforms/Uplift Justice/.env`).

1. The `$1.00/month` Creator price already exists (created 2026-08-13, live):
   `STRIPE_PRICE_CREATOR_MONTHLY = price_1U48KPQrfNRBru0zUamDe4wL`
   (product `Comic Metaphor Engine - Creator`). If it needs to be recreated:
   `unit_amount=100&currency=usd&recurring[interval]=month`.
2. Configure a webhook endpoint `{API_BASE}/api/billing/webhook` for events:
   `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`,
   `customer.subscription.deleted`. Copy the signing secret -> `STRIPE_WEBHOOK_SECRET`.
3. The webhook only persists entitlements to the `users` table. In production BOTH
   `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` must be set — if only one is set the
   backend fails closed (RuntimeError); if neither is set the backend runs in dev mode
   and billing writes are silently skipped. Never deploy the backend without both vars.

## Vercel

1. Deploy the `Comic Metaphor Logic` folder as a new project (framework: Other).
2. Backend env: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `STRIPE_SECRET_KEY`,
   `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_CREATOR_MONTHLY`, `APP_URL`.
   (No `VITE_STRIPE_PUBLISHABLE_KEY` needed — checkout URLs come from the backend.)
3. Frontend env (the `ui-v2` app): `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`.
4. `maxDuration: 300` in `vercel.json` requires Fluid compute (Pro); set 60 on Hobby.
5. Test-mode E2E, then flip Stripe to live keys.

## Local dev

Run the backend from this folder with no env vars: `uvicorn api.main:app --reload --port 8000`.
Dev mode returns a `dev-user` with `plan: creator`, so uploads + insights work without
Supabase or Stripe. Run the frontend from `ui-v2` with `npm run dev`.
