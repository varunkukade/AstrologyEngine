"""Krishnamurti Paddhati on its own chart: KP ayanamsa + Placidus cusps.

Significator levels for a house (Krishnamurti's order of strength):
  A planets in the star of an occupant, B occupants, C planets in the star of
  the cusp's sign lord, D the sign lord. Rahu/Ketu also act as agents of their
  sign lord, star lord, conjoined planets and planets aspecting them; they are
  added at the level of the planet they represent."""
from .constants import SIGNS, SIGN_LORD, PLANETS, VIM_ORDER, VIM_YEARS, NAK_SPAN, WEEKDAY_LORD
from .chart import Chart, sign_of, dms
from .aspects import aspects_sign


def kp_lords(lon):
    """Sign lord, star lord, sub lord, sub-sub lord (Vimshottari proportions)."""
    lon %= 360.0
    nk = int(lon // NAK_SPAN) % 27
    star = VIM_ORDER[nk % 9]
    pos = (lon - nk * NAK_SPAN) / NAK_SPAN * 120.0          # 0..120 "years"
    chain = [star]
    start = VIM_ORDER.index(star)
    span = 120.0
    for _ in range(2):
        acc = 0.0
        i0 = VIM_ORDER.index(chain[-1])
        for k in range(9):
            l = VIM_ORDER[(i0 + k) % 9]
            w = span * VIM_YEARS[l] / 120.0
            if pos < acc + w or k == 8:
                chain.append(l)
                pos -= acc
                span = w
                break
            acc += w
    return {"sign_lord": SIGN_LORD[sign_of(lon)], "star_lord": chain[0],
            "sub_lord": chain[1], "sub_sub_lord": chain[2]}


def kp_chart(birth, config):
    return Chart(birth, config, ayanamsa=config.kp_ayanamsa, placidus=True)


def kp(birth, config, vara):
    c = kp_chart(birth, config)
    cusps = c.placidus
    occ = {p: c.placidus_house(c.pos[p]) for p in PLANETS}
    owns = {p: [] for p in PLANETS}
    for h in range(12):
        owns[SIGN_LORD[sign_of(cusps[h])]].append(h + 1)
    lords = {p: kp_lords(c.pos[p]) for p in PLANETS}
    star = {p: lords[p]["star_lord"] for p in PLANETS}

    agents = {}
    for n in ("Rahu", "Ketu"):
        conj = [q for q in PLANETS if q != n and q not in ("Rahu", "Ketu") and c.sign(q) == c.sign(n)]
        asp = [q for q in PLANETS if q not in ("Rahu", "Ketu") and aspects_sign(c, q, c.sign(n))]
        agents[n] = {"sign_lord": lords[n]["sign_lord"], "star_lord": star[n],
                     "conjoined": conj, "aspected_by": asp}

    def represented(n):
        a = agents[n]
        return {a["sign_lord"], *a["conjoined"], *a["aspected_by"]}

    sig = {}
    for h in range(1, 13):
        B = [p for p in PLANETS if occ[p] == h]
        D = [p for p in PLANETS if h in owns[p]]
        A = [p for p in PLANETS if star[p] in B]
        C = [p for p in PLANETS if star[p] in D]
        for n in ("Rahu", "Ketu"):
            rep = represented(n)
            if rep & set(B) and n not in B:
                B.append(n)
            if rep & set(D) and n not in D:
                D.append(n)
        sig[h] = {"A_in_star_of_occupant": A, "B_occupant": B,
                  "C_in_star_of_owner": C, "D_owner": D}

    def planet_houses(p):
        s = star[p]
        res = {"star_lord_occupies": occ[s], "star_lord_owns": owns[s],
               "self_occupies": occ[p], "self_owns": owns[p]}
        if p in ("Rahu", "Ketu"):
            rep = represented(p)
            res["as_agent"] = sorted({occ[q] for q in rep} | {h for q in rep for h in owns[q]})
        allh = {res["star_lord_occupies"], *res["star_lord_owns"], res["self_occupies"], *res["self_owns"]}
        allh |= set(res.get("as_agent", []))
        res["all"] = sorted(allh)
        return res

    psig = {p: planet_houses(p) for p in PLANETS}
    cusp_rows = []
    for h in range(12):
        l = kp_lords(cusps[h])
        cusp_rows.append({"house": h + 1, "longitude": cusps[h], "sign": SIGNS[sign_of(cusps[h])],
                          "dms": dms(cusps[h] % 30), **l,
                          "sub_lord_signifies": psig[l["sub_lord"]]["all"]})
    asc_l, moon_l = kp_lords(c.asc), kp_lords(c.pos["Moon"])
    ruling = {"day_lord": WEEKDAY_LORD[vara],
              "lagna_sign_lord": asc_l["sign_lord"], "lagna_star_lord": asc_l["star_lord"],
              "lagna_sub_lord": asc_l["sub_lord"],
              "moon_sign_lord": moon_l["sign_lord"], "moon_star_lord": moon_l["star_lord"],
              "moon_sub_lord": moon_l["sub_lord"]}
    return {
        "ayanamsa": config.kp_ayanamsa, "ayanamsa_value": c.ayanamsa,
        "house_system": "Placidus" if c.placidus_system == "P" else
                        "Porphyry (Placidus undefined at this latitude)",
        "cusps": cusp_rows,
        "planets": {p: {"longitude": c.pos[p], "sign": SIGNS[c.sign(p)], "dms": dms(c.pos[p] % 30),
                        "house": occ[p], "owns": owns[p], **lords[p],
                        "signifies": psig[p]} for p in PLANETS},
        "house_significators": sig,
        "node_agency": agents,
        "ruling_planets_at_birth": ruling,
    }
