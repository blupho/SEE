# SEE — Spill Emission Estimator

Streamlit app: https://spillemissions.streamlit.app

Estimates evaporative emissions from liquid spills with three methods:

1. **Method 1** — RMP Guidance Equation D-1 (wind-sensitive, conservative)
2. **Method 2** — EPA EIIP Volume II Chapter 16 Eq. 3-24 (open-top vessel / spill)
3. **Method 3** — Empirical evaporation equations (Fingas Table 7.2; only for products with lab-derived equations)

## Product profiles are Google Sheet–driven

Product profiles (vapor pressure, vapor molecular weight, vapor-component weight %)
are read from a public Google Sheet:
<https://docs.google.com/spreadsheets/d/1duewVkxON4m83aXbcMZcwRRygz9AtkYRPNBDRT5_F_g/edit>

- **Add a product**: add a row to the sheet (name, vapor pressure in PSI, vapor MW,
  note, then one column per vapor component with its weight %). No code changes
  needed — it shows up in the app within 10 minutes, or click
  **"Reload profiles now"** in the sidebar.
- **Add a component**: add a column to the right of the note column
  (`weight% of Vapor Components ->`).
- **Speciation**: the app shows a component breakdown for every method —
  pounds of each component = method total × component weight % / 100. The
  remainder (weight % not summing to 100) is reported as "Other / uncharacterized".
- **Method 3** only exists for products with empirical equations (currently
  Gasoline, WTI Crude, Diesel Fuel — see `EMPIRICAL` in `SEE.py`). Other products
  get Methods 1 & 2 plus speciation.
- If the sheet is unreachable, the app falls back to a bundled copy
  (`FALLBACK_CSV` in `SEE.py`) so it never breaks.

## Development

```bash
streamlit run SEE.py
```

Logic functions (parsing, equations, speciation) are Streamlit-free and
unit-testable.

---

All rights reserved by Dayu Zhang.

I devloped this web app in my personal time, on my personal computer for satisfying my personal curiosity. I'm not responsible for any violations, penalties, jail time, injuries, confusion, divorces or nuclear holocausts caused by using this app.
