from src.repository.repository import Repository


class HealthCheckDataService:
    """Minimal availability checks for the readiness probe."""

    def __init__(self, db: Repository):
        self.db = db

    async def availability(self) -> dict[str, bool]:
        return {
            "service": True,
            "database": await self.db.is_alive(),
        }
