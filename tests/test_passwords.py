import pytest
from argon2 import PasswordHasher
from app.core.security.passwords import hash_password, verify_password, needs_rehash


def test_password_hash_verify_round_trip():
    raw = "SuperSecretPassword123!"
    hashed = hash_password(raw)

    assert hashed != raw
    assert verify_password(hashed, raw) is True
    assert verify_password(hashed, "WrongPassword456!") is False


def test_plaintext_password_never_appears_in_hash():
    raw = "MyUltraSecretPassphrase!@#123"
    hashed = hash_password(raw)

    assert raw not in hashed


def test_tampered_hash_fails_verification():
    raw = "ValidPassword123!"
    hashed = hash_password(raw)

    # Tamper with the hash string
    tampered = hashed[:-5] + "XXXXX"
    assert verify_password(tampered, raw) is False


def test_needs_rehash_after_parameter_change():
    raw = "PasswordToTestRehash123!"
    current_hash = hash_password(raw)
    assert needs_rehash(current_hash) is False

    # Create a hash with outdated/different parameters (e.g., time_cost=1, memory_cost=8192)
    old_hasher = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1)
    old_hash = old_hasher.hash(raw)

    assert needs_rehash(old_hash) is True
