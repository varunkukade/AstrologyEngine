"""Run: python -m pytest -q tests"""
import json
import random
from datetime import datetime, timezone, timedelta

import pytest

from astroengine import ephemeris as E
from astroengine.compute import compute
from astroengine.config import DEFAULT, Config
from astroengine.timeutil import parse_birth, iso
from astroengine.chart import Chart
from astroengine.constants import SIGNS, PADA_SPAN, PLANETS, GRAHAS, VIM_YEARS
from astroengine import vargas as V
from astroengine.dignity import rasi_dignity, compound_relationships
from astroengine.panchanga import SolarDay, panchanga
from astroengine.aspects import virupa, rashi_drishti_signs
from astroengine.ashtakavarga import ashtakavarga, BAV_TOTALS
from astroengine import dashas as DS
from astroengine.kp import kp_lords
from astroengine.transits import ingresses_and_stations

DELHI = {"timezone": "Asia/Kolkata", "lat": 28.6139, "lon": 77.209}
IST = timezone(timedelta(hours=5.5))


def chart(date, time, **kw):
    b = parse_birth({"date": date, "time": time, **DELHI, **kw})
    return Chart(b, DEFAULT)


def minutes_between(iso_str, expected):
    return abs((datetime.fromisoformat(iso_str) - expected).total_seconds()) / 60.0


# ------------------------------------------------------------- ephemeris / time
def test_swiss_ephemeris_files_are_used():
    import swisseph as swe
    E.init()
    xs, rf = swe.calc_ut(2451545.0, swe.MOON, swe.FLG_SWIEPH)
    assert rf & swe.FLG_SWIEPH


def test_out_of_range_date_refuses_moshier():
    b = parse_birth({"date": "1700-01-01", "time": "12:00", **DELHI})
    with pytest.raises(E.EphemerisError):
        Chart(b, DEFAULT)


def test_historical_war_time_and_dst():
    b = parse_birth({"date": "1943-06-01", "time": "10:00", **DELHI})
    assert b.utc_offset_hours == 6.5            # India war time
    g = parse_birth({"date": "2021-03-14", "time": "02:30", "timezone": "America/New_York",
                     "lat": 40.7, "lon": -74})
    assert any("does not exist" in w for w in g.warnings)
    a = parse_birth({"date": "2021-11-07", "time": "01:30", "timezone": "America/New_York",
                     "lat": 40.7, "lon": -74})
    assert any("ambiguous" in w for w in a.warnings)


def test_legacy_birth_keys():
    b = parse_birth({"y": 1990, "mo": 1, "d": 1, "hh": 12, "mm": 0, "tz_offset": 5.5,
                     "lat": 28.6, "lon": 77.2})
    assert b.utc.hour == 6 and b.utc.minute == 30


# ------------------------------------------------------------- published reference values
def test_saturn_pisces_ingress_2025():
    b = parse_birth({"date": "2025-01-01", "time": "00:00", **DELHI})
    ing, _ = ingresses_and_stations("Saturn", b.jd_ut, b.jd_ut + 200, "lahiri", "mean")
    assert ing[0]["to"] == "Pisces"
    assert minutes_between(iso(ing[0]["jd"], IST), datetime(2025, 3, 29, 21, 44, tzinfo=IST)) < 3


def test_jupiter_atichara_2025():
    b = parse_birth({"date": "2025-01-01", "time": "00:00", **DELHI})
    ing, _ = ingresses_and_stations("Jupiter", b.jd_ut, b.jd_ut + 365, "lahiri", "mean")
    got = [(e["to"], iso(e["jd"], IST)[:10]) for e in ing]
    assert ("Cancer", "2025-10-18") in got and ("Gemini", "2025-12-05") in got


def test_diwali_2024_amavasya_tithi_times():
    c = chart("2024-11-01", "09:00")
    p = panchanga(c, SolarDay(c))
    assert p["tithi"]["name"] == "Amavasya"
    assert minutes_between(p["tithi"]["start"], datetime(2024, 10, 31, 15, 52, tzinfo=IST)) < 3
    assert minutes_between(p["tithi"]["end"], datetime(2024, 11, 1, 18, 16, tzinfo=IST)) < 3
    assert p["masa"]["amanta"] == "Ashvina"
    assert minutes_between(p["sunrise"], datetime(2024, 11, 1, 6, 33, tzinfo=IST)) < 2


def test_guru_purnima_2024():
    c = chart("2024-07-21", "09:00")
    p = panchanga(c, SolarDay(c))
    assert p["tithi"]["name"] == "Purnima" and p["masa"]["amanta"] == "Ashadha"
    assert minutes_between(p["tithi"]["start"], datetime(2024, 7, 20, 17, 59, tzinfo=IST)) < 3
    assert minutes_between(p["tithi"]["end"], datetime(2024, 7, 21, 15, 46, tzinfo=IST)) < 3


def test_vara_changes_at_sunrise_not_midnight():
    assert SolarDay(chart("1990-01-01", "12:00")).vara == 1     # Monday
    assert SolarDay(chart("1990-01-01", "03:00")).vara == 0     # still Sunday before sunrise


# ------------------------------------------------------------- vargas
@pytest.mark.parametrize("n,lon,expect", [
    (9, 0.0, "Aries"), (9, 30.0, "Capricorn"), (9, 60.0, "Libra"), (9, 90.0, "Cancer"),
    (10, 30.0, "Capricorn"), (3, 10.0, "Leo"), (3, 20.0, "Sagittarius"),
    (2, 0.0, "Leo"), (2, 15.0, "Cancer"), (2, 30.0, "Cancer"), (2, 45.0, "Leo"),
    (30, 4.99, "Aries"), (30, 5.0, "Aquarius"), (30, 29.9, "Libra"),
    (30, 30.0, "Taurus"), (30, 35.0, "Virgo"), (30, 59.9, "Scorpio"),
    (60, 0.5, "Taurus"), (27, 30.0, "Cancer"), (16, 30.0, "Leo"), (20, 30.0, "Sagittarius"),
    (20, 60.0, "Leo"), (24, 0.0, "Leo"), (24, 30.0, "Cancer"), (45, 60.0, "Sagittarius"),
    (40, 30.0, "Libra"), (7, 30.0, "Scorpio"), (12, 332.5, "Aries"), (4, 7.5, "Cancer"),
])
def test_varga_spot_values(n, lon, expect):
    assert SIGNS[V.varga_sign(lon, n)] == expect


def test_navamsa_equals_pada_index():
    rnd = random.Random(3)
    for _ in range(20000):
        lon = rnd.uniform(0, 360)
        assert V.d9(lon) == int(lon // PADA_SPAN) % 12


def test_vimshopaka_weights_sum_to_20():
    for w in V.VIMSHOPAKA_SCHEMES.values():
        assert abs(sum(w.values()) - 20) < 1e-9


# ------------------------------------------------------------- dignity
def test_partitioned_signs():
    c = chart("1990-01-01", "12:00")
    comp = compound_relationships(c)
    d = lambda p, lon: rasi_dignity(p, lon, comp, DEFAULT)
    assert d("Mercury", 160) == "exalted" and d("Mercury", 167) == "moolatrikona"
    assert d("Mercury", 175) == "own" and d("Moon", 32) == "exalted"
    assert d("Moon", 40) == "moolatrikona" and d("Sun", 190) == "debilitated"
    assert d("Sun", 125) == "moolatrikona" and d("Sun", 145) == "own"


# ------------------------------------------------------------- aspects
def test_virupa_continuous():
    for b in (30, 60, 90, 120, 150, 180, 300):
        assert abs(virupa("Sun", 0, b - 1e-7) - virupa("Sun", 0, b)) < 1e-4
    assert virupa("Sun", 0, 180) == 60 and virupa("Saturn", 0, 75) == 60


def test_rashi_drishti_symmetric():
    for a in range(12):
        for b in rashi_drishti_signs(a):
            assert a in rashi_drishti_signs(b)
        assert len(rashi_drishti_signs(a)) == 3


# ------------------------------------------------------------- ashtakavarga
def test_bav_totals_invariant_and_shodhana_bounds():
    rnd = random.Random(5)
    for _ in range(25):
        c = chart(f"{rnd.randint(1900, 2090)}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}",
                  f"{rnd.randint(0, 23):02d}:{rnd.randint(0, 59):02d}")
        a = ashtakavarga(c)
        assert a["bav_totals"] == BAV_TOTALS and a["sav_total"] == 337
        for p in GRAHAS:
            raw = a["_raw"]["bav"][p]
            red = list(a["shodhana"][p]["after_ekadhipatya"].values())
            assert all(0 <= r <= x for r, x in zip(red, raw))


# ------------------------------------------------------------- KP
def test_kp_sub_lords_boundaries():
    assert kp_lords(0.0) == {"sign_lord": "Mars", "star_lord": "Ketu", "sub_lord": "Ketu",
                             "sub_sub_lord": "Ketu"}
    span = 360 / 27
    ketu_sub = span * 7 / 120
    assert kp_lords(ketu_sub - 1e-9)["sub_lord"] == "Ketu"
    assert kp_lords(ketu_sub + 1e-9)["sub_lord"] == "Venus"
    assert kp_lords(span - 1e-9)["sub_lord"] == "Mercury"


# ------------------------------------------------------------- dashas
def _y(a, b):
    return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 86400 / 365.2425


def test_vimshottari_structure():
    c = chart("1990-01-01", "12:00")
    v = DS.vimshottari(c)
    mds = v["mahadashas"]
    assert abs(sum(m["years"] for m in mds[:9]) - 120) < 1e-9
    for m in mds:
        assert abs(_y(m["antardashas"][0]["start"], m["antardashas"][-1]["end"]) - m["years"]) < 1e-4
        assert m["antardashas"][0]["lord"] == m["lord"]
    assert datetime.fromisoformat(mds[0]["start"]) <= c.birth.local < datetime.fromisoformat(mds[0]["end"])
    path = DS.vimshottari_at(c, c.jd + 5000, 5)
    assert len(path) == 5
    for a, b in zip(path, path[1:]):
        assert a["start"] <= b["start"] and b["end"] <= a["end"] + 1e-9


def test_yogini_ashtottari_cycles():
    c = chart("1990-01-01", "12:00")
    y = DS.yogini(c, 1)
    assert abs(sum(m["years"] for m in y["mahadashas"]) - 36) < 1e-9
    a = DS.ashtottari(c, SolarDay(c))
    assert sum(m["years"] for m in a["mahadashas"][:8]) == 108


def test_chara_two_cycles_sum():
    rnd = random.Random(11)
    for _ in range(10):
        c = chart(f"{rnd.randint(1950, 2020)}-{rnd.randint(1, 12):02d}-10", f"{rnd.randint(0, 23):02d}:15")
        ch = DS.chara_dasha(c)["mahadashas"]
        by = {}
        for m in ch:
            by.setdefault(m["sign"], []).append(m["years"])
        for s, ys in by.items():
            assert sum(ys) in (12, 13, 11) or (len(ys) == 1 and ys[0] >= 12)
        assert sum(m["years"] for m in ch) >= 140


# ------------------------------------------------------------- full pipeline
def test_compute_full_and_json_serialisable():
    r = compute({"date": "1990-01-01", "time": "12:00", **DELHI, "gender": "female"},
                as_of=datetime(2026, 11, 4, tzinfo=timezone.utc))
    s = json.dumps(r)
    assert r["meta"]["zodiac"] == "sidereal" and r["birth"]["gender"] == "female"
    sens = r["birth_time_sensitivity"]["factors"]
    assert sens["D9_lagna"]["minutes_earlier"] == sens["lagna_nakshatra_pada"]["minutes_earlier"]
    assert len(r["dashas"]["vimshottari"]["running_at_reference"]) == 5
    assert "NaN" not in s


@pytest.mark.parametrize("seed", range(12))
def test_fuzz_extreme_locations(seed):
    rnd = random.Random(seed)
    lat = rnd.choice([rnd.uniform(-89.9, 89.9), 78.2, -77.8, 0.0, 66.6])
    b = {"date": f"{rnd.randint(1801, 2398)}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}",
         "time": f"{rnd.randint(0, 23):02d}:{rnd.randint(0, 59):02d}:{rnd.randint(0, 59):02d}",
         "tz_offset": rnd.choice([-12, -9.5, -5, 0, 3.5, 5.5, 5.75, 9, 14]),
         "lat": lat, "lon": rnd.uniform(-180, 180)}
    r = compute(b, as_of=datetime(2399, 1, 1, tzinfo=timezone.utc), transit_years=2)
    json.dumps(r)
