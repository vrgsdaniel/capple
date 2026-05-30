-- Add num_ratings to recipes and drop the stale CHECK constraint
-- (rating is now a computed average, no longer bounded 1-5 at row level).
ALTER TABLE app.recipes
    DROP CONSTRAINT IF EXISTS recipes_rating_check,
    ALTER COLUMN rating TYPE numeric(3,1),
    ADD COLUMN num_ratings integer NOT NULL DEFAULT 0;

-- ─── Trigger function ────────────────────────────────────────────────────────
-- Fires AFTER INSERT or UPDATE on recipe_user_interactions when the row is a
-- 'rated' interaction. Keeps recipes.rating (running average) and
-- recipes.num_ratings in sync atomically — no application-layer calls needed.
--
-- INSERT path  (new rating):
--   num_ratings += 1
--   rating = round((old_avg * (num_ratings - 1) + new_value) / num_ratings, 1)
--
-- UPDATE path  (user changes their existing rating):
--   num_ratings unchanged
--   rating = round((old_avg * num_ratings - old_value + new_value) / num_ratings, 1)
CREATE OR REPLACE FUNCTION app.sync_recipe_rating()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE app.recipes
        SET
            num_ratings = num_ratings + 1,
            rating = ROUND(
                (COALESCE(rating, 0) * num_ratings + NEW.value::numeric)
                / (num_ratings + 1),
            1)
        WHERE id = NEW.recipe_id;

    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE app.recipes
        SET
            rating = ROUND(
                (COALESCE(rating, 0) * num_ratings
                    - COALESCE(OLD.value, 0)::numeric
                    + NEW.value::numeric)
                / NULLIF(num_ratings, 0),
            1)
        WHERE id = NEW.recipe_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_sync_recipe_rating
    AFTER INSERT OR UPDATE ON app.recipe_user_interactions
    FOR EACH ROW
    WHEN (NEW.interaction_type = 'rated')
    EXECUTE FUNCTION app.sync_recipe_rating();
