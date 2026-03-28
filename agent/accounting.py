"""Time accounting module for TimeBill.

Provides idle-based time tracking using monotonic timestamps and integer arithmetic.
"""

import time
from typing import Optional, List
from data.models import TimeEntry


class TimeAccountant:
    """Tracks time accounting with idle detection."""

    def __init__(self, idle_threshold_seconds: int = 300):
        """Initialize TimeAccountant.

        Args:
            idle_threshold_seconds: Number of seconds of inactivity before
                                   considering user idle (default 300 = 5 minutes)
        """
        self.idle_threshold_seconds = idle_threshold_seconds
        self.current_entry: Optional[TimeEntry] = None
        self.completed_entries: List[TimeEntry] = []

        # Track last activity time using monotonic clock
        self.last_activity_monotonic: Optional[float] = None

        # Track the monotonic time when current entry started
        self.current_entry_start_monotonic: Optional[float] = None

    def on_activity(self, project_name: str, timestamp_ms: Optional[int] = None):
        """Called when user activity is detected.

        Args:
            project_name: Name of the active project
            timestamp_ms: Optional Unix epoch milliseconds timestamp.
                         If not provided, current time is used.
        """
        # Get current time
        now_monotonic = time.monotonic()
        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)

        # Check if we need to finalize current entry due to idle
        if self.current_entry is not None:
            elapsed_since_activity = (
                now_monotonic - self.last_activity_monotonic
                if self.last_activity_monotonic is not None
                else 0
            )

            # If idle threshold exceeded, finalize current entry
            if elapsed_since_activity > self.idle_threshold_seconds:
                self._finalize_current_entry(idle_cutoff=True)

        # Check if project changed
        if self.current_entry is not None and self.current_entry.project_name != project_name:
            # Finalize old project entry
            self._finalize_current_entry()
            # Start new entry for new project
            self._start_new_entry(project_name, timestamp_ms, now_monotonic)
        elif self.current_entry is None:
            # Start tracking for this project
            self._start_new_entry(project_name, timestamp_ms, now_monotonic)

        # Update last activity time
        self.last_activity_monotonic = now_monotonic

    def _start_new_entry(self, project_name: str, timestamp_ms: int, monotonic_time: float):
        """Start a new time entry.

        Args:
            project_name: Name of the project
            timestamp_ms: Unix epoch milliseconds timestamp
            monotonic_time: Monotonic timestamp for elapsed time calculation
        """
        self.current_entry = TimeEntry(
            project_name=project_name,
            start_ts=timestamp_ms,
            end_ts=None,
            duration_ms=0,
            metadata={}
        )
        self.current_entry_start_monotonic = monotonic_time

    def _finalize_current_entry(self, idle_cutoff: bool = False):
        """Finalize the current time entry.

        Args:
            idle_cutoff: If True, the entry was finalized due to idle detection.
                        The end time is set to last_activity_time + idle_threshold.
        """
        if self.current_entry is None:
            return

        now_monotonic = time.monotonic()
        now_ms = int(time.time() * 1000)

        if idle_cutoff and self.last_activity_monotonic is not None:
            # Calculate end time based on last activity + idle threshold
            # Use monotonic time for precise duration calculation
            elapsed_monotonic = (
                self.last_activity_monotonic - self.current_entry_start_monotonic
            )
            # Convert to milliseconds using integer arithmetic
            duration_ms = int(elapsed_monotonic * 1000)

            # Calculate end timestamp
            end_ts = self.current_entry.start_ts + duration_ms
        else:
            # Normal finalization - use current time
            elapsed_monotonic = now_monotonic - self.current_entry_start_monotonic
            # Convert to milliseconds using integer arithmetic
            duration_ms = int(elapsed_monotonic * 1000)
            end_ts = now_ms

        # Update the entry
        self.current_entry.end_ts = end_ts
        self.current_entry.duration_ms = duration_ms

        # Add to completed entries
        self.completed_entries.append(self.current_entry)

        # Clear current entry
        self.current_entry = None
        self.current_entry_start_monotonic = None

    def check_idle(self):
        """Check if user has gone idle and finalize entry if so.

        Returns:
            True if idle was detected and entry was finalized, False otherwise
        """
        if self.current_entry is None or self.last_activity_monotonic is None:
            return False

        now_monotonic = time.monotonic()
        elapsed_since_activity = now_monotonic - self.last_activity_monotonic

        if elapsed_since_activity > self.idle_threshold_seconds:
            self._finalize_current_entry(idle_cutoff=True)
            return True

        return False

    def get_current_entry(self) -> Optional[TimeEntry]:
        """Get the current active time entry.

        Returns:
            Current TimeEntry or None if not tracking
        """
        return self.current_entry

    def get_all_entries(self) -> List[TimeEntry]:
        """Get all completed time entries.

        Returns:
            List of completed TimeEntry instances
        """
        return self.completed_entries.copy()

    def stop(self):
        """Stop tracking and finalize current entry.

        Called when shutting down the agent.
        """
        if self.current_entry is not None:
            self._finalize_current_entry()
