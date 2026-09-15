from datetime import date, datetime, time
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Upper bound on the span of a single calendar feed request. The month grid needs ~42 days and
# the agenda view at most a year; anything larger is not a view the UI can render.
MAX_FEED_RANGE_DAYS = 400

# Text bounds. Titles and names render in month-grid day cells, so they stay short.
MAX_TITLE_LENGTH = 200
MAX_LOCATION_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000

# A leap year used only to check that (month, day) is a shape that exists on the calendar at all
# (e.g. rejecting Feb 30), independent of any specific birth_year — which may be unknown.
_LEAP_YEAR_FOR_VALIDATION = 2020


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _is_valid_month_day(month: int, day: int) -> bool:
    try:
        date(_LEAP_YEAR_FOR_VALIDATION, month, day)
    except ValueError:
        return False
    return True


class CalendarFeedQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    range_from: date = Field(..., alias="from")
    range_to: date = Field(..., alias="to")

    @model_validator(mode="after")
    def validate_range(self) -> "CalendarFeedQuery":
        if self.range_to < self.range_from:
            raise ValueError("'to' must be on or after 'from'.")
        if (self.range_to - self.range_from).days > MAX_FEED_RANGE_DAYS:
            raise ValueError(f"Requested range is too large; the maximum span is {MAX_FEED_RANGE_DAYS} days.")
        return self


class CreateEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    event_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(None, max_length=MAX_LOCATION_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)

    @model_validator(mode="after")
    def validate_times(self) -> "CreateEventRequest":
        if self.end_time is not None and self.start_time is None:
            raise ValueError("end_time requires start_time")
        if self.start_time is not None and self.end_time is not None and self.end_time < self.start_time:
            raise ValueError("end_time must be >= start_time")
        return self


class UpdateEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH)
    event_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(None, max_length=MAX_LOCATION_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)

    @model_validator(mode="after")
    def validate_times(self) -> "UpdateEventRequest":
        """Times are patched as a unit.

        The two time columns are always written together, so the merged row is valid without
        reading the current one first — which keeps the update a single, ownership-scoped query.
        """
        patched = self.model_fields_set
        if ("start_time" in patched) != ("end_time" in patched):
            raise ValueError("start_time and end_time must be updated together")
        if self.end_time is not None and self.start_time is None:
            raise ValueError("end_time requires start_time")
        if self.start_time is not None and self.end_time is not None and self.end_time < self.start_time:
            raise ValueError("end_time must be >= start_time")
        return self


class EventResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    household_id: UUID
    title: str
    event_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    description: str | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class CreateBirthdayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person_name: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    birth_month: int = Field(..., ge=1, le=12)
    birth_day: int = Field(..., ge=1, le=31)
    # Optional: the person adding a birthday often knows the day and month but not the year, and
    # shouldn't be forced to guess it or do the math themselves.
    birth_year: int | None = Field(None, ge=1900)
    # None ⇒ inferred: show age once the year is known, hide it when it isn't — so a caller who
    # doesn't set birth_year isn't also forced to remember to set show_year=False for it.
    show_year: bool | None = None

    @model_validator(mode="after")
    def validate_birth_date(self) -> "CreateBirthdayRequest":
        if not _is_valid_month_day(self.birth_month, self.birth_day):
            raise ValueError(f"{self.birth_day} is not a valid day for month {self.birth_month}")
        if self.birth_year is not None:
            if self.birth_day == 29 and self.birth_month == 2 and not _is_leap(self.birth_year):
                raise ValueError("February 29 requires a leap birth_year, or omit birth_year")
            if date(self.birth_year, self.birth_month, self.birth_day) > date.today():
                raise ValueError("birth date cannot be in the future")
        if self.show_year is None:
            self.show_year = self.birth_year is not None
        elif self.show_year and self.birth_year is None:
            raise ValueError("show_year requires birth_year")
        return self


class UpdateBirthdayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person_name: str | None = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH)
    birth_month: int | None = Field(None, ge=1, le=12)
    birth_day: int | None = Field(None, ge=1, le=31)
    birth_year: int | None = Field(None, ge=1900)
    show_year: bool | None = None

    @model_validator(mode="after")
    def validate_birth_date(self) -> "UpdateBirthdayRequest":
        """birth_month/birth_day/birth_year are patched as one unit — including birth_year, even
        though it's optional data — so the combination can be validated (leap-day shape, "not in
        the future") from the patch alone, without reading the current row first. `birth_year`
        can still be cleared back to "unknown" by sending it as `null` alongside the other two.

        `show_year` is only auto-inferred here when this same patch changes the date (mirroring
        CreateBirthdayRequest): if it's touched on its own, whether True is valid depends on the
        row's *current* birth_year, which this patch may not include. That case is left to the
        show_year_requires_birth_year DB constraint (a 23514 violation surfaces as a 422 via
        Store's error translation) rather than forcing a pre-fetch here.
        """
        patched = self.model_fields_set
        date_fields = {"birth_month", "birth_day", "birth_year"}
        touched = date_fields & patched
        if touched and touched != date_fields:
            raise ValueError("birth_month, birth_day and birth_year must be updated together")
        if touched == date_fields:
            if self.birth_month is None or self.birth_day is None:
                raise ValueError("birth_month and birth_day are required")
            if not _is_valid_month_day(self.birth_month, self.birth_day):
                raise ValueError(f"{self.birth_day} is not a valid day for month {self.birth_month}")
            if self.birth_year is not None:
                if self.birth_day == 29 and self.birth_month == 2 and not _is_leap(self.birth_year):
                    raise ValueError("February 29 requires a leap birth_year, or omit birth_year")
                if date(self.birth_year, self.birth_month, self.birth_day) > date.today():
                    raise ValueError("birth date cannot be in the future")
            if "show_year" not in patched:
                self.show_year = self.birth_year is not None
            elif self.show_year and self.birth_year is None:
                raise ValueError("show_year requires birth_year")
        return self


class BirthdayResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    household_id: UUID
    person_name: str
    birth_month: int
    birth_day: int
    birth_year: int | None = None
    show_year: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class BirthdayOccurrence(BaseModel):
    """A birthday expanded to a concrete occurrence within a requested date range."""

    id: UUID
    person_name: str
    birth_month: int
    birth_day: int
    birth_year: int | None = None
    occurrence_date: date
    age: int | None = Field(None, ge=0)  # null when show_year is False or birth_year is unknown
    show_year: bool


class ChoreDot(BaseModel):
    count: int
    titles: list[str]


# --- feed events ---
#
# The feed merges events from every connected source into one `events` list, each item tagged
# with `source` so the client can style/group by origin without needing a separate array per
# integration. Adding a source later (Outlook, Apple Calendar, ...) means adding a union member
# here, not a new top-level field on CalendarFeedResponse and a client-side merge step.


class NativeCalendarEvent(EventResponse):
    """A capple-native event, as stored in app.calendar_events."""

    source: Literal["native"] = "native"


class GoogleCalendarEvent(BaseModel):
    """A read-only mirror of an event from a connected household member's Google Calendar.

    Reserved for Phase 2 (see feature-plan-calendar.md §3/§8) — `CalendarService.get_feed` does
    not emit these yet, so no event in the feed carries `source: "google"` until that phase lands.
    """

    model_config = ConfigDict(extra="ignore")

    source: Literal["google"] = "google"
    id: str
    user_id: UUID
    calendar_id: str
    title: str
    start: datetime
    end: datetime


CalendarFeedEvent = Annotated[NativeCalendarEvent | GoogleCalendarEvent, Field(discriminator="source")]


class CalendarFeedResponse(BaseModel):
    events: list[CalendarFeedEvent]
    birthdays: list[BirthdayOccurrence]
    chore_dots: dict[date, ChoreDot]
    range_from: date
    range_to: date
