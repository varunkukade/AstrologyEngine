"""KP significator machinery + career-window scoring. Built from scratch."""
from engine import *
from interpret import *
from datetime import datetime, timedelta

c = natal()
GR = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']

# ---- which house does each planet OCCUPY (KP uses cusp-based, not whole sign)
def kp_house_of(lon, cusps):
    for h in range(12):
        a = cusps[h]; b = cusps[(h+1) % 12]
        if a <= b:
            if a <= lon < b: return h+1
        else:
            if lon >= a or lon < b: return h+1
    return None

occ = {p: kp_house_of(c.pos[p], c.cusps) for p in GR}
# ownership (whole-sign rulership of the sign each cusp falls in)
owns = {p: [] for p in GR}
for h in range(1,13):
    lord = SIGN_LORDS[SIGNS[sign_of(c.cusps[h-1])]]
    owns[lord].append(h)

star_of = {p: kp_sub(c.pos[p])[0] for p in GR}
sub_of  = {p: kp_sub(c.pos[p])[1] for p in GR}

# FIX v3: these were defined inside `if __name__ == '__main__'`, so
# timing/gochara/converge/cross/days all died with ImportError.
# ---- 4-fold significators (Krishnamurti's order of strength)
def significators(house):
    A = [p for p in GR if star_of[p] in [q for q in GR if occ[q]==house]]  # in star of occupant
    B = [p for p in GR if occ[p]==house]                                    # occupant
    C = [p for p in GR if star_of[p] in [q for q in GR if house in owns[q]]]# in star of owner
    D = [p for p in GR if house in owns[p]]                                 # owner
    return A,B,C,D

def sig_set(house):
    A,B,C,D = significators(house)
    return set(A+B+C+D)

# ---- planet-level: does a planet signify job-change houses?
CHANGE = [6,10,11]      # new service, profession, gain/fulfilment
LEAVE  = [5,9,12]       # 12th to 6th = leaving present job (5th), 9th=change of place, 12th=foreign/exit
FOREIGN= [9,12,3,7]     # long distance, foreign residence, short travel, dealings with others

def score(planet, houses):
    s = 0; why=[]
    for h in houses:
        A,B,C,D = significators(h)
        if planet in A: s+=4; why.append(f"H{h}:starOfOccupant")
        elif planet in B: s+=3; why.append(f"H{h}:occupant")
        elif planet in C: s+=2; why.append(f"H{h}:starOfOwner")
        elif planet in D: s+=1; why.append(f"H{h}:owner")
    return s, why


if __name__ == "__main__":
    print("KP OCCUPANCY / OWNERSHIP / STAR")
    for p in GR:
        print(f"  {p:8s} occupies H{occ[p]:<2d} owns {str(owns[p]):12s} star-lord {star_of[p]:8s} sub {sub_of[p]}")

    for h in [2,6,9,10,11,12]:
        A,B,C,D = significators(h)
        print(f"\nH{h} significators:")
        print(f"   A (star of occupant): {A}")
        print(f"   B (occupant)        : {B}")
        print(f"   C (star of owner)   : {C}")
        print(f"   D (owner)           : {D}")

    print("\n\nPLANET SCORES")
    print(f"{'Planet':9s} {'JobChange(6,10,11)':22s} {'Leave(5,9,12)':18s} {'Foreign(9,12,3,7)':18s}")
    for p in GR:
        a,_=score(p,CHANGE); b,_=score(p,LEAVE); d,_=score(p,FOREIGN)
        print(f"{p:9s} {a:<22d} {b:<18d} {d:<18d}")

    print("\nCUSP SUB-LORDS (KP: the sub-lord of the cusp decides the matter)")
    for h in [2,6,9,10,11,12]:
        st,sb,ss = kp_sub(c.cusps[h-1])
        a,why = score(sb, CHANGE); f,fwhy = score(sb, FOREIGN)
        print(f"  C{h:2d} sublord {sb:8s} | jobchange score {a} {why} | foreign score {f} {fwhy}")
