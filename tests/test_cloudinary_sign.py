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
    assert params["tag"] == "pending"
    assert params["type"] == "authenticated"
    assert "timestamp" in params
    assert isinstance(params["timestamp"], int)
    assert params["api_key"] == api_key
    assert params["cloud_name"] == cloud_name
    assert "signature" in params
    assert len(params["signature"]) > 0


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
