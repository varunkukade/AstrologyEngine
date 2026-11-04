"""Ashtakavarga (BPHS ch.66-69): BAV, SAV, prastara, kakshya, trikona and
ekadhipatya shodhana, shodhya pinda."""
from .constants import SIGNS, GRAHAS
from .chart import house_from

# target -> contributor -> houses (counted from the contributor) giving a bindu
BAV_TABLES = {
    "Sun": {"Sun": [1, 2, 4, 7, 8, 9, 10, 11], "Moon": [3, 6, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11], "Mercury": [3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [5, 6, 9, 11], "Venus": [6, 7, 12],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Lagna": [3, 4, 6, 10, 11, 12]},
    "Moon": {"Sun": [3, 6, 7, 8, 10, 11], "Moon": [1, 3, 6, 7, 10, 11],
             "Mars": [2, 3, 5, 6, 9, 10, 11], "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
             "Jupiter": [1, 4, 7, 8, 10, 11, 12], "Venus": [3, 4, 5, 7, 9, 10, 11],
             "Saturn": [3, 5, 6, 11], "Lagna": [3, 6, 10, 11]},
    "Mars": {"Sun": [3, 5, 6, 10, 11], "Moon": [3, 6, 11],
             "Mars": [1, 2, 4, 7, 8, 10, 11], "Mercury": [3, 5, 6, 11],
             "Jupiter": [6, 10, 11, 12], "Venus": [6, 8, 11, 12],
             "Saturn": [1, 4, 7, 8, 9, 10, 11], "Lagna": [1, 3, 6, 10, 11]},
    "Mercury": {"Sun": [5, 6, 9, 11, 12], "Moon": [2, 4, 6, 8, 10, 11],
                "Mars": [1, 2, 4, 7, 8, 9, 10, 11], "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
                "Jupiter": [6, 8, 11, 12], "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
                "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Lagna": [1, 2, 4, 6, 8, 10, 11]},
    "Jupiter": {"Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11], "Moon": [2, 5, 7, 9, 11],
                "Mars": [1, 2, 4, 7, 8, 10, 11], "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
                "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11], "Venus": [2, 5, 6, 9, 10, 11],
                "Saturn": [3, 5, 6, 12], "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11]},
    "Venus": {"Sun": [8, 11, 12], "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
              "Mars": [3, 5, 6, 9, 11, 12], "Mercury": [3, 5, 6, 9, 11],
              "Jupiter": [5, 8, 9, 10, 11], "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
              "Saturn": [3, 4, 5, 8, 9, 10, 11], "Lagna": [1, 2, 3, 4, 5, 8, 9, 11]},
    "Saturn": {"Sun": [1, 2, 4, 7, 8, 10, 11], "Moon": [3, 6, 11],
               "Mars": [3, 5, 6, 10, 11, 12], "Mercury": [6, 8, 9, 10, 11, 12],
               "Jupiter": [5, 6, 11, 12], "Venus": [6, 11, 12],
               "Saturn": [3, 5, 6, 11], "Lagna": [1, 3, 4, 6, 10, 11]},
}
BAV_TOTALS = {"Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54, "Jupiter": 56,
              "Venus": 52, "Saturn": 39}
for _t, _tab in BAV_TABLES.items():
    assert sum(len(v) for v in _tab.values()) == BAV_TOTALS[_t], _t

# Kakshya order within a sign (each 3deg45'), BPHS: slowest to fastest, then lagna.
KAKSHYA_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"]

RASHI_GUNAKARA = [7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12]
GRAHA_GUNAKARA = {"Sun": 5, "Moon": 5, "Mars": 8, "Mercury": 5, "Jupiter": 10,
                  "Venus": 7, "Saturn": 5}
SAME_LORD_PAIRS = [(0, 7), (1, 6), (2, 5), (8, 11), (9, 10)]


def _refs(chart):
    r = {p: chart.sign(p) for p in GRAHAS}
    r["Lagna"] = chart.lagna
    return r


def prastara(chart):
    """target -> contributor -> [0/1 per sign]."""
    ref = _refs(chart)
    out = {}
    for tgt, tab in BAV_TABLES.items():
        out[tgt] = {}
        for c in KAKSHYA_ORDER:
            row = [0] * 12
            for h in tab[c]:
                row[(ref[c] + h - 1) % 12] = 1
            out[tgt][c] = row
    return out


def bav_from_prastara(pr):
    return {t: [sum(pr[t][c][s] for c in KAKSHYA_ORDER) for s in range(12)] for t in pr}


def trikona_shodhana(bindus):
    b = list(bindus)
    for i in range(4):
        grp = [i, i + 4, i + 8]
        vals = [b[s] for s in grp]
        if 0 in vals:
            continue
        if vals[0] == vals[1] == vals[2]:
            for s in grp:
                b[s] = 0
        else:
            m = min(vals)
            for s in grp:
                b[s] -= m
    return b


def ekadhipatya_shodhana(bindus, occupied):
    """Applied after trikona shodhana, to the five pairs of signs sharing a lord.
    occupied: set of sign indices holding at least one of the seven grahas.
    Rules (B.V. Raman, Ashtakavarga System): both occupied -> no change; either
    value 0 -> no change; neither occupied -> equal values both cleared,
    unequal both set to the smaller; one occupied -> if the occupied sign has
    more or equal bindus the unoccupied one is cleared, if fewer the unoccupied
    one is reduced to the occupied sign's value."""
    b = list(bindus)
    for x, y in SAME_LORD_PAIRS:
        ox, oy = x in occupied, y in occupied
        vx, vy = b[x], b[y]
        if (ox and oy) or vx == 0 or vy == 0:
            continue
        if not ox and not oy:
            if vx == vy:
                b[x] = b[y] = 0
            else:
                b[x] = b[y] = min(vx, vy)
            continue
        occ, un = (x, y) if ox else (y, x)
        if b[occ] >= b[un]:
            b[un] = 0
        else:
            b[un] = b[occ]
    return b


def kakshya_of(lon):
    i = int((lon % 30.0) // 3.75)
    return {"index": i + 1, "lord": KAKSHYA_ORDER[i],
            "start_degree": i * 3.75, "end_degree": (i + 1) * 3.75}


def ashtakavarga(chart):
    pr = prastara(chart)
    bav = bav_from_prastara(pr)
    sav = [sum(bav[t][s] for t in bav) for s in range(12)]
    occupied = {chart.sign(p) for p in GRAHAS}
    reduced, pinda = {}, {}
    for t in GRAHAS:
        tri = trikona_shodhana(bav[t])
        eka = ekadhipatya_shodhana(tri, occupied)
        rp = sum(eka[s] * RASHI_GUNAKARA[s] for s in range(12))
        gp = sum(eka[chart.sign(g)] * GRAHA_GUNAKARA[g] for g in GRAHAS)
        reduced[t] = {"after_trikona": tri, "after_ekadhipatya": eka}
        pinda[t] = {"rashi_pinda": rp, "graha_pinda": gp, "shodhya_pinda": rp + gp}
    by_sign = lambda arr: {SIGNS[s]: arr[s] for s in range(12)}
    return {
        "bav": {t: by_sign(v) for t, v in bav.items()},
        "bav_totals": {t: sum(v) for t, v in bav.items()},
        "sav": by_sign(sav),
        "sav_total": sum(sav),
        "sav_by_house": {h: sav[(chart.lagna + h - 1) % 12] for h in range(1, 13)},
        "prastara": {t: {c: by_sign(row) for c, row in rows.items()} for t, rows in pr.items()},
        "shodhana": {t: {k: by_sign(v) for k, v in d.items()} for t, d in reduced.items()},
        "shodhya_pinda": pinda,
        "kakshya_order": KAKSHYA_ORDER,
        "_raw": {"bav": bav, "sav": sav, "prastara": pr},
    }
