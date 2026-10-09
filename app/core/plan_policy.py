from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class PlanPolicy(Protocol):
    """Port for plan and quota evaluation and transfer lifecycle hooks."""

    # User-scoped entitlement questions: acting user only, no composition or band context.
    async def can_share_with_people(self, user_id: str) -> bool: ...
    async def can_create_band(self, user_id: str) -> bool: ...
    async def can_view_history(self, user_id: str) -> bool: ...
    async def demo_limit(self, user_id: str) -> Optional[int]: ...

    # Band-scoped questions.
    async def seat_limit(self, band_id: str) -> Optional[int]: ...
    async def is_band_active(self, band_id: str) -> bool: ...

    # Transfer hook: called on accept BEFORE the core swaps owner and roles.
    async def confirm_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> bool: ...
    # Called only after a confirmed transfer whose owner swap was lost, so the host can undo what confirm did.
    async def abort_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> None: ...


class UnlimitedPlanPolicy:
    """Default policy allowing all features with no limits."""

    async def can_share_with_people(self, user_id: str) -> bool:
        return True

    async def can_create_band(self, user_id: str) -> bool:
        return True

    async def can_view_history(self, user_id: str) -> bool:
        return True

    async def demo_limit(self, user_id: str) -> Optional[int]:
        return None

    async def seat_limit(self, band_id: str) -> Optional[int]:
        return None

    async def is_band_active(self, band_id: str) -> bool:
        return True

    async def confirm_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> bool:
        return True

    async def abort_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> None:
        return None


@dataclass
class HostCapabilities:
    extensions_available: bool = False
