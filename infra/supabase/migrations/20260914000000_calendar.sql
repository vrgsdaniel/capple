-- Generic trigger function to keep `updated_at` current on any table that has that column.
-- Shared across tables (rather than one function per table, as households currently does)
-- so the same trigger definition attaches to every future table with this need.
create or replace function app.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create table app.calendar_events (
    id             uuid primary key default gen_random_uuid(),
    household_id   uuid not null references app.households(id) on delete cascade,
    title          text not null check (length(trim(title)) > 0),
    event_date     date not null,
    start_time     time,
    end_time       time,
    location       text,
    description    text,
    created_by     uuid not null references app.profiles(id) on delete cascade,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now(),
    constraint end_time_requires_start
        check (end_time is null or start_time is not null),
    constraint end_time_after_start
        check (end_time is null or end_time >= start_time)
);

create index on app.calendar_events (household_id, event_date);

create trigger calendar_events_set_updated_at
    before update on app.calendar_events
    for each row execute function app.set_updated_at();

alter table app.calendar_events enable row level security;

create policy household_rw on app.calendar_events
    for all
    using (
        exists (
            select 1
            from app.household_members hm
            where hm.household_id = calendar_events.household_id
              and hm.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1
            from app.household_members hm
            where hm.household_id = calendar_events.household_id
              and hm.user_id = auth.uid()
        )
    );

-- birth_month/birth_day/birth_year are stored separately (rather than as one `date`) because the
-- birth year is frequently unknown to the person adding the entry — the UI must not force a
-- guess or make the user do the arithmetic. `birth_year` is nullable for exactly that case;
-- `show_year` additionally lets a known year be withheld from age display (a separate, privacy
-- concern from whether the year is known at all).
create table app.calendar_birthdays (
    id             uuid primary key default gen_random_uuid(),
    household_id   uuid not null references app.households(id) on delete cascade,
    person_name    text not null check (length(trim(person_name)) > 0),
    birth_month    smallint not null check (birth_month between 1 and 12),
    birth_day      smallint not null check (birth_day between 1 and 31),
    -- Wide static bound rather than one derived from now(): keeps this an immutable, always-true
    -- check rather than one whose meaning depends on when it's evaluated. Exact "not in the
    -- future" precision is enforced at the API boundary instead.
    birth_year     smallint check (birth_year is null or birth_year between 1900 and 2100),
    show_year      boolean not null default true,
    created_by     uuid not null references app.profiles(id) on delete cascade,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now(),
    constraint valid_birth_day_for_month
        -- Permissive on Feb 29 regardless of birth_year's own leap-ness — this is a coarse
        -- calendar-shape check, not an exact-date one; the app validates the exact combination
        -- when birth_year is provided.
        check (
            birth_day <= case birth_month
                when 2 then 29
                when 4 then 30
                when 6 then 30
                when 9 then 30
                when 11 then 30
                else 31
            end
        ),
    constraint show_year_requires_birth_year
        check (show_year = false or birth_year is not null)
);

create index on app.calendar_birthdays (household_id);

create trigger calendar_birthdays_set_updated_at
    before update on app.calendar_birthdays
    for each row execute function app.set_updated_at();

alter table app.calendar_birthdays enable row level security;

create policy household_rw on app.calendar_birthdays
    for all
    using (
        exists (
            select 1
            from app.household_members hm
            where hm.household_id = calendar_birthdays.household_id
              and hm.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1
            from app.household_members hm
            where hm.household_id = calendar_birthdays.household_id
              and hm.user_id = auth.uid()
        )
    );
