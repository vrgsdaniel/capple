create or replace view app.household_member_profiles
  with (security_invoker = true)
as
  select
    requester.user_id as request_user_id,
    member.household_id,
    member.user_id as id,
    member.role,
    member.created_at,
    p.display_name,
    p.avatar_url
  from app.household_members requester
  join app.household_members member on member.household_id = requester.household_id
  join app.profiles p on p.id = member.user_id;