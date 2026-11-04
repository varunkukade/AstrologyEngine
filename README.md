# Vedic Astrology Calculation Engine

Sidereal (Lahiri) chart engine on Swiss Ephemeris: positions, Placidus/KP cusps,
16 divisional charts, dignity, Vimshottari to 5 levels, KP star/sub/sub-sub lords
and four-fold significators, Ashtakavarga, yoga detection, Sade Sati from real
ingress scanning, Jaimini karakas/arudhas, and Chara, Yogini and Ashtottari dashas.

## Setup

```bash
pip install -r requirements.txt
cp birth.example.json birth.json   # then edit with real birth data
```

`birth.json` is git-ignored. Without it the engine falls back to the example chart.

## Run

| Command | Output |
|---|---|
| `python3 run.py` | Natal chart, cusps, vargas, dashas, transits |
| `python3 report.py` | Ashtakavarga, yogas, neecha bhanga, Saturn phases |
| `python3 kp.py` | KP significators and house scores |
| `python3 timing.py`, `gochara.py`, `converge.py`, `cross.py`, `days.py` | Timing layers |
| `python3 nulltest.py` | Real chart vs 200 random charts |
| `python3 stability.py` | Same chart, analyst rule choices varied |

## Modules

`engine.py` → `interpret.py` → `jaimini.py` → `kp.py`. Library modules are silent
on import; drivers print only under `__main__`.

## Validation — read before using timing output

The arithmetic is checked (e.g. Saturn's Pisces ingress resolves to
29 Mar 2025 21:44 IST, matching published panchangs; BAV totals reproduce
48/49/39/54/56/52/39 = 337).

Predictive validity is not established:

- **Null test:** the scoring pipeline's peak for the real chart sits around the
  94th percentile of random charts (one-sided p ≈ 0.06). The rules were chosen
  while looking at the real chart, so even that is inflated.
- **Stability test:** with the chart held fixed, toggling which classical rules
  are consulted spreads the "best month" across ~25 of 72 months.

Treat timing output as exploratory, not as a basis for decisions.

## Conventions you may want to change

- Year length 365.2425 days (classical alternatives: 365.25, 360)
- Mean node, not true node
- Chara dasha defaults to lagna-parity direction; `chara_dasha(c, t, scheme='rao')` for K.N. Rao's rules
- Chara karakas default to the 8-karaka scheme; `chara_karakas(c, scheme=7)` for 7
- Ashtottari folds Abhijit into the 27-nakshatra scheme
