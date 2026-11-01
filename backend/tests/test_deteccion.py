"""Author-approved DET cases from decisiones/08-acordes-y-tonalidad.md."""
from itertools import combinations

import pytest

from app.detection import KEYS, analyze, candidate_keys, name_chord

TRIADS = dict(zip(
    'C Cm C+ Db D Dm E Em F Fm F# G G#dim Ab A Am Bb Bbm'.split(),
    [[48,52,55], [48,51,55], [48,52,56], [49,53,56], [50,54,57],
     [50,53,57], [40,44,47], [52,55,59], [41,45,48], [41,44,48],
     [42,46,49], [43,47,50], [44,47,50], [44,48,51], [45,49,52],
     [45,48,52], [46,50,53], [46,49,53]],
))
NAME_CASES = [
    (1, [48,52,55], 'C', 'C'), (2, [45,48,52], 'C', 'Am'),
    (3, [47,50,53], 'C', 'Bdim'), (4, [48,52,56], 'Am', 'C+'),
    (5, [43,47,50,53], 'C', 'G7'), (6, [48,52,55,59], 'C', 'Cmaj7'),
    (7, [45,48,52,55], 'C', 'Am7'), (8, [48,52,55,57], 'C', 'C6'),
    (9, [55,48,52], 'C', 'C'), (10, [48,52,55,60,64], 'C', 'C'),
    (11, [52,55,60], 'C', 'C/E'), (12, [48,49,54], 'C', 'C(b9,#11)'),
    (14, [42,45,48], 'G', 'F#dim'), (15, [42,46,49], 'B', 'F#'),
    (16, [42,46,49], 'Db', 'Gb'), (17, [49,53,56], 'F#', 'C#'),
    (18, [49,53,56], 'Ab', 'Db'), (19, [44,48,51], 'C', 'Ab'),
    (20, [48,52,56], 'Fm', 'C+'), (21, [48,52,55,57], 'Am', 'C6'),
    (109, [40,44,47,50], 'Am', 'E7'),
    (109, [44,47,50,53], 'Am', 'G#dim7'),
    (126, [43,47,50,53,56], 'C', 'G7(b9)'),
    (126, [48,52,55,58,66], 'C', 'C7(#11)'),
    (127, [48,52,55,59,62], 'C', 'Cmaj9'),
    (128, [48,52,55,58,62], 'C', 'C9'),
    (24, [48,55], 'C', 'C5'), (25, [48,52], 'C', 'C(no5)'),
    (26, [48,51], 'Cm', 'Cm(no5)'), (27, [48,54], 'C', 'C(#11)'),
    (28, [40,55,56,62], 'C', 'E7(#9)'), (29, [48,64,70], 'C', 'C7'),
    (30, [48,64,71], 'C', 'Cmaj7'), (31, [48,63,70], 'C', 'Cm7'),
    (32, [48,64,70,74], 'C', 'C9'), (33, [52,60,70], 'C', 'C7/E'),
    (34, [48,64,69], 'C', 'Am/C'), (35, [48,67,71], 'C', 'C(5,7)'),
]


@pytest.mark.parametrize('case,notes,key,expected', NAME_CASES,
                         ids=[f'DET-{c[0]:03}' for c in NAME_CASES])
def test_DET_names(case, notes, key, expected):
    assert name_chord(notes, key) == expected


def test_DET_022():
    for notes in ([60], [48,60]):
        with pytest.raises(ValueError):
            name_chord(notes, 'C')


def test_DET_023():
    for _ in range(100):
        for case, notes, key, expected in NAME_CASES:
            if case <= 18:
                assert name_chord(notes, key) == expected


def test_DET_013():
    for size in range(2, 13):
        for pcs in combinations(range(12), size):
            for bass in pcs:
                notes = [36 + bass] + [60 + pc for pc in pcs]
                for key in KEYS:
                    result = name_chord(notes, key)
                    assert result and result.lower() not in {'unknown', 'desconocido', '?'}
                    assert result.isascii()


KEY_CASES = [
    (101, '', ''), (102, 'C', 'C G F Am Em Dm'),
    (103, 'Am', 'Am C G F Em Dm'), (104, 'C F G', 'C Am'),
    (105, 'Am F G', 'Am C'), (106, 'C F G E', 'Am C'),
    (107, 'C G D', 'G Em'), (108, 'Dm Em', 'C Am'),
    (109, 'Am E', 'Am E C G A B F Em F#m C#m G#m Dm'),
    (110, 'C Cm G Ab', 'Cm Fm C G Ab Eb Am Em'),
    (111, 'C Cm C+ G Db', 'Fm Am C G Ab Em'),
    (112, 'C F', 'C F Am Dm'), (113, 'F#', 'F# B Db G#m Ebm Bbm'),
    (114, 'C F G Ab', 'C Am'), (115, 'C F G Am D', 'C G Am Em'),
    (116, 'C F', 'C F Am Dm'), (117, 'C F E', 'Am C F Dm'),
    (118, 'F# Ab', 'Db Bbm'), (119, 'Fm Bbm C+', 'Fm Bbm Db Ab'),
    (120, 'Am C+', 'Am C G F Em Dm'), (121, 'G C F', 'C Am'),
    (123, 'Bb Bb A E', 'A E F#m C#m'), (124, 'C+', ''),
    (125, 'G7 C', 'C Am'), (126, 'G7(b9) C', 'C G Am Em'),
    (127, 'Cmaj9', 'C G Am Em'), (128, 'C9', 'F Dm'),
    (36, 'C F G7no5', 'C Am'),
]
TRIADS.update({'G7': [43,47,50,53], 'G7(b9)': [43,47,50,53,56],
               'Cmaj9': [48,52,55,59,62], 'C9': [48,52,55,58,62],
               'G7no5': [43,47,53]})


def chords(symbols):
    return [TRIADS[s] for s in symbols.split()]


@pytest.mark.parametrize('case,symbols,expected', KEY_CASES,
                         ids=[f'DET-{c[0]}' for c in KEY_CASES])
def test_DET_candidates(case, symbols, expected):
    assert candidate_keys(chords(symbols)) == expected.split()


def test_DET_122():
    for _ in range(100):
        for case, symbols, expected in KEY_CASES:
            if case <= 121:
                assert candidate_keys(chords(symbols)) == expected.split()


ANALYSIS_CASES = [
    (201, 'C F G E', 'auto', None, 'Am C', 'Am', 'C F G E', False),
    (202, 'F#', 'auto', None, 'F# B Db G#m Ebm Bbm', 'F#', 'F#', False),
    (203, 'F#', 'auto', 'Db', 'F# B Db G#m Ebm Bbm', 'Db', 'Gb', False),
    (204, 'F#', 'auto', 'Ebm', 'F# B Db G#m Ebm Bbm', 'Ebm', 'Gb', False),
    (205, 'F#', 'auto', 'G#m', 'F# B Db G#m Ebm Bbm', 'G#m', 'F#', False),
    (206, 'F# Ab', 'auto', 'F#', 'Db Bbm', 'Db', 'Gb Ab', True),
    (207, 'C F G', 'auto', None, 'C Am', 'C', 'C F G', False),
    (208, 'C F G', 'manual', 'D', 'C Am', 'D', 'C F G', False),
    (209, 'F# Db', 'manual', 'F#', 'F# Db Ebm Bbm', 'F#', 'F# C#', False),
    (210, 'F# Db', 'manual', 'Db', 'F# Db Ebm Bbm', 'Db', 'Gb Db', False),
    (211, '', 'manual', 'D', '', 'D', '', False),
    (212, '', 'auto', None, '', None, '', False),
    (213, 'C F G E', 'auto', 'C', 'Am C', 'C', 'C F G E', False),
    (214, 'C D G', 'auto', 'Am', 'G Em', 'G', 'C D G', True),
    (215, 'C D G', 'auto', 'D', 'G Em', 'G', 'C D G', True),
    (215, 'D', 'auto', 'D', 'D G A Em Bm F#m', 'D', 'D', False),
    (212, 'C', 'auto', None, 'C G F Am Em Dm', 'C', 'C', False),
    (124, 'C+', 'auto', None, '', None, 'C+', False),
]


@pytest.mark.parametrize('case,symbols,mode,selected,candidates,key,names,reset',
                         ANALYSIS_CASES, ids=[f'DET-{c[0]}' for c in ANALYSIS_CASES])
def test_DET_analysis(case, symbols, mode, selected, candidates, key, names, reset):
    assert analyze(chords(symbols), mode, selected) == {
        'candidates': candidates.split(), 'key': key, 'names': names.split(),
        'key_reset': reset,
    }
