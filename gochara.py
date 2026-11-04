from engine import *
from interpret import *
from kp import c, score, CHANGE, LEAVE, FOREIGN, GR
from datetime import datetime, timedelta
import swisseph as swe

LAG = c.lagna_idx; MOON = sign_of(c.pos['Moon'])
def house_from_lagna(si): return ((si-LAG)%12)+1
def house_from_moon(si): return ((si-MOON)%12)+1

# ---- Jupiter & Saturn sign transits 2026-2032
def ingresses(pid, y0, y1):
    """FIX v3: first row is the sign occupied on 1 Jan y0 (v2 dropped it, so a
    planet that stayed put all of 2026 vanished from the table); crossings are
    bisected to the true local date instead of the first noon noticed."""
    first, ev = sign_ingresses(pid, datetime(y0,1,1), datetime(y1,12,31,23,59))
    return [(datetime(y0,1,1).date(), first)] + [(t.date(), to) for t,frm,to in ev]

print("JUPITER TRANSITS (sidereal) 2026-2032")
for d,s in ingresses(swe.JUPITER,2026,2032):
    si=SIGNS.index(s)
    print(f"  {d}  -> {s:12s}  H{house_from_lagna(si):<2d} from Lagna | H{house_from_moon(si):<2d} from Moon")
print("\nSATURN TRANSITS 2026-2032")
for d,s in ingresses(swe.SATURN,2026,2032):
    si=SIGNS.index(s)
    print(f"  {d}  -> {s:12s}  H{house_from_lagna(si):<2d} from Lagna | H{house_from_moon(si):<2d} from Moon")

# ---- classical gochara: Jupiter good in 2,5,7,9,11 from Moon; Saturn in 3,6,11
# ---- KP: job change needs Jupiter or Saturn transiting in star of a
#      significator of 6/10/11, AND Sun/Moon triggering.
def star_lord_of(lon): return DASHA_ORDER[int(lon//NAK_SPAN)%9]

sig_change = {p for p in GR if score(p,CHANGE)[0] >= 5}
sig_leave  = {p for p in GR if score(p,LEAVE)[0] >= 4}
print(f"\nStrong job-change significators: {sorted(sig_change)}")
print(f"Strong 'leave present job' significators: {sorted(sig_leave)}")

print("\nDAY-LEVEL SCAN 2026-2028: Jupiter AND Saturn both transiting stars of")
print("job-change significators, with Sun in such a star too (KP triple trigger)")
d=datetime(2026,1,1); hits=[]
while d<datetime(2029,1,1):
    jd=swe.julday(d.year,d.month,d.day,6.5)
    ju=swe.calc_ut(jd,swe.JUPITER,FLAGS)[0][0]%360
    sa=swe.calc_ut(jd,swe.SATURN,FLAGS)[0][0]%360
    su=swe.calc_ut(jd,swe.SUN,FLAGS)[0][0]%360
    jl,sl,ul = star_lord_of(ju),star_lord_of(sa),star_lord_of(su)
    if jl in sig_change and sl in sig_change and ul in (sig_change|sig_leave):
        hits.append((d.date(),jl,sl,ul))
    d+=timedelta(days=1)
# compress to ranges
if hits:
    start=hits[0]; prev=hits[0]
    for h in hits[1:]+[None]:
        if h is None or (h[0]-prev[0]).days>1:
            print(f"  {start[0]} -> {prev[0]}   Jup*{start[1]} Sat*{start[2]} Sun*{start[3]}")
            start=h
        if h: prev=h
else:
    print("  NONE — the triple condition never fires in this range")
