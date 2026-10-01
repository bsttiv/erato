"""Vercel Python serverless entrypoint for Erato.

Re-exports the FastAPI application instance. No business logic belongs here.
"""

from app.main import app

__all__ = ["app"]
