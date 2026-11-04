from engine import *
from interpret import *
from kp import c, score, CHANGE, LEAVE, FOREIGN, GR
from datetime import datetime, timedelta
import swisseph as swe

bav = bhinnashtakavarga(c); sav = sarvashtakavarga(bav)
LAG=c.lagna_idx; MOONS=sign_of(c.pos['Moon'])
def star_lord_of(l): return DASHA_ORDER[int(l//NAK_SPAN)%9]
sig_change={p for p in GR if score(p,CHANGE)[0]>=5}
sig_leave ={p for p in GR if score(p,LEAVE)[0]>=4}
sig_frgn  ={p for p in GR if score(p,FOREIGN)[0]>=4}

v=vimshottari(c)
def dasha_lords(dt):
    out=[]; lvl=v['tree']
    for _ in range(4):
        n=next((x for x in lvl if x['start']<=dt<x['end']),None)
        if not n: break
        out.append(n['lord']); lvl=subdivide(n['lord'],n['start'],n['years'])
    return out

# D10 lagna & how transits sit in D10
d10 = divisional_chart(c,'D10'); D10L = d10['_lagna']

monthly=[]
d=datetime(2026,1,1)
while d<datetime(2032,1,1):
    jd=swe.julday(d.year,d.month,15,6.5)
    pos={n:swe.calc_ut(jd,p,FLAGS)[0][0]%360 for n,p in PLANET_IDS.items()}
    pos['Ketu']=(pos['Rahu']+180)%360
    L=dasha_lords(datetime(d.year,d.month,15))
    if len(L)<3: d=(d.replace(day=28)+timedelta(days=8)).replace(day=1); continue

    s=0; ev=[]
    # 1. dasha significator weight (AD weighted most)
    for lord,w in zip(L[:4],[1.0,2.0,1.5,0.5]):
        s+= w*score(lord,CHANGE)[0]*0.3
        s+= w*score(lord,LEAVE)[0]*0.2
    # 2. Jupiter in star of change-significator
    if star_lord_of(pos['Jupiter']) in sig_change: s+=3; ev.append('Jup*sig')
    # 3. Saturn in star of change-significator
    if star_lord_of(pos['Saturn']) in sig_change: s+=3; ev.append('Sat*sig')
    # 4. Jupiter gochara favourable from Moon (2,5,7,9,11)
    hj=((sign_of(pos['Jupiter'])-MOONS)%12)+1
    if hj in (2,5,7,9,11): s+=2; ev.append(f'JupG{hj}')
    # 5. Saturn over 10th/11th from lagna
    hs=((sign_of(pos['Saturn'])-LAG)%12)+1
    if hs in (10,11): s+=2.5; ev.append(f'Sat H{hs}')
    # 6. SAV of sign Jupiter transits
    s += (sav[sign_of(pos['Jupiter'])]-28)*0.3
    # 7. Rahu over 6th/10th/11th (career disruption/gain)
    hr=((sign_of(pos['Rahu'])-LAG)%12)+1
    if hr in (10,11,6): s+=1.5; ev.append(f'Rah H{hr}')
    # 8. D10: Jupiter or Saturn in D10 1st/10th/11th from D10 lagna
    for pl in ('Jupiter','Saturn'):
        hd=((d10_sign(pos[pl])-D10L)%12)+1
        if hd in (10,11,1): s+=1.5; ev.append(f'{pl[:3]}D10H{hd}')

    fr = sum(score(l,FOREIGN)[0] for l in L[:3])
    monthly.append((d.year,d.month,s,fr,'-'.join(L[:3]),','.join(ev)))
    d=(d.replace(day=28)+timedelta(days=8)).replace(day=1)

print("MONTHLY CONVERGENCE SCORE (higher = more independent methods agree)")
top=sorted(monthly,key=lambda x:-x[2])[:20]
for y,m,s,fr,l,ev in sorted(top,key=lambda x:(x[0],x[1])):
    print(f"  {y}-{m:02d}  score {s:5.1f}  foreign {fr:2d}  {l:22s} {ev}")

print("\nFULL 2026-2028 MONTH BY MONTH")
for y,m,s,fr,l,ev in monthly:
    if y>2028: break
    bar='#'*int(max(0,s))
    print(f"  {y}-{m:02d} {s:5.1f} {bar:22s} {l:20s} frgn{fr:2d}")
