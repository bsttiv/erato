"""AD14 legacy migration. Usage: python -m scripts.migrate_bands [--apply --confirm-db NAME]."""
import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util

from app.db import client as db_client
from app.settings import get_settings


async def close_client() -> None:
    """Release the script's application client, matching ensure_indexes."""
    if db_client._client is not None:
        await db_client._client.close()
        db_client._client = None


def confirmed_database(confirm_db: str | None) -> bool:
    if confirm_db != get_settings().mongodb_db:
        print("Operación rechazada: --confirm-db debe coincidir con MONGODB_DB")
        return False
    return True


async def run(apply: bool = False, confirm_db: str | None = None) -> int:
    """Report legacy ids by default; require confirmation and a durable backup to apply."""
    try:
        get_settings()
        if apply and not confirmed_database(confirm_db):
            return 1
        db = db_client.get_db()
        compositions = await db.compositions.find(
            {"band_id": None, "members.0": {"$exists": True}},
            {"members": 1},
        ).sort("_id", 1).to_list(None)
        invitations = await db.invitations.find(
            {"composition_id": {"$exists": True}, "target": {"$exists": False}},
        ).sort("_id", 1).to_list(None)
        if not compositions and not invitations:
            print("nada que migrar")
            return 0
        print("APLICAR" if apply else "DRY RUN")
        for name, documents in (("compositions", compositions), ("invitations", invitations)):
            for document in documents:
                print(f"{name}: {document['_id']}")
        if not apply:
            return 0

        directory = Path("backups")
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup = directory / f"migrate_bands-{timestamp}.json"
        # Exclusive creation prevents overwriting a previous backup.
        with backup.open("x", encoding="utf-8") as stream:
            stream.write(json_util.dumps(
                {"compositions": compositions, "invitations": invitations},
                json_options=json_util.CANONICAL_JSON_OPTIONS,
            ))
            stream.flush()
            os.fsync(stream.fileno())
        print(f"Respaldo: {backup}")
        for document in compositions:
            await db.compositions.update_one({"_id": document["_id"]}, {"$set": {"members": []}})
        await db.invitations.delete_many({"_id": {"$in": [d["_id"] for d in invitations]}})
        if "idx_invitations_composition_id" in await db.invitations.index_information():
            await db.invitations.drop_index("idx_invitations_composition_id")
        await db.invitations.create_index(
            [("target.type", 1), ("target.id", 1)], name="idx_invitations_target",
        )
        print(f"Migración completada: {len(compositions)} composiciones, {len(invitations)} invitaciones")
        return 0
    except Exception as exc:
        print(f"Error de migración: {type(exc).__name__}")
        return 1
    finally:
        await close_client()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migra permisos heredados con respaldo previo")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-db")
    args = parser.parse_args()
    sys.exit(asyncio.run(run(apply=args.apply, confirm_db=args.confirm_db)))


if __name__ == "__main__":
    main()
