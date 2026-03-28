"""Encryption module for TimeBill.

Provides AES-256-like encryption using Python standard library only.
Uses SHA-256 in CTR mode for keystream generation and HMAC for integrity.
"""

import hashlib
import hmac
import os
import uuid
import struct
from typing import Tuple


def derive_key() -> bytes:
    """Derive a 32-byte encryption key from machine-specific UUID.

    Uses PBKDF2-HMAC-SHA256 with the machine's UUID as the password and a fixed salt.
    The salt is fixed to ensure the same key is derived on the same machine.

    Returns:
        32-byte encryption key
    """
    # Get machine-specific identifier
    machine_id = str(uuid.getnode()).encode('utf-8')

    # Use a fixed salt (derived from a known string) to ensure consistency
    # In production, this could be stored in a config file
    salt = hashlib.sha256(b"timebill-v1-encryption-salt").digest()

    # Derive 32-byte key using PBKDF2
    key = hashlib.pbkdf2_hmac('sha256', machine_id, salt, iterations=100000, dklen=32)

    return key


def _generate_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    """Generate a keystream using SHA-256 in CTR mode.

    Args:
        key: 32-byte encryption key
        nonce: 16-byte nonce
        length: Number of bytes to generate

    Returns:
        Keystream bytes
    """
    keystream = bytearray()
    counter = 0

    while len(keystream) < length:
        # Combine key, nonce, and counter
        block_input = key + nonce + struct.pack('<Q', counter)
        # Generate block using SHA-256
        block = hashlib.sha256(block_input).digest()
        keystream.extend(block)
        counter += 1

    return bytes(keystream[:length])


def _xor_bytes(data: bytes, keystream: bytes) -> bytes:
    """XOR data with keystream.

    Args:
        data: Data to XOR
        keystream: Keystream to XOR with

    Returns:
        XORed bytes
    """
    return bytes(a ^ b for a, b in zip(data, keystream))


def encrypt(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt plaintext using AES-256-like encryption (CTR mode + HMAC).

    Format: [nonce (16 bytes)][ciphertext (variable)][hmac (32 bytes)]

    Args:
        plaintext: Data to encrypt
        key: 32-byte encryption key

    Returns:
        Encrypted data with nonce and HMAC
    """
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes")

    # Generate random nonce
    nonce = os.urandom(16)

    # Generate keystream
    keystream = _generate_keystream(key, nonce, len(plaintext))

    # Encrypt via XOR
    ciphertext = _xor_bytes(plaintext, keystream)

    # Compute HMAC over nonce + ciphertext
    mac = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()

    # Return nonce + ciphertext + mac
    return nonce + ciphertext + mac


def decrypt(encrypted: bytes, key: bytes) -> bytes:
    """Decrypt data encrypted with encrypt().

    Args:
        encrypted: Encrypted data (nonce + ciphertext + hmac)
        key: 32-byte encryption key

    Returns:
        Decrypted plaintext

    Raises:
        ValueError: If decryption fails (wrong key, tampered data, etc.)
    """
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes")

    if len(encrypted) < 48:  # 16 (nonce) + 0 (min ciphertext) + 32 (hmac)
        raise ValueError("Encrypted data too short")

    # Extract components
    nonce = encrypted[:16]
    ciphertext = encrypted[16:-32]
    mac = encrypted[-32:]

    # Verify HMAC
    expected_mac = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("Authentication failed - data may be tampered or wrong key")

    # Generate keystream
    keystream = _generate_keystream(key, nonce, len(ciphertext))

    # Decrypt via XOR
    plaintext = _xor_bytes(ciphertext, keystream)

    return plaintext


def encrypt_string(plaintext: str, key: bytes) -> bytes:
    """Encrypt a string.

    Args:
        plaintext: String to encrypt
        key: 32-byte encryption key

    Returns:
        Encrypted bytes
    """
    return encrypt(plaintext.encode('utf-8'), key)


def decrypt_string(encrypted: bytes, key: bytes) -> str:
    """Decrypt to a string.

    Args:
        encrypted: Encrypted data
        key: 32-byte encryption key

    Returns:
        Decrypted string
    """
    return decrypt(encrypted, key).decode('utf-8')
