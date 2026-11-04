# research/

`legacy/` is the previous (v3) engine and the timing experiments built on it,
kept unchanged for reproducibility. **It is not part of `astroengine`**, and it still
has the bugs listed in the root README (Moshier fallback, Lahiri used for KP, IST
hard-coded, single-cycle Chara dasha, ...).

Run the scripts from inside `legacy/` (they read `legacy/birth.json` or fall back to
`legacy/birth.example.json`).

What the experiments found, worth keeping in mind for any predictive use of the
engine's output:

- **Null test (`nulltest.py`):** the career-window score of the real chart sat at about
  the 94th percentile of 200 random charts (one-sided p ≈ 0.06). The rules were chosen
  while looking at the real chart, so even that figure is inflated.
- **Stability test (`stability.py`):** with the chart held fixed, toggling which classical
  rules are consulted spread the "best month" across about 25 of 72 months.
