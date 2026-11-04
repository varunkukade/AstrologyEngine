"""BPHS conditional nakshatra dashas (ch.46). Each is computed for every chart
and carries its applicability test; BPHS prescribes a dasha only when its
condition holds, so read 'applicable' before using one.

Lord of the birth star: count from the seed star to the Moon's nakshatra (in
the stated direction) and take the remainder by the number of lords. Balance:
unexpired fraction of the birth nakshatra x the lord's years (Vimshottari
method). Shashtihayani instead allots groups of 3/4 stars in the 28-star
scheme (Abhijit included) and takes the balance over the group's arc, as
Ashtottari does. Antardashas start from the dasha lord and are proportional
to the lords' years."""
from .constants import NAK_SPAN, NAKSHATRAS, SIGN_LORD
from .vargas import d2, d9, d12
from .chart import house_from
from .timeutil import iso

# name: (lords with years in order, seed nakshatra index (0-based), direction)
CYCLE_DASHAS = {
    "shodashottari": ([("Sun", 11), ("Mars", 12), ("Jupiter", 13), ("Saturn", 14), ("Ketu", 15),
                       ("Moon", 16), ("Mercury", 17), ("Venus", 18)], 7, 1),
    "dwadashottari": ([("Sun", 7), ("Jupiter", 9), ("Ketu", 11), ("Mercury", 13), ("Rahu", 15),
                       ("Mars", 17), ("Saturn", 19), ("Moon", 21)], 26, -1),
    "panchottari": ([("Sun", 12), ("Mercury", 13), ("Saturn", 14), ("Mars", 15), ("Venus", 16),
                     ("Moon", 17), ("Jupiter", 18)], 16, 1),
    "shatabdika": ([("Sun", 5), ("Moon", 5), ("Venus", 10), ("Mercury", 10), ("Jupiter", 20),
                    ("Mars", 20), ("Saturn", 30)], 26, 1),
    "chaturashiti_sama": ([(p, 12) for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                             "Venus", "Saturn")], 14, 1),
    "dwisaptati_sama": ([(p, 9) for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                                          "Saturn", "Rahu")], 18, 1),
    "shattrimsha_sama": ([("Moon", 1), ("Sun", 2), ("Jupiter", 3), ("Mars", 4), ("Mercury", 5),
                          ("Saturn", 6), ("Venus", 7), ("Rahu", 8)], 21, 1),
}
TOTALS = {"shodashottari": 116, "dwadashottari": 112, "panchottari": 105, "shatabdika": 100,
          "chaturashiti_sama": 84, "dwisaptati_sama": 72, "shattrimsha_sama": 36}
for _k, (_l, _s, _d) in CYCLE_DASHAS.items():
    assert sum(y for _, y in _l) == TOTALS[_k], _k

# Shashtihayani: (lord, years, arc start, arc end). 28 stars from Ashwini in
# groups 3,4,3,4,...; Abhijit = 276deg40' - 280deg53'20" sits at the head of Saturn's group.
_N = NAK_SPAN
SHASHTIHAYANI = [("Jupiter", 10, 0 * _N, 3 * _N), ("Sun", 10, 3 * _N, 7 * _N),
                 ("Mars", 10, 7 * _N, 10 * _N), ("Moon", 6, 10 * _N, 14 * _N),
                 ("Mercury", 6, 14 * _N, 17 * _N), ("Venus", 6, 17 * _N, 276.0 + 40 / 60),
                 ("Saturn", 6, 276.0 + 40 / 60, 23 * _N), ("Rahu", 6, 23 * _N, 360.0)]
assert sum(x[1] for x in SHASHTIHAYANI) == 60


def applicability(chart, day):
    lagna, asc = chart.lagna, chart.asc
    waxing = (chart.pos["Moon"] - chart.pos["Sun"]) % 360 < 180
    hora = d2(asc)                     # 4 = Sun's hora (Leo), 3 = Moon's hora (Cancer)
    tenth = (lagna + 9) % 12
    lagna_lord, seventh_lord = SIGN_LORD[lagna], SIGN_LORD[(lagna + 6) % 12]
    return {
        "shodashottari": {"applicable": (hora == 4 and waxing) or (hora == 3 and not waxing),
                          "rule": "lagna in Sun's hora with Shukla paksha, or Moon's hora with Krishna paksha"},
        "dwadashottari": {"applicable": d9(asc) in (1, 6),
                          "rule": "lagna in a Venus navamsa (Taurus or Libra)"},
        "panchottari": {"applicable": d12(asc) == 3,
                        "rule": "lagna in Cancer dwadasamsa",
                        "lagna_also_in_cancer": lagna == 3,
                        "note": "some read BPHS as also requiring a Cancer lagna"},
        "shatabdika": {"applicable": d9(asc) == lagna, "rule": "lagna vargottama"},
        "chaturashiti_sama": {"applicable": chart.sign(SIGN_LORD[tenth]) == tenth,
                              "rule": "10th lord in the 10th"},
        "dwisaptati_sama": {"applicable": chart.sign(lagna_lord) == (lagna + 6) % 12
                            or chart.sign(seventh_lord) == lagna,
                            "rule": "lagna lord in 7th or 7th lord in lagna"},
        "shashtihayani": {"applicable": chart.sign("Sun") == lagna, "rule": "Sun in lagna"},
        "shattrimsha_sama": {"applicable": None if day.is_day is None else
                             ((day.is_day and hora == 4) or (not day.is_day and hora == 3)),
                             "rule": "day birth with lagna in Sun's hora, or night birth with lagna in Moon's hora"},
    }


def _tree(chart, lords, idx, t0, years_cover):
    f = lambda jd: iso(jd, chart.birth.local.tzinfo)
    yd = chart.config.dasha_year_days
    total = sum(y for _, y in lords)
    n = len(lords)
    out, t, k = [], t0, 0
    while t < chart.jd + years_cover * yd:
        lord, y = lords[(idx + k) % n]
        ads, ta = [], t
        for j in range(n):
            l2, y2 = lords[(idx + k + j) % n]
            span = y * y2 / total
            ads.append({"lord": l2, "start": f(ta), "end": f(ta + span * yd)})
            ta += span * yd
        ads[-1]["end"] = f(t + y * yd)
        out.append({"lord": lord, "years": y, "start": f(t), "end": f(t + y * yd), "antardashas": ads})
        t += y * yd
        k += 1
    return out


def conditional_dashas(chart, day, years_cover=120):
    yd = chart.config.dasha_year_days
    moon = chart.pos["Moon"]
    nak = int(moon // NAK_SPAN) % 27
    frac = (moon % NAK_SPAN) / NAK_SPAN
    app = applicability(chart, day)
    out = {}
    for name, (lords, seed, direc) in CYCLE_DASHAS.items():
        idx = ((nak - seed) * direc) % len(lords)
        lord, y = lords[idx]
        t0 = chart.jd - frac * y * yd
        out[name] = {**app[name], "total_years": TOTALS[name],
                     "seed_nakshatra": NAKSHATRAS[seed][0],
                     "count_direction": "forward" if direc == 1 else "backward",
                     "birth_lord": lord, "balance_at_birth_years": y * (1 - frac),
                     "mahadashas": _tree(chart, lords, idx, t0, years_cover)}
    lords = [(l, y) for l, y, _, _ in SHASHTIHAYANI]
    i, (lord, y, a, z) = next((i, g) for i, g in enumerate(SHASHTIHAYANI) if g[2] <= moon < g[3])
    gfrac = (moon - a) / (z - a)
    out["shashtihayani"] = {**app["shashtihayani"], "total_years": 60,
                            "scheme": "28 stars incl. Abhijit, groups of 3/4 from Ashwini; balance over the group's arc",
                            "birth_lord": lord, "balance_at_birth_years": y * (1 - gfrac),
                            "mahadashas": _tree(chart, lords, i, chart.jd - gfrac * y * yd, years_cover)}
    return out
