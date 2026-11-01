"""One-shot migration from the old Erato database (decision 12, tests_md/migracion.md).

    python migrate.py --source-db OLD --target-db NEW [--apply]

Without --apply it is a dry run that only reports. The connection comes from MONGODB_URI
and CLOUDINARY_URL. The source database and the Cloudinary files are only read: demos
keep their existing files and identifiers.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import sys
import time
import unicodedata

from bson import ObjectId
from pymongo import MongoClient

from app.database import create_indexes
from app.detection import analyze, name_chord
from app.demos import FORMATS
from app.errors import APIError
from app.sections import META, SECTION_LABELS, SECTIONS, Meta, content, normalize, valid_cell
from app.storage import read_asset

TARGETS = ('users', 'songs', 'memberships', 'revisions', 'demo_comments')
OPEN_STRINGS = (40, 45, 50, 55, 59, 64)  # standard tuning, string 6 first, as old chords store frets
METADATA_ATTEMPTS = 3
CHORD_MARK = re.compile(r'\[([^\]]+)\]')


class MigrationStopped(Exception):
    def __init__(self, report):
        self.report = report
        super().__init__(report.get('error') or 'Unrepresentable data')


def object_id(value):
    if value is None:  # ObjectId(None) would silently generate a new identifier
        raise ValueError('Missing reference')
    return value if isinstance(value, ObjectId) else ObjectId(value)


def stable_id(composition_id, kind, value):
    """The same old record always yields the same ObjectId, so a rerun rewrites nothing."""
    return ObjectId(hashlib.sha256(f'{composition_id}:{kind}:{value}'.encode()).digest()[:12])


def problem(report, composition, reason, **details):
    report['problems'].append({'composition': str(composition['_id']), 'reason': reason, **details})


def legacy_format(report, name, composition):
    rows = report['legacy_formats'].setdefault(name, [])
    if str(composition['_id']) not in rows:
        rows.append(str(composition['_id']))


def username_base(display_name):
    letters = (char for char in unicodedata.normalize('NFKD', display_name) if not unicodedata.combining(char))
    name = re.sub(r'[^a-z0-9]+', '-', ''.join(letters).lower()).strip('-')[:30].rstrip('-')
    return name if len(name) >= 3 else 'usuario'


def plan_users(source, report):
    documents, taken, emails = [], set(), set()
    for row in source.users.find().sort([('created_at', 1), ('_id', 1)]):
        email = row['email'].lower()
        if email in emails:
            report['problems'].append({'user': str(row['_id']), 'reason': f'Repeated email {email}'})
        emails.add(email)
        base = username = username_base(row['display_name'])
        number = 1
        while username in taken:
            number += 1
            suffix = f'-{number}'
            username = base[:30 - len(suffix)].rstrip('-') + suffix
        taken.add(username)
        if username != base:
            report['suffixed_usernames'].append({'user': str(row['_id']), 'username': username})
        documents.append({'_id': row['_id'], 'email': email, 'username': username,
                          'display_name': row['display_name'], 'password_hash': row['password_hash'],
                          'created_at': row['created_at'], 'updated_at': row['created_at']})
    return documents


def guitar_shape(old_frets):
    """Old guitar `notes` hold six frets, string 6 first, with -1 for a muted string."""
    if len(old_frets) != 6 or not all(isinstance(fret, int) and -1 <= fret <= 24 for fret in old_frets):
        return None
    sounding = [(index, fret) for index, fret in enumerate(old_frets) if fret >= 0]
    return {'notes': [OPEN_STRINGS[index] + fret for index, fret in sounding],
            'frets': [fret for _, fret in sounding], 'strings': [6 - index for index, _ in sounding]}


def plan_chord_shapes(composition, report):
    """The valid chords as (old name, item); the key can only be chosen from their notes."""
    section = composition.get('chords') or {}
    instrument = section.get('instrument', 'guitar')
    shapes = []
    for index, entry in enumerate(section.get('entries') or []):
        item = {'id': str(stable_id(composition['_id'], 'chord', index)), 'instrument': instrument,
                'notes': entry['notes'], 'frets': None, 'strings': None}
        if instrument == 'guitar':
            legacy_format(report, 'chords_as_frets', composition)
            shape = guitar_shape(entry['notes'])
            if shape is None:
                problem(report, composition, 'Guitar chord without six valid frets', chord=index)
                continue
            item.update(shape)
        try:
            name_chord(item['notes'])
        except ValueError as error:
            problem(report, composition, f'Invalid chord: {error}', chord=index)
            continue
        shapes.append((entry['name'], item))
    return shapes


def plan_chords(composition, shapes, song, report):
    chords, by_old_name = [], {}
    for old_name, item in shapes:
        try:
            chords += normalize('chords', [item], song, historical=True)
        except ValueError as error:
            problem(report, composition, f'Invalid chord: {error}', chord=item['id'])
            continue
        by_old_name.setdefault(old_name, []).append(chords[-1]['id'])
    return chords, by_old_name


def plan_line(composition, raw, index, by_old_name, report):
    placements, text, last = [], '', 0
    for mark in CHORD_MARK.finditer(raw):
        text += raw[last:mark.start()]
        last = mark.end()
        name = mark[1]
        if name not in by_old_name:
            problem(report, composition, f'Chord {name} is not in the chord section', line=index)
            continue
        repeated = {'composition': str(composition['_id']), 'name': name}
        if len(by_old_name[name]) > 1 and repeated not in report['repeated_chord_names']:
            report['repeated_chord_names'].append(repeated)
        placements.append({'col': len(text), 'chord_id': str(by_old_name[name][0])})
    return {'text': text + raw[last:], 'chords': placements}


def plan_lyrics(composition, song, by_old_name, report):
    old = composition.get('lyrics')
    if isinstance(old, str):
        legacy_format(report, 'lyrics_as_string', composition)
    text = old if isinstance(old, str) else (old or {}).get('content')
    if not text:
        return None
    lines = [plan_line(composition, raw, index, by_old_name, report) for index, raw in enumerate(text.split('\n'))]
    try:
        return normalize('lyrics', {'lines': lines}, song)
    except ValueError as error:
        problem(report, composition, f'Invalid lyrics: {error}')
        return None


def plan_tab_columns(composition, tab, report):
    columns = []
    for index, column in enumerate(tab.get('columns') or []):
        if column == '|':
            legacy_format(report, 'tablature_bars', composition)
            columns.append(['|'] * 6)
            continue
        if not isinstance(column, list) or len(column) != 6:
            problem(report, composition, 'Column without six cells', tablature=tab.get('title'), column=index)
            continue
        for string, cell in enumerate(column):
            if not valid_cell(cell):
                problem(report, composition, f'Invalid cell {cell!r}', tablature=tab.get('title'),
                        column=index, string=string)
        columns.append(column)
    return columns


def plan_tablatures(composition, song, report):
    section = composition.get('tablature') or {}
    tabs = section.get('tabs') or []
    if section.get('strings', 6) != 6:
        problem(report, composition, 'Tablature without 6 strings')
    if section.get('content') and not tabs:
        problem(report, composition, 'Tablature with only text content')
    result = []
    for index, tab in enumerate(tabs):
        if tab.get('strings', 6) != 6:
            problem(report, composition, 'Tablature without 6 strings', tablature=tab.get('title'))
            continue
        if tab.get('content') and not tab.get('columns'):
            problem(report, composition, 'Tablature with only text content', tablature=tab.get('title'))
            continue
        item = {'id': str(stable_id(composition['_id'], 'tab', index)), 'title': tab.get('title'),
                'columns': plan_tab_columns(composition, tab, report)}
        try:
            result += normalize('tabs', [item], song, historical=True)
        except ValueError as error:
            problem(report, composition, f'Invalid tablature cell: {error}', tablature=tab.get('title'))
    return result


def plan_tasks(composition, song, report):
    result = []
    for index, todo in enumerate(composition.get('todos') or []):
        item = {'id': str(stable_id(composition['_id'], 'task', index)), 'title': todo['text'],
                'done': todo.get('done', False)}
        try:
            result += normalize('tasks', [item], song, historical=True)
        except ValueError as error:
            problem(report, composition, f'Invalid task: {error}', task=index)
    return result


def read_metadata(config, public_id, sleep, report):
    for attempt in range(METADATA_ATTEMPTS):
        try:
            return read_asset(config, public_id)
        except APIError:
            if attempt == METADATA_ATTEMPTS - 1:
                report['error'] = f'Could not read the metadata of {public_id}'
                raise MigrationStopped(report) from None
            sleep(2 ** attempt)


def usable_metadata(asset):
    return (asset.get('has_audio') is True and asset.get('format') in FORMATS
            and asset.get('duration') is not None and asset.get('bytes') is not None)


def demo_id_for(composition, old_id):
    if ObjectId.is_valid(old_id):
        return ObjectId(old_id)
    return stable_id(composition['_id'], 'demo', old_id)


def plan_demos(composition, config, sleep, report, demo_ids):
    result, seen = [], set()
    for old in composition.get('demos') or []:
        old_id, public_id = old['demo_id'], old['cloudinary_public_id']
        report['demos'].append({'composition': str(composition['_id']), 'demo': old_id, 'public_id': public_id})
        demo_id = demo_id_for(composition, old_id)
        if demo_id in seen:
            problem(report, composition, 'Demo ID collision', demo=old_id)
            continue
        seen.add(demo_id)
        demo_ids[composition['_id'], old_id] = demo_id
        asset = read_metadata(config, public_id, sleep, report)
        if asset is None:
            problem(report, composition, 'Not readable as video/authenticated', demo=old_id)
        elif not usable_metadata(asset):
            problem(report, composition, 'Unusable Cloudinary metadata', demo=old_id)
        elif old.get('uploaded_by') is None:
            problem(report, composition, 'Demo without an uploader', demo=old_id)
        else:
            result.append({'id': demo_id, 'title': old['title'], 'duration_s': asset['duration'],
                           'cloudinary_public_id': public_id, 'format': asset['format'],
                           'mime_type': FORMATS[asset['format']], 'size_bytes': asset['bytes'],
                           'uploaded_by': object_id(old['uploaded_by']), 'uploaded_at': old['uploaded_at']})
    return result


def plan_memberships(composition, now, report):
    rows, seen = [], {composition['owner_id']}
    for member in composition.get('members') or []:
        if member.get('user_id') is None:
            problem(report, composition, 'Member without a user')
            continue
        user_id = object_id(member['user_id'])
        if user_id not in seen:
            seen.add(user_id)
            rows.append({'_id': stable_id(composition['_id'], 'member', user_id), 'target_type': 'song',
                         'target_id': composition['_id'], 'user_id': user_id, 'role': member.get('role', 'editor'),
                         'invitation_id': None, 'joined_at': now})
    return rows


def plan_revisions(composition, song):
    """Version 1 of every non-empty section; the old history is not migrated."""
    return [{'_id': stable_id(composition['_id'], 'revision', section), 'song_id': song['_id'],
             'section': section, 'version': 1, 'author_id': song['owner_id'],
             'created_at': song['updated_at'], 'content': content(song, section),
             'summary': f'importó {SECTION_LABELS[section]}'}
            for section in SECTIONS if content(song, section)]


def plan_metadata(composition, shapes, report):
    # Manual mode requires a key, so a composition without one takes the first candidate.
    key = composition.get('key')
    key_mode = 'manual' if key else 'auto'
    if not key:
        key = analyze([item['notes'] for _, item in shapes])['key']
    try:
        return Meta.model_validate({'title': composition['title'], 'status': composition.get('status') or 'idea',
                                    'tempo': composition.get('bpm'), 'key': key,
                                    'time_signature': composition.get('time_signature'),
                                    'key_mode': key_mode}).model_dump()
    except ValueError as error:
        problem(report, composition, f'Invalid metadata: {error}')
        return None


def plan_composition(composition, config, sleep, now, report, documents, demo_ids):
    shapes = plan_chord_shapes(composition, report)
    meta = plan_metadata(composition, shapes, report)
    if meta is None:
        return
    public = composition['visibility'] == 'public'
    if public and not composition.get('share_slug'):
        problem(report, composition, 'Public composition without a share slug')
    if composition.get('band_id') is not None:
        report['band_songs'].append(str(composition['_id']))
    song = {'_id': composition['_id'], 'owner_type': 'user', 'owner_id': composition['owner_id'],
            **{field: meta[field] for field in META}, 'visibility': composition['visibility'],
            'share_slug': composition.get('share_slug') if public else None,
            'chords': [], 'tablatures': [], 'lyrics': None, 'tasks': [], 'demos': [],
            'section_versions': dict.fromkeys(SECTIONS, 1), 'created_at': composition['created_at'],
            'updated_at': composition['updated_at']}
    song['chords'], by_old_name = plan_chords(composition, shapes, song, report)
    song['lyrics'] = plan_lyrics(composition, song, by_old_name, report)
    song['tablatures'] = plan_tablatures(composition, song, report)
    song['tasks'] = plan_tasks(composition, song, report)
    song['demos'] = plan_demos(composition, config, sleep, report, demo_ids)
    documents['songs'].append(song)
    documents['memberships'] += plan_memberships(composition, now, report)
    documents['revisions'] += plan_revisions(composition, song)


def plan_comments(source, demo_ids, report):
    rows = []
    for comment in source.composition_comments.find().sort('_id', 1):
        demo_id = demo_ids.get((comment['composition_id'], comment['demo_id']))
        if demo_id is None:
            report['problems'].append({'composition': str(comment['composition_id']),
                                       'reason': f'A comment refers to a missing demo: {comment["demo_id"]}'})
            continue
        if comment.get('author_id') is None:
            report['problems'].append({'composition': str(comment['composition_id']),
                                       'reason': f'A comment has no author: {comment["_id"]}'})
            continue
        rows.append({'_id': comment['_id'], 'song_id': comment['composition_id'], 'demo_id': demo_id,
                     'author_id': object_id(comment['author_id']), 'timestamp_s': float(comment['timestamp_s']),
                     'text': comment['text'], 'created_at': comment['created_at'],
                     'updated_at': comment['created_at']})
    return rows


def target_conflict(target, documents):
    """Why the target cannot be overwritten; only an earlier run's exact output may be there."""
    for name in target.list_collection_names():
        if name not in TARGETS and name != 'login_attempts' and target[name].count_documents({}):
            return f'The target already holds data in {name}'
    for name in TARGETS:
        planned = {row['_id']: row for row in documents[name]}
        for row in target[name].find():
            expected = planned.get(row['_id'])
            if expected is None:
                return f'The target holds a document that is not in the source: {name} {row["_id"]}'
            ignored = {'joined_at'} if name == 'memberships' else set()
            if {k: v for k, v in row.items() if k not in ignored} != {k: v for k, v in expected.items() if k not in ignored}:
                return f'A migrated document changed in the target: {name} {row["_id"]}'
    return None


def write_collection(target, name, documents):
    present = {row['_id'] for row in target[name].find({}, {'_id': 1})}
    missing = [row for row in documents if row['_id'] not in present]
    if missing:
        target[name].insert_many(missing, ordered=False)


def run(source, target, config, *, apply=False, now=None, sleep=time.sleep):
    now = now or datetime.now(timezone.utc)
    report = {'problems': [], 'legacy_formats': {}, 'demos': [], 'demo_count': 0, 'suffixed_usernames': [],
              'band_songs': [], 'repeated_chord_names': []}
    if source.bands.count_documents({}) or source.invitations.count_documents({}):
        report['error'] = 'The old bands and invitations must be empty'
        raise MigrationStopped(report)
    documents = {name: [] for name in TARGETS}
    documents['users'] = plan_users(source, report)
    demo_ids = {}
    for composition in source.compositions.find().sort('_id', 1):
        plan_composition(composition, config, sleep, now, report, documents, demo_ids)
    documents['demo_comments'] = plan_comments(source, demo_ids, report)
    report['demo_count'] = len(report['demos'])
    conflict = target_conflict(target, documents)
    if not apply:
        report['target_conflict'] = conflict
        return report
    report['error'] = conflict
    if report['problems'] or conflict:
        raise MigrationStopped(report)
    create_indexes(target)
    for name in TARGETS:
        write_collection(target, name, documents[name])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--source-db', required=True)
    parser.add_argument('--target-db', required=True)
    parser.add_argument('--apply', action='store_true', help='write to the target; the default is a dry run')
    options = parser.parse_args()
    if options.source_db == options.target_db:
        parser.error('The source and target databases must differ')
    client = MongoClient(os.environ['MONGODB_URI'], tz_aware=True)
    config = {'CLOUDINARY_URL': os.environ.get('CLOUDINARY_URL', '')}
    try:
        report = run(client[options.source_db], client[options.target_db], config, apply=options.apply)
    except MigrationStopped as stopped:
        print(json.dumps(stopped.report, indent=2, ensure_ascii=False))
        sys.exit(1)
    finally:
        client.close()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(1 if report['problems'] else 0)


if __name__ == '__main__':
    main()
