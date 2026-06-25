create or replace view app.household_member_profiles
  with (security_invoker = true)
as
  select
    hm.household_id,
    hm.user_id as id,
    hm.role,
    hm.joined_at as created_at,
    p.display_name,
    p.avatar_url
  from app.household_members hm
  join app.profiles p on p.id = hm.user_id;
