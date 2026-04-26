from src.db.client import DB


class UserService:
    """Service for managing user-related operations."""

    def __init__(self, db: DB):
        self.db = db

    def get_first_id(self) -> dict[str, bool]:
        return self.db.get_first_id("profiles") is not None
