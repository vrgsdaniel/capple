from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers.api.calendar import get_calendar_service, router
from src.controllers.api.users import get_current_user
from src.errors import NotFoundException, ValidationException
from src.models.calendar import MAX_DESCRIPTION_LENGTH, MAX_LOCATION_LENGTH, MAX_TITLE_LENGTH
from src.models.user import CurrentUser
from src.service.calendar_service import CalendarService

FAKE_USER_ID = "00000000-0000-0000-0000-000000000001"
FAKE_USER = CurrentUser(id=FAKE_USER_ID)
FAKE_HOUSEHOLD_ID = "00000000-0000-0000-0000-000000000002"
FAKE_EVENT_ID = "00000000-0000-0000-0000-000000000003"
FAKE_BIRTHDAY_ID = "00000000-0000-0000-0000-000000000004"

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

FAKE_FEED = {
    "events": [{**FAKE_EVENT, "source": "native"}],
    "birthdays": [
        {
            "id": FAKE_BIRTHDAY_ID,
            "person_name": "Ada",
            "birth_month": 9,
            "birth_day": 20,
            "birth_year": 1990,
            "occurrence_date": "2026-09-20",
            "age": 36,
            "show_year": True,
        }
    ],
    "chore_dots": {"2026-09-14": {"count": 2, "titles": ["Trash", "Vacuum"]}},
    "range_from": "2026-09-01",
    "range_to": "2026-09-30",
}


@pytest.fixture
def mock_service():
    return MagicMock(spec=CalendarService)


@pytest.fixture
def client(mock_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_calendar_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    return TestClient(app)


class TestGetCalendarFeed:
    def test_returns_200_with_all_sections(self, client, mock_service):
        mock_service.get_feed.return_value = FAKE_FEED

        resp = client.get("/api/calendar/events?from=2026-09-01&to=2026-09-30")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["events"]) == 1
        assert body["events"][0]["source"] == "native"
        assert body["birthdays"][0]["age"] == 36
        assert body["chore_dots"]["2026-09-14"]["count"] == 2

    def test_passes_parsed_dates_to_service(self, client, mock_service):
        mock_service.get_feed.return_value = FAKE_FEED

        client.get("/api/calendar/events?from=2026-09-01&to=2026-09-30")

        mock_service.get_feed.assert_called_once_with(FAKE_USER_ID, date(2026, 9, 1), date(2026, 9, 30))

    def test_returns_422_when_range_inverted(self, client, mock_service):
        resp = client.get("/api/calendar/events?from=2026-09-30&to=2026-09-01")

        assert resp.status_code == 422
        mock_service.get_feed.assert_not_called()

    def test_returns_422_when_range_too_large(self, client, mock_service):
        resp = client.get("/api/calendar/events?from=2026-01-01&to=2030-01-01")

        assert resp.status_code == 422
        mock_service.get_feed.assert_not_called()

    def test_returns_422_when_range_params_missing(self, client, mock_service):
        resp = client.get("/api/calendar/events")

        assert resp.status_code == 422
        mock_service.get_feed.assert_not_called()

    def test_returns_422_when_date_malformed(self, client, mock_service):
        resp = client.get("/api/calendar/events?from=not-a-date&to=2026-09-30")

        assert resp.status_code == 422
        mock_service.get_feed.assert_not_called()

    def test_accepts_range_at_the_maximum_span(self, client, mock_service):
        mock_service.get_feed.return_value = FAKE_FEED

        resp = client.get("/api/calendar/events?from=2026-01-01&to=2027-02-05")

        assert resp.status_code == 200
        mock_service.get_feed.assert_called_once()

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.get_feed.side_effect = NotFoundException("No household.")

        resp = client.get("/api/calendar/events?from=2026-09-01&to=2026-09-30")

        assert resp.status_code == 404

    def test_serializes_a_google_event_merged_into_the_same_events_list(self, client, mock_service):
        # Not exercised by CalendarService today, but pins the Phase 2 wire shape now so the
        # eventual Google integration has a contract to build against: a google-sourced event
        # rides in the same `events` list as native ones, discriminated by `source`.
        mock_service.get_feed.return_value = {
            **FAKE_FEED,
            "events": [
                *FAKE_FEED["events"],
                {
                    "source": "google",
                    "id": "gcal-event-1",
                    "user_id": FAKE_USER_ID,
                    "calendar_id": "primary",
                    "title": "Team sync",
                    "start": "2026-09-20T09:00:00+00:00",
                    "end": "2026-09-20T10:00:00+00:00",
                },
            ],
        }

        resp = client.get("/api/calendar/events?from=2026-09-01&to=2026-09-30")

        assert resp.status_code == 200
        events = resp.json()["events"]
        assert [e["source"] for e in events] == ["native", "google"]
        assert events[1]["title"] == "Team sync"

    def test_rejects_an_event_with_an_unrecognized_source(self, client, mock_service):
        mock_service.get_feed.return_value = {
            **FAKE_FEED,
            "events": [{**FAKE_EVENT, "source": "outlook"}],
        }

        resp = client.get("/api/calendar/events?from=2026-09-01&to=2026-09-30")

        assert resp.status_code == 500


class TestCreateEvent:
    def test_returns_201_with_minimal_event(self, client, mock_service):
        mock_service.create_event.return_value = FAKE_EVENT

        resp = client.post("/api/calendar/events", json={"title": "Dentist", "event_date": "2026-09-20"})

        assert resp.status_code == 201
        assert resp.json()["title"] == "Dentist"

    def test_passes_all_fields_to_service(self, client, mock_service):
        mock_service.create_event.return_value = FAKE_EVENT

        client.post(
            "/api/calendar/events",
            json={
                "title": "Dentist",
                "event_date": "2026-09-20",
                "start_time": "09:00",
                "end_time": "10:00",
                "location": "Clinic",
                "description": "Bring card",
            },
        )

        mock_service.create_event.assert_called_once_with(
            FAKE_USER_ID,
            title="Dentist",
            event_date="2026-09-20",
            start_time="09:00:00",
            end_time="10:00:00",
            location="Clinic",
            description="Bring card",
        )

    def test_returns_422_when_title_missing(self, client, mock_service):
        resp = client.post("/api/calendar/events", json={"event_date": "2026-09-20"})

        assert resp.status_code == 422
        mock_service.create_event.assert_not_called()

    def test_returns_422_when_title_empty(self, client, mock_service):
        resp = client.post("/api/calendar/events", json={"title": "", "event_date": "2026-09-20"})

        assert resp.status_code == 422
        mock_service.create_event.assert_not_called()

    def test_returns_422_when_end_time_without_start_time(self, client, mock_service):
        resp = client.post(
            "/api/calendar/events",
            json={"title": "Dentist", "event_date": "2026-09-20", "end_time": "10:00"},
        )

        assert resp.status_code == 422
        mock_service.create_event.assert_not_called()

    def test_returns_422_when_end_time_before_start_time(self, client, mock_service):
        resp = client.post(
            "/api/calendar/events",
            json={"title": "Dentist", "event_date": "2026-09-20", "start_time": "11:00", "end_time": "10:00"},
        )

        assert resp.status_code == 422
        mock_service.create_event.assert_not_called()

    def test_returns_422_when_extra_field_supplied(self, client, mock_service):
        resp = client.post(
            "/api/calendar/events",
            json={"title": "Dentist", "event_date": "2026-09-20", "household_id": FAKE_HOUSEHOLD_ID},
        )

        assert resp.status_code == 422
        mock_service.create_event.assert_not_called()

    def test_returns_422_when_title_too_long(self, client, mock_service):
        resp = client.post(
            "/api/calendar/events",
            json={"title": "x" * (MAX_TITLE_LENGTH + 1), "event_date": "2026-09-20"},
        )

        assert resp.status_code == 422
        mock_service.create_event.assert_not_called()

    def test_returns_422_when_description_too_long(self, client, mock_service):
        resp = client.post(
            "/api/calendar/events",
            json={
                "title": "Dentist",
                "event_date": "2026-09-20",
                "description": "x" * (MAX_DESCRIPTION_LENGTH + 1),
            },
        )

        assert resp.status_code == 422
        mock_service.create_event.assert_not_called()

    def test_returns_422_when_location_too_long(self, client, mock_service):
        resp = client.post(
            "/api/calendar/events",
            json={"title": "Dentist", "event_date": "2026-09-20", "location": "x" * (MAX_LOCATION_LENGTH + 1)},
        )

        assert resp.status_code == 422
        mock_service.create_event.assert_not_called()

    def test_accepts_text_at_the_maximum_length(self, client, mock_service):
        mock_service.create_event.return_value = FAKE_EVENT

        resp = client.post(
            "/api/calendar/events",
            json={"title": "x" * MAX_TITLE_LENGTH, "event_date": "2026-09-20"},
        )

        assert resp.status_code == 201

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.create_event.side_effect = NotFoundException("No household.")

        resp = client.post("/api/calendar/events", json={"title": "Dentist", "event_date": "2026-09-20"})

        assert resp.status_code == 404

    def test_returns_422_when_service_raises_validation_exception(self, client, mock_service):
        mock_service.create_event.side_effect = ValidationException("Invalid data for calendar_events")

        resp = client.post("/api/calendar/events", json={"title": "Dentist", "event_date": "2026-09-20"})

        assert resp.status_code == 422


class TestUpdateEvent:
    def test_returns_200_with_updated_event(self, client, mock_service):
        mock_service.update_event.return_value = {**FAKE_EVENT, "title": "Doctor"}

        resp = client.patch(f"/api/calendar/events/{FAKE_EVENT_ID}", json={"title": "Doctor"})

        assert resp.status_code == 200
        assert resp.json()["title"] == "Doctor"

    def test_passes_only_set_fields(self, client, mock_service):
        mock_service.update_event.return_value = FAKE_EVENT

        client.patch(f"/api/calendar/events/{FAKE_EVENT_ID}", json={"title": "Doctor"})

        mock_service.update_event.assert_called_once_with(FAKE_USER_ID, FAKE_EVENT_ID, {"title": "Doctor"})

    def test_serializes_dates_and_times_as_strings(self, client, mock_service):
        mock_service.update_event.return_value = FAKE_EVENT

        client.patch(
            f"/api/calendar/events/{FAKE_EVENT_ID}",
            json={"event_date": "2026-10-01", "start_time": "08:30", "end_time": "09:15"},
        )

        _, updates = mock_service.update_event.call_args[0][1:]
        assert updates == {"event_date": "2026-10-01", "start_time": "08:30:00", "end_time": "09:15:00"}

    def test_returns_422_when_title_empty(self, client, mock_service):
        resp = client.patch(f"/api/calendar/events/{FAKE_EVENT_ID}", json={"title": ""})

        assert resp.status_code == 422
        mock_service.update_event.assert_not_called()

    def test_returns_422_when_title_too_long(self, client, mock_service):
        resp = client.patch(
            f"/api/calendar/events/{FAKE_EVENT_ID}", json={"title": "x" * (MAX_TITLE_LENGTH + 1)}
        )

        assert resp.status_code == 422
        mock_service.update_event.assert_not_called()

    def test_returns_422_when_only_start_time_patched(self, client, mock_service):
        resp = client.patch(f"/api/calendar/events/{FAKE_EVENT_ID}", json={"start_time": "09:00"})

        assert resp.status_code == 422
        mock_service.update_event.assert_not_called()

    def test_returns_422_when_only_end_time_patched(self, client, mock_service):
        resp = client.patch(f"/api/calendar/events/{FAKE_EVENT_ID}", json={"end_time": "10:00"})

        assert resp.status_code == 422
        mock_service.update_event.assert_not_called()

    def test_returns_422_when_patched_end_time_before_start_time(self, client, mock_service):
        resp = client.patch(
            f"/api/calendar/events/{FAKE_EVENT_ID}", json={"start_time": "11:00", "end_time": "10:00"}
        )

        assert resp.status_code == 422
        mock_service.update_event.assert_not_called()

    def test_returns_422_when_clearing_start_time_but_keeping_end_time(self, client, mock_service):
        resp = client.patch(
            f"/api/calendar/events/{FAKE_EVENT_ID}", json={"start_time": None, "end_time": "10:00"}
        )

        assert resp.status_code == 422
        mock_service.update_event.assert_not_called()

    def test_accepts_both_times_patched_together(self, client, mock_service):
        mock_service.update_event.return_value = FAKE_EVENT

        resp = client.patch(
            f"/api/calendar/events/{FAKE_EVENT_ID}", json={"start_time": "09:00", "end_time": "10:00"}
        )

        assert resp.status_code == 200
        mock_service.update_event.assert_called_once_with(
            FAKE_USER_ID, FAKE_EVENT_ID, {"start_time": "09:00:00", "end_time": "10:00:00"}
        )

    def test_accepts_clearing_both_times_together(self, client, mock_service):
        mock_service.update_event.return_value = FAKE_EVENT

        resp = client.patch(
            f"/api/calendar/events/{FAKE_EVENT_ID}", json={"start_time": None, "end_time": None}
        )

        assert resp.status_code == 200
        mock_service.update_event.assert_called_once_with(
            FAKE_USER_ID, FAKE_EVENT_ID, {"start_time": None, "end_time": None}
        )

    def test_returns_404_when_event_not_found(self, client, mock_service):
        mock_service.update_event.side_effect = NotFoundException("Event not found.")

        resp = client.patch(f"/api/calendar/events/{FAKE_EVENT_ID}", json={"title": "Doctor"})

        assert resp.status_code == 404

    def test_returns_422_when_service_raises_validation_exception(self, client, mock_service):
        mock_service.update_event.side_effect = ValidationException("Invalid data for calendar_events")

        resp = client.patch(f"/api/calendar/events/{FAKE_EVENT_ID}", json={"title": "Doctor"})

        assert resp.status_code == 422


class TestDeleteEvent:
    def test_returns_204_on_success(self, client, mock_service):
        mock_service.delete_event.return_value = None

        resp = client.delete(f"/api/calendar/events/{FAKE_EVENT_ID}")

        assert resp.status_code == 204
        mock_service.delete_event.assert_called_once_with(FAKE_USER_ID, FAKE_EVENT_ID)

    def test_returns_404_when_event_not_found(self, client, mock_service):
        mock_service.delete_event.side_effect = NotFoundException("Event not found.")

        resp = client.delete(f"/api/calendar/events/{FAKE_EVENT_ID}")

        assert resp.status_code == 404


class TestCreateBirthday:
    def test_returns_201_with_birthday(self, client, mock_service):
        mock_service.create_birthday.return_value = FAKE_BIRTHDAY

        resp = client.post(
            "/api/calendar/birthdays",
            json={"person_name": "Ada", "birth_month": 9, "birth_day": 20, "birth_year": 1990},
        )

        assert resp.status_code == 201
        assert resp.json()["person_name"] == "Ada"

    def test_infers_show_year_true_when_birth_year_given(self, client, mock_service):
        mock_service.create_birthday.return_value = FAKE_BIRTHDAY

        client.post(
            "/api/calendar/birthdays",
            json={"person_name": "Ada", "birth_month": 9, "birth_day": 20, "birth_year": 1990},
        )

        mock_service.create_birthday.assert_called_once_with(
            FAKE_USER_ID, person_name="Ada", birth_month=9, birth_day=20, birth_year=1990, show_year=True
        )

    def test_creates_birthday_with_unknown_year(self, client, mock_service):
        # The core UX case: day and month known, year isn't — no year, and no forced show_year.
        mock_service.create_birthday.return_value = {**FAKE_BIRTHDAY, "birth_year": None, "show_year": False}

        resp = client.post(
            "/api/calendar/birthdays", json={"person_name": "Ada", "birth_month": 9, "birth_day": 20}
        )

        assert resp.status_code == 201
        mock_service.create_birthday.assert_called_once_with(
            FAKE_USER_ID, person_name="Ada", birth_month=9, birth_day=20, birth_year=None, show_year=False
        )

    def test_returns_422_when_show_year_true_without_birth_year(self, client, mock_service):
        resp = client.post(
            "/api/calendar/birthdays",
            json={"person_name": "Ada", "birth_month": 9, "birth_day": 20, "show_year": True},
        )

        assert resp.status_code == 422
        mock_service.create_birthday.assert_not_called()

    def test_can_hide_age_even_when_birth_year_is_known(self, client, mock_service):
        mock_service.create_birthday.return_value = {**FAKE_BIRTHDAY, "show_year": False}

        resp = client.post(
            "/api/calendar/birthdays",
            json={"person_name": "Ada", "birth_month": 9, "birth_day": 20, "birth_year": 1990, "show_year": False},
        )

        assert resp.status_code == 201
        mock_service.create_birthday.assert_called_once_with(
            FAKE_USER_ID, person_name="Ada", birth_month=9, birth_day=20, birth_year=1990, show_year=False
        )

    def test_returns_422_when_person_name_empty(self, client, mock_service):
        resp = client.post(
            "/api/calendar/birthdays", json={"person_name": "", "birth_month": 9, "birth_day": 20}
        )

        assert resp.status_code == 422
        mock_service.create_birthday.assert_not_called()

    def test_returns_422_when_birth_month_missing(self, client, mock_service):
        resp = client.post("/api/calendar/birthdays", json={"person_name": "Ada", "birth_day": 20})

        assert resp.status_code == 422
        mock_service.create_birthday.assert_not_called()

    def test_returns_422_when_birth_day_missing(self, client, mock_service):
        resp = client.post("/api/calendar/birthdays", json={"person_name": "Ada", "birth_month": 9})

        assert resp.status_code == 422
        mock_service.create_birthday.assert_not_called()

    def test_returns_422_when_day_does_not_exist_in_month(self, client, mock_service):
        resp = client.post(
            "/api/calendar/birthdays", json={"person_name": "Ada", "birth_month": 4, "birth_day": 31}
        )

        assert resp.status_code == 422
        mock_service.create_birthday.assert_not_called()

    def test_accepts_feb_29_without_a_birth_year(self, client, mock_service):
        mock_service.create_birthday.return_value = {
            **FAKE_BIRTHDAY,
            "birth_month": 2,
            "birth_day": 29,
            "birth_year": None,
            "show_year": False,
        }

        resp = client.post(
            "/api/calendar/birthdays", json={"person_name": "Ada", "birth_month": 2, "birth_day": 29}
        )

        assert resp.status_code == 201

    def test_returns_422_when_feb_29_with_a_non_leap_birth_year(self, client, mock_service):
        resp = client.post(
            "/api/calendar/birthdays",
            json={"person_name": "Ada", "birth_month": 2, "birth_day": 29, "birth_year": 1990},
        )

        assert resp.status_code == 422
        mock_service.create_birthday.assert_not_called()

    def test_accepts_feb_29_with_a_leap_birth_year(self, client, mock_service):
        mock_service.create_birthday.return_value = {
            **FAKE_BIRTHDAY,
            "birth_month": 2,
            "birth_day": 29,
            "birth_year": 1992,
        }

        resp = client.post(
            "/api/calendar/birthdays",
            json={"person_name": "Ada", "birth_month": 2, "birth_day": 29, "birth_year": 1992},
        )

        assert resp.status_code == 201

    def test_returns_422_when_birth_date_in_the_future(self, client, mock_service):
        tomorrow = date.today() + timedelta(days=1)

        resp = client.post(
            "/api/calendar/birthdays",
            json={
                "person_name": "Ada",
                "birth_month": tomorrow.month,
                "birth_day": tomorrow.day,
                "birth_year": tomorrow.year,
            },
        )

        assert resp.status_code == 422
        mock_service.create_birthday.assert_not_called()

    def test_accepts_birth_date_of_today(self, client, mock_service):
        mock_service.create_birthday.return_value = FAKE_BIRTHDAY
        today = date.today()

        resp = client.post(
            "/api/calendar/birthdays",
            json={"person_name": "Ada", "birth_month": today.month, "birth_day": today.day, "birth_year": today.year},
        )

        assert resp.status_code == 201

    def test_returns_422_when_person_name_too_long(self, client, mock_service):
        resp = client.post(
            "/api/calendar/birthdays",
            json={"person_name": "x" * (MAX_TITLE_LENGTH + 1), "birth_month": 9, "birth_day": 20},
        )

        assert resp.status_code == 422
        mock_service.create_birthday.assert_not_called()

    def test_returns_422_when_extra_field_supplied(self, client, mock_service):
        resp = client.post(
            "/api/calendar/birthdays",
            json={"person_name": "Ada", "birth_month": 9, "birth_day": 20, "household_id": FAKE_HOUSEHOLD_ID},
        )

        assert resp.status_code == 422
        mock_service.create_birthday.assert_not_called()

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.create_birthday.side_effect = NotFoundException("No household.")

        resp = client.post(
            "/api/calendar/birthdays", json={"person_name": "Ada", "birth_month": 9, "birth_day": 20}
        )

        assert resp.status_code == 404

    def test_returns_422_when_service_raises_validation_exception(self, client, mock_service):
        mock_service.create_birthday.side_effect = ValidationException("Invalid data for calendar_birthdays")

        resp = client.post(
            "/api/calendar/birthdays", json={"person_name": "Ada", "birth_month": 9, "birth_day": 20}
        )

        assert resp.status_code == 422


class TestUpdateBirthday:
    def test_returns_200_with_updated_birthday(self, client, mock_service):
        mock_service.update_birthday.return_value = {**FAKE_BIRTHDAY, "person_name": "Grace"}

        resp = client.patch(f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}", json={"person_name": "Grace"})

        assert resp.status_code == 200
        assert resp.json()["person_name"] == "Grace"

    def test_passes_only_set_fields(self, client, mock_service):
        mock_service.update_birthday.return_value = FAKE_BIRTHDAY

        client.patch(f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}", json={"show_year": False})

        mock_service.update_birthday.assert_called_once_with(
            FAKE_USER_ID, FAKE_BIRTHDAY_ID, {"show_year": False}
        )

    def test_updates_birth_date_when_month_day_and_year_all_sent(self, client, mock_service):
        mock_service.update_birthday.return_value = FAKE_BIRTHDAY

        client.patch(
            f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}",
            json={"birth_month": 1, "birth_day": 2, "birth_year": 1991},
        )

        _, updates = mock_service.update_birthday.call_args[0][1:]
        assert updates == {"birth_month": 1, "birth_day": 2, "birth_year": 1991, "show_year": True}

    def test_clears_birth_year_back_to_unknown(self, client, mock_service):
        mock_service.update_birthday.return_value = {**FAKE_BIRTHDAY, "birth_year": None, "show_year": False}

        client.patch(
            f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}",
            json={"birth_month": 9, "birth_day": 20, "birth_year": None},
        )

        _, updates = mock_service.update_birthday.call_args[0][1:]
        assert updates == {"birth_month": 9, "birth_day": 20, "birth_year": None, "show_year": False}

    def test_returns_422_when_birth_month_patched_without_birth_day(self, client, mock_service):
        resp = client.patch(f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}", json={"birth_month": 1})

        assert resp.status_code == 422
        mock_service.update_birthday.assert_not_called()

    def test_returns_422_when_birth_year_patched_alone(self, client, mock_service):
        resp = client.patch(f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}", json={"birth_year": 1991})

        assert resp.status_code == 422
        mock_service.update_birthday.assert_not_called()

    def test_returns_422_when_birth_date_in_the_future(self, client, mock_service):
        tomorrow = date.today() + timedelta(days=1)

        resp = client.patch(
            f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}",
            json={"birth_month": tomorrow.month, "birth_day": tomorrow.day, "birth_year": tomorrow.year},
        )

        assert resp.status_code == 422
        mock_service.update_birthday.assert_not_called()

    def test_returns_422_when_feb_29_with_a_non_leap_birth_year(self, client, mock_service):
        resp = client.patch(
            f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}",
            json={"birth_month": 2, "birth_day": 29, "birth_year": 1991},
        )

        assert resp.status_code == 422
        mock_service.update_birthday.assert_not_called()

    def test_returns_422_when_show_year_true_without_birth_year_in_same_patch(self, client, mock_service):
        resp = client.patch(
            f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}",
            json={"birth_month": 9, "birth_day": 20, "show_year": True},
        )

        assert resp.status_code == 422
        mock_service.update_birthday.assert_not_called()

    def test_returns_404_when_birthday_not_found(self, client, mock_service):
        mock_service.update_birthday.side_effect = NotFoundException("Birthday not found.")

        resp = client.patch(f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}", json={"person_name": "Grace"})

        assert resp.status_code == 404

    def test_returns_422_when_service_raises_validation_exception(self, client, mock_service):
        mock_service.update_birthday.side_effect = ValidationException("Invalid data for calendar_birthdays")

        resp = client.patch(f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}", json={"person_name": "Grace"})

        assert resp.status_code == 422


class TestDeleteBirthday:
    def test_returns_204_on_success(self, client, mock_service):
        mock_service.delete_birthday.return_value = None

        resp = client.delete(f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}")

        assert resp.status_code == 204
        mock_service.delete_birthday.assert_called_once_with(FAKE_USER_ID, FAKE_BIRTHDAY_ID)

    def test_returns_404_when_birthday_not_found(self, client, mock_service):
        mock_service.delete_birthday.side_effect = NotFoundException("Birthday not found.")

        resp = client.delete(f"/api/calendar/birthdays/{FAKE_BIRTHDAY_ID}")

        assert resp.status_code == 404
