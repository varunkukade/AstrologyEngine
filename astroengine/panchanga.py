"""Sunrise-based Vedic day and the birth panchanga.

The Vedic weekday (vara) runs sunrise to sunrise, so a birth at 03:00 on a
civil Tuesday is a Monday birth. Every time-of-day technique (hora, Gulika,
Kala bala, special lagnas) is built on this."""
from . import ephemeris as E
from .constants import (WEEKDAYS, WEEKDAY_LORD, CHALDEAN, TITHIS, YOGAS, KARANA_MOVABLE,
                        NAK_SPAN, NAKSHATRAS, SIGNS, MASA_BY_SUN_SIGN, RAHU_KALAM_PART,
                        GULIKA_KALAM_PART, YAMAGANDA_PART, VARNA)
from .chart import sign_of, nakshatra_of
from .timeutil import iso, to_local


class SolarDay:
    """Sunrise before birth, sunset, next sunrise; None fields at polar latitudes."""

    def __init__(self, chart):
        b = chart.birth
        mode = chart.config.sunrise
        jd = chart.jd
        rise = lambda t: E.rise_set(t, b.lat, b.lon, b.alt, "rise", mode)
        sset = lambda t: E.rise_set(t, b.lat, b.lon, b.alt, "set", mode)
        prev, t = None, jd - 2.0
        for _ in range(6):
            r = rise(t)
            if r is None or r > jd:
                nxt = r
                break
            prev, t = r, r + 0.01
        else:
            nxt = None
        self.sunrise = prev
        self.next_sunrise = nxt if prev is not None else None
        self.sunset = sset(prev) if prev is not None else None
        self.polar = (self.sunrise is None or self.sunset is None or self.next_sunrise is None
                      or self.sunset > self.next_sunrise)
        if self.polar:
            self.is_day = None
        else:
            self.is_day = self.sunrise <= jd < self.sunset
        tz = b.local.tzinfo
        if self.sunrise is not None:
            wd = to_local(self.sunrise, tz).weekday()
        else:
            wd = b.local.weekday()
        self.vara = (wd + 1) % 7       # Sunday = 0
        self.mode = mode

    def portions(self, n=8):
        """(start, end) jd of the n equal parts of the birth half (day or night)."""
        if self.polar:
            return None
        a, z = (self.sunrise, self.sunset) if self.is_day else (self.sunset, self.next_sunrise)
        w = (z - a) / n
        return [(a + i * w, a + (i + 1) * w) for i in range(n)]


def _elong(jd, ay):
    return (E.sid_lon(jd, "Moon", ay) - E.sid_lon(jd, "Sun", ay)) % 360.0


def _yoga_sum(jd, ay):
    return (E.sid_lon(jd, "Moon", ay) + E.sid_lon(jd, "Sun", ay)) % 360.0


def _span(f, jd, unit, step, maxd):
    v = f(jd)
    k = int(v // unit)
    start = E.find_crossing(f, jd, (k * unit) % 360.0, step, maxd, forward=False)
    end = E.find_crossing(f, jd, ((k + 1) * unit) % 360.0, step, maxd, forward=True)
    return k, start, end


def karana_name(k):
    if k == 0:
        return "Kimstughna"
    if k >= 57:
        return ["Shakuni", "Chatushpada", "Naga"][k - 57]
    return KARANA_MOVABLE[(k - 1) % 7]


def panchanga(chart, day):
    ay = chart.ayanamsa_name
    jd = chart.jd
    tz = chart.birth.local.tzinfo
    t = lambda x: iso(x, tz) if x is not None else None

    ti, ts, te = _span(lambda x: _elong(x, ay), jd, 12.0, 0.1, 3.0)
    tnum = ti + 1
    paksha = "Shukla" if tnum <= 15 else "Krishna"
    tname = ("Purnima" if tnum == 15 else "Amavasya" if tnum == 30
             else TITHIS[(tnum - 1) % 15])

    ni, ns, ne = _span(lambda x: E.sid_lon(x, "Moon", ay), jd, NAK_SPAN, 0.1, 2.0)
    yi, ys, ye = _span(lambda x: _yoga_sum(x, ay), jd, NAK_SPAN, 0.1, 2.0)
    ki, ks, ke = _span(lambda x: _elong(x, ay), jd, 6.0, 0.05, 1.5)

    # Lunar month (amanta): Sun's sign at the opening new moon; adhika if the
    # closing new moon finds the Sun in the same sign (no sankranti between).
    nm0 = E.find_crossing(lambda x: _elong(x, ay), jd, 0.0, 0.5, 32, forward=False)
    nm1 = E.find_crossing(lambda x: _elong(x, ay), jd, 0.0, 0.5, 32, forward=True)
    s0 = sign_of(E.sid_lon(nm0, "Sun", ay))
    s1 = sign_of(E.sid_lon(nm1, "Sun", ay))
    amanta = MASA_BY_SUN_SIGN[s0]
    purnimanta = amanta if paksha == "Shukla" else MASA_BY_SUN_SIGN[(s0 + 1) % 12]

    moon = nakshatra_of(chart.pos["Moon"])
    out = {
        "vara": {"weekday": WEEKDAYS[day.vara], "lord": WEEKDAY_LORD[day.vara],
                 "note": "Vedic day runs sunrise to sunrise"},
        "tithi": {"number": tnum, "name": tname, "paksha": paksha,
                  "elapsed_fraction": (_elong(jd, ay) % 12.0) / 12.0,
                  "start": t(ts), "end": t(te)},
        "nakshatra": {"number": ni + 1, "name": NAKSHATRAS[ni][0], "pada": moon["pada"],
                      "lord": NAKSHATRAS[ni][1], "start": t(ns), "end": t(ne)},
        "yoga": {"number": yi + 1, "name": YOGAS[yi], "start": t(ys), "end": t(ye)},
        "karana": {"number": ki + 1, "name": karana_name(ki), "start": t(ks), "end": t(ke)},
        "masa": {"amanta": amanta, "purnimanta": purnimanta, "adhika": s0 == s1,
                 "previous_new_moon": t(nm0), "next_new_moon": t(nm1)},
        "moon_sign_attributes": {"varna": VARNA[chart.sign("Moon") % 4],
                                 "gana": moon["gana"], "yoni": moon["yoni"], "nadi": moon["nadi"]},
        "sunrise": t(day.sunrise), "sunset": t(day.sunset), "next_sunrise": t(day.next_sunrise),
        "sunrise_definition": day.mode,
        "birth_in_daytime": day.is_day,
        "polar_no_sunrise": day.polar,
    }
    if not day.polar:
        dur_day = day.sunset - day.sunrise
        out["day_length_hours"] = dur_day * 24
        out["ishta_kala_ghatis"] = (jd - day.sunrise) * 60.0   # 1 day = 60 ghatis
        # Unequal horas: 12 per day, 12 per night, Chaldean order from the vara lord.
        if day.is_day:
            idx = int((jd - day.sunrise) / (dur_day / 12.0))
        else:
            idx = 12 + int((jd - day.sunset) / ((day.next_sunrise - day.sunset) / 12.0))
        idx = min(idx, 23)
        start = CHALDEAN.index(WEEKDAY_LORD[day.vara])
        out["hora"] = {"number": idx + 1, "lord": CHALDEAN[(start + idx) % 7],
                       "scheme": "unequal (day/12, night/12)"}
        eighth = dur_day / 8.0
        kal = {}
        for name, table in (("rahu_kalam", RAHU_KALAM_PART), ("gulika_kalam", GULIKA_KALAM_PART),
                            ("yamaganda", YAMAGANDA_PART)):
            k = table[day.vara] - 1
            a, z = day.sunrise + k * eighth, day.sunrise + (k + 1) * eighth
            kal[name] = {"start": t(a), "end": t(z), "birth_inside": a <= jd < z}
        out["day_periods"] = kal
    return out
