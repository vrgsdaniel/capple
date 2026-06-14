ALTER TABLE app.recipes ENABLE ROW LEVEL SECURITY;

CREATE POLICY recipes_read_anon
ON app.recipes
FOR SELECT
TO anon
USING (true);

CREATE POLICY recipes_read_authenticated
ON app.recipes
FOR SELECT
TO authenticated
USING (true);
