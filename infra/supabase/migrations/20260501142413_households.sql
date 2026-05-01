-- households
create table public.households (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  created_by  uuid not null references auth.users(id) on delete restrict,
  invite_code text not null unique default substring(gen_random_uuid()::text, 1, 8),
  created_at  timestamptz not null default now()
);

-- household_members
create table public.household_members (
  id           uuid primary key default gen_random_uuid(),
  household_id uuid not null references public.households(id) on delete cascade,
  user_id      uuid not null references auth.users(id) on delete cascade,
  role         text not null default 'member' check (role in ('owner', 'member')),
  joined_at    timestamptz not null default now(),
  unique (household_id, user_id)
);

-- RLS
alter table public.households enable row level security;
alter table public.household_members enable row level security;

-- households: members can read their household
create policy "members can read own household"
  on public.households for select
  using (
    exists (
      select 1 from public.household_members hm
      where hm.household_id = id
      and hm.user_id = auth.uid()
    )
  );

-- households: owner can update
create policy "owner can update household"
  on public.households for update
  using (created_by = auth.uid());

-- households: authenticated users can create
create policy "authenticated users can create household"
  on public.households for insert
  with check (auth.uid() = created_by);

-- household_members: members can read their own household's members
create policy "members can read household members"
  on public.household_members for select
  using (
    exists (
      select 1 from public.household_members hm
      where hm.household_id = household_id
      and hm.user_id = auth.uid()
    )
  );

-- household_members: users can insert themselves (join via invite)
create policy "users can join household"
  on public.household_members for insert
  with check (user_id = auth.uid());

-- household_members: owner can remove members
create policy "owner can remove members"
  on public.household_members for delete
  using (
    exists (
      select 1 from public.households h
      where h.id = household_id
      and h.created_by = auth.uid()
    )
  );