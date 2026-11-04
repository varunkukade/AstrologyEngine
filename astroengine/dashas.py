"""Dasha systems. All arithmetic is in Julian days (UT); output in local ISO time.

* Vimshottari (BPHS ch.46) to 5 levels.
* Yogini (36-year cycle) with antardashas.
* Ashtottari (108 years, Ardra-based groups) with antardashas and its
  applicability tests.
* Jaimini Chara dasha, K.N. Rao's method: two cycles, exaltation/debilitation
  year adjustment, stronger co-lord for Scorpio/Aquarius, antardashas.
"""
from .constants import SIGNS, VIM_ORDER, VIM_YEARS, NAK_SPAN, SAVYA, SIGN_LORD
from .chart import sign_of, house_from
from .dignity import exaltation_sign, debilitation_sign
from .jaimini import stronger_lord
from .timeutil import iso


def _fmt(tz):
    return lambda jd: iso(jd, tz)


# ---------------------------------------------------------------- Vimshottari
def _vim_children(lord, start, span_years, yd):
    out, t = [], start
    i = VIM_ORDER.index(lord)
    for k in range(9):
        l = VIM_ORDER[(i + k) % 9]
        yrs = span_years * VIM_YEARS[l] / 120.0
        out.append({"lord": l, "start": t, "end": t + yrs * yd, "years": yrs})
        t += yrs * yd
    return out


def vimshottari_base(chart):
    moon = chart.pos["Moon"]
    idx = int(moon // NAK_SPAN) % 27
    lord = VIM_ORDER[idx % 9]
    frac = (moon % NAK_SPAN) / NAK_SPAN
    yd = chart.config.dasha_year_days
    md_start = chart.jd - frac * VIM_YEARS[lord] * yd
    mds, t, i = [], md_start, VIM_ORDER.index(lord)
    while t < chart.jd + 120 * yd:
        l = VIM_ORDER[i % 9]
        y = VIM_YEARS[l]
        mds.append({"lord": l, "start": t, "end": t + y * yd, "years": float(y)})
        t += y * yd
        i += 1
    return {"lord": lord, "nakshatra_index": idx, "fraction_elapsed": frac,
            "balance_years": VIM_YEARS[lord] * (1 - frac), "mahadashas": mds}


def vimshottari_at(chart, jd, depth=5, base=None):
    base = base or vimshottari_base(chart)
    yd = chart.config.dasha_year_days
    level, path = base["mahadashas"], []
    for _ in range(depth):
        node = next((n for n in level if n["start"] <= jd < n["end"]), None)
        if node is None:
            break
        path.append(node)
        level = _vim_children(node["lord"], node["start"], node["years"], yd)
    return path


def vimshottari(chart, ref_jd=None):
    tz = chart.birth.local.tzinfo
    f = _fmt(tz)
    yd = chart.config.dasha_year_days
    base = vimshottari_base(chart)
    tree = []
    for md in base["mahadashas"]:
        ads = []
        for ad in _vim_children(md["lord"], md["start"], md["years"], yd):
            pds = [{"lord": pd["lord"], "start": f(pd["start"]), "end": f(pd["end"])}
                   for pd in _vim_children(ad["lord"], ad["start"], ad["years"], yd)]
            ads.append({"lord": ad["lord"], "start": f(ad["start"]), "end": f(ad["end"]),
                        "pratyantardashas": pds})
        tree.append({"lord": md["lord"], "years": md["years"], "start": f(md["start"]),
                     "end": f(md["end"]), "antardashas": ads})
    out = {"birth_nakshatra_lord": base["lord"],
           "balance_at_birth_years": base["balance_years"],
           "year_length_days": yd, "mahadashas": tree}
    if ref_jd is not None:
        out["running_at_reference"] = [
            {"level": i + 1, "lord": n["lord"], "start": f(n["start"]), "end": f(n["end"])}
            for i, n in enumerate(vimshottari_at(chart, ref_jd, 5, base))]
    return out


# ---------------------------------------------------------------- Yogini
YOGINIS = [("Mangala", "Moon", 1), ("Pingala", "Sun", 2), ("Dhanya", "Jupiter", 3),
           ("Bhramari", "Mars", 4), ("Bhadrika", "Mercury", 5), ("Ulka", "Saturn", 6),
           ("Siddha", "Venus", 7), ("Sankata", "Rahu", 8)]


def yogini(chart, cycles=3):
    f = _fmt(chart.birth.local.tzinfo)
    yd = chart.config.dasha_year_days
    moon = chart.pos["Moon"]
    nk = int(moon // NAK_SPAN) % 27
    idx = (nk + 3) % 8          # (nakshatra number + 3) mod 8, 1 = Mangala
    frac = (moon % NAK_SPAN) / NAK_SPAN
    t = chart.jd - frac * YOGINIS[idx][2] * yd
    out = []
    for k in range(8 * cycles):
        name, lord, yrs = YOGINIS[(idx + k) % 8]
        ads, ta = [], t
        for j in range(8):
            n2, l2, y2 = YOGINIS[(idx + k + j) % 8]
            span = yrs * y2 / 36.0
            ads.append({"yogini": n2, "lord": l2, "start": f(ta), "end": f(ta + span * yd)})
            ta += span * yd
        out.append({"yogini": name, "lord": lord, "years": yrs, "start": f(t),
                    "end": f(t + yrs * yd), "antardashas": ads})
        t += yrs * yd
    return {"balance_at_birth_years": YOGINIS[idx][2] * (1 - frac), "mahadashas": out}


# ---------------------------------------------------------------- Ashtottari
ASHT_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Saturn", "Jupiter", "Rahu", "Venus"]
ASHT_YEARS = {"Sun": 6, "Moon": 15, "Mars": 8, "Mercury": 17, "Saturn": 10,
              "Jupiter": 19, "Rahu": 12, "Venus": 21}
# From Ardra: 4,3,4,3,4,3,4,3 in the 28-star scheme. Abhijit lies inside
# Saturn's arc, so folding it into UAsh/Shravana leaves every arc unchanged.
ASHT_GROUPS = [("Sun", [5, 6, 7, 8]), ("Moon", [9, 10, 11]), ("Mars", [12, 13, 14, 15]),
               ("Mercury", [16, 17, 18]), ("Saturn", [19, 20, 21]),
               ("Jupiter", [22, 23, 24]), ("Rahu", [25, 26, 0, 1]), ("Venus", [2, 3, 4])]


def ashtottari(chart, day):
    f = _fmt(chart.birth.local.tzinfo)
    yd = chart.config.dasha_year_days
    moon = chart.pos["Moon"]
    nk = int(moon // NAK_SPAN) % 27
    lord, grp = next((l, g) for l, g in ASHT_GROUPS if nk in g)
    frac = (grp.index(nk) + (moon % NAK_SPAN) / NAK_SPAN) / len(grp)
    t = chart.jd - frac * ASHT_YEARS[lord] * yd
    i = ASHT_ORDER.index(lord)
    out = []
    for k in range(9):
        l = ASHT_ORDER[(i + k) % 8]
        y = ASHT_YEARS[l]
        ads, ta = [], t
        for j in range(8):
            l2 = ASHT_ORDER[(i + k + j) % 8]
            span = y * ASHT_YEARS[l2] / 108.0
            ads.append({"lord": l2, "start": f(ta), "end": f(ta + span * yd)})
            ta += span * yd
        out.append({"lord": l, "years": y, "start": f(t), "end": f(t + y * yd), "antardashas": ads})
        t += y * yd
    lagna_lord = SIGN_LORD[chart.lagna]
    rh = house_from(chart.sign("Rahu"), chart.sign(lagna_lord))
    waxing = (chart.pos["Moon"] - chart.pos["Sun"]) % 360 < 180
    rule_a = rh in (1, 4, 5, 7, 9, 10) and chart.house("Rahu") != 1
    rule_b = None if day.is_day is None else ((day.is_day and not waxing) or
                                              (not day.is_day and waxing))
    return {"balance_at_birth_years": ASHT_YEARS[lord] * (1 - frac), "mahadashas": out,
            "applicability": {
                "rahu_in_kendra_or_trikona_from_lagna_lord_not_in_lagna": rule_a,
                "rahu_house_from_lagna_lord": rh,
                "day_birth_krishna_or_night_birth_shukla": rule_b,
                "note": "BPHS makes Ashtottari conditional; texts differ on which test applies"}}


# ---------------------------------------------------------------- Chara (K.N. Rao)
def _chara_years(chart, s):
    lord, why = stronger_lord(chart, s)
    ls = chart.sign(lord)
    if s in SAVYA:
        count = (ls - s) % 12 + 1
    else:
        count = (s - ls) % 12 + 1
    yrs = count - 1
    adj = None
    if yrs == 0:
        yrs = 12
    else:
        if ls == exaltation_sign(lord, chart.config):
            yrs, adj = yrs + 1, "+1 (lord exalted)"
        elif ls == debilitation_sign(lord, chart.config):
            yrs, adj = yrs - 1, "-1 (lord debilitated)"
    return yrs, lord, why, adj


def chara_dasha(chart):
    f = _fmt(chart.birth.local.tzinfo)
    yd = chart.config.dasha_year_days
    ninth = (chart.lagna + 8) % 12
    forward = ninth in SAVYA
    seq = [(chart.lagna + (k if forward else -k)) % 12 for k in range(12)]
    first = {s: _chara_years(chart, s) for s in seq}
    periods, t = [], chart.jd
    for cycle in (1, 2):
        for s in seq:
            y1, lord, why, adj = first[s]
            yrs = y1 if cycle == 1 else 12 - y1
            if yrs <= 0:
                continue
            ad_fwd = s in SAVYA
            ads, ta = [], t
            for k in range(1, 13):
                a = (s + (k if ad_fwd else -k)) % 12
                ads.append({"sign": SIGNS[a], "start": f(ta), "end": f(ta + yrs / 12.0 * yd)})
                ta += yrs / 12.0 * yd
            periods.append({"cycle": cycle, "sign": SIGNS[s], "house_from_lagna": house_from(s, chart.lagna),
                            "years": yrs, "lord": lord, "lord_choice": why, "adjustment": adj if cycle == 1 else None,
                            "start": f(t), "end": f(t + yrs * yd), "antardashas": ads})
            t += yrs * yd
    return {"method": "K.N. Rao: order from the 9th house's footedness, years counted by "
                      "each sign's footedness, exalted +1 / debilitated -1, second cycle = "
                      "12 - first; antardashas begin from the next sign in the dasha sign's "
                      "direction and end with the dasha sign",
            "direction": "zodiacal" if forward else "anti-zodiacal",
            "mahadashas": periods}
