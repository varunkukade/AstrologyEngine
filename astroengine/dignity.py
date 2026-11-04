"""Dignity, planetary relationships (natural / temporary / compound), avasthas,
combustion, planetary war, gandanta."""
from itertools import combinations
from .constants import (SIGNS, SIGN_LORD, GRAHAS, PLANETS, EXALT_POINT, OWN_SIGNS,
                        MOOLATRIKONA, NATURAL_FRIENDS, COMBUSTION_ORB,
                        COMBUSTION_ORB_RETRO, NAK_SPAN, MEAN_DAILY_MOTION)
from .chart import sign_of, deg_in_sign, house_from
from . import ephemeris as E

COMPOUND = {("friend", "friend"): "great_friend", ("friend", "enemy"): "neutral",
            ("neutral", "friend"): "friend", ("neutral", "enemy"): "enemy",
            ("enemy", "friend"): "neutral", ("enemy", "enemy"): "great_enemy"}


def exaltation_sign(p, config):
    if p in EXALT_POINT:
        return sign_of(EXALT_POINT[p])
    if config.node_exaltation == "taurus_scorpio":
        return {"Rahu": 1, "Ketu": 7}.get(p)
    if config.node_exaltation == "gemini_sagittarius":
        return {"Rahu": 2, "Ketu": 8}.get(p)
    raise ValueError("node_exaltation must be 'taurus_scorpio' or 'gemini_sagittarius'")


def debilitation_sign(p, config):
    e = exaltation_sign(p, config)
    return None if e is None else (e + 6) % 12


def natural_relation(p, q):
    f, n, e = NATURAL_FRIENDS[p]
    if q in f:
        return "friend"
    if q in e:
        return "enemy"
    return "neutral"


def temporary_relation(chart, p, q):
    """Tatkalika: q in 2,3,4,10,11,12 from p (by sign) is a temporary friend."""
    h = house_from(chart.sign(q), chart.sign(p))
    return "friend" if h in (2, 3, 4, 10, 11, 12) else "enemy"


def compound_relationships(chart):
    out = {}
    for p in PLANETS:
        out[p] = {}
        for q in PLANETS:
            if q == p:
                continue
            out[p][q] = COMPOUND[(natural_relation(p, q), temporary_relation(chart, p, q))]
    return out


def relationship_tables(chart):
    return {
        "natural": {p: {q: natural_relation(p, q) for q in PLANETS if q != p} for p in PLANETS},
        "temporary": {p: {q: temporary_relation(chart, p, q) for q in PLANETS if q != p}
                      for p in PLANETS},
        "compound": compound_relationships(chart),
    }


def rasi_dignity(p, lon, compound, config):
    """Degree-aware D1 dignity. Moon in Taurus: 0-3 exalted, 3-30 moolatrikona.
    Mercury in Virgo: 0-15 exalted, 15-20 moolatrikona, 20-30 own."""
    s, d = sign_of(lon), deg_in_sign(lon)
    if p == "Moon" and s == 1:
        return "exalted" if d < 3 else "moolatrikona"
    if p == "Mercury" and s == 5:
        return "exalted" if d < 15 else ("moolatrikona" if d < 20 else "own")
    if s == exaltation_sign(p, config):
        return "exalted"
    if s == debilitation_sign(p, config):
        return "debilitated"
    if p in MOOLATRIKONA:
        ms, lo, hi = MOOLATRIKONA[p]
        if s == ms and lo <= d < hi:
            return "moolatrikona"
    if s in OWN_SIGNS.get(p, []):
        return "own"
    lord = SIGN_LORD[s]
    if lord == p:
        return "own"
    return compound[p][lord]


def varga_dignity(p, s, compound, config):
    """Sign-only dignity inside a divisional chart."""
    if s == exaltation_sign(p, config):
        return "exalted"
    if s == debilitation_sign(p, config):
        return "debilitated"
    if s in OWN_SIGNS.get(p, []):
        return "own"
    return compound[p][SIGN_LORD[s]]


def exaltation_strength(p, lon):
    """Uchcha bala in virupas: arc from the debilitation point / 3 (0-60)."""
    if p not in EXALT_POINT:
        return None
    return E.angdist(lon, EXALT_POINT[p] + 180.0) / 3.0


# ---------------------------------------------------------------- avasthas
BALADI = ["Bala (infant)", "Kumara (youth)", "Yuva (adult)", "Vriddha (old)", "Mrita (dead)"]


def baladi(lon):
    i = min(int(deg_in_sign(lon) // 6), 4)
    return BALADI[i] if sign_of(lon) % 2 == 0 else BALADI[4 - i]


def jagradadi(dignity):
    if dignity in ("exalted", "own", "moolatrikona"):
        return "Jagrat (awake)"
    if dignity in ("great_friend", "friend", "neutral"):
        return "Swapna (dreaming)"
    return "Sushupti (sleeping)"


DEEPTADI = {"exalted": "Deepta", "moolatrikona": "Swastha", "own": "Swastha",
            "great_friend": "Mudita", "friend": "Shanta", "neutral": "Deena",
            "enemy": "Duhkhita", "great_enemy": "Khala", "debilitated": "Khala"}


def deeptadi(dignity, combust):
    """Deeptadi avastha from sign dignity (Phaladeepika ch.3 as commonly tabulated);
    a combust planet is Vikala whatever its sign. Lists of these states differ
    between Phaladeepika and Saravali; the dignity used is reported alongside."""
    return {"state": "Vikala" if combust else DEEPTADI[dignity], "by_sign_dignity": DEEPTADI[dignity],
            "vikala_combust": bool(combust)}


# ---------------------------------------------------------------- conditions
def combustion(chart):
    sun = chart.pos["Sun"]
    out = {}
    for p, orb in COMBUSTION_ORB.items():
        retro = chart.planets[p]["speed"] < 0
        lim = COMBUSTION_ORB_RETRO[p] if (retro and p in COMBUSTION_ORB_RETRO) else orb
        sep = E.angdist(chart.pos[p], sun)
        out[p] = {"combust": sep <= lim, "distance_from_sun": sep, "orb_used": lim}
    return out


def planetary_war(chart):
    """Graha yuddha: two of Mars/Mercury/Jupiter/Venus/Saturn within 1 degree.
    The winner rule differs between texts, so the deciding data is reported."""
    wars = []
    for a, b in combinations(["Mars", "Mercury", "Jupiter", "Venus", "Saturn"], 2):
        sep = E.angdist(chart.pos[a], chart.pos[b])
        if sep < 1.0:
            la, lb = chart.planets[a]["lat"], chart.planets[b]["lat"]
            ma, mb = E.magnitude(chart.jd, a), E.magnitude(chart.jd, b)
            wars.append({"planets": [a, b], "separation": sep,
                         "ecliptic_latitude": {a: la, b: lb},
                         "declination": {a: chart.planets[a]["dec"], b: chart.planets[b]["dec"]},
                         "apparent_magnitude": {a: ma, b: mb},
                         "northern_planet": a if la > lb else b,
                         "brighter_planet": a if ma < mb else b})
    return wars


GANDANTA_JUNCTIONS = [120.0, 240.0, 0.0]   # Ashlesha|Magha, Jyeshtha|Mula, Revati|Ashwini


def gandanta(lon):
    """Within one nakshatra pada (3deg20') either side of a water-fire junction."""
    for j in GANDANTA_JUNCTIONS:
        d = E.angdiff(lon, j)
        if abs(d) <= NAK_SPAN / 4.0:
            return {"gandanta": True, "junction": SIGNS[int(j // 30) % 12] + " 0°",
                    "degrees_from_junction": d}
    return {"gandanta": False}


def sandhi(lon):
    d = deg_in_sign(lon)
    return min(d, 30.0 - d)


def planet_details(chart, compound):
    comb = combustion(chart)
    out = {}
    for p in PLANETS:
        lon = chart.pos[p]
        pl = chart.planets[p]
        dg = rasi_dignity(p, lon, compound, chart.config)
        mean = MEAN_DAILY_MOTION[p]
        out[p] = {
            "dignity": dg,
            "uchcha_bala_virupas": exaltation_strength(p, lon),
            "retrograde": pl["speed"] < 0,
            "speed_deg_per_day": pl["speed"],
            "speed_vs_mean": pl["speed"] / mean,
            "combustion": comb.get(p),
            "baladi_avastha": baladi(lon),
            "jagradadi_avastha": jagradadi(dg),
            "deeptadi_avastha": deeptadi(dg, (comb.get(p) or {}).get("combust", False)),
            "gandanta": gandanta(lon),
            "degrees_from_sign_boundary": sandhi(lon),
            "whole_sign_house": chart.house(p),
            "bhava_house_sripati": chart.bhava_of(lon),
            "houses_ruled": chart.houses_ruled(p) if p in GRAHAS else [],
        }
    return out
