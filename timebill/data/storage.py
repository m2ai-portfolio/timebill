"""Storage implementation for TimeBill with encryption."""

import sqlite3
import json
import os
import hashlib
import uuid
import logging
from typing import Optional, List, Dict, Any
from timebill.data.models import Project, TimeEntry


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class EncryptionHelper:
    """
    Simple encryption helper using XOR stream cipher with SHA-256 key derivation.

    WARNING: This provides basic obfuscation for local data protection, not
    cryptographically secure encryption. The XOR stream cipher is vulnerable to
    known-plaintext attacks and should NOT be used for protecting sensitive data
    in adversarial environments. This implementation is constrained to stdlib-only
    and does not use AES-256 or other secure encryption algorithms.

    For production use cases requiring real security, use the cryptography library
    with AES-256-GCM or similar authenticated encryption.
    """

    def __init__(self, key_material: str):
        """
        Initialize encryption helper with key material.

        Args:
            key_material: String to derive encryption key from.
        """
        # Derive a 32-byte key from the material using SHA-256
        self.key = hashlib.sha256(key_material.encode('utf-8')).digest()

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using XOR stream cipher.

        Args:
            plaintext: String to encrypt.

        Returns:
            Hex-encoded encrypted string.
        """
        if not plaintext:
            return ""

        plaintext_bytes = plaintext.encode('utf-8')
        encrypted = bytearray()

        for i, byte in enumerate(plaintext_bytes):
            key_byte = self.key[i % len(self.key)]
            encrypted.append(byte ^ key_byte)

        return encrypted.hex()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext using XOR stream cipher.

        Args:
            ciphertext: Hex-encoded encrypted string.

        Returns:
            Decrypted plaintext string.
        """
        if not ciphertext:
            return ""

        try:
            ciphertext_bytes = bytes.fromhex(ciphertext)
        except ValueError as e:
            raise StorageError(f"Invalid ciphertext format: {e}")

        decrypted = bytearray()

        for i, byte in enumerate(ciphertext_bytes):
            key_byte = self.key[i % len(self.key)]
            decrypted.append(byte ^ key_byte)

        return decrypted.decode('utf-8')


class Storage:
    """
    Persistent storage for TimeBill with SQLite backend and encryption.

    Uses XOR stream cipher with SHA-256 key derivation (basic obfuscation, not
    cryptographically secure) with machine UUID-derived key.
    Supports both file-based and in-memory SQLite databases.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize storage with SQLite database.

        Args:
            db_path: Path to SQLite database file. If None, reads from
                    TIMEBILL_DB_PATH env var (default: ./data/timebill.db).
                    Use ':memory:' for in-memory database.
        """
        # Determine database path
        if db_path is None:
            db_path = os.environ.get('TIMEBILL_DB_PATH', './data/timebill.db')

        self.db_path = db_path
        self.is_memory = db_path == ':memory:'

        # Create data directory if needed (not for :memory:)
        if not self.is_memory:
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except OSError as e:
                    raise StorageError(f"Failed to create database directory: {e}")

        # Initialize encryption helper with machine UUID
        machine_id = self._get_machine_id()
        self.encryptor = EncryptionHelper(machine_id)

        # Connect to database
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise StorageError(f"Failed to connect to database: {e}")

        # Initialize schema
        self._init_schema()

    def _get_machine_id(self) -> str:
        """
        Get machine-specific identifier for encryption key derivation.

        Returns:
            Machine UUID as string.
        """
        try:
            # Try to get actual machine UUID
            machine_uuid = uuid.getnode()
            return str(machine_uuid)
        except Exception as e:
            # Fallback to a fixed UUID for testing
            logging.warning(f"Failed to get machine UUID: {e}. Using default.")
            return "timebill-default-machine-id"

    def _init_schema(self):
        """Initialize database schema with projects and time_entries tables."""
        try:
            cursor = self.conn.cursor()

            # Enable foreign key enforcement
            cursor.execute("PRAGMA foreign_keys = ON")

            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    color TEXT
                )
            """)

            # Time entries table
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

            self.conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to initialize database schema: {e}")

    def save_project(self, name: str, description: Optional[str] = None,
                    color: Optional[str] = None):
        """
        Save a project to storage.

        Args:
            name: Project name (unique identifier).
            description: Optional project description.
            color: Optional color code for the project.
        """
        if not name or not name.strip():
            raise StorageError("Project name cannot be empty")

        try:
            cursor = self.conn.cursor()

            # Encrypt sensitive fields
            encrypted_desc = self.encryptor.encrypt(description) if description else None

            cursor.execute("""
                INSERT OR REPLACE INTO projects (name, description, color)
                VALUES (?, ?, ?)
            """, (name, encrypted_desc, color))

            self.conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save project: {e}")

    def list_projects(self) -> List[Project]:
        """
        Retrieve all projects from storage.

        Returns:
            List of Project dataclass instances.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name, description, color FROM projects ORDER BY name")
            rows = cursor.fetchall()

            projects = []
            for row in rows:
                # Decrypt description
                decrypted_desc = None
                if row['description']:
                    try:
                        decrypted_desc = self.encryptor.decrypt(row['description'])
                    except StorageError as e:
                        # If decryption fails, treat as None
                        logging.warning(f"Failed to decrypt description for project '{row['name']}': {e}")
                        decrypted_desc = None

                projects.append(Project(
                    name=row['name'],
                    description=decrypted_desc,
                    color=row['color']
                ))

            return projects
        except sqlite3.Error as e:
            raise StorageError(f"Failed to list projects: {e}")

    def get_project(self, name: str) -> Optional[Project]:
        """
        Get a single project by name.

        Args:
            name: Project name to retrieve.

        Returns:
            Project instance if found, None otherwise.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name, description, color FROM projects WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            # Decrypt description
            decrypted_desc = None
            if row['description']:
                try:
                    decrypted_desc = self.encryptor.decrypt(row['description'])
                except StorageError as e:
                    logging.warning(f"Failed to decrypt description for project '{row['name']}': {e}")
                    decrypted_desc = None

            return Project(
                name=row['name'],
                description=decrypted_desc,
                color=row['color']
            )
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get project: {e}")

    def delete_project(self, name: str) -> bool:
        """
        Delete a project from storage.

        Args:
            name: Project name to delete.

        Returns:
            True if project was deleted, False if it didn't exist.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM projects WHERE name = ?", (name,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete project: {e}")

    def save_time_entry(self, entry: TimeEntry):
        """
        Save a time entry to storage.

        Args:
            entry: TimeEntry instance to save.
        """
        if not entry.project_name or not entry.project_name.strip():
            raise StorageError("Time entry must have a project name")

        if entry.start_ts <= 0:
            raise StorageError("Time entry must have a valid start timestamp")

        try:
            cursor = self.conn.cursor()

            # Encrypt metadata if present
            encrypted_metadata = None
            if entry.metadata is not None:
                metadata_json = json.dumps(entry.metadata)
                encrypted_metadata = self.encryptor.encrypt(metadata_json)

            cursor.execute("""
                INSERT INTO time_entries
                (project_name, start_ts, end_ts, duration_ms, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (entry.project_name, entry.start_ts, entry.end_ts,
                  entry.duration_ms, encrypted_metadata))

            self.conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save time entry: {e}")

    def list_time_entries(self, project_name: Optional[str] = None) -> List[TimeEntry]:
        """
        Retrieve time entries from storage.

        Args:
            project_name: Optional project name to filter by.

        Returns:
            List of TimeEntry dataclass instances.
        """
        try:
            cursor = self.conn.cursor()

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
                # Decrypt metadata
                metadata = {}
                if row['metadata']:
                    try:
                        decrypted_json = self.encryptor.decrypt(row['metadata'])
                        metadata = json.loads(decrypted_json)
                    except (StorageError, json.JSONDecodeError) as e:
                        logging.warning(f"Failed to decrypt metadata for time entry (project: {row['project_name']}): {e}")
                        metadata = {}

                entries.append(TimeEntry(
                    project_name=row['project_name'],
                    start_ts=row['start_ts'],
                    end_ts=row['end_ts'],
                    duration_ms=row['duration_ms'],
                    metadata=metadata
                ))

            return entries
        except sqlite3.Error as e:
            raise StorageError(f"Failed to list time entries: {e}")

    def close(self):
        """Close the database connection."""
        if hasattr(self, 'conn'):
            try:
                self.conn.close()
            except sqlite3.Error:
                pass  # Ignore errors on close

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
