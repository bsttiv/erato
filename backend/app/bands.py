"""Bands, multi-use invitations and memberships (approved decisions 05/06/11)."""
from datetime import timedelta
import secrets
from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import StrictStr, field_validator, model_validator
from pymongo.errors import DuplicateKeyError

from app.accounts import Current, new_id, public_user, sha256
from app.errors import APIError
from app.permissions import Permissions, band_access, object_id, require_song, resolve
from app.sections import Input
from app.songs import json_document, song_response, transact

router = APIRouter()
TargetType = Literal['song', 'band']
Role = Literal['editor', 'viewer']


class BandCreate(Input):
    name: StrictStr

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Name must not be empty')
        return value


class InvitationCreate(Input):
    target_type: TargetType
    target_id: StrictStr
    role: Role | None = None

    @model_validator(mode='after')
    def target_role(self):
        if (self.target_type == 'song') != (self.role is not None):
            raise ValueError('Songs require a role; bands have no role')
        return self


class MemberRole(Input):
    role: Role


class Transfer(Input):
    username: StrictStr


class Move(Input):
    band_id: StrictStr


def target_access(db, kind, target_id, uid, action='view', *, session=None):
    if kind == 'song':
        return require_song(db, target_id, uid, action, session=session)
    target_id = object_id(target_id)
    view, owner = band_access(db, target_id, uid, session=session)
    Permissions(view, view, owner).require(action)
    return db.bands.find_one({'_id': target_id}, session=session)


def touch(db, kind, target, now, session):
    """Serialize editor changes/link creation on the existing target document.

    A strictly increasing millisecond timestamp makes this a real write even with
    a fixed clock. A concurrent access change forces the transaction to retry its
    permission reads instead of committing a link from an obsolete snapshot.
    """
    stamp = max(now, target['updated_at'] + timedelta(milliseconds=1))
    collection = db.songs if kind == 'song' else db.bands
    collection.update_one({'_id': target['_id']}, {'$set': {'updated_at': stamp}}, session=session)


def invitation_response(invitation):
    return json_document({k: v for k, v in invitation.items() if k != 'token_hash'})


def membership(db, kind, target_id, uid, role, invitation_id, now, session):
    row = {'_id': new_id(), 'target_type': kind, 'target_id': target_id,
           'user_id': uid, 'role': role, 'invitation_id': invitation_id, 'joined_at': now}
    db.memberships.insert_one(row, session=session)
    return row


@router.post('/bands', status_code=201)
def create_band(body: BandCreate, request: Request, current: Current):
    now = request.app.state.clock()
    band = {'_id': new_id(), 'name': body.name, 'owner_id': current[0]['_id'],
            'created_at': now, 'updated_at': now}
    request.app.state.db.bands.insert_one(band)
    return json_document(band)


@router.get('/bands')
def list_bands(request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    ids = [m['target_id'] for m in db.memberships.find({'target_type': 'band', 'user_id': uid})]
    return [json_document(b) for b in db.bands.find({'$or': [
        {'owner_id': uid}, {'_id': {'$in': ids}},
    ]}).sort([('updated_at', -1), ('_id', 1)])]


@router.get('/bands/{band_id}')
def read_band(band_id: str, request: Request, current: Current):
    return json_document(target_access(request.app.state.db, 'band', band_id, current[0]['_id']))


@router.post('/invitations', status_code=201)
def create_invitation(body: InvitationCreate, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    token = secrets.token_urlsafe(32)

    def create(session):
        target = target_access(db, body.target_type, body.target_id, uid, 'edit', session=session)
        now = request.app.state.clock()
        touch(db, body.target_type, target, now, session)
        invitation = {'_id': new_id(), 'target_type': body.target_type, 'target_id': target['_id'],
                      'role': body.role, 'token_hash': sha256(token), 'created_by': uid,
                      'created_at': now, 'expires_at': now + timedelta(seconds=request.app.state.config['INVITATION_TTL'])}
        db.invitations.insert_one(invitation, session=session)
        return invitation

    return {**invitation_response(transact(db, create)), 'token': token, 'url': '/i/' + token}


@router.get('/invitations')
def list_invitations(request: Request, current: Current, target_type: TargetType, target_id: str):
    db, uid = request.app.state.db, current[0]['_id']
    target = target_access(db, target_type, target_id, uid, 'edit')
    return [invitation_response(row) for row in db.invitations.find({
        'target_type': target_type, 'target_id': target['_id'],
    }).sort([('created_at', -1), ('_id', 1)])]


@router.delete('/invitations/{invitation_id}', status_code=204)
def delete_invitation(invitation_id: str, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']

    def delete(session):
        invitation = db.invitations.find_one({'_id': object_id(invitation_id)}, session=session)
        if invitation is None:
            raise APIError('not_found')
        kind = invitation['target_type']
        target = target_access(db, kind, invitation['target_id'], uid, session=session)
        owner = (resolve(db, target, uid, session=session).manage if kind == 'song'
                 else target['owner_id'] == uid)
        if invitation['created_by'] != uid and not owner:
            raise APIError('forbidden')
        db.invitations.delete_one({'_id': invitation['_id']}, session=session)

    transact(db, delete)
    return Response(status_code=204)


@router.post('/invitations/{token}/use', status_code=201)
def use_invitation(token: str, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']

    def use(session):
        now = request.app.state.clock()
        invitation = db.invitations.find_one({'token_hash': sha256(token), 'expires_at': {'$gt': now}}, session=session)
        if invitation is None:
            raise APIError('not_found')
        kind, target_id = invitation['target_type'], invitation['target_id']
        target = (db.songs if kind == 'song' else db.bands).find_one({'_id': target_id}, session=session)
        if target is None:
            raise APIError('not_found')
        access = (resolve(db, target, uid, session=session).view if kind == 'song'
                  else band_access(db, target_id, uid, session=session)[0])
        if access:
            raise APIError('already_member')
        # Conflicts with editor-loss transactions and personal-to-band moves.
        touch(db, kind, target, now, session)
        return membership(db, kind, target_id, uid, invitation['role'], invitation['_id'], now, session)

    try:
        return json_document(transact(db, use))
    except DuplicateKeyError:
        raise APIError('already_member') from None


def list_members(kind, target_id, request, current):
    db, uid = request.app.state.db, current[0]['_id']
    target = target_access(db, kind, target_id, uid)
    owner_id = (target['owner_id'] if kind == 'band' or target['owner_type'] == 'user'
                else db.bands.find_one({'_id': target['owner_id']})['owner_id'])
    rows = [(owner_id, None if kind == 'band' else 'editor')]
    rows += [(m['user_id'], m['role']) for m in db.memberships.find({
        'target_type': kind, 'target_id': target['_id'],
    }) if m['user_id'] != owner_id]
    result = []
    for member_id, role in rows:
        user = db.users.find_one({'_id': member_id})
        if user:
            result.append({**public_user(user), 'role': role})
    return sorted(result, key=lambda row: row['username'])


@router.get('/bands/{band_id}/members')
def band_members(band_id: str, request: Request, current: Current):
    return list_members('band', band_id, request, current)


@router.get('/songs/{song_id}/members')
def song_members(song_id: str, request: Request, current: Current):
    return list_members('song', song_id, request, current)


def cascade_links(db, kind, target, uid, session):
    destinations = [{'target_type': kind, 'target_id': target['_id']}]
    if kind == 'band':
        for song in db.songs.find({'owner_type': 'band', 'owner_id': target['_id']}, session=session):
            destinations.append({'target_type': 'song', 'target_id': song['_id']})
            # Lock song editor checks too: a concurrent creator retries permissions.
            touch(db, 'song', song, target['updated_at'], session)
    db.invitations.delete_many({'created_by': uid, '$or': destinations}, session=session)


def remove_member(kind, target_id, username, request, current):
    db, uid = request.app.state.db, current[0]['_id']

    def remove(session):
        leaving = username == 'me'
        target = target_access(db, kind, target_id, uid, 'view' if leaving else 'manage', session=session)
        user = current[0] if leaving else db.users.find_one({'username': username}, session=session)
        if leaving and kind == 'band' and target['owner_id'] == uid:
            raise APIError('owner_must_transfer')
        member = None if user is None else db.memberships.find_one({
            'target_type': kind, 'target_id': target['_id'], 'user_id': user['_id'],
        }, session=session)
        if member is None:
            raise APIError('not_found')
        was_editor = (kind == 'band' or resolve(db, target, user['_id'], session=session).edit)
        db.memberships.delete_one({'_id': member['_id']}, session=session)
        touch(db, kind, target, request.app.state.clock(), session)
        remains_editor = kind == 'song' and resolve(db, target, user['_id'], session=session).edit
        if was_editor and not remains_editor:
            cascade_links(db, kind, target, user['_id'], session)

    transact(db, remove)
    return Response(status_code=204)


@router.delete('/bands/{band_id}/members/{username}', status_code=204)
def remove_band_member(band_id: str, username: str, request: Request, current: Current):
    return remove_member('band', band_id, username, request, current)


@router.delete('/songs/{song_id}/members/{username}', status_code=204)
def remove_song_member(song_id: str, username: str, request: Request, current: Current):
    return remove_member('song', song_id, username, request, current)


@router.patch('/songs/{song_id}/members/{username}')
def set_member_role(song_id: str, username: str, body: MemberRole, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']

    def update(session):
        song = require_song(db, song_id, uid, 'manage', session=session)
        user = db.users.find_one({'username': username}, session=session)
        member = None if user is None else db.memberships.find_one({
            'target_type': 'song', 'target_id': song['_id'], 'user_id': user['_id'],
        }, session=session)
        if member is None:
            raise APIError('not_found')
        was_editor = resolve(db, song, user['_id'], session=session).edit
        db.memberships.update_one({'_id': member['_id']}, {'$set': {'role': body.role}}, session=session)
        touch(db, 'song', song, request.app.state.clock(), session)
        if was_editor and not resolve(db, song, user['_id'], session=session).edit:
            cascade_links(db, 'song', song, user['_id'], session)
        return {**public_user(user), 'role': body.role}

    return transact(db, update)


@router.post('/bands/{band_id}/transfer')
def transfer_band(band_id: str, body: Transfer, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']

    def transfer(session):
        band = target_access(db, 'band', band_id, uid, 'manage', session=session)
        user = db.users.find_one({'username': body.username}, session=session)
        incoming = None if user is None else db.memberships.find_one({
            'target_type': 'band', 'target_id': band['_id'], 'user_id': user['_id'],
        }, session=session)
        if incoming is None or user['_id'] == uid:
            raise APIError('validation_error')
        now = request.app.state.clock()
        touch(db, 'band', band, now, session)
        db.bands.update_one({'_id': band['_id']}, {'$set': {'owner_id': user['_id']}}, session=session)
        db.memberships.delete_one({'_id': incoming['_id']}, session=session)
        membership(db, 'band', band['_id'], uid, None, None, now, session)
        return db.bands.find_one({'_id': band['_id']}, session=session)

    return json_document(transact(db, transfer))


@router.post('/songs/{song_id}/move')
def move_song(song_id: str, body: Move, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']

    def move(session):
        song = require_song(db, song_id, uid, session=session)
        if song['owner_type'] != 'user':
            raise APIError('validation_error')
        resolve(db, song, uid, session=session).require('manage')
        band = target_access(db, 'band', body.band_id, uid, session=session)
        total = sum(demo['size_bytes'] for row in db.songs.find({
            'owner_type': 'band', 'owner_id': band['_id'],
        }, session=session) for demo in row['demos'])
        if total + sum(d['size_bytes'] for d in song['demos']) > 2 * 1024 ** 3:
            raise APIError('quota_exceeded')
        now = request.app.state.clock()
        touch(db, 'band', band, now, session)
        touch(db, 'song', song, now, session)
        db.songs.update_one({'_id': song['_id']}, {'$set': {'owner_type': 'band', 'owner_id': band['_id']}}, session=session)
        members = [band['owner_id']] + [m['user_id'] for m in db.memberships.find({
            'target_type': 'band', 'target_id': band['_id'],
        }, session=session)]
        db.memberships.delete_many({'target_type': 'song', 'target_id': song['_id'],
                                    'user_id': {'$in': members}}, session=session)
        return db.songs.find_one({'_id': song['_id']}, session=session)

    return song_response(transact(db, move))
