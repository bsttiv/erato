from bson import ObjectId
import pytest
from app.core.permissions import Action, Role, can, resolve_role


def test_permission_matrix_can():
    # Owner can do everything
    assert can(Role.OWNER, Action.VIEW) is True
    assert can(Role.OWNER, Action.EDIT) is True
    assert can(Role.OWNER, Action.MANAGE_SHARING) is True
    assert can(Role.OWNER, Action.DELETE) is True

    # Editor can view and edit, but not manage sharing or delete
    assert can(Role.EDITOR, Action.VIEW) is True
    assert can(Role.EDITOR, Action.EDIT) is True
    assert can(Role.EDITOR, Action.MANAGE_SHARING) is False
    assert can(Role.EDITOR, Action.DELETE) is False

    # Viewer can view, but cannot edit, manage sharing, or delete
    assert can(Role.VIEWER, Action.VIEW) is True
    assert can(Role.VIEWER, Action.EDIT) is False
    assert can(Role.VIEWER, Action.MANAGE_SHARING) is False
    assert can(Role.VIEWER, Action.DELETE) is False

    # None (no role) cannot perform any action
    assert can(None, Action.VIEW) is False
    assert can(None, Action.EDIT) is False
    assert can(None, Action.MANAGE_SHARING) is False
    assert can(None, Action.DELETE) is False


def test_resolve_role_owner():
    owner_id = ObjectId()
    doc_public = {
        "owner_id": owner_id,
        "visibility": "public",
        "members": [],
    }
    doc_private = {
        "owner_id": owner_id,
        "visibility": "private",
        "members": [],
    }

    assert resolve_role(owner_id, doc_public) == Role.OWNER
    assert resolve_role(str(owner_id), doc_public) == Role.OWNER
    assert resolve_role(owner_id, doc_private) == Role.OWNER
    assert resolve_role(str(owner_id), doc_private) == Role.OWNER


def test_resolve_role_editor():
    owner_id = ObjectId()
    member_id = ObjectId()
    doc = {
        "owner_id": owner_id,
        "visibility": "private",
        "members": [{"user_id": member_id, "role": "editor"}],
    }

    assert resolve_role(member_id, doc) == Role.EDITOR
    assert resolve_role(str(member_id), doc) == Role.EDITOR

    # Works similarly when public
    doc["visibility"] = "public"
    assert resolve_role(member_id, doc) == Role.EDITOR


def test_resolve_role_viewer_public():
    owner_id = ObjectId()
    other_user_id = ObjectId()
    doc_public = {
        "owner_id": owner_id,
        "visibility": "public",
        "members": [],
    }

    # Authenticated non-member
    assert resolve_role(other_user_id, doc_public) == Role.VIEWER
    # Anonymous (None)
    assert resolve_role(None, doc_public) == Role.VIEWER


def test_resolve_role_no_access_private():
    owner_id = ObjectId()
    other_user_id = ObjectId()
    doc_private = {
        "owner_id": owner_id,
        "visibility": "private",
        "members": [],
    }

    # Authenticated non-member on private
    assert resolve_role(other_user_id, doc_private) is None
    # Anonymous on private
    assert resolve_role(None, doc_private) is None
