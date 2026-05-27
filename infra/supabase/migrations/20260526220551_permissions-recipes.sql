grant all on table app.recipes to service_role;
grant select on table app.recipes to authenticated;
grant select on table app.recipes to anon;

alter default privileges in schema app
grant all on tables to service_role;

alter default privileges in schema app
grant select, insert, update, delete on tables to authenticated;