from bson import ObjectId
import pytest
from starlette.requests import Request

from app.core.errors import ForbiddenError, NotFoundError
from app.core.permissions import Action
from app.deps import require


@pytest.mark.asyncio
async def test_direct_dependency_check_private_resource_raises_404():
    """Direct API dependency call without UI context: unauthorized read of private resource raises 404."""
    owner_id = ObjectId()
    stranger_id = ObjectId()
    private_record = {
        "_id": ObjectId(),
        "owner_id": owner_id,
        "visibility": "private",
        "members": [],
    }

    dep_view = require(Action.VIEW)
    fake_request = Request({"type": "http", "state": {}})

    # Non-member attempting to view private composition directly
    with pytest.raises(NotFoundError) as exc_info:
        await dep_view(
            request=fake_request,
            user={"id": str(stranger_id), "token_version": 1},
            access_record=private_record,
        )
    assert exc_info.value.status_code == 404

    # Anonymous attempting to view private composition directly
    with pytest.raises(NotFoundError) as exc_info_anon:
        await dep_view(
            request=fake_request,
            user=None,
            access_record=private_record,
        )
    assert exc_info_anon.value.status_code == 404


@pytest.mark.asyncio
async def test_direct_dependency_check_public_mutation_raises_403():
    """Direct API dependency call: mutation by non-invited user on public composition raises 403."""
    owner_id = ObjectId()
    stranger_id = ObjectId()
    public_record = {
        "_id": ObjectId(),
        "owner_id": owner_id,
        "visibility": "public",
        "members": [],
    }

    dep_edit = require(Action.EDIT)
    fake_request = Request({"type": "http", "state": {}})

    # Authenticated non-invited user attempting edit on public composition
    with pytest.raises(ForbiddenError) as exc_info:
        await dep_edit(
            request=fake_request,
            user={"id": str(stranger_id), "token_version": 1},
            access_record=public_record,
        )
    assert exc_info.value.status_code == 403

    # Anonymous user attempting edit on public composition
    with pytest.raises(ForbiddenError) as exc_info_anon:
        await dep_edit(
            request=fake_request,
            user=None,
            access_record=public_record,
        )
    assert exc_info_anon.value.status_code == 403


@pytest.mark.asyncio
async def test_direct_dependency_check_manage_sharing_and_delete():
    """Only owner can manage sharing and delete; editor gets 403, stranger on private gets 404."""
    owner_id = ObjectId()
    editor_id = ObjectId()
    stranger_id = ObjectId()
    private_record = {
        "_id": ObjectId(),
        "owner_id": owner_id,
        "visibility": "private",
        "members": [{"user_id": editor_id, "role": "editor"}],
    }

    dep_share = require(Action.MANAGE_SHARING)
    dep_delete = require(Action.DELETE)
    fake_request = Request({"type": "http", "state": {}})

    # Editor attempting manage_sharing -> 403
    with pytest.raises(ForbiddenError) as exc_share:
        await dep_share(
            request=fake_request,
            user={"id": str(editor_id), "token_version": 1},
            access_record=private_record,
        )
    assert exc_share.value.status_code == 403

    # Editor attempting delete -> 403
    with pytest.raises(ForbiddenError) as exc_del:
        await dep_delete(
            request=fake_request,
            user={"id": str(editor_id), "token_version": 1},
            access_record=private_record,
        )
    assert exc_del.value.status_code == 403

    # Stranger on private -> 404 (not 403)
    with pytest.raises(NotFoundError) as exc_stranger:
        await dep_share(
            request=fake_request,
            user={"id": str(stranger_id), "token_version": 1},
            access_record=private_record,
        )
    assert exc_stranger.value.status_code == 404
