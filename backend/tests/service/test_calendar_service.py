from datetime import date
from unittest.mock import MagicMock

import pytest

from src.errors import InternalServerException, NotFoundException
from src.repository.repository import Repository
from src.service.calendar_service import CalendarService

FAKE_USER_ID = "user-111"
FAKE_HOUSEHOLD_ID = "hh-222"
FAKE_HOUSEHOLD = {"id": FAKE_HOUSEHOLD_ID, "name": "Test Home"}
FAKE_EVENT_ID = "event-aaa"
FAKE_BIRTHDAY_ID = "bday-aaa"

FAKE_EVENT = {
    "id": FAKE_EVENT_ID,
    "household_id": FAKE_HOUSEHOLD_ID,
    "title": "Dentist",
    "event_date": "2026-09-20",
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "location": "Clinic",
    "description": None,
    "created_by": FAKE_USER_ID,
    "created_at": "2026-09-14T10:00:00+00:00",
    "updated_at": "2026-09-14T10:00:00+00:00",
}

FAKE_BIRTHDAY = {
    "id": FAKE_BIRTHDAY_ID,
    "household_id": FAKE_HOUSEHOLD_ID,
    "person_name": "Ada",
    "birth_month": 9,
    "birth_day": 20,
    "birth_year": 1990,
    "show_year": True,
    "created_by": FAKE_USER_ID,
    "created_at": "2026-09-14T10:00:00+00:00",
    "updated_at": "2026-09-14T10:00:00+00:00",
}


@pytest.fixture
def mock_db():
    db = MagicMock(spec=Repository)
    db.get_household_by_user.return_value = FAKE_HOUSEHOLD
    db.find_events_in_range.return_value = []
    db.find_birthdays_by_household.return_value = []
    db.find_active_task_dots.return_value = []
    return db


@pytest.fixture
def service(mock_db):
    return CalendarService(mock_db)


class TestGetFeed:
    async def test_returns_all_three_sections_scoped_to_household(self, service, mock_db):
        mock_db.find_events_in_range.return_value = [dict(FAKE_EVENT)]

        result = await service.get_feed(FAKE_USER_ID, date(2026, 9, 1), date(2026, 9, 30))

        assert result["events"] == [{**FAKE_EVENT, "source": "native"}]
        assert result["birthdays"] == []
        assert result["chore_dots"] == {}
        assert result["range_from"] == date(2026, 9, 1)
        assert result["range_to"] == date(2026, 9, 30)
        mock_db.find_events_in_range.assert_called_once_with(FAKE_HOUSEHOLD_ID, "2026-09-01", "2026-09-30")
        mock_db.find_birthdays_by_household.assert_called_once_with(FAKE_HOUSEHOLD_ID)
        mock_db.find_active_task_dots.assert_called_once_with(FAKE_HOUSEHOLD_ID, "2026-09-01", "2026-09-30")

    async def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            await service.get_feed(FAKE_USER_ID, date(2026, 9, 1), date(2026, 9, 30))

    async def test_does_not_query_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            await service.get_feed(FAKE_USER_ID, date(2026, 9, 1), date(2026, 9, 30))

        mock_db.find_events_in_range.assert_not_called()
        mock_db.find_birthdays_by_household.assert_not_called()
        mock_db.find_active_task_dots.assert_not_called()

    async def test_rejects_inverted_range(self, service, mock_db):
        # The boundary rejects this first; reaching the service means a caller bypassed it.
        with pytest.raises(InternalServerException):
            await service.get_feed(FAKE_USER_ID, date(2026, 9, 30), date(2026, 9, 1))

    async def test_passes_through_a_large_result_set_unmodified(self, service, mock_db):
        # Detecting a truncated result set is the repository's job (it owns the row caps); the
        # service just needs to pass whatever it gets back through unchanged.
        mock_db.find_events_in_range.return_value = [dict(FAKE_EVENT)] * 1000

        result = await service.get_feed(FAKE_USER_ID, date(2026, 9, 1), date(2026, 9, 30))

        assert len(result["events"]) == 1000

    async def test_tags_every_native_event_with_its_source(self, service, mock_db):
        mock_db.find_events_in_range.return_value = [dict(FAKE_EVENT)]

        result = await service.get_feed(FAKE_USER_ID, date(2026, 9, 1), date(2026, 9, 30))

        assert all(e["source"] == "native" for e in result["events"])

    async def test_single_day_range_is_allowed(self, service, mock_db):
        result = await service.get_feed(FAKE_USER_ID, date(2026, 9, 14), date(2026, 9, 14))

        assert result["range_from"] == result["range_to"] == date(2026, 9, 14)


class TestExpandBirthdays:
    def test_projects_birthday_onto_requested_year(self):
        rows = [dict(FAKE_BIRTHDAY)]

        result = CalendarService._expand_birthdays(rows, date(2026, 9, 1), date(2026, 9, 30))

        assert len(result) == 1
        assert result[0]["occurrence_date"] == date(2026, 9, 20)
        assert result[0]["person_name"] == "Ada"
        assert result[0]["birth_month"] == 9
        assert result[0]["birth_day"] == 20
        assert result[0]["birth_year"] == 1990
        assert result[0]["id"] == FAKE_BIRTHDAY_ID

    def test_computes_age_from_occurrence_year(self):
        result = CalendarService._expand_birthdays([dict(FAKE_BIRTHDAY)], date(2026, 9, 1), date(2026, 9, 30))

        assert result[0]["age"] == 36

    def test_age_is_none_when_show_year_false(self):
        row = {**FAKE_BIRTHDAY, "show_year": False}

        result = CalendarService._expand_birthdays([row], date(2026, 9, 1), date(2026, 9, 30))

        assert result[0]["age"] is None
        assert result[0]["show_year"] is False

    def test_excludes_occurrence_outside_range(self):
        result = CalendarService._expand_birthdays([dict(FAKE_BIRTHDAY)], date(2026, 10, 1), date(2026, 10, 31))

        assert result == []

    def test_emits_one_occurrence_per_year_in_multi_year_range(self):
        result = CalendarService._expand_birthdays([dict(FAKE_BIRTHDAY)], date(2026, 1, 1), date(2027, 12, 31))

        assert [o["occurrence_date"] for o in result] == [date(2026, 9, 20), date(2027, 9, 20)]

    def test_feb_29_falls_back_to_feb_28_in_non_leap_year(self):
        row = {**FAKE_BIRTHDAY, "birth_month": 2, "birth_day": 29, "birth_year": 2000}

        result = CalendarService._expand_birthdays([row], date(2026, 2, 1), date(2026, 2, 28))

        assert len(result) == 1
        assert result[0]["occurrence_date"] == date(2026, 2, 28)

    def test_feb_29_stays_on_feb_29_in_leap_year(self):
        row = {**FAKE_BIRTHDAY, "birth_month": 2, "birth_day": 29, "birth_year": 2000}

        result = CalendarService._expand_birthdays([row], date(2028, 2, 1), date(2028, 2, 29))

        assert result[0]["occurrence_date"] == date(2028, 2, 29)

    def test_sorts_by_date_then_name(self):
        rows = [
            {**FAKE_BIRTHDAY, "id": "b1", "person_name": "Zoe"},
            {**FAKE_BIRTHDAY, "id": "b2", "person_name": "Ada"},
            {**FAKE_BIRTHDAY, "id": "b3", "person_name": "Mia", "birth_day": 5},
        ]

        result = CalendarService._expand_birthdays(rows, date(2026, 9, 1), date(2026, 9, 30))

        assert [(o["occurrence_date"], o["person_name"]) for o in result] == [
            (date(2026, 9, 5), "Mia"),
            (date(2026, 9, 20), "Ada"),
            (date(2026, 9, 20), "Zoe"),
        ]

    def test_returns_empty_for_no_rows(self):
        assert CalendarService._expand_birthdays([], date(2026, 9, 1), date(2026, 9, 30)) == []

    def test_skips_occurrences_before_the_person_was_born(self):
        row = {**FAKE_BIRTHDAY, "birth_year": 2026}

        result = CalendarService._expand_birthdays([row], date(2020, 1, 1), date(2020, 12, 31))

        assert result == []

    def test_includes_the_birth_year_itself_at_age_zero(self):
        row = {**FAKE_BIRTHDAY, "birth_year": 2026}

        result = CalendarService._expand_birthdays([row], date(2026, 1, 1), date(2026, 12, 31))

        assert len(result) == 1
        assert result[0]["age"] == 0

    def test_never_produces_a_negative_age(self):
        row = {**FAKE_BIRTHDAY, "birth_year": 2026}

        result = CalendarService._expand_birthdays([row], date(2020, 1, 1), date(2027, 12, 31))

        assert all(o["age"] >= 0 for o in result)

    def test_unknown_birth_year_keeps_every_occurrence_in_range(self):
        # The core UX case: the day and month are known but the year isn't, and the user
        # shouldn't be forced to guess it. Every occurrence in the requested range is kept,
        # regardless of how far back the range goes.
        row = {**FAKE_BIRTHDAY, "birth_year": None, "show_year": False}

        result = CalendarService._expand_birthdays([row], date(1950, 9, 1), date(1950, 9, 30))

        assert len(result) == 1
        assert result[0]["occurrence_date"] == date(1950, 9, 20)

    def test_unknown_birth_year_never_has_an_age(self):
        row = {**FAKE_BIRTHDAY, "birth_year": None, "show_year": False}

        result = CalendarService._expand_birthdays([row], date(2026, 9, 1), date(2026, 9, 30))

        assert result[0]["age"] is None
        assert result[0]["birth_year"] is None


class TestAggregateChoreDots:
    def test_groups_tasks_by_due_date(self):
        rows = [
            {"id": "t1", "name": "Trash", "due_date": "2026-09-14"},
            {"id": "t2", "name": "Vacuum", "due_date": "2026-09-14"},
            {"id": "t3", "name": "Dishes", "due_date": "2026-09-15"},
        ]

        result = CalendarService._aggregate_chore_dots(rows)

        assert result[date(2026, 9, 14)] == {"count": 2, "titles": ["Trash", "Vacuum"]}
        assert result[date(2026, 9, 15)] == {"count": 1, "titles": ["Dishes"]}

    def test_returns_empty_for_no_rows(self):
        assert CalendarService._aggregate_chore_dots([]) == {}


class TestCreateEvent:
    async def test_creates_event_scoped_to_household(self, service, mock_db):
        mock_db.create_event.return_value = FAKE_EVENT

        result = await service.create_event(
            FAKE_USER_ID,
            title="Dentist",
            event_date="2026-09-20",
            start_time="09:00:00",
            end_time="10:00:00",
            location="Clinic",
            description=None,
        )

        assert result == FAKE_EVENT
        mock_db.create_event.assert_called_once_with(
            household_id=FAKE_HOUSEHOLD_ID,
            title="Dentist",
            event_date="2026-09-20",
            start_time="09:00:00",
            end_time="10:00:00",
            location="Clinic",
            description=None,
            created_by=FAKE_USER_ID,
        )

    async def test_strips_whitespace_from_text_fields(self, service, mock_db):
        mock_db.create_event.return_value = FAKE_EVENT

        await service.create_event(
            FAKE_USER_ID,
            title="  Dentist  ",
            event_date="2026-09-20",
            start_time=None,
            end_time=None,
            location="  Clinic  ",
            description="  Bring card  ",
        )

        _, kwargs = mock_db.create_event.call_args
        assert kwargs["title"] == "Dentist"
        assert kwargs["location"] == "Clinic"
        assert kwargs["description"] == "Bring card"

    async def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            await service.create_event(
                FAKE_USER_ID,
                title="Dentist",
                event_date="2026-09-20",
                start_time=None,
                end_time=None,
                location=None,
                description=None,
            )


class TestUpdateEvent:
    async def test_updates_event_scoped_to_household(self, service, mock_db):
        mock_db.update_event.return_value = {**FAKE_EVENT, "title": "Doctor"}

        result = await service.update_event(FAKE_USER_ID, FAKE_EVENT_ID, {"title": "Doctor"})

        assert result["title"] == "Doctor"
        mock_db.update_event.assert_called_once_with(
            FAKE_EVENT_ID, {"title": "Doctor"}, household_id=FAKE_HOUSEHOLD_ID
        )

    async def test_strips_title(self, service, mock_db):
        mock_db.update_event.return_value = FAKE_EVENT

        await service.update_event(FAKE_USER_ID, FAKE_EVENT_ID, {"title": "  Doctor  "})

        args, _ = mock_db.update_event.call_args
        assert args[1]["title"] == "Doctor"

    async def test_raises_when_zero_rows_updated(self, service, mock_db):
        mock_db.update_event.return_value = None

        with pytest.raises(NotFoundException):
            await service.update_event(FAKE_USER_ID, FAKE_EVENT_ID, {"title": "Doctor"})

    async def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            await service.update_event(FAKE_USER_ID, FAKE_EVENT_ID, {"title": "Doctor"})

    async def test_does_not_prefetch_before_update(self, service, mock_db):
        mock_db.update_event.return_value = FAKE_EVENT

        await service.update_event(FAKE_USER_ID, FAKE_EVENT_ID, {"title": "Doctor"})

        assert [call[0] for call in mock_db.method_calls] == ["get_household_by_user", "update_event"]

    async def test_does_not_mutate_caller_dict(self, service, mock_db):
        mock_db.update_event.return_value = FAKE_EVENT
        original = {"title": "  Doctor  "}

        await service.update_event(FAKE_USER_ID, FAKE_EVENT_ID, original)

        assert original == {"title": "  Doctor  "}


class TestDeleteEvent:
    async def test_deletes_event_scoped_to_household(self, service, mock_db):
        mock_db.delete_event.return_value = True

        await service.delete_event(FAKE_USER_ID, FAKE_EVENT_ID)

        mock_db.delete_event.assert_called_once_with(FAKE_EVENT_ID, household_id=FAKE_HOUSEHOLD_ID)

    async def test_raises_when_zero_rows_deleted(self, service, mock_db):
        mock_db.delete_event.return_value = False

        with pytest.raises(NotFoundException):
            await service.delete_event(FAKE_USER_ID, FAKE_EVENT_ID)

    async def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            await service.delete_event(FAKE_USER_ID, FAKE_EVENT_ID)


class TestCreateBirthday:
    async def test_creates_birthday_scoped_to_household(self, service, mock_db):
        mock_db.create_birthday.return_value = FAKE_BIRTHDAY

        result = await service.create_birthday(
            FAKE_USER_ID, person_name="Ada", birth_month=9, birth_day=20, birth_year=1990, show_year=True
        )

        assert result == FAKE_BIRTHDAY
        mock_db.create_birthday.assert_called_once_with(
            household_id=FAKE_HOUSEHOLD_ID,
            person_name="Ada",
            birth_month=9,
            birth_day=20,
            birth_year=1990,
            show_year=True,
            created_by=FAKE_USER_ID,
        )

    async def test_creates_birthday_with_unknown_year(self, service, mock_db):
        mock_db.create_birthday.return_value = {**FAKE_BIRTHDAY, "birth_year": None, "show_year": False}

        await service.create_birthday(
            FAKE_USER_ID, person_name="Ada", birth_month=9, birth_day=20, birth_year=None, show_year=False
        )

        _, kwargs = mock_db.create_birthday.call_args
        assert kwargs["birth_year"] is None

    async def test_strips_person_name(self, service, mock_db):
        mock_db.create_birthday.return_value = FAKE_BIRTHDAY

        await service.create_birthday(
            FAKE_USER_ID, person_name="  Ada  ", birth_month=9, birth_day=20, birth_year=1990, show_year=True
        )

        _, kwargs = mock_db.create_birthday.call_args
        assert kwargs["person_name"] == "Ada"

    async def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            await service.create_birthday(
                FAKE_USER_ID, person_name="Ada", birth_month=9, birth_day=20, birth_year=1990, show_year=True
            )


class TestUpdateBirthday:
    async def test_updates_birthday_scoped_to_household(self, service, mock_db):
        mock_db.update_birthday.return_value = {**FAKE_BIRTHDAY, "person_name": "Grace"}

        result = await service.update_birthday(FAKE_USER_ID, FAKE_BIRTHDAY_ID, {"person_name": "Grace"})

        assert result["person_name"] == "Grace"
        mock_db.update_birthday.assert_called_once_with(
            FAKE_BIRTHDAY_ID, {"person_name": "Grace"}, household_id=FAKE_HOUSEHOLD_ID
        )

    async def test_strips_person_name(self, service, mock_db):
        mock_db.update_birthday.return_value = FAKE_BIRTHDAY

        await service.update_birthday(FAKE_USER_ID, FAKE_BIRTHDAY_ID, {"person_name": "  Grace  "})

        args, _ = mock_db.update_birthday.call_args
        assert args[1]["person_name"] == "Grace"

    async def test_raises_when_zero_rows_updated(self, service, mock_db):
        mock_db.update_birthday.return_value = None

        with pytest.raises(NotFoundException):
            await service.update_birthday(FAKE_USER_ID, FAKE_BIRTHDAY_ID, {"person_name": "Grace"})

    async def test_does_not_prefetch_before_update(self, service, mock_db):
        mock_db.update_birthday.return_value = FAKE_BIRTHDAY

        await service.update_birthday(FAKE_USER_ID, FAKE_BIRTHDAY_ID, {"person_name": "Grace"})

        assert [call[0] for call in mock_db.method_calls] == ["get_household_by_user", "update_birthday"]

    async def test_does_not_mutate_caller_dict(self, service, mock_db):
        mock_db.update_birthday.return_value = FAKE_BIRTHDAY
        original = {"person_name": "  Grace  "}

        await service.update_birthday(FAKE_USER_ID, FAKE_BIRTHDAY_ID, original)

        assert original == {"person_name": "  Grace  "}

    async def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            await service.update_birthday(FAKE_USER_ID, FAKE_BIRTHDAY_ID, {"person_name": "Grace"})


class TestDeleteBirthday:
    async def test_deletes_birthday_scoped_to_household(self, service, mock_db):
        mock_db.delete_birthday.return_value = True

        await service.delete_birthday(FAKE_USER_ID, FAKE_BIRTHDAY_ID)

        mock_db.delete_birthday.assert_called_once_with(FAKE_BIRTHDAY_ID, household_id=FAKE_HOUSEHOLD_ID)

    async def test_raises_when_zero_rows_deleted(self, service, mock_db):
        mock_db.delete_birthday.return_value = False

        with pytest.raises(NotFoundException):
            await service.delete_birthday(FAKE_USER_ID, FAKE_BIRTHDAY_ID)

    async def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            await service.delete_birthday(FAKE_USER_ID, FAKE_BIRTHDAY_ID)
