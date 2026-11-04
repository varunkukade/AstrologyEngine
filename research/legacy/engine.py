"""
Vedic Astrology Calculation Engine — corrected build.
All bugs listed in FIXES.md are addressed here.
"""
import swisseph as swe
from datetime import datetime, timedelta

# ---------------------------------------------------------------- SETUP
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

# FIX #1: FLG_SIDEREAL is present, so calc_ut ALREADY returns sidereal
# longitudes. Never subtract ayanamsa again.
FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

SIGN_LORDS = {"Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
              "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
              "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn",
              "Pisces":"Jupiter"}

PLANET_IDS = {'Sun':swe.SUN,'Moon':swe.MOON,'Mars':swe.MARS,'Mercury':swe.MERCURY,
              'Jupiter':swe.JUPITER,'Venus':swe.VENUS,'Saturn':swe.SATURN,
              'Rahu':swe.MEAN_NODE}

NAK_SPAN = 360.0 / 27.0
NAK_NAMES = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
"Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
"Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula",
"Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
"Purva Bhadrapada","Uttara Bhadrapada","Revati"]

# Birth data of record lives in birth.json (git-ignored, never committed).
# Copy birth.example.json to birth.json and fill in real values.
import json as _json, os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_BIRTH_FILE = next((p for p in (_os.path.join(_HERE, 'birth.json'),
                                _os.path.join(_HERE, 'birth.example.json'))
                    if _os.path.exists(p)), None)
if _BIRTH_FILE is None:
    raise FileNotFoundError("birth.json not found - copy birth.example.json to birth.json")
with open(_BIRTH_FILE) as _f:
    BIRTH = _json.load(_f)
USING_EXAMPLE_BIRTH = _BIRTH_FILE.endswith('birth.example.json')

DASHA_ORDER = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']
DASHA_YEARS = {'Ketu':7,'Venus':20,'Sun':6,'Moon':10,'Mars':7,
               'Rahu':18,'Jupiter':16,'Saturn':19,'Mercury':17}
YEAR_DAYS = 365.2425

def dms(deg):
    total = round(deg * 3600, 1)
    d = int(total // 3600); rem = total - d*3600
    m = int(rem // 60); s = rem - m*60
    if round(s,1) >= 60: s -= 60; m += 1
    if m >= 60: m -= 60; d += 1
    return f"{d}°{m:02d}'{s:04.1f}\""

def sign_of(lon):   return int(lon // 30) % 12
def deg_in_sign(lon): return lon % 30

# ---------------------------------------------------------------- CHART
class Chart:
    def __init__(self, y, mo, d, hh, mm, tz_offset, lat, lon, place=""):
        self.local = datetime(y, mo, d, hh, mm)
        self.tz = tz_offset
        self.lat, self.lon, self.place = lat, lon, place
        ut = hh + mm/60.0 - tz_offset
        self.jd = swe.julday(y, mo, d, ut)
        self.ayanamsa = swe.get_ayanamsa_ut(self.jd)

        # planets
        self.pos, self.speed = {}, {}
        for name, pid in PLANET_IDS.items():
            xx, _ = swe.calc_ut(self.jd, pid, FLAGS)
            self.pos[name] = xx[0] % 360        # already sidereal
            self.speed[name] = xx[3]
        # FIX #4: Ketu computed explicitly, not from a leaked loop variable
        self.pos['Ketu'] = (self.pos['Rahu'] + 180) % 360
        self.speed['Ketu'] = self.speed['Rahu']

        # houses — FIX #2: with FLG_SIDEREAL these are already sidereal
        cusps, ascmc = swe.houses_ex(self.jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        self.cusps = [c % 360 for c in cusps]
        self.asc = ascmc[0] % 360
        self.mc = ascmc[1] % 360
        self.lagna_idx = sign_of(self.asc)

    def house_of(self, lon):
        """Whole-sign house."""
        return ((sign_of(lon) - self.lagna_idx) % 12) + 1

    def is_retro(self, name):
        if name in ('Rahu','Ketu'):
            return True          # nodes are always retrograde
        return self.speed[name] < 0

def nakshatra(lon):
    idx = int(lon // NAK_SPAN) % 27
    pada = int((lon % NAK_SPAN) // (NAK_SPAN/4)) + 1
    return idx, NAK_NAMES[idx], DASHA_ORDER[idx % 9], pada

# ---------------------------------------------------------------- VARGAS
def d9_sign(lon):
    s = sign_of(lon); part = int((lon % 30) // (30/9))
    start = [s, (s+8) % 12, (s+4) % 12][s % 3]
    return (start + part) % 12

def d10_sign(lon):
    s = sign_of(lon); part = int((lon % 30) // 3)
    start = s if s % 2 == 0 else (s+8) % 12   # odd signs from same, even from 9th
    return (start + part) % 12

def d4_sign(lon):
    s = sign_of(lon); part = int((lon % 30) // 7.5)
    return (s + part*3) % 12

def d3_sign(lon):
    s = sign_of(lon); part = int((lon % 30) // 10)
    return (s + part*4) % 12

def d7_sign(lon):
    s = sign_of(lon); part = int((lon % 30) // (30/7))
    start = s if s % 2 == 0 else (s+6) % 12
    return (start + part) % 12

def d12_sign(lon):
    s = sign_of(lon); part = int((lon % 30) // 2.5)
    return (s + part) % 12

VARGAS = {'D3':d3_sign,'D4':d4_sign,'D7':d7_sign,'D9':d9_sign,
          'D10':d10_sign,'D12':d12_sign}

def divisional_chart(chart, vtype):
    """FIX #4: iterates over stored longitudes; Ketu handled like any other body."""
    conv = VARGAS[vtype]
    lagna = conv(chart.asc)
    out = {'_lagna': lagna}
    for name, lon in chart.pos.items():
        s = conv(lon)
        out[name] = {'sign_idx': s, 'sign': SIGNS[s],
                     'house': ((s - lagna) % 12) + 1}
    return out

# ---------------------------------------------------------------- DIGNITY
DIGNITY = {
 'Sun':{'own':['Leo'],'exalt':('Aries',10),'debil':('Libra',10),'mt':('Leo',(0,20))},
 'Moon':{'own':['Cancer'],'exalt':('Taurus',3),'debil':('Scorpio',3),'mt':('Taurus',(3,30)),
         'exalt_range':(0,3)},
 'Mars':{'own':['Aries','Scorpio'],'exalt':('Capricorn',28),'debil':('Cancer',28),'mt':('Aries',(0,12))},
 'Mercury':{'own':['Gemini','Virgo'],'exalt':('Virgo',15),'debil':('Pisces',15),'mt':('Virgo',(15,20)),
            'exalt_range':(0,15)},
 'Jupiter':{'own':['Sagittarius','Pisces'],'exalt':('Cancer',5),'debil':('Capricorn',5),'mt':('Sagittarius',(0,10))},
 'Venus':{'own':['Taurus','Libra'],'exalt':('Pisces',27),'debil':('Virgo',27),'mt':('Libra',(0,15))},
 'Saturn':{'own':['Capricorn','Aquarius'],'exalt':('Libra',20),'debil':('Aries',20),'mt':('Aquarius',(0,20))},
 'Rahu':{'own':[],'exalt':('Taurus',20),'debil':('Scorpio',20),'mt':None},
 'Ketu':{'own':[],'exalt':('Scorpio',20),'debil':('Taurus',20),'mt':None},
}

def dignity(planet, lon):
    """FIX #6: exaltation is tested BEFORE own-sign, so Mercury in Virgo
    no longer reports merely 'Own Sign'. Moolatrikona added."""
    d = DIGNITY[planet]; s = SIGNS[sign_of(lon)]; deg = deg_in_sign(lon)
    tags = []
    # FIX v3: for Moon (Taurus) and Mercury (Virgo) the sign is partitioned
    # (BPHS): exaltation only inside 'exalt_range', MT/own after it. Previously
    # Mercury at 25 Virgo read "Exalted + Own Sign" and 15-16 Virgo fell in a gap.
    er = d.get('exalt_range')
    if d['exalt'] and s == d['exalt'][0] and (er is None or er[0] <= deg < er[1]):
        tags.append('Exalted (deep %s)' % dms(d['exalt'][1]) if abs(deg-d['exalt'][1])<1 else 'Exalted')
    if d['debil'] and s == d['debil'][0]:
        tags.append('Debilitated')
    if d['mt'] and s == d['mt'][0] and d['mt'][1][0] <= deg < d['mt'][1][1]:
        tags.append('Moolatrikona')
    if s in d['own'] and 'Moolatrikona' not in tags and not any(t.startswith('Exalted') for t in tags):
        tags.append('Own Sign')
    return ' + '.join(tags) if tags else 'Neutral'

# ---------------------------------------------------------------- VIMSHOTTARI
def vimshottari(chart):
    moon = chart.pos['Moon']
    nak_idx, nak_name, lord, pada = nakshatra(moon)
    frac_elapsed = (moon % NAK_SPAN) / NAK_SPAN
    balance_years = DASHA_YEARS[lord] * (1 - frac_elapsed)

    # FIX: MD true start is BEFORE birth; anchor there so all sub-periods align.
    md_start = chart.local - timedelta(days=DASHA_YEARS[lord]*frac_elapsed*YEAR_DAYS)

    tree, cur, idx = [], md_start, DASHA_ORDER.index(lord)
    for i in range(12):
        l = DASHA_ORDER[(idx+i) % 9]
        end = cur + timedelta(days=DASHA_YEARS[l]*YEAR_DAYS)
        tree.append({'lord':l,'start':cur,'end':end,'years':DASHA_YEARS[l]})
        cur = end
    return {'nak':nak_name,'nak_idx':nak_idx,'pada':pada,'lord':lord,
            'balance':balance_years,'tree':tree}

def subdivide(lord, start, span_years):
    """One generic level. FIX: parent span is passed in years, never re-derived
    from the lord's base years — that was what drifted the deeper levels."""
    out, cur, idx = [], start, DASHA_ORDER.index(lord)
    for i in range(9):
        l = DASHA_ORDER[(idx+i) % 9]
        yrs = DASHA_YEARS[l] * span_years / 120.0
        end = cur + timedelta(days=yrs*YEAR_DAYS)
        out.append({'lord':l,'start':cur,'end':end,'years':yrs})
        cur = end
    return out

def dasha_at(chart, when, depth=5):
    v = vimshottari(chart)
    path, level = [], v['tree']
    span = None
    for _ in range(depth):
        node = next((n for n in level if n['start'] <= when < n['end']), None)
        if node is None: break
        path.append(node)
        span = node['years']
        level = subdivide(node['lord'], node['start'], span)
    return path

# ---------------------------------------------------------------- KP
def kp_sub(lon):
    nak_idx = int(lon // NAK_SPAN) % 27
    star = DASHA_ORDER[nak_idx % 9]
    frac = (lon % NAK_SPAN) / NAK_SPAN
    target = frac * 120.0
    cum = 0.0; si = DASHA_ORDER.index(star)
    for i in range(9):
        l = DASHA_ORDER[(si+i) % 9]
        if cum <= target < cum + DASHA_YEARS[l]:
            # sub-sub
            inner_frac = (target - cum) / DASHA_YEARS[l]
            t2 = inner_frac * 120.0; c2 = 0.0; si2 = DASHA_ORDER.index(l)
            subsub = DASHA_ORDER[(si2+8) % 9]
            for j in range(9):
                l2 = DASHA_ORDER[(si2+j) % 9]
                if c2 <= t2 < c2 + DASHA_YEARS[l2]:
                    subsub = l2; break
                c2 += DASHA_YEARS[l2]
            return star, l, subsub
        cum += DASHA_YEARS[l]
    return star, DASHA_ORDER[(si+8) % 9], DASHA_ORDER[(si+8) % 9]

# ---------------------------------------------------------------- ASPECTS
def angular_distance(a, b):
    d = abs(a-b) % 360
    return min(d, 360-d)

VEDIC_SPECIAL = {'Mars':[4,7,8],'Jupiter':[5,7,9],'Saturn':[3,7,10],
                 'Rahu':[5,7,9],'Ketu':[5,7,9]}

def graha_drishti(chart):
    """Vedic sign-based aspects — absent from the original reference entirely."""
    out = {}
    for p, lon in chart.pos.items():
        s = sign_of(lon)
        houses = VEDIC_SPECIAL.get(p, [7])
        aspected = [(h, SIGNS[(s+h-1) % 12]) for h in houses]
        targets = [q for q, ql in chart.pos.items()
                   if q != p and sign_of(ql) in [(s+h-1) % 12 for h in houses]]
        out[p] = {'aspects_signs': aspected, 'aspects_planets': targets}
    return out

def western_aspects(a, b, orb=3.0):
    """FIX #7: original only tested one direction, silently missing half of
    every non-symmetric aspect."""
    res = []
    for name, ang in {'conjunction':0,'semi-sextile':30,'sextile':60,
                      'square':90,'trine':120,'opposition':180}.items():
        sep = angular_distance(a, b)
        if abs(sep - ang) <= orb:
            res.append((name, abs(sep-ang)))
    return res

# ---------------------------------------------------------------- TRANSITS
def transit_positions(dt, tz=5.5):
    """FIX #3: transits now sidereal, matching the natal frame.
    The original returned tropical longitudes here and compared them to
    sidereal natal points — a permanent ~24° error."""
    jd = swe.julday(dt.year, dt.month, dt.day,
                    dt.hour + dt.minute/60.0 - tz)
    pos, spd = {}, {}
    for name, pid in PLANET_IDS.items():
        xx, _ = swe.calc_ut(jd, pid, FLAGS)
        pos[name] = xx[0] % 360; spd[name] = xx[3]
    pos['Ketu'] = (pos['Rahu'] + 180) % 360; spd['Ketu'] = spd['Rahu']
    return pos, spd

def sudarshan(lon, chart):
    s = sign_of(lon)
    return {'from_lagna': ((s - chart.lagna_idx) % 12) + 1,
            'from_moon': ((s - sign_of(chart.pos['Moon'])) % 12) + 1,
            'from_sun': ((s - sign_of(chart.pos['Sun'])) % 12) + 1}


# ---------------------------------------------------------------- INGRESSES
def _lon(jd, pid):
    return swe.calc_ut(jd, pid, FLAGS)[0][0] % 360

def _jd_to_local(jd, tz):
    y, mo, d, h = swe.revjul(jd)
    return datetime(y, mo, d) + timedelta(hours=h + tz)

def sign_ingresses(pid, start, end, tz=5.5):
    """Every sidereal sign change of body `pid` between local datetimes
    start and end, retrograde re-entries included. Sampled daily, then each
    crossing is bisected to well under a second, and returned in LOCAL time.
    Returns (sign_at_start, [(local_datetime, from_sign, to_sign), ...]).
    Daily sampling is safe for every body here: none crosses two signs in a day."""
    jd0 = swe.julday(start.year, start.month, start.day,
                     start.hour + start.minute/60.0 - tz)
    jd_end = swe.julday(end.year, end.month, end.day,
                        end.hour + end.minute/60.0 - tz)
    first = prev = sign_of(_lon(jd0, pid))
    events, lo = [], jd0
    while lo < jd_end:
        hi = min(lo + 1.0, jd_end)
        s = sign_of(_lon(hi, pid))
        if s != prev:
            a, b = lo, hi
            for _ in range(40):
                mid = (a + b) / 2.0
                if sign_of(_lon(mid, pid)) == prev: a = mid
                else: b = mid
            events.append((_jd_to_local(b, tz), SIGNS[prev], SIGNS[s]))
            prev = s
        lo = hi
    return SIGNS[first], events

def natal():
    """The chart of record. Use this everywhere instead of re-entering data."""
    return Chart(**BIRTH)
