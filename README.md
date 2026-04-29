# Capple
planning app

## Database Migrations

Migrations live in `infra/supabase/migrations/` and follow the naming convention `YYYYMMDDHHmmss_<identifier>.sql`.

### First-time setup

Link your local `infra/` directory to the remote Supabase project (only needed once):

```bash
cd infra && supabase link --project-ref $SUPABASE_PROJECT
```

### Create a new migration

```bash
make migration name=<identifier>
```

Example:

```bash
make migration name=add_couples_table
# Creates infra/supabase/migrations/20260426143022_add_couples_table.sql
```

### Apply migrations

```bash
make db-push
```

This runs `supabase db push` from the `infra/` directory, applying any pending migrations to the linked Supabase project.

In CI — migrations are applied automatically when files under
`infra/supabase/migrations/` are merged to main.