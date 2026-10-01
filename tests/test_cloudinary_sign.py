import time
import pytest
from app.core.security.cloudinary_sign import (
    mint_delivery_url,
    sign_upload_params,
    verify_upload_response,
)


def test_sign_upload_params_structure_and_signature():
    cid = "6abdc3a18a8242d50b4e7118"
    folder_prefix = "erato/test"
    api_key = "test_key"
    api_secret = "test_secret"
    cloud_name = "test_cloud"

    params = sign_upload_params(
        composition_id=cid,
        folder_prefix=folder_prefix,
        api_secret=api_secret,
        api_key=api_key,
        cloud_name=cloud_name,
    )

    # Required fields
    assert params["folder"] == f"{folder_prefix}/compositions/{cid}"
    assert params["resource_type"] == "video"
    assert params["tags"] == "pending"
    assert "tag" not in params
    assert params["type"] == "authenticated"
    assert "timestamp" in params
    assert isinstance(params["timestamp"], int)
    assert params["api_key"] == api_key
    assert params["cloud_name"] == cloud_name
    assert "signature" in params
    assert len(params["signature"]) > 0

    # Signature covers exactly the params the client POSTs to Cloudinary
    import cloudinary.utils

    signed = {
        "folder": params["folder"],
        "tags": "pending",
        "timestamp": params["timestamp"],
        "type": "authenticated",
    }
    assert params["signature"] == cloudinary.utils.api_sign_request(signed, api_secret)

    # resource_type travels in the URL path, so it must NOT be signed
    with_resource_type = {**signed, "resource_type": "video"}
    assert params["signature"] != cloudinary.utils.api_sign_request(
        with_resource_type, api_secret
    )


def test_verify_upload_response_accepts_valid_and_rejects_forged():
    api_secret = "test_secret"
    expected_folder = "erato/test/compositions/123"
    valid_public_id = "erato/test/compositions/123/demo_abc"

    import cloudinary.utils
    upload_result_params = {
        "public_id": valid_public_id,
        "version": "123456",
    }
    valid_signature = cloudinary.utils.api_sign_request(upload_result_params, api_secret)

    # 1. Correct signature and folder -> True
    assert verify_upload_response(
        params_to_sign=upload_result_params,
        signature=valid_signature,
        api_secret=api_secret,
        expected_folder_prefix=expected_folder,
        public_id=valid_public_id,
    ) is True

    # 2. Forged signature -> False
    assert verify_upload_response(
        params_to_sign=upload_result_params,
        signature="forged_signature_hex",
        api_secret=api_secret,
        expected_folder_prefix=expected_folder,
        public_id=valid_public_id,
    ) is False


def test_verify_upload_response_rejects_wrong_folder_prefix():
    api_secret = "test_secret"
    expected_folder = "erato/test/compositions/123"
    wrong_public_id = "erato/other_composition/456/demo_evil"

    import cloudinary.utils
    upload_result_params = {
        "public_id": wrong_public_id,
        "version": "123456",
    }
    valid_signature = cloudinary.utils.api_sign_request(upload_result_params, api_secret)

    # Wrong folder prefix -> False
    assert verify_upload_response(
        params_to_sign=upload_result_params,
        signature=valid_signature,
        api_secret=api_secret,
        expected_folder_prefix=expected_folder,
        public_id=wrong_public_id,
    ) is False


def test_mint_delivery_url_produces_signed_url():
    public_id = "erato/test/compositions/123/demo_abc"
    cloud_name = "test_cloud"
    api_key = "test_key"
    api_secret = "test_secret"

    url = mint_delivery_url(
        public_id=public_id,
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        expires_at_or_ttl=3600,
    )

    assert isinstance(url, str)
    assert url.startswith("https://") or url.startswith("http://")
    assert "signature=" in url
    assert "expires_at=" in url


def _cloudinary_documented_signature(public_id: str, version: str, secret: str) -> str:
    """Signature as documented by Cloudinary for an upload RESPONSE (SHA-1, no SDK)."""
    import hashlib

    return hashlib.sha1(
        f"public_id={public_id}&version={version}{secret}".encode("utf-8")
    ).hexdigest()


def test_verify_upload_response_matches_documented_response_signature():
    secret = "test_secret"
    folder = "erato/test/compositions/123"
    public_id = f"{folder}/demo_abc"
    signature = _cloudinary_documented_signature(public_id, "1790876123", secret)

    params = {"public_id": public_id, "version": "1790876123"}
    assert verify_upload_response(
        params_to_sign=params,
        signature=signature,
        api_secret=secret,
        expected_folder_prefix=folder,
        public_id=public_id,
    ) is True

    wrong = _cloudinary_documented_signature(public_id, "1790876124", secret)
    assert verify_upload_response(
        params_to_sign=params,
        signature=wrong,
        api_secret=secret,
        expected_folder_prefix=folder,
        public_id=public_id,
    ) is False


def test_verify_upload_response_rejects_sibling_composition_folder():
    secret = "test_secret"
    folder = "erato/test/compositions/123"
    sibling_id = "erato/test/compositions/1234/demo_evil"
    signature = _cloudinary_documented_signature(sibling_id, "1", secret)

    assert verify_upload_response(
        params_to_sign={"public_id": sibling_id, "version": "1"},
        signature=signature,
        api_secret=secret,
        expected_folder_prefix=folder,
        public_id=sibling_id,
    ) is False
