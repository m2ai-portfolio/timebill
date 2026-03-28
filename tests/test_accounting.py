"""Tests for time tracking with idle detection."""

import os
import time
import pytest
from timebill.agent.accounting import TimeTracker
from timebill.data.models import TimeEntry


class TestTimeTracker:
    """Test suite for TimeTracker class."""

    def test_initialization_default(self):
        """Test TimeTracker initialization with default idle time."""
        tracker = TimeTracker()
        assert tracker.idle_seconds == 300  # default

    def test_initialization_custom_idle(self):
        """Test TimeTracker initialization with custom idle time."""
        tracker = TimeTracker(idle_seconds=60)
        assert tracker.idle_seconds == 60

    def test_initialization_from_env(self):
        """Test TimeTracker initialization from environment variable."""
        os.environ['TIMEBILL_IDLE_SECONDS'] = '120'
        tracker = TimeTracker()
        assert tracker.idle_seconds == 120
        del os.environ['TIMEBILL_IDLE_SECONDS']

    def test_start_tracking(self):
        """Test starting time tracking for a project."""
        tracker = TimeTracker()
        tracker.start_tracking('TestProject')

        assert tracker._current_project == 'TestProject'
        assert tracker._start_time_mono is not None
        assert tracker._start_ts is not None
        assert tracker._last_activity_mono is not None

    def test_stop_tracking_returns_entry(self):
        """Test that stop_tracking returns a TimeEntry."""
        tracker = TimeTracker()
        tracker.start_tracking('TestProject')
        time.sleep(0.1)  # Small delay to ensure duration > 0
        entry = tracker.stop_tracking()

        assert entry is not None
        assert isinstance(entry, TimeEntry)
        assert entry.project_name == 'TestProject'
        assert entry.start_ts > 0
        assert entry.end_ts > 0
        assert entry.duration_ms > 0

    def test_stop_tracking_without_start_returns_none(self):
        """Test that stop_tracking without start returns None."""
        tracker = TimeTracker()
        entry = tracker.stop_tracking()
        assert entry is None

    def test_duration_calculation(self):
        """Test that duration is calculated correctly."""
        tracker = TimeTracker()
        tracker.start_tracking('TestProject')
        time.sleep(0.5)  # Sleep for 500ms
        entry = tracker.stop_tracking()

        # Duration should be at least 500ms (allowing some margin)
        assert entry.duration_ms >= 450  # 50ms margin for execution time
        assert entry.duration_ms < 1000  # Should not be longer than 1s

    def test_get_current_duration_ms_active(self):
        """Test get_current_duration_ms while tracking."""
        tracker = TimeTracker()
        tracker.start_tracking('TestProject')
        time.sleep(0.1)  # Sleep for 100ms
        duration = tracker.get_current_duration_ms()

        # Should be at least 100ms
        assert duration >= 90  # 10ms margin
        assert duration < 500  # Should not be too long

    def test_get_current_duration_ms_inactive(self):
        """Test get_current_duration_ms when not tracking."""
        tracker = TimeTracker()
        duration = tracker.get_current_duration_ms()
        assert duration == 0

    def test_is_idle_initially_true(self):
        """Test that is_idle returns True when no activity recorded."""
        tracker = TimeTracker(idle_seconds=1)
        assert tracker.is_idle() is True

    def test_is_idle_after_activity(self):
        """Test is_idle returns False immediately after activity."""
        tracker = TimeTracker(idle_seconds=1)
        tracker.start_tracking('TestProject')
        assert tracker.is_idle() is False

    def test_is_idle_after_threshold(self):
        """Test is_idle returns True after idle threshold exceeded."""
        tracker = TimeTracker(idle_seconds=1)
        tracker.start_tracking('TestProject')
        time.sleep(1.1)  # Sleep longer than threshold
        assert tracker.is_idle() is True

    def test_record_activity_resets_idle(self):
        """Test that record_activity resets idle timer."""
        tracker = TimeTracker(idle_seconds=2)
        tracker.start_tracking('TestProject')
        time.sleep(1.5)  # Sleep but not past threshold
        tracker.record_activity()  # Reset idle timer
        time.sleep(0.6)  # Sleep a bit more
        # Total would be 2.1s without reset, but reset should make it < 2s
        assert tracker.is_idle() is False

    def test_multiple_project_switching(self):
        """Test switching between multiple projects."""
        tracker = TimeTracker()

        # Track first project
        tracker.start_tracking('Project1')
        time.sleep(0.1)
        entry1 = tracker.stop_tracking()

        # Track second project
        tracker.start_tracking('Project2')
        time.sleep(0.1)
        entry2 = tracker.stop_tracking()

        assert entry1.project_name == 'Project1'
        assert entry2.project_name == 'Project2'
        assert entry1.duration_ms > 0
        assert entry2.duration_ms > 0

    def test_automatic_stop_on_new_start(self):
        """Test that starting a new project stops the current one."""
        tracker = TimeTracker()

        tracker.start_tracking('Project1')
        time.sleep(0.1)

        # Start tracking new project without explicitly stopping
        tracker.start_tracking('Project2')

        # Should have one completed entry for Project1
        entries = tracker.get_entries()
        assert len(entries) == 1
        assert entries[0].project_name == 'Project1'
        assert entries[0].duration_ms > 0

        # Currently tracking Project2
        assert tracker._current_project == 'Project2'

    def test_get_entries_returns_copy(self):
        """Test that get_entries returns a copy of the list."""
        tracker = TimeTracker()
        tracker.start_tracking('Project1')
        time.sleep(0.05)
        tracker.stop_tracking()

        entries1 = tracker.get_entries()
        entries2 = tracker.get_entries()

        assert entries1 is not entries2  # Different list objects
        assert len(entries1) == len(entries2)  # Same contents

    def test_get_entries_accumulates(self):
        """Test that entries accumulate over multiple tracking sessions."""
        tracker = TimeTracker()

        # Track multiple projects
        for i in range(3):
            tracker.start_tracking(f'Project{i}')
            time.sleep(0.05)
            tracker.stop_tracking()

        entries = tracker.get_entries()
        assert len(entries) == 3
        assert entries[0].project_name == 'Project0'
        assert entries[1].project_name == 'Project1'
        assert entries[2].project_name == 'Project2'

    def test_entry_timestamps_are_integers(self):
        """Test that all timestamps are integers (no floats)."""
        tracker = TimeTracker()
        tracker.start_tracking('TestProject')
        time.sleep(0.05)
        entry = tracker.stop_tracking()

        assert isinstance(entry.start_ts, int)
        assert isinstance(entry.end_ts, int)
        assert isinstance(entry.duration_ms, int)

    def test_entry_end_after_start(self):
        """Test that end timestamp is after start timestamp."""
        tracker = TimeTracker()
        tracker.start_tracking('TestProject')
        time.sleep(0.05)
        entry = tracker.stop_tracking()

        assert entry.end_ts > entry.start_ts

    def test_idle_threshold_zero(self):
        """Test idle detection with zero threshold."""
        tracker = TimeTracker(idle_seconds=0)
        tracker.start_tracking('TestProject')
        # Any time without activity should be idle
        time.sleep(0.01)
        assert tracker.is_idle() is True

    def test_multiple_record_activity_calls(self):
        """Test multiple calls to record_activity."""
        tracker = TimeTracker(idle_seconds=1)
        tracker.start_tracking('TestProject')

        # Record activity multiple times
        for _ in range(5):
            time.sleep(0.1)
            tracker.record_activity()

        # Should not be idle
        assert tracker.is_idle() is False
