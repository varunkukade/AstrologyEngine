"""Special lagnas and upagrahas."""
from . import ephemeris as E
from .constants import SIGN_LORD, WEEKDAY_LORD, NAK_SPAN
from .chart import sign_of, position_summary

INDU_KALA = {"Sun": 30, "Moon": 16, "Mars": 6, "Mercury": 8, "Jupiter": 10,
             "Venus": 12, "Saturn": 1}


def special_lagnas(chart, day):
    ay = chart.ayanamsa_name
    out = {}
    if day.sunrise is not None:
        sun_sr = E.sid_lon(day.sunrise, "Sun", ay)
        minutes = (chart.jd - day.sunrise) * 1440.0
        # 1 sign per 5 ghatis (120 min), per 2.5 ghatis (60 min), per 1 ghati (24 min).
        out["bhava_lagna"] = position_summary((sun_sr + minutes * 30.0 / 120.0) % 360)
        out["hora_lagna"] = position_summary((sun_sr + minutes * 30.0 / 60.0) % 360)
        out["ghati_lagna"] = position_summary((sun_sr + minutes * 30.0 / 24.0) % 360)
        out["_basis"] = "Sun's sidereal longitude at the sunrise preceding birth"
    frac = (chart.pos["Moon"] % NAK_SPAN) / NAK_SPAN
    out["sree_lagna"] = position_summary((chart.asc + frac * 360.0) % 360)

    moon_s = chart.sign("Moon")
    l9 = SIGN_LORD[(chart.lagna + 8) % 12]
    m9 = SIGN_LORD[(moon_s + 8) % 12]
    r = (INDU_KALA[l9] + INDU_KALA[m9]) % 12 or 12
    indu = (moon_s + r - 1) % 12
    out["indu_lagna"] = {"sign_index": indu, "sign": position_summary(indu * 30.0)["sign"],
                         "ninth_lord_from_lagna": l9, "ninth_lord_from_moon": m9}

    if day.sunrise is not None:
        # Pranapada (BPHS 3.71-74): vighatis since sunrise / 15 = signs (2 deg per
        # vighati), added to the Sun if it is in a movable sign, to the 9th from it
        # if fixed, to the 5th from it if dual.
        vighatis = (chart.jd - day.sunrise) * 86400.0 / 24.0
        offset = [0.0, 240.0, 120.0][chart.sign("Sun") % 3]
        out["pranapada"] = position_summary((chart.pos["Sun"] + 2.0 * vighatis + offset) % 360)
        out["pranapada"]["basis"] = "Sun's longitude at birth (BPHS); vighatis from the preceding sunrise"
        out["varnada_lagna"] = varnada(chart, out["hora_lagna"]["longitude"])
    return out


def varnada(chart, hora_lagna_lon):
    """Varnada lagna from lagna and hora lagna. Two published methods differ, both given.
    B.V. Raman (sign counts): count Aries->sign for odd signs or Pisces->sign (backward)
    for even, for both lagnas; add the counts if their parity matches, else take the
    difference; count that from Aries (odd lagna) or backward from Pisces (even lagna).
    Sanjay Rath (longitudes): the same with full longitudes, reflected for even signs."""
    L, H = chart.lagna, int(hora_lagna_lon // 30) % 12
    cnt = lambda s: s + 1 if s % 2 == 0 else 12 - s
    c1, c2 = cnt(L), cnt(H)
    c = (c1 + c2) % 12 if (L % 2) == (H % 2) else abs(c1 - c2) % 12
    c = c or 12
    sign = (c - 1) % 12 if L % 2 == 0 else (12 - c) % 12
    raman = position_summary(sign * 30.0 + chart.asc % 30)
    a = chart.asc if L % 2 == 0 else 360.0 - chart.asc
    h = hora_lagna_lon if H % 2 == 0 else 360.0 - hora_lagna_lon
    v = (a + h) % 360 if (L % 2) == (H % 2) else abs(a - h) % 360
    if L % 2 == 1:
        v = 360.0 - v
    rath = position_summary(v % 360)
    return {"bv_raman": raman, "sanjay_rath": rath,
            "note": "authors disagree on Varnada; both published methods are given"}


def upagrahas(chart, day):
    out = {}
    sun = chart.pos["Sun"]
    dhuma = (sun + 133.0 + 20.0 / 60.0) % 360
    vyatipata = (360.0 - dhuma) % 360
    parivesha = (vyatipata + 180.0) % 360
    indrachapa = (360.0 - parivesha) % 360
    upaketu = (indrachapa + 16.0 + 40.0 / 60.0) % 360
    for n, v in (("Dhuma", dhuma), ("Vyatipata", vyatipata), ("Parivesha", parivesha),
                 ("Indrachapa", indrachapa), ("Upaketu", upaketu)):
        out[n] = position_summary(v)

    parts = day.portions(8)
    if parts is not None:
        start = day.vara if day.is_day else (day.vara + 4) % 7
        lords = [WEEKDAY_LORD[(start + i) % 7] for i in range(7)] + [None]
        k = lords.index("Saturn")
        a, z = parts[k]
        b = chart.birth
        out["Gulika"] = position_summary(E.ascendant(a, b.lat, b.lon, chart.ayanamsa_name))
        out["Mandi"] = position_summary(E.ascendant((a + z) / 2, b.lat, b.lon, chart.ayanamsa_name))
        out["_gulika_mandi_basis"] = ("lagna rising at the start (Gulika) and middle (Mandi) "
                                      "of Saturn's eighth of the birth day/night")
        for name, lord in (("Kala", "Sun"), ("Mrityu", "Mars"), ("Ardhaprahara", "Mercury"),
                           ("Yamaghantaka", "Jupiter")):
            a, z = parts[lords.index(lord)]
            out[name] = position_summary(E.ascendant((a + z) / 2, b.lat, b.lon, chart.ayanamsa_name))
        out["_kala_group_basis"] = ("lagna rising at the middle of the eighth ruled by Sun (Kala), "
                                    "Mars (Mrityu), Mercury (Ardhaprahara), Jupiter (Yamaghantaka)")
    return out
