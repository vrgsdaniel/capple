MIGRATIONS_DIR := infra/supabase/migrations

# Usage: make migration name=add_users_table
.PHONY: migration
migration:
	@test -n "$(name)" || (echo "Error: provide a name, e.g. make migration name=add_users_table" && exit 1)
	@ts=$$(date +%Y%m%d%H%M%S) && \
	file="$(MIGRATIONS_DIR)/$${ts}_$(name).sql" && \
	touch "$$file" && \
	echo "Created $$file"

# Run: make be-dev
.PHONY: be-dev
be-dev:
	cd backend && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# Run: make fe-dev [port=3000]
.PHONY: fe-dev
fe-dev:
	cd frontend && pnpm run dev $(if $(port),-- --port $(port),)

# Run: make docker-build  (runs test stage, fails if lint/tests fail)
.PHONY: docker-build
docker-build:
	docker build --target test -t capple-backend:test ./backend

# Run: make docker-up
.PHONY: docker-up
docker-up:
	docker compose up --build

# Run: make docker-down
.PHONY: docker-down
docker-down:
	docker compose down

# Run: make lint
.PHONY: lint
lint:
	cd backend && uv run ruff check .

# Run: make db-push
.PHONY: db-push
db-push:
	cd infra && supabase db push
