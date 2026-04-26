class HealthCheckDataService:
    """Minimal availability checks for the readiness probe.

    Extend ``availability`` to verify external dependencies (e.g. database
    connections, cache) as the service grows.
    """

    def availability(self) -> dict[str, bool]:
        return {
            "service": True,
            # TODO: add more dependencies, e.g. db
        }

    def close(self) -> None:
        pass
