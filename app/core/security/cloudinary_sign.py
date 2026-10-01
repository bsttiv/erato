from datetime import datetime, timezone
import secrets
import time
from typing import Any, Dict, Optional
import cloudinary.utils

from app.settings import get_settings


def sign_upload_params(
    composition_id: str,
    folder_prefix: Optional[str] = None,
    api_secret: Optional[str] = None,
    api_key: Optional[str] = None,
    cloud_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate signed upload parameters for direct client-to-Cloudinary upload.
    
    Signs exactly the parameters the client POSTs to Cloudinary: folder, tags=pending,
    timestamp and type=authenticated. resource_type is part of the upload URL path, so it
    is returned for information but never signed. The signature is computed with
    CLOUDINARY_API_SECRET.
    """
    settings = get_settings()
    prefix = folder_prefix or settings.cloudinary_folder_prefix
    secret = api_secret or settings.cloudinary_api_secret
    key = api_key or settings.cloudinary_api_key
    cname = cloud_name or settings.cloudinary_cloud_name

    timestamp = int(datetime.now(timezone.utc).timestamp())
    folder = f"{prefix}/compositions/{composition_id}"

    # Only parameters actually sent in the upload POST are signed
    params_to_sign = {
        "folder": folder,
        "tags": "pending",
        "timestamp": timestamp,
        "type": "authenticated",
    }

    signature = cloudinary.utils.api_sign_request(params_to_sign, secret)

    return {
        **params_to_sign,
        "resource_type": "video",
        "api_key": key,
        "cloud_name": cname,
        "signature": signature,
    }


def verify_upload_response(
    params_to_sign: Dict[str, Any],
    signature: str,
    api_secret: Optional[str] = None,
    expected_folder_prefix: Optional[str] = None,
    public_id: Optional[str] = None,
) -> bool:
    """Verify that a Cloudinary upload result was legitimately created and within authorized folder."""
    settings = get_settings()
    secret = api_secret or settings.cloudinary_api_secret

    # 1. Check folder prefix constraint to prevent arbitrary asset attachment
    if expected_folder_prefix and public_id:
        if not public_id.startswith(expected_folder_prefix):
            return False

    # 2. Re-compute signature
    expected_signature = cloudinary.utils.api_sign_request(params_to_sign, secret)
    return secrets.compare_digest(expected_signature, signature)


def mint_delivery_url(
    public_id: str,
    cloud_name: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    expires_at_or_ttl: Optional[int] = 3600,
) -> str:
    """Mint a short-lived signed delivery URL for authenticated Cloudinary assets."""
    settings = get_settings()
    cname = cloud_name or settings.cloudinary_cloud_name
    key = api_key or settings.cloudinary_api_key
    secret = api_secret or settings.cloudinary_api_secret

    now = int(time.time())
    ttl = expires_at_or_ttl if expires_at_or_ttl is not None else 3600

    # If ttl is relative duration in seconds (< 10000000), compute absolute timestamp
    if ttl < 100_000_000:
        expires_at = now + ttl
    else:
        expires_at = ttl

    return cloudinary.utils.private_download_url(
        public_id=public_id,
        format="",
        resource_type="video",
        type="authenticated",
        cloud_name=cname,
        api_key=key,
        api_secret=secret,
        expires_at=expires_at,
    )
