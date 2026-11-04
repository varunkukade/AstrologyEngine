"""Tajika annual chart (Varshaphala): sidereal solar return, Muntha, the
office-holders that do not need Tajika strength tables, and Tajika aspects
with Ithasala (applying) / Ishrafa (separating)."""
from dataclasses import replace
from itertools import combinations
from . import ephemeris as E
from .constants import SIGNS, SIGN_LORD, GRAHAS
from .chart import Chart, sign_of, house_from, dms
from .timeutil import utc_from_jd, iso

DEEPTAMSHA = {"Sun": 15, "Moon": 12, "Mars": 8, "Mercury": 7, "Jupiter": 9, "Venus": 7,
              "Saturn": 9}
TAJIKA_ASPECTS = {0: "conjunction", 60: "sextile", 90: "square", 120: "trine",
                  180: "opposition"}
SIDEREAL_YEAR = 365.256363


def solar_return_jd(natal, age):
    target = natal.pos["Sun"]
    guess = natal.jd + age * SIDEREAL_YEAR
    f = lambda t: E.sid_lon(t, "Sun", natal.ayanamsa_name)
    return E.find_crossing(f, guess - 4.0, target, 0.25, 8.0, forward=True)


def _shift_birth(birth, jd):
    utc = utc_from_jd(jd)
    return replace(birth, jd_ut=jd, utc=utc, local=utc.astimezone(birth.local.tzinfo),
                   warnings=[])


def tajika_aspects(c):
    out = []
    for a, b in combinations(GRAHAS, 2):
        sep = E.angdist(c.pos[a], c.pos[b])
        orb = (DEEPTAMSHA[a] + DEEPTAMSHA[b]) / 2.0
        for ang, name in TAJIKA_ASPECTS.items():
            dev = abs(sep - ang)
            if dev <= orb:
                dt = 0.01
                la = c.pos[a] + c.planets[a]["speed"] * dt
                lb = c.pos[b] + c.planets[b]["speed"] * dt
                dev2 = abs(E.angdist(la, lb) - ang)
                out.append({"planets": [a, b], "aspect": name, "orb": dev, "allowed_orb": orb,
                            "state": "ithasala (applying)" if dev2 < dev else "ishrafa (separating)"})
    return out


def varshaphala(natal, age, from_day_cls):
    jd = solar_return_jd(natal, age)
    try:
        jd_next = solar_return_jd(natal, age + 1)
    except E.EphemerisError:
        jd_next = None
    na = {"unavailable": "next solar return is outside the bundled ephemeris range"}
    vb = _shift_birth(natal.birth, jd)
    vc = Chart(vb, natal.config)
    day = from_day_cls(vc)
    muntha = (natal.lagna + age) % 12
    return {
        "age_completed": age, "solar_return_time": iso(jd, natal.birth.local.tzinfo),
        "next_solar_return_time": iso(jd_next, natal.birth.local.tzinfo) if jd_next else None,
        "location": "birth place",
        "varsha_lagna": {"sign": SIGNS[vc.lagna], "dms": dms(vc.asc % 30), "longitude": vc.asc},
        "planets": {p: {"sign": SIGNS[vc.sign(p)], "dms": dms(vc.pos[p] % 30),
                        "longitude": vc.pos[p], "house": vc.house(p),
                        "retrograde": vc.planets[p]["speed"] < 0} for p in vc.pos},
        "muntha": {"sign": SIGNS[muntha], "house_in_varsha": house_from(muntha, vc.lagna),
                   "lord": SIGN_LORD[muntha]},
        "solar_return_birth_in_daytime": day.is_day,
        "year_lord": year_lord(natal, vc, age, day.is_day),
        "tajika_aspects": tajika_aspects(vc),
        "sahams": sahams(vc, day.is_day),
        "mudda_dasha": mudda_dasha(natal, age, jd, jd_next) if jd_next else na,
        "patyayini_dasha": patyayini_dasha(vc, jd, jd_next) if jd_next else na,
    }


# ---------------------------------------------------------------- Tajika strength and year lord
from .constants import OWN_SIGNS, EXALT_POINT, VIM_ORDER, VIM_YEARS, NAK_SPAN
from .dignity import natural_relation
from .vargas import d3, d9

# Egyptian terms (hadda), each (lord, end degree). Checked: per-planet totals
# Jupiter 79, Venus 82, Mercury 76, Mars 66, Saturn 57.
HADDA = [
    [("Jupiter", 6), ("Venus", 12), ("Mercury", 20), ("Mars", 25), ("Saturn", 30)],
    [("Venus", 8), ("Mercury", 14), ("Jupiter", 22), ("Saturn", 27), ("Mars", 30)],
    [("Mercury", 6), ("Jupiter", 12), ("Venus", 17), ("Mars", 24), ("Saturn", 30)],
    [("Mars", 7), ("Venus", 13), ("Mercury", 19), ("Jupiter", 26), ("Saturn", 30)],
    [("Jupiter", 6), ("Venus", 11), ("Saturn", 18), ("Mercury", 24), ("Mars", 30)],
    [("Mercury", 7), ("Venus", 17), ("Jupiter", 21), ("Mars", 28), ("Saturn", 30)],
    [("Saturn", 6), ("Mercury", 14), ("Jupiter", 21), ("Venus", 28), ("Mars", 30)],
    [("Mars", 7), ("Venus", 11), ("Mercury", 19), ("Jupiter", 24), ("Saturn", 30)],
    [("Jupiter", 12), ("Venus", 17), ("Mercury", 21), ("Saturn", 26), ("Mars", 30)],
    [("Mercury", 7), ("Jupiter", 14), ("Venus", 22), ("Saturn", 26), ("Mars", 30)],
    [("Mercury", 7), ("Venus", 13), ("Jupiter", 20), ("Mars", 25), ("Saturn", 30)],
    [("Venus", 12), ("Jupiter", 16), ("Mercury", 19), ("Mars", 28), ("Saturn", 30)],
]


def _hadda_totals():
    tot = {}
    for row in HADDA:
        lo = 0
        for lord, hi in row:
            tot[lord] = tot.get(lord, 0) + hi - lo
            lo = hi
        assert lo == 30
    return tot


assert _hadda_totals() == {"Jupiter": 79, "Venus": 82, "Mercury": 76, "Mars": 66, "Saturn": 57}


def hadda_lord(lon):
    d = lon % 30
    for lord, hi in HADDA[sign_of(lon)]:
        if d < hi:
            return lord
    return HADDA[sign_of(lon)][-1][0]


TRI_RASHI_DAY = ["Sun", "Venus", "Saturn", "Venus", "Jupiter", "Moon", "Mercury", "Mars",
                 "Saturn", "Mars", "Jupiter", "Moon"]
TRI_RASHI_NIGHT = ["Jupiter", "Moon", "Mercury", "Mars", "Sun", "Venus", "Saturn", "Venus",
                   "Saturn", "Mars", "Jupiter", "Moon"]


def _rel_points(p, lord, own, friend, neutral, enemy):
    if lord == p:
        return own
    return {"friend": friend, "neutral": neutral, "enemy": enemy}[natural_relation(p, lord)]


def pancha_vargiya_bala(c):
    """Kshetra (own 30 / friend 22.5 / neutral 15 / enemy 7.5), Uchcha (0-20),
    Hadda (15/7.5/-/3.75), Drekkana (10/5/-/2.5), Navamsa (5/2.5/-/1.25), summed and
    divided by 4 (max 20). Values as given by P.V.R. Narasimha Rao; for the last
    three the neutral value is not stated and the friend/enemy midpoint is used,
    which reproduces the stated Kshetra pattern. Natural relationships."""
    out = {}
    for p in GRAHAS:
        lon = c.pos[p]
        s = sign_of(lon)
        k = 30.0 if s in OWN_SIGNS[p] else _rel_points(p, SIGN_LORD[s], 30, 22.5, 15, 7.5)
        u = E.angdist(lon, EXALT_POINT[p] + 180.0) / 9.0
        h = _rel_points(p, hadda_lord(lon), 15, 7.5, 5.625, 3.75)
        ds, ns = d3(lon), d9(lon)
        dk = 10.0 if ds in OWN_SIGNS[p] else _rel_points(p, SIGN_LORD[ds], 10, 5, 3.75, 2.5)
        nv = 5.0 if ns in OWN_SIGNS[p] else _rel_points(p, SIGN_LORD[ns], 5, 2.5, 1.875, 1.25)
        out[p] = {"kshetra": k, "uchcha": u, "hadda": h, "hadda_lord": hadda_lord(lon),
                  "drekkana": dk, "navamsa": nv, "total": (k + u + h + dk + nv) / 4.0}
    return out


def tajika_aspect_on(c, p, sign):
    """Sign-based Tajika aspect of planet p on a sign (2/6/8/12 have none)."""
    h = house_from(sign, c.sign(p))
    if h in (3, 5, 9, 11):
        return "friendly"
    if h in (1, 4, 7, 10):
        return "inimical" if h != 1 else "conjunction"
    return None


def year_lord(natal, vc, age, is_day):
    muntha = (natal.lagna + age) % 12
    offices = {"muntha_lord": SIGN_LORD[muntha], "janma_lagna_lord": SIGN_LORD[natal.lagna],
               "varsha_lagna_lord": SIGN_LORD[vc.lagna]}
    if is_day is not None:
        offices["tri_rashi_pati"] = (TRI_RASHI_DAY if is_day else TRI_RASHI_NIGHT)[vc.lagna]
        offices["dina_ratri_pati"] = SIGN_LORD[vc.sign("Sun")] if is_day else SIGN_LORD[vc.sign("Moon")]
    pvb = pancha_vargiya_bala(vc)
    cands = {}
    for office, p in offices.items():
        cands.setdefault(p, {"offices": [], "pancha_vargiya_bala": pvb[p]["total"],
                             "aspect_on_varsha_lagna": tajika_aspect_on(vc, p, vc.lagna)})
        cands[p]["offices"].append(office)
    asp = [p for p, v in cands.items() if v["aspect_on_varsha_lagna"]]
    pool = asp or list(cands)
    lord = max(pool, key=lambda p: (cands[p]["pancha_vargiya_bala"], len(cands[p]["offices"])))
    return {"year_lord": lord,
            "rule": ("strongest (pancha-vargiya bala) office-holder aspecting the varsha lagna"
                     if asp else "no office-holder aspects the varsha lagna; strongest of them taken"),
            "office_holders": offices, "candidates": cands, "pancha_vargiya_bala": pvb}


# ---------------------------------------------------------------- Sahams
# (name, A, B, C, reverse at night) -> A - B + C, +30 deg when C is not on the arc B->A.
SAHAMS = [
    ("Punya", "Moon", "Sun", "Asc", True), ("Vidya", "Sun", "Moon", "Asc", True),
    ("Yasas", "Jupiter", "Punya", "Asc", True), ("Mitra", "Jupiter", "Punya", "Venus", True),
    ("Mahatmya", "Punya", "Mars", "Asc", True), ("Asha", "Saturn", "Mars", "Asc", True),
    ("Bhratri", "Jupiter", "Saturn", "Asc", False), ("Pitri", "Saturn", "Sun", "Asc", True),
    ("Matri", "Moon", "Venus", "Asc", True), ("Putra", "Jupiter", "Moon", "Asc", True),
    ("Jeeva", "Saturn", "Jupiter", "Asc", True), ("Karma", "Mars", "Mercury", "Asc", True),
    ("Roga", "Asc", "Moon", "Asc", False), ("Kali", "Jupiter", "Mars", "Asc", True),
    ("Bandhu", "Mercury", "Moon", "Asc", True), ("Mrityu", "H8", "Moon", "Asc", False),
    ("Paradesa", "H9", "L9", "Asc", False), ("Artha", "H2", "L2", "Asc", False),
    ("Paradara", "Venus", "Sun", "Asc", True), ("Vanika", "Moon", "Mercury", "Asc", True),
    ("Vivaha", "Venus", "Saturn", "Asc", True), ("Shraddha", "Venus", "Mars", "Asc", True),
    ("Jadya", "Mars", "Saturn", "Mercury", True), ("Vyapara", "Mars", "Saturn", "Asc", False),
    ("Shatru", "Mars", "Saturn", "Asc", True), ("Jalapatana", "Cancer15", "Saturn", "Asc", True),
    ("Bandhana", "Punya", "Saturn", "Asc", True), ("Apamrityu", "H8", "Mars", "Asc", True),
]


def _between(c, b, a):
    """Is c on the zodiacal arc from b to a?"""
    return (c - b) % 360.0 <= (a - b) % 360.0


def sahams(c, is_day):
    night = is_day is False
    pts = dict(c.pos)
    pts.update({"Asc": c.asc, "H8": (c.asc + 210) % 360, "H9": (c.asc + 240) % 360,
                "H2": (c.asc + 30) % 360, "Cancer15": 105.0,
                "L9": c.pos[SIGN_LORD[(c.lagna + 8) % 12]], "L2": c.pos[SIGN_LORD[(c.lagna + 1) % 12]]})
    out = {}
    for name, A, B, C, rev in SAHAMS:
        if night and rev:
            A, B = B, A
        a, b, cc = pts[A], pts[B], pts[C]
        v = (a - b + cc) % 360
        corr = not _between(cc, b, a)
        if corr:
            v = (v + 30.0) % 360
        out[name] = {"longitude": v, "sign": SIGNS[sign_of(v)], "dms": dms(v % 30),
                     "formula": f"{A} - {B} + {C}" + (" + 30" if corr else "")}
        if name == "Punya":
            pts["Punya"] = v
    return {"sahams": out, "night_formulae_used": night,
            "rule": "A - B + C, with A and B swapped at night where the text reverses it; "
                    "30 deg added when C does not fall on the zodiacal arc from B to A"}


# ---------------------------------------------------------------- Mudda and Patyayini
MUDDA_DAYS = {"Ketu": 21, "Venus": 60, "Sun": 18, "Moon": 30, "Mars": 21, "Rahu": 54,
              "Jupiter": 48, "Saturn": 57, "Mercury": 51}
assert sum(MUDDA_DAYS.values()) == 360


def mudda_dasha(natal, age, jd0, jd1):
    """Varsha Vimshottari: Vimshottari order in a 360-unit year scaled to this
    solar year. First lord = birth-star lord advanced by the completed years
    ((nakshatra no. + years - 2) mod 9 from Sun, Tajika rule); balance as at birth."""
    tz = natal.birth.local.tzinfo
    unit = (jd1 - jd0) / 360.0
    moon = natal.pos["Moon"]
    nk = int(moon // NAK_SPAN) % 27
    frac = (moon % NAK_SPAN) / NAK_SPAN
    i0 = (nk + age) % 9
    t = jd0 - frac * MUDDA_DAYS[VIM_ORDER[i0]] * unit
    out = []
    for k in range(10):
        l = VIM_ORDER[(i0 + k) % 9]
        d = MUDDA_DAYS[l] * unit
        ads, ta = [], t
        for j in range(9):
            l2 = VIM_ORDER[(i0 + k + j) % 9]
            span = d * MUDDA_DAYS[l2] / 360.0
            ads.append({"lord": l2, "start": iso(ta, tz), "end": iso(ta + span, tz)})
            ta += span
        ads[-1]["end"] = iso(t + d, tz)
        out.append({"lord": l, "days": MUDDA_DAYS[l] * unit, "start": iso(t, tz),
                    "end": iso(t + d, tz), "antardashas": ads})
        t += d
        if t > jd1:
            break
    return out


def patyayini_dasha(vc, jd0, jd1):
    """Tajika Patyayini: lagna and the seven grahas sorted by degrees in sign;
    each period is proportional to its degree gap from the previous one."""
    tz = vc.birth.local.tzinfo
    pts = [("Lagna", vc.asc % 30)] + [(p, vc.pos[p] % 30) for p in GRAHAS]
    pts.sort(key=lambda x: x[1])
    arcs = [(pts[0][0], pts[0][1])] + [(pts[i][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts))]
    total = sum(a for _, a in arcs) or 1.0
    year = jd1 - jd0
    out, t = [], jd0
    for i, (p, a) in enumerate(arcs):
        d = year * a / total
        ads, ta = [], t
        for j in range(len(arcs)):
            q, b = arcs[(i + j) % len(arcs)]
            ads.append({"lord": q, "start": iso(ta, tz), "end": iso(ta + d * b / total, tz)})
            ta += d * b / total
        if ads:
            ads[-1]["end"] = iso(t + d, tz)
        out.append({"lord": p, "patyamsa_degrees": a, "days": d, "start": iso(t, tz),
                    "end": iso(t + d, tz), "antardashas": ads})
        t += d
    return out
