from engine import *
from interpret import *
from kp import c, score, CHANGE, LEAVE, FOREIGN, GR, significators, occ
from datetime import datetime, timedelta
import swisseph as swe
def star_lord_of(l): return DASHA_ORDER[int(l//NAK_SPAN)%9]
sig={p for p in GR if score(p,CHANGE)[0]>=5}
leave={p for p in GR if score(p,LEAVE)[0]>=4}
v=vimshottari(c)
def chain(dt,depth=5):
    out=[];lvl=v['tree']
    for _ in range(depth):
        n=next((x for x in lvl if x['start']<=dt<x['end']),None)
        if not n:break
        out.append(n['lord']);lvl=subdivide(n['lord'],n['start'],n['years'])
    return out

print("DAY SCAN 2027-05-01 to 2027-09-30 (peak convergence window)")
print("Criteria: sookshma+prana lords are change-significators, transit Moon")
print("in star of a significator, Sun in star of significator\n")
d=datetime(2027,5,1); best=[]
while d<datetime(2027,10,1):
    jd=swe.julday(d.year,d.month,d.day,6.5)
    mo=swe.calc_ut(jd,swe.MOON,FLAGS)[0][0]%360
    su=swe.calc_ut(jd,swe.SUN,FLAGS)[0][0]%360
    L=chain(d)
    if len(L)<5: d+=timedelta(days=1); continue
    sc=0
    if star_lord_of(mo) in sig: sc+=2
    if star_lord_of(su) in sig: sc+=2
    if L[3] in sig: sc+=2
    if L[4] in sig: sc+=2
    if L[3] in leave or L[4] in leave: sc+=1
    # Moon in 6th/10th/11th from lagna
    h=((sign_of(mo)-c.lagna_idx)%12)+1
    if h in (10,11,6): sc+=1
    if sc>=7: best.append((d.date(),sc,'-'.join(L[2:5]),star_lord_of(mo),star_lord_of(su),h))
    d+=timedelta(days=1)
for b in best: print(f"  {b[0]}  score {b[1]}  PD-SK-PR {b[2]:24s} Moon*{b[3]:8s} Sun*{b[4]:8s} MoonH{b[5]}")
if not best: print("  no day clears threshold 7")

print("\n\n--- CURRENCY / FOREIGN EMPLOYER ANALYSIS ---")
for h,label in [(7,'7th: contracts, dealings with others/partners'),
                (9,'9th: long distance, foreign connection, overseas'),
                (10,'10th: profession'),
                (12,'12th: foreign lands, residence abroad, outgoing')]:
    st,sb,ss=kp_sub(c.cusps[h-1])
    A,B,C,D=significators(h)
    print(f"\nCusp {h} ({label})")
    print(f"   star {st}, sub {sb}, sub-sub {ss}")
    print(f"   sublord {sb} signifies -> ", end='')
    hs=[]
    for hh in range(1,13):
        a,b_,cc,dd=significators(hh)
        if sb in a+b_+cc+dd: hs.append(hh)
    print(hs)

print("\nRahu (foreign karaka) placement:")
print(f"   sign {SIGNS[sign_of(c.pos['Rahu'])]}, whole-sign H{c.house_of(c.pos['Rahu'])}, "
      f"KP H{occ['Rahu']}, star lord {kp_sub(c.pos['Rahu'])[0]}")   # FIX v3: was a typed literal
print("D10 (career chart) positions:")
d10=divisional_chart(c,'D10')
for p in GR: print(f"   {p:8s} {d10[p]['sign']:12s} H{d10[p]['house']}")
print(f"   D10 lagna {SIGNS[d10['_lagna']]}")
print("\nD9, D12, D3 lagnas:", SIGNS[d9_sign(c.asc)], SIGNS[d12_sign(c.asc)], SIGNS[d3_sign(c.asc)])
