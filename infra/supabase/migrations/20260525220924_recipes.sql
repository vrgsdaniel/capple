create table app.recipes (
    id UUID primary key,
    name varchar(100) not null,
    source_name varchar(100),
    source_url text,
    recipe_type varchar(30),
    ingredients JSONB not null,
    labels JSONB not null,
    instructions text,
    prep_time_minutes integer,
    cook_time_minutes integer,
    servings integer,
    rating integer check (rating >= 1 and rating <= 5),
    image_uri text,
    created_at timestamp not null default NOW()
);
