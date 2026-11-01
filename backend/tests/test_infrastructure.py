"""Approved INFRA rules implementable in the runnable scaffold."""
import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import time
import wave
from uuid import uuid4

from fastapi.testclient import TestClient
import httpx
import pytest
from pymongo import MongoClient

from app.config import OPTIONAL, REQUIRED
from app.main import create_app

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def maestro():
    with httpx.Client(base_url=os.environ["MAESTRO_URL"], timeout=2,
                      headers={"X-Api-Key": os.environ["MAESTRO_API_KEY"]}) as client:
        for _ in range(50):
            try:
                if client.post("/__control/reset").status_code == 204:
                    break
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        else:
            pytest.fail("Control mock did not become ready")
        yield client
        client.post("/__control/reset")


def pair(client):
    response = client.post("/mint", json={"userId": "alice", "context": "device"})
    assert response.status_code == 200
    return response.json()


def validate(client, token, fingerprint="device"):
    return client.post("/validate", json={"token": token, "fingerprint": fingerprint})


def test_infra_010_mongo_primary():
    with MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=5000) as client:
        hello = client.admin.command("hello")
        assert hello["isWritablePrimary"] and hello["setName"] == "rs0"


def test_infra_030_health():
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200


@pytest.mark.parametrize("name", REQUIRED)
def test_infra_031_missing_required_variable(monkeypatch, name):
    monkeypatch.delenv(name)
    with pytest.raises(ValueError, match=name):
        create_app()


def test_infra_032_env_parity():
    expected = {line.split("=", 1)[0] for line in (ROOT / ".env.example").read_text().splitlines() if line and not line.startswith("#")}
    assert expected == set(REQUIRED + OPTIONAL)
    source = ast.parse((Path(__file__).resolve().parents[1] / "app/config.py").read_text())
    literal_reads = {node.args[0].value for node in ast.walk(source)
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                     and isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "environ"
                     and node.args and isinstance(node.args[0], ast.Constant)}
    assert literal_reads <= expected


def test_infra_033_ffmpeg_libopus():
    output = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, check=True)
    assert "libopus" in output.stdout


def test_infra_034_opus_encoding(tmp_path):
    source, target = tmp_path / "input.wav", tmp_path / "output.ogg"
    with wave.open(str(source), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        wav.writeframes(b"\0\0" * 48000)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(source), "-c:a", "libopus", "-b:a", "96k", str(target)], check=True)
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(target)], capture_output=True, text=True, check=True)
    assert float(result.stdout) == pytest.approx(1, abs=0.1)


def test_infra_048_fault_controls(maestro):
    assert maestro.post("/__control/fault", json={"endpoint": "/mint", "mode": "error_503"}).status_code == 204
    assert maestro.post("/mint", json={"userId": "alice", "context": "device"}).status_code == 503
    assert maestro.post("/__control/fault", json={"endpoint": "/mint", "mode": "no_response"}).status_code == 204
    with pytest.raises(httpx.TimeoutException):
        maestro.post("/mint", json={"userId": "alice", "context": "device"})


def test_infra_049_controls_disabled():
    url = os.environ["TEST_MAESTRO_PLAIN_URL"]
    for method, path in [("POST", "/__control/reset"), ("POST", "/__control/expire"), ("POST", "/__control/fault"), ("GET", "/__control/calls")]:
        assert httpx.request(method, url + path).status_code == 404


def test_infra_060_invalid_bodies(maestro):
    for endpoint in ("/mint", "/validate", "/revoke", "/refresh"):
        for body in ("{", "{}", '{"token":42}'):
            response = maestro.post(endpoint, content=body, headers={"Content-Type": "application/json"})
            assert response.status_code == 400 and response.headers["content-type"].startswith("text/plain")


def test_infra_061_call_registry(maestro):
    tokens = pair(maestro)
    validate(maestro, tokens["accessToken"])
    calls = maestro.get("/__control/calls").json()
    assert calls == [{"path": "/mint", "body": {"userId": "alice", "context": "device"}},
                     {"path": "/validate", "body": {"token": tokens["accessToken"], "fingerprint": "device"}}]


def test_infra_062_reset_registry(maestro):
    pair(maestro)
    assert maestro.post("/__control/reset").status_code == 204
    assert maestro.get("/__control/calls").json() == []
