"""One-shot, idempotent creation of the MongoDB indexes.

Usage: python -m scripts.ensure_indexes (reads MONGODB_URI / MONGODB_DB).
Not run at app startup on purpose: Vercel serverless cold starts would repeat it.
"""
import asyncio
import sys

from app.db import client as db_client
from app.db.repositories.comments import CommentsRepository
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.invitations import InvitationsRepository
from app.db.repositories.refresh_tokens import RefreshTokensRepository
from app.db.repositories.section_revisions import SectionRevisionsRepository
from app.db.repositories.users import UsersRepository
from app.settings import get_settings

REPOSITORIES = (
    ("users", UsersRepository),
    ("compositions", CompositionsRepository),
    ("refresh_tokens", RefreshTokensRepository),
    ("invitations", InvitationsRepository),
    ("comments", CommentsRepository),
    ("section_revisions", SectionRevisionsRepository),
)

ROLLBACK_INDEXES = (
    ("section_revisions", "uq_section_revisions_comp_section_rev"),
)


async def run(rollback: bool = False) -> int:
    """Ensure indexes or drop rollback indexes; return 0 if all ok, 1 otherwise."""
    get_settings()
    failures = 0
    try:
        if rollback:
            db = db_client.get_db()
            for coll_name, index_name in ROLLBACK_INDEXES:
                try:
                    await db[coll_name].drop_index(index_name)
                    print(f"{coll_name} index {index_name} dropped: ok")
                except Exception as exc:
                    # Ignore if index does not exist during rollback
                    print(f"{coll_name} index {index_name} drop: {exc}")
        else:
            for name, repository_cls in REPOSITORIES:
                try:
                    await repository_cls().ensure_indexes()
                    print(f"{name}: ok")
                except Exception as exc:
                    failures += 1
                    print(f"{name}: error - {exc}")
    finally:
        await db_client.get_client().close()
        db_client._client = None
    return 1 if failures else 0


def main() -> None:
    rollback = "--rollback" in sys.argv
    sys.exit(asyncio.run(run(rollback=rollback)))


if __name__ == "__main__":
    main()

