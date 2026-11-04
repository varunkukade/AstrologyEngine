"""Thin, strict wrapper over Swiss Ephemeris.

* Ephemeris files are bundled (astroengine/ephe, 1800-2399 CE). Every call checks
  the return flag and raises if Swiss Ephemeris silently fell back to Moshier.
* swe's sidereal mode is process-global, so every sidereal call sets it first.
"""
import os
import math
import swisseph as swe

EPHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ephe")
_initialised = False
ALLOW_MOSHIER = False      # set by compute() from Config.allow_moshier
# Coverage of the bundled files (sepl_18/semo_18), with a small safety margin.
RANGE_START_JD = swe.julday(1800, 1, 3, 0.0)
RANGE_END_JD = swe.julday(2399, 12, 29, 0.0)

AYANAMSA = {
    "lahiri": swe.SIDM_LAHIRI,
    "lahiri_icrc": swe.SIDM_LAHIRI_ICRC,
    "raman": swe.SIDM_RAMAN,
    "kp": swe.SIDM_KRISHNAMURTI,
    "kp_vp291": swe.SIDM_KRISHNAMURTI_VP291,
    "true_chitra": swe.SIDM_TRUE_CITRA,
    "yukteshwar": swe.SIDM_YUKTESHWAR,
    "fagan_bradley": swe.SIDM_FAGAN_BRADLEY,
}

BODY = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
        "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO}


class EphemerisError(RuntimeError):
    pass


def init():
    global _initialised
    if not _initialised:
        swe.set_ephe_path(EPHE_DIR)
        _initialised = True


def _check(retflag, allow_moshier, what):
    if not (allow_moshier or ALLOW_MOSHIER) and not (retflag & swe.FLG_SWIEPH):
        raise EphemerisError(
            f"{what}: Swiss Ephemeris files not used (Moshier fallback). The bundled "
            f"files cover 1800-2399 CE; for other dates add .se1 files to {EPHE_DIR} "
            f"or set allow_moshier=True.")


def set_ayanamsa(name):
    try:
        swe.set_sid_mode(AYANAMSA[name], 0, 0)
    except KeyError:
        raise ValueError(f"unknown ayanamsa {name!r}; choose from {sorted(AYANAMSA)}")


def ayanamsa_value(jd, name):
    """True ayanamsa (with nutation), the value sidereal positions are based on."""
    init()
    set_ayanamsa(name)
    _, val = swe.get_ayanamsa_ex_ut(jd, swe.FLG_SWIEPH)
    return val


def node_id(node):
    if node == "mean":
        return swe.MEAN_NODE
    if node == "true":
        return swe.TRUE_NODE
    raise ValueError("node must be 'mean' or 'true'")


def body_position(jd, name, ayanamsa, node="mean", allow_moshier=False):
    """Sidereal ecliptic longitude/latitude/distance + speeds, and tropical
    equatorial RA/declination. Ketu is derived from Rahu."""
    init()
    set_ayanamsa(ayanamsa)
    pid = node_id(node) if name in ("Rahu", "Ketu") else BODY[name]
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    xs, rf = swe.calc_ut(jd, pid, flags | swe.FLG_SIDEREAL)
    _check(rf, allow_moshier, name)
    xe, rf = swe.calc_ut(jd, pid, flags | swe.FLG_EQUATORIAL)
    _check(rf, allow_moshier, name)
    lon, lat, dist, slon, slat, sdist = xs[:6]
    ra, dec = xe[0], xe[1]
    if name == "Ketu":
        lon, lat, slat = (lon + 180.0) % 360.0, -lat, -slat
        ra, dec = (ra + 180.0) % 360.0, -dec
    return {"lon": lon % 360.0, "lat": lat, "dist_au": dist, "speed": slon,
            "lat_speed": slat, "ra": ra, "dec": dec}


def sid_lon(jd, name, ayanamsa, node="mean", allow_moshier=False):
    """Fast path: sidereal longitude only."""
    init()
    set_ayanamsa(ayanamsa)
    pid = node_id(node) if name in ("Rahu", "Ketu") else BODY[name]
    xs, rf = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    _check(rf, allow_moshier, name)
    lon = xs[0] % 360.0
    return (lon + 180.0) % 360.0 if name == "Ketu" else lon


def sid_speed(jd, name, ayanamsa, node="mean", allow_moshier=False):
    init()
    set_ayanamsa(ayanamsa)
    pid = node_id(node) if name in ("Rahu", "Ketu") else BODY[name]
    xs, rf = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
    _check(rf, allow_moshier, name)
    return xs[3]


def tropical_lon(jd, name, allow_moshier=False):
    init()
    xs, rf = swe.calc_ut(jd, BODY[name], swe.FLG_SWIEPH)
    _check(rf, allow_moshier, name)
    return xs[0] % 360.0


def heliocentric_lon(jd, name, allow_moshier=False):
    init()
    xs, rf = swe.calc_ut(jd, BODY[name], swe.FLG_SWIEPH | swe.FLG_HELCTR)
    _check(rf, allow_moshier, name)
    return xs[0] % 360.0


def magnitude(jd, name):
    init()
    return swe.pheno_ut(jd, BODY[name], swe.FLG_SWIEPH)[4]


def obliquity(jd):
    init()
    xx, _ = swe.calc_ut(jd, swe.ECL_NUT, 0)
    return xx[0]          # true obliquity


def houses(jd, lat, lon, hsys, ayanamsa):
    """Sidereal house cusps. Returns (cusps[12], asc, mc, armc, system_used).
    Placidus (and Koch) are undefined near the poles; there we fall back to
    Porphyry and say so."""
    init()
    set_ayanamsa(ayanamsa)
    code = hsys.encode() if isinstance(hsys, str) else hsys
    try:
        cusps, ascmc = swe.houses_ex(jd, lat, lon, code, swe.FLG_SIDEREAL)
        used = code.decode()
    except swe.Error:
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b"O", swe.FLG_SIDEREAL)
        used = "O"
    return [c % 360.0 for c in cusps[:12]], ascmc[0] % 360.0, ascmc[1] % 360.0, ascmc[2], used


def ascendant(jd, lat, lon, ayanamsa):
    """Sidereal ascendant only (Porphyry call: defined at every latitude and the
    ascendant is identical in every quadrant system)."""
    init()
    set_ayanamsa(ayanamsa)
    _, ascmc = swe.houses_ex(jd, lat, lon, b"O", swe.FLG_SIDEREAL)
    return ascmc[0] % 360.0


def rise_set(jd_start, lat, lon, alt, event, sunrise_mode):
    """Next sunrise ('rise') or sunset ('set') after jd_start, or None if the
    Sun does not rise/set (polar day/night)."""
    init()
    rsmi = swe.CALC_RISE if event == "rise" else swe.CALC_SET
    if sunrise_mode == "disc_centre_no_refraction":
        rsmi |= swe.BIT_HINDU_RISING
    elif sunrise_mode != "upper_limb_refraction":
        raise ValueError("sunrise must be 'upper_limb_refraction' or 'disc_centre_no_refraction'")
    res, tret = swe.rise_trans(jd_start, swe.SUN, rsmi, (lon, lat, alt), 1013.25, 15.0,
                               swe.FLG_SWIEPH)
    if res != 0:
        return None
    return tret[0]


def norm(x):
    return x % 360.0


def angdiff(a, b):
    """Signed shortest difference a-b in (-180, 180]."""
    d = (a - b) % 360.0
    return d - 360.0 if d > 180.0 else d


def angdist(a, b):
    return abs(angdiff(a, b))


def mean_sun_tropical(jd):
    """Mean longitude of the Sun (Meeus 25.2), tropical degrees."""
    t = (jd - 2451545.0) / 36525.0
    return (280.46646 + 36000.76983 * t + 0.0003032 * t * t) % 360.0


def find_crossing(f, jd0, target, step, max_days, forward=True):
    """First time after (or before) jd0 at which angle f(jd) passes `target`
    (f must be locally increasing, as for longitudes of direct bodies and
    elongations). Returns jd or None."""
    sgn = 1.0 if forward else -1.0
    g = lambda t: angdiff(f(t), target)
    t_prev, g_prev = jd0, g(jd0)
    n = int(math.ceil(max_days / step))
    for _ in range(n):
        t = t_prev + sgn * step
        gt = g(t)
        crossed = (g_prev < 0 <= gt) if forward else (gt < 0 <= g_prev)
        if crossed and abs(gt - g_prev) < 180:
            a, b = (t_prev, t) if forward else (t, t_prev)
            for _ in range(60):
                m = 0.5 * (a + b)
                if g(m) < 0:
                    a = m
                else:
                    b = m
            return b
        t_prev, g_prev = t, gt
    return None
