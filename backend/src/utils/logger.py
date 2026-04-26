"""
Structured logger built on loguru, designed for Loki ingestion (JSON) with
optional ANSI colouring for human readability in k8s / Argo CD.

How colours + Loki coexist
---------------------------
ANSI escape codes wrap the **whole JSON line** — they are placed before and
after the ``{...}`` blob, so the JSON itself remains valid.  Loki's Promtail
has a built-in ``decolorize`` pipeline stage that strips these codes before
parsing:

    # promtail pipeline_stages:
    - decolorize: {}
    - json:
        expressions:
          level:     level
          service:   service
          message:   message
          endpoint:  endpoint

Colour strategy
---------------
- ``COLORIZE_LOGS=true``  → colours on  (use this in k8s / Argo CD)
- ``COLORIZE_LOGS=false`` → colours off (CI, file sinks, etc.)
- unset                   → auto-detect via ``sys.stdout.isatty()``
  (works for local dev; not reliable in k8s because stdout is not a TTY)

Each log level gets its own line colour so you can spot WARNINGs and ERRORs
at a glance while scrolling through kubectl/Argo logs.

Quick start
-----------
Call ``setup_json_logging()`` **once** at application startup, then import
and use ``logger`` everywhere:

    # main.py / lifespan
    from bm_common.core.json_log import setup_json_logging, logger

    setup_json_logging(service="my-api", environment="production")
    logger.info("Application started")

    # ── local dev: human-readable coloured output ──────────────────────────
    from bm_common.core.json_log import setup_pretty_logging, logger

    setup_pretty_logging()
    logger.info("Application started")

Adding request context (FastAPI example)
-----------------------------------------
``logger.contextualize()`` propagates bound values through the entire async
call chain — every log inside the ``with`` block automatically carries them:

    from fastapi import FastAPI, Request
    from bm_common.core.json_log import logger

    app = FastAPI()

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        with logger.contextualize(
            endpoint=request.url.path,
            method=request.method,
            request_id=request.headers.get("x-request-id"),
        ):
            response = await call_next(request)
            logger.info("Request completed", status_code=response.status_code)
            return response

    # Inside any route — no extra work needed:
    @app.get("/users")
    async def list_users():
        logger.info("Fetching users")
        # → automatically includes endpoint, method, request_id

One-off binding (without middleware)
--------------------------------------
    logger.bind(endpoint="/jobs/run").info("Job triggered")
"""

import json
import os
import sys

from datetime import timezone
from loguru import logger

MAX_LOG_LENGTH = 5000

# ── ANSI colour codes ──────────────────────────────────────────────────────

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_CYAN = "\033[36m"

_LEVEL_STYLES: dict[str, str] = {
    "TRACE": "\033[37m",  # white
    "DEBUG": "\033[36m",  # cyan
    "INFO": "\033[32m",  # green
    "SUCCESS": "\033[32;1m",  # bold green
    "WARNING": "\033[33m",  # yellow
    "ERROR": "\033[31m",  # red
    "CRITICAL": "\033[1;31m",  # bold red
}


def _resolve_colorize(stream=sys.stdout) -> bool:
    """Decide whether to emit ANSI codes.

    Priority:
    1. ``COLORIZE_LOGS`` env var (``"true"`` / ``"false"``) — explicit override,
       needed in k8s where ``isatty()`` always returns False.
    2. ``stream.isatty()`` — automatic detection for local terminals.
    """
    env = os.getenv("COLORIZE_LOGS", "").lower()  # TODO: get it form settings
    if env == "true":
        return True
    if env == "false":
        return False
    return hasattr(stream, "isatty") and stream.isatty()


# ── JSON sink (Loki / production) ─────────────────────────────────────────


def _build_json_sink(
    service: str | None,
    environment: str | None,
    max_message_length: int,
    extra_labels: dict,
    colorize: bool,
):
    """Return a loguru sink that writes one (optionally coloured) JSON line per record."""

    def sink(message):
        record = message.record

        msg = record["message"]
        if len(msg) > max_message_length:
            msg = msg[:max_message_length] + "... (truncated)"

        entry: dict = {
            "timestamp": record["time"].astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record["level"].name,
            "logger": record["name"],
            "message": msg,
            "filename": record["file"].name,
            "line": record["line"],
            "function": record["function"],
        }

        if service:
            entry["service"] = service
        if environment:
            entry["environment"] = environment
        if extra_labels:
            entry.update(extra_labels)

        # Values bound via logger.bind() or logger.contextualize()
        bound = record.get("extra", {})
        if bound:
            entry.update(bound)

        if record["exception"]:
            entry["exception"] = str(record["exception"])

        line = json.dumps(entry, default=str)

        # Wrap the entire JSON line in the level's ANSI colour.
        # The JSON content itself is untouched, so Loki can strip the codes
        # with the `decolorize` pipeline stage and parse clean JSON.
        if colorize:
            color = _LEVEL_STYLES.get(record["level"].name, "")
            line = f"{color}{line}{_RESET}"

        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    return sink


def setup_json_logging(
    service: str | None = None,
    environment: str | None = None,
    level: str | None = None,
    max_message_length: int = MAX_LOG_LENGTH,
    **extra_labels,
) -> None:
    """Configure loguru to emit one JSON line per record to stdout.

    Lines are optionally wrapped in ANSI colour codes (controlled by the
    ``COLORIZE_LOGS`` env var) so you can read them in k8s / Argo CD while
    Loki still parses valid JSON after its ``decolorize`` pipeline stage.

    Call **once** at application startup.

    Args:
        service: Service name label. Falls back to ``SERVICE_NAME`` env var.
        environment: Deployment environment. Falls back to ``ENVIRONMENT`` env var.
        level: Minimum log level string (e.g. ``"INFO"``). Falls back to
            ``LOG_LEVEL`` env var, then ``"INFO"``.
        max_message_length: Truncate the ``message`` field beyond this many chars.
        **extra_labels: Static key/value pairs added to every log record.

    Environment variables
    ---------------------
    LOG_LEVEL       : log level (default: INFO)
    SERVICE_NAME    : service label
    ENVIRONMENT     : environment label
    COLORIZE_LOGS   : "true" / "false" — force colour on or off.
                      Set to "true" in your k8s Deployment manifest.
                      Defaults to auto-detect via isatty() (unreliable in k8s).
    """
    _level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    _service = service or os.getenv("SERVICE_NAME")
    _environment = environment or os.getenv("ENVIRONMENT")
    _colorize = _resolve_colorize(sys.stdout)

    logger.remove()
    logger.add(
        _build_json_sink(_service, _environment, max_message_length, extra_labels, _colorize),
        level=_level,
        format="{message}",  # all formatting happens inside the sink
        backtrace=False,
        diagnose=False,
    )


# ── Pretty sink (coloured / local development) ────────────────────────────


def _build_pretty_sink(max_message_length: int, colorize: bool):
    """Return a loguru sink that writes a coloured, human-readable line to stderr."""

    def _c(code: str, text: str) -> str:
        return f"{code}{text}{_RESET}" if colorize else text

    def sink(message):
        record = message.record
        level = record["level"].name
        lvl_color = _LEVEL_STYLES.get(level, "")

        msg = record["message"]
        if len(msg) > max_message_length:
            msg = msg[:max_message_length] + "... (truncated)"

        ts = record["time"].astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        location = f"{record['name']}:{record['line']}"

        # Bound context from logger.bind() / logger.contextualize()
        bound = record.get("extra", {})
        context_str = ""
        if bound:
            pairs = "  ".join(f"{k}={v!r}" for k, v in bound.items())
            context_str = "  " + _c(_DIM, f"[{pairs}]")

        line = (
            _c(_GREEN, ts)
            + "  "
            + _c(_BOLD + lvl_color, f"{level:<8}")
            + "  "
            + _c(_CYAN, location)
            + "  "
            + _c(lvl_color, msg)
            + context_str
        )

        sys.stderr.write(line + "\n")

        if record["exception"]:
            sys.stderr.write(str(record["exception"]) + "\n")

        sys.stderr.flush()

    return sink


def setup_pretty_logging(
    level: str | None = None,
    max_message_length: int = MAX_LOG_LENGTH,
) -> None:
    """Configure loguru to emit coloured, human-readable logs to stderr.

    Intended for local development. Colours are resolved via ``COLORIZE_LOGS``
    env var, falling back to ``sys.stderr.isatty()``.

    Call **once** at application startup.

    Args:
        level: Minimum log level string (e.g. ``"DEBUG"``). Falls back to
            ``LOG_LEVEL`` env var, then ``"INFO"``.
        max_message_length: Truncate the message beyond this many characters.
    """
    _level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    _colorize = _resolve_colorize(sys.stderr)

    logger.remove()
    logger.add(
        _build_pretty_sink(max_message_length, _colorize),
        level=_level,
        format="{message}",
        backtrace=True,
        diagnose=True,
    )
