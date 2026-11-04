"""CLI:  python -m astroengine birth.json [--as-of 2026-11-04T12:00:00+05:30]
        [--out chart.json] [--set ayanamsa=raman --set node=true ...]"""
import argparse
import json
import sys
from datetime import datetime, timezone
from dataclasses import fields

from .config import Config
from .compute import compute


def _coerce(name, raw):
    typ = {f.name: f.type for f in fields(Config)}[name]
    typ = typ if isinstance(typ, type) else {"str": str, "bool": bool, "int": int,
                                             "float": float}[typ]
    if typ is bool:
        return raw.lower() in ("1", "true", "yes")
    return typ(raw)


def summary(r):
    L = []
    b = r["birth"]
    L.append(f"{b['name'] or 'Chart'}  {b['local_time']}  ({b['latitude']}, {b['longitude']})  "
             f"gender={b['gender']}")
    L.append(f"Ayanamsa {r['ayanamsa']['name']} {r['ayanamsa']['dms']}   "
             f"Lagna {r['lagna']['sign']} {r['lagna']['dms']} ({r['lagna']['nakshatra']['name']} "
             f"pada {r['lagna']['nakshatra']['pada']})")
    L.append("")
    L.append(f"{'Planet':8} {'Sign':12} {'Deg':11} {'H':>2} {'Nakshatra':18} {'Pd':>2} R  Dignity")
    for p, v in r["planets"].items():
        L.append(f"{p:8} {v['sign']:12} {v['dms']:11} {v['whole_sign_house']:>2} "
                 f"{v['nakshatra']['name']:18} {v['nakshatra']['pada']:>2} "
                 f"{'R' if v['retrograde'] else ' '}  {v['dignity']}")
    pan = r["panchanga"]
    L.append("")
    L.append(f"Vara {pan['vara']['weekday']} | Tithi {pan['tithi']['paksha']} {pan['tithi']['name']} | "
             f"Yoga {pan['yoga']['name']} | Karana {pan['karana']['name']} | Sunrise {pan['sunrise']}")
    run = r["dashas"]["vimshottari"].get("running_at_reference", [])
    if run:
        L.append("Vimshottari at as_of: " + " > ".join(x["lord"] for x in run) +
                 f"  (sookshma ends {run[-1]['end']})")
    L.append("Yogas: " + ", ".join(y["name"] for y in r["yogas"]["yogas"]))
    sens = r["birth_time_sensitivity"]["factors"]
    L.append(f"Birth-time sensitivity (minutes earlier/later): lagna sign "
             f"{sens['lagna_sign']['minutes_earlier']}/{sens['lagna_sign']['minutes_later']}, "
             f"D9 lagna {sens['D9_lagna']['minutes_earlier']}/{sens['D9_lagna']['minutes_later']}")
    for w in r["warnings"]:
        L.append("WARNING: " + w)
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="astroengine")
    ap.add_argument("birth", help="birth JSON file")
    ap.add_argument("--as-of", help="ISO datetime with offset for transits/running dasha")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="override a Config field")
    ap.add_argument("--transit-years", type=int, default=100)
    ap.add_argument("--summary", action="store_true",
                    help="print a short human-readable overview instead of JSON")
    a = ap.parse_args(argv)

    with open(a.birth) as f:
        birth = json.load(f)
    kw = {}
    for s in a.set:
        k, v = s.split("=", 1)
        kw[k] = _coerce(k, v)
    as_of = None
    if a.as_of:
        as_of = datetime.fromisoformat(a.as_of)
        if as_of.tzinfo is None:
            ap.error("--as-of needs a UTC offset, e.g. 2026-11-04T12:00:00+05:30")
    res = compute(birth, Config(**kw), as_of=as_of, transit_years=a.transit_years)
    txt = summary(res) if a.summary else json.dumps(res, indent=2, ensure_ascii=False)
    if a.out:
        with open(a.out, "w") as f:
            f.write(txt)
    else:
        sys.stdout.write(txt + "\n")


if __name__ == "__main__":
    main()
