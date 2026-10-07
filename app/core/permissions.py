from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Union
from bson import ObjectId


@dataclass(frozen=True)
class BandContext:
    band_id: str
    is_member: bool


class Role(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class Action(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    MANAGE_SHARING = "manage_sharing"
    DELETE = "delete"


# Permission Matrix from design.md:
# Action         | owner | editor | viewer | no access
# view           | yes   | yes    | yes    | 404
# edit           | yes   | yes    | 403    | 404
# manage_sharing | yes   | 403    | 403    | 404
# delete         | yes   | 403    | 403    | 404
_PERMISSIONS: Dict[Role, set[Action]] = {
    Role.OWNER: {Action.VIEW, Action.EDIT, Action.MANAGE_SHARING, Action.DELETE},
    Role.EDITOR: {Action.VIEW, Action.EDIT},
    Role.VIEWER: {Action.VIEW},
}


def can(role: Optional[Role], action: Action) -> bool:
    """Check whether a given role is permitted to perform the specified action."""
    if role is None:
        return False
    return action in _PERMISSIONS.get(role, set())


def resolve_role(
    user_id: Optional[Union[str, ObjectId]],
    access_record: Dict[str, Any],
    band: Optional[BandContext] = None,
) -> Optional[Role]:
    """Resolve owner, eligible composition role, band role, then public visibility."""
    uid_str = str(user_id) if user_id is not None else None

    # 1. Owner check
    owner_id = access_record.get("owner_id")
    if owner_id is not None and uid_str == str(owner_id):
        return Role.OWNER

    # 2. Member check (e.g. editor)
    is_band_member = band is not None and band.is_member and uid_str is not None
    if uid_str is not None and (not access_record.get("band_id") or is_band_member):
        for member in access_record.get("members", []):
            if str(member.get("user_id")) == uid_str:
                role_val = member.get("role")
                if role_val == "owner":
                    return Role.OWNER
                if role_val == "editor":
                    return Role.EDITOR
                if role_val == "viewer":
                    return Role.VIEWER

    # 3. Band membership grants the default role.
    if access_record.get("band_id") and is_band_member:
        return Role.EDITOR if access_record.get("band_editable", False) else Role.VIEWER

    # 4. Public visibility check -> viewer
    if access_record.get("visibility") == "public":
        return Role.VIEWER

    # 5. Otherwise private and not a member -> no access
    return None
