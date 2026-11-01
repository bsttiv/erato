"""Accounts and session endpoints, using the approved flat-module architecture."""
from datetime import timedelta
import hashlib
import math
import re
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from bson import ObjectId
from fastapi import APIRouter, Cookie, Depends, Header, Request, Response
from pydantic import BaseModel, ConfigDict, StrictStr, field_validator, model_validator
from pymongo.errors import DuplicateKeyError

from app.errors import APIError
from app.maestro import call_maestro, issued_pair

router = APIRouter()
password_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
DUMMY_HASH = password_hasher.hash("not-a-real-account-password")
WINDOW = timedelta(minutes=15)
MAX_ATTEMPTS = 5
REFRESH_COOKIE = "refresh_token"
# The browser sees the backend under /api (Vercel and the Vite proxy both mount it there).
REFRESH_COOKIE_PATH = "/api/auth"
REFRESH_TTL = 7 * 24 * 3600


def sha256(value):
    return hashlib.sha256(value.encode()).hexdigest()


def new_id():
    """One ObjectId constructor for persistent and embedded identifiers."""
    return ObjectId()


def public_user(user):
    return {key: user[key] for key in ("username", "display_name")}


def own_user(user):
    return {**public_user(user), "email": user["email"]}


def normalize_username(value):
    value = value.lower()
    if not 3 <= len(value) <= 30 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("Invalid username")
    return value


def normalize_email(value):
    value = value.lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValueError("Invalid email")
    return value


def normalize_display_name(value):
    value = value.strip()
    if not 1 <= len(value) <= 60:
        raise ValueError("Invalid display name")
    return value


def validate_password(value):
    if not 8 <= len(value) <= 128:
        raise ValueError("Invalid password length")
    return value


class Registration(BaseModel):
    email: StrictStr
    username: StrictStr
    display_name: StrictStr
    password: StrictStr
    _email = field_validator("email")(normalize_email)
    _username = field_validator("username")(normalize_username)
    _name = field_validator("display_name")(normalize_display_name)
    _password = field_validator("password")(validate_password)


class Login(BaseModel):
    email: StrictStr
    password: StrictStr
    _email = field_validator("email")(normalize_email)


class ProfilePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: StrictStr | None = None
    display_name: StrictStr | None = None

    @model_validator(mode="after")
    def normalize(self):
        if not self.model_fields_set:
            raise ValueError("Empty patch")
        if "username" in self.model_fields_set:
            if self.username is None:
                raise ValueError("Invalid username")
            self.username = normalize_username(self.username)
        if "display_name" in self.model_fields_set:
            if self.display_name is None:
                raise ValueError("Invalid display name")
            self.display_name = normalize_display_name(self.display_name)
        return self


class EmailChange(BaseModel):
    email: StrictStr
    current_password: StrictStr
    _email = field_validator("email")(normalize_email)


class PasswordChange(BaseModel):
    current_password: StrictStr
    new_password: StrictStr
    _password = field_validator("new_password")(validate_password)


Device = Annotated[str, Header(alias="X-Device-Id", min_length=1)]


def verify_password(value, encoded):
    try:
        return password_hasher.verify(encoded, value)
    except (VerificationError, InvalidHashError):
        return False


def device_label(user_agent):
    browser = next((name for marker, name in (
        ("Firefox/", "Firefox"), ("Edg/", "Edge"), ("Chrome/", "Chrome"),
        ("Safari/", "Safari"),
    ) if marker in user_agent), None)
    system = next((name for marker, name in (
        ("Android", "Android"), ("iPhone", "iOS"), ("Windows", "Windows"),
        ("Macintosh", "macOS"), ("Linux", "Linux"),
    ) if marker in user_agent), None)
    return f"{browser} en {system}" if browser and system else "Dispositivo desconocido"


def attempt_key(request, email):
    # First proxy-chain address; production must ensure the edge overwrites XFF.
    ip = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    if not ip:
        ip = request.client.host if request.client else "unknown"
    return {"email_hash": sha256(email), "ip": ip}


def check_rate_limit(request, email):
    now = request.app.state.clock()
    attempts = list(request.app.state.db.login_attempts.find({
        **attempt_key(request, email), "created_at": {"$gt": now - WINDOW},
    }).sort("created_at", 1).limit(MAX_ATTEMPTS))
    if len(attempts) >= MAX_ATTEMPTS:
        seconds = max(1, math.ceil((attempts[0]["created_at"] + WINDOW - now).total_seconds()))
        raise APIError("rate_limited", headers={"Retry-After": str(seconds)})


def record_failure(request, email):
    request.app.state.db.login_attempts.insert_one({
        **attempt_key(request, email), "created_at": request.app.state.clock(),
    })


def check_current_password(request, user, password):
    check_rate_limit(request, user["email"])
    if not verify_password(password, user["password_hash"]):
        record_failure(request, user["email"])
        raise APIError("invalid_credentials")


def duplicate_error(error):
    keys = (error.details or {}).get("keyPattern", {})
    raise APIError("email_taken" if "email" in keys else "username_taken") from None


def mint_session(request, user, device):
    data = call_maestro(request, "/mint", {"userId": str(user["_id"]), "context": device})
    tokens, sid, expires = issued_pair(data, user["_id"])
    now = request.app.state.clock()
    request.app.state.db.sessions.insert_one({
        "_id": new_id(), "user_id": user["_id"], "sid": sid,
        "refresh_token_hash": sha256(tokens["refresh_token"]),
        "device": device_label(request.headers.get("user-agent", "")),
        "last_access_at": now, "created_at": now, "expires_at": expires,
    })
    return tokens


def set_refresh_cookie(response, tokens):
    """Move the refresh token out of the JSON body into an httpOnly cookie."""
    response.set_cookie(REFRESH_COOKIE, tokens.pop("refresh_token"), max_age=REFRESH_TTL,
                        path=REFRESH_COOKIE_PATH, httponly=True, secure=True, samesite="strict")


def authenticated(request: Request):
    authorization = request.headers.get("authorization", "").split()
    device = request.headers.get("x-device-id")
    if len(authorization) != 2 or authorization[0].lower() != "bearer" or not device:
        raise APIError("not_authenticated")
    token = authorization[1]
    admitted = call_maestro(request, "/validate", {"token": token, "fingerprint": device})
    user_id = admitted["userId"]
    if not ObjectId.is_valid(user_id):
        raise APIError("not_authenticated")
    db = request.app.state.db
    user = db.users.find_one({"_id": ObjectId(user_id)})
    session = db.sessions.find_one({"sid": admitted["sessionId"], "user_id": ObjectId(user_id),
                                    "expires_at": {"$gt": request.app.state.clock()}})
    if user is None or session is None:
        raise APIError("not_authenticated")
    request.state.session = session
    request.state.access_token = token
    return user, session


Current = Annotated[tuple, Depends(authenticated)]


@router.post("/auth/register", status_code=201)
def register(body: Registration, request: Request, response: Response, x_device_id: Device):
    now = request.app.state.clock()
    user = {"_id": new_id(), "email": body.email, "username": body.username,
            "display_name": body.display_name, "password_hash": password_hasher.hash(body.password),
            "created_at": now, "updated_at": now}
    try:
        request.app.state.db.users.insert_one(user)
    except DuplicateKeyError as error:
        duplicate_error(error)
    result = {"user": public_user(user)}
    try:
        tokens = mint_session(request, user, x_device_id)
        set_refresh_cookie(response, tokens)
        result.update(tokens)
    except APIError as error:
        if error.code != "session_upstream_error":
            raise
    return result


@router.post("/auth/login")
def login(body: Login, request: Request, response: Response, x_device_id: Device):
    check_rate_limit(request, body.email)
    user = request.app.state.db.users.find_one({"email": body.email})
    valid = verify_password(body.password, user["password_hash"] if user else DUMMY_HASH)
    if not valid or user is None:
        record_failure(request, body.email)
        raise APIError("invalid_credentials")
    tokens = mint_session(request, user, x_device_id)
    request.app.state.db.login_attempts.delete_many(attempt_key(request, body.email))
    set_refresh_cookie(response, tokens)
    return tokens


@router.post("/auth/refresh")
def refresh(request: Request, response: Response, x_device_id: Device,
            refresh_token: Annotated[str | None, Cookie()] = None):
    if not refresh_token:
        raise APIError("not_authenticated")
    db = request.app.state.db
    old = db.sessions.find_one({"refresh_token_hash": sha256(refresh_token),
                                "expires_at": {"$gt": request.app.state.clock()}})
    if old is None or db.users.find_one({"_id": old["user_id"]}) is None:
        raise APIError("not_authenticated")
    data = call_maestro(request, "/refresh", {
        "refresh": refresh_token, "fingerprint": x_device_id,
    })
    tokens, sid, expires = issued_pair(data, old["user_id"])
    result = db.sessions.update_one({"_id": old["_id"], "sid": sid,
                                     "refresh_token_hash": old["refresh_token_hash"]}, {"$set": {
        "refresh_token_hash": sha256(tokens["refresh_token"]),
        "last_access_at": request.app.state.clock(), "expires_at": expires,
    }})
    if result.matched_count != 1:
        raise APIError("not_authenticated")
    set_refresh_cookie(response, tokens)
    return tokens


def revoke_current_session(request, session):
    """Maestro revokes by token, and Erato only holds the requester's."""
    call_maestro(request, "/revoke", {"token": request.state.access_token})
    request.app.state.db.sessions.delete_one({"_id": session["_id"]})


@router.post("/auth/logout", status_code=204)
def logout(request: Request, current: Current):
    revoke_current_session(request, current[1])
    response = Response(status_code=204)
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH, httponly=True,
                           secure=True, samesite="strict")
    return response


@router.get("/me")
def me(current: Current):
    return own_user(current[0])


@router.patch("/me")
def update_me(body: ProfilePatch, request: Request, current: Current):
    user = current[0]
    changes = body.model_dump(exclude_unset=True)
    changes["updated_at"] = request.app.state.clock()
    try:
        request.app.state.db.users.update_one({"_id": user["_id"]}, {"$set": changes})
    except DuplicateKeyError as error:
        duplicate_error(error)
    return own_user({**user, **changes})


@router.patch("/me/email")
def change_email(body: EmailChange, request: Request, current: Current):
    user = current[0]
    check_current_password(request, user, body.current_password)
    changes = {"email": body.email, "updated_at": request.app.state.clock()}
    try:
        request.app.state.db.users.update_one({"_id": user["_id"]}, {"$set": changes})
    except DuplicateKeyError as error:
        duplicate_error(error)
    return own_user({**user, **changes})


@router.patch("/me/password", status_code=204)
def change_password(body: PasswordChange, request: Request, current: Current):
    user, session = current
    check_current_password(request, user, body.current_password)
    encoded = password_hasher.hash(body.new_password)
    # Erato rejects a session without its row, so the other devices stop here.
    request.app.state.db.sessions.delete_many({"user_id": user["_id"],
                                               "_id": {"$ne": session["_id"]}})
    request.app.state.db.users.update_one({"_id": user["_id"]}, {"$set": {
        "password_hash": encoded, "updated_at": request.app.state.clock(),
    }})
    return Response(status_code=204)


@router.get("/me/sessions")
def list_sessions(request: Request, current: Current):
    user, session = current
    return [{"id": str(item["_id"]), "device": item["device"],
             "last_access_at": item["last_access_at"], "created_at": item["created_at"],
             "current": item["sid"] == session["sid"]}
            for item in request.app.state.db.sessions.find({"user_id": user["_id"],
                "expires_at": {"$gt": request.app.state.clock()}}).sort("last_access_at", -1)]


@router.delete("/me/sessions/{session_id}", status_code=204)
def close_session(session_id: str, request: Request, current: Current):
    if not ObjectId.is_valid(session_id):
        raise APIError("not_found")
    session = request.app.state.db.sessions.find_one({"_id": ObjectId(session_id),
                                                      "user_id": current[0]["_id"]})
    if session is None:
        raise APIError("not_found")
    if session["_id"] == current[1]["_id"]:
        revoke_current_session(request, session)
    else:
        # Erato rejects a session without its row, so the other device stops here.
        request.app.state.db.sessions.delete_one({"_id": session["_id"]})
    return Response(status_code=204)
