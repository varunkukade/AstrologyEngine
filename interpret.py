"""
Interpretation layer for the Vedic engine.

Contains:
  - Bhinnashtakavarga / Sarvashtakavarga (Parashari tables)
  - Yoga detection (Raja, Dhana, Panchamahapurusha, Neecha Bhanga,
    Vipreeta, Gaja Kesari, Kemadruma, Sunapha/Anapha/Durudhara, etc.)
  - Sade Sati / Dhaiya phase calculator with real ingress scanning
  - Transit strength scoring against SAV bindus

Everything here is rule-application over the chart object in engine.py.
Where classical sources disagree, the disagreement is reported rather than
silently resolved — see `notes` fields.
"""
from engine import (Chart, SIGNS, SIGN_LORDS, PLANET_IDS, DASHA_ORDER,
                    DASHA_YEARS, sign_of, deg_in_sign, dms, dignity, DIGNITY,
                    VEDIC_SPECIAL, transit_positions, nakshatra, sign_ingresses)
from datetime import datetime, timedelta
import swisseph as swe

GRAHAS = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']
NODES = ['Rahu','Ketu']
NATURAL_BENEFIC = ['Jupiter','Venus','Moon']      # Moon conditional
NATURAL_MALEFIC = ['Sun','Mars','Saturn','Rahu','Ketu']

# ==================================================================
# ASHTAKAVARGA — Parashari benefic-place tables
# Each entry: contributor -> houses (1-indexed from contributor's sign)
# that receive a bindu in that planet's Bhinnashtakavarga.
# ==================================================================
BAV_TABLES = {
 'Sun': {
   'Sun':[1,2,4,7,8,9,10,11], 'Moon':[3,6,10,11],
   'Mars':[1,2,4,7,8,9,10,11], 'Mercury':[3,5,6,9,10,11,12],
   'Jupiter':[5,6,9,11], 'Venus':[6,7,12],
   'Saturn':[1,2,4,7,8,9,10,11], 'Lagna':[3,4,6,10,11,12]},          # 48
 'Moon': {
   'Sun':[3,6,7,8,10,11], 'Moon':[1,3,6,7,10,11],
   'Mars':[2,3,5,6,9,10,11], 'Mercury':[1,3,4,5,7,8,10,11],
   'Jupiter':[1,4,7,8,10,11,12], 'Venus':[3,4,5,7,9,10,11],
   'Saturn':[3,5,6,11], 'Lagna':[3,6,10,11]},                        # 49
 'Mars': {
   'Sun':[3,5,6,10,11], 'Moon':[3,6,11],
   'Mars':[1,2,4,7,8,10,11], 'Mercury':[3,5,6,11],
   'Jupiter':[6,10,11,12], 'Venus':[6,8,11,12],
   'Saturn':[1,4,7,8,9,10,11], 'Lagna':[1,3,6,10,11]},               # 39
 'Mercury': {
   'Sun':[5,6,9,11,12], 'Moon':[2,4,6,8,10,11],
   'Mars':[1,2,4,7,8,9,10,11], 'Mercury':[1,3,5,6,9,10,11,12],
   'Jupiter':[6,8,11,12], 'Venus':[1,2,3,4,5,8,9,11],
   'Saturn':[1,2,4,7,8,9,10,11], 'Lagna':[1,2,4,6,8,10,11]},         # 54
 'Jupiter': {
   'Sun':[1,2,3,4,7,8,9,10,11], 'Moon':[2,5,7,9,11],
   'Mars':[1,2,4,7,8,10,11], 'Mercury':[1,2,4,5,6,9,10,11],
   'Jupiter':[1,2,3,4,7,8,10,11], 'Venus':[2,5,6,9,10,11],
   'Saturn':[3,5,6,12], 'Lagna':[1,2,4,5,6,7,9,10,11]},              # 56
 'Venus': {
   'Sun':[8,11,12], 'Moon':[1,2,3,4,5,8,9,11,12],
   'Mars':[3,5,6,9,11,12], 'Mercury':[3,5,6,9,11],
   'Jupiter':[5,8,9,10,11], 'Venus':[1,2,3,4,5,8,9,10,11],
   'Saturn':[3,4,5,8,9,10,11], 'Lagna':[1,2,3,4,5,8,9,11]},          # 52
 'Saturn': {
   'Sun':[1,2,4,7,8,10,11], 'Moon':[3,6,11],
   'Mars':[3,5,6,10,11,12], 'Mercury':[6,8,9,10,11,12],
   'Jupiter':[5,6,11,12], 'Venus':[6,11,12],
   'Saturn':[3,5,6,11], 'Lagna':[1,3,4,6,10,11]},                    # 39
}

def bhinnashtakavarga(chart):
    """Returns {planet: [bindus per sign index 0-11]}."""
    ref = {p: sign_of(chart.pos[p]) for p in GRAHAS}
    ref['Lagna'] = chart.lagna_idx
    out = {}
    for target, table in BAV_TABLES.items():
        bindus = [0]*12
        for contributor, houses in table.items():
            base = ref[contributor]
            for h in houses:
                bindus[(base + h - 1) % 12] += 1
        out[target] = bindus
    return out

def sarvashtakavarga(bav):
    sav = [0]*12
    for bindus in bav.values():
        for i in range(12):
            sav[i] += bindus[i]
    return sav

# ==================================================================
# HOUSE / LORD HELPERS
# ==================================================================
KENDRAS = [1,4,7,10]
TRIKONAS = [1,5,9]
DUSTHANAS = [6,8,12]
UPACHAYA = [3,6,10,11]

def house_lord(chart, house):
    return SIGN_LORDS[SIGNS[(chart.lagna_idx + house - 1) % 12]]

def lords_of(chart, planet):
    """Which houses does this planet rule for this lagna?"""
    return [h for h in range(1,13) if house_lord(chart, h) == planet]

def house_of_planet(chart, planet):
    return ((sign_of(chart.pos[planet]) - chart.lagna_idx) % 12) + 1

def aspects_sign(chart, planet, target_sign_idx):
    s = sign_of(chart.pos[planet])
    return any((s + h - 1) % 12 == target_sign_idx
               for h in VEDIC_SPECIAL.get(planet, [7]))

def mutual_aspect(chart, p1, p2):
    return (aspects_sign(chart, p1, sign_of(chart.pos[p2])) and
            aspects_sign(chart, p2, sign_of(chart.pos[p1])))

def conjunct(chart, p1, p2):
    return sign_of(chart.pos[p1]) == sign_of(chart.pos[p2])

def exchange(chart, p1, p2):
    """Parivartana — each sits in the other's owned sign."""
    s1, s2 = SIGNS[sign_of(chart.pos[p1])], SIGNS[sign_of(chart.pos[p2])]
    return SIGN_LORDS[s1] == p2 and SIGN_LORDS[s2] == p1

def relation(chart, p1, p2):
    if conjunct(chart, p1, p2):     return 'conjunction'
    if exchange(chart, p1, p2):     return 'exchange (parivartana)'
    if mutual_aspect(chart, p1, p2):return 'mutual aspect'
    return None

# ==================================================================
# YOGAS
# ==================================================================
def raja_yogas(chart):
    found = []
    for p1 in GRAHAS:
        for p2 in GRAHAS:
            if p1 >= p2: continue
            h1, h2 = lords_of(chart, p1), lords_of(chart, p2)
            kend = [h for h in h1 if h in KENDRAS]
            trik = [h for h in h2 if h in TRIKONAS]
            kend2 = [h for h in h2 if h in KENDRAS]
            trik1 = [h for h in h1 if h in TRIKONAS]
            pair = None
            if kend and trik:   pair = (p1, kend, p2, trik)
            elif kend2 and trik1: pair = (p2, kend2, p1, trik1)
            if not pair: continue
            rel = relation(chart, p1, p2)
            if rel:
                found.append({
                    'type':'Raja Yoga',
                    'detail':f"{pair[0]} (kendra lord of {pair[1]}) + "
                             f"{pair[2]} (trikona lord of {pair[3]}) by {rel}",
                    'planets':[p1,p2],
                    'house':house_of_planet(chart,p1)})
    return found

def dhana_yogas(chart):
    found = []
    wealth = [1,2,5,9,11]
    for p1 in GRAHAS:
        for p2 in GRAHAS:
            if p1 >= p2: continue
            h1 = [h for h in lords_of(chart,p1) if h in wealth]
            h2 = [h for h in lords_of(chart,p2) if h in wealth]
            if not (h1 and h2): continue
            if not ({2,11} & set(h1+h2)): continue   # need a 2nd or 11th lord
            rel = relation(chart, p1, p2)
            if rel:
                found.append({'type':'Dhana Yoga',
                    'detail':f"{p1} (lord of {h1}) + {p2} (lord of {h2}) by {rel}",
                    'planets':[p1,p2],'house':house_of_planet(chart,p1)})
    return found

PMP = {'Mars':'Ruchaka','Mercury':'Bhadra','Jupiter':'Hamsa',
       'Venus':'Malavya','Saturn':'Sasa'}

def panchamahapurusha(chart):
    found = []
    for p, name in PMP.items():
        h = house_of_planet(chart, p)
        if h not in KENDRAS: continue
        d = dignity(p, chart.pos[p])
        if 'Exalted' in d or 'Own Sign' in d or 'Moolatrikona' in d:
            found.append({'type':f'{name} Yoga (Panchamahapurusha)',
                'detail':f"{p} {d} in house {h} (kendra)",
                'planets':[p],'house':h})
    return found

def neecha_bhanga(chart):
    """Debilitation cancellation. Conditions vary by school — all are
    reported with which authority accepts them."""
    found = []
    for p in GRAHAS:
        d = dignity(p, chart.pos[p])
        if 'Debilitated' not in d: continue
        sign = SIGNS[sign_of(chart.pos[p])]
        debil_lord = SIGN_LORDS[sign]
        exalt_sign = DIGNITY[p]['exalt'][0]
        exalt_lord = SIGN_LORDS[exalt_sign]
        conds, notes = [], []
        for label, ruler in (('debilitation-sign lord', debil_lord),
                             ('exaltation-sign lord', exalt_lord)):
            h = house_of_planet(chart, ruler)
            if h in KENDRAS:
                conds.append(f"{label} {ruler} in kendra (house {h}) — accepted by all schools")
            elif h in TRIKONAS:
                conds.append(f"{label} {ruler} in trikona (house {h}) — accepted by some")
            else:
                notes.append(f"{label} {ruler} in house {h} — no cancellation from this rule")
        # Moon-kendra variant
        moon_sign = sign_of(chart.pos['Moon'])
        for label, ruler in (('debilitation lord', debil_lord),
                             ('exaltation lord', exalt_lord)):
            hm = ((sign_of(chart.pos[ruler]) - moon_sign) % 12) + 1
            if hm in KENDRAS:
                conds.append(f"{label} {ruler} in kendra from Moon (house {hm}) — Phaladeepika variant")
        found.append({'type':'Neecha Bhanga check','planet':p,'sign':sign,
                      'satisfied':conds,'failed':notes,
                      'verdict':'cancelled' if conds else 'NOT cancelled'})
    return found

def vipreeta_raja(chart):
    found = []
    for p in GRAHAS:
        owned = [h for h in lords_of(chart,p) if h in DUSTHANAS]
        if not owned: continue
        h = house_of_planet(chart, p)
        if h in DUSTHANAS:
            name = {6:'Harsha',8:'Sarala',12:'Vimala'}[owned[0]]
            found.append({'type':f'Vipreeta Raja Yoga ({name})',
                'detail':f"{p}, lord of {owned}, placed in dusthana house {h}",
                'planets':[p],'house':h})
    return found

def lunar_yogas(chart):
    found = []
    moon_sign = sign_of(chart.pos['Moon'])
    def rel_house(p):
        return ((sign_of(chart.pos[p]) - moon_sign) % 12) + 1

    # Gaja Kesari
    jh = rel_house('Jupiter')
    if jh in KENDRAS:
        found.append({'type':'Gaja Kesari Yoga',
            'detail':f"Jupiter in house {jh} from Moon (kendra)",
            'planets':['Moon','Jupiter'],'house':house_of_planet(chart,'Jupiter')})

    # Chandra-Mangala
    if conjunct(chart,'Moon','Mars') or mutual_aspect(chart,'Moon','Mars'):
        found.append({'type':'Chandra-Mangala Yoga',
            'detail':'Moon and Mars in ' + (relation(chart,'Moon','Mars') or ''),
            'planets':['Moon','Mars'],'house':house_of_planet(chart,'Moon')})

    # Sunapha / Anapha / Durudhara / Kemadruma (exclude Sun and nodes)
    others = [p for p in GRAHAS if p not in ('Sun','Moon')]
    second = [p for p in others if rel_house(p) == 2]
    twelfth = [p for p in others if rel_house(p) == 12]
    if second and twelfth:
        found.append({'type':'Durudhara Yoga',
            'detail':f"planets in both 2nd ({', '.join(second)}) and 12th "
                     f"({', '.join(twelfth)}) from Moon",
            'planets':second+twelfth,'house':None})
    elif second:
        found.append({'type':'Sunapha Yoga',
            'detail':f"{', '.join(second)} in 2nd from Moon",'planets':second,'house':None})
    elif twelfth:
        found.append({'type':'Anapha Yoga',
            'detail':f"{', '.join(twelfth)} in 12th from Moon",'planets':twelfth,'house':None})
    else:
        found.append({'type':'Kemadruma Yoga',
            'detail':'no planets (excluding Sun/nodes) in 2nd or 12th from Moon',
            'planets':[],'house':None})
    return found

def misc_yogas(chart):
    found = []
    if conjunct(chart,'Sun','Mercury'):
        sep = abs(chart.pos['Sun'] - chart.pos['Mercury'])
        found.append({'type':'Budhaditya Yoga',
            'detail':f"Sun and Mercury in {SIGNS[sign_of(chart.pos['Sun'])]}, "
                     f"separation {sep:.2f}°",
            'planets':['Sun','Mercury'],'house':house_of_planet(chart,'Sun')})
    # Combustion
    for p in ['Moon','Mars','Mercury','Jupiter','Venus','Saturn']:
        orb = {'Moon':12,'Mars':17,'Mercury':14,'Jupiter':11,'Venus':10,'Saturn':15}[p]
        # FIX v3: classical reduced orbs when retrograde (Mercury 12, Venus 8)
        if chart.speed[p] < 0 and p in ('Mercury','Venus'):
            orb = {'Mercury':12,'Venus':8}[p]
        sep = abs(chart.pos['Sun'] - chart.pos[p]) % 360
        sep = min(sep, 360-sep)
        if sep <= orb:
            found.append({'type':'Combustion (Astangata)',
                'detail':f"{p} within {sep:.2f}° of Sun (limit {orb}°) — "
                         f"classical strength reduction",
                'planets':[p],'house':house_of_planet(chart,p)})
    # Kala Sarpa
    node_lon = chart.pos['Rahu']
    spans = []
    for p in GRAHAS:
        d = (chart.pos[p] - node_lon) % 360
        spans.append(d)
    if all(s < 180 for s in spans) or all(s > 180 for s in spans):
        found.append({'type':'Kala Sarpa Yoga',
            'detail':'all seven grahas fall on one side of the Rahu-Ketu axis',
            'planets':GRAHAS,'house':None})
    return found

def all_yogas(chart):
    return (panchamahapurusha(chart) + raja_yogas(chart) + dhana_yogas(chart) +
            vipreeta_raja(chart) + lunar_yogas(chart) + misc_yogas(chart))

# ==================================================================
# SADE SATI / DHAIYA — real ingress scanning, not sign arithmetic
# ==================================================================
def saturn_sign_ingresses(start_year, end_year, tz=5.5):
    """Saturn sidereal sign changes, retrograde re-entries included.
    FIX v3: crossings are bisected to the actual moment and reported as the
    LOCAL date. v2 sampled once a day at local noon and stamped the event on
    the first noon it was noticed, so any crossing after noon came out a day
    late. The scan also no longer runs past 31 Dec of end_year."""
    _, ev = sign_ingresses(swe.SATURN, datetime(start_year,1,1),
                           datetime(end_year,12,31,23,59), tz)
    return [(t.date(), frm, to) for t, frm, to in ev]

def saturn_intervals(start_year, end_year, tz=5.5):
    """Build contiguous (start, end, sign) intervals from the ingress list.
    Doing it as intervals rather than open/close state avoids losing a phase
    when Saturn retrogrades straight from one target sign into another.
    FIX v3: a range with no ingress now returns one interval instead of [],
    which silently reported 'no Saturn phase' for short ranges."""
    first, ev = sign_ingresses(swe.SATURN, datetime(start_year,1,1),
                               datetime(end_year,12,31,23,59), tz)
    out = []
    cur_sign = first
    cur_start = datetime(start_year,1,1).date()
    for t, frm, to in ev:
        out.append((cur_start, t.date(), cur_sign))
        cur_start, cur_sign = t.date(), to
    out.append((cur_start, datetime(end_year,12,31).date(), cur_sign))
    return out

def sade_sati_phases(chart, start_year=1995, end_year=2060, min_days=1):
    """Saturn through 12th, 1st, 2nd from natal Moon sign = Sade Sati.
    Saturn through 4th or 8th from Moon = Dhaiya (Kantaka / Ashtama).
    Retrograde re-entries are preserved as separate segments; adjacent
    segments with the same label are merged."""
    moon_sign = sign_of(chart.pos['Moon'])
    targets = {(moon_sign+11)%12:'Sade Sati phase 1 (12th from Moon, rising)',
               moon_sign:'Sade Sati phase 2 (over natal Moon, PEAK)',
               (moon_sign+1)%12:'Sade Sati phase 3 (2nd from Moon, setting)',
               (moon_sign+3)%12:'Kantaka Shani / Dhaiya (4th from Moon)',
               (moon_sign+7)%12:'Ashtama Shani / Dhaiya (8th from Moon)'}
    segs = []
    for start, end, sign in saturn_intervals(start_year, end_year):
        si = SIGNS.index(sign)
        if si not in targets: continue
        if (end - start).days < min_days: continue
        segs.append({'start':start,'end':end,'sign':sign,'label':targets[si]})
    merged = []
    for s in segs:
        if merged and merged[-1]['label'] == s['label'] and \
           (s['start'] - merged[-1]['end']).days <= 1:
            merged[-1]['end'] = s['end']
        else:
            merged.append(dict(s))
    return merged

def sade_sati_summary(chart, when=None):
    """Which Saturn phase, if any, is running on a given date."""
    when = when or datetime.now()
    if isinstance(when, datetime): when = when.date()
    for p in sade_sati_phases(chart, when.year-10, when.year+10):
        if p['start'] <= when < p['end']:
            total = (p['end'] - p['start']).days
            done = (when - p['start']).days
            return {**p, 'pct_elapsed': 100.0*done/total,
                    'days_remaining': (p['end'] - when).days}
    return None

# ==================================================================
# TRANSIT STRENGTH SCORING vs SAV
# ==================================================================
def transit_strength(chart, when):
    """Score each transiting graha by the SAV bindus of the sign it occupies
    and its own BAV bindus there. Classical rule of thumb: >30 SAV in a sign
    is supportive, <25 is weak."""
    bav = bhinnashtakavarga(chart)
    sav = sarvashtakavarga(bav)
    tp, ts = transit_positions(when)
    rows = []
    for p in GRAHAS + NODES:
        si = sign_of(tp[p])
        own = bav[p][si] if p in bav else None
        rows.append({'planet':p,'sign':SIGNS[si],
                     'deg':deg_in_sign(tp[p]),
                     'house_from_lagna':((si - chart.lagna_idx)%12)+1,
                     'house_from_moon':((si - sign_of(chart.pos['Moon']))%12)+1,
                     'sav':sav[si],'bav':own,
                     'retro': p in NODES or ts[p] < 0})
    return rows, sav, bav
