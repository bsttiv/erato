"""Only approved indexes; no database validators or additional fields."""
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import OperationFailure

INDEX_NOT_FOUND = 27


def drop_jti_index(db):
    """Rows have no jti any more, so the old unique index would reject the second one."""
    try:
        db.sessions.drop_index("jti_1")
    except OperationFailure as error:
        # Another instance may have dropped it first.
        if error.code != INDEX_NOT_FOUND:
            raise


def create_indexes(db):
    db.users.create_index("email", unique=True)
    db.users.create_index("username", unique=True)
    db.sessions.create_index("user_id")
    drop_jti_index(db)
    # Rows from before sid cannot reach a Maestro session, and would collide on the new index.
    db.sessions.delete_many({"sid": {"$exists": False}})
    db.sessions.create_index("sid", unique=True)
    db.sessions.create_index("expires_at", expireAfterSeconds=0)
    db.login_attempts.create_index([
        ("email_hash", ASCENDING), ("ip", ASCENDING), ("created_at", ASCENDING),
    ])
    db.login_attempts.create_index("created_at", expireAfterSeconds=900)
    db.songs.create_index([("owner_type", ASCENDING), ("owner_id", ASCENDING),
                           ("updated_at", DESCENDING)])
    db.songs.create_index("share_slug", unique=True,
                          partialFilterExpression={"share_slug": {"$type": "string"}})
    db.revisions.create_index([("song_id", ASCENDING), ("section", ASCENDING),
                               ("version", DESCENDING)], unique=True)
    db.bands.create_index("owner_id")
    db.invitations.create_index("token_hash", unique=True)
    db.invitations.create_index([("target_type", ASCENDING), ("target_id", ASCENDING)])
    db.invitations.create_index("expires_at", expireAfterSeconds=0)
    db.memberships.create_index([("target_type", ASCENDING), ("target_id", ASCENDING),
                                 ("user_id", ASCENDING)], unique=True)
    db.memberships.create_index([("user_id", ASCENDING), ("target_type", ASCENDING)])
    db.demo_comments.create_index([("song_id", ASCENDING), ("demo_id", ASCENDING),
                                   ("timestamp_s", ASCENDING)])
