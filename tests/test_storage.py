"""Tests for the storage module."""

import os
import tempfile
import pytest
from data.storage import Storage
from data.models import Project, TimeEntry


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_timebill.db")
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(temp_dir)


def test_storage_initialization_sqlite(temp_db_path):
    """Test Storage initializes with SQLite."""
    storage = Storage(db_path=temp_db_path)

    assert storage.db_path == temp_db_path
    assert storage.connection is not None
    assert storage.use_json_fallback is False

    storage.close()


def test_storage_creates_database_file(temp_db_path):
    """Test that Storage creates the database file."""
    storage = Storage(db_path=temp_db_path)

    assert os.path.exists(temp_db_path)

    storage.close()


def test_storage_creates_directory_if_needed():
    """Test that Storage creates parent directory if needed."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "subdir", "test.db")

    storage = Storage(db_path=db_path)

    assert os.path.exists(db_path)

    storage.close()
    os.remove(db_path)
    os.rmdir(os.path.dirname(db_path))
    os.rmdir(temp_dir)


def test_save_and_get_project_sqlite(temp_db_path):
    """Test saving and retrieving projects with SQLite."""
    storage = Storage(db_path=temp_db_path)

    project = Project(name="TestProject", description="Test Description", color="#FF0000")
    storage.save_project(project)

    projects = storage.get_projects()
    assert len(projects) == 1
    assert projects[0].name == "TestProject"
    assert projects[0].description == "Test Description"
    assert projects[0].color == "#FF0000"

    storage.close()


def test_save_project_upsert(temp_db_path):
    """Test that saving a project with same name updates it."""
    storage = Storage(db_path=temp_db_path)

    # Save initial project
    project1 = Project(name="TestProject", description="Original", color="#FF0000")
    storage.save_project(project1)

    # Save updated project with same name
    project2 = Project(name="TestProject", description="Updated", color="#00FF00")
    storage.save_project(project2)

    # Should only have one project
    projects = storage.get_projects()
    assert len(projects) == 1
    assert projects[0].description == "Updated"
    assert projects[0].color == "#00FF00"

    storage.close()


def test_save_and_get_time_entry_sqlite(temp_db_path):
    """Test saving and retrieving time entries with SQLite."""
    storage = Storage(db_path=temp_db_path)

    # First save a project
    project = Project(name="TestProject")
    storage.save_project(project)

    # Save a time entry
    entry = TimeEntry(
        project_name="TestProject",
        start_ts=1000000,
        end_ts=1005000,
        duration_ms=5000,
        metadata={"key": "value"}
    )
    storage.save_time_entry(entry)

    # Retrieve entries
    entries = storage.get_time_entries()
    assert len(entries) == 1
    assert entries[0].project_name == "TestProject"
    assert entries[0].start_ts == 1000000
    assert entries[0].end_ts == 1005000
    assert entries[0].duration_ms == 5000
    assert entries[0].metadata["key"] == "value"

    storage.close()


def test_get_time_entries_filtered_by_project(temp_db_path):
    """Test retrieving time entries filtered by project name."""
    storage = Storage(db_path=temp_db_path)

    # Save projects
    storage.save_project(Project(name="ProjectA"))
    storage.save_project(Project(name="ProjectB"))

    # Save time entries for different projects
    entry1 = TimeEntry(project_name="ProjectA", start_ts=1000, end_ts=2000, duration_ms=1000)
    entry2 = TimeEntry(project_name="ProjectB", start_ts=2000, end_ts=3000, duration_ms=1000)
    entry3 = TimeEntry(project_name="ProjectA", start_ts=3000, end_ts=4000, duration_ms=1000)

    storage.save_time_entry(entry1)
    storage.save_time_entry(entry2)
    storage.save_time_entry(entry3)

    # Get entries for ProjectA only
    entries_a = storage.get_time_entries(project_name="ProjectA")
    assert len(entries_a) == 2
    assert all(e.project_name == "ProjectA" for e in entries_a)

    # Get entries for ProjectB only
    entries_b = storage.get_time_entries(project_name="ProjectB")
    assert len(entries_b) == 1
    assert entries_b[0].project_name == "ProjectB"

    storage.close()


def test_get_all_time_entries(temp_db_path):
    """Test retrieving all time entries."""
    storage = Storage(db_path=temp_db_path)

    # Save projects and entries
    storage.save_project(Project(name="ProjectA"))
    storage.save_project(Project(name="ProjectB"))

    entry1 = TimeEntry(project_name="ProjectA", start_ts=1000, end_ts=2000, duration_ms=1000)
    entry2 = TimeEntry(project_name="ProjectB", start_ts=2000, end_ts=3000, duration_ms=1000)

    storage.save_time_entry(entry1)
    storage.save_time_entry(entry2)

    # Get all entries
    all_entries = storage.get_time_entries()
    assert len(all_entries) == 2

    storage.close()


def test_storage_persistence(temp_db_path):
    """Test that data persists across Storage instances."""
    # First instance - save data
    storage1 = Storage(db_path=temp_db_path)
    project = Project(name="PersistentProject", description="Test")
    storage1.save_project(project)
    storage1.close()

    # Second instance - load data
    storage2 = Storage(db_path=temp_db_path)
    projects = storage2.get_projects()

    assert len(projects) == 1
    assert projects[0].name == "PersistentProject"

    storage2.close()


def test_storage_json_fallback():
    """Test that Storage falls back to JSON when SQLite fails."""
    # Use an invalid path to force SQLite failure
    invalid_path = "/nonexistent/directory/that/cannot/be/created/test.db"

    storage = Storage(db_path=invalid_path)

    # Should use JSON fallback
    assert storage.use_json_fallback is True
    assert storage.connection is None


def test_json_fallback_save_and_get_project():
    """Test saving and retrieving projects with JSON fallback."""
    invalid_path = "/nonexistent/directory/test.db"
    storage = Storage(db_path=invalid_path)

    assert storage.use_json_fallback is True

    # Save a project
    project = Project(name="JSONProject", description="Test", color="#FF0000")
    storage.save_project(project)

    # Retrieve projects
    projects = storage.get_projects()
    assert len(projects) == 1
    assert projects[0].name == "JSONProject"
    assert projects[0].description == "Test"

    storage.close()


def test_json_fallback_save_and_get_time_entry():
    """Test saving and retrieving time entries with JSON fallback."""
    invalid_path = "/nonexistent/directory/test.db"
    storage = Storage(db_path=invalid_path)

    assert storage.use_json_fallback is True

    # Save project and entry
    storage.save_project(Project(name="TestProject"))

    entry = TimeEntry(
        project_name="TestProject",
        start_ts=1000,
        end_ts=2000,
        duration_ms=1000,
        metadata={"test": "data"}
    )
    storage.save_time_entry(entry)

    # Retrieve entries
    entries = storage.get_time_entries()
    assert len(entries) == 1
    assert entries[0].project_name == "TestProject"
    assert entries[0].metadata["test"] == "data"

    storage.close()


def test_json_fallback_filter_by_project():
    """Test filtering entries by project with JSON fallback."""
    invalid_path = "/nonexistent/directory/test.db"
    storage = Storage(db_path=invalid_path)

    # Save entries for different projects
    entry1 = TimeEntry(project_name="ProjectA", start_ts=1000, end_ts=2000, duration_ms=1000)
    entry2 = TimeEntry(project_name="ProjectB", start_ts=2000, end_ts=3000, duration_ms=1000)

    storage.save_time_entry(entry1)
    storage.save_time_entry(entry2)

    # Filter by project
    entries_a = storage.get_time_entries(project_name="ProjectA")
    assert len(entries_a) == 1
    assert entries_a[0].project_name == "ProjectA"

    storage.close()


def test_entry_metadata_with_none(temp_db_path):
    """Test that entries with None metadata are handled correctly."""
    storage = Storage(db_path=temp_db_path)

    storage.save_project(Project(name="TestProject"))

    entry = TimeEntry(
        project_name="TestProject",
        start_ts=1000,
        end_ts=2000,
        duration_ms=1000,
        metadata=None
    )
    storage.save_time_entry(entry)

    entries = storage.get_time_entries()
    assert len(entries) == 1
    assert entries[0].metadata == {}

    storage.close()


def test_multiple_projects(temp_db_path):
    """Test saving multiple projects."""
    storage = Storage(db_path=temp_db_path)

    projects_data = [
        Project(name="Project1", description="First", color="#FF0000"),
        Project(name="Project2", description="Second", color="#00FF00"),
        Project(name="Project3", description="Third", color="#0000FF"),
    ]

    for project in projects_data:
        storage.save_project(project)

    retrieved = storage.get_projects()
    assert len(retrieved) == 3

    # Verify all projects are present
    names = {p.name for p in retrieved}
    assert names == {"Project1", "Project2", "Project3"}

    storage.close()


def test_close_connection(temp_db_path):
    """Test that close() properly closes the connection."""
    storage = Storage(db_path=temp_db_path)

    assert storage.connection is not None

    storage.close()

    assert storage.connection is None


def test_close_with_json_fallback():
    """Test that close() works with JSON fallback."""
    invalid_path = "/nonexistent/directory/test.db"
    storage = Storage(db_path=invalid_path)

    # Should not raise an error
    storage.close()

    assert storage.connection is None
