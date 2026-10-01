from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# Pinned Argon2id parameters per design.md:
# OWASP minimum configuration: time cost 2, memory 19 MiB (19456 KiB), parallelism 1.
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 19456  # 19 MiB in KiB
ARGON2_PARALLELISM = 1

_hasher = PasswordHasher(
    time_cost=ARGON2_TIME_COST,
    memory_cost=ARGON2_MEMORY_COST,
    parallelism=ARGON2_PARALLELISM,
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id with pinned parameters."""
    return _hasher.hash(password)


def verify_password(hash_str: str, password: str) -> bool:
    """Verify a plaintext password against an Argon2 hash.
    
    Returns True if valid, False if mismatch or invalid/tampered hash.
    """
    try:
        return _hasher.verify(hash_str, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(hash_str: str) -> bool:
    """Check whether the given hash was created with parameters different from current pinned values."""
    try:
        return _hasher.check_needs_rehash(hash_str)
    except (VerificationError, InvalidHashError):
        return True
