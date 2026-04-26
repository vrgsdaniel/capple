# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# ── Stage 2: test ─────────────────────────────────────────────────────────────
FROM builder AS test

RUN uv sync --frozen
RUN uv run pytest

# ── Stage 3: final ────────────────────────────────────────────────────────────
FROM python:3.13-slim AS final

WORKDIR /app

COPY --from=builder /app/.venv .venv
COPY --from=builder /app/app ./app

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
