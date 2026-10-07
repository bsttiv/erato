import pytest
from httpx import ASGITransport, AsyncClient
import cloudinary.utils

from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.comments import CommentsRepository
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.users import UsersRepository


@pytest.fixture(autouse=True)
async def clean_db():
    db = get_db()
    await db.users.drop()
    await db.compositions.drop()
    await db.composition_comments.drop()
    await UsersRepository(db).ensure_indexes()
    await CompositionsRepository(db).ensure_indexes()
    await CommentsRepository(db).ensure_indexes()
    yield
    await db.users.drop()
    await db.compositions.drop()
    await db.composition_comments.drop()


@pytest.mark.asyncio
async def test_demos_upload_signature_and_permission_scenarios():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner")
    stranger = await users_repo.create_user("stranger@test.com", "hash", "Stranger")

    owner_token = mint_access_token(str(owner["_id"]))
    stranger_token = mint_access_token(str(stranger["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create private composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Demo Testing Comp", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_create.json()["id"]

        # 1. Unauthenticated upload-signature request rejected -> 401
        res_unauth = await client.post(f"/api/compositions/{cid}/demos/upload-signature")
        assert res_unauth.status_code == 401

        # 2. Stranger on private composition rejected -> 404 (or 403 on public)
        res_stranger = await client.post(
            f"/api/compositions/{cid}/demos/upload-signature",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger.status_code == 404

        # 3. Authenticated owner receives signed credential without receiving file bytes
        res_sig = await client.post(
            f"/api/compositions/{cid}/demos/upload-signature",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_sig.status_code == 200
        sig_data = res_sig.json()
        assert "signature" in sig_data
        assert "timestamp" in sig_data
        assert "api_key" in sig_data
        assert sig_data["folder"] == f"erato/test/compositions/{cid}"
        assert sig_data["type"] == "authenticated"
        assert sig_data["tags"] == "pending"
        assert "tag" not in sig_data


@pytest.mark.asyncio
async def test_confirm_demo_upload_signature_verification():
    from app.main import app
    from app.settings import get_settings
    settings = get_settings()

    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner")
    owner_token = mint_access_token(str(owner["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Demo Verification Comp", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_create.json()["id"]

        folder = f"erato/test/compositions/{cid}"
        valid_public_id = f"{folder}/take_1"
        version = "1700000000"

        # Compute valid Cloudinary signature
        valid_signature = cloudinary.utils.api_sign_request(
            {"public_id": valid_public_id, "version": version},
            settings.cloudinary_api_secret,
        )

        # 1. Forged signature rejected -> 400 or 422
        res_forged = await client.post(
            f"/api/compositions/{cid}/demos",
            json={
                "public_id": valid_public_id,
                "version": version,
                "signature": "forged_hex",
                "title": "Toma 1",
                "duration_s": 120.5,
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_forged.status_code in (400, 422)

        # 2. Public ID outside authorized folder rejected -> 400 or 422
        evil_public_id = "erato/other/take_evil"
        evil_sig = cloudinary.utils.api_sign_request(
            {"public_id": evil_public_id, "version": version},
            settings.cloudinary_api_secret,
        )
        res_evil_folder = await client.post(
            f"/api/compositions/{cid}/demos",
            json={
                "public_id": evil_public_id,
                "version": version,
                "signature": evil_sig,
                "title": "Toma 1",
                "duration_s": 120.5,
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_evil_folder.status_code in (400, 422)

        # 3. Verified upload is persisted with reference fields only (no binary)
        res_success = await client.post(
            f"/api/compositions/{cid}/demos",
            json={
                "public_id": valid_public_id,
                "version": version,
                "signature": valid_signature,
                "title": "Toma 1",
                "duration_s": 120.5,
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_success.status_code == 201
        created_demo = res_success.json()
        assert created_demo["title"] == "Toma 1"
        assert created_demo["cloudinary_public_id"] == valid_public_id
        demo_id = created_demo["demo_id"]

        # Check in DB that no binary was stored
        comp_in_db = await CompositionsRepository().get_by_id(cid)
        demo_in_db = comp_in_db["demos"][0]
        assert "bytes" not in demo_in_db
        assert "file" not in demo_in_db

        # 4. Playback URL endpoint requires VIEW and mints signed delivery URL
        res_url = await client.get(
            f"/api/compositions/{cid}/demos/{demo_id}/url",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_url.status_code == 200
        url_data = res_url.json()
        assert "url" in url_data
        assert "signature=" in url_data["url"]


@pytest.mark.asyncio
async def test_timestamped_comments_on_demos():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner")
    stranger = await users_repo.create_user("stranger@test.com", "hash", "Stranger")

    owner_token = mint_access_token(str(owner["_id"]))
    stranger_token = mint_access_token(str(stranger["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Demo Comments Comp", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_create.json()["id"]

        # Add demo to composition directly
        await CompositionsRepository().add_demo(
            cid,
            demo_id="d1",
            cloudinary_public_id="erato/test/demo1",
            title="Take 1",
            duration_s=180.0,
            uploaded_by=owner["_id"],
        )

        # Owner adds comment
        res_comment = await client.post(
            f"/api/compositions/{cid}/demos/d1/comments",
            json={"timestamp_s": 24.5, "text": "Entrada de coros aca"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_comment.status_code == 201
        comment_data = res_comment.json()
        assert comment_data["timestamp_s"] == 24.5
        assert comment_data["text"] == "Entrada de coros aca"

        # List comments
        res_list = await client.get(
            f"/api/compositions/{cid}/demos/d1/comments",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_list.status_code == 200
        assert len(res_list.json()) == 1

        # Stranger on private cannot list comments -> 404
        res_stranger_list = await client.get(
            f"/api/compositions/{cid}/demos/d1/comments",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger_list.status_code == 404


@pytest.mark.asyncio
async def test_comments_expose_author_name_without_email():
    from datetime import datetime, timezone
    from bson import ObjectId
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner Name")
    owner_token = mint_access_token(str(owner["_id"]))
    headers = {"Authorization": f"Bearer {owner_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Author Name Comp", "visibility": "private"},
            headers=headers,
        )
        cid = res_create.json()["id"]
        await CompositionsRepository().add_demo(
            cid,
            demo_id="d1",
            cloudinary_public_id="erato/test/demo1",
            title="Take 1",
            duration_s=10.0,
            uploaded_by=owner["_id"],
        )

        res_comment = await client.post(
            f"/api/compositions/{cid}/demos/d1/comments",
            json={"timestamp_s": 1.0, "text": "Hola"},
            headers=headers,
        )
        assert res_comment.status_code == 201
        assert res_comment.json()["author_name"] == "Owner Name"

        # A comment whose author no longer exists
        await get_db().composition_comments.insert_one(
            {
                "composition_id": ObjectId(cid),
                "demo_id": "d1",
                "author_id": ObjectId(),
                "timestamp_s": 2.0,
                "text": "Huerfano",
                "created_at": datetime.now(timezone.utc),
            }
        )

        res_list = await client.get(
            f"/api/compositions/{cid}/demos/d1/comments", headers=headers
        )
        assert res_list.status_code == 200
        items = res_list.json()
        by_text = {c["text"]: c for c in items}
        assert by_text["Hola"]["author_name"] == "Owner Name"
        assert by_text["Huerfano"]["author_name"] is None
        assert "owner@test.com" not in res_list.text
        assert "owner@test.com" not in res_comment.text


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [1, 2, None])
async def test_demo_quota_credentials_and_parallel_confirm(limit, monkeypatch):
    import asyncio
    from app.main import app
    from app.core.plan_policy import UnlimitedPlanPolicy
    from app.deps import get_plan_policy
    from app.settings import get_settings

    removed_tags = []
    monkeypatch.setattr("cloudinary.uploader.remove_tag", lambda *args, **kwargs: removed_tags.append(args))
    barrier = asyncio.Barrier(2)
    confirming = False

    class LimitedPolicy(UnlimitedPlanPolicy):
        async def demo_limit(self, user_id):
            if confirming:
                await barrier.wait()
            return limit

    app.dependency_overrides[get_plan_policy] = lambda: LimitedPolicy()
    user = await UsersRepository().create_user("quota@test.com", "hash", "Gate User")
    uid = str(user["_id"])
    repo = CompositionsRepository()
    comp = await repo.create_composition(owner_id=uid, title="Quota")
    cid = str(comp["_id"])
    initial_count = limit - 1 if limit is not None else 21
    for index in range(initial_count):
        await repo.add_demo(cid, str(index), str(index), "Existing", 1, uid)
    headers = {"Authorization": f"Bearer {mint_access_token(uid)}"}
    settings = get_settings()
    filters = []
    collection = repo.collection
    original_update = type(collection).find_one_and_update

    async def record_update(target_collection, filter_doc, *args, **kwargs):
        filters.append(filter_doc)
        return await original_update(target_collection, filter_doc, *args, **kwargs)

    monkeypatch.setattr(type(collection), "find_one_and_update", record_update)

    def upload_body(index):
        public_id = f"{settings.cloudinary_folder_prefix}/compositions/{cid}/take_{index}"
        return {"public_id": public_id, "version": "1", "title": "Take", "duration_s": 1,
                "signature": cloudinary.utils.api_sign_request(
                    {"public_id": public_id, "version": "1"}, settings.cloudinary_api_secret)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prefix = f"/api/compositions/{cid}/demos"
        assert (await client.post(prefix + "/upload-signature", headers=headers)).status_code == 200
        confirming = True
        responses = await asyncio.gather(*[
            client.post(prefix, json=upload_body(index), headers=headers) for index in range(2)
        ])
        confirming = False
        assert sorted(r.status_code for r in responses) == ([201, 201] if limit is None else [201, 403])
        for response in responses:
            if response.status_code == 403:
                assert response.json()["error"] == "plan_gate_demo_limit"
        credential = await client.post(prefix + "/upload-signature", headers=headers)
        assert credential.status_code == (200 if limit is None else 403)
        if limit is not None:
            assert credential.json()["error"] == "plan_gate_demo_limit"
        stranger = await UsersRepository().create_user("quota-stranger@test.com", "hash", "Gate User")
        for suffix, body in [("/upload-signature", None), ("", upload_body(3))]:
            denied = await client.post(prefix + suffix, json=body, headers={
                "Authorization": f"Bearer {mint_access_token(str(stranger['_id']))}"})
            assert denied.status_code == 404
    expected_filter = {"_id": comp["_id"]}
    if limit is not None:
        expected_filter[f"demos.{limit - 1}"] = {"$exists": False}
    assert filters == [expected_filter, expected_filter]
    assert len(removed_tags) == (2 if limit is None else 1)
    stored = await repo.get_by_id(cid)
    assert len(stored["demos"]) == initial_count + (2 if limit is None else 1)


@pytest.mark.asyncio
async def test_demo_signature_at_limit_issues_no_credential(monkeypatch):
    from app.main import app
    from app.core.plan_policy import UnlimitedPlanPolicy
    from app.deps import get_plan_policy
    from unittest.mock import Mock

    class LimitOnePolicy(UnlimitedPlanPolicy):
        async def demo_limit(self, user_id):
            return 1

    from app.core.security.cloudinary_sign import sign_upload_params
    signer = Mock(wraps=sign_upload_params)
    monkeypatch.setattr("app.services.demo_service.sign_upload_params", signer)
    app.dependency_overrides[get_plan_policy] = lambda: LimitOnePolicy()
    user = await UsersRepository().create_user("credential@test.com", "hash", "Owner")
    uid = str(user["_id"])
    repo = CompositionsRepository()
    comp = await repo.create_composition(owner_id=uid, title="Full")
    cid = str(comp["_id"])
    await repo.add_demo(cid, "existing", "existing", "Existing", 1, uid)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/compositions/{cid}/demos/upload-signature",
                                     headers={"Authorization": f"Bearer {mint_access_token(uid)}"})
    assert response.status_code == 403
    assert response.json()["error"] == "plan_gate_demo_limit"
    signer.assert_not_called()
