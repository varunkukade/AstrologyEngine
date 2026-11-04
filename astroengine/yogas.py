"""Yoga and dosha detection. Each result carries the rule it applied and the
data it tested, so the reader can check or re-weight it. Only yogas with an
unambiguous definition are coded; 'source' names the text the rule follows."""
from itertools import combinations
from .constants import SIGNS, SIGN_LORD, GRAHAS, PLANETS, OWN_SIGNS
from .chart import house_from
from .dignity import rasi_dignity, exaltation_sign, debilitation_sign, combustion
from .aspects import aspects_sign
from .vargas import d9

KENDRA, TRIKONA, DUSTHANA = (1, 4, 7, 10), (1, 5, 9), (6, 8, 12)
STRONG = ("exalted", "own", "moolatrikona")


def _y(name, category, source, planets, detail, **extra):
    return {"name": name, "category": category, "source": source,
            "planets": planets, "detail": detail, **extra}


def relation(c, a, b):
    """Parashari sambandha between two grahas, strongest first."""
    rels = []
    if c.sign(a) == c.sign(b):
        rels.append("conjunction")
    if SIGN_LORD[c.sign(a)] == b and SIGN_LORD[c.sign(b)] == a:
        rels.append("exchange")
    ab, ba = aspects_sign(c, a, c.sign(b)), aspects_sign(c, b, c.sign(a))
    if ab and ba:
        rels.append("mutual_aspect")
    elif ab:
        rels.append(f"{a}_aspects_{b}")
    elif ba:
        rels.append(f"{b}_aspects_{a}")
    return rels


def _hmoon(c, p):
    return house_from(c.sign(p), c.sign("Moon"))


def raja_yogas(c):
    out = []
    for p in GRAHAS:
        r = c.houses_ruled(p)
        k = [h for h in r if h in (4, 7, 10)]
        t = [h for h in r if h in (5, 9)]
        if k and t:
            out.append(_y("Yogakaraka", "raja", "BPHS ch.34", [p],
                          f"{p} alone rules kendra {k} and trikona {t}",
                          tainted_by_dusthana=[h for h in r if h in DUSTHANA]))
    for a, b in combinations(GRAHAS, 2):
        ra, rb = c.houses_ruled(a), c.houses_ruled(b)
        pairs = []
        for x, y, rx, ry in ((a, b, ra, rb), (b, a, rb, ra)):
            kx = [h for h in rx if h in KENDRA]
            ty = [h for h in ry if h in TRIKONA]
            if kx and ty and not (kx == [1] and ty == [1]):
                pairs.append((x, kx, y, ty))
        if not pairs:
            continue
        rel = [x for x in relation(c, a, b) if x in ("conjunction", "exchange", "mutual_aspect")
               or "_aspects_" in x]
        if not rel:
            continue
        x, kx, y, ty = pairs[0]
        out.append(_y("Raja Yoga (kendra-trikona lords)", "raja", "BPHS ch.34",
                      [a, b], f"{x} (kendra lord {kx}) and {y} (trikona lord {ty}): {', '.join(rel)}",
                      relation=rel,
                      also_rule_dusthana={a: [h for h in ra if h in DUSTHANA],
                                          b: [h for h in rb if h in DUSTHANA]}))
    return out


def dhana_yogas(c):
    out = []
    wealth = {1, 2, 5, 9, 11}
    for a, b in combinations(GRAHAS, 2):
        ha = [h for h in c.houses_ruled(a) if h in wealth]
        hb = [h for h in c.houses_ruled(b) if h in wealth]
        if not ha or not hb or not ({2, 11} & set(ha + hb)):
            continue
        rel = [x for x in relation(c, a, b) if x in ("conjunction", "exchange", "mutual_aspect")]
        if rel:
            out.append(_y("Dhana Yoga", "wealth", "BPHS ch.41",
                          [a, b], f"{a} rules {ha}, {b} rules {hb}: {', '.join(rel)}", relation=rel))
    return out


PMP = {"Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa", "Venus": "Malavya",
       "Saturn": "Sasa"}


def pancha_mahapurusha(c, compound):
    out = []
    for p, name in PMP.items():
        dg = rasi_dignity(p, c.pos[p], compound, c.config)
        if dg not in STRONG:
            continue
        hl, hm = c.house(p), _hmoon(c, p)
        if hl in KENDRA:
            out.append(_y(f"{name} (Pancha Mahapurusha)", "mahapurusha", "BPHS ch.75",
                          [p], f"{p} {dg} in house {hl} from lagna", reference="lagna"))
        elif hm in KENDRA:
            out.append(_y(f"{name} (Pancha Mahapurusha, from Moon)", "mahapurusha",
                          "variant: counted from the Moon", [p],
                          f"{p} {dg} in house {hm} from Moon", reference="moon"))
    return out


def vipreeta(c):
    out = []
    names = {6: "Harsha", 8: "Sarala", 12: "Vimala"}
    for p in GRAHAS:
        owned = [h for h in c.houses_ruled(p) if h in DUSTHANA]
        h = c.house(p)
        if owned and h in DUSTHANA:
            out.append(_y(f"Vipreeta Raja Yoga ({names[owned[0]]})", "raja",
                          "Uttara Kalamrita / BPHS", [p],
                          f"{p}, lord of {owned}, placed in house {h}"))
    return out


def neecha_bhanga(c, compound):
    out = []
    cfg = c.config
    moon = c.sign("Moon")
    for p in GRAHAS:
        if rasi_dignity(p, c.pos[p], compound, cfg) != "debilitated":
            continue
        s = c.sign(p)
        dl = SIGN_LORD[s]
        el = SIGN_LORD[exaltation_sign(p, cfg)]
        ex_here = [q for q in GRAHAS if exaltation_sign(q, cfg) == s]
        chk = []

        def kendra_test(label, q, src):
            hl, hm = c.house(q), house_from(c.sign(q), moon)
            chk.append({"rule": f"{label} ({q}) in kendra from lagna", "met": hl in KENDRA,
                        "house": hl, "source": src})
            chk.append({"rule": f"{label} ({q}) in kendra from Moon", "met": hm in KENDRA,
                        "house": hm, "source": src})

        kendra_test("lord of debilitation sign", dl, "BPHS ch.49")
        kendra_test("lord of exaltation sign", el, "BPHS ch.49")
        for q in ex_here:
            kendra_test(f"planet exalted in {SIGNS[s]}", q, "Phaladeepika ch.7")
        chk.append({"rule": f"debilitation-sign lord {dl} aspects {p}",
                    "met": aspects_sign(c, dl, s) if dl != p else False, "source": "common"})
        chk.append({"rule": f"debilitation-sign lord {dl} conjunct {p}",
                    "met": c.sign(dl) == s, "source": "common"})
        chk.append({"rule": f"{p} exalted in navamsa",
                    "met": d9(c.pos[p]) == exaltation_sign(p, cfg), "source": "common"})
        chk.append({"rule": f"{p} in exchange with {dl}",
                    "met": SIGN_LORD[c.sign(dl)] == p, "source": "common"})
        chk.append({"rule": f"{p} itself in kendra from lagna or Moon",
                    "met": c.house(p) in KENDRA or house_from(s, moon) in KENDRA,
                    "source": "Phaladeepika (some readings)"})
        met = [x for x in chk if x["met"]]
        out.append({"planet": p, "sign": SIGNS[s], "checks": chk,
                    "cancelled_by_bphs_rules": any(x["met"] and x["source"] == "BPHS ch.49" for x in chk),
                    "cancelled_by_any_rule": bool(met)})
    return out


def lunar_yogas(c):
    out = []
    moon = c.sign("Moon")
    jh = _hmoon(c, "Jupiter")
    if jh in KENDRA:
        out.append(_y("Gaja Kesari", "lunar", "BPHS ch.36", ["Moon", "Jupiter"],
                      f"Jupiter in house {jh} from Moon"))
    rel = relation(c, "Moon", "Mars")
    if "conjunction" in rel or "mutual_aspect" in rel:
        out.append(_y("Chandra-Mangala", "lunar", "Phaladeepika ch.6", ["Moon", "Mars"],
                      ", ".join(rel)))
    others = [p for p in GRAHAS if p not in ("Sun", "Moon")]
    second = [p for p in others if _hmoon(c, p) == 2]
    twelfth = [p for p in others if _hmoon(c, p) == 12]
    if second and twelfth:
        out.append(_y("Durudhara", "lunar", "BPHS ch.37", second + twelfth,
                      f"2nd from Moon {second}, 12th from Moon {twelfth}"))
    elif second:
        out.append(_y("Sunapha", "lunar", "BPHS ch.37", second, f"2nd from Moon {second}"))
    elif twelfth:
        out.append(_y("Anapha", "lunar", "BPHS ch.37", twelfth, f"12th from Moon {twelfth}"))
    else:
        canc = {
            "graha_in_kendra_from_lagna": [p for p in GRAHAS if p != "Moon" and c.house(p) in KENDRA],
            "graha_in_kendra_from_moon": [p for p in GRAHAS if p != "Moon" and _hmoon(c, p) in (4, 7, 10)],
            "graha_conjunct_moon": [p for p in GRAHAS if p != "Moon" and c.sign(p) == moon],
        }
        out.append(_y("Kemadruma", "lunar", "BPHS ch.37 (cancellations: Phaladeepika ch.6)", ["Moon"],
                      "no graha (Sun excluded) in 2nd or 12th from Moon",
                      cancellation_factors=canc, cancelled=any(canc.values())))
    adhi = [p for p in ("Mercury", "Jupiter", "Venus") if _hmoon(c, p) in (6, 7, 8)]
    if adhi:
        out.append(_y("Adhi Yoga" + ("" if len(adhi) == 3 else " (partial)"), "lunar",
                      "BPHS ch.36", adhi, f"benefics in 6/7/8 from Moon: {adhi}"))
    ju_to_moon = house_from(moon, c.sign("Jupiter"))
    if ju_to_moon in (6, 8, 12):
        out.append(_y("Shakata", "lunar", "Phaladeepika ch.6", ["Moon", "Jupiter"],
                      f"Moon in house {ju_to_moon} from Jupiter",
                      moon_in_kendra_from_lagna=c.house("Moon") in KENDRA))
    for ref, rs in (("lagna", c.lagna), ("Moon", moon)):
        tenth = [p for p in ("Mercury", "Jupiter", "Venus") if house_from(c.sign(p), rs) == 10]
        if tenth:
            out.append(_y("Amala", "benefic", "Phaladeepika ch.6", tenth,
                          f"natural benefic in 10th from {ref}", reference=ref))
    return out


def solar_yogas(c):
    out = []
    sun = c.sign("Sun")
    pl = [p for p in GRAHAS if p not in ("Sun", "Moon")]
    second = [p for p in pl if house_from(c.sign(p), sun) == 2]
    twelfth = [p for p in pl if house_from(c.sign(p), sun) == 12]
    if second and twelfth:
        out.append(_y("Ubhayachari", "solar", "BPHS ch.37", second + twelfth,
                      f"2nd from Sun {second}, 12th from Sun {twelfth}"))
    elif second:
        out.append(_y("Vesi", "solar", "BPHS ch.37", second, f"2nd from Sun {second}"))
    elif twelfth:
        out.append(_y("Vasi", "solar", "BPHS ch.37", twelfth, f"12th from Sun {twelfth}"))
    if c.sign("Mercury") == sun:
        comb = combustion(c)["Mercury"]
        out.append(_y("Budhaditya", "solar", "common", ["Sun", "Mercury"],
                      f"Sun and Mercury in {SIGNS[sun]}",
                      separation=comb["distance_from_sun"], mercury_combust=comb["combust"]))
    return out


def parivartana(c):
    out = []
    for a, b in combinations(GRAHAS, 2):
        if SIGN_LORD[c.sign(a)] == b and SIGN_LORD[c.sign(b)] == a:
            ha, hb = c.house(a), c.house(b)
            hs = {ha, hb}
            kind = "Dainya" if hs & set(DUSTHANA) else ("Khala" if 3 in hs else "Maha")
            out.append(_y(f"{kind} Parivartana", "exchange", "Phaladeepika ch.6", [a, b],
                          f"{a} in house {ha} and {b} in house {hb} exchange signs"))
    return out


def nabhasa(c):
    out = []
    signs = {c.sign(p) for p in GRAHAS}
    names = {7: "Vallaki (Veena)", 6: "Dama", 5: "Pasha", 4: "Kedara", 3: "Shula", 2: "Yuga",
             1: "Gola"}
    out.append(_y(f"{names[len(signs)]} (Sankhya)", "nabhasa", "BPHS ch.35", GRAHAS,
                  f"seven grahas occupy {len(signs)} signs"))
    q = {s % 3 for s in signs}
    if len(q) == 1:
        nm = ["Rajju", "Musala", "Nala"][q.pop()]
        out.append(_y(f"{nm} (Ashraya)", "nabhasa", "BPHS ch.35", GRAHAS,
                      "all seven grahas in signs of one quality"))
    return out


def kartari(c):
    out = []
    from .shadbala import benefic_set
    ben = benefic_set(c)
    mal = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"} | ({"Moon"} - ben) | ({"Mercury"} - ben)
    for ref, rs in (("lagna", c.lagna), ("Moon", c.sign("Moon"))):
        s2, s12 = c.occupants((rs + 1) % 12), c.occupants((rs + 11) % 12)
        if ref == "Moon":
            s2, s12 = [p for p in s2 if p != "Moon"], [p for p in s12 if p != "Moon"]
        if s2 and s12 and all(p in ben for p in s2 + s12):
            out.append(_y("Shubha Kartari", "kartari", "common", s2 + s12,
                          f"{ref} hemmed by benefics", reference=ref))
        if s2 and s12 and all(p in mal for p in s2 + s12):
            out.append(_y("Papa Kartari", "kartari", "common", s2 + s12,
                          f"{ref} hemmed by malefics", reference=ref))
    return out


def node_yogas(c):
    out = []
    rahu = c.pos["Rahu"]
    rel = [(c.pos[p] - rahu) % 360.0 for p in GRAHAS]
    inside = sum(1 for r in rel if r < 180.0)
    if inside in (0, 7):
        nm = "Kala Sarpa" if inside == 0 else "Kala Amrita"
        out.append(_y(nm, "dosha", "modern (not in BPHS)", GRAHAS,
                      "all seven grahas on one side of the Rahu-Ketu axis"))
    elif inside in (1, 6):
        out.append(_y("Partial Kala Sarpa", "dosha", "modern (not in BPHS)", GRAHAS,
                      "six of seven grahas on one side of the nodal axis"))
    for lum in ("Sun", "Moon"):
        with_n = [n for n in ("Rahu", "Ketu") if c.sign(n) == c.sign(lum)]
        if with_n:
            out.append(_y("Grahana Yoga", "dosha", "modern", [lum] + with_n,
                          f"{lum} with {with_n[0]} in {SIGNS[c.sign(lum)]}"))
    with_j = [n for n in ("Rahu", "Ketu") if c.sign(n) == c.sign("Jupiter")]
    if with_j:
        out.append(_y("Guru-Chandala", "dosha", "modern", ["Jupiter"] + with_j,
                      f"Jupiter with {with_j[0]}"))
    return out


def mangal_dosha(c):
    res = {}
    for ref, rs in (("lagna", c.lagna), ("moon", c.sign("Moon")), ("venus", c.sign("Venus"))):
        h = house_from(c.sign("Mars"), rs)
        res[ref] = {"mars_house": h, "present": h in (1, 2, 4, 7, 8, 12)}
    return {"by_reference": res, "rule": "Mars in 1,2,4,7,8,12 (exceptions vary by school "
                                         "and are not applied)"}


def all_yogas(c, compound):
    found = (raja_yogas(c) + dhana_yogas(c) + pancha_mahapurusha(c, compound) + vipreeta(c)
             + lunar_yogas(c) + solar_yogas(c) + parivartana(c) + nabhasa(c) + kartari(c)
             + node_yogas(c))
    return {"yogas": found, "neecha_bhanga": neecha_bhanga(c, compound),
            "mangal_dosha": mangal_dosha(c)}
