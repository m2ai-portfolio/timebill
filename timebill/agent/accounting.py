"""Time tracking with idle detection for TimeBill."""

import time
import os
from typing import Optional, List
from timebill.data.models import TimeEntry


class TimeTracker:
    """Track time for projects with idle detection."""

    def __init__(self, idle_seconds: Optional[int] = None):
        """
        Initialize the time tracker.

        Args:
            idle_seconds: Idle threshold in seconds. If None, reads from
                         TIMEBILL_IDLE_SECONDS env var (default 300).
        """
        # Use env var or default to 300
        if idle_seconds is not None:
            self.idle_seconds = idle_seconds
        else:
            self.idle_seconds = int(os.environ.get('TIMEBILL_IDLE_SECONDS', '300'))
        self._current_project: Optional[str] = None
        self._start_time_mono: Optional[float] = None  # time.monotonic()
        self._start_ts: Optional[int] = None  # Unix epoch ms
        self._last_activity_mono: Optional[float] = None
        self._entries: List[TimeEntry] = []  # completed TimeEntry objects

    def start_tracking(self, project_name: str):
        """
        Start tracking time for a project.

        Args:
            project_name: Name of the project to track time for.
        """
        # If already tracking, stop current first
        if self._current_project:
            self.stop_tracking()

        self._current_project = project_name
        self._start_time_mono = time.monotonic()
        self._start_ts = int(time.time() * 1000)  # ms
        self._last_activity_mono = self._start_time_mono

    def stop_tracking(self) -> Optional[TimeEntry]:
        """
        Stop tracking and return the TimeEntry.

        Returns:
            TimeEntry object for the completed tracking session, or None if
            no tracking was in progress.
        """
        if not self._current_project:
            return None

        end_ts = int(time.time() * 1000)
        duration_mono = time.monotonic() - self._start_time_mono
        duration_ms = int(duration_mono * 1000)  # integer arithmetic

        entry = TimeEntry(
            project_name=self._current_project,
            start_ts=self._start_ts,
            end_ts=end_ts,
            duration_ms=duration_ms
        )

        self._entries.append(entry)
        self._current_project = None
        self._start_time_mono = None
        self._start_ts = None

        return entry

    def record_activity(self):
        """Record that user activity was detected."""
        self._last_activity_mono = time.monotonic()

    def is_idle(self) -> bool:
        """
        Check if user has been idle longer than threshold.

        Returns:
            True if idle time exceeds threshold, False otherwise.
        """
        if self._last_activity_mono is None:
            return True
        elapsed = time.monotonic() - self._last_activity_mono
        # For zero threshold, any elapsed time > 0 is considered idle
        if self.idle_seconds == 0:
            return elapsed > 0
        return elapsed >= self.idle_seconds

    def get_current_duration_ms(self) -> int:
        """
        Get current tracking duration in milliseconds.

        Returns:
            Duration in ms if tracking is active, 0 otherwise.
        """
        if not self._start_time_mono:
            return 0
        return int((time.monotonic() - self._start_time_mono) * 1000)

    def get_entries(self) -> List[TimeEntry]:
        """
        Return all completed time entries.

        Returns:
            List of completed TimeEntry objects.
        """
        return list(self._entries)
