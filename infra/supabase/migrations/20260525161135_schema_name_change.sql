CREATE SCHEMA IF NOT EXISTS app;

-- All tables are created in the public schema by default, so move them to app.
ALTER TABLE public.profiles SET SCHEMA app;
ALTER TABLE public.battery_logs SET SCHEMA app;
ALTER TABLE public.households SET SCHEMA app;
ALTER TABLE public.household_members SET SCHEMA app;

-- Move and update the auth trigger function for the new schema.
ALTER FUNCTION public.handle_new_user() SET SCHEMA app;
CREATE OR REPLACE FUNCTION app.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO app.profiles (id, display_name, avatar_url)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'avatar_url'
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION app.handle_new_user();

-- Recreate the retention cron job so it points at app.battery_logs.
SELECT cron.unschedule(jobid)
FROM cron.job
WHERE jobname = 'delete-old-battery-logs';

SELECT cron.schedule(
  'delete-old-battery-logs',
  '0 0 1,15 * *',
  $$DELETE FROM app.battery_logs
    WHERE logged_at < NOW() - INTERVAL '12 months'$$
);

GRANT USAGE ON SCHEMA app TO anon;
GRANT USAGE ON SCHEMA app TO authenticated;
GRANT USAGE ON SCHEMA app TO service_role;

GRANT ALL ON ALL TABLES IN SCHEMA app TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA app
TO authenticated;


