-- A user may only belong to one household at a time.
alter table public.household_members
  add constraint household_members_user_id_unique unique (user_id);
