from typing import Optional


def compute_initials(name: Optional[str]) -> Optional[str]:
    """Derive 1-2 uppercase characters from display name."""
    if not name:
        return None
    parts = name.strip().split()
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()
