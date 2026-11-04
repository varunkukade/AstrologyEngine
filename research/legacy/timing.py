from engine import *
from interpret import *
from kp import c, score, CHANGE, LEAVE, FOREIGN, GR, occ, owns, star_of, significators
from datetime import datetime, timedelta

# ---------- build every pratyantardasha (L3) from 2026 to 2032
v = vimshottari(c)
rows = []
for md in v['tree']:
    if md['end'] < datetime(2026,1,1) or md['start'] > datetime(2032,1,1): continue
    for ad in subdivide(md['lord'], md['start'], md['years']):
        if ad['end'] < datetime(2026,1,1) or ad['start'] > datetime(2032,1,1): continue
        for pd in subdivide(ad['lord'], ad['start'], ad['years']):
            if pd['end'] < datetime(2026,1,1) or pd['start'] > datetime(2032,1,1): continue
            rows.append((md['lord'], ad['lord'], pd['lord'], pd['start'], pd['end'], pd['years']))

def combo_score(md, ad, pd, houses):
    # weight: AD is the primary trigger in KP, PD fine-tunes, MD sets the field
    w = {'md':1.0, 'ad':2.0, 'pd':1.5}
    s = w['md']*score(md,houses)[0] + w['ad']*score(ad,houses)[0] + w['pd']*score(pd,houses)[0]
    return s

print("PRATYANTARDASHA WINDOWS 2026-2032, scored for JOB CHANGE (6,10,11)")
print(f"{'Period':26s} {'Start':11s} {'End':11s} {'Chg':>6s} {'Leave':>6s} {'Frgn':>6s} {'Days':>5s}")
scored = []
for md,ad,pd,s,e,y in rows:
    ch = combo_score(md,ad,pd,CHANGE)
    lv = combo_score(md,ad,pd,LEAVE)
    fr = combo_score(md,ad,pd,FOREIGN)
    scored.append((ch,lv,fr,md,ad,pd,s,e))
    print(f"{md+'-'+ad+'-'+pd:26s} {s:%Y-%m-%d} {e:%Y-%m-%d} {ch:6.1f} {lv:6.1f} {fr:6.1f} {(e-s).days:5d}")

print("\nTOP 8 BY JOB-CHANGE SCORE (combined chg+leave):")
for ch,lv,fr,md,ad,pd,s,e in sorted(scored, key=lambda x:-(x[0]+x[1]))[:8]:
    print(f"  {md}-{ad}-{pd:9s} {s:%Y-%m-%d} -> {e:%Y-%m-%d}  chg {ch:.1f} leave {lv:.1f} foreign {fr:.1f}")
