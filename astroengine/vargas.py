"""Shodashavarga (BPHS ch.6, Parashari mappings) with the longitude inside each
varga, vargottama flags, D60 deities and Vimshopaka bala."""
import math
from .constants import SIGNS, D60_DEITIES, PLANETS, GRAHAS
from .chart import sign_of, deg_in_sign

EPS = 1e-9


def _part(lon, n):
    """Index (0..n-1) of the equal 30/n segment of the sign containing lon.
    Exact boundaries belong to the following segment."""
    return min(int(math.floor(deg_in_sign(lon) * n / 30.0 + EPS)), n - 1)


def _odd(s):
    return s % 2 == 0      # Aries (index 0) is an odd sign


def d1(lon): return sign_of(lon)


def d2(lon):
    s, p = sign_of(lon), _part(lon, 2)
    if _odd(s):
        return 4 if p == 0 else 3     # Sun (Leo) then Moon (Cancer)
    return 3 if p == 0 else 4


def d3(lon):
    return (sign_of(lon) + 4 * _part(lon, 3)) % 12


def d4(lon):
    return (sign_of(lon) + 3 * _part(lon, 4)) % 12


def d7(lon):
    s = sign_of(lon)
    return ((s if _odd(s) else s + 6) + _part(lon, 7)) % 12


def d9(lon):
    s = sign_of(lon)
    start = [s, s + 8, s + 4][s % 3]   # movable: same, fixed: 9th, dual: 5th
    return (start + _part(lon, 9)) % 12


def d10(lon):
    s = sign_of(lon)
    return ((s if _odd(s) else s + 8) + _part(lon, 10)) % 12


def d12(lon):
    return (sign_of(lon) + _part(lon, 12)) % 12


def d16(lon):
    return ([0, 4, 8][sign_of(lon) % 3] + _part(lon, 16)) % 12


def d20(lon):
    return ([0, 8, 4][sign_of(lon) % 3] + _part(lon, 20)) % 12


def d24(lon):
    return ((4 if _odd(sign_of(lon)) else 3) + _part(lon, 24)) % 12


def d27(lon):
    return (3 * (sign_of(lon) % 4) + _part(lon, 27)) % 12


D30_ODD = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]    # Mars Sat Jup Merc Ven
D30_EVEN = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]   # Ven Merc Jup Sat Mars


def _d30_segment(lon):
    d = deg_in_sign(lon)
    table = D30_ODD if _odd(sign_of(lon)) else D30_EVEN
    lo = 0.0
    for hi, sg in table:
        if d < hi - EPS or hi == 30:
            return sg, lo, hi
        lo = hi
    return table[-1][1], lo, 30.0


def d30(lon):
    return _d30_segment(lon)[0]


def d40(lon):
    return ((0 if _odd(sign_of(lon)) else 6) + _part(lon, 40)) % 12


def d45(lon):
    return ([0, 4, 8][sign_of(lon) % 3] + _part(lon, 45)) % 12


def d60(lon):
    return (sign_of(lon) + _part(lon, 60)) % 12


VARGA_FUNCS = {1: d1, 2: d2, 3: d3, 4: d4, 7: d7, 9: d9, 10: d10, 12: d12, 16: d16,
               20: d20, 24: d24, 27: d27, 30: d30, 40: d40, 45: d45, 60: d60}
VARGA_NAMES = {1: "Rasi", 2: "Hora", 3: "Drekkana", 4: "Chaturthamsa", 7: "Saptamsa",
               9: "Navamsa", 10: "Dasamsa", 12: "Dwadasamsa", 16: "Shodasamsa",
               20: "Vimsamsa", 24: "Chaturvimsamsa", 27: "Bhamsa", 30: "Trimsamsa",
               40: "Khavedamsa", 45: "Akshavedamsa", 60: "Shashtiamsa"}


def varga_sign(lon, n):
    return VARGA_FUNCS[n](lon)


def varga_degree(lon, n):
    """Degree the point occupies inside its varga sign (0-30)."""
    if n == 1:
        return deg_in_sign(lon)
    if n == 30:
        _, lo, hi = _d30_segment(lon)
        return (deg_in_sign(lon) - lo) / (hi - lo) * 30.0
    return (deg_in_sign(lon) * n) % 30.0


def d60_deity(lon):
    p = _part(lon, 60)
    return D60_DEITIES[p] if _odd(sign_of(lon)) else D60_DEITIES[59 - p]


def varga_chart(chart, n):
    lagna = varga_sign(chart.asc, n)
    out = {"name": VARGA_NAMES[n], "lagna": SIGNS[lagna], "lagna_index": lagna,
           "lagna_degree": varga_degree(chart.asc, n), "planets": {}}
    for p, lon in chart.pos.items():
        s = varga_sign(lon, n)
        out["planets"][p] = {"sign": SIGNS[s], "sign_index": s,
                             "house": ((s - lagna) % 12) + 1,
                             "degree": varga_degree(lon, n)}
    return out


def all_vargas(chart):
    res = {f"D{n}": varga_chart(chart, n) for n in VARGA_FUNCS}
    res["D60"]["deities"] = {p: d60_deity(lon) for p, lon in chart.pos.items()}
    res["D60"]["lagna_deity"] = d60_deity(chart.asc)
    return res


def vargottama(chart):
    """Same sign in D1 and D9."""
    pts = dict(chart.pos)
    pts["Lagna"] = chart.asc
    return {p: d1(l) == d9(l) for p, l in pts.items()}


# ---------------------------------------------------------------- Vimshopaka
VIMSHOPAKA_SCHEMES = {
    "shadvarga": {1: 6, 2: 2, 3: 4, 9: 5, 12: 2, 30: 1},
    "saptavarga": {1: 5, 2: 2, 3: 3, 7: 2.5, 9: 4.5, 12: 2, 30: 1},
    "dashavarga": {1: 3, 2: 1.5, 3: 1.5, 7: 1.5, 9: 1.5, 10: 1.5, 12: 1.5, 16: 1.5,
                   30: 1.5, 60: 5},
    "shodashavarga": {1: 3.5, 2: 1, 3: 1, 4: 0.5, 7: 0.5, 9: 3, 10: 0.5, 12: 0.5,
                      16: 2, 20: 0.5, 24: 0.5, 27: 0.5, 30: 1, 40: 0.5, 45: 0.5, 60: 4},
}
for _k, _v in VIMSHOPAKA_SCHEMES.items():
    assert abs(sum(_v.values()) - 20) < 1e-9, _k

# BPHS ch.7: own 20, great friend 18, friend 15, neutral 10, enemy 7, great enemy 5.
VIMSHOPAKA_POINTS = {"exalted": 20, "own": 20, "great_friend": 18, "friend": 15,
                     "neutral": 10, "enemy": 7, "great_enemy": 5}


def vimshopaka(chart, compound):
    """compound: dignity.compound_relationships(chart). Sign-based in every
    varga: exaltation sign and own sign score 20, otherwise the compound
    relationship with the varga sign's lord (debilitation is scored by that
    relationship too, as BPHS lists no separate value for it)."""
    from .dignity import exaltation_sign
    from .constants import SIGN_LORD, OWN_SIGNS
    out = {}
    for p in GRAHAS:
        res = {}
        for scheme, weights in VIMSHOPAKA_SCHEMES.items():
            tot = 0.0
            for n, w in weights.items():
                s = varga_sign(chart.pos[p], n)
                if s == exaltation_sign(p, chart.config):
                    key = "exalted"
                elif s in OWN_SIGNS[p]:
                    key = "own"
                else:
                    key = compound[p][SIGN_LORD[s]]
                tot += w * VIMSHOPAKA_POINTS[key] / 20.0
            res[scheme] = round(tot, 3)
        out[p] = res
    return out
