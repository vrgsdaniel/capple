-- Create unified interactions table for recipes at user level
CREATE TABLE app.recipe_user_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL REFERENCES app.recipes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    interaction_type VARCHAR(20) NOT NULL CHECK (interaction_type IN ('liked', 'cooked', 'rated')),
    value INTEGER,
    created_at timestamptz DEFAULT NOW(),
    updated_at timestamptz DEFAULT NOW(),

    -- 'liked': unique per (user, recipe) - one like per user
    UNIQUE(user_id, recipe_id, interaction_type)
        WHERE interaction_type = 'liked',

    -- 'cooked': unique per (user, recipe) - one cooked entry per user
    -- 'rated': unique per (user, recipe) - one rating per user
    UNIQUE(user_id, recipe_id, interaction_type)
        WHERE interaction_type IN ('cooked', 'rated')
);

CREATE INDEX idx_recipe_user_interactions_lookup
    ON app.recipe_user_interactions (user_id, recipe_id, interaction_type);
CREATE INDEX idx_recipe_user_interactions_type
    ON app.recipe_user_interactions (interaction_type);

-- RLS: Enable row security
ALTER TABLE app.recipe_user_interactions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own interactions
CREATE POLICY "users can view their recipe interactions"
    ON app.recipe_user_interactions
    FOR SELECT
    USING (user_id = auth.uid());

-- Policy: Users can insert their own interactions
CREATE POLICY "users can insert recipe interactions"
    ON app.recipe_user_interactions
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Policy: Users can delete their own interactions
CREATE POLICY "users can delete recipe interactions"
    ON app.recipe_user_interactions
    FOR DELETE
    USING (user_id = auth.uid());

-- Policy: Users can update their own interactions
CREATE POLICY "users can update recipe interactions"
    ON app.recipe_user_interactions
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

