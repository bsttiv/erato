"""Cloudinary access for demo audio. Audio is a `video` resource; delivery is private."""
import time
from urllib.parse import unquote, urlsplit

import cloudinary.api
import cloudinary.exceptions
import cloudinary.uploader
import cloudinary.utils

from app.errors import APIError

ASSET = {'resource_type': 'video', 'type': 'authenticated'}
PLAYBACK_SECONDS = 15 * 60  # File 10: playback URLs last 15 minutes.


def credentials(config):
    url = urlsplit(config['CLOUDINARY_URL'])
    if url.scheme != 'cloudinary' or not url.hostname or not url.username or not url.password:
        raise APIError('storage_unavailable')
    return {'cloud_name': url.netloc.rpartition('@')[2], 'api_key': unquote(url.username),
            'api_secret': unquote(url.password)}


def upload_target(config, public_id):
    keys = credentials(config)
    # overwrite is signed off: replaying these fields must not swap a confirmed asset.
    signed = {'overwrite': 'false', 'public_id': public_id, 'timestamp': int(time.time()),
              'type': ASSET['type']}
    signature = cloudinary.utils.api_sign_request(signed, keys['api_secret'])
    return {'upload_url': f'https://api.cloudinary.com/v1_1/{keys["cloud_name"]}/video/upload',
            'fields': {**signed, 'api_key': keys['api_key'], 'signature': signature}}


def read_asset(config, public_id):
    """The asset's details as Cloudinary reports them, or None when it does not exist."""
    keys = credentials(config)
    try:
        return cloudinary.api.resource(public_id, media_metadata=True, **ASSET, **keys)
    except cloudinary.exceptions.NotFound:
        return None
    except Exception:  # the SDK raises bare Exception for statuses it does not map
        raise APIError('storage_unavailable') from None


def destroy_asset(config, public_id):
    # "not found" counts as deleted, so a retry after a partial failure completes.
    keys = credentials(config)
    try:
        result = cloudinary.uploader.destroy(public_id, invalidate=True, **ASSET, **keys)
    except Exception:  # the SDK raises bare Exception for statuses it does not map
        raise APIError('storage_unavailable') from None
    if result.get('result') not in ('ok', 'not found'):
        raise APIError('storage_unavailable')


def playback_link(config, demo):
    return {'url': cloudinary.utils.private_download_url(
        demo['cloudinary_public_id'], demo['format'], expires_at=int(time.time()) + PLAYBACK_SECONDS,
        **ASSET, **credentials(config)), 'expires_in': PLAYBACK_SECONDS}
