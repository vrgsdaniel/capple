create table public.battery_logs (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id) on delete cascade,
  household_id uuid not null references public.households(id) on delete cascade,
  level        smallint not null check (level >= 0 and level <= 100),
  note         text,
  effective_at timestamptz not null,
  logged_at    timestamptz not null default now()
);

-- index for time-series queries using effective_at (what the charts query)
create index battery_logs_household_effective_at
  on public.battery_logs (household_id, effective_at desc);

-- index for per-user queries
create index battery_logs_user_effective_at
  on public.battery_logs (user_id, effective_at desc);

-- RLS
alter table public.battery_logs enable row level security;

create policy "members can read household battery logs"
  on public.battery_logs for select
  using (
    exists (
      select 1 from public.household_members hm
      where hm.household_id = battery_logs.household_id
      and hm.user_id = auth.uid()
    )
  );

create policy "users can insert own battery logs"
  on public.battery_logs for insert
  with check (user_id = auth.uid());

create policy "users can update own battery logs"
  on public.battery_logs for update
  using (user_id = auth.uid());

-- 12 month retention via pg_cron (enable when ready)
create extension if not exists pg_cron;
select cron.schedule('delete-old-battery-logs', '0 0 1,15 * *',
  $$delete from public.battery_logs
    where logged_at < now() - interval '12 months'$$);