"""Tests for the tools module."""

import datetime
from zoneinfo import ZoneInfo

from agent_smithers.tools import current_datetime


def test_current_datetime_no_timezone():
    """Test current_datetime returns ISO format with UTC when no timezone specified."""
    result = current_datetime()
    dt = datetime.datetime.fromisoformat(result)
    assert dt.tzinfo == datetime.UTC


def test_current_datetime_with_timezone():
    """Test current_datetime with a specific timezone."""
    result = current_datetime(timezone="US/Pacific")
    dt = datetime.datetime.fromisoformat(result)
    # Convert the datetime to the target timezone to verify it worked
    pacific_time = dt.astimezone(ZoneInfo("US/Pacific"))
    assert str(pacific_time.tzinfo) == "US/Pacific"


def test_current_datetime_invalid_timezone():
    """Test current_datetime with an invalid timezone."""
    result = current_datetime(timezone="InvalidZone")
    assert result == "Unknown timezone: InvalidZone"
