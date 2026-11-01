"""Demos and timestamp comments (approved decisions 05, 06 and 10).

The audio never passes through the backend: it is uploaded directly to Cloudinary
with a signed request and played back with an expiring URL. Compression is paused
(decisions 03 and 10) and is not implemented here.
"""
import re
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from pydantic import AfterValidator, BaseModel, StrictFloat, StrictInt, StrictStr, field_validator

from app.accounts import Current, new_id, public_user
from app.errors import APIError
from app.permissions import object_id, require_song, resolve
from app.sections import Input
from app.songs import demo_response, transact
from app.storage import destroy_asset, playback_link, read_asset, upload_target

router = APIRouter()
MAX_BYTES = 100 * 1024 ** 2
MAX_SECONDS = 20 * 60
UUID_PATTERN = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
QUOTA_BYTES = 2 * 1024 ** 3
# Cloudinary format -> mime type. Compression is paused, so the real format is kept.
FORMATS = {'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg', 'opus': 'audio/ogg', 'flac': 'audio/flac',
           'aac': 'audio/aac', 'm4a': 'audio/mp4', 'mp4': 'audio/mp4', 'webm': 'audio/webm'}


def find_demo(song, demo_id):
    demo_id = object_id(demo_id)
    for demo in song['demos']:
        if demo['id'] == demo_id:
            return demo
    raise APIError('not_found')


def public_song(db, slug):
    song = db.songs.find_one({'share_slug': slug, 'visibility': 'public'})
    if song is None:
        raise APIError('not_found')
    return song


def trimmed_text(value):
    value = value.strip()
    if not 1 <= len(value) <= 2000:
        raise ValueError('Text must have 1 to 2000 characters')
    return value


Text = Annotated[StrictStr, AfterValidator(trimmed_text)]


class Rename(Input):
    title: StrictStr

    @field_validator('title')
    @classmethod
    def title_valid(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Title is required')
        return value


class Confirm(BaseModel):  # extra fields, such as a client duration_s, are ignored
    public_id: StrictStr
    title: StrictStr | None = None

    @field_validator('title')
    @classmethod
    def title_valid(cls, value):
        return None if value is None else Rename.title_valid(value)


class CommentBody(BaseModel):
    # Unknown fields, such as a client-sent author_id, are ignored (file 10).
    timestamp_s: StrictInt | StrictFloat
    text: Text


class CommentUpdate(BaseModel):
    timestamp_s: StrictInt | StrictFloat | None = None
    text: Text | None = None


def comment_response(db, comment):
    user = db.users.find_one({'_id': comment['author_id']})
    return {'id': str(comment['_id']), 'demo_id': str(comment['demo_id']),
            'timestamp_s': comment['timestamp_s'], 'text': comment['text'],
            'created_at': comment['created_at'], 'updated_at': comment['updated_at'],
            'author': public_user(user) if user else None}


def list_comments(db, song, demo):
    rows = db.demo_comments.find({'song_id': song['_id'], 'demo_id': demo['id']}).sort('timestamp_s', 1)
    return [comment_response(db, row) for row in rows]


@router.post('/songs/{song_id}/demos/upload-url')
def upload_url(song_id: str, request: Request, current: Current):
    user_id = current[0]['_id']
    song = require_song(request.app.state.db, song_id, user_id, 'edit')
    public_id = f'erato/songs/{song["_id"]}/{user_id}/{uuid4()}'
    return upload_target(request.app.state.config, public_id)


def valid_audio(asset):
    return (asset.get('format') in FORMATS and asset.get('has_audio') is True and asset.get('duration') is not None
            and asset['bytes'] <= MAX_BYTES and asset['duration'] <= MAX_SECONDS)


def owner_usage(db, song, session):
    return sum(demo['size_bytes'] for row in db.songs.find({
        'owner_type': song['owner_type'], 'owner_id': song['owner_id'],
    }, session=session) for demo in row['demos'])


@router.post('/songs/{song_id}/demos', status_code=201)
def confirm_upload(song_id: str, body: Confirm, request: Request, current: Current):
    db, uid, config = request.app.state.db, current[0]['_id'], request.app.state.config
    song = require_song(db, song_id, uid, 'edit')
    public_id = body.public_id

    def in_use(target):
        return any(demo['cloudinary_public_id'] == public_id for demo in target['demos'])

    if not re.fullmatch(rf'erato/songs/{song["_id"]}/{uid}/{UUID_PATTERN}', public_id) or in_use(song):
        raise APIError('not_found')
    asset = read_asset(config, public_id)
    if asset is None:
        raise APIError('not_found')
    try:
        if not valid_audio(asset):
            raise APIError('validation_error')
        size, demo_id = asset['bytes'], new_id()

        def add(session):
            current_song = require_song(db, song_id, uid, 'edit', session=session)
            if in_use(current_song):
                return None  # a concurrent confirmation won; its asset must survive
            if owner_usage(db, current_song, session) + size > QUOTA_BYTES:
                raise APIError('quota_exceeded')
            demo = {'id': demo_id, 'title': body.title or f'Demo {len(current_song["demos"]) + 1}',
                    'duration_s': round(asset['duration'], 3), 'cloudinary_public_id': public_id,
                    'format': asset['format'], 'mime_type': FORMATS[asset['format']], 'size_bytes': size,
                    'uploaded_by': uid, 'uploaded_at': request.app.state.clock()}
            db.songs.update_one({'_id': current_song['_id']}, {'$push': {'demos': demo}}, session=session)
            return demo

        demo = transact(db, add)
    except BaseException:
        destroy_asset(config, public_id)  # no orphans in Cloudinary
        raise
    if demo is None:
        raise APIError('not_found')
    return demo_response(demo)


@router.patch('/songs/{song_id}/demos/{demo_id}')
def rename_demo(song_id: str, demo_id: str, body: Rename, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    song = require_song(db, song_id, uid, 'edit')
    demo = find_demo(song, demo_id)
    db.songs.update_one({'_id': song['_id'], 'demos.id': demo['id']}, {'$set': {'demos.$.title': body.title}})
    return demo_response({**demo, 'title': body.title})


@router.delete('/songs/{song_id}/demos/{demo_id}', status_code=204)
def delete_demo(song_id: str, demo_id: str, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    demo = find_demo(require_song(db, song_id, uid, 'edit'), demo_id)
    # Remote deletion precedes DB deletion: a Cloudinary error never drops metadata.
    destroy_asset(request.app.state.config, demo['cloudinary_public_id'])

    def delete(session):
        song = require_song(db, song_id, uid, 'edit', session=session)
        find_demo(song, demo_id)
        db.songs.update_one({'_id': song['_id']}, {'$pull': {'demos': {'id': demo['id']}}}, session=session)
        db.demo_comments.delete_many({'song_id': song['_id'], 'demo_id': demo['id']}, session=session)

    transact(db, delete)
    return Response(status_code=204)


@router.get('/songs/{song_id}/demos/{demo_id}/url')
def playback_url(song_id: str, demo_id: str, request: Request, current: Current):
    song = require_song(request.app.state.db, song_id, current[0]['_id'])
    demo = find_demo(song, demo_id)
    return playback_link(request.app.state.config, demo)


@router.get('/c/{slug}/demos/{demo_id}/url')
def public_playback_url(slug: str, demo_id: str, request: Request):
    demo = find_demo(public_song(request.app.state.db, slug), demo_id)
    return playback_link(request.app.state.config, demo)


@router.get('/songs/{song_id}/demos/{demo_id}/comments')
def read_comments(song_id: str, demo_id: str, request: Request, current: Current):
    db = request.app.state.db
    song = require_song(db, song_id, current[0]['_id'])
    return list_comments(db, song, find_demo(song, demo_id))


@router.get('/c/{slug}/demos/{demo_id}/comments')
def read_public_comments(slug: str, demo_id: str, request: Request):
    db = request.app.state.db
    song = public_song(db, slug)
    return list_comments(db, song, find_demo(song, demo_id))


def check_timestamp(demo, value):
    if not 0 <= value <= demo['duration_s']:
        raise APIError('validation_error')


@router.post('/songs/{song_id}/demos/{demo_id}/comments', status_code=201)
def create_comment(song_id: str, demo_id: str, body: CommentBody, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    song = require_song(db, song_id, uid, 'edit')
    demo = find_demo(song, demo_id)
    check_timestamp(demo, body.timestamp_s)
    now = request.app.state.clock()
    comment = {'_id': new_id(), 'song_id': song['_id'], 'demo_id': demo['id'], 'author_id': uid,
               'timestamp_s': float(body.timestamp_s), 'text': body.text, 'created_at': now, 'updated_at': now}
    db.demo_comments.insert_one(comment)
    return comment_response(db, comment)


def find_comment(db, song, demo, comment_id):
    comment = db.demo_comments.find_one({'_id': object_id(comment_id), 'song_id': song['_id'],
                                         'demo_id': demo['id']})
    if comment is None:
        raise APIError('not_found')
    return comment


@router.patch('/songs/{song_id}/demos/{demo_id}/comments/{comment_id}')
def update_comment(song_id: str, demo_id: str, comment_id: str, body: CommentUpdate,
                   request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    song = require_song(db, song_id, uid)
    demo = find_demo(song, demo_id)
    comment = find_comment(db, song, demo, comment_id)
    if comment['author_id'] != uid:
        raise APIError('forbidden')
    changes = body.model_dump(exclude_none=True)
    if not changes:
        raise APIError('validation_error')
    if 'timestamp_s' in changes:
        check_timestamp(demo, changes['timestamp_s'])
        changes['timestamp_s'] = float(changes['timestamp_s'])
    changes['updated_at'] = request.app.state.clock()
    db.demo_comments.update_one({'_id': comment['_id']}, {'$set': changes})
    return comment_response(db, {**comment, **changes})


@router.delete('/songs/{song_id}/demos/{demo_id}/comments/{comment_id}', status_code=204)
def delete_comment(song_id: str, demo_id: str, comment_id: str, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    song = require_song(db, song_id, uid)
    comment = find_comment(db, song, find_demo(song, demo_id), comment_id)
    # The author or the owner (the band owner in a band song) may delete.
    if comment['author_id'] != uid and not resolve(db, song, uid).manage:
        raise APIError('forbidden')
    db.demo_comments.delete_one({'_id': comment['_id']})
    return Response(status_code=204)
