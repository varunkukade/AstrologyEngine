from engine import *
from interpret import *
from datetime import datetime

c = natal()
NOW = datetime(2026,9,10,12,0)

print("="*70)
# FIX v3: header computed from the chart. v2 hardcoded "Lagna Cancer 14°31'",
# which is wrong (14°30'21") and would not follow any change to BIRTH.
_ni,_nn,_nl,_pd = nakshatra(c.pos['Moon'])
print(f"INTERPRETATION REPORT — {c.local:%d %b %Y, %H:%M} (UTC+{c.tz:g}), {c.place.split(',')[0]}")
print(f"Lagna {SIGNS[c.lagna_idx]} {dms(deg_in_sign(c.asc))} | "
      f"Moon {SIGNS[sign_of(c.pos['Moon'])]} {dms(deg_in_sign(c.pos['Moon']))} ({_nn} {_pd})")
print("="*70)

# ---- Ashtakavarga
bav = bhinnashtakavarga(c)
sav = sarvashtakavarga(bav)
print("\n--- ASHTAKAVARGA ---")
print(f"{'Sign':12s} {'H':>2s} " + " ".join(f"{p[:2]:>3s}" for p in GRAHAS) + f" {'SAV':>4s}")
print("-"*56)
for h in range(1,13):
    si = (c.lagna_idx + h - 1) % 12
    row = " ".join(f"{bav[p][si]:3d}" for p in GRAHAS)
    flag = "  <<" if sav[si] >= 30 else ("  ..low" if sav[si] < 25 else "")
    print(f"{SIGNS[si]:12s} {h:2d} {row} {sav[si]:4d}{flag}")
print(f"{'TOTAL':12s}    " + " ".join(f"{sum(bav[p]):3d}" for p in GRAHAS) + f" {sum(sav):4d}")
print("(no trikona/ekadhipatya sodhana applied — raw bindus)")

# ---- Yogas
print("\n--- YOGAS ---")
ys = all_yogas(c)
seen = set()
for y in ys:
    key = (y['type'], y['detail'])
    if key in seen: continue
    seen.add(key)
    print(f"  [{y['type']}]")
    print(f"      {y['detail']}")

print("\n--- NEECHA BHANGA ---")
for n in neecha_bhanga(c):
    print(f"  {n['planet']} debilitated in {n['sign']} -> {n['verdict'].upper()}")
    for s in n['satisfied']: print(f"      YES  {s}")
    for f in n['failed']:    print(f"      no   {f}")
if not neecha_bhanga(c): print("  no debilitated grahas")

# ---- Sade Sati
print(f"\n--- SATURN PHASES RELATIVE TO NATAL MOON ({SIGNS[sign_of(c.pos['Moon'])]}) ---")
for p in sade_sati_phases(c, 1998, 2050):
    print(f"  {str(p['start']):12s} -> {str(p['end']):12s}  {p['sign']:12s} {p['label']}")

# ---- Transit strength
print(f"\n--- TRANSIT STRENGTH ON {NOW:%d %b %Y} (SAV-scored) ---")
rows, sav, bav = transit_strength(c, NOW)
print(f"{'Planet':9s} {'Sign':12s} {'Deg':12s} {'HL':>3s} {'HM':>3s} {'SAV':>4s} {'BAV':>4s}  R")
for r in rows:
    print(f"{r['planet']:9s} {r['sign']:12s} {dms(r['deg']):12s} "
          f"{r['house_from_lagna']:3d} {r['house_from_moon']:3d} "
          f"{r['sav']:4d} {str(r['bav'] if r['bav'] is not None else '-'):>4s}  "
          f"{'R' if r['retro'] else ''}")

# ---- Dasha context
print("\n--- DASHA CONTEXT ---")
for i, n in enumerate(dasha_at(c, NOW)):
    lord_house = house_of_planet(c, n['lord']) if n['lord'] in c.pos else '-'
    lord_rules = lords_of(c, n['lord'])
    dg = dignity(n['lord'], c.pos[n['lord']])
    print(f"  L{i+1} {n['lord']:8s} {n['start']:%Y-%m-%d} -> {n['end']:%Y-%m-%d}"
          f"   [natal: H{lord_house}, rules {lord_rules}, {dg}]")
