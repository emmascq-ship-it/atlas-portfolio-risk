# ATLAS V7 | Model validation research and implementation choices

**Scope:** Research prototype, not a regulated VaR engine, investment decision system, or independent model-validation opinion. All default outputs use a seeded **synthetic** price history.

## Regulatory-methodology reference (checked 22 October 2026)

The US Federal Reserve published **SR 26-2 on 17 April 2026**, superseding SR 11-7. The revised interagency guidance is most relevant to supervised banks and emphasizes a proportional, risk-based approach, including development, testing, ongoing monitoring, outcome analysis, and defined governance responsibilities. **ATLAS is not a banking organization and makes no claim of compliance.** This source motivates documentation and transparent verification patterns, not regulatory certification.

- Federal Reserve, *SR 26-2 Revised Guidance on Model Risk Management*, April 17, 2026: https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm
- Federal Reserve, *Supervisory Guidance on Model Risk Management* (revised 2026): https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm
- OCC, *Model Risk Management: Revised Guidance*, 2026: https://www.occ.ustreas.gov/news-issuances/bulletins/2026/bulletin-2026-13.html
- Christoffersen, P.F. (1998), *Evaluating Interval Forecasts*, International Economic Review 39(4), 841–862: https://ideas.repec.org/a/ier/iecrev/v39y1998i4p841-62.html

## Changes after examining V6 code

1. **Corrected wealth high-water mark:** original max drawdown used `wealth.cummax()` without the starting $1 NAV. A sample beginning at -20% then +5% must have an initial -20% drawdown. In V7, the high-water mark is `max(initial 1.0, cumulative wealth peak)`; both Python report and offline chart use the same definition.
2. **Independent formula, shared data:** in addition to empirical historical-simulation VaR, V7 computes parametric Gaussian VaR using *the same trailing returns* (sample mean and standard deviation with `ddof=1`). It is a **methodological comparator**, not independent market observations. Formula: `max(0, z_confidence * sample_std - trailing_mean)` for a one-day loss quantile.
3. **No look-ahead:** forecast at index `t` uses only `[t-window, t)` returns. Regression tests mutate day `t` and confirm forecast `t` remains unchanged.
4. **Severity plus hit rate:** benchmark rows report number/rate of breaches, the longest consecutive breach streak, mean/worst excess realized loss over VaR, Kupiec coverage and Christoffersen combined tests.
5. **Fragile p-value warnings:** the tests rely on asymptotic chi-square approximations. Expected exceptions fewer than 10, or very sparse transition counts, trigger warnings. Failure to reject is **not** positive validation.
6. **More reliable input acceptance:** price tables must have monotonic, nonmissing daily timestamp indexes and non-boolean numeric values; merely having ascending integer row numbers does not count as valid dates.
7. **Data quality differs from data truth:** supplementary checks flag outdated snapshots and unexpectedly large weekday gaps. They do not account for every trading holiday and **cannot** establish that a provider price series is correct or licensed.

## Default demonstration observations (synthetic, not empirical market claims)

- 900 synthetic price observations imply 899 returns and **649 out-of-sample one-day forecasts** using a prior-250-day window.
- At 95% confidence, **32.45** exceptions are expected under the simple nominal coverage model; seeded demonstration yields **31 historical VaR breaches** and **30 Gaussian VaR breaches**.
- The baseline instantaneous **Equity selloff** synthetic scenario remains **-13.045%** under V6/V7 weights and shocks. A prior resume bullet citing -12.5% is **not reproduced by these exact assumptions**. Do not change inputs just to match that number.

## What requires more work before describing this as professional production software

- External verification of market data quality, corporate actions and usage rights (Yahoo Finance is an unofficial convenience source).
- Independent factor calibration and methodology benchmarking across out-of-time market regimes; the current regression is an in-sample, self-referential ETF-spread *descriptive* analysis.
- Streamlit real-browser run, live feed failure tests, authenticated reviewer identity, durable audit storage, server-side credentials and authorization.
- GitHub Pages publication of **synthetic-only** demo and review of the actual public URL. Offline HTML has no authenticated approvals or persistence.

## Skills/resources useful later (search GitHub carefully; inspect trust and licensing)

- `frontend-design SKILL.md` — component hierarchy, UX and responsive visual polish.
- `playwright browser testing SKILL.md` — real-browser regression of the Streamlit interface and deployed HTML.
- `quantitative risk backtesting python` — numerical reference implementations to cross-check, not blindly copy.

V7 does not require these downloads: it is already independently testable with installed standard tools. Avoid granting unreviewed skills arbitrary access to private financial files or secrets.
