from engine import *
from datetime import datetime

c = natal()

print("="*66)
print(f"NATAL CHART — {c.local:%d %b %Y, %H:%M} (UTC+{c.tz:g}), {c.place.split(',')[0]} "
      f"({c.lat:.2f}N {c.lon:.2f}E)")
print(f"JD(UT) {c.jd:.6f}   Lahiri ayanamsa {dms(c.ayanamsa)}")
print("="*66)
print(f"Lagna  {SIGNS[c.lagna_idx]:12s} {dms(deg_in_sign(c.asc))}   MC {SIGNS[sign_of(c.mc)]} {dms(deg_in_sign(c.mc))}")
ni,nn,nl,pd = nakshatra(c.asc)
print(f"       Lagna nakshatra {nn} pada {pd} (lord {nl})")
print()
print(f"{'Planet':9s} {'Sign':11s} {'Deg':12s} {'H':>2s} {'Nakshatra':18s} {'Pd':>2s} {'Lord':8s} {'R':1s} Dignity")
print("-"*100)
for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
    lon = c.pos[p]; ni,nn,nl,pd = nakshatra(lon)
    print(f"{p:9s} {SIGNS[sign_of(lon)]:11s} {dms(deg_in_sign(lon)):12s} {c.house_of(lon):2d} "
          f"{nn:18s} {pd:2d} {nl:8s} {'R' if c.is_retro(p) else ' '} {dignity(p,lon)}")

print("\nHOUSE OCCUPANCY (whole sign)")
for h in range(1,13):
    si = (c.lagna_idx + h - 1) % 12
    occ = [p for p in c.pos if sign_of(c.pos[p]) == si]
    print(f"  H{h:2d} {SIGNS[si]:12s} lord {SIGN_LORDS[SIGNS[si]]:8s} : {', '.join(occ) if occ else '-'}")

print("\nKP CUSPS (Placidus, sidereal — no double ayanamsa subtraction)")
for h in range(1,13):
    cl = c.cusps[h-1]; st,sb,ss = kp_sub(cl)
    print(f"  C{h:2d} {SIGNS[sign_of(cl)]:11s} {dms(deg_in_sign(cl)):12s}  star {st:8s} sub {sb:8s} sub-sub {ss}")

print("\nKP PLANETARY SUB-LORDS")
for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
    st,sb,ss = kp_sub(c.pos[p])
    print(f"  {p:9s} star {st:8s} sub {sb:8s} sub-sub {ss}")

print("\nDIVISIONAL CHARTS")
for v in ['D3','D4','D7','D9','D10','D12']:
    d = divisional_chart(c, v)
    print(f"  {v}  lagna {SIGNS[d['_lagna']]}")
    line = "     " + "  ".join(f"{p[:2]}:{d[p]['sign'][:3]}({d[p]['house']})"
                               for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])
    print(line)

print("\nVEDIC GRAHA DRISHTI")
g = graha_drishti(c)
for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
    print(f"  {p:9s} -> {', '.join(g[p]['aspects_planets']) or '(no planets)'}")

v = vimshottari(c)
print(f"\nVIMSHOTTARI  birth nakshatra {v['nak']} pada {v['pada']}, lord {v['lord']}")
print(f"  Balance at birth: {v['balance']:.4f} years of {v['lord']}")
print("\n  MAHADASHA TIMELINE")
for n in v['tree'][:9]:
    print(f"    {n['lord']:8s} {n['start']:%Y-%m-%d} -> {n['end']:%Y-%m-%d}")

now = datetime(2026,9,9,12,0)
print(f"\n  RUNNING PERIOD on {now:%d %b %Y} (5 levels)")
for i,n in enumerate(dasha_at(c, now)):
    print(f"    L{i+1} {n['lord']:8s} {n['start']:%Y-%m-%d %H:%M} -> {n['end']:%Y-%m-%d %H:%M}")

print("\n  ANTARDASHAS OF CURRENT MAHADASHA")
md = dasha_at(c, now)[0]
for a in subdivide(md['lord'], md['start'], md['years']):
    print(f"    {md['lord']}-{a['lord']:8s} {a['start']:%Y-%m-%d} -> {a['end']:%Y-%m-%d}")

print("\nTRANSITS TODAY (sidereal, Sudarshan view)")
tp, ts = transit_positions(now)
for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
    s = sudarshan(tp[p], c)
    r = 'R' if (p in ('Rahu','Ketu') or ts[p] < 0) else ' '
    print(f"  {p:9s} {SIGNS[sign_of(tp[p])]:11s} {dms(deg_in_sign(tp[p])):12s} {r}  "
          f"H{s['from_lagna']:<2d} from Lagna | H{s['from_moon']:<2d} Moon | H{s['from_sun']:<2d} Sun")

print("\nTRANSIT-TO-NATAL CONJUNCTIONS (<=3 deg)")
hits = [(t,n,angular_distance(tp[t],c.pos[n])) for t in tp for n in c.pos
        if angular_distance(tp[t],c.pos[n]) <= 3]
for t,n,o in sorted(hits, key=lambda x:x[2]):
    print(f"  transit {t:9s} conj natal {n:9s} orb {o:.2f}")
if not hits: print("  none")
