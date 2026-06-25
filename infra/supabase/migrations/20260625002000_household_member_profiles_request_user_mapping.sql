drop view if exists app.household_member_profiles;

create view app.household_member_profiles
  with (security_invoker = true)
as
  select
    req.user_id as request_user_id,
    mem.household_id,
    mem.user_id as id,
    mem.role,
    mem.joined_at as created_at,
    p.display_name,
    p.avatar_url
  from app.household_members req
  join app.household_members mem on req.household_id = mem.household_id
  join app.profiles p on mem.user_id = p.id;