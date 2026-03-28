"""Data models for TimeBill using dataclasses."""

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class Project:
    """Represents a project that time is tracked against."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


@dataclass
class TimeEntry:
    """Represents a time tracking entry for a project."""
    project_name: str
    start_ts: int  # Unix epoch ms (UTC)
    end_ts: Optional[int] = None
    duration_ms: int = 0
    metadata: Optional[Dict[str, str]] = field(default_factory=dict)
