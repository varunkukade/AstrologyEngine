"""
Decisive test: hold the chart FIXED, vary only the analyst's defensible
choices (weights on each rule, all within ranges any astrologer would accept).
If the chart determines the date, the predicted month should barely move.
"""
from engine import *
from interpret import *
from nulltest import build, GR
from datetime import datetime, timedelta
import swisseph as swe, random, collections
c=natal(); sc=build(c)
bav=bhinnashtakavarga(c); sav=sarvashtakavarga(bav)
v=vimshottari(c); LAG=c.lagna_idx; MOONS=sign_of(c.pos['Moon'])
def chain(dt,n=3):
    out=[];lvl=v['tree']
    for _ in range(n):
        x=next((q for q in lvl if q['start']<=dt<q['end']),None)
        if not x:break
        out.append(x['lord']);lvl=subdivide(x['lord'],x['start'],x['years'])
    return out
def starlord(l): return DASHA_ORDER[int(l//NAK_SPAN)%9]
sigc={p for p in GR if sc(p,[6,10,11])>=5}

months=[]
d=datetime(2026,1,1)
while d<datetime(2032,1,1):
    m=datetime(d.year,d.month,15); L=chain(m)
    jd=swe.julday(m.year,m.month,15,6.5)
    pos={n:swe.calc_ut(jd,p,FLAGS)[0][0]%360 for n,p in PLANET_IDS.items()}
    feats={
     'md':sc(L[0],[6,10,11]) if L else 0,
     'ad':sc(L[1],[6,10,11]) if len(L)>1 else 0,
     'pd':sc(L[2],[6,10,11]) if len(L)>2 else 0,
     'leave':sum(sc(l,[5,9,12]) for l in L),
     'jupstar':1 if starlord(pos['Jupiter']) in sigc else 0,
     'satstar':1 if starlord(pos['Saturn']) in sigc else 0,
     'jupgoch':1 if ((sign_of(pos['Jupiter'])-MOONS)%12)+1 in (2,5,7,9,11) else 0,
     'sat1011':1 if ((sign_of(pos['Saturn'])-LAG)%12)+1 in (10,11) else 0,
     'sav':(sav[sign_of(pos['Jupiter'])]-28)/10.0,
     'rahu':1 if ((sign_of(pos['Rahu'])-LAG)%12)+1 in (6,10,11) else 0,
    }
    months.append((m,feats))
    d=(d.replace(day=28)+timedelta(days=8)).replace(day=1)

def run(trials, toggle, rng):
    """toggle=False: rules fixed, weights vary (v2's test).
    toggle=True : each rule independently in or out (p=0.5, at least 2 kept),
                  weights vary - the test section 12.2 of the reference describes."""
    keys=list(months[0][1]); winners=collections.Counter()
    for _ in range(trials):
        w={k:rng.uniform(0.5,2.5) for k in keys}
        if toggle:
            on=[k for k in keys if rng.random()<0.5]
            while len(on)<2: on=rng.sample(keys,2)
            w={k:(w[k] if k in on else 0.0) for k in keys}
        best=max(months,key=lambda x:sum(w[k]*x[1][k] for k in keys))
        winners[(best[0].year,best[0].month)]+=1
    return winners

if __name__ == "__main__":
    # FIX v3: v2 shipped only the weights-only variant (2000 trials), which
    # gives one month ~99.7% of the time; the reference's headline result
    # (3,000 trials, rules toggled) came from code that was not shipped.
    for label,toggle,trials in (("RULES FIXED, weights vary",False,3000),
                                ("RULES TOGGLED in/out, weights vary",True,3000)):
        winners=run(trials,toggle,random.Random(7))
        print(f"{label}: {trials} trials, chart fixed")
        for (y,m),n in winners.most_common(10):
            print(f"   {y}-{m:02d}   {100*n/trials:5.1f}%   {'#'*int(50*n/trials)}")
        top=winners.most_common(1)[0]
        print(f"   distinct winning months: {len(winners)} of {len(months)}")
        print(f"   most frequent: {top[0][0]}-{top[0][1]:02d} at {100*top[1]/trials:.1f}%\n")
