"""Single entry point: compute(birth_dict) -> JSON-ready dict of every
astronomical and astrological factor. No interpretation, no predictions."""
import math
import os
from datetime import datetime, timezone
import swisseph as swe

from . import ephemeris as E
from .config import Config, DEFAULT
from .constants import SIGNS, PLANETS, OUTER, GRAHAS
from .timeutil import parse_birth, jd_from_utc, iso
from .chart import Chart, position_summary, dms, house_from, sign_info, nakshatra_of
from .dignity import (compound_relationships, relationship_tables, planet_details,
                      planetary_war)
from .vargas import all_vargas, vargottama, vimshopaka
from .panchanga import SolarDay, panchanga
from .special import special_lagnas, upagrahas
from .aspects import graha_drishti, virupa_matrix, rashi_drishti, argala
from .ashtakavarga import ashtakavarga
from .shadbala import shadbala
from .yogas import all_yogas
from .dashas import vimshottari, yogini, ashtottari, chara_dasha, narayana_dasha, kalachakra_dasha
from .jaimini import jaimini
from .kp import kp
from .transits import slow_planet_timeline, saturn_phases, snapshot
from .tajika import varshaphala
from .sensitivity import sensitivity

ENGINE_VERSION = "4.0.0"
SCHEMA_VERSION = "1"


def _clean(x, nd=6):
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return None
        return round(x, nd)
    if isinstance(x, dict):
        return {str(k): _clean(v, nd) for k, v in x.items() if not str(k).startswith("_raw")}
    if isinstance(x, (list, tuple, set)):
        return [_clean(v, nd) for v in x]
    return x


def compute(birth_data, config=DEFAULT, as_of=None, transit_years=100):
    """birth_data: see timeutil.parse_birth. as_of: aware datetime used for the
    transit snapshot, running dasha and current varshaphala (default: now)."""
    if isinstance(config, dict):
        config = Config(**config)
    E.ALLOW_MOSHIER = config.allow_moshier
    E.init()
    birth = parse_birth(birth_data)
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    ref_jd = jd_from_utc(as_of)

    c = Chart(birth, config)
    day = SolarDay(c)
    pan = panchanga(c, day)
    comp = compound_relationships(c)
    det = planet_details(c, comp)
    tz = birth.local.tzinfo

    planets = {}
    for p in PLANETS:
        pl = c.planets[p]
        planets[p] = {**position_summary(pl["lon"]), "latitude": pl["lat"],
                      "declination": pl["dec"], "right_ascension": pl["ra"],
                      "distance_au": pl["dist_au"], **det[p]}
    outer = {}
    for p in OUTER:
        if p in c.planets:
            pl = c.planets[p]
            outer[p] = {**position_summary(pl["lon"]), "retrograde": pl["speed"] < 0,
                        "whole_sign_house": c.house(p), "speed_deg_per_day": pl["speed"]}

    whole = []
    for h in range(1, 13):
        s = (c.lagna + h - 1) % 12
        whole.append({"house": h, **sign_info(s), "occupants": c.occupants(s)})
    bhava = [{"bhava": h + 1, "madhya": c.bhava_madhya[h], "madhya_dms": dms(c.bhava_madhya[h] % 30),
              "madhya_sign": SIGNS[int(c.bhava_madhya[h] // 30)],
              "start_sandhi": c.bhava_sandhi[h],
              "occupants": [p for p in PLANETS if c.bhava_of(c.pos[p]) == h + 1]}
             for h in range(12)]

    ashta = ashtakavarga(c)
    hora_lord = pan.get("hora", {}).get("lord")
    shad = shadbala(c, comp, day, hora_lord) if hora_lord else {
        "unavailable": "no sunrise/sunset at this latitude on the birth date"}

    timeline = slow_planet_timeline(c, transit_years)
    age_now = None
    if ref_jd > c.jd:
        from .tajika import solar_return_jd
        age_now = int((ref_jd - c.jd) / 365.256363)
        if age_now > 0 and solar_return_jd(c, age_now) > ref_jd:
            age_now -= 1
    varsha = None
    if age_now is not None and age_now >= 0:
        varsha = {"running": varshaphala(c, age_now, SolarDay),
                  "next": varshaphala(c, age_now + 1, SolarDay)}

    result = {
        "meta": {
            "engine": "astroengine", "engine_version": ENGINE_VERSION,
            "schema_version": SCHEMA_VERSION,
            "ephemeris": {"library": "Swiss Ephemeris", "pyswisseph": swe.version,
                          "files": sorted(os.listdir(E.EPHE_DIR)), "moshier_allowed": config.allow_moshier},
            "config": config.as_dict(),
            "as_of": as_of.isoformat(),
            "zodiac": "sidereal",
            "description": "Calculation output only. No interpretation or prediction is made.",
        },
        "birth": birth.as_dict(),
        "ayanamsa": {"name": c.ayanamsa_name, "value": c.ayanamsa, "dms": dms(c.ayanamsa)},
        "lagna": {**position_summary(c.asc), "whole_sign_index": c.lagna},
        "midheaven": position_summary(c.mc),
        "planets": planets,
        "outer_planets": outer or None,
        "planetary_war": planetary_war(c),
        "houses": {"whole_sign": whole, "bhava_sripati": bhava},
        "relationships": relationship_tables(c),
        "vargas": all_vargas(c),
        "vargottama": vargottama(c),
        "vimshopaka_bala": vimshopaka(c, comp),
        "panchanga": pan,
        "special_lagnas": special_lagnas(c, day),
        "upagrahas": upagrahas(c, day),
        "aspects": {"graha_drishti": graha_drishti(c), "drishti_virupas": virupa_matrix(c),
                    "rashi_drishti": rashi_drishti(c), "argala": argala(c)},
        "ashtakavarga": ashta,
        "shadbala": shad,
        "yogas": all_yogas(c, comp),
        "dashas": {"vimshottari": vimshottari(c, ref_jd), "yogini": yogini(c),
                   "ashtottari": ashtottari(c, day), "chara": chara_dasha(c),
                   "narayana": narayana_dasha(c), "kalachakra": kalachakra_dasha(c)},
        "jaimini": jaimini(c),
        "kp": kp(birth, config, day.vara),
        "transits": {"at_as_of": snapshot(c, ref_jd, ashta),
                     "slow_planets_lifetime": timeline,
                     "saturn_phases_from_moon": saturn_phases(c, timeline["Saturn"]["ingresses"],
                                                              transit_years)},
        "varshaphala": varsha,
        "birth_time_sensitivity": sensitivity(c),
        "warnings": list(birth.warnings),
    }
    return _clean(result)
