"""In-memory Maestro contract simulator; never use for production sessions."""
import asyncio
import hashlib
import os
import secrets
import time
from typing import Any, Literal
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, ConfigDict, StrictStr


PREFIX = "/api/v1/maestro"


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Mint(Body):
    userId: StrictStr
    context: StrictStr


class Validate(Body):
    token: StrictStr
    fingerprint: StrictStr


class Revoke(Body):
    token: StrictStr


class Refresh(Body):
    refresh: StrictStr
    fingerprint: StrictStr


class Expire(Body):
    token: StrictStr


class Fault(Body):
    endpoint: Literal["/mint", "/validate", "/revoke", "/refresh"]
    mode: Literal["error_429", "error_503", "no_response", "body"]
    body: Any = None


class ForcedBody(Exception):
    def __init__(self, body):
        self.body = body


def create_app(control=None):
    app = FastAPI(title="Maestro mock")
    enabled = os.environ.get("MAESTRO_MOCK_CONTROL") == "1" if control is None else control
    api_key = os.environ["MAESTRO_API_KEY"]
    key = secrets.token_bytes(32)
    sessions, expired, faults, calls = {}, set(), {}, []

    def authorize(request: Request):
        keys = request.headers.getlist("x-api-key")
        if not keys:
            raise HTTPException(401, "Missing API Key")
        if keys != [api_key]:
            raise HTTPException(401, "Invalid API Key")

    router = APIRouter(prefix=PREFIX)
    secured = APIRouter(dependencies=[Depends(authorize)])

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return PlainTextResponse("Invalid request", status_code=400)

    @app.exception_handler(HTTPException)
    async def failure(request, exc):
        return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

    @app.exception_handler(ForcedBody)
    async def forced(request, exc):
        return JSONResponse(exc.body)

    async def record(path, body):
        if enabled:
            calls.append({"path": path, "body": body.model_dump()})
        mode, forced_body = faults.get(path, (None, None))
        if mode in ("error_429", "error_503"):
            raise HTTPException(int(mode[-3:]), "Forced error")
        if mode == "no_response":
            await asyncio.sleep(30)
        if mode == "body":
            raise ForcedBody(forced_body)

    def hashed(fingerprint):
        return hashlib.sha256(fingerprint.encode()).hexdigest()

    def issue(user_id, sid, context, session_exp, jti):
        now = int(time.time())
        common = {"iss": "maestro", "sub": f"sub_{user_id}", "sid": sid, "ctx": context, "iat": now}
        access = {**common, "typ": "access", "exp": min(now + 900, session_exp)}
        refresh = {**common, "typ": "refresh", "exp": session_exp, "jti": jti}
        return {"accessToken": jwt.encode(access, key, algorithm="HS256"),
                "refreshToken": jwt.encode(refresh, key, algorithm="HS256")}

    def decode(token):
        try:
            return jwt.decode(token, key, algorithms=["HS256"], options={
                "verify_exp": False, "require": ["sub", "sid", "typ", "ctx", "iat", "exp"]})
        except jwt.PyJWTError:
            raise HTTPException(401, "Token signature does not match any used keys") from None

    def admitted(claims, token, typ):
        if claims["typ"] != typ or token in expired or claims["exp"] <= time.time():
            raise HTTPException(401, "Token has expired")
        if claims["sid"] not in sessions:
            raise HTTPException(401, "Token not found")

    @secured.post("/mint")
    async def mint(body: Mint):
        await record("/mint", body)
        sid, jti = str(uuid4()), str(uuid4())
        sessions[sid] = jti
        return issue(body.userId, sid, hashed(body.context), int(time.time()) + 604800, jti)

    @secured.post("/validate")
    async def validate(body: Validate):
        await record("/validate", body)
        claims = decode(body.token)
        admitted(claims, body.token, "access")
        if claims["ctx"] != hashed(body.fingerprint):
            raise HTTPException(401, "Token does not match the current fingerprint")
        return {"userId": claims["sub"].removeprefix("sub_"), "sessionId": claims["sid"]}

    @secured.post("/revoke", status_code=204)
    async def revoke(body: Revoke):
        await record("/revoke", body)
        sessions.pop(decode(body.token)["sid"], None)
        return Response(status_code=204)

    @secured.post("/refresh")
    async def refresh(body: Refresh):
        await record("/refresh", body)
        claims = decode(body.refresh)
        admitted(claims, body.refresh, "refresh")
        sid, context = claims["sid"], hashed(body.fingerprint)
        if claims.get("jti") != sessions[sid] or claims["ctx"] != context:
            del sessions[sid]
            raise HTTPException(401, "Token was not valid")
        sessions[sid] = str(uuid4())
        return issue(claims["sub"].removeprefix("sub_"), sid, context, claims["exp"], sessions[sid])

    if enabled:
        @router.post("/__control/expire", status_code=204)
        def expire(body: Expire):
            expired.add(body.token)
            return Response(status_code=204)

        @router.post("/__control/fault", status_code=204)
        def fault(body: Fault):
            faults[body.endpoint] = (body.mode, body.body)
            return Response(status_code=204)

        @router.post("/__control/reset", status_code=204)
        def reset():
            sessions.clear()
            expired.clear()
            faults.clear()
            calls.clear()
            return Response(status_code=204)

        @router.get("/__control/calls")
        def list_calls():
            return calls

    router.include_router(secured)
    app.include_router(router)
    return app
