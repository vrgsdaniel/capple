from src.db.db import DB


class HealthCheckDataService:
    """Minimal availability checks for the readiness probe.

    Extend ``availability`` to verify external dependencies (e.g. database
    connections, cache) as the service grows.
    """

    def __init__(self, db: DB):
        self.db = db

    def availability(self) -> dict[str, bool]:
        return {
            "service": True,
            "database": self.db.is_alive(),
        }
