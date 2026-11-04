"""Shadbala in virupas (60 virupas = 1 rupa), following the structure of BPHS
ch.27 as worked in B.V. Raman's 'Graha and Bhava Balas'.

Conventions that differ between texts/software are listed in CONVENTIONS and
echoed in the output. Not cross-checked against Jagannatha Hora: expect
agreement in structure, with possible differences of a few virupas in
Chesta and Kala bala."""
import math
from datetime import date
from .constants import (GRAHAS, SIGN_LORD, OWN_SIGNS, WEEKDAY_LORD, NAISARGIKA_BALA,
                        SHADBALA_REQUIRED_RUPAS)
from .chart import sign_of, deg_in_sign
from .vargas import varga_sign
from .dignity import rasi_dignity, exaltation_strength
from .aspects import virupa
from . import ephemeris as E
from .timeutil import to_local

CONVENTIONS = {
    "kendradi": "Sripati bhava placement",
    "dig_bala": "arc from the powerless bhava madhya / 3",
    "nathonnata": "from the Sun's true hour angle (apparent solar time)",
    "paksha": "benefics arc(Sun,Moon)/3, malefics 60 minus that; Moon's value doubled",
    "mercury_nature": "malefic when sharing a sign with Sun, Mars, Saturn, Rahu or Ketu",
    "moon_nature": "benefic when waxing (Moon-Sun elongation < 180)",
    "abda_masa": "weekday lord of the 360-day year / 30-day month start counted from the "
                 "Kali epoch (JDN 588466, a Friday)",
    "ayana": "declination of the ecliptic point (latitude ignored), 24-degree scale; Sun doubled",
    "chesta": "seeghra-kendra method rebuilt with modern elements (heliocentric longitude, "
              "mean Sun); Sun = ayana bala, Moon = paksha bala",
    "drik": "(sum of benefic minus malefic virupa aspects) / 4, nodes excluded",
    "yuddha": "planets within 1 degree; the one with greater sthana+dig+kala gains the difference",
}

SAPTAVARGA = [1, 2, 3, 7, 9, 12, 30]
REL_POINTS = {"great_friend": 20.0, "friend": 15.0, "neutral": 10.0, "enemy": 4.0,
              "great_enemy": 2.0}
DIG_POWERLESS_CUSP = {"Sun": 3, "Mars": 3, "Jupiter": 6, "Mercury": 6, "Moon": 9,
                      "Venus": 9, "Saturn": 0}   # index into bhava madhya (4th, 7th, 10th, 1st)
DAY_STRONG = {"Sun", "Jupiter", "Venus"}
NIGHT_STRONG = {"Moon", "Mars", "Saturn"}
KALI_JDN = 588466


def _mercury_benefic(chart):
    s = chart.sign("Mercury")
    return not any(chart.sign(m) == s for m in ("Sun", "Mars", "Saturn", "Rahu", "Ketu"))


def _moon_waxing(chart):
    return (chart.pos["Moon"] - chart.pos["Sun"]) % 360.0 < 180.0


def benefic_set(chart):
    b = {"Jupiter", "Venus"}
    if _mercury_benefic(chart):
        b.add("Mercury")
    if _moon_waxing(chart):
        b.add("Moon")
    return b


def _saptavargaja(chart, p, compound):
    total, detail = 0.0, {}
    for n in SAPTAVARGA:
        if n == 1:
            dg = rasi_dignity(p, chart.pos[p], compound, chart.config)
            s = chart.sign(p)
            if dg == "moolatrikona":
                v = 45.0
            elif s in OWN_SIGNS[p]:
                v = 30.0
            else:
                v = REL_POINTS[compound[p][SIGN_LORD[s]]]
        else:
            s = varga_sign(chart.pos[p], n)
            v = 30.0 if s in OWN_SIGNS[p] else REL_POINTS[compound[p][SIGN_LORD[s]]]
        detail[f"D{n}"] = v
        total += v
    return total, detail


def _chesta_kendra(chart, p):
    jd = chart.jd
    true = E.tropical_lon(jd, p)
    helio = E.heliocentric_lon(jd, p)
    msun = E.mean_sun_tropical(jd)
    if p in ("Mercury", "Venus"):
        mean, sighra = msun, helio
    else:
        mean, sighra = helio, msun
    avg = (mean + E.angdiff(true, mean) / 2.0) % 360.0
    ck = (sighra - avg) % 360.0
    if ck > 180.0:
        ck = 360.0 - ck
    return ck


def shadbala(chart, compound, day, hora_lord):
    cfg = chart.config
    res = {p: {} for p in GRAHAS}
    eps = E.obliquity(chart.jd)
    elong = E.angdist(chart.pos["Moon"], chart.pos["Sun"])
    benefics = benefic_set(chart)

    # ---- Kala: weekday, year and month lords
    vara_lord = WEEKDAY_LORD[day.vara]
    if day.sunrise is not None:
        vd = to_local(day.sunrise, chart.birth.local.tzinfo).date()
    else:
        vd = chart.birth.local.date()
    ahargana = vd.toordinal() + 1721425 - KALI_JDN
    abda_lord = WEEKDAY_LORD[(5 + 3 * (ahargana // 360)) % 7]
    masa_lord = WEEKDAY_LORD[(5 + 2 * (ahargana // 30)) % 7]

    hour_angle = E.angdiff(chart.armc, chart.planets["Sun"]["ra"])

    for p in GRAHAS:
        lon = chart.pos[p]
        r = res[p]
        # ---------------- Sthana
        uchcha = exaltation_strength(p, lon)
        sv, svd = _saptavargaja(chart, p, compound)
        even_want = p in ("Moon", "Venus")
        oja = 0.0
        for s in (chart.sign(p), varga_sign(lon, 9)):
            if (s % 2 == 1) == even_want:
                oja += 15.0
        bh = chart.bhava_of(lon)
        kendradi = 60.0 if bh in (1, 4, 7, 10) else (30.0 if bh in (2, 5, 8, 11) else 15.0)
        dk = int(deg_in_sign(lon) // 10)
        want = 0 if p in ("Sun", "Mars", "Jupiter") else (1 if p in ("Mercury", "Saturn") else 2)
        drek = 15.0 if dk == want else 0.0
        sthana = uchcha + sv + oja + kendradi + drek
        r["sthana"] = {"uchcha": uchcha, "saptavargaja": sv, "saptavargaja_detail": svd,
                       "ojayugma": oja, "kendradi": kendradi, "drekkana": drek, "total": sthana}

        # ---------------- Dig
        dig = E.angdist(lon, chart.bhava_madhya[DIG_POWERLESS_CUSP[p]]) / 3.0
        r["dig"] = dig

        # ---------------- Kala
        if p == "Mercury":
            nat = 60.0
        elif p in DAY_STRONG:
            nat = (180.0 - abs(hour_angle)) / 3.0
        else:
            nat = abs(hour_angle) / 3.0
        pb = elong / 3.0
        if p == "Moon":
            paksha = 2.0 * pb
        elif p in benefics:
            paksha = pb
        else:
            paksha = 60.0 - pb
        tri = 0.0
        if p == "Jupiter":
            tri = 60.0
        elif day.is_day is not None:
            parts = day.portions(3)
            k = next(i for i, (a, z) in enumerate(parts) if a <= chart.jd < z or i == 2)
            rulers = ["Mercury", "Sun", "Saturn"] if day.is_day else ["Moon", "Venus", "Mars"]
            tri = 60.0 if rulers[k] == p else 0.0
        abda = 15.0 if p == abda_lord else 0.0
        masa = 30.0 if p == masa_lord else 0.0
        vara = 45.0 if p == vara_lord else 0.0
        hora = 60.0 if p == hora_lord else 0.0
        trop = (lon + chart.ayanamsa) % 360.0
        kranti = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(trop))))
        if p == "Mercury":
            ayana = (24.0 + abs(kranti)) / 48.0 * 60.0
        elif p in ("Moon", "Saturn"):
            ayana = (24.0 - kranti) / 48.0 * 60.0
        else:
            ayana = (24.0 + kranti) / 48.0 * 60.0
        ayana_raw = ayana
        if p == "Sun":
            ayana *= 2.0
        kala = nat + paksha + tri + abda + masa + vara + hora + ayana
        r["kala"] = {"nathonnata": nat, "paksha": paksha, "tribhaga": tri, "abda": abda,
                     "masa": masa, "vara": vara, "hora": hora, "ayana": ayana,
                     "yuddha": 0.0, "total": kala}

        # ---------------- Chesta
        if p == "Sun":
            chesta = ayana_raw
        elif p == "Moon":
            chesta = paksha
        else:
            chesta = _chesta_kendra(chart, p) / 3.0
        r["chesta"] = chesta
        r["naisargika"] = NAISARGIKA_BALA[p]

        # ---------------- Drik
        drik = 0.0
        for q in GRAHAS:
            if q == p:
                continue
            v = virupa(q, chart.pos[q], lon)
            drik += v if q in benefics else -v
        r["drik"] = drik / 4.0

    # ---- Yuddha (planetary war)
    war = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    for i, a in enumerate(war):
        for b in war[i + 1:]:
            if E.angdist(chart.pos[a], chart.pos[b]) < 1.0:
                ta = res[a]["sthana"]["total"] + res[a]["dig"] + res[a]["kala"]["total"]
                tb = res[b]["sthana"]["total"] + res[b]["dig"] + res[b]["kala"]["total"]
                diff = abs(ta - tb)
                win, lose = (a, b) if ta >= tb else (b, a)
                res[win]["kala"]["yuddha"] += diff
                res[lose]["kala"]["yuddha"] -= diff
                res[win]["kala"]["total"] += diff
                res[lose]["kala"]["total"] -= diff

    out = {}
    for p in GRAHAS:
        r = res[p]
        total = (r["sthana"]["total"] + r["dig"] + r["kala"]["total"] + r["chesta"]
                 + r["naisargika"] + r["drik"])
        uch, ch = r["sthana"]["uchcha"], r["chesta"]
        ch_c = max(0.0, min(60.0, ch))
        out[p] = {**r, "total_virupas": total, "total_rupas": total / 60.0,
                  "required_rupas": SHADBALA_REQUIRED_RUPAS[p],
                  "strength_ratio": (total / 60.0) / SHADBALA_REQUIRED_RUPAS[p],
                  "ishta_phala": math.sqrt(uch * ch_c),
                  "kashta_phala": math.sqrt((60.0 - uch) * (60.0 - ch_c))}
    ranking = sorted(GRAHAS, key=lambda p: -out[p]["strength_ratio"])
    return {"planets": out, "ranking_by_ratio": ranking,
            "lords": {"vara": vara_lord, "hora": hora_lord, "abda": abda_lord, "masa": masa_lord},
            "conventions": CONVENTIONS}
