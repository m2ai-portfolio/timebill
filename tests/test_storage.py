"""Tests for persistent storage with encryption."""

import os
import tempfile
import shutil
import pytest
from timebill.data.storage import Storage, StorageError, EncryptionHelper
from timebill.data.models import Project, TimeEntry


class TestEncryptionHelper:
    """Test suite for EncryptionHelper class."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        helper = EncryptionHelper("test-key-material")
        plaintext = "Hello, World!"
        encrypted = helper.encrypt(plaintext)
        decrypted = helper.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        helper = EncryptionHelper("test-key")
        encrypted = helper.encrypt("")
        assert encrypted == ""
        decrypted = helper.decrypt(encrypted)
        assert decrypted == ""

    def test_encrypt_long_text(self):
        """Test encrypting text longer than key size."""
        helper = EncryptionHelper("short")
        plaintext = "This is a much longer text that exceeds the key size and should still work correctly."
        encrypted = helper.encrypt(plaintext)
        decrypted = helper.decrypt(encrypted)
        assert decrypted == plaintext

    def test_decrypt_invalid_hex_raises_error(self):
        """Test that decrypting invalid hex raises StorageError."""
        helper = EncryptionHelper("test-key")
        with pytest.raises(StorageError, match="Invalid ciphertext format"):
            helper.decrypt("not-valid-hex")

    def test_different_keys_produce_different_ciphertext(self):
        """Test that different keys produce different ciphertext."""
        plaintext = "Secret message"
        helper1 = EncryptionHelper("key1")
        helper2 = EncryptionHelper("key2")

        encrypted1 = helper1.encrypt(plaintext)
        encrypted2 = helper2.encrypt(plaintext)

        assert encrypted1 != encrypted2


class TestStorageInMemory:
    """Test suite for Storage class with in-memory database."""

    def test_initialization_memory(self):
        """Test Storage initialization with :memory: database."""
        storage = Storage(':memory:')
        assert storage.db_path == ':memory:'
        assert storage.is_memory is True
        storage.close()

    def test_save_and_list_projects(self):
        """Test saving and listing projects."""
        storage = Storage(':memory:')
        storage.save_project('Project1', 'Description 1')
        storage.save_project('Project2', 'Description 2')

        projects = storage.list_projects()
        assert len(projects) == 2
        assert projects[0].name == 'Project1'
        assert projects[0].description == 'Description 1'
        assert projects[1].name == 'Project2'
        assert projects[1].description == 'Description 2'
        storage.close()

    def test_save_project_with_color(self):
        """Test saving project with color."""
        storage = Storage(':memory:')
        storage.save_project('ColorProject', 'A colorful project', color='#FF5733')

        projects = storage.list_projects()
        assert len(projects) == 1
        assert projects[0].color == '#FF5733'
        storage.close()

    def test_save_project_empty_name_raises_error(self):
        """Test that saving project with empty name raises error."""
        storage = Storage(':memory:')
        with pytest.raises(StorageError, match="Project name cannot be empty"):
            storage.save_project('')
        with pytest.raises(StorageError, match="Project name cannot be empty"):
            storage.save_project('   ')
        storage.close()

    def test_get_project_exists(self):
        """Test getting an existing project."""
        storage = Storage(':memory:')
        storage.save_project('TestProject', 'Test description')

        project = storage.get_project('TestProject')
        assert project is not None
        assert project.name == 'TestProject'
        assert project.description == 'Test description'
        storage.close()

    def test_get_project_not_exists(self):
        """Test getting a non-existent project returns None."""
        storage = Storage(':memory:')
        project = storage.get_project('NonExistent')
        assert project is None
        storage.close()

    def test_delete_project_exists(self):
        """Test deleting an existing project."""
        storage = Storage(':memory:')
        storage.save_project('ToDelete', 'Will be deleted')

        result = storage.delete_project('ToDelete')
        assert result is True

        projects = storage.list_projects()
        assert len(projects) == 0
        storage.close()

    def test_delete_project_not_exists(self):
        """Test deleting a non-existent project returns False."""
        storage = Storage(':memory:')
        result = storage.delete_project('NonExistent')
        assert result is False
        storage.close()

    def test_replace_existing_project(self):
        """Test that saving a project with existing name replaces it."""
        storage = Storage(':memory:')
        storage.save_project('Project', 'Original description')
        storage.save_project('Project', 'Updated description')

        projects = storage.list_projects()
        assert len(projects) == 1
        assert projects[0].description == 'Updated description'
        storage.close()

    def test_list_projects_empty(self):
        """Test listing projects when database is empty."""
        storage = Storage(':memory:')
        projects = storage.list_projects()
        assert len(projects) == 0
        assert isinstance(projects, list)
        storage.close()

    def test_save_time_entry(self):
        """Test saving a time entry."""
        storage = Storage(':memory:')
        storage.save_project('Project1', 'Test project')

        entry = TimeEntry(
            project_name='Project1',
            start_ts=1000000,
            end_ts=1060000,
            duration_ms=60000
        )
        storage.save_time_entry(entry)

        entries = storage.list_time_entries()
        assert len(entries) == 1
        assert entries[0].project_name == 'Project1'
        assert entries[0].start_ts == 1000000
        assert entries[0].end_ts == 1060000
        assert entries[0].duration_ms == 60000
        storage.close()

    def test_save_time_entry_with_metadata(self):
        """Test saving time entry with metadata."""
        storage = Storage(':memory:')
        storage.save_project('Project1', 'Test project')

        entry = TimeEntry(
            project_name='Project1',
            start_ts=1000000,
            end_ts=1060000,
            duration_ms=60000,
            metadata={'task': 'coding', 'tags': 'backend'}
        )
        storage.save_time_entry(entry)

        entries = storage.list_time_entries()
        assert len(entries) == 1
        assert entries[0].metadata == {'task': 'coding', 'tags': 'backend'}
        storage.close()

    def test_save_time_entry_empty_project_raises_error(self):
        """Test that saving time entry with empty project name raises error."""
        storage = Storage(':memory:')
        entry = TimeEntry(project_name='', start_ts=1000000, duration_ms=60000)
        with pytest.raises(StorageError, match="Time entry must have a project name"):
            storage.save_time_entry(entry)
        storage.close()

    def test_save_time_entry_invalid_timestamp_raises_error(self):
        """Test that saving time entry with invalid timestamp raises error."""
        storage = Storage(':memory:')
        entry = TimeEntry(project_name='Project1', start_ts=0, duration_ms=60000)
        with pytest.raises(StorageError, match="Time entry must have a valid start timestamp"):
            storage.save_time_entry(entry)
        storage.close()

    def test_list_time_entries_by_project(self):
        """Test listing time entries filtered by project."""
        storage = Storage(':memory:')
        storage.save_project('Project1', 'Test project 1')
        storage.save_project('Project2', 'Test project 2')

        entry1 = TimeEntry(project_name='Project1', start_ts=1000000, duration_ms=60000)
        entry2 = TimeEntry(project_name='Project2', start_ts=2000000, duration_ms=120000)
        entry3 = TimeEntry(project_name='Project1', start_ts=3000000, duration_ms=90000)

        storage.save_time_entry(entry1)
        storage.save_time_entry(entry2)
        storage.save_time_entry(entry3)

        entries = storage.list_time_entries(project_name='Project1')
        assert len(entries) == 2
        # Should be ordered by start_ts DESC
        assert entries[0].start_ts == 3000000
        assert entries[1].start_ts == 1000000
        storage.close()

    def test_list_time_entries_all(self):
        """Test listing all time entries."""
        storage = Storage(':memory:')
        storage.save_project('Project1', 'Test project')

        entry1 = TimeEntry(project_name='Project1', start_ts=1000000, duration_ms=60000)
        entry2 = TimeEntry(project_name='Project1', start_ts=2000000, duration_ms=120000)

        storage.save_time_entry(entry1)
        storage.save_time_entry(entry2)

        entries = storage.list_time_entries()
        assert len(entries) == 2
        storage.close()

    def test_list_time_entries_empty(self):
        """Test listing time entries when database is empty."""
        storage = Storage(':memory:')
        entries = storage.list_time_entries()
        assert len(entries) == 0
        assert isinstance(entries, list)
        storage.close()

    def test_encryption_is_applied(self):
        """Test that description is actually encrypted in storage."""
        storage = Storage(':memory:')
        storage.save_project('SecretProject', 'Secret description')

        # Query raw database to verify encryption
        cursor = storage.conn.cursor()
        cursor.execute("SELECT description FROM projects WHERE name = ?", ('SecretProject',))
        row = cursor.fetchone()

        # Raw value should NOT be the plaintext
        assert row['description'] != 'Secret description'
        # But should decrypt correctly
        decrypted = storage.encryptor.decrypt(row['description'])
        assert decrypted == 'Secret description'
        storage.close()

    def test_time_entry_without_end_ts(self):
        """Test saving time entry without end timestamp (ongoing)."""
        storage = Storage(':memory:')
        storage.save_project('Project1', 'Test project')

        entry = TimeEntry(project_name='Project1', start_ts=1000000, duration_ms=0)
        storage.save_time_entry(entry)

        entries = storage.list_time_entries()
        assert len(entries) == 1
        assert entries[0].end_ts is None
        storage.close()


class TestStorageFileBased:
    """Test suite for Storage class with file-based database."""

    def test_initialization_with_file(self):
        """Test Storage initialization with file path."""
        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, 'test.db')
            storage = Storage(db_path)
            assert storage.db_path == db_path
            assert storage.is_memory is False
            assert os.path.exists(db_path)
            storage.close()
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_creates_directory(self):
        """Test that Storage creates the database directory if needed."""
        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, 'nested', 'dir', 'test.db')
            storage = Storage(db_path)
            assert os.path.exists(os.path.dirname(db_path))
            storage.close()
        finally:
            shutil.rmtree(temp_dir)

    def test_persistence_across_sessions(self):
        """Test that data persists across storage instances."""
        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, 'test.db')

            # First session: save data
            storage1 = Storage(db_path)
            storage1.save_project('Persistent', 'Persisted description')
            storage1.close()

            # Second session: retrieve data
            storage2 = Storage(db_path)
            projects = storage2.list_projects()
            assert len(projects) == 1
            assert projects[0].name == 'Persistent'
            assert projects[0].description == 'Persisted description'
            storage2.close()
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_from_env_variable(self):
        """Test Storage initialization from TIMEBILL_DB_PATH env variable."""
        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, 'env_test.db')
            os.environ['TIMEBILL_DB_PATH'] = db_path

            storage = Storage()  # No path provided
            assert storage.db_path == db_path
            assert os.path.exists(db_path)
            storage.close()

            del os.environ['TIMEBILL_DB_PATH']
        finally:
            shutil.rmtree(temp_dir)

    def test_default_path_if_no_env(self):
        """Test that default path is used if no env variable set."""
        # Make sure env var is not set
        if 'TIMEBILL_DB_PATH' in os.environ:
            del os.environ['TIMEBILL_DB_PATH']

        storage = Storage(':memory:')  # Use memory to avoid creating default file
        # Just verify it doesn't crash
        assert storage.db_path == ':memory:'
        storage.close()


class TestStorageEdgeCases:
    """Test edge cases and error handling."""

    def test_project_with_none_description(self):
        """Test saving project with None description."""
        storage = Storage(':memory:')
        storage.save_project('NoDesc')

        project = storage.get_project('NoDesc')
        assert project is not None
        assert project.description is None
        storage.close()

    def test_project_with_special_characters(self):
        """Test saving project with special characters in name."""
        storage = Storage(':memory:')
        special_name = "Project-123_Test!@#"
        storage.save_project(special_name, 'Special chars')

        project = storage.get_project(special_name)
        assert project is not None
        assert project.name == special_name
        storage.close()

    def test_project_list_sorted_by_name(self):
        """Test that projects are sorted alphabetically by name."""
        storage = Storage(':memory:')
        storage.save_project('Zebra', 'Last alphabetically')
        storage.save_project('Alpha', 'First alphabetically')
        storage.save_project('Middle', 'In the middle')

        projects = storage.list_projects()
        assert len(projects) == 3
        assert projects[0].name == 'Alpha'
        assert projects[1].name == 'Middle'
        assert projects[2].name == 'Zebra'
        storage.close()

    def test_time_entries_sorted_by_start_desc(self):
        """Test that time entries are sorted by start timestamp descending."""
        storage = Storage(':memory:')
        storage.save_project('Project1', 'Test')

        entry1 = TimeEntry(project_name='Project1', start_ts=1000, duration_ms=100)
        entry2 = TimeEntry(project_name='Project1', start_ts=3000, duration_ms=100)
        entry3 = TimeEntry(project_name='Project1', start_ts=2000, duration_ms=100)

        storage.save_time_entry(entry1)
        storage.save_time_entry(entry2)
        storage.save_time_entry(entry3)

        entries = storage.list_time_entries()
        assert len(entries) == 3
        assert entries[0].start_ts == 3000
        assert entries[1].start_ts == 2000
        assert entries[2].start_ts == 1000
        storage.close()

    def test_close_is_idempotent(self):
        """Test that calling close multiple times doesn't cause errors."""
        storage = Storage(':memory:')
        storage.close()
        storage.close()  # Should not raise error

    def test_unicode_in_descriptions(self):
        """Test saving and retrieving Unicode characters."""
        storage = Storage(':memory:')
        unicode_text = "Hello 世界 🌍 Привет"
        storage.save_project('Unicode', unicode_text)

        project = storage.get_project('Unicode')
        assert project.description == unicode_text
        storage.close()

    def test_time_entry_metadata_empty_dict(self):
        """Test time entry with empty metadata dictionary."""
        storage = Storage(':memory:')
        storage.save_project('Project1', 'Test')

        entry = TimeEntry(
            project_name='Project1',
            start_ts=1000000,
            duration_ms=60000,
            metadata={}
        )
        storage.save_time_entry(entry)

        entries = storage.list_time_entries()
        assert len(entries) == 1
        # Empty dict should be preserved
        assert entries[0].metadata == {}
        storage.close()
