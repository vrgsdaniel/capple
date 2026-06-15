create table app.grocery_items (
    id               uuid primary key default gen_random_uuid(),
    household_id     uuid not null references app.households(id) on delete cascade,
    name             text not null check (length(trim(name)) > 0),
    qty              text,
    bought           boolean not null default false,
    bought_at        timestamptz,
    source_recipe_id uuid references app.recipes(id) on delete set null,
    added_by         uuid references app.profiles(id) on delete set null,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

create index on app.grocery_items (household_id, bought, created_at desc);

alter table app.grocery_items enable row level security;

-- Members can read/write only their own household's items.
create policy household_rw on app.grocery_items
    for all
    using  (household_id = (select household_id from app.household_members
                            where user_id = auth.uid()))
    with check (household_id = (select household_id from app.household_members
                                where user_id = auth.uid()));

