from engine import *
from jaimini import *
from kp import c, score, CHANGE, LEAVE, FOREIGN, GR
from datetime import datetime, timedelta
import swisseph as swe
LAG=c.lagna_idx
def hfl(si): return ((si-LAG)%12)+1

# --- Chara antardashas
def chara_ad(md):
    direct = LAG in ODD
    out=[];t=md['start']; per=md['years']/12.0
    s=md['sign_idx']
    for i in range(12):
        sg=(s+i)%12 if direct else (s-i)%12
        end=t+timedelta(days=per*365.2425)
        out.append({'sign':SIGNS[sg],'sign_idx':sg,'start':t,'end':end}); t=end
    return out

print("CHARA ANTARDASHAS in current & next mahadasha (house from lagna)")
for md in chara_dasha(c,c.local):
    if md['end'].year<2026 or md['start'].year>2030: continue
    print(f"  MD {md['sign']} ({md['years']}y):")
    for ad in chara_ad(md):
        if ad['end'].year<2026 or ad['start'].year>2031: continue
        h=hfl(ad['sign_idx'])
        flag='  <-- 10th/11th/6th' if h in (10,11,6) else ''
        print(f"     AD {ad['sign']:12s} H{h:<2d} {ad['start']:%Y-%m-%d} -> {ad['end']:%Y-%m-%d}{flag}")

# --- Yogini antardashas
def yog_ad(md):
    i=[y[0] for y in YOG].index(md['yogini']); out=[];t=md['start']
    for k in range(8):
        y=YOG[(i+k)%8]
        yrs=md['years']*y[2]/36.0
        end=t+timedelta(days=yrs*365.2425)
        out.append({'yogini':y[0],'lord':y[1],'start':t,'end':end}); t=end
    return out
print("\nYOGINI ANTARDASHAS 2026-2031")
for md in yogini_dasha(c,3):
    if md['end'].year<2026 or md['start'].year>2031: continue
    for ad in yog_ad(md):
        if ad['end'].year<2026 or ad['start'].year>2031: continue
        sc=score(ad['lord'],CHANGE)[0]
        print(f"  {md['yogini']:9s}/{ad['yogini']:9s} ({ad['lord']:8s}) {ad['start']:%Y-%m-%d} -> {ad['end']:%Y-%m-%d}  chgScore {sc}")

# --- cross-system month agreement
print("\n\nCROSS-SYSTEM AGREEMENT SCAN (5 independent dasha/varga systems)")
print("Each system votes independently; 'votes' = how many flag career change\n")
v=vimshottari(c)
def vim_chain(dt,n=3):
    out=[];lvl=v['tree']
    for _ in range(n):
        x=next((q for q in lvl if q['start']<=dt<q['end']),None)
        if not x:break
        out.append(x['lord']);lvl=subdivide(x['lord'],x['start'],x['years'])
    return out
CH=chara_dasha(c,c.local); YG=yogini_dasha(c,3); AS=ashtottari(c,10)
A10=arudha(c,10); AL=arudha(c,1)

rows=[]
d=datetime(2026,1,1)
while d<datetime(2032,1,1):
    m=datetime(d.year,d.month,15); votes=[]; 
    # 1 Vimshottari: AD or PD is a strong change significator
    ch=vim_chain(m)
    if len(ch)>=3 and (score(ch[1],CHANGE)[0]>=5 or score(ch[2],CHANGE)[0]>=5): votes.append('Vim')
    # 2 Chara: MD or AD sign is 10th/11th/6th from lagna, or is A10 sign
    cmd=next((x for x in CH if x['start']<=m<x['end']),None)
    if cmd:
        cad=next((x for x in chara_ad(cmd) if x['start']<=m<x['end']),None)
        hs=[hfl(cmd['sign_idx'])]+([hfl(cad['sign_idx'])] if cad else [])
        if any(h in (10,11,6) for h in hs) or (cad and cad['sign_idx']==A10): votes.append('Chara')
    # 3 Yogini: AD lord is change significator >=5
    ymd=next((x for x in YG if x['start']<=m<x['end']),None)
    if ymd:
        yad=next((x for x in yog_ad(ymd) if x['start']<=m<x['end']),None)
        if yad and score(yad['lord'],CHANGE)[0]>=5: votes.append('Yogini')
    # 4 Ashtottari lord significator
    amd=next((x for x in AS if x['start']<=m<x['end']),None)
    if amd and score(amd['lord'],CHANGE)[0]>=4: votes.append('Ashtot')
    # 5 Gochara: Jupiter or Saturn transiting A10 sign or 10th from lagna/A10
    jd=swe.julday(m.year,m.month,15,6.5)
    ju=sign_of(swe.calc_ut(jd,swe.JUPITER,FLAGS)[0][0]%360)
    sa=sign_of(swe.calc_ut(jd,swe.SATURN,FLAGS)[0][0]%360)
    if ju in (A10,(A10+9)%12,(LAG+9)%12) or sa in (A10,(A10+9)%12,(LAG+9)%12): votes.append('Gochara')
    rows.append((m,len(votes),votes,'-'.join(ch[:3])))
    d=(d.replace(day=28)+timedelta(days=8)).replace(day=1)

for m,n,vt,ch in rows:
    bar='*'*n
    print(f"  {m:%Y-%m} {n} {bar:6s} {','.join(vt):32s} {ch}")
