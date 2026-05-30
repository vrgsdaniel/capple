-- Add composite unique constraint to recipe_user_interactions.
-- This makes the (user_id, recipe_id, interaction_type) triplet explicitly
-- unique across all interaction types, which allows PostgREST upserts to
-- target a single deterministic conflict key instead of relying on partial indexes.
-- The three existing partial unique indexes remain for their lookup benefits.
ALTER TABLE app.recipe_user_interactions
    ADD CONSTRAINT uq_recipe_user_interaction
    UNIQUE (user_id, recipe_id, interaction_type);
