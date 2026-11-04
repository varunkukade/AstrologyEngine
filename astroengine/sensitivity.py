"""Birth-time sensitivity: how many minutes earlier/later the birth would have
to be for each time-critical factor to change. Lets a reader weigh results by
how much birth-time error they can survive."""
from . import ephemeris as E
from .constants import SIGNS, NAK_SPAN, PADA_SPAN, VIM_YEARS, VIM_ORDER, NAKSHATRAS
from .chart import sign_of
from .vargas import varga_sign
from .kp import kp_lords

WINDOW_MIN = 120.0
STEP_SEC = 10.0


def _pada(lon):
    i = int((lon % 360.0) // PADA_SPAN)
    return f"{NAKSHATRAS[i // 4][0]} pada {i % 4 + 1}"


def _state(jd, b, ay, kp_ay, node):
    asc = E.ascendant(jd, b.lat, b.lon, ay)
    moon = E.sid_lon(jd, "Moon", ay, node)
    st = {"lagna_sign": SIGNS[sign_of(asc)],
          "lagna_nakshatra_pada": _pada(asc),
          "D9_lagna": SIGNS[varga_sign(asc, 9)], "D10_lagna": SIGNS[varga_sign(asc, 10)],
          "D12_lagna": SIGNS[varga_sign(asc, 12)], "D60_lagna": SIGNS[varga_sign(asc, 60)],
          "moon_sign": SIGNS[sign_of(moon)], "moon_nakshatra_pada": _pada(moon)}
    cusps, _, _, _, _ = E.houses(jd, b.lat, b.lon, "P", kp_ay)
    for h in range(12):
        st[f"kp_cusp{h + 1}_sub_lord"] = kp_lords(cusps[h])["sub_lord"]
    return st


def sensitivity(chart):
    b, cfg = chart.birth, chart.config
    ay, kp_ay, node = chart.ayanamsa_name, cfg.kp_ayanamsa, cfg.node
    f = lambda jd: _state(jd, b, ay, kp_ay, node)
    base = f(chart.jd)
    step = STEP_SEC / 86400.0
    n = int(WINDOW_MIN * 60 / STEP_SEC)
    res = {k: {"value": v, "minutes_earlier": None, "minutes_later": None} for k, v in base.items()}
    for sgn, key in ((-1, "minutes_earlier"), (1, "minutes_later")):
        pending = set(base)
        prev_jd = chart.jd
        for i in range(1, n + 1):
            jd = chart.jd + sgn * i * step
            st = f(jd)
            for k in list(pending):
                if st[k] != base[k]:
                    a, z = prev_jd, jd          # a: same as base, z: changed
                    for _ in range(14):
                        m = (a + z) / 2
                        if f(m)[k] == base[k]:
                            a = m
                        else:
                            z = m
                    res[k][key] = abs(z - chart.jd) * 1440.0
                    pending.discard(k)
            prev_jd = jd
            if not pending:
                break
    for k in res:
        for key in ("minutes_earlier", "minutes_later"):
            if res[k][key] is None:
                res[k][key] = f">{WINDOW_MIN:g}"
    # Vimshottari: dasha dates shift by this many days per minute of birth-time error.
    moon_speed = E.sid_speed(chart.jd, "Moon", ay, node)
    lord = VIM_ORDER[int(chart.pos["Moon"] // NAK_SPAN) % 9]
    days_per_min = VIM_YEARS[lord] * cfg.dasha_year_days * (moon_speed / 1440.0) / NAK_SPAN
    return {"window_minutes": WINDOW_MIN, "factors": res,
            "vimshottari_dates_shift_days_per_minute": days_per_min,
            "note": "values in minutes of birth time; '>120' means stable over the window"}
