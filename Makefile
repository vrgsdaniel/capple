MIGRATIONS_DIR := infra/supabase/migrations

# Usage: make migration name=add_users_table
.PHONY: migration
migration:
	@test -n "$(name)" || (echo "Error: provide a name, e.g. make migration name=add_users_table" && exit 1)
	@ts=$$(date +%Y%m%d%H%M%S) && \
	file="$(MIGRATIONS_DIR)/$${ts}_$(name).sql" && \
	touch "$$file" && \
	echo "Created $$file"

# Run: make db-push
.PHONY: db-push
db-push:
	cd infra && supabase db push
