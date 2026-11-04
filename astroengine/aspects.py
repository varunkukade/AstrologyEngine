"""Graha drishti (sign-based and degree-based virupas), Jaimini rashi drishti, argala."""
from .constants import SIGNS, PLANETS, GRAHAS
from .chart import sign_of, house_from
from . import ephemeris as E

SPECIAL = {"Mars": [4, 7, 8], "Jupiter": [5, 7, 9], "Saturn": [3, 7, 10]}


def aspect_houses(planet, config):
    if planet in SPECIAL:
        return SPECIAL[planet]
    if planet in ("Rahu", "Ketu"):
        return [5, 7, 9] if config.node_aspects == "5_7_9" else [7]
    return [7]


def graha_drishti(chart):
    """Sign-based full aspects (BPHS ch.26)."""
    out = {}
    for p in PLANETS:
        s = chart.sign(p)
        hs = aspect_houses(p, chart.config)
        signs = [(s + h - 1) % 12 for h in hs]
        out[p] = {
            "aspects_houses_from_itself": hs,
            "aspects_signs": [SIGNS[x] for x in signs],
            "aspects_houses_from_lagna": [house_from(x, chart.lagna) for x in signs],
            "aspects_planets": [q for q in PLANETS if q != p and chart.sign(q) in signs],
        }
    aspected_by = {SIGNS[i]: [p for p in PLANETS
                              if SIGNS[i] in out[p]["aspects_signs"]] for i in range(12)}
    return {"by_planet": out, "signs_aspected_by": aspected_by}


def aspects_sign(chart, p, sign):
    s = chart.sign(p)
    return any((s + h - 1) % 12 == sign for h in aspect_houses(p, chart.config))


def virupa(aspecting, from_lon, to_lon):
    """Drishti strength in virupas (0-60), BPHS ch.26 formula on the arc from the
    aspecting body to the aspected point. Special aspects of Mars (4th, 8th),
    Jupiter (5th, 9th) and Saturn (3rd, 10th) are full (60) over that 30-degree arc."""
    d = (to_lon - from_lon) % 360.0
    special = {"Mars": [(90, 120), (210, 240)], "Jupiter": [(120, 150), (240, 270)],
               "Saturn": [(60, 90), (270, 300)]}.get(aspecting, [])
    for a, b in special:
        if a <= d < b:
            return 60.0
    if d < 30 or d >= 300:
        return 0.0
    if d < 60:
        return (d - 30) / 2.0
    if d < 90:
        return d - 60 + 15.0
    if d < 120:
        return (120 - d) / 2.0 + 30.0
    if d < 150:
        return 150.0 - d
    if d < 180:
        return (d - 150) * 2.0
    return (300.0 - d) / 2.0


def virupa_matrix(chart):
    return {p: {q: round(virupa(p, chart.pos[p], chart.pos[q]), 3)
                for q in GRAHAS if q != p} for p in GRAHAS}


def rashi_drishti_signs(s):
    """Jaimini sign aspects: movable -> fixed except the adjacent one;
    fixed -> movable except the adjacent one; dual -> the other duals."""
    q = s % 3
    if q == 0:
        return [t for t in range(12) if t % 3 == 1 and t != (s + 1) % 12]
    if q == 1:
        return [t for t in range(12) if t % 3 == 0 and t != (s - 1) % 12]
    return [t for t in range(12) if t % 3 == 2 and t != s]


def rashi_drishti(chart):
    out = {}
    for s in range(12):
        tgt = rashi_drishti_signs(s)
        out[SIGNS[s]] = {"aspects_signs": [SIGNS[t] for t in tgt],
                         "planets_aspected": [p for p in PLANETS if chart.sign(p) in tgt]}
    planets = {p: {"aspects_signs": out[SIGNS[chart.sign(p)]]["aspects_signs"],
                   "aspects_planets": [q for q in out[SIGNS[chart.sign(p)]]["planets_aspected"]
                                       if q != p]} for p in PLANETS}
    return {"by_sign": out, "by_planet": planets}


ARGALA = {2: 12, 4: 10, 11: 3, 5: 9}     # argala house -> its obstruction (virodha)


def argala(chart):
    """Occupants causing argala on, and obstructing it for, each house from lagna.
    Reported raw (no strength comparison), counted forward for every planet."""
    out = {}
    for h in range(1, 13):
        base = (chart.lagna + h - 1) % 12
        row = {}
        for a, v in ARGALA.items():
            pa = chart.occupants((base + a - 1) % 12)
            pv = chart.occupants((base + v - 1) % 12)
            row[f"from_{a}"] = {"argala_planets": pa, "virodha_house": v, "virodha_planets": pv,
                                "unobstructed": len(pa) > len(pv)}
        out[h] = row
    return out
