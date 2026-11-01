"""Approved INV/PERM area rules (decisions 06, 11, 14); no guessed ID mappings."""
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

from bson import ObjectId
import pytest

from test_accounts import api, maestro, register, headers
from test_songs import create, error, snapshot


@pytest.fixture
def people(api, db):
    result = {}
    for name in ('alice', 'bob', 'carol', 'dave'):
        auth = headers(register(api, name))
        result[name] = (auth, db.users.find_one({'username': name})['_id'])
    return result


def band(api, auth):
    response = api.post('/bands', headers=auth, json={'name': 'Faroles'})
    assert response.status_code == 201, response.text
    return response.json()


def link(api, auth, kind, target, role=None):
    response = api.post('/invitations', headers=auth, json={
        'target_type': kind, 'target_id': target, 'role': role,
    })
    assert response.status_code == 201, response.text
    return response.json()


def use(api, auth, invitation):
    return api.post(f'/invitations/{invitation["token"]}/use', headers=auth)


def join(api, owner, member, target):
    invitation = link(api, owner, 'band', target['id'])
    response = use(api, member, invitation)
    assert response.status_code == 201, response.text
    return invitation


def test_inv_rule_multiuse_membership_and_single_reveal(api, db, people):
    alice, bob, carol = [people[n][0] for n in ('alice', 'bob', 'carol')]
    target = band(api, alice)
    invitation = link(api, alice, 'band', target['id'])
    stored = db.invitations.find_one()
    assert stored['token_hash'] != invitation['token'] and 'token' not in stored
    assert invitation['url'] == '/i/' + invitation['token']
    assert (stored['expires_at'] - stored['created_at']).total_seconds() == api.app.state.config['INVITATION_TTL']
    assert use(api, bob, invitation).status_code == 201
    assert use(api, carol, invitation).status_code == 201
    error(db, lambda: use(api, bob, invitation), 409, 'already_member')
    error(db, lambda: use(api, alice, invitation), 409, 'already_member')
    assert api.get('/bands', headers=bob).json()[0]['id'] == target['id']
    assert api.get('/bands', headers=alice).json()[0]['id'] == target['id']
    metadata = api.get('/invitations', headers=alice, params={'target_type': 'band', 'target_id': target['id']}).json()
    assert 'token' not in metadata[0] and 'token_hash' not in metadata[0]
    members = api.get(f'/bands/{target["id"]}/members', headers=bob).json()
    assert all(set(m) == {'username', 'display_name', 'role'} for m in members)
    assert {m['username'] for m in members} == {'alice', 'bob', 'carol'}
    assert api.delete(f'/invitations/{invitation["id"]}', headers=alice).status_code == 204
    assert api.get(f'/bands/{target["id"]}', headers=bob).status_code == 200
    error(db, lambda: use(api, carol, invitation), 404, 'not_found')


@pytest.mark.parametrize('kind,role', [('song', None), ('song', 'admin'), ('band', 'editor'), ('other', None)])
def test_inv_rule_role_validation(api, db, people, kind, role):
    auth = people['alice'][0]
    target = band(api, auth)
    error(db, lambda: api.post('/invitations', headers=auth, json={
        'target_type': kind, 'target_id': target['id'], 'role': role,
    }), 422, 'validation_error')


@pytest.mark.parametrize('field', ['created_by', 'token_hash', 'expires_at', 'created_at'])
def test_inv_rule_server_fields_rejected(api, db, people, field):
    auth = people['alice'][0]
    target = band(api, auth)
    error(db, lambda: api.post('/invitations', headers=auth, json={
        'target_type': 'band', 'target_id': target['id'], field: 'injected',
    }), 422, 'validation_error')


def test_inv_rule_expiry_auth_and_deleted_target(api, db, people):
    auth, bob = people['alice'][0], people['bob'][0]
    song = create(api, auth)
    invitation = link(api, auth, 'song', song['id'], 'viewer')
    error(db, lambda: api.post(f'/invitations/{invitation["token"]}/use'), 401, 'not_authenticated')
    now = api.app.state.clock()
    db.invitations.update_one({}, {'$set': {'expires_at': now}})
    api.app.state.clock = lambda: now
    error(db, lambda: use(api, bob, invitation), 404, 'not_found')
    db.invitations.update_one({}, {'$set': {'expires_at': now + timedelta(days=1)}})
    db.songs.delete_one({'_id': ObjectId(song['id'])})
    error(db, lambda: use(api, bob, invitation), 404, 'not_found')
    error(db, lambda: api.post('/invitations/missing/use', headers=bob), 404, 'not_found')


@pytest.mark.parametrize('role', ['viewer', 'editor'])
def test_inv_rule_song_access_and_editor_permissions(api, db, people, role):
    alice, bob, carol = [people[n][0] for n in ('alice', 'bob', 'carol')]
    song = create(api, alice)
    invitation = link(api, alice, 'song', song['id'], role)
    assert use(api, bob, invitation).status_code == 201
    # The second link is created before the rejected request's snapshot.
    second = link(api, alice, 'song', song['id'], 'editor')
    error(db, lambda: use(api, bob, second), 409, 'already_member')
    assert db.memberships.find_one({'user_id': people['bob'][1]})['role'] == role
    if role == 'viewer':
        error(db, lambda: link_request(api, bob, song['id']), 403, 'forbidden')
    else:
        owned = link(api, bob, 'song', song['id'], 'viewer')
        error(db, lambda: api.delete(f'/invitations/{owned["id"]}', headers=carol), 404, 'not_found')
        error(db, lambda: api.delete(f'/invitations/{invitation["id"]}', headers=bob), 403, 'forbidden')
    error(db, lambda: link_request(api, carol, song['id']), 404, 'not_found')
    error(db, lambda: api.delete(f'/songs/{song["id"]}/members/bob', headers=bob), 403, 'forbidden')


def link_request(api, auth, song_id):
    return api.post('/invitations', headers=auth, json={
        'target_type': 'song', 'target_id': song_id, 'role': 'editor',
    })


@pytest.mark.parametrize('mode', ['remove', 'leave', 'demote'])
def test_inv_rule_song_editor_loss_cascades_only_own_links(api, db, people, mode):
    alice, bob, carol = [people[n][0] for n in ('alice', 'bob', 'carol')]
    song = create(api, alice)
    entry = link(api, alice, 'song', song['id'], 'editor')
    assert use(api, bob, entry).status_code == 201
    own_links = [link(api, bob, 'song', song['id'], role) for role in ('editor', 'viewer')]
    assert use(api, carol, own_links[1]).status_code == 201
    other_song = create(api, bob)
    other = link(api, bob, 'song', other_song['id'], 'editor')
    path = f'/songs/{song["id"]}/members'
    if mode == 'remove':
        response = api.delete(path + '/bob', headers=alice)
    elif mode == 'leave':
        response = api.delete(path + '/me', headers=bob)
    else:
        response = api.patch(path + '/bob', headers=alice, json={'role': 'viewer'})
    assert response.status_code == (200 if mode == 'demote' else 204)
    assert not db.invitations.count_documents({'_id': {'$in': [ObjectId(x['id']) for x in own_links]}})
    assert db.invitations.find_one({'_id': ObjectId(entry['id'])})
    assert db.invitations.find_one({'_id': ObjectId(other['id'])})
    assert api.get(f'/songs/{song["id"]}', headers=carol).status_code == 200
    if mode == 'demote':
        assert db.memberships.find_one({'user_id': people['bob'][1]})['role'] == 'viewer'
        for role in ('editor', 'viewer'):
            assert api.patch(path + '/bob', headers=alice, json={'role': role}).status_code == 200
            if role == 'editor':
                renewed = link(api, bob, 'song', song['id'], 'editor')
        assert not db.invitations.find_one({'_id': ObjectId(renewed['id'])})
    else:
        error(db, lambda: api.get(f'/songs/{song["id"]}', headers=bob), 404, 'not_found')
        assert use(api, bob, entry).status_code == 201


@pytest.mark.parametrize('mode', ['remove', 'leave'])
def test_inv_rule_band_loss_cascade_and_direct_song_access(api, db, people, mode):
    alice, bob, carol = [people[n][0] for n in ('alice', 'bob', 'carol')]
    target = band(api, alice)
    join(api, alice, bob, target)
    song = create(api, alice, owner_type='band', owner_id=target['id'])
    band_link = link(api, bob, 'band', target['id'])
    song_link = link(api, bob, 'song', song['id'], 'editor')
    assert use(api, carol, song_link).status_code == 201
    error(db, lambda: api.get(f'/bands/{target["id"]}', headers=carol), 404, 'not_found')
    error(db, lambda: api.delete(f'/bands/{target["id"]}/members/alice', headers=bob), 403, 'forbidden')
    if mode == 'remove':
        response = api.delete(f'/bands/{target["id"]}/members/bob', headers=alice)
    else:
        response = api.delete(f'/bands/{target["id"]}/members/me', headers=bob)
    assert response.status_code == 204
    for inv in (band_link, song_link):
        assert db.invitations.find_one({'_id': ObjectId(inv['id'])}) is None
    assert api.get(f'/songs/{song["id"]}', headers=carol).status_code == 200
    assert api.get('/bands', headers=bob).json() == []
    error(db, lambda: api.get(f'/songs/{song["id"]}', headers=bob), 404, 'not_found')


def test_inv_rule_transfer_and_owner_leave(api, db, people):
    alice, bob, carol = [people[n][0] for n in ('alice', 'bob', 'carol')]
    target = band(api, alice)
    invitation = join(api, alice, bob, target)
    path = f'/bands/{target["id"]}'
    error(db, lambda: api.delete(path + '/members/me', headers=alice), 409, 'owner_must_transfer')
    for actor, user, status in [(bob, 'bob', 403), (alice, 'alice', 422), (alice, 'carol', 422)]:
        error(db, lambda: api.post(path + '/transfer', headers=actor, json={'username': user}),
              status, 'forbidden' if status == 403 else 'validation_error')
    response = api.post(path + '/transfer', headers=alice, json={'username': 'bob'})
    assert response.status_code == 200
    assert db.bands.find_one()['owner_id'] == people['bob'][1]
    assert db.memberships.find_one({'user_id': people['bob'][1]}) is None
    membership = db.memberships.find_one({'user_id': people['alice'][1]})
    assert membership['role'] is membership['invitation_id'] is None
    assert db.invitations.find_one({'_id': ObjectId(invitation['id'])})
    error(db, lambda: api.delete(path + '/members/bob', headers=alice), 403, 'forbidden')
    assert api.delete(path + '/members/me', headers=alice).status_code == 204


@pytest.mark.parametrize('kind', ['song', 'band'])
def test_inv_rule_concurrent_use(api, db, people, kind):
    alice, bob, carol = [people[n][0] for n in ('alice', 'bob', 'carol')]
    target = create(api, alice) if kind == 'song' else band(api, alice)
    invitation = link(api, alice, kind, target['id'], 'editor' if kind == 'song' else None)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: use(api, bob, invitation), range(2)))
    assert sorted(r.status_code for r in responses) == [201, 409]
    assert db.memberships.count_documents({'user_id': people['bob'][1]}) == 1
    another = link(api, alice, kind, target['id'], 'viewer' if kind == 'song' else None)
    # A separate pair of users can use the same link successfully.
    dave = people['dave'][0]
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert [r.status_code for r in pool.map(lambda auth: use(api, auth, another), (carol, dave))] == [201, 201]


def test_perm_rule_move_preserves_content_and_cleans_redundant_memberships(api, db, people):
    alice, bob, carol = [people[n][0] for n in ('alice', 'bob', 'carol')]
    target = band(api, alice)
    join(api, alice, bob, target)
    song = create(api, alice)
    invitation = link(api, alice, 'song', song['id'], 'viewer')
    assert use(api, bob, invitation).status_code == 201
    assert use(api, carol, invitation).status_code == 201
    before = db.songs.find_one()
    response = api.post(f'/songs/{song["id"]}/move', headers=alice, json={'band_id': target['id']})
    assert response.status_code == 200, response.text
    after = db.songs.find_one()
    assert after == {**before, 'owner_type': 'band', 'owner_id': ObjectId(target['id']), 'updated_at': after['updated_at']}
    assert not db.memberships.find_one({'target_type': 'song', 'user_id': people['bob'][1]})
    assert db.memberships.find_one({'target_type': 'song', 'user_id': people['carol'][1]})['role'] == 'viewer'
    assert db.invitations.find_one({'_id': ObjectId(invitation['id'])})
    error(db, lambda: api.post(f'/songs/{song["id"]}/move', headers=alice, json={'band_id': target['id']}),
          422, 'validation_error')


def transaction_failure(api, db, people, monkeypatch, operation):
    from pymongo.collection import Collection
    alice, bob = people['alice'][0], people['bob'][0]
    target = band(api, alice)
    join(api, alice, bob, target)
    link(api, bob, 'band', target['id'])
    before = snapshot(db)
    original = Collection.delete_many if operation == 'cascade' else Collection.insert_one

    def fail(self, *args, **kwargs):
        if self.name == ('invitations' if operation == 'cascade' else 'memberships'):
            raise RuntimeError('Injected transaction failure')
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Collection, 'delete_many' if operation == 'cascade' else 'insert_one', fail)
    with pytest.raises(RuntimeError, match='Injected transaction failure'):
        if operation == 'cascade':
            api.delete(f'/bands/{target["id"]}/members/bob', headers=alice)
        else:
            api.post(f'/bands/{target["id"]}/transfer', headers=alice, json={'username': 'bob'})
    assert snapshot(db) == before


def test_inv_122_cascade_transaction_aborts(api, db, people, monkeypatch):
    transaction_failure(api, db, people, monkeypatch, 'cascade')


def test_inv_129_transfer_transaction_aborts(api, db, people, monkeypatch):
    transaction_failure(api, db, people, monkeypatch, 'transfer')


@pytest.mark.parametrize('value', ['nonnumeric', '0d', '-1d', '0', ''])
def test_inv_060_invalid_ttl_refuses_startup(db, monkeypatch, value):
    from app.main import create_app
    before = snapshot(db)
    monkeypatch.setenv('INVITATION_TTL', value)
    with pytest.raises(ValueError, match='INVITATION_TTL'):
        create_app()
    assert snapshot(db) == before


def test_inv_rule_indexes_and_duplicate_integrity(db):
    from app.database import create_indexes
    from pymongo.errors import DuplicateKeyError
    create_indexes(db)
    assert db.invitations.index_information()['expires_at_1']['expireAfterSeconds'] == 0
    assert db.invitations.index_information()['token_hash_1']['unique']
    assert db.memberships.index_information()['target_type_1_target_id_1_user_id_1']['unique']
    assert 'owner_id_1' in db.bands.index_information()
    for collection, row in [(db.invitations, {'token_hash': 'same'}),
                            (db.memberships, {'target_type': 'band', 'target_id': ObjectId(), 'user_id': ObjectId()})]:
        collection.insert_one(dict(row))
        before = snapshot(db)
        with pytest.raises(DuplicateKeyError):
            collection.insert_one(dict(row))
        assert snapshot(db) == before


def test_inv_rule_band_access_without_membership_is_not_granted(api, db, people):
    alice, bob = people['alice'][0], people['bob'][0]
    target = band(api, alice)
    invitation = link(api, alice, 'band', target['id'])
    assert api.get('/bands', headers=bob).json() == []
    error(db, lambda: api.get(f'/bands/{target["id"]}', headers=bob), 404, 'not_found')
    error(db, lambda: api.get(f'/bands/{target["id"]}/members', headers=bob), 404, 'not_found')
    error(db, lambda: api.post('/invitations', headers=bob, json={
        'target_type': 'band', 'target_id': target['id'],
    }), 404, 'not_found')
    error(db, lambda: api.get('/bands'), 401, 'not_authenticated')
    error(db, lambda: api.post('/bands', json={'name': 'Unauthorized'}), 401, 'not_authenticated')
    assert use(api, bob, invitation).status_code == 201
    # Members can create band links with precisely the owner's effect.
    member_link = link(api, bob, 'band', target['id'])
    assert use(api, people['carol'][0], member_link).status_code == 201
    assert api.delete(f'/bands/{target["id"]}/members/bob', headers=alice).status_code == 204
    assert use(api, bob, invitation).status_code == 201
    error(db, lambda: api.delete(f'/bands/{target["id"]}/members/alice', headers=alice), 404, 'not_found')
    error(db, lambda: api.delete(f'/bands/{target["id"]}/members/missing', headers=alice), 404, 'not_found')


@pytest.mark.parametrize('role', ['editor', 'viewer'])
def test_perm_rule_band_access_subsumes_song_links(api, db, people, role):
    alice, bob, carol = [people[n][0] for n in ('alice', 'bob', 'carol')]
    target = band(api, alice)
    join(api, alice, bob, target)
    song = create(api, bob, owner_type='band', owner_id=target['id'])
    invitation = link(api, alice, 'song', song['id'], role)
    error(db, lambda: use(api, bob, invitation), 409, 'already_member')
    error(db, lambda: use(api, alice, invitation), 409, 'already_member')
    assert db.memberships.count_documents({'target_type': 'song'}) == 0
    assert use(api, carol, invitation).status_code == 201
    error(db, lambda: api.post('/invitations', headers=carol, json={
        'target_type': 'band', 'target_id': target['id'],
    }), 404, 'not_found')
    error(db, lambda: api.patch(f'/songs/{song["id"]}/members/carol', headers=bob, json={'role': 'editor'}),
          403, 'forbidden')
    error(db, lambda: api.patch(f'/songs/{song["id"]}/members/carol', headers=alice, json={'role': 'admin'}),
          422, 'validation_error')
    error(db, lambda: api.delete(f'/songs/{song["id"]}/members/carol', headers=bob), 403, 'forbidden')
    error(db, lambda: api.delete(f'/songs/{song["id"]}', headers=bob), 403, 'forbidden')
    assert api.delete(f'/songs/{song["id"]}/members/carol', headers=alice).status_code == 204
    error(db, lambda: api.get(f'/songs/{song["id"]}', headers=carol), 404, 'not_found')


def test_inv_rule_band_removal_preserves_explicit_song_membership(api, db, people):
    alice, bob = people['alice'][0], people['bob'][0]
    target = band(api, alice)
    song = create(api, alice, owner_type='band', owner_id=target['id'])
    invitation = link(api, alice, 'song', song['id'], 'viewer')
    assert use(api, bob, invitation).status_code == 201
    join(api, alice, bob, target)
    assert api.delete(f'/bands/{target["id"]}/members/bob', headers=alice).status_code == 204
    assert api.get(f'/songs/{song["id"]}', headers=bob).status_code == 200
    assert db.memberships.find_one({'target_type': 'song'})['role'] == 'viewer'
    error(db, lambda: api.get(f'/bands/{target["id"]}', headers=bob), 404, 'not_found')


@pytest.mark.parametrize('failure', ['nonowner', 'not_band_member', 'quota'])
def test_perm_rule_move_errors_change_nothing(api, db, people, failure):
    alice, bob = people['alice'][0], people['bob'][0]
    target = band(api, alice if failure != 'not_band_member' else bob)
    song = create(api, alice)
    actor = alice
    if failure == 'nonowner':
        invitation = link(api, alice, 'song', song['id'], 'editor')
        assert use(api, bob, invitation).status_code == 201
        actor = bob
    if failure == 'quota':
        existing = create(api, alice, owner_type='band', owner_id=target['id'])
        # Approved embedded demo metadata; no object writes are needed to test sums.
        demo = {'id': ObjectId(), 'title': 'Take', 'duration_s': 1.0,
                'cloudinary_public_id': 'erato/songs/test/demo', 'format': 'ogg', 'mime_type': 'audio/ogg',
                'size_bytes': 2 * 1024 ** 3, 'uploaded_by': people['alice'][1],
                'uploaded_at': api.app.state.clock()}
        db.songs.update_one({'_id': ObjectId(existing['id'])}, {'$set': {'demos': [demo]}})
        db.songs.update_one({'_id': ObjectId(song['id'])}, {'$set': {'demos': [{**demo, 'size_bytes': 1}]}})
    status, code = {'nonowner': (403, 'forbidden'), 'not_band_member': (404, 'not_found'),
                    'quota': (422, 'quota_exceeded')}[failure]
    error(db, lambda: api.post(f'/songs/{song["id"]}/move', headers=actor, json={'band_id': target['id']}), status, code)


def test_inv_rule_removal_races_use_without_surviving_creator_links(api, db, people):
    alice, bob, carol = [people[n][0] for n in ('alice', 'bob', 'carol')]
    song = create(api, alice)
    entry = link(api, alice, 'song', song['id'], 'editor')
    assert use(api, bob, entry).status_code == 201
    invitation = link(api, bob, 'song', song['id'], 'viewer')
    with ThreadPoolExecutor(max_workers=2) as pool:
        removing = pool.submit(api.delete, f'/songs/{song["id"]}/members/bob', headers=alice)
        joining = pool.submit(use, api, carol, invitation)
        assert removing.result().status_code == 204
        response = joining.result()
    assert response.status_code in (201, 404)
    assert db.invitations.count_documents({'created_by': people['bob'][1]}) == 0
    assert bool(db.memberships.find_one({'user_id': people['carol'][1]})) == (response.status_code == 201)
    error(db, lambda: use(api, people['dave'][0], invitation), 404, 'not_found')
