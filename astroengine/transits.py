"""Transit data (gochara) relative to the natal chart. Data only: which sign,
house, bindus, vedha, tara - no verdicts."""
import swisseph as swe
from . import ephemeris as E
from .constants import SIGNS, PLANETS, GRAHAS, NAK_SPAN, TARA_NAMES
from .chart import sign_of, house_from, nakshatra_of, dms
from .ashtakavarga import kakshya_of
from .timeutil import iso

GOCHARA_GOOD = {"Sun": [3, 6, 10, 11], "Moon": [1, 3, 6, 7, 10, 11], "Mars": [3, 6, 11],
                "Mercury": [2, 4, 6, 8, 10, 11], "Jupiter": [2, 5, 7, 9, 11],
                "Venus": [1, 2, 3, 4, 5, 8, 9, 11, 12], "Saturn": [3, 6, 11],
                "Rahu": [3, 6, 11], "Ketu": [3, 6, 11]}
# good house -> vedha (obstructing) house, counted from natal Moon (Phaladeepika ch.26)
VEDHA = {"Sun": {3: 9, 6: 12, 10: 4, 11: 5},
         "Moon": {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
         "Mars": {3: 12, 6: 9, 11: 5},
         "Mercury": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
         "Jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
         "Venus": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 6, 12: 3},
         "Saturn": {3: 12, 6: 9, 11: 5}, "Rahu": {3: 12, 6: 9, 11: 5},
         "Ketu": {3: 12, 6: 9, 11: 5}}
NO_VEDHA_BETWEEN = [{"Sun", "Saturn"}, {"Moon", "Mercury"}]

STEP = {"Moon": 0.25, "Sun": 0.5, "Mercury": 0.5, "Venus": 0.5, "Mars": 0.5,
        "Jupiter": 1.0, "Saturn": 1.0, "Rahu": 1.0, "Ketu": 1.0}


def _lon_speed(jd, p, ay, node):
    E.init()
    E.set_ayanamsa(ay)
    pid = E.node_id(node) if p in ("Rahu", "Ketu") else E.BODY[p]
    xs, rf = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
    E._check(rf, E.ALLOW_MOSHIER, p)
    lon = xs[0] % 360.0
    if p == "Ketu":
        lon = (lon + 180.0) % 360.0
    return lon, xs[3]


def ingresses_and_stations(p, jd0, jd1, ay, node, want_stations=True):
    """Sign ingresses (retrograde re-entries included) and retrograde/direct
    stations, each bisected to < 0.1 s. Sampling step is far below the time
    any of these bodies needs to traverse a sign."""
    step = STEP[p]
    ing, sta = [], []
    lon, spd = _lon_speed(jd0, p, ay, node)
    s_prev, v_prev, t_prev = sign_of(lon), spd, jd0
    t = jd0
    while t < jd1:
        t = min(t + step, jd1)
        lon, spd = _lon_speed(t, p, ay, node)
        s = sign_of(lon)
        if s != s_prev:
            a, b = t_prev, t
            for _ in range(45):
                m = (a + b) / 2
                if sign_of(_lon_speed(m, p, ay, node)[0]) == s_prev:
                    a = m
                else:
                    b = m
            ing.append({"jd": b, "from": SIGNS[s_prev], "to": SIGNS[s], "retrograde": spd < 0})
        if want_stations and p not in ("Rahu", "Ketu", "Sun", "Moon") and (spd < 0) != (v_prev < 0):
            a, b = t_prev, t
            for _ in range(45):
                m = (a + b) / 2
                if (_lon_speed(m, p, ay, node)[1] < 0) == (v_prev < 0):
                    a = m
                else:
                    b = m
            l_st = _lon_speed(b, p, ay, node)[0]
            sta.append({"jd": b, "type": "retrograde" if spd < 0 else "direct",
                        "sign": SIGNS[sign_of(l_st)], "degree": l_st % 30})
        s_prev, v_prev, t_prev = s, spd, t
    return ing, sta


def slow_planet_timeline(natal, years=100):
    tz = natal.birth.local.tzinfo
    ay, node = natal.ayanamsa_name, natal.config.node
    jd0, jd1 = natal.jd, natal.jd + years * 365.25
    moon = natal.sign("Moon")
    out = {}
    for p in ("Jupiter", "Saturn", "Rahu"):
        ing, sta = ingresses_and_stations(p, jd0, jd1, ay, node)
        for e in ing:
            si = SIGNS.index(e["to"])
            e.update({"time": iso(e["jd"], tz), "house_from_lagna": house_from(si, natal.lagna),
                      "house_from_moon": house_from(si, moon)})
        for e in sta:
            e["time"] = iso(e["jd"], tz)
        out[p] = {"sign_at_birth": SIGNS[natal.sign(p)], "ingresses": ing, "stations": sta}
        if p == "Rahu":
            out[p]["note"] = "Ketu is always the opposite sign"
    return out


SATURN_PHASES = {12: "Sade Sati phase 1 (12th from Moon)", 1: "Sade Sati phase 2 (over Moon)",
                 2: "Sade Sati phase 3 (2nd from Moon)", 4: "Kantaka Shani (4th from Moon)",
                 8: "Ashtama Shani (8th from Moon)"}


def saturn_phases(natal, saturn_ingresses, years=100):
    tz = natal.birth.local.tzinfo
    moon = natal.sign("Moon")
    cur_sign, cur_start = natal.sign("Saturn"), natal.jd
    spans = []
    for e in saturn_ingresses:
        spans.append((cur_start, e["jd"], cur_sign))
        cur_sign, cur_start = SIGNS.index(e["to"]), e["jd"]
    spans.append((cur_start, natal.jd + years * 365.25, cur_sign))
    out = []
    for a, z, s in spans:
        h = house_from(s, moon)
        if h not in SATURN_PHASES:
            continue
        lab = SATURN_PHASES[h]
        if out and out[-1]["label"] == lab and abs(out[-1]["_end"] - a) < 1e-6:
            out[-1]["_end"] = z
        else:
            out.append({"label": lab, "house_from_moon": h, "sign": SIGNS[s], "_start": a, "_end": z})
    for o in out:
        o["start"], o["end"] = iso(o.pop("_start"), tz), iso(o.pop("_end"), tz)
        o["note"] = "starts at birth" if o["start"] == iso(natal.jd, tz) else None
    return out


def snapshot(natal, jd, ashtaka):
    """Where every planet is at jd, relative to the natal chart."""
    tz = natal.birth.local.tzinfo
    ay, node = natal.ayanamsa_name, natal.config.node
    moon = natal.sign("Moon")
    bav, sav, pr = ashtaka["_raw"]["bav"], ashtaka["_raw"]["sav"], ashtaka["_raw"]["prastara"]
    pos, spd = {}, {}
    for p in PLANETS:
        pos[p], spd[p] = _lon_speed(jd, p, ay, node)
    hm = {p: house_from(sign_of(pos[p]), moon) for p in PLANETS}
    rows = {}
    for p in PLANETS:
        s = sign_of(pos[p])
        k = kakshya_of(pos[p])
        good = hm[p] in GOCHARA_GOOD[p]
        vedha_by = []
        if good:
            vh = VEDHA[p][hm[p]]
            vedha_by = [q for q in PLANETS if q != p and hm[q] == vh
                        and {p, q} not in NO_VEDHA_BETWEEN]
        near = {q: round(E.angdist(pos[p], natal.pos[q]), 3) for q in PLANETS
                if E.angdist(pos[p], natal.pos[q]) <= 5.0}
        if E.angdist(pos[p], natal.asc) <= 5.0:
            near["Lagna"] = round(E.angdist(pos[p], natal.asc), 3)
        row = {"longitude": pos[p], "sign": SIGNS[s], "dms": dms(pos[p] % 30),
               "nakshatra": nakshatra_of(pos[p])["name"], "retrograde": spd[p] < 0,
               "house_from_lagna": house_from(s, natal.lagna), "house_from_moon": hm[p],
               "sav_bindus_in_sign": sav[s],
               "kakshya": k, "within_5deg_of_natal": near,
               "gochara_favourable_house_from_moon": good,
               "vedha_obstructed_by": vedha_by}
        if p in bav:
            row["own_bav_bindus_in_sign"] = bav[p][s]
            lord = k["lord"]
            row["kakshya_lord_gives_bindu"] = bool(pr[p][lord][s])
        rows[p] = row
    birth_nak = int(natal.pos["Moon"] // NAK_SPAN)
    t_nak = int(pos["Moon"] // NAK_SPAN)
    tara = (t_nak - birth_nak) % 27 % 9
    return {"time": iso(jd, tz), "planets": rows,
            "tara_bala": {"tara": tara + 1, "name": TARA_NAMES[tara]},
            "chandra_bala_house_from_moon": hm["Moon"],
            "ayanamsa": ay}
