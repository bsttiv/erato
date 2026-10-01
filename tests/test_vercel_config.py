import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
SUPPORTED_PYTHON = {"3.12", "3.13", "3.14"}


def test_frontend_is_built_from_its_subfolder_into_the_published_directory():
    assert "frontend" in CONFIG["buildCommand"]
    assert "npm ci" in CONFIG["buildCommand"]
    assert "npm run build" in CONFIG["buildCommand"]
    assert CONFIG["outputDirectory"] == "frontend/dist"


def test_api_requests_rewrite_to_the_function_route_and_spa_is_the_fallback():
    rewrites = CONFIG["rewrites"]
    assert rewrites[0] == {"source": "/api/(.*)", "destination": "/api/index"}
    assert rewrites[-1] == {"source": "/(.*)", "destination": "/index.html"}
    assert (ROOT / "api" / "index.py").is_file()


def test_function_has_a_duration_and_keeps_the_frontend_out_of_the_bundle():
    function = CONFIG["functions"]["api/index.py"]
    assert isinstance(function["maxDuration"], int) and function["maxDuration"] >= 10
    for ignored in ("frontend/**", "tests/**", "openspec/**"):
        assert ignored in function["excludeFiles"]


def test_every_cron_points_to_an_existing_backend_route():
    from app.main import app

    # Included routers are not listed in app.routes, but the OpenAPI schema lists every path.
    paths = set(app.openapi()["paths"])
    for cron in CONFIG["crons"]:
        assert cron["path"] in paths


def test_python_version_is_pinned_to_a_version_supported_by_vercel():
    version = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    assert version in SUPPORTED_PYTHON


def test_dependencies_are_installed_from_requirements_txt_without_a_projectless_pyproject():
    # With a pyproject.toml present, Vercel runs `uv lock`, which fails when it has no [project] table.
    assert (ROOT / "requirements.txt").is_file()
    pyproject = ROOT / "pyproject.toml"
    if pyproject.exists():
        assert "project" in tomllib.loads(pyproject.read_text(encoding="utf-8"))
