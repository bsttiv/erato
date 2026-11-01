"""Songs, explicit section saves and revision history (approved decisions 05–09)."""
from copy import deepcopy
import secrets
from typing import Literal

from bson import ObjectId
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.accounts import Current, new_id, public_user
from app.detection import analyze, candidate_keys, name_chord
from app.errors import APIError
from app.permissions import band_access, object_id, require_song, resolve
from app.sections import (Chord, FIELDS, META, SECTIONS, Restore, Save, SongCreate, revision_summary,
                          Visibility, assign, content, normalize)
from app.storage import destroy_asset

router = APIRouter()


def json_document(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, dict):
        return {('id' if key == '_id' else key): json_document(child) for key, child in value.items()}
    if isinstance(value, list):
        return [json_document(child) for child in value]
    return value


STORAGE_FIELDS = {'cloudinary_public_id', 'format'}


def demo_response(demo):
    return json_document({key: value for key, value in demo.items() if key not in STORAGE_FIELDS})


def song_response(song):
    return {**json_document(song), 'demos': [demo_response(demo) for demo in song['demos']],
            'key_candidates': candidate_keys([c['notes'] for c in song['chords']])}


def public_document(value):
    if isinstance(value, dict):
        hidden = {'_id', 'owner_id', 'uploaded_by', 'author_id', *STORAGE_FIELDS}
        return {key: public_document(child) for key, child in value.items() if key not in hidden}
    if isinstance(value, list):
        return [public_document(child) for child in value]
    return json_document(value)


def transact(db, callback):
    # MongoDB retries write-conflicted snapshots. Every retry rechecks permissions
    # and section bases; revisions and the embedded state commit together.
    with db.client.start_session() as session:
        return session.with_transaction(callback)


def write_revision(db, song, section, author_id, now, session, summary):
    db.revisions.insert_one({
        '_id': new_id(), 'song_id': song['_id'], 'section': section,
        'version': song['section_versions'][section], 'author_id': author_id,
        'created_at': now, 'content': content(song, section), 'summary': summary,
    }, session=session)
    retained = list(db.revisions.find({'song_id': song['_id'], 'section': section},
                                      {'_id': 1}, session=session).sort('version', -1).skip(50))
    if retained:
        db.revisions.delete_many({'_id': {'$in': [row['_id'] for row in retained]}}, session=session)


@router.post('/songs', status_code=201)
def create_song(body: SongCreate, request: Request, current: Current):
    user_id = current[0]['_id']
    db = request.app.state.db

    def create(session):
        owner_id = user_id if body.owner_type == 'user' else ObjectId(body.owner_id)
        if body.owner_type == 'band' and not band_access(db, owner_id, user_id, session=session)[0]:
            raise APIError('not_found')
        now = request.app.state.clock()
        meta = {field: getattr(body, field) for field in META}
        try:
            meta['key'] = analyze([], meta['key_mode'], meta['key'])['key']
        except ValueError:
            raise APIError('validation_error') from None
        if body.key_mode == 'auto' and body.key is not None:
            raise APIError('validation_error')
        song = {'_id': new_id(), 'owner_type': body.owner_type, 'owner_id': owner_id,
                **meta, 'visibility': 'private', 'share_slug': None,
                'chords': [], 'tablatures': [], 'lyrics': None, 'tasks': [], 'demos': [],
                'section_versions': dict.fromkeys(SECTIONS, 1), 'created_at': now, 'updated_at': now}
        db.songs.insert_one(song, session=session)
        write_revision(db, song, 'meta', user_id, now, session, 'creó la composición')
        return db.songs.find_one({'_id': song['_id']}, session=session)

    return song_response(transact(db, create))


@router.get('/songs')
def list_songs(request: Request, current: Current,
               workspace: Literal['personal', 'shared', 'all', 'band'] = 'personal', band_id: str | None = None):
    db, uid = request.app.state.db, current[0]['_id']
    own = {'owner_type': 'user', 'owner_id': uid}
    song_ids = [m['target_id'] for m in db.memberships.find({'target_type': 'song', 'user_id': uid})]
    band_ids = {m['target_id'] for m in db.memberships.find({'target_type': 'band', 'user_id': uid})}
    band_ids.update(b['_id'] for b in db.bands.find({'owner_id': uid}))
    shared = {'_id': {'$in': song_ids}, '$nor': [own, {'owner_type': 'band', 'owner_id': {'$in': list(band_ids)}}]}
    if workspace == 'band':
        target = object_id(band_id)
        if not band_access(db, target, uid)[0]:
            raise APIError('not_found')
        query = {'owner_type': 'band', 'owner_id': target}
    elif workspace == 'personal':
        query = own
    elif workspace == 'shared':
        query = shared
    else:
        query = {'$or': [own, shared, {'owner_type': 'band', 'owner_id': {'$in': list(band_ids)}}]}
    songs = []
    for song in db.songs.find(query).sort('updated_at', -1):
        # Discard stale memberships to deleted bands, and re-resolve every row.
        if not resolve(db, song, uid).view:
            continue
        origin = ('own' if song['owner_type'] == 'user' and song['owner_id'] == uid else
                  'band' if song['owner_type'] == 'band' and song['owner_id'] in band_ids else 'shared')
        songs.append({**song_response(song), 'origin': origin})
    return songs


@router.get('/songs/{song_id}')
def read_song(song_id: str, request: Request, current: Current):
    return song_response(require_song(request.app.state.db, song_id, current[0]['_id']))


@router.get('/c/{slug}')
def read_public_song(slug: str, request: Request):
    song = request.app.state.db.songs.find_one({'share_slug': slug, 'visibility': 'public'})
    if song is None:
        raise APIError('not_found')
    result = public_document(song)
    for demo, source in zip(result['demos'], song['demos']):
        user = request.app.state.db.users.find_one({'_id': source['uploaded_by']})
        demo['author'] = public_user(user) if user else None
    result['key_candidates'] = candidate_keys([c['notes'] for c in song['chords']])
    return result


@router.patch('/songs/{song_id}/visibility')
def set_visibility(song_id: str, body: Visibility, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']

    def update(session):
        song = require_song(db, song_id, uid, 'manage', session=session)
        if song['visibility'] != body.visibility:
            slug = None
            if body.visibility == 'public':
                slug = secrets.token_urlsafe(16)
                while db.songs.find_one({'share_slug': slug}, session=session):
                    slug = secrets.token_urlsafe(16)
            db.songs.update_one({'_id': song['_id']}, {'$set': {
                'visibility': body.visibility, 'share_slug': slug, 'updated_at': request.app.state.clock(),
            }}, session=session)
        return db.songs.find_one({'_id': song['_id']}, session=session)

    return song_response(transact(db, update))


class VersionConflict(Exception):
    def __init__(self, conflicts):
        self.conflicts = conflicts


def conflict_response(error):
    return JSONResponse(status_code=409, content={
        'code': 'version_conflict', 'detail': 'Sections have changed',
        'saved': [], 'conflicts': error.conflicts,
    })


def lyric_ids(lyrics):
    return {p['chord_id'] for line in lyrics['lines'] for p in line['chords']} if lyrics else set()


def plan_save(song, submitted, bases, *, historical=False):
    """Build a coherent partial save without ever persisting a dangling chord ID."""
    conflicts = {section for section in submitted if bases[section] != song['section_versions'][section]}
    # A stale array may legitimately contain IDs deleted since its base. It is
    # validated structurally, never written; its dependent sections conflict too.
    normalized = {section: normalize(section, value, song, historical=historical or section in conflicts)
                  for section, value in submitted.items()}
    for _ in range(len(SECTIONS) + 1):
        candidate = deepcopy(song)
        active = normalized.keys() - conflicts
        for section in active:
            assign(candidate, section, normalized[section])
        chord_ids = {c['id'] for c in candidate['chords']}
        if 'lyrics' in active and not lyric_ids(candidate['lyrics']) <= chord_ids:
            # A valid new reference cannot be saved when its chord save failed.
            attempted_ids = {c['id'] for c in normalized.get('chords', [])}
            missing = lyric_ids(candidate['lyrics']) - chord_ids
            if 'chords' in conflicts and missing <= attempted_ids:
                conflicts.add('lyrics')
                continue
            raise ValueError('Lyrics refer to chords outside this song')
        removed = {c['id'] for c in song['chords']} - chord_ids
        if removed and candidate['lyrics']:
            for line in candidate['lyrics']['lines']:
                line['chords'] = [p for p in line['chords'] if p['chord_id'] not in removed]
        music_changed = ('chords' in active or 'meta' in active)
        analysis = analyze([c['notes'] for c in candidate['chords']], candidate['key_mode'], candidate['key'])
        if music_changed:
            explicit_key = ('meta' in active and 'key' in submitted['meta'])
            if explicit_key and candidate['key_mode'] == 'auto' and candidate['key'] not in analysis['candidates']:
                if candidate['key'] is not None or analysis['candidates']:
                    if 'chords' in conflicts:
                        conflicts.add('meta')
                        continue
                    raise ValueError('Auto key must be a candidate')
            candidate['key'] = analysis['key']
            for chord, name in zip(candidate['chords'], analysis['names']):
                chord['name'] = name
        changed = {section for section in SECTIONS if content(song, section) != content(candidate, section)}
        # An implicit rename/cleanup/key update must not bypass an explicitly
        # conflicted section. Keep the requesting dependency conflicted too.
        blocked_dependencies = changed & conflicts
        if blocked_dependencies:
            dependents = set()
            if 'lyrics' in blocked_dependencies:
                dependents.add('chords')
            if 'meta' in blocked_dependencies:
                dependents.add('chords')
            if 'chords' in blocked_dependencies:
                dependents.add('meta')
            conflicts.update(dependents & active)
            continue
        return candidate, changed, conflicts, analysis['key_reset'] if music_changed else False
    raise ValueError('Inconsistent section dependencies')


def persist_save(db, song_id, user_id, submitted, bases, now, session, *, restore=None):
    song = require_song(db, song_id, user_id, 'edit', session=session)
    if isinstance(submitted.get('meta'), dict) and 'visibility' in submitted['meta']:
        resolve(db, song, user_id, session=session).require('manage')
    if restore is not None:
        section, version = restore
        if section not in SECTIONS:
            raise APIError('not_found')
        revision = db.revisions.find_one({'song_id': song['_id'], 'section': section, 'version': version}, session=session)
        if revision is None:
            raise APIError('not_found')
        historical = deepcopy(revision['content'])
        if section == 'chords':
            historical = [{k: v for k, v in chord.items() if k != 'name'} for chord in historical]
        submitted = {section: json_document(historical)}
    try:
        candidate, changed, conflicts, reset = plan_save(song, submitted, bases, historical=restore is not None)
    except (ValueError, TypeError, ValidationError):
        raise APIError('validation_error') from None
    conflict_rows = [{'section': s, 'current_version': song['section_versions'][s]} for s in SECTIONS if s in conflicts]
    if set(submitted) <= conflicts:
        raise VersionConflict(conflict_rows)
    if restore is not None:
        changed.add(restore[0])  # Restoring creates a new version, even for equal snapshots.
    if changed:
        for section in changed:
            candidate['section_versions'][section] += 1
        candidate['updated_at'] = now
        # Do not replace untouched arrays: demos are not versioned by this API.
        updates = {field: candidate[field] for field in META}
        updates.update({field: candidate[field] for field in FIELDS.values()})
        updates.update(section_versions=candidate['section_versions'], updated_at=now)
        db.songs.update_one({'_id': song['_id']}, {'$set': updates}, session=session)
        for section in SECTIONS:
            if section in changed:
                summary = (f'restauró la versión {restore[1]}' if restore is not None and section == restore[0]
                           else revision_summary(section, content(song, section), content(candidate, section)))
                write_revision(db, candidate, section, user_id, now, session, summary)
    result = db.songs.find_one({'_id': song['_id']}, session=session)
    return {'song': song_response(result), 'saved': [
        {'section': s, 'version': result['section_versions'][s]} for s in SECTIONS if s in changed],
        'conflicts': conflict_rows, 'key_reset': reset}


@router.put('/songs/{song_id}/sections')
def save_sections(song_id: str, body: Save, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    try:
        return transact(db, lambda session: persist_save(db, song_id, uid, body.sections, body.base_versions,
                                                         request.app.state.clock(), session))
    except VersionConflict as error:
        return conflict_response(error)


@router.post('/songs/{song_id}/chord-name')
def preview_chord(song_id: str, body: Chord, request: Request, current: Current):
    song = require_song(request.app.state.db, song_id, current[0]['_id'], 'edit')
    return {'name': name_chord(body.notes, song['key'])}


def revision_response(db, revision):
    user = db.users.find_one({'_id': revision['author_id']})
    # Deleted accounts are not implemented; a missing author exposes no private data.
    return {'section': revision['section'], 'version': revision['version'],
            'created_at': revision['created_at'], 'content': json_document(revision['content']),
            'summary': revision.get('summary'), 'author': public_user(user) if user else None}


@router.get('/songs/{song_id}/revisions/{section}')
def list_revisions(song_id: str, section: Literal['lyrics', 'chords', 'tabs', 'tasks', 'meta'],
                   request: Request, current: Current):
    db = request.app.state.db
    song = require_song(db, song_id, current[0]['_id'])
    return [revision_response(db, revision) for revision in db.revisions.find({
        'song_id': song['_id'], 'section': section,
    }).sort('version', -1)]


@router.get('/songs/{song_id}/revisions/{section}/{version}')
def read_revision(song_id: str, section: str, version: int, request: Request, current: Current):
    db = request.app.state.db
    song = require_song(db, song_id, current[0]['_id'])
    revision = db.revisions.find_one({'song_id': song['_id'], 'section': section, 'version': version})
    if revision is None:
        raise APIError('not_found')
    return revision_response(db, revision)


@router.post('/songs/{song_id}/revisions/{section}/{version}/restore')
def restore_revision(song_id: str, section: str, version: int, body: Restore, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    try:
        return transact(db, lambda session: persist_save(db, song_id, uid, {}, {section: body.base_version},
                                                         request.app.state.clock(), session, restore=(section, version)))
    except VersionConflict as error:
        return conflict_response(error)


@router.delete('/songs/{song_id}', status_code=204)
def delete_song(song_id: str, request: Request, current: Current):
    db, uid = request.app.state.db, current[0]['_id']
    # Remote deletion precedes DB deletion: a Cloudinary error never drops metadata.
    song = require_song(db, song_id, uid, 'manage')
    for demo in song['demos']:
        destroy_asset(request.app.state.config, demo['cloudinary_public_id'])

    def delete(session):
        song = require_song(db, song_id, uid, 'manage', session=session)
        for collection in ('demo_comments', 'revisions'):
            db[collection].delete_many({'song_id': song['_id']}, session=session)
        for collection in ('invitations', 'memberships'):
            db[collection].delete_many({'target_type': 'song', 'target_id': song['_id']}, session=session)
        db.songs.delete_one({'_id': song['_id']}, session=session)

    transact(db, delete)
    return Response(status_code=204)
