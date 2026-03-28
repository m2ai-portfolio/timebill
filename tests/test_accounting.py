"""Tests for the time accounting module."""

import time
import pytest
from agent.accounting import TimeAccountant
from data.models import TimeEntry


def test_accountant_initialization():
    """Test TimeAccountant initializes with correct defaults."""
    accountant = TimeAccountant()
    assert accountant.idle_threshold_seconds == 300
    assert accountant.current_entry is None
    assert accountant.completed_entries == []
    assert accountant.last_activity_monotonic is None


def test_accountant_custom_idle_threshold():
    """Test TimeAccountant with custom idle threshold."""
    accountant = TimeAccountant(idle_threshold_seconds=60)
    assert accountant.idle_threshold_seconds == 60


def test_start_tracking_on_activity():
    """Test that activity starts tracking for a project."""
    accountant = TimeAccountant()
    accountant.on_activity("TestProject")

    current = accountant.get_current_entry()
    assert current is not None
    assert current.project_name == "TestProject"
    assert current.start_ts > 0
    assert current.end_ts is None
    assert current.duration_ms == 0


def test_activity_with_explicit_timestamp():
    """Test activity with explicit timestamp."""
    accountant = TimeAccountant()
    timestamp = int(time.time() * 1000)

    accountant.on_activity("TestProject", timestamp_ms=timestamp)

    current = accountant.get_current_entry()
    assert current is not None
    assert current.start_ts == timestamp


def test_project_switch_creates_new_entry():
    """Test that switching projects creates a new entry and finalizes old one."""
    accountant = TimeAccountant()

    # Start with project A
    accountant.on_activity("ProjectA")
    time.sleep(0.1)  # Small delay to ensure duration > 0

    # Switch to project B
    accountant.on_activity("ProjectB")

    # Should have one completed entry for ProjectA
    completed = accountant.get_all_entries()
    assert len(completed) == 1
    assert completed[0].project_name == "ProjectA"
    assert completed[0].end_ts is not None
    assert completed[0].duration_ms > 0

    # Current entry should be ProjectB
    current = accountant.get_current_entry()
    assert current is not None
    assert current.project_name == "ProjectB"


def test_duration_uses_integer_arithmetic():
    """Test that duration calculation uses integer arithmetic."""
    accountant = TimeAccountant()

    accountant.on_activity("TestProject")
    time.sleep(0.05)  # 50ms
    accountant.stop()

    entries = accountant.get_all_entries()
    assert len(entries) == 1

    # Duration should be an integer in milliseconds
    assert isinstance(entries[0].duration_ms, int)
    assert entries[0].duration_ms >= 50  # At least 50ms
    assert entries[0].duration_ms < 200  # But not too much more


def test_timestamp_epoch_milliseconds():
    """Test that timestamps are Unix epoch milliseconds."""
    accountant = TimeAccountant()

    before_ms = int(time.time() * 1000)
    accountant.on_activity("TestProject")
    after_ms = int(time.time() * 1000)

    current = accountant.get_current_entry()
    assert current.start_ts >= before_ms
    assert current.start_ts <= after_ms

    # Verify it's in milliseconds (should be a large number)
    assert current.start_ts > 1000000000000  # After year 2001 in ms


def test_stop_finalizes_current_entry():
    """Test that stop() finalizes the current entry."""
    accountant = TimeAccountant()

    accountant.on_activity("TestProject")
    time.sleep(0.05)
    accountant.stop()

    # Should have no current entry
    assert accountant.get_current_entry() is None

    # Should have one completed entry
    entries = accountant.get_all_entries()
    assert len(entries) == 1
    assert entries[0].project_name == "TestProject"
    assert entries[0].end_ts is not None
    assert entries[0].duration_ms > 0


def test_get_all_entries_returns_copy():
    """Test that get_all_entries returns a copy, not the original list."""
    accountant = TimeAccountant()

    accountant.on_activity("ProjectA")
    accountant.stop()

    entries1 = accountant.get_all_entries()
    entries2 = accountant.get_all_entries()

    # Should be equal but not the same object
    assert entries1 == entries2
    assert entries1 is not entries2


def test_idle_detection_no_current_entry():
    """Test check_idle when no entry is active."""
    accountant = TimeAccountant(idle_threshold_seconds=1)
    was_idle = accountant.check_idle()
    assert was_idle is False


def test_idle_detection_below_threshold():
    """Test check_idle when below idle threshold."""
    accountant = TimeAccountant(idle_threshold_seconds=10)

    accountant.on_activity("TestProject")
    time.sleep(0.1)  # 100ms, well below 10 second threshold

    was_idle = accountant.check_idle()
    assert was_idle is False

    # Entry should still be active
    assert accountant.get_current_entry() is not None


def test_idle_detection_exceeds_threshold():
    """Test check_idle when idle threshold is exceeded."""
    accountant = TimeAccountant(idle_threshold_seconds=0.1)  # 100ms threshold

    accountant.on_activity("TestProject")
    time.sleep(0.2)  # 200ms, exceeds threshold

    was_idle = accountant.check_idle()
    assert was_idle is True

    # Entry should be finalized
    assert accountant.get_current_entry() is None

    # Should have one completed entry
    entries = accountant.get_all_entries()
    assert len(entries) == 1


def test_activity_after_idle_starts_new_entry():
    """Test that activity after idle period starts a new entry."""
    accountant = TimeAccountant(idle_threshold_seconds=0.1)

    # Start activity
    accountant.on_activity("ProjectA")
    time.sleep(0.15)  # Exceed idle threshold

    # New activity on same project after idle
    accountant.on_activity("ProjectA")

    # Should have finalized the old entry
    entries = accountant.get_all_entries()
    assert len(entries) == 1
    assert entries[0].project_name == "ProjectA"

    # Should have started a new current entry
    current = accountant.get_current_entry()
    assert current is not None
    assert current.project_name == "ProjectA"


def test_continued_activity_updates_last_activity_time():
    """Test that continued activity on same project updates last activity time."""
    accountant = TimeAccountant(idle_threshold_seconds=0.2)

    accountant.on_activity("TestProject")
    time.sleep(0.1)

    # Continue activity - should not create new entry
    accountant.on_activity("TestProject")
    time.sleep(0.1)

    # Should still be tracking
    current = accountant.get_current_entry()
    assert current is not None

    # Should have no completed entries (no project switch)
    entries = accountant.get_all_entries()
    assert len(entries) == 0


def test_multiple_project_switches():
    """Test multiple project switches create correct entries."""
    accountant = TimeAccountant()

    accountant.on_activity("ProjectA")
    time.sleep(0.05)

    accountant.on_activity("ProjectB")
    time.sleep(0.05)

    accountant.on_activity("ProjectC")
    time.sleep(0.05)

    accountant.stop()

    entries = accountant.get_all_entries()
    assert len(entries) == 3
    assert entries[0].project_name == "ProjectA"
    assert entries[1].project_name == "ProjectB"
    assert entries[2].project_name == "ProjectC"

    # All should have durations
    for entry in entries:
        assert entry.duration_ms > 0
        assert entry.end_ts is not None


def test_entry_duration_calculation():
    """Test that entry duration is correctly calculated."""
    accountant = TimeAccountant()

    accountant.on_activity("TestProject")
    time.sleep(0.1)  # 100ms
    accountant.stop()

    entries = accountant.get_all_entries()
    entry = entries[0]

    # Verify duration matches end_ts - start_ts
    # Note: There might be small differences due to timing precision
    calculated_duration = entry.end_ts - entry.start_ts
    assert abs(entry.duration_ms - calculated_duration) < 10  # Within 10ms tolerance


def test_metadata_preserved():
    """Test that metadata is preserved in entries."""
    accountant = TimeAccountant()

    accountant.on_activity("TestProject")

    # Access current entry and add metadata
    current = accountant.get_current_entry()
    current.metadata["test_key"] = "test_value"

    accountant.stop()

    entries = accountant.get_all_entries()
    assert entries[0].metadata["test_key"] == "test_value"


def test_no_floating_point_in_duration():
    """Test that duration_ms is always an integer, never float."""
    accountant = TimeAccountant()

    accountant.on_activity("ProjectA")
    time.sleep(0.05)

    accountant.on_activity("ProjectB")
    time.sleep(0.05)

    accountant.stop()

    for entry in accountant.get_all_entries():
        assert isinstance(entry.duration_ms, int)
        assert not isinstance(entry.duration_ms, float)
