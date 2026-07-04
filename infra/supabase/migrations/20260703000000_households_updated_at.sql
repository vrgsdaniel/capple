-- add updated_at to households
alter table app.households
  add column if not exists updated_at timestamptz not null default now();

-- trigger function to keep updated_at current on every update
create or replace function app.set_households_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger households_set_updated_at
  before update on app.households
  for each row execute function app.set_households_updated_at();
