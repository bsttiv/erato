"""Approved decision 06/09/14 rules; rule names do not invent missing numeric IDs."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from bson import ObjectId
import cloudinary.uploader
import pytest

from test_accounts import api, maestro, register, headers


def snapshot(db):
    return {name: list(db[name].find().sort('_id', 1))
            for name in sorted(db.list_collection_names())}


def error(db, call, status, code):
    before = snapshot(db)
    response = call()
    assert response.status_code == status, response.text
    assert response.json()['code'] == code
    assert snapshot(db) == before
    return response


@pytest.fixture
def owner(api, db):
    auth = headers(register(api))
    uid = db.users.find_one({'username': 'alice'})['_id']
    return auth, uid


def create(api, auth, **extra):
    response = api.post('/songs', headers=auth, json={'title': 'Under the lamp', **extra})
    assert response.status_code == 201, response.text
    return response.json()


def save(api, auth, song, sections, bases=None):
    return api.put(f'/songs/{song["id"]}/sections', headers=auth, json={
        'sections': sections, 'base_versions': bases or song['section_versions'],
    })


def piano(notes, **extra):
    return {'instrument': 'piano', 'notes': notes, **extra}


def payload_chords(song):
    return [{k: v for k, v in chord.items() if k != 'name'} for chord in song['chords']]


def test_song_rule_creation_defaults(api, db, owner):
    auth, uid = owner
    song = create(api, auth)
    assert song['owner_type'] == 'user' and song['owner_id'] == str(uid)
    assert song['status'] == 'idea' and song['visibility'] == 'private'
    assert song['key_mode'] == 'auto' and song['key'] is song['lyrics'] is song['share_slug'] is None
    assert all(song[field] == [] for field in ('chords', 'tablatures', 'tasks', 'demos'))
    assert song['section_versions'] == dict.fromkeys(('lyrics', 'chords', 'tabs', 'tasks', 'meta'), 1)
    assert song['created_at'].endswith('+00:00') or song['created_at'].endswith('Z')
    revision = db.revisions.find_one()
    assert db.revisions.count_documents({}) == 1
    assert revision['section'] == 'meta' and revision['version'] == 1 and revision['author_id'] == uid
    assert api.get(f'/songs/{song["id"]}', headers=auth).json() == song


@pytest.mark.parametrize('field,value', [
    ('title', ''), ('title', '  '), ('status', 'finished'), ('tempo', 19), ('tempo', 401),
    ('tempo', -5), ('tempo', 0), ('tempo', 92.5), ('time_signature', '0/4'),
    ('time_signature', '33/4'), ('time_signature', '4/3'), ('time_signature', '4/64'),
    ('time_signature', 'x/y'), ('key', 'H#'), ('key', 'c'), ('key', 'E#'), ('key', 'Fb'),
    ('key', 'Cbm'), ('key', 'A#'), ('key_mode', 'random'),
])
def test_song_rule_metadata_validation(api, db, owner, field, value):
    auth, _ = owner
    song = create(api, auth)
    error(db, lambda: save(api, auth, song, {'meta': {field: value}}), 422, 'validation_error')


@pytest.mark.parametrize('field,value', [('owner_id', str(ObjectId())), ('owner_type', 'band'),
                                         ('section_versions', {'meta': 5}), ('share_slug', 'mine')])
def test_song_rule_protected_fields(api, db, owner, field, value):
    auth, _ = owner
    song = create(api, auth)
    error(db, lambda: save(api, auth, song, {'meta': {field: value}}), 422, 'validation_error')


@pytest.mark.parametrize('owner_type', ['user', 'band'])
@pytest.mark.parametrize('visibility', ['private', 'public'])
@pytest.mark.parametrize('actor', ['ANON', 'EXT', 'OWN', 'SE', 'SV', 'BO', 'BE', 'IL'])
@pytest.mark.parametrize('action', ['view', 'edit', 'manage', 'delete'])
def test_perm_rule_matrix(api, db, owner, owner_type, visibility, actor, action):
    auth, uid = owner
    outsider = headers(register(api, 'bob'))
    bob = db.users.find_one({'username': 'bob'})['_id']
    now = datetime.now(timezone.utc)
    band = ObjectId()
    db.bands.insert_one({'_id': band, 'name': 'Faroles', 'owner_id': uid,
                         'created_at': now, 'updated_at': now})
    db.memberships.insert_one({'target_type': 'band', 'target_id': band,
                               'user_id': uid, 'role': None, 'invitation_id': None, 'joined_at': now})
    song = create(api, auth, **({'owner_type': 'band', 'owner_id': str(band)} if owner_type == 'band' else {}))
    if visibility == 'public':
        assert api.patch(f'/songs/{song["id"]}/visibility', headers=auth,
                         json={'visibility': 'public'}).status_code == 200
    if actor in ('SE', 'SV'):
        db.memberships.insert_one({'target_type': 'song', 'target_id': ObjectId(song['id']),
                                   'user_id': bob, 'role': 'editor' if actor == 'SE' else 'viewer',
                                   'invitation_id': None, 'joined_at': now})
    if actor == 'BE':
        db.memberships.insert_one({'target_type': 'band', 'target_id': band, 'user_id': bob,
                                   'role': None, 'invitation_id': None, 'joined_at': now})
    acting_owner = actor == ('OWN' if owner_type == 'user' else 'BO')
    actor_auth = {} if actor == 'ANON' else auth if acting_owner else outsider
    view = acting_owner or actor in ('SE', 'SV') or (owner_type == 'band' and actor == 'BE')
    edit = acting_owner or actor == 'SE' or (owner_type == 'band' and actor == 'BE')
    allowed = {'view': view, 'edit': edit, 'manage': acting_owner, 'delete': acting_owner}[action]
    path = f'/songs/{song["id"]}'
    call = {'view': lambda: api.get(path, headers=actor_auth),
            'edit': lambda: save(api, actor_auth, song, {'tasks': [{'title': 'Record bass', 'done': False}]}),
            'manage': lambda: api.patch(path + '/visibility', headers=actor_auth, json={'visibility': 'private'}),
            'delete': lambda: api.delete(path, headers=actor_auth)}[action]
    if allowed:
        assert call().status_code in (200, 204)
    else:
        error(db, call, 401 if actor == 'ANON' else 403 if view else 404,
              'not_authenticated' if actor == 'ANON' else 'forbidden' if view else 'not_found')


def test_perm_061_membership_rechecked(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    visitor = headers(register(api, 'bob'))
    uid = db.users.find_one({'username': 'bob'})['_id']
    membership = {'target_type': 'song', 'target_id': ObjectId(song['id']), 'user_id': uid, 'role': 'editor'}
    db.memberships.insert_one(membership)
    assert api.get(f'/songs/{song["id"]}', headers=visitor).status_code == 200
    db.memberships.delete_one({'_id': membership['_id']})
    error(db, lambda: api.get(f'/songs/{song["id"]}', headers=visitor), 404, 'not_found')


def test_perm_062_role_rechecked(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    visitor = headers(register(api, 'bob'))
    uid = db.users.find_one({'username': 'bob'})['_id']
    db.memberships.insert_one({'target_type': 'song', 'target_id': ObjectId(song['id']),
                               'user_id': uid, 'role': 'editor'})
    assert save(api, visitor, song, {'tasks': [{'title': 'Record bass', 'done': False}]}).status_code == 200
    db.memberships.update_one({'user_id': uid}, {'$set': {'role': 'viewer'}})
    error(db, lambda: save(api, visitor, song, {'tasks': []}), 403, 'forbidden')


def test_slug_rule_public_projection_and_rotation(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    path = f'/songs/{song["id"]}/visibility'
    public = api.patch(path, headers=auth, json={'visibility': 'public'}).json()
    slug = public['share_slug']
    assert len(slug) == 22
    response = api.get('/c/' + slug)
    assert response.status_code == 200
    def safe(value):
        if isinstance(value, dict):
            assert not {'_id', 'owner_id', 'author_id', 'uploaded_by', 'cloudinary_public_id'} & value.keys()
            for child in value.values(): safe(child)
        elif isinstance(value, list):
            for child in value: safe(child)
    safe(response.json())
    assert 'id' not in response.json()
    assert save(api, auth, song, {'meta': {'title': 'New name'}}).status_code == 200
    assert api.get('/c/' + slug).status_code == 200
    before_meta = db.revisions.count_documents({'section': 'meta'})
    assert api.patch(path, headers=auth, json={'visibility': 'private'}).status_code == 200
    error(db, lambda: api.get('/c/' + slug), 404, 'not_found')
    new = api.patch(path, headers=auth, json={'visibility': 'public'}).json()
    assert new['share_slug'] != slug
    assert db.revisions.count_documents({'section': 'meta'}) == before_meta
    before = snapshot(db)
    assert api.post('/c/' + new['share_slug'], json={}).status_code in (404, 405)
    assert snapshot(db) == before


@pytest.mark.parametrize('chord', [
    piano([]), piano([48, 60]), piano([-1, 55]), piano([48, 128]),
    piano([48, 55], frets=[0, 0]), piano([48, 55], name='C5'),
    {'instrument': 'bass', 'notes': [48, 55]},
    {'instrument': 'guitar', 'notes': [48, 55], 'frets': [3], 'strings': [5, 3]},
    {'instrument': 'guitar', 'notes': [48, 55], 'frets': [3, 0], 'strings': [5, 7]},
    {'instrument': 'guitar', 'notes': [48, 55], 'frets': [-1, 25], 'strings': [5, 3]},
    {'instrument': 'guitar', 'notes': [48, 55], 'frets': [3, 0], 'strings': [5, 5]},
    {'instrument': 'guitar', 'notes': [48, 55], 'frets': [2, 0], 'strings': [5, 3]},
])
def test_chd_rule_validation(api, db, owner, chord):
    auth, _ = owner
    song = create(api, auth)
    error(db, lambda: save(api, auth, song, {'chords': [chord]}), 422, 'validation_error')


def test_chd_018_power_chord_and_shapes(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    response = save(api, auth, song, {'chords': [piano([48, 55]), piano([60, 67])]})
    assert response.status_code == 200, response.text
    chords = response.json()['song']['chords']
    assert [chord['name'] for chord in chords] == ['C5', 'C5']
    assert chords[0]['id'] != chords[1]['id']
    assert isinstance(db.songs.find_one()['chords'][0]['id'], ObjectId)
    preview = api.post(f'/songs/{song["id"]}/chord-name', headers=auth, json=piano([48, 55]))
    assert preview.status_code == 200 and preview.json()['name'] == 'C5'


VALID_CELLS = ['', 'x', '0', '24', '3h5', '5p3', '7b9', '9r7', '3/5', '5\\3', '3s5',
               '5~', '5v', '5h7p5', '5h7p5~', '3/5/7', '7b9r7']
INVALID_CELLS = ['X', '25', '-1', '03', '3h', '5p', '7b', '9r', '3/', '5\\', '3s', 'h5',
                 '3q5', '3h25', '5~7', '5v7', '1h2h3h4h5', '5~h7', '5h7~~', '5hp7',
                 '5h7p25', 'abc', '1.5', 3, 'x5', '||', '3 ', ' 3']


@pytest.mark.parametrize('cell', VALID_CELLS + INVALID_CELLS)
def test_tab_rule_cell_grammar(api, db, owner, cell):
    auth, _ = owner
    song = create(api, auth)
    call = lambda: save(api, auth, song, {'tabs': [{'columns': [[cell, '', '', '', '', '']]}]})
    if cell in INVALID_CELLS:
        error(db, call, 422, 'validation_error')
    else:
        response = call()
        assert response.status_code == 200, response.text
        tab = response.json()['song']['tablatures'][0]
        assert tab['title'] == 'Tablatura 1' and tab['tuning'] == ['E4', 'B3', 'G3', 'D3', 'A2', 'E2']
        assert tab['columns'][0][0] == cell


@pytest.mark.parametrize('tab', [
    {'columns': [['|', '0', '', '', '', '']]}, {'columns': [[''] * 5]}, {'columns': [[''] * 7]},
    *[{'columns': [], 'tuning': tuning} for tuning in (
        ['E4'] * 5, ['E4'] * 7, ['H9'] * 6, ['E'] * 6, ['e4'] * 6, ['E10'] * 6)],
])
def test_tab_rule_columns_and_tuning_validation(api, db, owner, tab):
    auth, _ = owner
    song = create(api, auth)
    error(db, lambda: save(api, auth, song, {'tabs': [tab]}), 422, 'validation_error')


def test_lyr_rule_placements_and_chord_deletion(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'chords': [piano([48, 55]), piano([50, 57])]}).json()['song']
    first, second = (chord['id'] for chord in song['chords'])
    lyrics = {'lines': [{'text': '', 'chords': [{'col': 20, 'chord_id': first}]},
                        {'text': 'Song', 'chords': [{'col': 0, 'chord_id': second}]}]}
    song = save(api, auth, song, {'lyrics': lyrics}).json()['song']
    for placements in ([{'col': -1, 'chord_id': first}], [{'col': 0, 'chord_id': str(ObjectId())}],
                       [{'col': 0, 'chord_id': first}, {'col': 0, 'chord_id': second}]):
        error(db, lambda: save(api, auth, song, {'lyrics': {'lines': [{'text': '', 'chords': placements}]}}),
              422, 'validation_error')
    updated = save(api, auth, song, {'chords': payload_chords(song)[1:]}).json()['song']
    assert updated['lyrics']['lines'] == [{'text': '', 'chords': []}, lyrics['lines'][1]]
    assert updated['section_versions']['lyrics'] == song['section_versions']['lyrics'] + 1
    assert db.revisions.find_one({'section': 'lyrics', 'version': updated['section_versions']['lyrics']})
    assert save(api, auth, updated, {'lyrics': None}).json()['song']['lyrics'] is None


def test_lyr_001_section_is_trimmed_and_stored(api, db, owner):
    auth, _ = owner
    lines = [{'section': ' Coro ', 'text': '', 'chords': []}]
    song = save(api, auth, create(api, auth), {'lyrics': {'lines': lines}}).json()['song']
    assert song['lyrics']['lines'] == [{'section': 'Coro', 'text': '', 'chords': []}]
    assert db.songs.find_one()['lyrics']['lines'][0]['section'] == 'Coro'


def test_lyr_002_section_rejects_text(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    lines = [{'section': 'Coro', 'text': 'Hola', 'chords': []}]
    error(db, lambda: save(api, auth, song, {'lyrics': {'lines': lines}}), 422, 'validation_error')


def test_lyr_003_section_rejects_chords(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'chords': [piano([48, 55])]}).json()['song']
    placement = {'col': 0, 'chord_id': song['chords'][0]['id']}
    lines = [{'section': 'Coro', 'text': '', 'chords': [placement]}]
    error(db, lambda: save(api, auth, song, {'lyrics': {'lines': lines}}), 422, 'validation_error')


@pytest.mark.parametrize('section', ['', '   ', 'x' * 41])
def test_lyr_004_section_length(api, db, owner, section):
    auth, _ = owner
    song = create(api, auth)
    lines = [{'section': section, 'text': '', 'chords': []}]
    error(db, lambda: save(api, auth, song, {'lyrics': {'lines': lines}}), 422, 'validation_error')


def test_lyr_005_line_without_section_has_no_key(api, db, owner):
    auth, _ = owner
    lyrics = {'lines': [{'text': 'Hola', 'chords': []}]}
    song = save(api, auth, create(api, auth), {'lyrics': lyrics}).json()['song']
    assert song['lyrics'] == lyrics
    assert 'section' not in db.songs.find_one()['lyrics']['lines'][0]


def test_lyr_006_restore_revision_without_sections(api, db, owner):
    auth, _ = owner
    lyrics = {'lines': [{'text': 'Hola', 'chords': []}]}
    song = save(api, auth, create(api, auth), {'lyrics': lyrics}).json()['song']
    version = song['section_versions']['lyrics']
    named = {'lines': [{'section': 'Coro', 'text': '', 'chords': []}]}
    song = save(api, auth, song, {'lyrics': named}).json()['song']
    restored = api.post(f'/songs/{song["id"]}/revisions/lyrics/{version}/restore', headers=auth,
                        json={'base_version': song['section_versions']['lyrics']})
    assert restored.status_code == 200, restored.text
    assert restored.json()['song']['lyrics'] == lyrics
    assert 'section' not in db.songs.find_one()['lyrics']['lines'][0]


@pytest.mark.parametrize('task', [{'title': ''}, {'title': '  '}, {'title': 'x' * 201},
                                 {'title': 'Record bass', 'done': 1}])
def test_task_rule_validation(api, db, owner, task):
    auth, _ = owner
    song = create(api, auth)
    error(db, lambda: save(api, auth, song, {'tasks': [task]}), 422, 'validation_error')


def test_task_rule_lifecycle(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'tasks': [{'title': ' Record bass ', 'done': False}]}).json()['song']
    task = song['tasks'][0]
    assert task['title'] == 'Record bass' and task['done'] is False
    task.update(title='Record guitar', done=True)
    song = save(api, auth, song, {'tasks': [task]}).json()['song']
    assert song['tasks'] == [task]
    assert save(api, auth, song, {'tasks': []}).json()['song']['tasks'] == []


def test_rev_rule_partial_conflicts_noop_and_missing_base(api, db, owner):
    auth, _ = owner
    original = create(api, auth)
    song = save(api, auth, original, {'tasks': [{'title': 'Record bass', 'done': False}]}).json()['song']
    before = snapshot(db)
    response = save(api, auth, song, {'tasks': song['tasks']})
    assert response.status_code == 200 and response.json()['saved'] == []
    assert snapshot(db) == before
    error(db, lambda: api.put(f'/songs/{song["id"]}/sections', headers=auth,
                              json={'sections': {'tasks': []}, 'base_versions': {}}), 422, 'validation_error')
    error(db, lambda: save(api, auth, original, {'tasks': []}), 409, 'version_conflict')
    response = save(api, auth, original, {'tasks': [], 'meta': {'title': 'Updated'}})
    assert response.status_code == 200
    assert response.json()['conflicts'] == [{'section': 'tasks', 'current_version': 2}]
    assert response.json()['saved'] == [{'section': 'meta', 'version': 2}]
    assert response.json()['song']['tasks'] == song['tasks']


def test_rev_rule_concurrent_same_base(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    before = snapshot(db)
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(lambda title: save(api, auth, song, {'meta': {'title': title}}), ['First', 'Second']))
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert next(r for r in responses if r.status_code == 409).json()['code'] == 'version_conflict'
    winner = next(r for r in responses if r.status_code == 200).json()['song']
    assert db.songs.find_one()['title'] == winner['title']
    assert db.songs.find_one()['section_versions']['meta'] == 2
    assert db.revisions.count_documents({}) == len(before['revisions']) + 1


def test_rev_rule_history_restore_and_retention(api, db, owner):
    auth, uid = owner
    song = create(api, auth)
    for index in range(51):
        response = save(api, auth, song, {'meta': {'title': f'Title {index}'}})
        assert response.status_code == 200, response.text
        song = response.json()['song']
    path = f'/songs/{song["id"]}/revisions/meta'
    rows = api.get(path, headers=auth).json()
    assert len(rows) == 50 and rows[0]['version'] == 52 and rows[-1]['version'] == 3
    assert set(rows[0]['author']) == {'username', 'display_name'}
    assert 'author_id' not in str(rows)
    error(db, lambda: api.post(path + '/1/restore', headers=auth, json={'base_version': 52}), 404, 'not_found')
    restored = api.post(path + '/3/restore', headers=auth, json={'base_version': 52})
    assert restored.status_code == 200, restored.text
    assert restored.json()['song']['title'] == 'Title 1'
    assert restored.json()['song']['section_versions']['meta'] == 53
    assert db.revisions.count_documents({'section': 'meta'}) == 50
    assert db.revisions.find_one({'version': 53})['author_id'] == uid


def test_key_002_manual_preserved(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'meta': {'key_mode': 'manual', 'key': 'D'}}).json()['song']
    song = save(api, auth, song, {'chords': [piano([48, 52, 55])]}).json()['song']
    assert song['key'] == 'D' and song['key_candidates']


def test_key_003_manual_renames(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'meta': {'key_mode': 'manual', 'key': 'B'},
                                           'chords': [piano([42, 46, 49])]}).json()['song']
    assert song['chords'][0]['name'] == 'F#'
    song = save(api, auth, song, {'meta': {'key': 'Db'}}).json()['song']
    assert song['chords'][0]['name'] == 'Gb'


def test_key_004_auto_rejects_non_candidate(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'chords': [piano([48, 52, 55])]}).json()['song']
    error(db, lambda: save(api, auth, song, {'meta': {'key': 'D'}}), 422, 'validation_error')


def test_key_005_manual_to_auto_reset(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'meta': {'key_mode': 'manual', 'key': 'D'},
                                           'chords': [piano([48, 52, 55])]}).json()['song']
    response = save(api, auth, song, {'meta': {'key_mode': 'auto'}})
    assert response.json()['key_reset'] is True
    assert response.json()['song']['key'] == 'C'


def band_fixture(db, uid):
    now = datetime.now(timezone.utc)
    band = ObjectId()
    db.bands.insert_one({'_id': band, 'owner_id': uid, 'name': 'Faroles',
                         'created_at': now, 'updated_at': now})
    db.memberships.insert_one({'target_type': 'band', 'target_id': band, 'user_id': uid,
                               'role': None, 'invitation_id': None, 'joined_at': now})
    return band


def test_perm_017_band_membership_does_not_grant_personal_access(api, db, owner):
    auth, uid = owner
    song = create(api, auth)
    visitor = headers(register(api, 'bob'))
    bob = db.users.find_one({'username': 'bob'})['_id']
    band = band_fixture(db, uid)
    db.memberships.insert_one({'target_type': 'band', 'target_id': band, 'user_id': bob, 'role': None})
    error(db, lambda: api.get(f'/songs/{song["id"]}', headers=visitor), 404, 'not_found')


def test_perm_rule_workspace_listings(api, db, owner):
    auth, uid = owner
    own = create(api, auth)
    visitor = headers(register(api, 'bob'))
    bob = db.users.find_one({'username': 'bob'})['_id']
    shared = create(api, visitor)
    unrelated = create(api, visitor)
    db.memberships.insert_one({'target_type': 'song', 'target_id': ObjectId(shared['id']),
                               'user_id': uid, 'role': 'viewer'})
    band = band_fixture(db, uid)
    band_song = create(api, auth, owner_type='band', owner_id=str(band))
    assert api.get('/songs?workspace=personal', headers=auth).json()[0]['id'] == own['id']
    assert [s['id'] for s in api.get('/songs?workspace=shared', headers=auth).json()] == [shared['id']]
    all_songs = api.get('/songs?workspace=all', headers=auth).json()
    assert {s['id']: s['origin'] for s in all_songs} == {
        own['id']: 'own', shared['id']: 'shared', band_song['id']: 'band'}
    assert [s['updated_at'] for s in all_songs] == sorted([s['updated_at'] for s in all_songs], reverse=True)
    assert api.get(f'/songs?workspace=band&band_id={band}', headers=auth).json()[0]['id'] == band_song['id']
    error(db, lambda: api.get(f'/songs?workspace=band&band_id={band}', headers=visitor), 404, 'not_found')
    assert unrelated['id'] not in {s['id'] for s in all_songs}


def test_song_rule_physical_cascade_delete(api, db, owner, monkeypatch):
    destroyed = []
    monkeypatch.setattr(cloudinary.uploader, 'destroy', lambda public_id, **_: destroyed.append(public_id) or {'result': 'ok'})
    auth, uid = owner
    song = create(api, auth)
    sid, demo_id = ObjectId(song['id']), ObjectId()
    key = f'erato/songs/{sid}/{uid}/{demo_id}'
    demo = {'id': demo_id, 'title': 'Take 1', 'duration_s': 1.0, 'cloudinary_public_id': key,
            'format': 'ogg', 'mime_type': 'audio/ogg', 'size_bytes': 25, 'uploaded_by': uid,
            'uploaded_at': datetime.now(timezone.utc)}
    db.songs.update_one({'_id': sid}, {'$set': {'demos': [demo]}})
    db.demo_comments.insert_one({'song_id': sid, 'demo_id': str(demo_id), 'author_id': uid,
                                 'timestamp_s': 0.0, 'text': 'Start'})
    for collection in ('memberships', 'invitations'):
        db[collection].insert_one({'target_type': 'song', 'target_id': sid})
    public = api.patch(f'/songs/{sid}/visibility', headers=auth, json={'visibility': 'public'}).json()
    projection = api.get('/c/' + public['share_slug']).json()
    assert projection['demos'][0]['author'] == {'username': 'alice', 'display_name': 'Alice'}
    assert 'uploaded_by' not in str(projection) and 'cloudinary_public_id' not in str(projection)
    response = api.delete(f'/songs/{sid}', headers=auth)
    assert response.status_code == 204 and response.content == b''
    assert db.songs.count_documents({}) == 0
    for collection in ('revisions', 'demo_comments', 'memberships', 'invitations'):
        assert db[collection].count_documents({}) == 0
    assert destroyed == [key]
    error(db, lambda: api.get('/c/' + public['share_slug']), 404, 'not_found')


def test_chd_017_single_pitch_class_rejected(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    error(db, lambda: save(api, auth, song, {'chords': [piano([48, 60])]}), 422, 'validation_error')


def test_chd_rule_guitar_shape(api, db, owner):
    auth, _ = owner
    chord = {'instrument': 'guitar', 'notes': [48, 52, 55, 60, 64],
             'frets': [3, 2, 0, 1, 0], 'strings': [5, 4, 3, 2, 1]}
    song = save(api, auth, create(api, auth), {'chords': [chord]}).json()['song']
    assert song['chords'][0]['name'] == 'C'
    assert song['chords'][0]['frets'] == chord['frets']


def test_rev_rule_viewer_history_but_no_writes(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    visitor = headers(register(api, 'bob'))
    bob = db.users.find_one({'username': 'bob'})['_id']
    db.memberships.insert_one({'target_type': 'song', 'target_id': ObjectId(song['id']),
                               'user_id': bob, 'role': 'viewer'})
    path = f'/songs/{song["id"]}/revisions/meta'
    assert api.get(path, headers=visitor).status_code == 200
    row = api.get(path + '/1', headers=visitor).json()
    assert row['author'] == {'username': 'alice', 'display_name': 'Alice'}
    error(db, lambda: api.post(path + '/1/restore', headers=visitor, json={'base_version': 1}), 403, 'forbidden')
    error(db, lambda: api.post(f'/songs/{song["id"]}/chord-name', headers=visitor,
                               json=piano([48, 55])), 403, 'forbidden')
    db.memberships.delete_many({'user_id': bob})
    api.patch(f'/songs/{song["id"]}/visibility', headers=auth, json={'visibility': 'public'})
    error(db, lambda: api.get(path, headers=visitor), 404, 'not_found')
    error(db, lambda: api.get(path), 401, 'not_authenticated')


def test_perm_rule_visibility_hidden_in_meta_is_forbidden(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    visitor = headers(register(api, 'bob'))
    bob = db.users.find_one({'username': 'bob'})['_id']
    db.memberships.insert_one({'target_type': 'song', 'target_id': ObjectId(song['id']),
                               'user_id': bob, 'role': 'editor'})
    error(db, lambda: save(api, visitor, song, {'meta': {'visibility': 'public'}}), 403, 'forbidden')


def test_rev_rule_chord_dependency_conflict(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'chords': [piano([48, 55])]}).json()['song']
    chord_id = song['chords'][0]['id']
    lyrics = {'lines': [{'text': 'Song', 'chords': [{'col': 0, 'chord_id': chord_id}]}]}
    stale = song
    song = save(api, auth, song, {'lyrics': lyrics}).json()['song']
    # Deletion would modify lyrics, whose explicit save has a stale base.
    error(db, lambda: save(api, auth, stale, {'chords': [], 'lyrics': None}), 409, 'version_conflict')
    assert db.songs.find_one()['lyrics']['lines'][0]['chords'][0]['chord_id'] == ObjectId(chord_id)


def test_rev_rule_restore_chord_snapshot_with_original_ids(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'chords': [piano([48, 55])]}).json()['song']
    old = song['chords']
    song = save(api, auth, song, {'chords': []}).json()['song']
    path = f'/songs/{song["id"]}/revisions/chords/2/restore'
    response = api.post(path, headers=auth, json={'base_version': 3})
    assert response.status_code == 200, response.text
    assert response.json()['song']['chords'] == old
    assert response.json()['song']['section_versions']['chords'] == 4


def test_tab_rule_valid_bar_and_tuning(api, db, owner):
    auth, _ = owner
    tab = {'columns': [['|'] * 6], 'tuning': ['D#3', 'Eb3', 'C0', 'D3', 'A2', 'E2']}
    response = save(api, auth, create(api, auth), {'tabs': [tab]})
    assert response.status_code == 200
    assert response.json()['song']['tablatures'][0]['columns'] == [['|'] * 6]


def test_rev_rule_partial_save_holds_lyrics_depending_on_conflicted_chords(api, db, owner):
    auth, _ = owner
    stale = save(api, auth, create(api, auth), {'chords': [piano([48, 55])]}).json()['song']
    current = save(api, auth, stale, {'chords': []}).json()['song']
    lyrics = {'lines': [{'text': '', 'chords': [{'col': 0, 'chord_id': stale['chords'][0]['id']}]}]}
    response = save(api, auth, stale, {'chords': payload_chords(stale), 'lyrics': lyrics,
                                       'tasks': [{'title': 'Record bass', 'done': False}]})
    assert response.status_code == 200, response.text
    assert response.json()['conflicts'] == [
        {'section': 'lyrics', 'current_version': 1},
        {'section': 'chords', 'current_version': current['section_versions']['chords']}]
    assert response.json()['saved'] == [{'section': 'tasks', 'version': 2}]
    assert db.songs.find_one()['chords'] == [] and db.songs.find_one()['lyrics'] is None


def test_slug_rule_partial_unique_index(api, db, owner):
    from pymongo.errors import DuplicateKeyError
    auth, _ = owner
    first, second = create(api, auth), create(api, auth)
    assert first['share_slug'] is second['share_slug'] is None
    assert db.songs.count_documents({}) == 2
    slug = api.patch(f'/songs/{first["id"]}/visibility', headers=auth,
                      json={'visibility': 'public'}).json()['share_slug']
    before = snapshot(db)
    with pytest.raises(DuplicateKeyError):
        db.songs.update_one({'_id': ObjectId(second['id'])}, {'$set': {'share_slug': slug}})
    assert snapshot(db) == before
    assert db.revisions.index_information()['song_id_1_section_1_version_-1']['unique'] is True
    assert db.songs.index_information()['owner_type_1_owner_id_1_updated_at_-1']['key'] == [
        ('owner_type', 1), ('owner_id', 1), ('updated_at', -1)]


TAB = {'columns': [['|'] * 6], 'tuning': ['D#3', 'Eb3', 'C0', 'D3', 'A2', 'E2']}


def latest_summary(db, section):
    return db.revisions.find_one({'section': section}, sort=[('version', -1)])['summary']


def line(text, *chords):
    return {'text': text, 'chords': list(chords)}


def test_his_001_lyric_summary_names_the_section(api, db, owner):
    auth, _ = owner
    head = {'section': 'Coro', 'text': '', 'chords': []}
    song = save(api, auth, create(api, auth), {'lyrics': {'lines': [head, line('Hola')]}}).json()['song']
    save(api, auth, song, {'lyrics': {'lines': [head, line('Chao')]}})
    assert latest_summary(db, 'lyrics') == 'editó la letra de Coro'


def test_his_002_moved_chord_summary(api, db, owner):
    auth, _ = owner
    head = {'section': 'Coro', 'text': '', 'chords': []}
    song = save(api, auth, create(api, auth), {'chords': [piano([48, 52, 55])]}).json()['song']
    chord_id = song['chords'][0]['id']
    placed = {'lines': [head, line('Hola', {'col': 0, 'chord_id': chord_id})]}
    song = save(api, auth, song, {'lyrics': placed}).json()['song']
    moved = {'lines': [head, line('Hola', {'col': 3, 'chord_id': chord_id})]}
    save(api, auth, song, {'lyrics': moved})
    assert latest_summary(db, 'lyrics') == 'cambió los acordes de la letra de Coro'


def test_his_003_chord_summary_names_each_change(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'chords': [piano([48, 52, 55]), piano([50, 53, 57])]}).json()['song']
    removed = song['chords'][1]['name']
    kept = payload_chords(song)[0]
    response = save(api, auth, song, {'chords': [{**kept, 'notes': [48, 52, 55, 59]}, piano([53, 57, 60])]})
    assert response.status_code == 200, response.text
    changed, added = [chord['name'] for chord in response.json()['song']['chords']]
    assert latest_summary(db, 'chords') == (
        f'agregó el acorde {added}, quitó el acorde {removed}, cambió el acorde {changed}')


def test_his_004_tablature_summaries(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'tabs': [{**TAB, 'title': 'Intro'}]}).json()['song']
    assert latest_summary(db, 'tabs') == 'agregó la tablatura Intro'
    renamed = {**song['tablatures'][0], 'title': 'Riff'}
    response = save(api, auth, song, {'tabs': [renamed]})
    assert response.status_code == 200, response.text
    assert latest_summary(db, 'tabs') == 'cambió la tablatura Riff'
    song = save(api, auth, response.json()['song'], {'tabs': []}).json()['song']
    assert latest_summary(db, 'tabs') == 'quitó la tablatura Riff'
    save(api, auth, song, {'tabs': [TAB]})
    # The server names an untitled tablature, so `sin título` cannot reach a saved revision.
    assert latest_summary(db, 'tabs') == 'agregó la tablatura Tablatura 1'


def test_his_005_task_summaries(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'tasks': [{'title': 'Grabar', 'done': False}]}).json()['song']
    song = save(api, auth, song, {'tasks': [{**song['tasks'][0], 'done': True}]}).json()['song']
    assert latest_summary(db, 'tasks') == 'completó la tarea Grabar'
    save(api, auth, song, {'tasks': [{**song['tasks'][0], 'done': False}]})
    assert latest_summary(db, 'tasks') == 'reabrió la tarea Grabar'


def test_his_006_meta_summary_names_each_change(api, db, owner):
    auth, _ = owner
    # All five at once exceed the 120-character limit that HIS-010 pins.
    response = save(api, auth, create(api, auth), {'meta': {'title': 'Otra', 'status': 'ready', 'tempo': 92}})
    assert response.status_code == 200, response.text
    assert latest_summary(db, 'meta') == 'renombró la canción a Otra, cambió el estado a Lista, cambió el tempo a 92 bpm'
    response = save(api, auth, response.json()['song'], {'meta': {'time_signature': '3/4', 'key_mode': 'manual', 'key': 'D'}})
    assert response.status_code == 200, response.text
    assert latest_summary(db, 'meta') == 'cambió el compás a 3/4, cambió la tonalidad a D'


def test_his_007_cleared_meta_summary(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'meta': {'tempo': 92, 'time_signature': '3/4'}}).json()['song']
    save(api, auth, song, {'meta': {'tempo': None, 'time_signature': None}})
    assert latest_summary(db, 'meta') == 'quitó el tempo, quitó el compás'


def test_his_008_creation_summary(api, db, owner):
    auth, _ = owner
    create(api, auth)
    assert latest_summary(db, 'meta') == 'creó la composición'


def test_his_009_restore_summary(api, db, owner):
    auth, _ = owner
    song = save(api, auth, create(api, auth), {'lyrics': {'lines': [line('Uno')]}}).json()['song']
    song = save(api, auth, song, {'lyrics': {'lines': [line('Dos')]}}).json()['song']
    response = api.post(f'/songs/{song["id"]}/revisions/lyrics/2/restore', headers=auth,
                        json={'base_version': song['section_versions']['lyrics']})
    assert response.status_code == 200, response.text
    assert latest_summary(db, 'lyrics') == 'restauró la versión 2'


def test_his_010_long_summary_is_cut(api, db, owner):
    auth, _ = owner
    tasks = [{'title': f'Tarea numero {index}', 'done': False} for index in range(10)]
    save(api, auth, create(api, auth), {'tasks': tasks})
    summary = latest_summary(db, 'tasks')
    assert len(summary) == 120 and summary.endswith('…')


def test_his_011_unchanged_save_writes_no_revision(api, db, owner):
    auth, _ = owner
    lyrics = {'lines': [line('Hola')]}
    song = save(api, auth, create(api, auth), {'lyrics': lyrics}).json()['song']
    count = db.revisions.count_documents({})
    save(api, auth, song, {'lyrics': lyrics})
    assert db.revisions.count_documents({}) == count


def test_his_012_revision_without_summary_reads_null(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    db.revisions.update_many({}, {'$unset': {'summary': ''}})
    before = db.revisions.find_one()['content']
    row = api.get(f'/songs/{song["id"]}/revisions/meta', headers=auth).json()[0]
    assert row['summary'] is None
    assert row['content'] == before


def test_his_013_reader_gets_summary_and_no_internal_id(api, db, owner):
    auth, _ = owner
    song = create(api, auth)
    reader = headers(register(api, 'bob'))
    db.memberships.insert_one({'target_type': 'song', 'target_id': ObjectId(song['id']),
                               'user_id': db.users.find_one({'username': 'bob'})['_id'],
                               'role': 'viewer', 'invitation_id': None, 'joined_at': datetime.now(timezone.utc)})
    response = api.get(f'/songs/{song["id"]}/revisions/meta', headers=reader)
    assert response.status_code == 200, response.text
    assert response.json()[0]['summary'] == 'creó la composición'
    assert set(response.json()[0]) == {'section', 'version', 'created_at', 'content', 'summary', 'author'}

