"""Tests for the encryption module."""

import os
import tempfile
import pytest
from data.encryption import (
    derive_key,
    encrypt,
    decrypt,
    encrypt_string,
    decrypt_string
)
from data.storage import Storage
from data.models import Project, TimeEntry


def test_derive_key_returns_32_bytes():
    """Test that derive_key returns exactly 32 bytes."""
    key = derive_key()
    assert len(key) == 32
    assert isinstance(key, bytes)


def test_derive_key_is_consistent():
    """Test that derive_key produces the same key on multiple calls."""
    key1 = derive_key()
    key2 = derive_key()
    assert key1 == key2


def test_encrypt_decrypt_roundtrip():
    """Test that encrypt/decrypt produces original plaintext."""
    key = derive_key()
    plaintext = b"Hello, World! This is a test message."

    ciphertext = encrypt(plaintext, key)
    decrypted = decrypt(ciphertext, key)

    assert decrypted == plaintext


def test_encrypt_produces_different_ciphertext():
    """Test that encrypting the same plaintext twice produces different ciphertext."""
    key = derive_key()
    plaintext = b"Hello, World!"

    ciphertext1 = encrypt(plaintext, key)
    ciphertext2 = encrypt(plaintext, key)

    # Should be different due to random nonce
    assert ciphertext1 != ciphertext2

    # But both should decrypt to same plaintext
    assert decrypt(ciphertext1, key) == plaintext
    assert decrypt(ciphertext2, key) == plaintext


def test_decrypt_with_wrong_key_fails():
    """Test that decryption with wrong key fails."""
    key1 = os.urandom(32)
    key2 = os.urandom(32)
    plaintext = b"Secret message"

    ciphertext = encrypt(plaintext, key1)

    with pytest.raises(ValueError, match="Authentication failed"):
        decrypt(ciphertext, key2)


def test_decrypt_tampered_data_fails():
    """Test that tampering detection works."""
    key = derive_key()
    plaintext = b"Important data"

    ciphertext = encrypt(plaintext, key)

    # Tamper with the ciphertext (flip a bit in the middle)
    tampered = bytearray(ciphertext)
    tampered[20] ^= 0xFF
    tampered = bytes(tampered)

    with pytest.raises(ValueError, match="Authentication failed"):
        decrypt(tampered, key)


def test_decrypt_truncated_data_fails():
    """Test that truncated data fails gracefully."""
    key = derive_key()
    plaintext = b"Test"

    ciphertext = encrypt(plaintext, key)

    # Truncate the ciphertext
    truncated = ciphertext[:20]

    with pytest.raises(ValueError, match="too short"):
        decrypt(truncated, key)


def test_encrypt_empty_data():
    """Test encrypting empty data."""
    key = derive_key()
    plaintext = b""

    ciphertext = encrypt(plaintext, key)
    decrypted = decrypt(ciphertext, key)

    assert decrypted == plaintext


def test_encrypt_large_data():
    """Test encrypting large data."""
    key = derive_key()
    plaintext = b"x" * 10000

    ciphertext = encrypt(plaintext, key)
    decrypted = decrypt(ciphertext, key)

    assert decrypted == plaintext


def test_encrypt_string_roundtrip():
    """Test string encryption/decryption."""
    key = derive_key()
    plaintext = "Hello, World! UTF-8: \u00e9\u00e8\u00ea"

    ciphertext = encrypt_string(plaintext, key)
    decrypted = decrypt_string(ciphertext, key)

    assert decrypted == plaintext


def test_encrypt_string_unicode():
    """Test encrypting unicode strings."""
    key = derive_key()
    plaintext = "Unicode test: \u4e2d\u6587 \u65e5\u672c\u8a9e \ud55c\uad6d\uc5b4"

    ciphertext = encrypt_string(plaintext, key)
    decrypted = decrypt_string(ciphertext, key)

    assert decrypted == plaintext


def test_invalid_key_size():
    """Test that invalid key sizes are rejected."""
    plaintext = b"Test"

    with pytest.raises(ValueError, match="Key must be 32 bytes"):
        encrypt(plaintext, b"short")

    with pytest.raises(ValueError, match="Key must be 32 bytes"):
        decrypt(b"fake ciphertext", b"short")


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_encrypted.db")
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(temp_dir)


def test_encrypted_storage_save_and_get_project(temp_db_path):
    """Test saving and retrieving encrypted projects."""
    storage = Storage(db_path=temp_db_path, encrypted=True)

    project = Project(
        name="SecretProject",
        description="This is a secret description",
        color="#FF0000"
    )
    storage.save_project(project)

    # Retrieve and verify
    projects = storage.get_projects()
    assert len(projects) == 1
    assert projects[0].name == "SecretProject"
    assert projects[0].description == "This is a secret description"
    assert projects[0].color == "#FF0000"

    storage.close()


def test_encrypted_storage_data_is_encrypted_in_db(temp_db_path):
    """Test that data is actually encrypted in the database."""
    storage = Storage(db_path=temp_db_path, encrypted=True)

    secret_description = "This is a secret description"
    project = Project(name="TestProject", description=secret_description, color="#FF0000")
    storage.save_project(project)

    storage.close()

    # Read raw data from database
    import sqlite3
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT description FROM projects WHERE name = ?", ("TestProject",))
    row = cursor.fetchone()
    conn.close()

    stored_description = row[0]

    # The stored description should NOT be plaintext
    assert stored_description != secret_description
    # It should be base64-encoded encrypted data
    assert len(stored_description) > len(secret_description)


def test_encrypted_storage_save_and_get_time_entry(temp_db_path):
    """Test saving and retrieving encrypted time entries."""
    storage = Storage(db_path=temp_db_path, encrypted=True)

    storage.save_project(Project(name="TestProject"))

    entry = TimeEntry(
        project_name="TestProject",
        start_ts=1000000,
        end_ts=1005000,
        duration_ms=5000,
        metadata={"secret": "confidential data", "user": "alice"}
    )
    storage.save_time_entry(entry)

    # Retrieve and verify
    entries = storage.get_time_entries()
    assert len(entries) == 1
    assert entries[0].project_name == "TestProject"
    assert entries[0].metadata["secret"] == "confidential data"
    assert entries[0].metadata["user"] == "alice"

    storage.close()


def test_encrypted_storage_metadata_is_encrypted_in_db(temp_db_path):
    """Test that metadata is actually encrypted in the database."""
    storage = Storage(db_path=temp_db_path, encrypted=True)

    storage.save_project(Project(name="TestProject"))

    entry = TimeEntry(
        project_name="TestProject",
        start_ts=1000000,
        end_ts=1005000,
        duration_ms=5000,
        metadata={"secret": "confidential"}
    )
    storage.save_time_entry(entry)

    storage.close()

    # Read raw data from database
    import sqlite3
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT metadata FROM time_entries WHERE project_name = ?", ("TestProject",))
    row = cursor.fetchone()
    conn.close()

    stored_metadata = row[0]

    # The stored metadata should NOT contain plaintext "confidential"
    assert "confidential" not in stored_metadata
    assert "secret" not in stored_metadata


def test_unencrypted_storage_still_works(temp_db_path):
    """Test that unencrypted storage (default) still works."""
    storage = Storage(db_path=temp_db_path, encrypted=False)

    project = Project(name="NormalProject", description="Normal description", color="#00FF00")
    storage.save_project(project)

    projects = storage.get_projects()
    assert len(projects) == 1
    assert projects[0].description == "Normal description"

    storage.close()


def test_encrypted_and_unencrypted_separate_instances(temp_db_path):
    """Test that encrypted and unencrypted instances work independently."""
    # Save unencrypted
    storage1 = Storage(db_path=temp_db_path, encrypted=False)
    storage1.save_project(Project(name="Project1", description="Plain description"))
    storage1.close()

    # Try to read with encrypted storage (should handle gracefully)
    storage2 = Storage(db_path=temp_db_path, encrypted=True)
    projects = storage2.get_projects()
    # Should return project (decryption will fail gracefully and keep original)
    assert len(projects) == 1
    storage2.close()


def test_encrypted_storage_multiple_projects(temp_db_path):
    """Test encrypting multiple projects."""
    storage = Storage(db_path=temp_db_path, encrypted=True)

    projects_data = [
        Project(name="Project1", description="Secret 1", color="#FF0000"),
        Project(name="Project2", description="Secret 2", color="#00FF00"),
        Project(name="Project3", description="Secret 3", color="#0000FF"),
    ]

    for project in projects_data:
        storage.save_project(project)

    retrieved = storage.get_projects()
    assert len(retrieved) == 3

    # Verify all descriptions are correctly decrypted
    descriptions = {p.name: p.description for p in retrieved}
    assert descriptions["Project1"] == "Secret 1"
    assert descriptions["Project2"] == "Secret 2"
    assert descriptions["Project3"] == "Secret 3"

    storage.close()


def test_encrypted_storage_multiple_entries(temp_db_path):
    """Test encrypting multiple time entries."""
    storage = Storage(db_path=temp_db_path, encrypted=True)

    storage.save_project(Project(name="ProjectA"))
    storage.save_project(Project(name="ProjectB"))

    entries_data = [
        TimeEntry(project_name="ProjectA", start_ts=1000, end_ts=2000, duration_ms=1000,
                  metadata={"note": "secret note 1"}),
        TimeEntry(project_name="ProjectB", start_ts=2000, end_ts=3000, duration_ms=1000,
                  metadata={"note": "secret note 2"}),
        TimeEntry(project_name="ProjectA", start_ts=3000, end_ts=4000, duration_ms=1000,
                  metadata={"note": "secret note 3"}),
    ]

    for entry in entries_data:
        storage.save_time_entry(entry)

    # Retrieve all entries
    all_entries = storage.get_time_entries()
    assert len(all_entries) == 3

    # Retrieve filtered entries
    entries_a = storage.get_time_entries(project_name="ProjectA")
    assert len(entries_a) == 2
    assert all(e.metadata["note"].startswith("secret note") for e in entries_a)

    storage.close()


def test_encrypted_storage_with_none_values(temp_db_path):
    """Test encrypted storage handles None values correctly."""
    storage = Storage(db_path=temp_db_path, encrypted=True)

    # Project with None description
    project = Project(name="NoDescProject", description=None, color="#FF0000")
    storage.save_project(project)

    projects = storage.get_projects()
    assert len(projects) == 1
    assert projects[0].description is None

    # Time entry with None metadata
    entry = TimeEntry(
        project_name="NoDescProject",
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


def test_encrypted_storage_json_fallback():
    """Test that encrypted storage works with JSON fallback."""
    invalid_path = "/nonexistent/directory/test.db"
    storage = Storage(db_path=invalid_path, encrypted=True)

    assert storage.use_json_fallback is True

    # Save encrypted project
    project = Project(name="JSONProject", description="Secret JSON", color="#FF0000")
    storage.save_project(project)

    # Retrieve and verify
    projects = storage.get_projects()
    assert len(projects) == 1
    assert projects[0].description == "Secret JSON"

    # Save encrypted time entry
    entry = TimeEntry(
        project_name="JSONProject",
        start_ts=1000,
        end_ts=2000,
        duration_ms=1000,
        metadata={"secret": "json data"}
    )
    storage.save_time_entry(entry)

    entries = storage.get_time_entries()
    assert len(entries) == 1
    assert entries[0].metadata["secret"] == "json data"

    storage.close()


def test_encrypted_storage_persistence(temp_db_path):
    """Test that encrypted data persists across storage instances."""
    # First instance - save encrypted data
    storage1 = Storage(db_path=temp_db_path, encrypted=True)
    project = Project(name="PersistProject", description="Secret persist", color="#FF0000")
    storage1.save_project(project)
    storage1.close()

    # Second instance - load encrypted data
    storage2 = Storage(db_path=temp_db_path, encrypted=True)
    projects = storage2.get_projects()

    assert len(projects) == 1
    assert projects[0].name == "PersistProject"
    assert projects[0].description == "Secret persist"

    storage2.close()


def test_encryption_with_special_characters():
    """Test encryption works with special characters."""
    key = derive_key()
    special_strings = [
        "Line1\nLine2\nLine3",
        "Tab\tseparated\tvalues",
        "Quote: \"test\"",
        "Backslash: \\test\\",
        "Null byte: \x00",
        "Unicode: \u2665 \u2660 \u2663 \u2666",
    ]

    for plaintext in special_strings:
        ciphertext = encrypt_string(plaintext, key)
        decrypted = decrypt_string(ciphertext, key)
        assert decrypted == plaintext
