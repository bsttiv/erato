"""Approved MIG cases of tests_md/migracion.md, with their Cloudinary and demo ID revisions."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from uuid import uuid4

from argon2 import PasswordHasher
from bson import ObjectId
import cloudinary.api
import pytest

import migrate
from app.detection import analyze, name_chord
from migrate import MigrationStopped, run, username_base
from test_accounts import api, maestro, headers
from test_demos import cloud

CONFIG = {'CLOUDINARY_URL': 'cloudinary://key:secret@erato-test'}
DAY = datetime(2026, 1, 1, tzinfo=timezone.utc)
NOW = datetime(2026, 10, 31, tzinfo=timezone.utc)
TARGETS = ('users', 'songs', 'memberships', 'revisions', 'demo_comments')


@pytest.fixture
def old(db):
    name = f'erato_old_{uuid4().hex}'
    database = db.client[name]
    yield database
    db.client.drop_database(name)


def user(old, name='Alice', **fields):
    doc = {'_id': ObjectId(), 'email': f'{uuid4().hex}@example.com', 'password_hash': 'hash',
           'display_name': name, 'token_version': 3, 'created_at': DAY, **fields}
    old.users.insert_one(doc)
    return doc


def composition(old, owner, **fields):
    doc = {'_id': ObjectId(), 'owner_id': owner['_id'], 'band_id': None, 'band_editable': False,
           'title': 'Under the lamp', 'visibility': 'private', 'share_slug': None, 'key': 'C',
           'bpm': 90, 'time_signature': '4/4', 'style_tags': ['jazz'], 'status': 'ready',
           'sections_enabled': {'chords': True}, 'section_revs': {'lyrics': 2}, 'members': [],
           'chords': None, 'tablature': None, 'lyrics': None, 'todos': [], 'demos': [],
           'created_at': DAY, 'updated_at': DAY + timedelta(days=1), **fields}
    old.compositions.insert_one(doc)
    return doc


def old_demo(public_id='legacy/demo-01', demo_id='take-01', uploader=None):
    return {'demo_id': demo_id, 'cloudinary_public_id': public_id, 'title': 'Take',
            'duration_s': 9.0, 'uploaded_by': uploader or ObjectId(), 'uploaded_at': DAY}


def chords(*entries, instrument='guitar'):
    return {'instrument': instrument, 'entries': list(entries)}


def entry(name, notes, **fields):
    return {'bar': 1, 'notes': notes, 'name': name, **fields}


# Guitar entries hold six frets from string 6 to 1; -1 is a muted string.
C, AM7, G = [-1, 3, 2, 0, 1, 0], [-1, 0, 2, 0, 1, 0], [3, -1, 0, 0, 0, -1]
PIANO_C = [48, 52, 55, 60, 64]


def apply(old, db, **options):
    return run(old, db, CONFIG, apply=True, now=NOW, sleep=lambda _: None, **options)


def preview(old, db):
    return run(old, db, CONFIG, apply=False, now=NOW, sleep=lambda _: None)


def stopped(call, *args):
    with pytest.raises(MigrationStopped) as caught:
        call(*args)
    return caught.value.report


def snapshot(database):
    return {name: list(database[name].find().sort('_id', 1)) for name in sorted(database.list_collection_names())}


def fingerprint(database):
    return hashlib.sha256(json.dumps(snapshot(database), default=str).encode()).hexdigest()


def song_of(db, source):
    return db.songs.find_one({'_id': source['_id']})


def assert_empty(db):
    assert all(db[name].count_documents({}) == 0 for name in db.list_collection_names())


def assert_unrepresentable(old, db, text):
    """The approved criterion: dry run reports it, and the real run stops writing nothing."""
    report = preview(old, db)
    assert any(text in problem['reason'] for problem in report['problems']), report['problems']
    assert_empty(db)
    report = stopped(apply, old, db)
    assert any(text in problem['reason'] for problem in report['problems'])
    assert_empty(db)
    return report


# Dry run

def test_mig_001_dry_run_lists_demos_and_touches_no_file(old, db, cloud):
    owner = user(old)
    composition(old, owner, demos=[old_demo()])
    cloud.add('legacy/demo-01')
    report = preview(old, db)
    assert_empty(db)
    assert report['demo_count'] == 1 and report['demos'][0]['public_id'] == 'legacy/demo-01'
    assert {call[0] for call in cloud.calls} == {'resource'}


def test_mig_002_dry_run_reports_legacy_formats(old, db, cloud):
    owner = user(old)
    first = composition(old, owner, lyrics='Plain', chords=chords(entry('C', C)))
    second = composition(old, owner, tablature={'strings': 6, 'content': '', 'tabs': [
        {'id': 'a', 'title': 'Riff', 'strings': 6, 'columns': ['|']}]})
    formats = preview(old, db)['legacy_formats']
    assert formats['chords_as_frets'] == [str(first['_id'])]
    assert formats['lyrics_as_string'] == [str(first['_id'])]
    assert formats['tablature_bars'] == [str(second['_id'])]


@pytest.mark.parametrize('collection', ['bands', 'invitations'])
def test_mig_003_004_007_stop_when_bands_or_invitations_exist(old, db, cloud, collection):
    user(old)
    old[collection].insert_one({'name': 'x'})
    stopped(preview, old, db)
    assert_empty(db)
    stopped(apply, old, db)
    assert_empty(db)


def test_mig_005_dry_run_succeeds_without_bands(old, db, cloud):
    user(old)
    old.bands.insert_one({'name': 'x'})
    old.bands.delete_many({})
    assert preview(old, db)['problems'] == []


def test_mig_006_dry_run_shows_suffixed_usernames(old, db, cloud):
    first, second = user(old, 'Juan Pérez'), user(old, 'Juan Perez', created_at=DAY + timedelta(days=1))
    assert preview(old, db)['suffixed_usernames'] == [{'user': str(second['_id']), 'username': 'juan-perez-2'}]
    assert first['display_name'] == 'Juan Pérez'


def test_mig_008_unrepresentable_is_reported_with_its_composition(old, db, cloud):
    source = composition(old, user(old), title='   ')
    report = assert_unrepresentable(old, db, 'metadata')
    assert report['problems'][0]['composition'] == str(source['_id'])


def test_mig_008_demo_without_uploader(old, db, cloud):
    cloud.add('legacy/demo-01')
    demo = old_demo()
    del demo['uploaded_by']
    composition(old, user(old), demos=[demo])
    assert_unrepresentable(old, db, 'uploader')


def test_mig_009_refuses_foreign_documents(old, db, cloud):
    user(old)
    db.songs.insert_one({'_id': ObjectId(), 'title': 'Created in the app'})
    before = snapshot(db)
    stopped(apply, old, db)
    assert snapshot(db) == before


# Untouched source

def test_mig_010_source_fingerprint_is_identical(old, db, cloud):
    owner = user(old)
    cloud.add('legacy/demo-01')
    composition(old, owner, demos=[old_demo()], lyrics={'content': 'Line'})
    before = fingerprint(old)
    apply(old, db)
    assert fingerprint(old) == before


def test_mig_011_only_metadata_reads(old, db, cloud):
    cloud.add('legacy/demo-01')
    before = json.dumps(cloud.assets)
    composition(old, user(old), demos=[old_demo()])
    apply(old, db)
    assert {call[0] for call in cloud.calls} == {'resource'}
    assert json.dumps(cloud.assets) == before
    assert cloud.calls[0][2]['resource_type'] == 'video' and cloud.calls[0][2]['type'] == 'authenticated'


# Users

def test_mig_020_021_hash_is_copied_and_login_works(old, db, api):
    encoded = PasswordHasher().hash('aaaaaaaa')
    user(old, email='alice@example.com', password_hash=encoded)
    apply(old, db)
    assert db.users.find_one({})['password_hash'] == encoded
    response = api.post('/auth/login', headers={'X-Device-Id': 'device'},
                        json={'email': 'alice@example.com', 'password': 'aaaaaaaa'})
    assert response.status_code == 200


@pytest.mark.parametrize('name, expected', [
    ('Juan Pérez', 'juan-perez'), ('Ñandú & Cía.', 'nandu-cia'), ('', 'usuario'), ('!!!', 'usuario'),
    ('Al', 'usuario'), ('a' * 40, 'a' * 30), ('José—María', 'jose-maria'), ('Ana李Paz', 'ana-paz'),
    ('Bjørn Lund', 'bj-rn-lund')])
def test_mig_022_025_026_026b_username_normalization(name, expected):
    assert username_base(name) == expected


def test_mig_022_display_name_is_kept(old, db, cloud):
    user(old, 'Juan Pérez')
    apply(old, db)
    assert db.users.find_one({})['display_name'] == 'Juan Pérez'


def test_mig_023_oldest_keeps_the_original_username(old, db, cloud):
    later = user(old, 'Juan Pérez', created_at=DAY + timedelta(days=2))
    oldest = user(old, 'Juan Pérez')
    middle = user(old, 'Juan Pérez', created_at=DAY + timedelta(days=1))
    apply(old, db)
    usernames = {row['_id']: row['username'] for row in db.users.find()}
    assert usernames == {oldest['_id']: 'juan-perez', middle['_id']: 'juan-perez-2', later['_id']: 'juan-perez-3'}


def test_mig_023_tie_goes_to_the_lower_id(old, db, cloud):
    low, high = sorted([ObjectId(), ObjectId()])
    user(old, 'Ana Paz', _id=high)
    user(old, 'Ana Paz', _id=low)
    apply(old, db)
    assert db.users.find_one({'_id': low})['username'] == 'ana-paz'


def test_mig_024_equal_normalizations_stay_unique(old, db, cloud):
    for name in ('Juan Pérez', 'juan perez', 'JUAN PÉREZ'):
        user(old, name)
    apply(old, db)
    assert len({row['username'] for row in db.users.find()}) == 3


def test_mig_026_empty_names_share_usuario_with_suffix(old, db, cloud):
    user(old, '')
    user(old, '***')
    apply(old, db)
    assert {row['username'] for row in db.users.find()} == {'usuario', 'usuario-2'}


def test_mig_027_email_is_lowercased(old, db, cloud):
    user(old, email='ALICE@Example.com')
    apply(old, db)
    assert db.users.find_one({})['email'] == 'alice@example.com'


def test_mig_027b_colliding_emails(old, db, cloud):
    user(old, email='Alice@example.com')
    user(old, email='alice@example.com')
    assert_unrepresentable(old, db, 'email')


def test_mig_028_029_users_hold_only_approved_fields(old, db, cloud):
    user(old)
    apply(old, db)
    assert set(db.users.find_one({})) == {'_id', 'email', 'username', 'display_name', 'password_hash',
                                          'created_at', 'updated_at'}


def test_mig_030_refresh_tokens_are_discarded(old, db, cloud):
    owner = user(old)
    old.refresh_tokens.insert_one({'user_id': owner['_id'], 'token_hash': 'x'})
    apply(old, db)
    assert db.sessions.count_documents({}) == 0


# Songs

def test_mig_040_public_song_keeps_slug(old, db, cloud, api):
    source = composition(old, user(old), visibility='public', share_slug='slug-1')
    apply(old, db)
    song = song_of(db, source)
    assert song['visibility'] == 'public' and song['share_slug'] == 'slug-1'
    assert api.get('/c/slug-1').status_code == 200


@pytest.mark.parametrize('slug', [None, 'residual'])
def test_mig_041_042_private_song_has_no_slug(old, db, cloud, slug):
    source = composition(old, user(old), share_slug=slug)
    apply(old, db)
    song = song_of(db, source)
    assert song['visibility'] == 'private' and song['share_slug'] is None


def test_mig_043_key_is_manual_and_kept(old, db, cloud):
    source = composition(old, user(old), key='Am')
    apply(old, db)
    song = song_of(db, source)
    assert song['key_mode'] == 'manual' and song['key'] == 'Am'


def test_mig_043b_missing_key_becomes_auto(old, db, cloud):
    source = composition(old, user(old), key=None, chords=chords(entry('Am7', AM7)))
    apply(old, db)
    song = song_of(db, source)
    notes = song['chords'][0]['notes']
    assert song['key_mode'] == 'auto' and song['key'] == analyze([notes])['key'] is not None
    assert song['chords'][0]['name'] == name_chord(notes, song['key'])


def test_mig_043b_missing_key_without_chords_stays_empty(old, db, cloud):
    source = composition(old, user(old), key=None)
    apply(old, db)
    song = song_of(db, source)
    assert song['key_mode'] == 'auto' and song['key'] is None


def test_mig_047b_missing_status_is_idea(old, db, cloud):
    owner = user(old)
    source = composition(old, owner)
    old.compositions.update_one({'_id': source['_id']}, {'$unset': {'status': ''}})
    apply(old, db)
    assert song_of(db, source)['status'] == 'idea'


def test_mig_044_045_047_048b_song_fields(old, db, cloud):
    owner = user(old)
    source = composition(old, owner)
    apply(old, db)
    song = song_of(db, source)
    assert not {'style_tags', 'sections_enabled', 'section_revs', 'band_editable', 'bpm', 'members'} & set(song)
    assert song['owner_type'] == 'user' and song['owner_id'] == owner['_id']
    assert song['tempo'] == 90
    for field in ('time_signature', 'status', 'title', 'created_at', 'updated_at'):
        assert song[field] == source[field]


def test_mig_046_band_id_becomes_personal_and_is_reported(old, db, cloud):
    owner = user(old)
    source = composition(old, owner, band_id=ObjectId())
    report = apply(old, db)
    song = song_of(db, source)
    assert song['owner_type'] == 'user' and song['owner_id'] == owner['_id']
    assert report['band_songs'] == [str(source['_id'])]


def test_mig_048_049_versions_and_no_old_history(old, db, cloud):
    source = composition(old, user(old), lyrics={'content': 'Line'}, chords=chords(entry('C', C)))
    old.section_revisions.insert_one({'composition_id': source['_id'], 'section': 'lyrics', 'rev': 1, 'content': 'x'})
    apply(old, db)
    assert song_of(db, source)['section_versions'] == dict.fromkeys(('lyrics', 'chords', 'tabs', 'tasks', 'meta'), 1)
    rows = list(db.revisions.find({'song_id': source['_id']}))
    assert {row['section'] for row in rows} == {'lyrics', 'chords', 'meta'}
    assert all(row['version'] == 1 and row['summary'] for row in rows)


# Memberships

def test_mig_050_051_052_memberships(old, db, cloud):
    editor, viewer = user(old, 'Eddie'), user(old, 'Vera')
    source = composition(old, user(old), members=[{'user_id': editor['_id'], 'role': 'editor'},
                                                  {'user_id': viewer['_id'], 'role': 'viewer'}])
    apply(old, db)
    rows = {row['user_id']: row for row in db.memberships.find()}
    assert rows[editor['_id']]['role'] == 'editor' and rows[viewer['_id']]['role'] == 'viewer'
    row = rows[editor['_id']]
    assert row['target_type'] == 'song' and row['target_id'] == source['_id']
    assert row['invitation_id'] is None and row['joined_at'] == NOW


def test_mig_050b_missing_role_is_editor(old, db, cloud):
    member = user(old, 'Eddie')
    composition(old, user(old), members=[{'user_id': member['_id']}])
    apply(old, db)
    assert db.memberships.find_one({})['role'] == 'editor'


def test_mig_053_054_owner_and_duplicates_are_skipped(old, db, cloud):
    owner, member = user(old), user(old, 'Eddie')
    composition(old, owner, members=[{'user_id': owner['_id'], 'role': 'editor'},
                                     {'user_id': member['_id'], 'role': 'editor'},
                                     {'user_id': member['_id'], 'role': 'editor'}])
    apply(old, db)
    assert [row['user_id'] for row in db.memberships.find()] == [member['_id']]


@pytest.mark.parametrize('role, status', [('editor', 200), ('viewer', 403)])
def test_mig_055_member_access_follows_the_role(old, db, api, role, status):
    member = user(old, 'Eddie', email='eddie@example.com', password_hash=PasswordHasher().hash('aaaaaaaa'))
    source = composition(old, user(old), members=[{'user_id': member['_id'], 'role': role}])
    apply(old, db)
    login = api.post('/auth/login', headers={'X-Device-Id': 'device'},
                     json={'email': 'eddie@example.com', 'password': 'aaaaaaaa'}).json()
    auth = headers(login)
    assert api.get(f'/songs/{source["_id"]}', headers=auth).status_code == 200
    saved = api.put(f'/songs/{source["_id"]}/sections', headers=auth, json={
        'sections': {'tasks': [{'title': 'New'}]}, 'base_versions': {'tasks': 1}})
    assert saved.status_code == status


# Chords

def test_mig_060_guitar_frets_become_midi_keeping_the_shape(old, db, cloud):
    source = composition(old, user(old), chords=chords(entry('Whatever', C)))
    apply(old, db)
    chord = song_of(db, source)['chords'][0]
    assert chord['notes'] == [48, 52, 55, 60, 64] and chord['frets'] == [3, 2, 0, 1, 0]
    assert chord['strings'] == [5, 4, 3, 2, 1] and chord['name'] == 'C'


@pytest.mark.parametrize('notes', [[48, 52, 55], [-2, 3, 2, 0, 1, 0], [25, 3, 2, 0, 1, 0], [-1] * 6],
                         ids=['short', 'below', 'above', 'silent'])
def test_mig_060b_not_six_valid_frets(old, db, cloud, notes):
    source = composition(old, user(old), chords=chords(entry('X', notes)))
    report = assert_unrepresentable(old, db, 'chord')
    assert report['problems'][0]['composition'] == str(source['_id']) and report['problems'][0]['chord'] == 0


def test_mig_063_piano_has_no_shape(old, db, cloud):
    source = composition(old, user(old), chords=chords(entry('C', PIANO_C), instrument='piano'))
    apply(old, db)
    chord = song_of(db, source)['chords'][0]
    assert chord['frets'] is None and chord['strings'] is None and chord['instrument'] == 'piano'
    assert chord['notes'] == PIANO_C


def test_mig_065_instrument_comes_from_the_section(old, db, cloud):
    source = composition(old, user(old), chords=chords(entry('C', PIANO_C), entry('C', PIANO_C), instrument='piano'))
    apply(old, db)
    assert {chord['instrument'] for chord in song_of(db, source)['chords']} == {'piano'}


def test_mig_067_each_chord_has_its_own_id(old, db, cloud):
    source = composition(old, user(old), chords=chords(entry('C', C), entry('C', C)))
    apply(old, db)
    first, second = song_of(db, source)['chords']
    assert isinstance(first['id'], ObjectId) and first['id'] != second['id']


# Tablatures

def tab(*columns, **fields):
    return {'id': 'tab-1', 'title': 'Riff', 'strings': 6, 'columns': list(columns), **fields}


def tablature(*tabs, **fields):
    return {'strings': 6, 'content': '', 'tabs': list(tabs), **fields}


COLUMN = ['', '', '5', '', '', '']


def test_mig_070_071_075_columns_bars_and_tuning(old, db, cloud):
    source = composition(old, user(old), tablature=tablature(tab(COLUMN, '|', ['x', '', '5h7', '', '', ''])))
    apply(old, db)
    migrated = song_of(db, source)['tablatures'][0]
    assert migrated['columns'] == [COLUMN, ['|'] * 6, ['x', '', '5h7', '', '', '']]
    assert migrated['tuning'] == ['E4', 'B3', 'G3', 'D3', 'A2', 'E2']
    assert migrated['title'] == 'Riff' and isinstance(migrated['id'], ObjectId)


@pytest.mark.parametrize('section, text', [
    (tablature(strings=7), 'strings'), (tablature(tab(COLUMN, strings=7)), 'strings'),
    (tablature(content='e|--5--|'), 'text'), (tablature(tab(content='e|--5--|')), 'text'),
    (tablature(tab(['', '', 'bad', '', '', ''])), 'cell')],
    ids=['section-strings', 'tab-strings', 'section-content', 'tab-content', 'cell'])
def test_mig_072_073_074_unrepresentable_tablature(old, db, cloud, section, text):
    composition(old, user(old), tablature=section)
    assert_unrepresentable(old, db, text)


def test_mig_074_cell_report_names_tab_column_and_string(old, db, cloud):
    composition(old, user(old), tablature=tablature(tab(COLUMN, ['', '', 'bad', '', '', ''])))
    problem = preview(old, db)['problems'][0]
    assert (problem['tablature'], problem['column'], problem['string']) == ('Riff', 1, 2)


# Lyrics

def lyrics_of(db, source):
    return song_of(db, source)['lyrics']['lines']


def ids_by_old_name(db, source, *names):
    return [song_of(db, source)['chords'][index]['id'] for index in range(len(names))]


def test_mig_080_chordpro_line(old, db, cloud):
    source = composition(old, user(old), lyrics={'content': '[Am7]Fly me to the [C]moon'},
                         chords=chords(entry('Am7', AM7), entry('C', C)))
    apply(old, db)
    am, c = ids_by_old_name(db, source, 'Am7', 'C')
    assert lyrics_of(db, source) == [{'text': 'Fly me to the moon', 'chords': [{'col': 0, 'chord_id': am},
                                                                               {'col': 14, 'chord_id': c}]}]


def test_mig_081_083_084_lines_empty_lines_and_plain_strings(old, db, cloud):
    source = composition(old, user(old), lyrics='First\n\nThird')
    apply(old, db)
    assert lyrics_of(db, source) == [{'text': 'First', 'chords': []}, {'text': '', 'chords': []},
                                     {'text': 'Third', 'chords': []}]


def test_mig_082_chord_only_line(old, db, cloud):
    source = composition(old, user(old), lyrics={'content': '[C] [G]'},
                         chords=chords(entry('C', C), entry('G', G)))
    apply(old, db)
    c, g = ids_by_old_name(db, source, 'C', 'G')
    assert lyrics_of(db, source) == [{'text': ' ', 'chords': [{'col': 0, 'chord_id': c}, {'col': 1, 'chord_id': g}]}]


def test_mig_085_lyric_chord_missing_from_the_section(old, db, cloud):
    composition(old, user(old), lyrics={'content': 'One\n[Dm]Two'})
    report = assert_unrepresentable(old, db, 'Dm')
    assert report['problems'][0]['line'] == 1


def test_mig_086_repeated_name_uses_the_first_and_is_reported(old, db, cloud):
    source = composition(old, user(old), lyrics={'content': '[C]One'},
                         chords=chords(entry('C', C), entry('C', [-1, 3, -1, 0, -1, 0])))
    report = apply(old, db)
    first = song_of(db, source)['chords'][0]['id']
    assert lyrics_of(db, source)[0]['chords'] == [{'col': 0, 'chord_id': first}]
    assert report['repeated_chord_names'] == [{'composition': str(source['_id']), 'name': 'C'}]


def test_mig_086b_match_uses_the_old_name(old, db, cloud):
    source = composition(old, user(old), lyrics={'content': '[Old]One'}, chords=chords(entry('Old', C)))
    apply(old, db)
    chord = song_of(db, source)['chords'][0]
    assert chord['name'] == 'C' and lyrics_of(db, source)[0]['chords'][0]['chord_id'] == chord['id']


@pytest.mark.parametrize('lyrics', [None, {'content': ''}, ''])
def test_mig_087_no_lyrics(old, db, cloud, lyrics):
    source = composition(old, user(old), lyrics=lyrics)
    apply(old, db)
    assert song_of(db, source)['lyrics'] is None


def test_mig_088_every_chord_id_exists(old, db, cloud):
    source = composition(old, user(old), lyrics={'content': '[C]One\n[C]Two'}, chords=chords(entry('C', C)))
    apply(old, db)
    song = song_of(db, source)
    known = {chord['id'] for chord in song['chords']}
    assert all(placement['chord_id'] in known for line in song['lyrics']['lines'] for placement in line['chords'])


def test_tasks_keep_text_and_state(old, db, cloud):
    source = composition(old, user(old), todos=[{'id': 'a', 'text': 'Record', 'done': True}])
    apply(old, db)
    task = song_of(db, source)['tasks'][0]
    assert task['title'] == 'Record' and task['done'] is True and isinstance(task['id'], ObjectId)


# Demos and comments

def test_mig_090_094_demo_reuses_the_file_with_cloudinary_values(old, db, cloud):
    owner = user(old)
    cloud.add('legacy/demo-01', format='wav', bytes=64044, duration=2.0)
    source = composition(old, owner, demos=[old_demo(uploader=owner['_id'])])
    apply(old, db)
    demo = song_of(db, source)['demos'][0]
    assert demo['cloudinary_public_id'] == 'legacy/demo-01'
    assert (demo['title'], demo['uploaded_by'], demo['uploaded_at']) == ('Take', owner['_id'], DAY)
    assert (demo['format'], demo['mime_type'], demo['size_bytes'], demo['duration_s']) == ('wav', 'audio/wav', 64044, 2.0)
    assert 'r2_key' not in demo and 'demo_id' not in demo


def test_mig_091_valid_id_becomes_its_object_id(old, db, cloud):
    demo_id = str(ObjectId())
    cloud.add('legacy/demo-01')
    source = composition(old, user(old), demos=[old_demo(demo_id=demo_id)])
    apply(old, db)
    assert song_of(db, source)['demos'][0]['id'] == ObjectId(demo_id)


def test_mig_091b_other_ids_are_stable_across_runs(old, db, cloud):
    cloud.add('legacy/demo-01')
    source = composition(old, user(old), demos=[old_demo()])
    before = fingerprint(old)
    apply(old, db)
    first = song_of(db, source)['demos']
    apply(old, db)
    assert song_of(db, source)['demos'] == first and len(first) == 1
    assert isinstance(first[0]['id'], ObjectId) and fingerprint(old) == before


def test_mig_091b_id_depends_on_the_composition(old, db, cloud):
    cloud.add('legacy/demo-01')
    owner = user(old)
    one, two = composition(old, owner, demos=[old_demo()]), composition(old, owner, demos=[old_demo()])
    apply(old, db)
    assert song_of(db, one)['demos'][0]['id'] != song_of(db, two)['demos'][0]['id']


def test_mig_091b_collision_stops_without_writing(old, db, cloud):
    demo_id = str(ObjectId())
    cloud.add('legacy/demo-01')
    composition(old, user(old), demos=[old_demo(demo_id=demo_id), old_demo(demo_id=demo_id.upper())])
    assert_unrepresentable(old, db, 'collision')


@pytest.mark.parametrize('demo_id', ['take-01', str(ObjectId())], ids=['derived', 'object-id'])
def test_mig_092_comments_follow_their_demo(old, db, cloud, demo_id):
    author = user(old, 'Eddie')
    cloud.add('legacy/demo-01')
    source = composition(old, user(old), demos=[old_demo(demo_id=demo_id)])
    comment = {'_id': ObjectId(), 'composition_id': source['_id'], 'demo_id': demo_id, 'author_id': author['_id'],
               'timestamp_s': 1.5, 'text': 'Nice', 'created_at': DAY}
    old.composition_comments.insert_one(comment)
    apply(old, db)
    row = db.demo_comments.find_one({})
    assert row['_id'] == comment['_id'] and row['song_id'] == source['_id']
    assert row['demo_id'] == song_of(db, source)['demos'][0]['id']
    assert (row['author_id'], row['timestamp_s'], row['text'], row['created_at']) == (author['_id'], 1.5, 'Nice', DAY)


def test_mig_092_orphan_comment_is_unrepresentable(old, db, cloud):
    source = composition(old, user(old))
    old.composition_comments.insert_one({'composition_id': source['_id'], 'demo_id': 'gone', 'author_id': ObjectId(),
                                         'timestamp_s': 1.0, 'text': 'Lost', 'created_at': DAY})
    assert_unrepresentable(old, db, 'comment')


def test_mig_092b_comment_without_author(old, db, cloud):
    cloud.add('legacy/demo-01')
    source = composition(old, user(old), demos=[old_demo()])
    old.composition_comments.insert_one({'composition_id': source['_id'], 'demo_id': 'take-01', 'author_id': None,
                                         'timestamp_s': 1.0, 'text': 'Lost', 'created_at': DAY})
    assert_unrepresentable(old, db, 'author')


def test_mig_092b_member_without_user(old, db, cloud):
    composition(old, user(old), members=[{'user_id': None, 'role': 'editor'}])
    assert_unrepresentable(old, db, 'Member')


def failing_reads(cloud, monkeypatch, failures):
    real = cloud.resource
    left = [failures]

    def flaky(public_id, **options):
        if left[0]:
            left[0] -= 1
            cloud.calls.append(('resource', public_id, options))
            raise RuntimeError('metadata unavailable')
        return real(public_id, **options)

    monkeypatch.setattr(cloudinary.api, 'resource', flaky)
    return left


def test_mig_093_retries_with_growing_waits(old, db, cloud, monkeypatch):
    cloud.add('legacy/demo-01')
    source = composition(old, user(old), demos=[old_demo()])
    failing_reads(cloud, monkeypatch, 2)
    waits = []
    run(old, db, CONFIG, apply=True, now=NOW, sleep=waits.append)
    assert len(song_of(db, source)['demos']) == 1
    assert len(waits) == 2 and waits[0] < waits[1]
    assert {call[0] for call in cloud.calls} == {'resource'}


def test_mig_093b_third_failure_stops_and_a_rerun_continues(old, db, cloud, monkeypatch):
    cloud.add('legacy/demo-01')
    source = composition(old, user(old), demos=[old_demo()])
    before = fingerprint(old)
    failing_reads(cloud, monkeypatch, 3)
    report = stopped(apply, old, db)
    assert 'legacy/demo-01' in report['error'] and fingerprint(old) == before
    apply(old, db)
    assert len(song_of(db, source)['demos']) == 1 and db.songs.count_documents({}) == 1


def test_mig_095_unreadable_identifier(old, db, cloud):
    source = composition(old, user(old), demos=[old_demo()])
    report = assert_unrepresentable(old, db, 'authenticated')
    problem = report['problems'][0]
    assert problem['composition'] == str(source['_id']) and problem['demo'] == 'take-01'
    assert {call[0] for call in cloud.calls} == {'resource'}


@pytest.mark.parametrize('fields', [{'has_audio': False}, {'duration': None}, {'format': 'avi'}, {'bytes': None}],
                         ids=['no-audio', 'no-duration', 'format', 'no-size'])
def test_mig_096_unusable_metadata(old, db, cloud, fields):
    cloud.add('legacy/demo-01', **fields)
    composition(old, user(old), demos=[old_demo()])
    assert_unrepresentable(old, db, 'metadata')
    assert 'legacy/demo-01' in cloud.assets


def test_mig_096b_opus_is_representable(old, db, cloud):
    cloud.add('legacy/demo-01', format='opus')
    source = composition(old, user(old), demos=[old_demo()])
    apply(old, db)
    demo = song_of(db, source)['demos'][0]
    assert demo['format'] == 'opus' and demo['mime_type'] == 'audio/ogg'


def test_mig_096_long_legacy_audio_is_representable(old, db, cloud):
    cloud.add('legacy/demo-01', duration=3600.0, bytes=500 * 1024 ** 2)
    source = composition(old, user(old), demos=[old_demo()])
    apply(old, db)
    assert song_of(db, source)['demos'][0]['duration_s'] == 3600.0


# Idempotence

def full_source(old, cloud):
    owner, member = user(old, 'Juan Pérez'), user(old, 'Juan Perez')
    cloud.add('legacy/demo-01')
    source = composition(old, owner, members=[{'user_id': member['_id'], 'role': 'editor'}],
                         demos=[old_demo()], lyrics={'content': '[C]One'}, chords=chords(entry('C', C)),
                         todos=[{'id': 'a', 'text': 'Record', 'done': False}],
                         tablature=tablature(tab(COLUMN, '|')))
    old.composition_comments.insert_one({'composition_id': source['_id'], 'demo_id': 'take-01', 'author_id': owner['_id'],
                                         'timestamp_s': 1.0, 'text': 'Nice', 'created_at': DAY})
    return source


def test_mig_100_101_102_second_run_changes_nothing(old, db, cloud):
    full_source(old, cloud)
    apply(old, db)
    documents, assets = snapshot(db), json.dumps(cloud.assets)
    usernames = {row['username'] for row in db.users.find()}
    run(old, db, CONFIG, apply=True, now=NOW + timedelta(days=1), sleep=lambda _: None)
    assert snapshot(db) == documents and json.dumps(cloud.assets) == assets
    assert {row['username'] for row in db.users.find()} == usernames


@pytest.mark.parametrize('collection', TARGETS)
def test_mig_103_interrupted_run_finishes_without_duplicates(old, db, cloud, monkeypatch, collection):
    full_source(old, cloud)
    apply(old, db)
    expected = snapshot(db)
    for name in db.list_collection_names():
        db[name].delete_many({})
    real = migrate.write_collection

    def interrupted(target, name, documents):
        if name == collection:
            target[name].insert_one(documents[0])
            raise ConnectionError('interrupted')
        real(target, name, documents)

    monkeypatch.setattr(migrate, 'write_collection', interrupted)
    with pytest.raises(ConnectionError):
        apply(old, db)
    monkeypatch.setattr(migrate, 'write_collection', real)
    apply(old, db)
    assert {name: rows for name, rows in snapshot(db).items() if rows} == {name: rows for name, rows in expected.items() if rows}


def test_mig_104_refuses_after_the_app_created_data(old, db, cloud):
    full_source(old, cloud)
    apply(old, db)
    db.songs.insert_one({'_id': ObjectId(), 'title': 'New in the app'})
    before = snapshot(db)
    stopped(apply, old, db)
    assert snapshot(db) == before


def test_mig_104_refuses_after_the_app_edited_data(old, db, cloud):
    source = full_source(old, cloud)
    apply(old, db)
    db.songs.update_one({'_id': source['_id']}, {'$set': {'title': 'Edited in the app'}})
    before = snapshot(db)
    report = stopped(apply, old, db)
    assert snapshot(db) == before and 'songs' in report['error']


def test_mig_104_refuses_after_the_app_created_sessions(old, db, cloud):
    full_source(old, cloud)
    apply(old, db)
    db.sessions.insert_one({'sid': 'x'})
    stopped(apply, old, db)
