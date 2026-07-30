-- Deterministic, database-owned recipe full-text indexing and matching.
--
-- The generated vector backfills existing rows when this migration is applied
-- and remains synchronized automatically for future inserts and updates.

CREATE OR REPLACE FUNCTION app.recipe_search_jsonb_text(value jsonb)
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
SET search_path = pg_catalog
AS $$
    SELECT COALESCE(
        string_agg(
            CASE jsonb_typeof(element)
                WHEN 'string' THEN element #>> '{}'
                WHEN 'object' THEN COALESCE(
                    element ->> 'name',
                    element ->> 'item',
                    element ->> 'label',
                    element::text
                )
                ELSE element::text
            END,
            ' ' ORDER BY ordinal
        ),
        ''
    )
    FROM jsonb_array_elements(
        CASE
            WHEN jsonb_typeof(value) = 'array' THEN value
            ELSE '[]'::jsonb
        END
    ) WITH ORDINALITY AS entries(element, ordinal);
$$;

ALTER TABLE app.recipes
    ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english'::regconfig, COALESCE(name, '')), 'A')
        ||
        setweight(to_tsvector('english'::regconfig, app.recipe_search_jsonb_text(labels)), 'B')
        ||
        setweight(to_tsvector('english'::regconfig, COALESCE(recipe_type, '')), 'C')
        ||
        setweight(to_tsvector('english'::regconfig, app.recipe_search_jsonb_text(ingredients)), 'D')
    ) STORED;

CREATE INDEX recipes_search_vector_idx
    ON app.recipes
    USING GIN (search_vector);

-- Keep this function deliberately narrow: changeable filters, sorting,
-- interaction enrichment, counts, and pagination belong to the service layer.
CREATE OR REPLACE FUNCTION app.match_recipes(p_text text)
RETURNS TABLE (
    recipe_id uuid,
    relevance real
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, app
AS $$
    WITH search_query AS (
        SELECT CASE
            WHEN NULLIF(btrim(p_text), '') IS NULL THEN NULL::tsquery
            ELSE websearch_to_tsquery('english'::regconfig, btrim(p_text))
        END AS query
    )
    SELECT
        recipe.id AS recipe_id,
        ts_rank_cd(recipe.search_vector, search_query.query) AS relevance
    FROM app.recipes AS recipe
    CROSS JOIN search_query
    WHERE search_query.query IS NOT NULL
      AND recipe.search_vector @@ search_query.query
    ORDER BY recipe.id;
$$;

REVOKE ALL ON FUNCTION app.match_recipes(text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION app.match_recipes(text) TO service_role;
