"""Jaimini + alternative dasha systems, built fresh."""
from engine import *
from datetime import datetime, timedelta
GR=['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu']
ODD=[0,2,4,6,8,10]   # Aries,Gemini,Leo,Libra,Sag,Aquarius (sign index)

# ---------- extended vargas (Shodasavarga) ----------
# FIX v3: odd signs -> first hora Sun (Leo=4), second Moon (Cancer=3); even
# signs reversed (BPHS). v2 had it backwards for every sign.
def d2(l):  s=sign_of(l);p=int((l%30)//15); return (4 if s%2==0 else 3) if p==0 else (3 if s%2==0 else 4)
def d16(l): s=sign_of(l);p=int((l%30)//1.875); base={0:0,1:4,2:8}[s%3]; return (base+p)%12
def d20(l): s=sign_of(l);p=int((l%30)//1.5);  base={0:0,1:8,2:4}[s%3]; return (base+p)%12
def d24(l): s=sign_of(l);p=int((l%30)//1.25); base=4 if s%2==0 else 3; return (base+p)%12
# FIX v3: Bhamsa parts are 30/27 = 1d06'40" of a SIGN, starting Aries/Cancer/
# Libra/Capricorn for fire/earth/air/water. v2 divided the zodiac by 360/27
# (the nakshatra span) and returned nakshatra-index mod 12.
def d27(l): s=sign_of(l);p=int((l%30)//(30.0/27)); return (3*(s%4)+p)%12
def d30(l):
    s=sign_of(l); d=l%30; odd=s%2==0
    if odd:
        for lim,sg in [(5,0),(10,10),(18,8),(25,2),(30,6)]:
            if d<lim: return sg
    else:
        # FIX v3: even signs run Venus(Taurus) 5, Mercury(Virgo) 7, Jupiter
        # (Pisces) 8, Saturn(Capricorn) 5, Mars(Scorpio) 5. v2 swapped the
        # first and last lords (0-5 Scorpio, 25-30 Taurus).
        for lim,sg in [(5,1),(12,5),(20,11),(25,9),(30,7)]:
            if d<lim: return sg
def d40(l): s=sign_of(l);p=int((l%30)//0.75); base=0 if s%2==0 else 6; return (base+p)%12
def d45(l): s=sign_of(l);p=int((l%30)//(30/45)); base={0:0,1:4,2:8}[s%3]; return (base+p)%12
def d60(l): s=sign_of(l);p=int((l%30)//0.5); return (s+p)%12
ALLV={'D1':lambda l:sign_of(l),'D2':d2,'D3':d3_sign,'D4':d4_sign,'D7':d7_sign,
      'D9':d9_sign,'D10':d10_sign,'D12':d12_sign,'D16':d16,'D20':d20,'D24':d24,
      'D27':d27,'D30':d30,'D40':d40,'D45':d45,'D60':d60}

# ---------- Jaimini chara karakas ----------
def chara_karakas(c, scheme=8):
    """FIX v3: v2 ranked 8 bodies (Rahu included) against 7 labels, so the
    lowest-degree planet - the real Darakaraka - was silently dropped, the
    7th was mislabelled DK, and Putrakaraka never appeared.
    scheme=8: Sun..Saturn + Rahu (30-deg), AK AmK BK MK PiK PK GK DK.
    scheme=7: Sun..Saturn only,           AK AmK BK MK PK GK DK."""
    bodies = GR if scheme==8 else GR[:7]
    names = (['AK','AmK','BK','MK','PiK','PK','GK','DK'] if scheme==8
             else ['AK','AmK','BK','MK','PK','GK','DK'])
    vals={}
    for p in bodies:
        d=deg_in_sign(c.pos[p])
        vals[p]= 30-d if p=='Rahu' else d
    order=sorted(vals,key=lambda p:-vals[p])
    return {order[i]:names[i] for i in range(len(names))}, vals

# ---------- Arudha padas ----------
def arudha(c,house):
    sign=(c.lagna_idx+house-1)%12
    lord=SIGN_LORDS[SIGNS[sign]]
    lordsign=sign_of(c.pos[lord])
    count=(lordsign-sign)%12
    a=(lordsign+count)%12
    if a==sign or (a-sign)%12==6: a=(a+9)%12
    return a

# ---------- Chara dasha ----------
SAVYA=[0,1,2,6,7,8]   # Aries,Taurus,Gemini,Libra,Scorpio,Sagittarius
def chara_lord(sign_idx):
    s=SIGNS[sign_idx]
    if s=='Scorpio': return ['Mars','Ketu']
    if s=='Aquarius': return ['Saturn','Rahu']
    return [SIGN_LORDS[s]]

def chara_dasha(c, start, scheme='parity'):
    """scheme='parity' (default, unchanged v2 behaviour): direction and
    counting from odd/even sign. v2 labelled this 'KN Rao' - it is not.
    scheme='rao': direction from the 9th house and counting by footedness
    group (Aries-Gemini, Libra-Sag forward; the rest backward), per K.N. Rao.
    Dual-lord selection is the simple max-degree rule in both schemes."""
    grp = ODD if scheme=='parity' else SAVYA
    ref = c.lagna_idx if scheme=='parity' else (c.lagna_idx+8)%12
    direct = ref in grp
    seq=[]; cur=c.lagna_idx
    for _ in range(12):
        seq.append(cur); cur=(cur+1)%12 if direct else (cur-1)%12
    out=[]; t=start
    for s in seq:
        lords=chara_lord(s)
        # strongest lord: the one with more degrees advanced (simple rule)
        lord=max(lords,key=lambda p:deg_in_sign(c.pos[p]))
        ls=sign_of(c.pos[lord])
        if s in grp: cnt=(ls-s)%12+1
        else:        cnt=(s-ls)%12+1
        yrs=cnt-1
        if yrs==0: yrs=12
        end=t+timedelta(days=yrs*365.2425)
        out.append({'sign':SIGNS[s],'sign_idx':s,'lord':lord,'years':yrs,'start':t,'end':end})
        t=end
    return out

# ---------- Yogini dasha (36-yr cycle) ----------
YOG=[('Mangala','Moon',1),('Pingala','Sun',2),('Dhanya','Jupiter',3),
     ('Bhramari','Mars',4),('Bhadrika','Mercury',5),('Ulka','Saturn',6),
     ('Siddha','Venus',7),('Sankata','Rahu',8)]
def yogini_dasha(c,cycles=4):
    moon=c.pos['Moon']; nk=int(moon//NAK_SPAN)  # 0-based
    # FIX v3: rule is remainder of (1-based nakshatra no. + 3)/8, remainder 1 =
    # Mangala ... 0 = Sankata. 0-based index = (nk+1+3-1) % 8 = (nk+3) % 8.
    # v2 used (nk+4)%8: every chart got the NEXT yogini (Ashwini -> Bhadrika
    # instead of Bhramari).
    idx=(nk+3)%8
    frac=(moon%NAK_SPAN)/NAK_SPAN
    y0=YOG[idx]
    start=c.local-timedelta(days=y0[2]*frac*365.2425)
    out=[];t=start;i=idx
    for k in range(8*cycles):
        y=YOG[i%8]
        end=t+timedelta(days=y[2]*365.2425)
        out.append({'yogini':y[0],'lord':y[1],'years':y[2],'start':t,'end':end})
        t=end;i+=1
    return out

# ---------- Ashtottari dasha (108 yrs) ----------
ASHT_ORDER=['Sun','Moon','Mars','Mercury','Saturn','Jupiter','Rahu','Venus']
ASHT_YRS={'Sun':6,'Moon':15,'Mars':8,'Mercury':17,'Saturn':10,'Jupiter':19,'Rahu':12,'Venus':21}
# FIX v3: groups from Ardra are 4,3,4,3,4,3,4,3 in the 28-nakshatra scheme
# (Saturn's 4 includes Abhijit). v2 had 3,4,3,4,3,4,3,3 - six of eight lords
# owned the wrong stars. Abhijit is folded into Uttara Ashadha / Shravana
# here (27-nakshatra convention), so Saturn holds 3.
ASHT_GROUPS=[('Sun',[5,6,7,8]),('Moon',[9,10,11]),('Mars',[12,13,14,15]),
             ('Mercury',[16,17,18]),('Saturn',[19,20,21]),
             ('Jupiter',[22,23,24]),('Rahu',[25,26,0,1]),
             ('Venus',[2,3,4])]
def ashtottari(c,n=12):
    nk=int(c.pos['Moon']//NAK_SPAN)
    lord=next(l for l,ns in ASHT_GROUPS if nk in ns)
    grp=next(ns for l,ns in ASHT_GROUPS if l==lord)
    pos_in=grp.index(nk)
    frac=(pos_in+(c.pos['Moon']%NAK_SPAN)/NAK_SPAN)/len(grp)
    start=c.local-timedelta(days=ASHT_YRS[lord]*frac*365.2425)
    out=[];t=start;i=ASHT_ORDER.index(lord)
    for k in range(n):
        l=ASHT_ORDER[i%8]
        end=t+timedelta(days=ASHT_YRS[l]*365.2425)
        out.append({'lord':l,'start':t,'end':end,'years':ASHT_YRS[l]})
        t=end;i+=1
    return out
