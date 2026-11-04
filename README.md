# astroengine — Vedic astrology calculation engine

Input: birth date, time, timezone, latitude/longitude, gender.
Output: one JSON document holding every astronomical and astrological factor a
Parashari, Jaimini, KP or Tajika reading needs. **The engine computes; it never
interprets or predicts.** The output is meant to be read by a person or an AI that
does the interpretation.

Positions come from the Swiss Ephemeris. The data files are bundled (1800–2399 CE),
and the engine **refuses to run on the Moshier fallback** unless told to.

## Setup

```bash
pip install -r requirements.txt          # Python 3.9+
cp birth.example.json birth.json         # edit with real data; birth.json is git-ignored
```

## Run

```bash
python -m astroengine birth.json --summary                      # short human overview
python -m astroengine birth.json --out chart.json               # full JSON
python -m astroengine birth.json --as-of 2026-11-04T12:00:00+05:30 --out chart.json
python -m astroengine birth.json --set ayanamsa=raman --set node=true
python -m pytest -q tests                                       # test suite
```

From Python:

```python
from datetime import datetime, timezone
from astroengine import compute, Config
data = compute({"date": "1990-01-01", "time": "12:00:00", "timezone": "Asia/Kolkata",
                "lat": 28.6139, "lon": 77.209, "gender": "female"},
               Config(), as_of=datetime.now(timezone.utc))
```

### Birth input

| key | required | notes |
|---|---|---|
| `date` | yes | `YYYY-MM-DD` |
| `time` | yes | `HH:MM` or `HH:MM:SS` local civil time |
| `timezone` | one of these two | IANA name, e.g. `Asia/Kolkata`. Applies historical DST and India's 1942–45 war time (+6:30). **Preferred.** |
| `tz_offset` | | fixed hours from UTC; no historical correction (a warning is emitted) |
| `lat`, `lon` | yes | decimal degrees, north/east positive |
| `alt` | no | metres, used for sunrise |
| `gender` | no | `male`/`female`/`other`/`unspecified`. Carried as metadata; no classical calculation in this engine changes with it |
| `fold` | no | `0`/`1` to choose between the two readings of a local time repeated at a DST change |

Old keys (`y, mo, d, hh, mm, tz_offset`) are still accepted. Times that don't exist
(DST gaps) or are ambiguous (DST overlaps) produce warnings in the output.

## What the output contains

| section | contents |
|---|---|
| `birth`, `ayanamsa`, `meta` | UTC, Julian day, ΔT, LMT, ayanamsa value, ephemeris files, **every convention used** |
| `lagna`, `midheaven`, `planets` | sidereal longitude, sign, nakshatra/pada with deity/gana/yoni/nadi, latitude, declination, RA, speed, retrograde, dignity (degree-aware), Uchcha bala, combustion with orb, Baladi/Jagradadi avasthas, gandanta, distance from sign edge, whole-sign and Sripati houses, houses ruled |
| `planetary_war` | pairs within 1° with latitude, declination and magnitude (texts disagree on which decides the winner) |
| `houses` | whole-sign houses with occupants; Sripati bhava madhya/sandhi |
| `relationships` | natural, temporary and compound (five-fold) friendship |
| `vargas`, `vargottama`, `vimshopaka_bala` | all 16 Shodashavarga charts with the degree inside each varga, D60 deities; Vimshopaka on the 6/7/10/16-varga schemes |
| `panchanga` | sunrise-based vara, tithi, nakshatra, yoga and karana with start/end times, amanta/purnimanta month and adhika flag, hora lord, Rahu kalam / Gulika kalam / Yamaganda, ishta kala |
| `special_lagnas`, `upagrahas` | Bhava, Hora, Ghati, Sree and Indu lagnas; Gulika, Mandi, Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu |
| `aspects` | graha drishti (sign), drishti strength in virupas, Jaimini rashi drishti, argala/virodhargala |
| `ashtakavarga` | BAV, SAV (by sign and by house), prastara, trikona and ekadhipatya shodhana, shodhya pinda, kakshya order |
| `shadbala` | all six balas with sub-components, rupas, required minimum, ratio, Ishta/Kashta phala |
| `yogas` | Raja (incl. Yogakaraka), Dhana, Pancha Mahapurusha, Vipreeta, lunar (Gaja Kesari, Sunapha/Anapha/Durudhara, Kemadruma with cancellation factors, Adhi, Shakata, Amala, Chandra-Mangala), solar (Vesi/Vasi/Ubhayachari, Budhaditya), Parivartana (Maha/Khala/Dainya), Nabhasa Sankhya and Ashraya, Kartari, node yogas; Neecha bhanga as a checklist of 10+ rules; Mangal dosha from lagna/Moon/Venus. Each result names its source rule |
| `dashas` | Vimshottari (MD/AD/PD for the whole life, 5 levels at `as_of`), Yogini with ADs, Ashtottari with ADs and its applicability tests, Chara (K.N. Rao: both cycles, ±1 year for exalted/debilitated lords, ADs), Narayana (seed sign with the strength rule that decided it, Saturn/Ketu exceptions, both cycles, ADs), Kalachakra (Moon's pada cycle, savya/apasavya group, paramayush, balance, continuation through later padas, ADs, sign jump between consecutive dashas), and the Jaimini ayur dashas Sthira (7/8/9 years from Brahma's sign), Shoola (9 years each from the stronger of lagna/7th) and Brahma (years from each sign's 6th lord), each with a caution that they are not lifespan estimates |
| `jaimini` | chara karakas (8- and 7-karaka schemes, near-tie flags), stronger co-lord of Scorpio/Aquarius with the reason, all 12 arudha padas incl. AL and UL, Karakamsha, Swamsha, Brahma (candidates, scores, deciding rule) |
| `kp` | KP ayanamsa + Placidus cusps; sign/star/sub/sub-sub lords for cusps and planets; four-level house significators with node agency; each planet's significations; cusp sub-lord significations; ruling planets at birth |
| `transits` | snapshot at `as_of` (house from lagna/Moon, SAV/BAV bindus, kakshya and whether its lord gives a bindu, gochara-favourable flag, vedha, Tara bala, Chandra bala, natal points within 5°); lifetime Jupiter/Saturn/Rahu ingresses and Jupiter/Saturn stations, timed to the second; Sade Sati, Kantaka and Ashtama Shani periods |
| `varshaphala` | running and next sidereal solar return: varsha lagna, planets, Muntha, four office-holders, Tajika aspects marked applying (ithasala) or separating (ishrafa) |
| `birth_time_sensitivity` | minutes earlier/later at which the lagna sign, lagna pada, D9/D10/D12/D60 lagna, Moon sign/pada and each KP cusp sub-lord change; days of dasha shift per minute of birth-time error |

**Read the sensitivity block before trusting fine-grained output.** The D60 lagna
changes about every 2 minutes and KP cusp sub-lords often change within a minute or
two. An unrectified birth time can't support conclusions drawn from those factors.

## Conventions (all in `astroengine/config.py`, all echoed in `meta.config`)

| setting | default | alternatives |
|---|---|---|
| `ayanamsa` | `lahiri` (true, i.e. with nutation, consistent with the positions) | `lahiri_icrc`, `raman`, `kp`, `kp_vp291`, `true_chitra`, `yukteshwar`, `fagan_bradley` |
| `kp_ayanamsa` | `kp` (Krishnamurti) — KP sections always use this, never Lahiri | `kp_vp291` |
| `node` | `mean` | `true` |
| `dasha_year_days` | 365.2425 | 365.25, 360 |
| `sunrise` | `upper_limb_refraction` (modern panchang sunrise) | `disc_centre_no_refraction` (classical Hindu rising) |
| `node_aspects` | `5_7_9` | `7` |
| `node_exaltation` | `taurus_scorpio` | `gemini_sagittarius` |
| `chara_karaka_scheme` | 8 | 7 (both are output; this picks the primary one) |
| `include_outer_planets` | false | true (Uranus/Neptune/Pluto, reported separately) |

Other fixed choices, stated in the output where they apply:
- Gulika is the lagna at the start of Saturn's portion; Mandi is the lagna at its middle.
- Horas are unequal (day ÷ 12, night ÷ 12).
- Shadbala's conventions are listed in `shadbala.conventions`.
- Ekadhipatya shodhana follows B.V. Raman's rules.
- Chara dasha follows K.N. Rao's method.
- KP node agency covers the node's sign lord, the planets conjoined with it and the planets aspecting it.

## Validation

`tests/` holds 66 tests:
- **Published values:**
  - Saturn's sidereal Pisces ingress: 29 Mar 2025 21:45 IST, published 21:44.
  - Jupiter's 2025 atichara: Cancer on 18 Oct, back to Gemini on 5 Dec.
  - Diwali 2024 Amavasya tithi: 15:53 to 18:17 IST, published 15:52 to 18:16.
  - Guru Purnima 2024 tithi times.
  - Delhi sunrise, and the weekday changing at sunrise.
- **Structural invariants:**
  - Navamsa sign equals the pada index mod 12 (checked on 20,000 random points).
  - BAV totals stay at 48/49/39/54/56/52/39 = 337 on every chart.
  - Shodhana never increases a bindu count.
  - Dasha periods nest and sum (120, 108, 36 years).
  - Rashi drishti is symmetric and virupa strength is continuous.
  - KP sub-lords fall on the right side of their boundaries.
- **Fuzzing:** charts at extreme latitudes (including polar day and night) across 1801–2398. A separate run of 400 random charts with random conventions produced no failures.

The KP star/sub/sub-sub arithmetic matches the previous engine on 200,000 random
longitudes. Planet positions match it to within 0.5″; the gap is the Moshier
fallback the old code used without saying so.

**Not cross-checked against Jagannatha Hora or another commercial program** (none could
be run here). Expect differences of a few virupas in Shadbala (Chesta and Kala bala
depend on implementation details) and on any rule where schools differ. The output
labels which one was used.

### How Narayana and Kalachakra were checked

- **Narayana:** the dasha order is generated from the rules (movable signs
  consecutive, fixed signs every 6th, dual signs by trines grouped in kendras,
  Saturn/Ketu exceptions). It reproduces all 36 rows of Jagannatha Hora's sequence
  tables as published in the open-source PyJHora project. Sign strength uses Rath's six
  rules, and the output names the rule that decided the seed.
- **Kalachakra:** sign years and the 16 pada cycles follow BPHS. Every cycle is checked at
  import to sum to its paramayush (100/85/83/86), and every nakshatra to belong to
  exactly one group. Two deliberate differences from PyJHora:
  - After a pada's cycle the dasha continues with the *actual next pada*, so
    Mrigashira 4 is followed by Ardra 1. PyJHora uses a fixed group swap that is wrong for some stars.
  - Antardashas of the birth dasha run from that dasha's true start, before birth,
    exactly as in Vimshottari. They aren't compressed into the remaining balance.
  - Kalachakra antardasha schemes differ between authors. This engine uses the cycle
    restarted from the dasha sign, with years in proportion (P.V.R. Narasimha Rao's book).
    Gati names (Manduka, Markati, Simhavalokana) are not assigned; each dasha reports the sign jump from the previous one.

### Sthira, Shoola and Brahma: confidence and open points

- **Sthira** (from Brahma's sign, zodiacal, 7/8/9 years, 96 in all) and **Shoola** (from
  the stronger of lagna and 7th, zodiacal, 9 years each, 108 in all) are well agreed.
- **Brahma (the planet)** is worded differently across texts. The engine scores the lords of
  the 6th, 8th and 12th from the stronger of lagna/7th on three criteria: odd sign, houses 1–7
  from that sign, friendly-or-better dignity. Ties are broken by Jaimini planet strength.
  Rahu and Ketu are excluded. Every candidate and the deciding rule are in the output, so
  a reader can apply another school's rule.
- **Shoola antardashas:** authors start them from the dasha sign, from its lord, or from the
  stronger of the sign and its 7th. The engine uses the last, and the output says so. Even
  the PyJHora reference uses two different defaults in two places.
- **Brahma dasha years** (count to each sign's 6th lord, minus one, ±1 for an
  exalted/debilitated lord, 0 when the lord occupies the sign) often add up to far less
  than a human life. That total is **not** a lifespan, and the output carries an explicit caution.

## Not included, on purpose

Each of these has competing definitions or needs tables that couldn't be verified
here. Shipping a plausible-looking wrong number would be worse for a downstream
reader than leaving it out.
- The conditional nakshatra dashas (Shodasottari, Dwadasottari etc.)
- Bhava bala
- Deeptadi avasthas, Pranapada, Varnada lagna
- Kala, Mrityu, Ardhaprahara and Yamaghantaka
- The Tajika year lord, tri-rashi pati, Sahams and the Mudda/Patyayini dashas
- Longevity calculations (Pindayu/Amsayu): left out deliberately, since they invite death-timing claims

## Changes from the previous version (bugs fixed)

1. It silently used the Moshier ephemeris because no files were configured. Files are now bundled, and the fallback is an error.
2. KP used the Lahiri ayanamsa (5.8′ off), which is enough to move sub-lords. KP now runs on its own KP-ayanamsa chart.
3. Transits, ingresses and Sade Sati were hard-wired to IST, so they were wrong for any other timezone.
4. Only fixed UTC offsets were accepted, with no seconds. Now IANA zones (historical DST and war time), seconds, and gap/overlap detection.
5. Placidus crashed above about 66° latitude. It now falls back to Porphyry and says so.
6. Chara dasha stopped after one 12-sign cycle (age 69 for the example chart). It now has both cycles, the exaltation/debilitation adjustment, the proper stronger co-lord rule, and antardashas in the dasha sign's direction.
7. Arudha padas ignored Ketu and Rahu as co-lords of Scorpio and Aquarius.
8. Yogakaraka raja yoga was never detected.
9. Neecha bhanga missed several classical conditions and mislabelled the BPHS Moon rule.
10. KP significators ignored the nodes' agency.
11. Dignity had no friend/enemy layer.
12. The weekday did not exist; it now changes at sunrise.
13. The library read birth data at import, so one process could build only one chart. Now everything is pure functions of the birth input.

The old prediction experiments were removed in the cleanup. Their conclusion still
stands for anyone who uses this output to predict: a career-timing score built on
the old engine put the real chart only at about the 94th percentile of 200 random
charts (p ≈ 0.06, inflated by rule selection). Holding the chart fixed and toggling
which classical rules were used spread the "best month" over about 25 of 72 months.

## License note

The Swiss Ephemeris and pyswisseph are dual-licensed: AGPL, or a paid professional
license from Astrodienst. If you later run this as a closed-source backend service,
you need the professional license or must release your code under the AGPL.
