from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
import pytest
from fastapi import FastAPI, Depends, Request
from httpx import ASGITransport, AsyncClient

from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.core.permissions import Action, Role
from app.core.security.tokens import mint_access_token
from app.db.repositories.compositions import CompositionsRepository
from app.deps import AuthContext, composition_access, require


# Mock helper app to test require(...) dependency in isolation
mock_app = FastAPI()

@mock_app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

@mock_app.get("/test/compositions/{composition_id}/view")
async def view_endpoint(auth: AuthContext = Depends(require(Action.VIEW))):
    return {"status": "ok", "role": auth.role, "comp_id": str(auth.composition["_id"])}

@mock_app.put("/test/compositions/{composition_id}/edit")
async def edit_endpoint(auth: AuthContext = Depends(require(Action.EDIT))):
    return {"status": "ok", "role": auth.role}

@mock_app.post("/test/compositions/{composition_id}/multi-check")
async def multi_check_endpoint(
    req: Request,
    auth1: AuthContext = Depends(require(Action.VIEW)),
    auth2: AuthContext = Depends(require(Action.VIEW)),
):
    # Verify both dependencies resolve the same cached access record
    return {"status": "ok", "cached": hasattr(req.state, "composition_access")}



@pytest.mark.asyncio
async def test_require_caches_access_record_on_request_state():
    owner_id = ObjectId()
    comp_id = ObjectId()
    access_doc = {
        "_id": comp_id,
        "owner_id": owner_id,
        "visibility": "public",
        "members": [],
    }

    with patch.object(CompositionsRepository, "get_by_id", new_callable=AsyncMock) as mock_get_by_id:
        mock_get_by_id.return_value = access_doc

        async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as client:

            res = await client.post(f"/test/compositions/{comp_id}/multi-check")
            assert res.status_code == 200
            assert res.json()["status"] == "ok"
            assert res.json()["cached"] is True

            # Assert Mongo read happened exactly once despite multiple require() calls
            assert mock_get_by_id.call_count == 1


@pytest.mark.asyncio
async def test_require_unauthorized_read_private_returns_404():
    owner_id = ObjectId()
    comp_id = ObjectId()
    private_doc = {
        "_id": comp_id,
        "owner_id": owner_id,
        "visibility": "private",
        "members": [],
    }

    with patch.object(CompositionsRepository, "get_by_id", new_callable=AsyncMock) as mock_get_by_id:
        mock_get_by_id.return_value = private_doc

        async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as client:

            # Anonymous on private -> 404
            res_anon = await client.get(f"/test/compositions/{comp_id}/view")
            assert res_anon.status_code == 404

            # Non-member authenticated user on private -> 404 (not 403, preventing existence probing)
            other_user_id = str(ObjectId())
            token = mint_access_token(other_user_id)
            res_non_member = await client.get(
                f"/test/compositions/{comp_id}/view",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert res_non_member.status_code == 404


@pytest.mark.asyncio
async def test_require_viewer_edit_returns_403():
    owner_id = ObjectId()
    comp_id = ObjectId()
    public_doc = {
        "_id": comp_id,
        "owner_id": owner_id,
        "visibility": "public",
        "members": [],
    }

    with patch.object(CompositionsRepository, "get_by_id", new_callable=AsyncMock) as mock_get_by_id:
        mock_get_by_id.return_value = public_doc

        async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as client:

            # Viewer can view public -> 200
            res_view = await client.get(f"/test/compositions/{comp_id}/view")
            assert res_view.status_code == 200
            assert res_view.json()["role"] == "viewer"

            # Viewer attempting edit -> 403 (insufficient permissions, existence already known)
            res_edit = await client.put(f"/test/compositions/{comp_id}/edit")
            assert res_edit.status_code == 403


@pytest.mark.asyncio
async def test_require_owner_and_editor_succeed():
    owner_id = ObjectId()
    editor_id = ObjectId()
    comp_id = ObjectId()

    doc = {
        "_id": comp_id,
        "owner_id": owner_id,
        "visibility": "private",
        "members": [{"user_id": editor_id, "role": "editor"}],
    }

    with patch.object(CompositionsRepository, "get_by_id", new_callable=AsyncMock) as mock_get_by_id:
        mock_get_by_id.return_value = doc

        async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as client:

            # Owner edit -> 200
            owner_token = mint_access_token(str(owner_id))
            res_owner = await client.put(
                f"/test/compositions/{comp_id}/edit",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            assert res_owner.status_code == 200
            assert res_owner.json()["role"] == "owner"

            # Editor edit -> 200
            editor_token = mint_access_token(str(editor_id))
            res_editor = await client.put(
                f"/test/compositions/{comp_id}/edit",
                headers={"Authorization": f"Bearer {editor_token}"},
            )
            assert res_editor.status_code == 200
            assert res_editor.json()["role"] == "editor"


@pytest.mark.parametrize("has_band,has_user", [(True, True), (False, True), (True, False)])
async def test_band_context_projected_once(has_band, has_user):
    from app.deps import band_context
    uid, bid = ObjectId(), ObjectId()
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value={"owner_id": ObjectId(), "members": [{"user_id": uid}]})
    with patch("app.deps.BandsRepository") as repo:
        repo.return_value.collection = collection
        context = await band_context(Request({"type": "http"}),
                                     {"id": str(uid)} if has_user else None,
                                     {"band_id": bid if has_band else None})
    if has_band and has_user:
        assert context.band_id == str(bid) and context.is_member
        collection.find_one.assert_awaited_once_with(
            {"_id": bid}, {"owner_id": 1, "members.user_id": 1})
    else:
        assert context is None
        collection.find_one.assert_not_awaited()


@pytest.mark.parametrize("action", list(Action))
@pytest.mark.parametrize("identity", ["owner", "editor", "stranger"])
async def test_inactive_band_require(action, identity):
    from app.core.permissions import BandContext
    uid, bid = ObjectId(), ObjectId()
    doc = {"owner_id": uid if identity == "owner" else ObjectId(), "band_id": bid,
           "band_editable": True, "visibility": "private", "members": []}
    policy = MagicMock()
    policy.is_band_active = AsyncMock(return_value=False)
    kwargs = dict(request=Request({"type": "http"}), user={"id": str(uid)},
                  access_record=doc, band=BandContext(str(bid), identity != "stranger"), policy=policy)
    if identity == "stranger":
        with pytest.raises(NotFoundError):
            await require(action)(**kwargs)
    elif identity == "editor" and action != Action.VIEW:
        with pytest.raises(ForbiddenError) as exc:
            await require(action)(**kwargs)
        assert exc.value.code == "band_inactive"
        policy.is_band_active.assert_awaited_once_with(str(bid))
    else:
        assert (await require(action)(**kwargs)).role == (Role.OWNER if identity == "owner" else Role.EDITOR)
    if identity != "editor" or action == Action.VIEW:
        policy.is_band_active.assert_not_awaited()
