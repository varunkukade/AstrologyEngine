"""Core sidereal chart: planets, ascendant, whole-sign and Sripati bhavas,
optional Placidus (for KP)."""
from . import ephemeris as E
from .constants import (SIGNS, SIGN_LORD, NAKSHATRAS, NAK_SPAN, PADA_SPAN, PLANETS,
                        OUTER, QUALITY, ELEMENT)
from .config import DEFAULT


def sign_of(lon):
    return int((lon % 360.0) // 30.0) % 12


def deg_in_sign(lon):
    return lon % 30.0


def dms(x):
    """Degrees -> D°MM'SS" (rounded to whole arc-seconds, never shows 60)."""
    neg = x < 0
    total = int(round(abs(x) * 3600))
    d, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{'-' if neg else ''}{d}°{m:02d}'{s:02d}\""


def house_from(sign, ref_sign):
    return ((sign - ref_sign) % 12) + 1


def nakshatra_of(lon):
    lon %= 360.0
    idx = int(lon // NAK_SPAN) % 27
    within = lon - idx * NAK_SPAN
    pada = min(int(within // PADA_SPAN), 3) + 1
    name, lord, deity, gana, yoni, nadi = NAKSHATRAS[idx]
    return {"index": idx, "number": idx + 1, "name": name, "lord": lord, "pada": pada,
            "deity": deity, "gana": gana, "yoni": yoni, "nadi": nadi,
            "fraction_elapsed": within / NAK_SPAN}


def position_summary(lon):
    s = sign_of(lon)
    return {"longitude": lon, "sign": SIGNS[s], "sign_index": s,
            "degree_in_sign": deg_in_sign(lon), "dms": dms(deg_in_sign(lon)),
            "sign_lord": SIGN_LORD[s], "nakshatra": nakshatra_of(lon)}


class Chart:
    def __init__(self, birth, config=DEFAULT, ayanamsa=None, placidus=False):
        self.birth = birth
        self.config = config
        self.ayanamsa_name = ayanamsa or config.ayanamsa
        self.jd = birth.jd_ut
        E.init()
        self.ayanamsa = E.ayanamsa_value(self.jd, self.ayanamsa_name)

        names = list(PLANETS) + (list(OUTER) if config.include_outer_planets else [])
        self.planets = {}
        for n in names:
            p = E.body_position(self.jd, n, self.ayanamsa_name, config.node, config.allow_moshier)
            p["retrograde"] = p["speed"] < 0
            self.planets[n] = p
        self.pos = {n: p["lon"] for n, p in self.planets.items()}

        # Porphyry cusps = Sripati bhava madhyas; sandhis are their midpoints.
        cusps, asc, mc, armc, _ = E.houses(self.jd, birth.lat, birth.lon, "O", self.ayanamsa_name)
        self.asc, self.mc, self.armc = asc, mc, armc
        self.lagna = sign_of(asc)
        self.bhava_madhya = cusps
        self.bhava_sandhi = [(cusps[i - 1] + E.angdiff(cusps[i], cusps[i - 1]) / 2.0) % 360.0
                             for i in range(12)]   # sandhi[i] = start of bhava i+1

        self.placidus = None
        self.placidus_system = None
        if placidus:
            pc, _, _, _, used = E.houses(self.jd, birth.lat, birth.lon, "P", self.ayanamsa_name)
            self.placidus, self.placidus_system = pc, used

    # ---- placements
    def sign(self, p):
        return sign_of(self.pos[p])

    def house(self, p):
        """Whole-sign house from lagna."""
        return house_from(sign_of(self.pos[p]), self.lagna)

    def house_from_sign(self, p, ref_sign):
        return house_from(sign_of(self.pos[p]), ref_sign)

    def bhava_of(self, lon):
        return cusp_house(lon, self.bhava_sandhi)

    def placidus_house(self, lon):
        return cusp_house(lon, self.placidus)

    def occupants(self, sign):
        return [p for p in PLANETS if sign_of(self.pos[p]) == sign]

    def lord_of_house(self, h):
        return SIGN_LORD[(self.lagna + h - 1) % 12]

    def houses_ruled(self, planet):
        return [h for h in range(1, 13) if self.lord_of_house(h) == planet]


def cusp_house(lon, starts):
    """House (1-12) whose arc [starts[i], starts[i+1]) contains lon."""
    lon %= 360.0
    for i in range(12):
        a, b = starts[i], starts[(i + 1) % 12]
        span = (b - a) % 360.0
        if (lon - a) % 360.0 < span:
            return i + 1
    return 1


def sign_info(i):
    return {"sign": SIGNS[i], "index": i, "lord": SIGN_LORD[i],
            "quality": QUALITY[i % 3], "element": ELEMENT[i % 4],
            "odd": i % 2 == 0}
