"""Data models for TimeBill."""


class Project:
    """Represents a project being tracked."""

    def __init__(self, name: str, description: str = None, color: str = None):
        """Initialize a Project.

        Args:
            name: Project name (e.g., "Website Redesign")
            description: Optional project description
            color: Optional color for UI tagging
        """
        self.name = name
        self.description = description
        self.color = color

    def __repr__(self):
        return f"Project(name={self.name!r}, description={self.description!r}, color={self.color!r})"


class TimeEntry:
    """Represents a time tracking entry."""

    def __init__(
        self,
        project_name: str,
        start_ts: int,
        end_ts: int = None,
        duration_ms: int = 0,
        metadata: dict = None
    ):
        """Initialize a TimeEntry.

        Args:
            project_name: Name of the project (FK to Project.name)
            start_ts: Unix epoch milliseconds (UTC) when tracking started
            end_ts: Unix epoch milliseconds (UTC) when tracking ended
            duration_ms: Computed duration as end_ts - start_ts
            metadata: Optional metadata dictionary
        """
        self.project_name = project_name
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.duration_ms = duration_ms
        self.metadata = metadata or {}

    def __repr__(self):
        return (
            f"TimeEntry(project_name={self.project_name!r}, "
            f"start_ts={self.start_ts}, end_ts={self.end_ts}, "
            f"duration_ms={self.duration_ms})"
        )
