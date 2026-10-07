"""Restore an AD14 backup: python -m scripts.restore_bands_migration --backup FILE --confirm-db NAME."""
import argparse
import asyncio
import sys
from pathlib import Path

from bson import json_util
from pymongo.errors import DuplicateKeyError

from app.db import client as db_client
from scripts.migrate_bands import close_client, confirmed_database


async def run(backup: Path, confirm_db: str | None = None) -> int:
    """Restore original members and invitation ids; repeated restores ignore duplicate keys."""
    try:
        if not confirmed_database(confirm_db):
            return 1
        data = json_util.loads(Path(backup).read_text(encoding="utf-8"))
        db = db_client.get_db()
        for document in data["compositions"]:
            await db.compositions.update_one(
                {"_id": document["_id"]}, {"$set": {"members": document["members"]}},
            )
        for document in data["invitations"]:
            try:
                await db.invitations.insert_one(document)
            except DuplicateKeyError:
                pass
        await db.invitations.create_index("composition_id", name="idx_invitations_composition_id")
        print(f"Restauración completada: {len(data['compositions'])} composiciones, {len(data['invitations'])} invitaciones")
        return 0
    except Exception as exc:
        print(f"Error de restauración: {type(exc).__name__}")
        return 1
    finally:
        await close_client()


def main() -> None:
    parser = argparse.ArgumentParser(description="Restaura un respaldo de la migración de bandas")
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--confirm-db", required=True)
    args = parser.parse_args()
    sys.exit(asyncio.run(run(backup=args.backup, confirm_db=args.confirm_db)))


if __name__ == "__main__":
    main()
