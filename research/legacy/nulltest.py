"""
Null test: does this chart produce a MORE convincing convergence than
random charts? If fake birth data scores the same, the method has no
discriminating power and every peak is an artifact of the search.
"""
from engine import *
from interpret import *
from datetime import datetime, timedelta
import swisseph as swe, random, statistics
GR=['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']

def kp_house_of(lon,cusps):
    for h in range(12):
        a,b=cusps[h],cusps[(h+1)%12]
        if a<=b:
            if a<=lon<b: return h+1
        else:
            if lon>=a or lon<b: return h+1
    return 1

def build(ch):
    occ={p:kp_house_of(ch.pos[p],ch.cusps) for p in GR}
    owns={p:[] for p in GR}
    for h in range(1,13):
        owns[SIGN_LORDS[SIGNS[sign_of(ch.cusps[h-1])]]].append(h)
    star={p:kp_sub(ch.pos[p])[0] for p in GR}
    def sig(h):
        B=[p for p in GR if occ[p]==h]
        A=[p for p in GR if star[p] in B]
        D=[p for p in GR if h in owns[p]]
        C=[p for p in GR if star[p] in D]
        return A,B,C,D
    def sc(p,hs):
        s=0
        for h in hs:
            A,B,C,D=sig(h)
            if p in A: s+=4
            elif p in B: s+=3
            elif p in C: s+=2
            elif p in D: s+=1
        return s
    return sc

def peak_score(ch, y0=2026, y1=2032):
    sc=build(ch)
    bav=bhinnashtakavarga(ch); sav=sarvashtakavarga(bav)
    v=vimshottari(ch); LAG=ch.lagna_idx; MOONS=sign_of(ch.pos['Moon'])
    def chain(dt,n=3):
        out=[];lvl=v['tree']
        for _ in range(n):
            x=next((q for q in lvl if q['start']<=dt<q['end']),None)
            if not x: break
            out.append(x['lord']); lvl=subdivide(x['lord'],x['start'],x['years'])
        return out
    def starlord(l): return DASHA_ORDER[int(l//NAK_SPAN)%9]
    sigc={p for p in GR if sc(p,[6,10,11])>=5}
    best=-99; bestm=None
    d=datetime(y0,1,1)
    while d<datetime(y1,1,1):
        m=datetime(d.year,d.month,15)
        L=chain(m)
        if len(L)>=3:
            jd=swe.julday(m.year,m.month,15,6.5)
            pos={n:swe.calc_ut(jd,p,FLAGS)[0][0]%360 for n,p in PLANET_IDS.items()}
            s=0
            for lord,w in zip(L,[1.0,2.0,1.5]):
                s+=w*sc(lord,[6,10,11])*0.3 + w*sc(lord,[5,9,12])*0.2
            if starlord(pos['Jupiter']) in sigc: s+=3
            if starlord(pos['Saturn']) in sigc: s+=3
            hj=((sign_of(pos['Jupiter'])-MOONS)%12)+1
            if hj in (2,5,7,9,11): s+=2
            hs=((sign_of(pos['Saturn'])-LAG)%12)+1
            if hs in (10,11): s+=2.5
            s+=(sav[sign_of(pos['Jupiter'])]-28)*0.3
            if s>best: best=s; bestm=(m.year,m.month)
        d=(d.replace(day=28)+timedelta(days=8)).replace(day=1)
    return best,bestm

# FIX v3: driver guarded - stability.py imports build/GR and v2 silently
# re-ran the whole 200-chart test (and printed it) on import.
if __name__ == "__main__":
    random.seed(42)
    real=natal()
    r_peak,r_month=peak_score(real)
    print(f"REAL CHART   peak {r_peak:.1f} at {r_month[0]}-{r_month[1]:02d}\n")

    peaks=[];months={};failed=[]
    for i in range(200):
        y=random.randint(1985,2005); mo=random.randint(1,12); day=random.randint(1,28)
        hh=random.randint(0,23); mm=random.randint(0,59)
        lat=random.uniform(8,34); lon=random.uniform(68,88)
        try:
            ch=Chart(y,mo,day,hh,mm,5.5,lat,lon)
            p,mth=peak_score(ch)
            peaks.append(p); months[mth]=months.get(mth,0)+1
        except Exception as e:
            failed.append((y,mo,day,hh,mm,repr(e)))

    peaks.sort(); n=len(peaks)
    if failed: print(f"WARNING: {len(failed)} random charts raised and were excluded: {failed[:3]}")
    print(f"{n} RANDOM CHARTS, same pipeline:")
    print(f"  mean peak {statistics.mean(peaks):.1f}   sd {statistics.stdev(peaks):.1f}")
    print(f"  min {peaks[0]:.1f}   median {statistics.median(peaks):.1f}   max {peaks[-1]:.1f}")
    above=sum(1 for p in peaks if p>=r_peak)
    print(f"\n  random charts scoring >= the real chart: {above}/{n} = {100*above/n:.1f}%")
    print(f"  => real chart percentile: {100-100*above/n:.1f}  (one-sided p = {(above+1)/(n+1):.3f})")
    print("\n  Interpretation: if the real chart carried signal, its peak would sit")
    print("  far out in the tail. A percentile near 50 means the 'convergence' is")
    print("  what ANY chart produces when scored this way. Caveat: the rules were")
    print("  chosen while looking at the real chart, which inflates its score, so a")
    print("  high percentile here is NOT evidence of signal either.")
