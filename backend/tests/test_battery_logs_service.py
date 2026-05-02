from unittest.mock import MagicMock

import pytest

from src.db.db import DB
from src.errors import NotFoundException
from src.service.battery_logs import BatteryLogService

FAKE_USER_ID = "user-111"
FAKE_HOUSEHOLD = {"id": "hh-001", "name": "Home", "role": "owner"}
FAKE_LOG = {
    "id": "log-001",
    "user_id": FAKE_USER_ID,
    "household_id": "hh-001",
    "level": 75,
    "note": "Feeling good",
    "effective_at": "2026-05-01T10:00:00+00:00",
    "logged_at": "2026-05-01T10:00:00+00:00",
}


@pytest.fixture
def mock_db():
    return MagicMock(spec=DB)


@pytest.fixture
def service(mock_db):
    return BatteryLogService(mock_db)


class TestCreateBatteryLog:
    def test_creates_log_with_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = FAKE_HOUSEHOLD
        mock_db.create_battery_log.return_value = FAKE_LOG

        result = service.create_battery_log(FAKE_USER_ID, level=75, note="Feeling good", effective_at="2026-05-01T10:00:00+00:00")

        assert result == FAKE_LOG
        mock_db.create_battery_log.assert_called_once_with(
            user_id=FAKE_USER_ID,
            household_id="hh-001",
            level=75,
            note="Feeling good",
            effective_at="2026-05-01T10:00:00+00:00",
        )

    def test_raises_not_found_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.create_battery_log(FAKE_USER_ID, level=75, note=None, effective_at="2026-05-01T10:00:00+00:00")


class TestUpdateBatteryLog:
    def test_updates_own_log(self, service, mock_db):
        updated = {**FAKE_LOG, "level": 50}
        mock_db.update_battery_log.return_value = updated

        result = service.update_battery_log(FAKE_USER_ID, "log-001", {"level": 50})

        assert result["level"] == 50
        mock_db.update_battery_log.assert_called_once_with("log-001", FAKE_USER_ID, {"level": 50})

    def test_raises_not_found_when_no_rows_affected(self, service, mock_db):
        mock_db.update_battery_log.return_value = None

        with pytest.raises(NotFoundException):
            service.update_battery_log(FAKE_USER_ID, "log-001", {"level": 50})

    def test_raises_not_found_when_empty_updates(self, service, mock_db):
        with pytest.raises(NotFoundException):
            service.update_battery_log(FAKE_USER_ID, "log-001", {})


class TestDeleteBatteryLog:
    def test_deletes_own_log(self, service, mock_db):
        mock_db.delete_battery_log.return_value = True

        service.delete_battery_log(FAKE_USER_ID, "log-001")
        mock_db.delete_battery_log.assert_called_once_with("log-001", FAKE_USER_ID)

    def test_raises_not_found_when_no_rows_affected(self, service, mock_db):
        mock_db.delete_battery_log.return_value = False

        with pytest.raises(NotFoundException):
            service.delete_battery_log(FAKE_USER_ID, "log-001")


class TestGetHouseholdBatteryLogs:
    def test_returns_logs_for_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = FAKE_HOUSEHOLD
        mock_db.find_battery_logs_by_household.return_value = [FAKE_LOG]

        result = service.get_household_battery_logs(FAKE_USER_ID, "2026-05-01T00:00:00Z", "2026-05-02T00:00:00Z")

        assert result == [FAKE_LOG]
        mock_db.find_battery_logs_by_household.assert_called_once_with(
            "hh-001", "2026-05-01T00:00:00Z", "2026-05-02T00:00:00Z"
        )

    def test_raises_not_found_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.get_household_battery_logs(FAKE_USER_ID, "2026-05-01T00:00:00Z", "2026-05-02T00:00:00Z")
