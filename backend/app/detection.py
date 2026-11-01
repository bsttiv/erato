"""Pure implementation of the author's chord/key algorithm (decision 08).

Gap choices: complete voicings win; the only inferred omission, besides the
approved dyads, is the perfect fifth of a chord that keeps its third and at least
one more tone. Extensions stack thirds through 9, 11 and 13. The single quality
table below stores semitones AND diatonic degrees, so enharmonic costs count the
actual written chord tones (including double accidentals). Remaining ties use
catalog order, then ascending root pitch class. Alterations may decorate approved
qualities with a principal major/minor triad; no new base quality is inferred.
Theory reference: https://openmusictheory.github.io/triads.html
Extensions: https://musictheory.pugetsound.edu/mt21c/SeventhChordsIntroduction.html
"""
from functools import lru_cache
from itertools import combinations

# suffix, (semitone, diatonic degree) pairs. Root is always implicit (0, 1).
QUALITY_TABLE = (
    ('', ((4, 3), (7, 5))),
    ('m', ((3, 3), (7, 5))),
    ('dim', ((3, 3), (6, 5))),
    ('+', ((4, 3), (8, 5))),
    ('7', ((4, 3), (7, 5), (10, 7))),
    ('maj7', ((4, 3), (7, 5), (11, 7))),
    ('m7', ((3, 3), (7, 5), (10, 7))),
    ('6', ((4, 3), (7, 5), (9, 6))),
    ('m7b5', ((3, 3), (6, 5), (10, 7))),
    ('dim7', ((3, 3), (6, 5), (9, 7))),
    ('sus2', ((2, 2), (7, 5))),
    ('sus4', ((5, 4), (7, 5))),
    ('add9', ((4, 3), (7, 5), (2, 9))),
    ('9', ((4, 3), (7, 5), (10, 7), (2, 9))),
    ('maj9', ((4, 3), (7, 5), (11, 7), (2, 9))),
    ('m9', ((3, 3), (7, 5), (10, 7), (2, 9))),
    ('11', ((4, 3), (7, 5), (10, 7), (2, 9), (5, 11))),
    ('m11', ((3, 3), (7, 5), (10, 7), (2, 9), (5, 11))),
    ('13', ((4, 3), (7, 5), (10, 7), (2, 9), (5, 11), (9, 13))),
    ('5', ((7, 5),)),
    ('(no5)', ((4, 3),)),
    ('m(no5)', ((3, 3),)),
)
# Fallback labels deliberately use the approved tension spelling for 1 and 6.
INTERVALS = ('1', 'b9', '9', 'b3', '3', '11', '#11', '5', 'b13', '13', 'b7', '7')
DEGREES = (1, 9, 9, 3, 3, 11, 11, 5, 13, 13, 7, 7)
ALTERATIONS = ((1, 9, 'b9'), (3, 9, '#9'), (6, 11, '#11'), (8, 13, 'b13'))
MAJOR_KEYS = ('C', 'G', 'D', 'A', 'E', 'B', 'F#', 'Db', 'Ab', 'Eb', 'Bb', 'F')
MINOR_KEYS = ('Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'Ebm', 'Bbm', 'Fm', 'Cm', 'Gm', 'Dm')
KEYS = MAJOR_KEYS + MINOR_KEYS
LETTERS = 'CDEFGAB'
NATURALS = (0, 2, 4, 5, 7, 9, 11)
MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)
MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10)


def _pitch(name):
    return (NATURALS[LETTERS.index(name[0])] + name.count('#') - name.count('b')) % 12


@lru_cache(maxsize=64)
def _scale(key):
    tonic = key.removesuffix('m')
    root = _pitch(tonic)
    steps = MINOR_SCALE if key.endswith('m') else MAJOR_SCALE
    start = LETTERS.index(tonic[0])
    return { (root + step) % 12: _letter_name((root + step) % 12, (start + i) % 7)
             for i, step in enumerate(steps) }


def _letter_name(pc, letter):
    delta = (pc - NATURALS[letter] + 6) % 12 - 6
    return LETTERS[letter] + ('#' * delta if delta > 0 else 'b' * -delta)


def _notes(notes):
    notes = tuple(notes)
    if any(type(n) is not int or not 0 <= n <= 127 for n in notes):
        raise ValueError('Notes must be MIDI integers from 0 through 127')
    pcs = frozenset(n % 12 for n in notes)
    if len(pcs) < 2:
        raise ValueError('A chord requires at least two distinct pitch classes')
    return pcs, min(notes) % 12


def _catalog():
    catalog = []
    for suffix, tones in QUALITY_TABLE:
        catalog.append((suffix, ((0, 1),) + tones, False))
    # Standard altered tensions replace their natural extension, if present.
    for suffix, tones in QUALITY_TABLE[:19]:
        semitones = {s for s, _ in tones}
        if not ({4, 7} <= semitones or {3, 7} <= semitones):
            continue
        for count in range(1, 5):
            for alterations in combinations(ALTERATIONS, count):
                if any(s in semitones for s, _, _ in alterations):
                    continue
                degrees = {d for _, d, _ in alterations}
                kept = tuple((s, d) for s, d in tones if d not in degrees)
                added = tuple((s, d) for s, d, _ in alterations)
                label = ','.join(label for _, _, label in alterations)
                catalog.append((suffix + '(' + label + ')', ((0, 1),) + kept + added, True))
    return catalog


def _without_fifth(catalog):
    # Same names as the complete chord; triads stay dyads, handled by (no5).
    result = []
    for suffix, tones, altered in catalog:
        has_third = (4, 3) in tones or (3, 3) in tones
        if (7, 5) in tones and has_third and len(tones) > 3:
            result.append((suffix, tuple(t for t in tones if t != (7, 5)), altered))
    return result


def _by_pitches(catalog):
    result = {}
    for root in range(12):
        for index, (suffix, tones, altered) in enumerate(catalog):
            pcs = frozenset((root + s) % 12 for s, _ in tones)
            result.setdefault(pcs, []).append((root, suffix, tones, altered, index))
    return result


CATALOG = _by_pitches(_catalog())
NO_FIFTH_CATALOG = _by_pitches(_without_fifth(_catalog()))


def _reading(pcs, bass, key):
    options = CATALOG.get(pcs) or NO_FIFTH_CATALOG.get(pcs, ())
    if not options:
        tones = tuple((s, DEGREES[s]) for s in sorted((p - bass) % 12 for p in pcs))
        suffix = '(' + ','.join(INTERVALS[s] for s, _ in tones if s) + ')'
        return bass, suffix, tones, True, -1
    scale = _scale(key)
    # All pitch classes must belong; root/degree spelling resolves symmetric
    # interpretations whose pitch membership alone cannot distinguish them.
    def rank(option):
        root, _, tones, _, index = option
        diatonic = pcs <= scale.keys() and root in scale
        if diatonic:
            letter = LETTERS.index(scale[root][0])
            diatonic = all(scale[(root + s) % 12][0] == LETTERS[(letter + d - 1) % 7]
                           for s, d in tones)
        return (root != bass, not diatonic, index, root)
    return min(options, key=rank)


@lru_cache(maxsize=16384)
def _spell(root, tones, key):
    scale = _scale(key)
    pcs = {(root + s) % 12 for s, _ in tones}
    if pcs <= scale.keys():
        return scale[root]
    prefer_sharps = '#' in key or key in {'G', 'D', 'A', 'E', 'B', 'Em', 'Bm'}
    choices = []
    for letter in range(7):
        name = _letter_name(root, letter)
        if len(name) > 2:
            continue
        cost = sum(len(_letter_name((root + s) % 12, (letter + d - 1) % 7)) - 1
                   for s, d in tones)
        choices.append((cost, ('b' in name) if prefer_sharps else ('#' in name), name))
    return min(choices)[2]


def name_chord(notes, key=None):
    """Name MIDI notes; bass is their minimum, never their list position.

    ``None`` uses C spelling when no candidate exists. Invalid input raises
    ValueError; translating that to HTTP 422 belongs to the future API layer.
    """
    pcs, bass = _notes(notes)
    key = key or 'C'
    _scale(key)  # Validate/resolve the selected key independently of MIDI order.
    root, suffix, tones, _, _ = _reading(pcs, bass, key)
    name = _spell(root, tones, key) + suffix
    if root != bass:
        scale = _scale(key)
        bass_name = scale.get(bass) or _spell(bass, ((0, 1),), key)
        name += '/' + bass_name
    return name


def _scoring_notes(pcs):
    # Scoring cannot depend on voicing/bass: duplicate pitch sets count once.
    root, _, tones, altered, index = _reading(pcs, min(pcs), 'C')
    if not altered:
        return pcs
    if index >= 0:
        return frozenset((root + s) % 12 for s, d in tones if d in {1, 3, 5})
    # Fallback intervals follow the same altered-tension rule; retain the
    # sounding principal tones, never invent missing third/fifth notes.
    if any(s in {1, 6, 8} for s, _ in tones):
        return frozenset((root + s) % 12 for s, d in tones if d in {1, 3, 5})
    return pcs


def candidate_keys(chords):
    """Return every maximum-score key, ordered by the four approved criteria."""
    distinct = {_notes(notes)[0] for notes in chords}
    if not distinct:
        return []
    scoring = [_scoring_notes(pcs) for pcs in distinct]
    scores = {key: sum(pcs <= _scale(key).keys() for pcs in scoring) for key in KEYS}
    maximum = max(scores.values())
    if maximum == 0:
        return []

    def rank(key):
        root = _pitch(key.removesuffix('m'))
        minor = key.endswith('m')
        harmonic = set()
        if minor:
            for offset, suffix in ((7, ''), (7, '7'), (11, 'dim'), (11, 'dim7'), (3, '+')):
                tones = next(tones for quality, tones in QUALITY_TABLE if quality == suffix)
                harmonic.add(frozenset((root + offset + s) % 12 for s in (0,) + tuple(s for s, _ in tones)))
        tonic = frozenset((root, (root + (3 if minor else 4)) % 12, (root + 7) % 12))
        tonic_present = any(
            tonic <= pcs and _reading(pcs, min(pcs), key)[0] == root
            for pcs in distinct
        )
        return (-len(harmonic & distinct), not tonic_present, minor,
                (MINOR_KEYS if minor else MAJOR_KEYS).index(key))

    return sorted((key for key in KEYS if scores[key] == maximum), key=rank)


def analyze(chords, key_mode='auto', selected_key=None):
    """Recalculate candidates/names and preserve or reset the previous key.

    selected_key is the previous selection, not a new user request. Validation
    of an explicit out-of-candidate auto choice belongs to the API boundary.
    """
    chords = list(chords)
    candidates = candidate_keys(chords)
    if key_mode not in {'auto', 'manual'}:
        raise ValueError('Key mode must be auto or manual')
    if key_mode == 'manual':
        if selected_key is None:
            raise ValueError('Manual mode requires a selected key')
        key = selected_key
    else:
        key = selected_key if selected_key in candidates else next(iter(candidates), None)
    return {'candidates': candidates, 'key': key,
            'names': [name_chord(notes, key) for notes in chords],
            'key_reset': key_mode == 'auto' and selected_key is not None and key != selected_key}
