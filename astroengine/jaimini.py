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


def stronger_sign(c, a, b):
    """Jaimini strength of two signs (rules as used for Narayana dasha, Rath/JHora):
    (1) more planets in it; (2) more of Jupiter, Mercury and its lord conjoined with
    or rashi-aspecting it; (3) contains an exalted planet; (4) lord placed in a sign of
    the opposite oddity; (5) dual > fixed > movable; (6) lord more advanced in degrees."""
    from .aspects import rashi_drishti_signs
    if a == b:
        return a, "same sign"
    n = {s: len(c.occupants(s)) for s in (a, b)}
    if n[a] != n[b]:
        w = a if n[a] > n[b] else b
        return w, f"rule 1: more planets ({SIGNS[a]} {n[a]}, {SIGNS[b]} {n[b]})"

    def r2(s):
        k = 0
        for p in ("Mercury", "Jupiter", SIGN_LORD[s]):
            if c.sign(p) == s:
                k += 1
            if s in rashi_drishti_signs(c.sign(p)):
                k += 1
        return k
    v = {s: r2(s) for s in (a, b)}
    if v[a] != v[b]:
        w = a if v[a] > v[b] else b
        return w, "rule 2: more association/aspect of Jupiter, Mercury, own lord"
    ex = {s: any(exaltation_sign(p, c.config) == s for p in c.occupants(s)) for s in (a, b)}
    if ex[a] != ex[b]:
        w = a if ex[a] else b
        return w, "rule 3: contains an exalted planet"
    odd = {s: (s % 2) != (c.sign(SIGN_LORD[s]) % 2) for s in (a, b)}
    if odd[a] != odd[b]:
        w = a if odd[a] else b
        return w, "rule 4: lord in a sign of different oddity"
    if a % 3 != b % 3:
        w = a if a % 3 > b % 3 else b
        return w, "rule 5: dual > fixed > movable"
    la, lb = stronger_lord(c, a)[0], stronger_lord(c, b)[0]
    w = a if _jaimini_degree(c, la) >= _jaimini_degree(c, lb) else b
    return w, "rule 6: lord more advanced in degrees"


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


def jaimini(c, compound=None):
    from .dignity import compound_relationships
    compound = compound or compound_relationships(c)
    k8 = chara_karakas(c, 8)
    k7 = chara_karakas(c, 7)
    primary = k8 if c.config.chara_karaka_scheme == 8 else k7
    return {"chara_karakas": primary, "chara_karakas_alternate": k7 if primary is k8 else k8,
            "arudha_padas": arudha_padas(c), "karakamsha": karakamsha(c, primary),
            "brahma": brahma(c, compound),
            "stronger_co_lords": {SIGNS[s]: dict(zip(("lord", "reason"), stronger_lord(c, s)))
                                  for s in CO_LORD}}


def stronger_planet(c, a, b):
    """Jaimini planet strength: (1) conjoined with more planets; (2) more of
    Jupiter, Mercury and its dispositor conjoining or rashi-aspecting it;
    (3) exalted; (4) more advanced in degrees."""
    from .aspects import rashi_drishti_signs
    if a == b:
        return a, "same planet"
    conj = {x: len([p for p in PLANETS if p != x and c.sign(p) == c.sign(x)]) for x in (a, b)}
    if conj[a] != conj[b]:
        w = a if conj[a] > conj[b] else b
        return w, "rule 1: conjoined with more planets"

    def r2(x):
        s, k = c.sign(x), 0
        for p in ("Mercury", "Jupiter", SIGN_LORD[s]):
            if p == x:
                continue
            k += (c.sign(p) == s) + (s in rashi_drishti_signs(c.sign(p)))
        return k
    v = {x: r2(x) for x in (a, b)}
    if v[a] != v[b]:
        w = a if v[a] > v[b] else b
        return w, "rule 2: more association/aspect of Jupiter, Mercury, dispositor"
    ex = {x: c.sign(x) == exaltation_sign(x, c.config) for x in (a, b)}
    if ex[a] != ex[b]:
        w = a if ex[a] else b
        return w, "rule 3: exalted"
    w = a if _jaimini_degree(c, a) >= _jaimini_degree(c, b) else b
    return w, "rule 4: more advanced in degrees"


GOOD_DIGNITY = ("exalted", "moolatrikona", "own", "great_friend", "friend")


def brahma(c, compound):
    """Brahma: among the lords of the 6th, 8th and 12th from the stronger of
    lagna and 7th (Rahu/Ketu excluded, so Scorpio/Aquarius give Mars/Saturn),
    the planet scoring highest on: placed in an odd sign; placed in houses 1-7
    from that stronger sign; dignity friendly or better. Ties go to Jaimini
    planet strength. Texts word this rule differently; candidates are reported."""
    from .dignity import rasi_dignity
    S, why = stronger_sign(c, c.lagna, (c.lagna + 6) % 12)
    lords = []
    for h in (6, 8, 12):
        l = SIGN_LORD[(S + h - 1) % 12]
        if l not in lords:
            lords.append(l)
    cands = {}
    for l in lords:
        s = c.sign(l)
        crit = {"odd_sign": s % 2 == 0, "in_houses_1_to_7": house_from(s, S) <= 7,
                "friendly_or_better": rasi_dignity(l, c.pos[l], compound, c.config) in GOOD_DIGNITY}
        cands[l] = {"rules_houses_from_reference": [h for h in (6, 8, 12)
                                                    if SIGN_LORD[(S + h - 1) % 12] == l],
                    "sign": SIGNS[s], "criteria": crit, "score": sum(crit.values())}
    top = max(v["score"] for v in cands.values())
    best = [l for l in lords if cands[l]["score"] == top]
    pick, reason = best[0], f"highest score {top}"
    for other in best[1:]:
        pick, r = stronger_planet(c, pick, other)
        reason = f"tied on score {top}; {r}"
    return {"reference_sign": SIGNS[S], "reference_reason": why, "candidates": cands,
            "brahma": pick, "brahma_sign": SIGNS[c.sign(pick)], "sign_index": c.sign(pick),
            "selection": reason}
