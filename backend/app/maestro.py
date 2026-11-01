"""Bounded synchronous calls to Maestro, under the contract of bsttiv/maestro.

No tokens, request bodies or upstream error bodies are logged: only the route, the
status and the exception class, because an exception's text can quote a header.
"""
import base64
import json
import logging
from datetime import datetime, timezone

import httpx

from app.errors import APIError

log = logging.getLogger(__name__)

# Maestro answers 401 to Erato's own credential too: that is not the user's session failing.
API_KEY_ERRORS = ("Missing API Key", "Invalid API Key")


def call_maestro(request, path, body):
    try:
        response = request.app.state.maestro.post(path, json=body)
    except httpx.TransportError as error:
        log.warning("Maestro %s failed: %s", path, type(error).__name__)
        raise APIError("session_upstream_error") from None
    if (response.status_code == 401 and path in ("/validate", "/refresh")
            and response.text not in API_KEY_ERRORS):
        raise APIError("not_authenticated")
    expected = 204 if path == "/revoke" else 200
    if response.status_code != expected:
        log.warning("Maestro %s answered %s", path, response.status_code)
        raise APIError("session_upstream_error")
    if expected == 204:
        return None
    try:
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError
        if path == "/validate" and not all(
                isinstance(data.get(name), str) and data[name] for name in ("userId", "sessionId")):
            raise ValueError
        return data
    except (ValueError, TypeError) as error:
        log.warning("Maestro %s sent an unusable body: %s", path, type(error).__name__)
        raise APIError("session_upstream_error") from None


def token_claims(token):
    """Read a pair Maestro just issued; not signature validation."""
    try:
        parts = token.split(".")
        if len(parts) != 3 or not all(parts):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
        if not isinstance(data, dict):
            raise ValueError
        if not isinstance(data.get("sub"), str) or not data["sub"].startswith("sub_"):
            raise ValueError
        if not isinstance(data.get("sid"), str) or not data["sid"]:
            raise ValueError
        return data
    except (ValueError, TypeError, UnicodeError):
        raise APIError("not_authenticated") from None


def issued_pair(data, user_id):
    """Check issuer response before committing session metadata."""
    try:
        access, refresh = data["accessToken"], data["refreshToken"]
        a, r = token_claims(access), token_claims(refresh)
        if (a["sub"] != f"sub_{user_id}" or r["sub"] != a["sub"]
                or a["sid"] != r["sid"] or a.get("typ") != "access"
                or r.get("typ") != "refresh" or isinstance(r["exp"], bool)
                or not isinstance(r["exp"], (int, float))):
            raise ValueError
        expires = datetime.fromtimestamp(r["exp"], timezone.utc)
        return {"access_token": access, "refresh_token": refresh}, a["sid"], expires
    except (APIError, KeyError, ValueError, TypeError, AttributeError, OverflowError, OSError) as error:
        log.warning("Maestro issued an unusable token pair: %s", type(error).__name__)
        raise APIError("session_upstream_error") from None
