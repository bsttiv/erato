from enum import Enum
from typing import Any, Dict, Optional, Union
from bson import ObjectId


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
) -> Optional[Role]:
    """Resolve the effective role of a caller on a composition access record.
    
    Roles:
    - owner: caller matches composition owner_id
    - editor: caller is in composition members with role 'editor' (or 'owner')
    - viewer: caller is anonymous or authenticated non-member, ONLY when visibility == 'public'
    - None: caller is not invited/owner on a private composition
    """
    uid_str = str(user_id) if user_id is not None else None

    # 1. Owner check
    owner_id = access_record.get("owner_id")
    if owner_id is not None and uid_str == str(owner_id):
        return Role.OWNER

    # 2. Member check (e.g. editor)
    if uid_str is not None:
        for member in access_record.get("members", []):
            if str(member.get("user_id")) == uid_str:
                role_val = member.get("role")
                if role_val == "owner":
                    return Role.OWNER
                if role_val == "editor":
                    return Role.EDITOR
                if role_val == "viewer":
                    return Role.VIEWER

    # 3. Public visibility check -> viewer
    if access_record.get("visibility") == "public":
        return Role.VIEWER

    # 4. Otherwise private and not a member -> no access
    return None
