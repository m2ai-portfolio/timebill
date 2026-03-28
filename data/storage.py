"""Storage module for TimeBill.

Provides SQLite-based storage with JSON fallback for persisting projects and time entries.
"""

import json
import sqlite3
import os
from typing import List, Optional
from data.models import Project, TimeEntry


class Storage:
    """Storage class that uses SQLite as primary storage with JSON fallback."""

    def __init__(self, db_path: str = "./data/timebill.db"):
        """Initialize storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self.use_json_fallback = False
        self.json_data = {"projects": [], "time_entries": []}

        # Try to initialize SQLite
        try:
            self._init_sqlite()
        except Exception as e:
            print(f"SQLite initialization failed: {e}. Using JSON fallback.")
            self.use_json_fallback = True
            self._init_json_fallback()

    def _init_sqlite(self):
        """Initialize SQLite database and create tables if needed."""
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Connect to database
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()

        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                name TEXT PRIMARY KEY,
                description TEXT,
                color TEXT
            )
        """)

        # Create time_entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                start_ts INTEGER NOT NULL,
                end_ts INTEGER,
                duration_ms INTEGER NOT NULL,
                metadata TEXT,
                FOREIGN KEY (project_name) REFERENCES projects(name)
            )
        """)

        self.connection.commit()

    def _init_json_fallback(self):
        """Initialize JSON fallback storage (in-memory)."""
        self.json_data = {"projects": [], "time_entries": []}

    def save_project(self, project: Project):
        """Save or update a project.

        Args:
            project: Project instance to save
        """
        if self.use_json_fallback:
            self._save_project_json(project)
        else:
            self._save_project_sqlite(project)

    def _save_project_sqlite(self, project: Project):
        """Save project to SQLite database."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO projects (name, description, color)
            VALUES (?, ?, ?)
        """, (project.name, project.description, project.color))
        self.connection.commit()

    def _save_project_json(self, project: Project):
        """Save project to JSON fallback storage."""
        # Remove existing project with same name
        self.json_data["projects"] = [
            p for p in self.json_data["projects"]
            if p["name"] != project.name
        ]
        # Add new/updated project
        self.json_data["projects"].append({
            "name": project.name,
            "description": project.description,
            "color": project.color
        })

    def save_time_entry(self, entry: TimeEntry):
        """Save a time entry.

        Args:
            entry: TimeEntry instance to save
        """
        if self.use_json_fallback:
            self._save_time_entry_json(entry)
        else:
            self._save_time_entry_sqlite(entry)

    def _save_time_entry_sqlite(self, entry: TimeEntry):
        """Save time entry to SQLite database."""
        cursor = self.connection.cursor()
        metadata_json = json.dumps(entry.metadata) if entry.metadata else None
        cursor.execute("""
            INSERT INTO time_entries (project_name, start_ts, end_ts, duration_ms, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (entry.project_name, entry.start_ts, entry.end_ts, entry.duration_ms, metadata_json))
        self.connection.commit()

    def _save_time_entry_json(self, entry: TimeEntry):
        """Save time entry to JSON fallback storage."""
        self.json_data["time_entries"].append({
            "project_name": entry.project_name,
            "start_ts": entry.start_ts,
            "end_ts": entry.end_ts,
            "duration_ms": entry.duration_ms,
            "metadata": entry.metadata
        })

    def get_projects(self) -> List[Project]:
        """Get all projects.

        Returns:
            List of Project instances
        """
        if self.use_json_fallback:
            return self._get_projects_json()
        else:
            return self._get_projects_sqlite()

    def _get_projects_sqlite(self) -> List[Project]:
        """Get all projects from SQLite database."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name, description, color FROM projects")
        rows = cursor.fetchall()
        return [Project(name=row[0], description=row[1], color=row[2]) for row in rows]

    def _get_projects_json(self) -> List[Project]:
        """Get all projects from JSON fallback storage."""
        return [
            Project(name=p["name"], description=p["description"], color=p["color"])
            for p in self.json_data["projects"]
        ]

    def get_time_entries(self, project_name: Optional[str] = None) -> List[TimeEntry]:
        """Get time entries, optionally filtered by project name.

        Args:
            project_name: Optional project name filter

        Returns:
            List of TimeEntry instances
        """
        if self.use_json_fallback:
            return self._get_time_entries_json(project_name)
        else:
            return self._get_time_entries_sqlite(project_name)

    def _get_time_entries_sqlite(self, project_name: Optional[str] = None) -> List[TimeEntry]:
        """Get time entries from SQLite database."""
        cursor = self.connection.cursor()
        if project_name:
            cursor.execute("""
                SELECT project_name, start_ts, end_ts, duration_ms, metadata
                FROM time_entries
                WHERE project_name = ?
                ORDER BY start_ts DESC
            """, (project_name,))
        else:
            cursor.execute("""
                SELECT project_name, start_ts, end_ts, duration_ms, metadata
                FROM time_entries
                ORDER BY start_ts DESC
            """)
        rows = cursor.fetchall()
        entries = []
        for row in rows:
            metadata = json.loads(row[4]) if row[4] else {}
            entries.append(TimeEntry(
                project_name=row[0],
                start_ts=row[1],
                end_ts=row[2],
                duration_ms=row[3],
                metadata=metadata
            ))
        return entries

    def _get_time_entries_json(self, project_name: Optional[str] = None) -> List[TimeEntry]:
        """Get time entries from JSON fallback storage."""
        entries = self.json_data["time_entries"]
        if project_name:
            entries = [e for e in entries if e["project_name"] == project_name]
        return [
            TimeEntry(
                project_name=e["project_name"],
                start_ts=e["start_ts"],
                end_ts=e["end_ts"],
                duration_ms=e["duration_ms"],
                metadata=e.get("metadata", {})
            )
            for e in entries
        ]

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
