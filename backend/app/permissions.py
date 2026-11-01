"""Per-request access resolution against the approved membership collections."""
from dataclasses import dataclass

from bson import ObjectId

from app.errors import APIError


def object_id(value):
    if not isinstance(value, (str, ObjectId)) or not ObjectId.is_valid(value):
        raise APIError('not_found')
    return ObjectId(value)


def band_access(db, band_id, user_id, *, session=None):
    band = db.bands.find_one({'_id': band_id}, session=session)
    if band is None:
        return False, False
    owner = band['owner_id'] == user_id
    member = owner or db.memberships.find_one({
        'target_type': 'band', 'target_id': band_id, 'user_id': user_id,
    }, session=session) is not None
    return member, owner


@dataclass(frozen=True)
class Permissions:
    view: bool
    edit: bool
    manage: bool

    def require(self, action):
        if not self.view:
            raise APIError('not_found')
        if not getattr(self, action):
            raise APIError('forbidden')


def resolve(db, song, user_id, *, session=None):
    """Public visibility deliberately does not grant access through internal IDs."""
    if song['owner_type'] == 'user':
        owner = song['owner_id'] == user_id
        band_member = False
    else:
        band_member, owner = band_access(db, song['owner_id'], user_id, session=session)
    membership = db.memberships.find_one({
        'target_type': 'song', 'target_id': song['_id'], 'user_id': user_id,
    }, session=session)
    editor = membership is not None and membership['role'] == 'editor'
    return Permissions(owner or band_member or membership is not None,
                       owner or band_member or editor, owner)


def require_song(db, song_id, user_id, action='view', *, session=None):
    song = db.songs.find_one({'_id': object_id(song_id)}, session=session)
    if song is None:
        raise APIError('not_found')
    resolve(db, song, user_id, session=session).require(action)
    return song
