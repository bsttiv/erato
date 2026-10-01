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
