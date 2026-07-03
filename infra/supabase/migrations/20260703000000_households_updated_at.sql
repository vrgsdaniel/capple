-- add updated_at to households
alter table public.households
  add column if not exists updated_at timestamptz not null default now();

-- trigger function to keep updated_at current on every update
create or replace function public.set_households_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger households_set_updated_at
  before update on public.households
  for each row execute function public.set_households_updated_at();
