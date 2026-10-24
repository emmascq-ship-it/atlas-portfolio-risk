# Methodology and validation

ATLAS is a reproducible research prototype, not a trading system or independent
model-validation opinion. Default analytics use 900 seeded synthetic price dates,
seven assets, five classes and a hypothetical USD 1 million portfolio.

| Measure | Calculation and interpretation |
|---|---|
| Portfolio returns | Daily simple asset returns × constant long-only target weights; daily rebalancing, no fees or slippage |
| Historical VaR | Positive loss magnitude from the lower return quantile, floored at zero; empirical interpolation |
| Expected Shortfall | Positive mean loss in the observed tail at/below the historical quantile; floored at zero |
| Gaussian VaR | max(0, z(confidence) × sample standard deviation − mean), ddof=1 |
| Volatility | Sample daily standard deviation × sqrt(252) |
| Drawdown | Wealth divided by its high-water mark including initial $1, minus one |
| Stress | Sum of weight × explicit instantaneous class shock; deterministic and hypothetical |
| Factors | In-sample OLS with intercept against five descriptive ETF return-spread proxies; not causal exposures |
| Backtest | Forecast at t uses only returns [t−window,t); breach means realized loss strictly exceeds forecast |

The overview VaR/ES use the entire selected history. The validation view compares
Historical and Gaussian forecasts using the SAME preceding 250/500 sessions;
its latest forecast has a stated target date and can differ from overview VaR.
The JSON packet and CSV exports preserve unrounded inputs/outputs. Percentages in
the UI are rounded labels, not a different calculation. Read CSV float64 values
with a round-trip parser to reproduce the exact input fingerprint.

Default synthetic checks: 899 returns, 649 forecasts, 31 Historical and 30 Gaussian
breaches at 95% confidence. These are demonstrations, not out-of-time investment
performance. Default stress is −13.045% (−$130,450 per $1 million). No archived
inputs support the older 12.5% résumé claim; see STRESS_RECONCILIATION.md.

Validation covers arithmetic identities, no-look-ahead mutation tests, factor
reconstruction, loss/forecast/breach reconciliation, displayed metrics versus JSON,
CSV round trips, evidence hashes and approval revocation. Real browser downloads
in this run reproduced the full input SHA-256 and risk/factor/stress/backtest
outputs. The project owner reports the full Chromium/Streamlit/mobile preflight passed
in normal Mac Terminal. VERIFICATION_REPORT.md distinguishes those observations
from the agent sandbox execution limits; no real-market certification is implied.

Yahoo/yfinance is primary in optional market mode. The current session is excluded;
missing/invalid prices, stale feeds and adjustment failures stop analytics visibly.
No market-data error falls back to synthetic prices. Tiingo Starter checks are
optional, private, explicitly invoked and PENDING without usable free access.
Provider self-consistency is not independent verification. No provider-licensed
records belong in the public demo. No external AI requests are enabled.

Limits: sparse-tail asymptotic Kupiec/Christoffersen tests have limited power;
non-rejection is not validation. No liquidity horizon, nonlinear instruments,
transaction costs, regulatory capital or guaranteed loss bounds. Factors share
ETFs and may be collinear. Approval is a session-local attestation, not authenticated
identity, enterprise authorization or durable audit storage.
