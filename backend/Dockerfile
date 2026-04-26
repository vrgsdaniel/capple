# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# ── Stage 2: test ─────────────────────────────────────────────────────────────
FROM builder AS test

RUN uv sync --frozen --group test
RUN .venv/bin/ruff check .
RUN .venv/bin/pytest

# ── Stage 3: final ────────────────────────────────────────────────────────────
FROM python:3.13-slim AS final

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY --from=builder /app/src ./src

CMD ["/app/.venv/bin/python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
