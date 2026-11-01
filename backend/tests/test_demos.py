"""Approved cases of tests_md/propuesta-cloudinary-2026-10-31.md."""
from datetime import datetime, timezone
import time
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from bson import ObjectId
import cloudinary.api
import cloudinary.exceptions
import cloudinary.uploader
import cloudinary.utils
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError
import pytest

from app import demos
from app.main import create_app
from test_accounts import api, maestro, register, headers
from test_songs import create, error, owner

SECRET = 'test-secret'
MB = 1024 ** 2


class FakeCloudinary:
    """Network calls only: signatures and download URLs use the real SDK."""

    def __init__(self):
        self.assets, self.calls, self.fail_destroy = {}, [], set()

    def add(self, public_id, **fields):
        self.assets[public_id] = {'format': 'mp3', 'bytes': 2 * MB, 'duration': 61.5,
                                  'has_audio': True, 'audio_codec': 'mp3', **fields}

    def resource(self, public_id, **options):
        self.calls.append(('resource', public_id, options))
        if public_id not in self.assets:
            raise cloudinary.exceptions.NotFound(public_id)
        return self.assets[public_id]

    def destroy(self, public_id, **options):
        self.calls.append(('destroy', public_id, options))
        if public_id in self.fail_destroy:
            raise cloudinary.exceptions.GeneralError(public_id)
        return {'result': 'ok' if self.assets.pop(public_id, None) else 'not found'}


@pytest.fixture
def cloud(monkeypatch):
    fake = FakeCloudinary()
    monkeypatch.setattr(cloudinary.api, 'resource', fake.resource)
    monkeypatch.setattr(cloudinary.uploader, 'destroy', fake.destroy)
    return fake


def public_id_for(song, uid):
    return f'erato/songs/{song["id"]}/{uid}/{uuid4()}'


def confirm(api, auth, song, public_id, **extra):
    return api.post(f'/songs/{song["id"]}/demos', headers=auth, json={'public_id': public_id, **extra})


def uploaded(api, auth, uid, cloud, song, **fields):
    public_id = public_id_for(song, uid)
    cloud.add(public_id, **fields)
    response = confirm(api, auth, song, public_id)
    assert response.status_code == 201, response.text
    return public_id, response.json()


def member(api, db, song, role):
    auth = headers(register(api, role))
    uid = db.users.find_one({'username': role})['_id']
    db.memberships.insert_one({'target_type': 'song', 'target_id': ObjectId(song['id']), 'user_id': uid,
                               'role': role, 'created_at': datetime.now(timezone.utc)})
    return auth, uid


def stored(db, song):
    return db.songs.find_one({'_id': ObjectId(song['id'])})['demos']


def test_cld_001_upload_target(api, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    response = api.post(f'/songs/{song["id"]}/demos/upload-url', headers=auth)
    assert response.status_code == 200
    body = response.json()
    assert body['upload_url'] == 'https://api.cloudinary.com/v1_1/erato-test/video/upload'
    fields = body['fields']
    assert set(fields) == {'api_key', 'timestamp', 'signature', 'public_id', 'type', 'overwrite'}
    assert fields['type'] == 'authenticated' and fields['overwrite'] == 'false'
    assert fields['public_id'].startswith(f'erato/songs/{song["id"]}/{uid}/')
    assert SECRET not in response.text


def test_cld_002_signature_recomputes(api, owner, cloud):
    auth, _ = owner
    song = create(api, auth)
    fields = api.post(f'/songs/{song["id"]}/demos/upload-url', headers=auth).json()['fields']
    signed = {name: fields[name] for name in ('overwrite', 'public_id', 'timestamp', 'type')}
    assert cloudinary.utils.api_sign_request(signed, SECRET) == fields['signature']


def test_cld_003_viewer_cannot_request_upload(api, db, owner, cloud):
    auth, _ = owner
    song = create(api, auth)
    viewer, _ = member(api, db, song, 'viewer')
    error(db, lambda: api.post(f'/songs/{song["id"]}/demos/upload-url', headers=viewer), 403, 'forbidden')


def test_cld_004_confirm_reads_the_server_values(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    public_id = public_id_for(song, uid)
    cloud.add(public_id)
    response = confirm(api, auth, song, public_id, duration_s=1, size_bytes=1, title='Take')
    assert response.status_code == 201, response.text
    demo = stored(db, song)[0]
    assert demo['cloudinary_public_id'] == public_id and demo['format'] == 'mp3'
    assert demo['mime_type'] == 'audio/mpeg' and demo['size_bytes'] == 2 * MB
    assert demo['duration_s'] == 61.5 and demo['title'] == 'Take'
    assert 'r2_key' not in demo
    assert cloud.calls[0][2]['resource_type'] == 'video'
    assert cloud.calls[0][2]['type'] == 'authenticated'
    assert public_id in cloud.assets


def test_cld_005_foreign_public_id(api, db, owner, cloud):
    auth, uid = owner
    song, other_song = create(api, auth), create(api, auth)
    foreign = [public_id_for(song, ObjectId()), public_id_for(other_song, uid)]
    for public_id in foreign:
        cloud.add(public_id)
        error(db, lambda: confirm(api, auth, song, public_id), 404, 'not_found')
        assert public_id in cloud.assets
    assert cloud.calls == []


def test_cld_006_missing_asset(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    error(db, lambda: confirm(api, auth, song, public_id_for(song, uid)), 404, 'not_found')


def test_cld_012_duplicate_confirmation_preserves_asset(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    public_id, demo = uploaded(api, auth, uid, cloud, song)
    cloud.calls.clear()
    error(db, lambda: confirm(api, auth, song, public_id), 404, 'not_found')
    assert [row['id'] for row in stored(db, song)] == [ObjectId(demo['id'])]
    assert public_id in cloud.assets
    assert cloud.calls == []


def test_cld_013_invalid_uuid_never_calls_cloudinary(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    public_id = f'erato/songs/{song["id"]}/{uid}/../{uuid4()}'
    cloud.add(public_id)
    error(db, lambda: confirm(api, auth, song, public_id), 404, 'not_found')
    assert cloud.calls == []
    assert public_id in cloud.assets
    assert stored(db, song) == []


def test_cld_014_confirm_accepts_admin_audio_metadata(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    public_id = public_id_for(song, uid)
    cloud.add(public_id, format='wav', bytes=64044, duration=2.0,
              has_audio=True, audio_codec='pcm_s16le', audio_duration=2.0)
    assert 'audio' not in cloud.assets[public_id]
    response = confirm(api, auth, song, public_id, size_bytes=1, duration_s=1)
    assert response.status_code == 201, response.text
    demo = stored(db, song)[0]
    assert len(stored(db, song)) == 1
    assert str(demo['id']) == response.json()['id']
    assert demo['cloudinary_public_id'] == public_id
    assert demo['format'] == 'wav' and demo['mime_type'] == 'audio/wav'
    assert demo['size_bytes'] == 64044 and demo['duration_s'] == 2.0
    assert public_id in cloud.assets
    assert [call[0] for call in cloud.calls] == ['resource']


@pytest.mark.parametrize('fields', [
    {'has_audio': False}, {'has_audio': None},  # CLD-007 (false or missing)
    {'bytes': 100 * MB + 1}, {'duration': 20 * 60 + 1},  # CLD-008
    {'format': 'avi'},  # CLD-009
], ids=['no-audio', 'missing-audio-flag', 'too-big', 'too-long', 'format'])
def test_cld_007_to_009_rejected_asset(api, db, owner, cloud, fields):
    auth, uid = owner
    song = create(api, auth)
    public_id = public_id_for(song, uid)
    cloud.add(public_id, **fields)
    if fields.get('has_audio', True) is None:
        cloud.assets[public_id].pop('has_audio')
    error(db, lambda: confirm(api, auth, song, public_id), 422, 'validation_error')
    assert public_id not in cloud.assets


def test_cld_010_quota_counts_the_band(api, db, owner, cloud):
    auth, uid = owner
    band = ObjectId()
    guest = headers(register(api, 'bob'))
    guest_id = db.users.find_one({'username': 'bob'})['_id']
    now = datetime.now(timezone.utc)
    db.bands.insert_one({'_id': band, 'name': 'Band', 'owner_id': uid, 'created_at': now, 'updated_at': now})
    db.memberships.insert_one({'target_type': 'band', 'target_id': band, 'user_id': guest_id, 'created_at': now})
    song = create(api, auth)
    db.songs.update_one({'_id': ObjectId(song['id'])}, {'$set': {
        'owner_type': 'band', 'owner_id': band,
        'demos': [{'id': ObjectId(), 'cloudinary_public_id': 'other', 'size_bytes': 2 * 1024 ** 3}]}})
    public_id = public_id_for(song, guest_id)
    cloud.add(public_id)
    error(db, lambda: confirm(api, guest, song, public_id), 422, 'quota_exceeded')
    assert public_id not in cloud.assets


def test_cld_011_mongo_failure_leaves_no_orphan(api, db, owner, cloud, monkeypatch):
    auth, uid = owner
    song = create(api, auth)
    public_id = public_id_for(song, uid)
    cloud.add(public_id)

    def failing(*_):
        raise PyMongoError('down')

    monkeypatch.setattr(demos, 'transact', failing)
    with pytest.raises(PyMongoError):
        confirm(api, auth, song, public_id)
    assert public_id not in cloud.assets and stored(db, song) == []


def assert_playback(body, public_id):
    url = urlsplit(body['url'])
    query = {name: values[0] for name, values in parse_qs(url.query).items()}
    assert url.path == '/v1_1/erato-test/video/download'
    assert query['public_id'] == public_id and query['format'] == 'mp3' and query['type'] == 'authenticated'
    assert abs(int(query['expires_at']) - time.time() - 900) < 5
    assert body['expires_in'] == 900


def test_cld_020_member_playback(api, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    public_id, demo = uploaded(api, auth, uid, cloud, song)
    response = api.get(f'/songs/{song["id"]}/demos/{demo["id"]}/url', headers=auth)
    assert response.status_code == 200
    assert_playback(response.json(), public_id)


def test_cld_021_022_public_playback(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    public_id, demo = uploaded(api, auth, uid, cloud, song)
    slug = api.patch(f'/songs/{song["id"]}/visibility', headers=auth, json={'visibility': 'public'}).json()['share_slug']
    response = api.get(f'/c/{slug}/demos/{demo["id"]}/url')
    assert response.status_code == 200 and 'cloudinary_public_id' not in response.json()
    assert_playback(response.json(), public_id)
    api.patch(f'/songs/{song["id"]}/visibility', headers=auth, json={'visibility': 'private'})
    error(db, lambda: api.get(f'/c/{slug}/demos/{demo["id"]}/url'), 404, 'not_found')


def test_cld_023_responses_hide_storage_fields(api, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    _, demo = uploaded(api, auth, uid, cloud, song)
    slug = api.patch(f'/songs/{song["id"]}/visibility', headers=auth, json={'visibility': 'public'}).json()['share_slug']
    bodies = [demo, api.get(f'/songs/{song["id"]}', headers=auth).json()['demos'][0],
              api.get(f'/songs', headers=auth).json()[0]['demos'][0], api.get(f'/c/{slug}').json()['demos'][0],
              api.patch(f'/songs/{song["id"]}/demos/{demo["id"]}', headers=auth, json={'title': 'New'}).json()]
    for body in bodies:
        assert not {'cloudinary_public_id', 'format'} & set(body)


def test_cld_030_delete_demo_before_mongo(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    public_id, demo = uploaded(api, auth, uid, cloud, song)
    api.post(f'/songs/{song["id"]}/demos/{demo["id"]}/comments', headers=auth, json={'timestamp_s': 1, 'text': 'Hi'})
    response = api.delete(f'/songs/{song["id"]}/demos/{demo["id"]}', headers=auth)
    assert response.status_code == 204
    assert public_id not in cloud.assets and stored(db, song) == []
    assert db.demo_comments.count_documents({}) == 0
    assert cloud.calls[-1][2]['resource_type'] == 'video' and cloud.calls[-1][2]['type'] == 'authenticated'


def test_cld_031_delete_demo_failure(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    public_id, demo = uploaded(api, auth, uid, cloud, song)
    api.post(f'/songs/{song["id"]}/demos/{demo["id"]}/comments', headers=auth, json={'timestamp_s': 1, 'text': 'Hi'})
    cloud.fail_destroy.add(public_id)
    error(db, lambda: api.delete(f'/songs/{song["id"]}/demos/{demo["id"]}', headers=auth), 503, 'storage_unavailable')
    assert public_id in cloud.assets


def test_cld_032_delete_song_destroys_every_asset(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    first, _ = uploaded(api, auth, uid, cloud, song)
    second, _ = uploaded(api, auth, uid, cloud, song)
    assert api.delete(f'/songs/{song["id"]}', headers=auth).status_code == 204
    assert cloud.assets == {} and db.songs.count_documents({}) == 0
    assert [call[1] for call in cloud.calls if call[0] == 'destroy'] == [first, second]


def test_cld_033_delete_song_partial_failure(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    uploaded(api, auth, uid, cloud, song)
    second, _ = uploaded(api, auth, uid, cloud, song)
    cloud.fail_destroy.add(second)
    error(db, lambda: api.delete(f'/songs/{song["id"]}', headers=auth), 503, 'storage_unavailable')


def test_cld_034_missing_asset_counts_as_deleted(api, db, owner, cloud):
    auth, uid = owner
    song = create(api, auth)
    public_id, demo = uploaded(api, auth, uid, cloud, song)
    del cloud.assets[public_id]
    assert api.delete(f'/songs/{song["id"]}/demos/{demo["id"]}', headers=auth).status_code == 204
    assert stored(db, song) == []


def test_cld_040_041_no_credentials(db, maestro, monkeypatch):
    monkeypatch.delenv('CLOUDINARY_URL')
    with TestClient(create_app(maestro_timeout=0.2)) as api:
        assert api.get('/health').status_code == 200
        auth = headers(register(api))
        song = create(api, auth)
        error(db, lambda: api.post(f'/songs/{song["id"]}/demos/upload-url', headers=auth), 503, 'storage_unavailable')
        demo = {'id': ObjectId(), 'title': 'Take', 'duration_s': 1.0, 'cloudinary_public_id': 'x',
                'format': 'mp3', 'mime_type': 'audio/mpeg', 'size_bytes': 1}
        db.songs.update_one({'_id': ObjectId(song['id'])}, {'$set': {'demos': [demo]}})
        error(db, lambda: api.get(f'/songs/{song["id"]}/demos/{demo["id"]}/url', headers=auth), 503, 'storage_unavailable')
