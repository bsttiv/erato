"""Strict input validation and normalization for the five embedded sections."""
from difflib import SequenceMatcher
import re
from typing import Literal

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator, model_validator

from app.accounts import new_id
from app.detection import name_chord

SECTIONS = ('lyrics', 'chords', 'tabs', 'tasks', 'meta')
FIELDS = {'lyrics': 'lyrics', 'chords': 'chords', 'tabs': 'tablatures', 'tasks': 'tasks'}
META = ('title', 'status', 'tempo', 'time_signature', 'key', 'key_mode')
VALID_KEYS = set(('C G D A E B F# C# F Bb Eb Ab Db Gb Cb '
                  'Am Em Bm F#m C#m G#m D#m A#m Dm Gm Cm Fm Bbm Ebm Abm').split())
TUNING = ['E4', 'B3', 'G3', 'D3', 'A2', 'E2']
FRET = r'(?:[0-9]|1[0-9]|2[0-4])'
CELL = re.compile(rf'{FRET}(?:[hpbr/\\s]{FRET}){{0,3}}[~v]?')


def valid_cell(value):
    return isinstance(value, str) and (value in ('', 'x', '|') or CELL.fullmatch(value) is not None)


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Meta(Input):
    title: StrictStr
    status: Literal['idea', 'in_progress', 'ready'] = 'idea'
    tempo: StrictInt | None = Field(default=None, ge=20, le=400)
    time_signature: StrictStr | None = None
    key: StrictStr | None = None
    key_mode: Literal['auto', 'manual'] = 'auto'

    @field_validator('title')
    @classmethod
    def title_valid(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Title is required')
        return value

    @field_validator('key')
    @classmethod
    def key_valid(cls, value):
        if value is not None and value not in VALID_KEYS:
            raise ValueError('Invalid key')
        return value

    @field_validator('time_signature')
    @classmethod
    def meter_valid(cls, value):
        if value is not None and not re.fullmatch(r'(?:[1-9]|[12][0-9]|3[0-2])/(?:1|2|4|8|16|32)', value):
            raise ValueError('Invalid time signature')
        return value


class SongCreate(Meta):
    owner_type: Literal['user', 'band'] = 'user'
    owner_id: StrictStr | None = None

    @model_validator(mode='after')
    def owner_valid(self):
        if self.owner_type == 'user' and self.owner_id is not None:
            raise ValueError('Personal ownership is assigned by the server')
        if self.owner_type == 'band' and (self.owner_id is None or not ObjectId.is_valid(self.owner_id)):
            raise ValueError('Band ID is required')
        return self


class Embedded(Input):
    id: StrictStr | None = None

    @field_validator('id')
    @classmethod
    def id_valid(cls, value):
        if value is not None and not ObjectId.is_valid(value):
            raise ValueError('Invalid embedded ID')
        return value


class Chord(Embedded):
    instrument: Literal['guitar', 'piano']
    notes: list[StrictInt]
    frets: list[StrictInt] | None = None
    strings: list[StrictInt] | None = None

    @model_validator(mode='after')
    def shape_valid(self):
        name_chord(self.notes)
        if self.instrument == 'piano':
            if self.frets is not None or self.strings is not None:
                raise ValueError('Piano has no frets or strings')
        else:
            if self.frets is None or self.strings is None or not len(self.notes) == len(self.frets) == len(self.strings):
                raise ValueError('Parallel guitar arrays required')
            if len(set(self.strings)) != len(self.strings):
                raise ValueError('Each string may sound only once')
            standard = [64, 59, 55, 50, 45, 40]
            for note, fret, string in zip(self.notes, self.frets, self.strings):
                if not 0 <= fret <= 24 or not 1 <= string <= 6 or standard[string - 1] + fret != note:
                    raise ValueError('Notes must match the standard guitar tuning')
        return self


class Tablature(Embedded):
    title: StrictStr | None = None
    tuning: list[StrictStr] = Field(default_factory=lambda: TUNING.copy())
    columns: list[list[StrictStr]]

    @model_validator(mode='after')
    def tab_valid(self):
        if len(self.tuning) != 6 or any(not re.fullmatch(r'[A-G](?:#|b)?[0-9]', note) for note in self.tuning):
            raise ValueError('Six valid tuning notes required')
        for column in self.columns:
            if len(column) != 6 or not all(valid_cell(cell) for cell in column):
                raise ValueError('Invalid column')
            if '|' in column and column != ['|'] * 6:
                raise ValueError('Bar must occupy all six strings')
        return self


class Task(Embedded):
    title: StrictStr
    done: StrictBool = False

    @field_validator('title')
    @classmethod
    def title_valid(cls, value):
        value = value.strip()
        if not 1 <= len(value) <= 200:
            raise ValueError('Task title must contain 1 to 200 characters')
        return value


class Placement(Input):
    col: StrictInt = Field(ge=0)
    chord_id: StrictStr


class Line(Input):
    section: StrictStr | None = Field(default=None, min_length=1, max_length=40)
    text: StrictStr
    chords: list[Placement] = Field(default_factory=list)

    @model_validator(mode='after')
    def columns_unique(self):
        if len({p.col for p in self.chords}) != len(self.chords):
            raise ValueError('Repeated chord column')
        return self

    @model_validator(mode='after')
    def section_marker(self):
        if self.section is not None:
            self.section = self.section.strip()
            if not self.section or self.text or self.chords:
                raise ValueError('A section line holds only its name')
        return self


class Lyrics(Input):
    lines: list[Line]


class Save(Input):
    sections: dict[str, object]
    base_versions: dict[str, StrictInt]

    @model_validator(mode='after')
    def bases_valid(self):
        if not self.sections or not self.sections.keys() <= set(SECTIONS):
            raise ValueError('Unknown or empty section selection')
        if not self.sections.keys() <= self.base_versions.keys():
            raise ValueError('Every submitted section requires a base version')
        if not self.base_versions.keys() <= set(SECTIONS) or any(v < 1 for v in self.base_versions.values()):
            raise ValueError('Invalid base versions')
        return self


class Visibility(Input):
    visibility: Literal['private', 'public']


class Restore(Input):
    base_version: StrictInt = Field(ge=1)


def content(song, section):
    return {field: song[field] for field in META} if section == 'meta' else song[FIELDS[section]]


def assign(song, section, value):
    if section == 'meta':
        song.update(value)
    else:
        song[FIELDS[section]] = value


def normalize(section, value, song, *, historical=False):
    if section == 'meta':
        if not isinstance(value, dict):
            raise ValueError('Metadata must be an object')
        return Meta.model_validate({**content(song, 'meta'), **value}).model_dump()
    if section == 'lyrics':
        if value is None:
            return None
        normalized = Lyrics.model_validate(value).model_dump(exclude_none=True)
        for line in normalized['lines']:
            for placement in line['chords']:
                if not ObjectId.is_valid(placement['chord_id']):
                    raise ValueError('Invalid chord ID')
                placement['chord_id'] = ObjectId(placement['chord_id'])
        return normalized
    if not isinstance(value, list):
        raise ValueError('Section must be an array')
    model = {'chords': Chord, 'tabs': Tablature, 'tasks': Task}[section]
    existing = {str(item['id']) for item in content(song, section)}
    result = []
    for index, item in enumerate(value):
        item = model.model_validate(item).model_dump()
        if not historical and item['id'] is not None and item['id'] not in existing:
            raise ValueError('Embedded ID does not belong to this section')
        item['id'] = ObjectId(item['id']) if item['id'] is not None else new_id()
        if section == 'tabs' and item['title'] is None:
            item['title'] = f'Tablatura {index + 1}'
        if section == 'chords':
            item['name'] = name_chord(item['notes'], song['key'])
        result.append(item)
    if len({item['id'] for item in result}) != len(result):
        raise ValueError('Duplicate embedded ID')
    return result


SUMMARY_LENGTH = 120
STATUS_LABELS = {'idea': 'Idea', 'in_progress': 'En progreso', 'ready': 'Lista'}
SECTION_LABELS = {'lyrics': 'la letra', 'chords': 'los acordes', 'tabs': 'las tablaturas',
                  'tasks': 'las tareas', 'meta': 'los datos de la canción'}


def element_phrases(before, after, noun, label, verb=lambda old, new: 'cambió'):
    old = {item['id']: item for item in before}
    new = {item['id']: item for item in after}
    return ([f'agregó {noun} {label(item)}' for key, item in new.items() if key not in old]
            + [f'quitó {noun} {label(item)}' for key, item in old.items() if key not in new]
            + [f'{verb(old[key], item)} {noun} {label(item)}' for key, item in new.items()
               if key in old and old[key] != item])


def lyric_part(lines, index):
    return next((line['section'] for line in reversed(lines[:index + 1]) if line.get('section')), None)


def lyric_phrases(before, after):
    if not before:
        return ['agregó la letra']
    if not after:
        return ['borró la letra']
    old, new = before['lines'], after['lines']
    old_text = [line.get('section') or line['text'] for line in old]
    new_text = [line.get('section') or line['text'] for line in new]
    if old_text != new_text:
        phrase = 'editó la letra'
        matcher = SequenceMatcher(None, old_text, new_text, autojunk=False)
        touched = [start for tag, _, _, start, _ in matcher.get_opcodes() if tag != 'equal']
    else:
        phrase = 'cambió los acordes de la letra'
        touched = [index for index, line in enumerate(new) if line != old[index]]
    last = max(len(new) - 1, 0)
    parts = dict.fromkeys(lyric_part(new, min(index, last)) for index in touched)
    names = [name for name in parts if name]
    return [f'{phrase} de {", ".join(names)}' if names else phrase]


def meta_phrases(before, after):
    phrases = []
    if before['title'] != after['title']:
        phrases.append(f'renombró la canción a {after["title"]}')
    if before['status'] != after['status']:
        phrases.append(f'cambió el estado a {STATUS_LABELS[after["status"]]}')
    if before['tempo'] != after['tempo']:
        phrases.append(f'cambió el tempo a {after["tempo"]} bpm' if after['tempo'] else 'quitó el tempo')
    if before['time_signature'] != after['time_signature']:
        phrases.append(f'cambió el compás a {after["time_signature"]}' if after['time_signature'] else 'quitó el compás')
    if before['key'] != after['key'] or before['key_mode'] != after['key_mode']:
        phrases.append(f'cambió la tonalidad a {after["key"]}' if after['key'] else 'quitó la tonalidad')
    return phrases


def task_verb(old, new):
    if old['done'] != new['done']:
        return 'completó' if new['done'] else 'reabrió'
    return 'editó'


def revision_summary(section, before, after):
    if section == 'lyrics':
        phrases = lyric_phrases(before, after)
    elif section == 'meta':
        phrases = meta_phrases(before, after)
    elif section == 'chords':
        phrases = element_phrases(before, after, 'el acorde', lambda chord: chord['name'])
    elif section == 'tabs':
        phrases = element_phrases(before, after, 'la tablatura', lambda tab: tab.get('title') or 'sin título')
    else:
        phrases = element_phrases(before, after, 'la tarea', lambda task: task['title'], task_verb)
    summary = ', '.join(phrases) or f'actualizó {SECTION_LABELS[section]}'
    return summary if len(summary) <= SUMMARY_LENGTH else summary[:SUMMARY_LENGTH - 1] + '…'
