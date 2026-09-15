import asyncio
from datetime import date

from src.errors import InternalServerException, NotFoundException
from src.repository.repository import Repository
from src.utils.logger import logger as log


class CalendarService:
    def __init__(self, db: Repository):
        self.db = db

    async def _resolve_household(self, user_id: str) -> str:
        household = await self.db.get_household_by_user(user_id)
        if not household:
            log.warning(f"User {user_id} attempted calendar operation without a household")
            raise NotFoundException("You must belong to a household to use the calendar.")
        return household["id"]

    # --- feed ---

    async def get_feed(self, user_id: str, range_from: date, range_to: date) -> dict:
        if range_to < range_from:
            log.warning(f"get_feed called with inverted range [{range_from}..{range_to}] for user {user_id}")
            raise InternalServerException("Invalid calendar range.")
        household_id = await self._resolve_household(user_id)
        log.info(f"Loading calendar feed for household {household_id} [{range_from}..{range_to}]")

        # Three independent reads — run them concurrently instead of paying for three
        # round-trips in series. (Not a fit for a thread pool: these are non-blocking
        # `await`s on the async DB client already, not CPU-bound or blocking I/O work.)
        events, birthdays_raw, chore_rows = await asyncio.gather(
            self.db.find_events_in_range(household_id, str(range_from), str(range_to)),
            self.db.find_birthdays_by_household(household_id),
            self.db.find_active_task_dots(household_id, str(range_from), str(range_to)),
        )

        birthdays = self._expand_birthdays(birthdays_raw, range_from, range_to)
        chore_dots = self._aggregate_chore_dots(chore_rows)

        # Tag each native event with its source so it merges into one `events` list alongside
        # future sources (Google, Phase 2 — see feature-plan-calendar.md §8) without the client
        # needing a separate array per integration. Native events are already date-ordered by
        # the query; once a second source is merged in, this needs to sort the combined list.
        native_events = [{**event, "source": "native"} for event in events]

        return {
            "events": native_events,
            "birthdays": birthdays,
            "chore_dots": chore_dots,
            "range_from": range_from,
            "range_to": range_to,
        }

    @staticmethod
    def _expand_birthdays(rows: list[dict], range_from: date, range_to: date) -> list[dict]:
        """Project each birthday onto every year in [range_from, range_to] and keep occurrences inside the range.

        birth_year may be None (the year is often unknown to whoever added the birthday) — in
        that case every occurrence in range is kept and age is always null, since there's nothing
        to count age from.
        """
        occurrences: list[dict] = []
        for row in rows:
            month, day = row["birth_month"], row["birth_day"]
            birth_year = row["birth_year"]
            show_year = bool(row["show_year"])
            for year in range(range_from.year, range_to.year + 1):
                if birth_year is not None and year < birth_year:
                    continue  # a birthday has no occurrences before the person was born
                # Handle Feb 29: fall back to Feb 28 in years where it doesn't occur.
                try:
                    occ = date(year, month, day)
                except ValueError:
                    occ = date(year, 2, 28)
                if range_from <= occ <= range_to:
                    age = (year - birth_year) if (show_year and birth_year is not None) else None
                    occurrences.append(
                        {
                            "id": row["id"],
                            "person_name": row["person_name"],
                            "birth_month": month,
                            "birth_day": day,
                            "birth_year": birth_year,
                            "occurrence_date": occ,
                            "age": age,
                            "show_year": show_year,
                        }
                    )
        occurrences.sort(key=lambda o: (o["occurrence_date"], o["person_name"]))
        return occurrences

    @staticmethod
    def _aggregate_chore_dots(rows: list[dict]) -> dict[date, dict]:
        dots: dict[date, dict] = {}
        for row in rows:
            due = date.fromisoformat(row["due_date"])
            bucket = dots.setdefault(due, {"count": 0, "titles": []})
            bucket["count"] += 1
            bucket["titles"].append(row["name"])
        return dots

    # --- events ---

    async def create_event(
        self,
        user_id: str,
        title: str,
        event_date: str,
        start_time: str | None,
        end_time: str | None,
        location: str | None,
        description: str | None,
    ) -> dict:
        household_id = await self._resolve_household(user_id)
        log.info(f"Creating event '{title}' on {event_date} for household {household_id}")
        return await self.db.create_event(
            household_id=household_id,
            title=title.strip(),
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            location=location.strip() if location else None,
            description=description.strip() if description else None,
            created_by=user_id,
        )

    async def update_event(self, user_id: str, event_id: str, updates: dict) -> dict:
        household_id = await self._resolve_household(user_id)
        updates = dict(updates)
        if "title" in updates and updates["title"] is not None:
            updates["title"] = updates["title"].strip()
        log.info(f"Updating event {event_id} in household {household_id} (fields: {list(updates.keys()) or ['none']})")
        result = await self.db.update_event(event_id, updates, household_id=household_id)
        if not result:
            log.warning(f"Event {event_id} not found in household {household_id}")
            raise NotFoundException("Event not found.")
        return result

    async def delete_event(self, user_id: str, event_id: str) -> None:
        household_id = await self._resolve_household(user_id)
        log.info(f"Deleting event {event_id} from household {household_id}")
        deleted = await self.db.delete_event(event_id, household_id=household_id)
        if not deleted:
            log.warning(f"Event {event_id} not found in household {household_id}")
            raise NotFoundException("Event not found.")

    # --- birthdays ---

    async def create_birthday(
        self,
        user_id: str,
        person_name: str,
        birth_month: int,
        birth_day: int,
        birth_year: int | None,
        show_year: bool,
    ) -> dict:
        household_id = await self._resolve_household(user_id)
        log.info(f"Creating birthday for '{person_name}' in household {household_id}")
        return await self.db.create_birthday(
            household_id=household_id,
            person_name=person_name.strip(),
            birth_month=birth_month,
            birth_day=birth_day,
            birth_year=birth_year,
            show_year=show_year,
            created_by=user_id,
        )

    async def update_birthday(self, user_id: str, birthday_id: str, updates: dict) -> dict:
        household_id = await self._resolve_household(user_id)
        updates = dict(updates)  # copy — don't mutate the caller's dict
        if "person_name" in updates and updates["person_name"] is not None:
            updates["person_name"] = updates["person_name"].strip()
        log.info(
            f"Updating birthday {birthday_id} in household {household_id} "
            f"(fields: {list(updates.keys()) or ['none']})"
        )
        result = await self.db.update_birthday(birthday_id, updates, household_id=household_id)
        if not result:
            log.warning(f"Birthday {birthday_id} not found in household {household_id}")
            raise NotFoundException("Birthday not found.")
        return result

    async def delete_birthday(self, user_id: str, birthday_id: str) -> None:
        household_id = await self._resolve_household(user_id)
        log.info(f"Deleting birthday {birthday_id} from household {household_id}")
        deleted = await self.db.delete_birthday(birthday_id, household_id=household_id)
        if not deleted:
            log.warning(f"Birthday {birthday_id} not found in household {household_id}")
            raise NotFoundException("Birthday not found.")
