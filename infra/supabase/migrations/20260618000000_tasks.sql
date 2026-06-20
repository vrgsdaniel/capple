create table app.tasks (
    id             uuid primary key default gen_random_uuid(),
    household_id   uuid not null references app.households(id) on delete cascade,
    name           text not null check (length(trim(name)) > 0),
    assignee_type  text not null default 'none' check (assignee_type in ('none', 'specific', 'all')),
    assignee_id    uuid references app.profiles(id) on delete set null,
    due_date       date,
    frequency      text check (frequency in ('daily', 'weekly', 'monthly')),
    created_by     uuid not null references app.profiles(id) on delete cascade,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now(),
    completed_at   timestamptz,
    constraint assignee_id_requires_specific
        check (assignee_type = 'specific' or assignee_id is null)
);

create index on app.tasks (household_id, completed_at, due_date);

alter table app.tasks enable row level security;

-- Household members can read and write their household's tasks.
create policy household_rw on app.tasks
    for all
    using (
        exists (
            select 1
            from app.household_members hm
            where hm.household_id = household_id
              and hm.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1
            from app.household_members hm
            where hm.household_id = household_id
              and hm.user_id = auth.uid()
        )
    );
