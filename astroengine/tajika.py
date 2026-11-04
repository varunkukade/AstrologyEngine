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
    vb = _shift_birth(natal.birth, jd)
    vc = Chart(vb, natal.config)
    day = from_day_cls(vc)
    muntha = (natal.lagna + age) % 12
    dina_ratri = None
    if day.is_day is not None:
        dina_ratri = SIGN_LORD[vc.sign("Sun")] if day.is_day else SIGN_LORD[vc.sign("Moon")]
    return {
        "age_completed": age, "solar_return_time": iso(jd, natal.birth.local.tzinfo),
        "location": "birth place",
        "varsha_lagna": {"sign": SIGNS[vc.lagna], "dms": dms(vc.asc % 30), "longitude": vc.asc},
        "planets": {p: {"sign": SIGNS[vc.sign(p)], "dms": dms(vc.pos[p] % 30),
                        "longitude": vc.pos[p], "house": vc.house(p),
                        "retrograde": vc.planets[p]["speed"] < 0} for p in vc.pos},
        "muntha": {"sign": SIGNS[muntha], "house_in_varsha": house_from(muntha, vc.lagna),
                   "lord": SIGN_LORD[muntha]},
        "office_holders": {"muntha_lord": SIGN_LORD[muntha],
                           "janma_lagna_lord": SIGN_LORD[natal.lagna],
                           "varsha_lagna_lord": SIGN_LORD[vc.lagna],
                           "dina_ratri_pati": dina_ratri,
                           "note": "tri-rashi pati and the year-lord selection need Tajika "
                                   "strength tables and are not computed"},
        "solar_return_birth_in_daytime": day.is_day,
        "tajika_aspects": tajika_aspects(vc),
    }
