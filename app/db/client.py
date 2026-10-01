import asyncio
import logging
from typing import Optional
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.settings import get_settings

logger = logging.getLogger("erato.db")

_client: Optional[AsyncMongoClient] = None
_client_loop: Optional[asyncio.AbstractEventLoop] = None


def get_client() -> AsyncMongoClient:
    """Get or create the module-level lazy AsyncMongoClient singleton.

    Guarded by checking that the current event loop matches the loop on which the client
    was initialized. If the loop changed or was closed, the stale client is closed and
    recreated with the pool parameters defined in design.md.
    """
    global _client, _client_loop

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    is_stale = (
        _client is None
        or _client_loop is None
        or _client_loop is not current_loop
        or (_client_loop is not None and _client_loop.is_closed())
    )

    if is_stale:
        if _client is not None:
            try:
                if _client_loop is current_loop and current_loop is not None and not current_loop.is_closed():
                    if current_loop.is_running():
                        current_loop.create_task(_client.close())
                    else:
                        asyncio.run(_client.close())
            except Exception as e:
                logger.warning("Error closing stale Mongo client: %s", e)


        settings = get_settings()
        _client = AsyncMongoClient(
            settings.mongodb_uri,
            maxPoolSize=5,
            minPoolSize=0,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000,
            retryWrites=True,
        )
        _client_loop = current_loop

    return _client


def get_db() -> AsyncDatabase:
    """Return the application database handle from the warm client singleton."""
    client = get_client()
    settings = get_settings()
    return client[settings.mongodb_db]
