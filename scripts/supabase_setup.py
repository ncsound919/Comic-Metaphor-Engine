import os
import re
import sys

PWD_FILE = r"C:\Users\User\Downloads\Uplift\plans\Hempforge.txt"
DB_PASSWORD = os.environ.get("CME_DB_PASSWORD", "")

if not DB_PASSWORD:
    with open(PWD_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    # password on line 1 and line 8; take the first
    m = re.search(r"^supabase psswrd:\s*(\S+)", text, re.M)
    DB_PASSWORD = m.group(1) if m else ""

import psycopg2  # noqa: E402

SQL = """
create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  supabase_uid uuid unique references auth.users(id),
  email text,
  stripe_customer_id text,
  plan text default 'free',
  subscription_status text default 'inactive',
  current_period_end bigint,
  created_at timestamptz default now()
);

create table if not exists public.comics (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id),
  filename text,
  storage_path text,
  size_bytes bigint,
  page_count int,
  status text default 'processing',
  error text,
  created_at timestamptz default now()
);

create table if not exists public.insights (
  id uuid primary key default gen_random_uuid(),
  comic_id uuid references public.comics(id),
  user_id uuid references public.users(id),
  report jsonb,
  created_at timestamptz default now()
);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.users (supabase_uid, email, plan, subscription_status)
  values (new.id, new.email, 'free', 'inactive')
  on conflict (supabase_uid) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
"""

conn = psycopg2.connect(
    host="db.xaawyyvtqttoudwqxabw.supabase.co",
    port=5432,
    dbname="postgres",
    user="postgres",
    password=DB_PASSWORD,
    connect_timeout=30,
    sslmode="require",
)
conn.autocommit = True
cur = conn.cursor()
cur.execute(SQL)
cur.execute(
    "select table_name from information_schema.tables "
    "where table_schema='public' and table_name in ('users','comics','insights') order by table_name"
)
rows = cur.fetchall()
print("tables present:", [r[0] for r in rows])
cur.execute(
    "select tgname from pg_trigger where tgname='on_auth_user_created'"
)
print("trigger present:", [r[0] for r in cur.fetchall()])
cur.close()
conn.close()
print("SCHEMA OK")
