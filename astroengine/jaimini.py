"""Jaimini: chara karakas, stronger co-lord rule, arudha padas, upapada,
karakamsha. Chara dasha lives in dashas.py and uses stronger_lord()."""
from .constants import SIGNS, SIGN_LORD, CO_LORD, PLANETS, GRAHAS
from .chart import sign_of, deg_in_sign, house_from
from .vargas import d9
from .dignity import exaltation_sign

KARAKA8 = ["AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"]
KARAKA7 = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]
KARAKA_MEANING = {"AK": "Atmakaraka (self)", "AmK": "Amatyakaraka (career/minister)",
                  "BK": "Bhratrikaraka (siblings/guru)", "MK": "Matrikaraka (mother)",
                  "PiK": "Pitrikaraka (father)", "PK": "Putrakaraka (children)",
                  "GK": "Gnatikaraka (rivals/disease)", "DK": "Darakaraka (spouse)"}


def _jaimini_degree(c, p):
    d = deg_in_sign(c.pos[p])
    return 30.0 - d if p in ("Rahu", "Ketu") else d


def chara_karakas(c, scheme=8):
    bodies = GRAHAS + (["Rahu"] if scheme == 8 else [])
    names = KARAKA8 if scheme == 8 else KARAKA7
    vals = {p: _jaimini_degree(c, p) for p in bodies}
    order = sorted(bodies, key=lambda p: -vals[p])
    ties = [[order[i], order[i + 1]] for i in range(len(order) - 1)
            if abs(vals[order[i]] - vals[order[i + 1]]) < 1.0 / 60.0]
    return {"scheme": scheme,
            "karakas": {names[i]: order[i] for i in range(len(names))},
            "by_planet": {order[i]: names[i] for i in range(len(names))},
            "degrees_used": vals, "near_ties_within_1_arcmin": ties,
            "meanings": {k: KARAKA_MEANING[k] for k in names}}


def stronger_lord(c, sign):
    """Lord used by Jaimini techniques for a sign. Scorpio (Mars/Ketu) and
    Aquarius (Saturn/Rahu) pick the stronger co-lord: (1) if exactly one lord
    sits in the sign, the other; (2) more planets conjoined; (3) exalted;
    (4) lord's sign dual > fixed > movable; (5) more advanced in degrees."""
    if sign not in CO_LORD:
        return SIGN_LORD[sign], "single lord"
    a, b = SIGN_LORD[sign], CO_LORD[sign]
    ina, inb = c.sign(a) == sign, c.sign(b) == sign
    if ina and not inb:
        return b, f"{a} occupies the sign, so {b} is taken"
    if inb and not ina:
        return a, f"{b} occupies the sign, so {a} is taken"
    if ina and inb:
        return a, "both lords occupy the sign"
    conj = {x: len([p for p in PLANETS if p != x and c.sign(p) == c.sign(x)]) for x in (a, b)}
    if conj[a] != conj[b]:
        w = a if conj[a] > conj[b] else b
        return w, f"{w} conjoined with more planets ({conj})"
    ex = {x: c.sign(x) == exaltation_sign(x, c.config) for x in (a, b)}
    if ex[a] != ex[b]:
        w = a if ex[a] else b
        return w, f"{w} exalted"
    q = {x: c.sign(x) % 3 for x in (a, b)}
    if q[a] != q[b]:
        w = a if q[a] > q[b] else b
        return w, f"{w} in the stronger sign type (dual > fixed > movable)"
    w = a if _jaimini_degree(c, a) >= _jaimini_degree(c, b) else b
    return w, f"{w} more advanced in degrees"


def arudha_of_sign(c, sign):
    lord, why = stronger_lord(c, sign)
    ls = c.sign(lord)
    n = (ls - sign) % 12
    a = (ls + n) % 12
    exception = None
    if a == sign:
        a, exception = (a + 9) % 12, "fell in the sign itself -> 10th from it"
    elif (a - sign) % 12 == 6:
        a, exception = (a + 9) % 12, "fell in the 7th -> 10th from that (4th from the sign)"
    return a, lord, why, exception


def arudha_padas(c):
    out = {}
    for h in range(1, 13):
        s = (c.lagna + h - 1) % 12
        a, lord, why, exc = arudha_of_sign(c, s)
        key = "AL" if h == 1 else ("UL" if h == 12 else f"A{h}")
        out[key] = {"house": h, "sign": SIGNS[a], "sign_index": a,
                    "house_from_lagna": house_from(a, c.lagna), "lord_used": lord,
                    "lord_choice": why, "exception": exc}
    return out


def karakamsha(c, karakas):
    ak = karakas["karakas"]["AK"]
    ks = d9(c.pos[ak])
    return {"atmakaraka": ak, "karakamsha_sign": SIGNS[ks], "sign_index": ks,
            "house_from_rasi_lagna": house_from(ks, c.lagna),
            "planets_in_karakamsha_rasi": c.occupants(ks),
            "planets_in_karakamsha_navamsa": [p for p in PLANETS if d9(c.pos[p]) == ks],
            "swamsha_navamsa_lagna": SIGNS[d9(c.asc)]}


def jaimini(c):
    k8 = chara_karakas(c, 8)
    k7 = chara_karakas(c, 7)
    primary = k8 if c.config.chara_karaka_scheme == 8 else k7
    return {"chara_karakas": primary, "chara_karakas_alternate": k7 if primary is k8 else k8,
            "arudha_padas": arudha_padas(c), "karakamsha": karakamsha(c, primary),
            "stronger_co_lords": {SIGNS[s]: dict(zip(("lord", "reason"), stronger_lord(c, s)))
                                  for s in CO_LORD}}
