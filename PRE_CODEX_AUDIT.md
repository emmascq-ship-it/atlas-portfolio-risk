# ATLAS V7.1 — pre-Codex audit and launch gates

**Assessment:** Research-grade, reproducible, compelling interactive synthetic demo. **Not yet production-grade, not yet publicly deployed, and not yet a verified live-market monitoring system.** This document separates demonstrable features from future work.

## Verified in this handoff

- 102 Python unit/regression tests and the existing real Chromium browser test pass in the supplied environment.
- Deterministic synthetic seven-asset/five-class risk analysis; 250-session lookback; historical versus Gaussian VaR, ES, backtesting, factor-spread proxy exposures, stress scenarios, and unapproved research report exports.
- The default modeled equity-selloff is **-13.045%** under documented weights and shocks, **not the 12.5%** in a prior resume. Do not change the model to force a match. A truthful interview explanation is to describe it as a changed set of explicit demo assumptions; the 12.5% claim requires separate historical scenario evidence if retained.
- The static GitHub Pages demo is intentionally **synthetic and offline**, not a live-updating trading system. Scenario sliders change hypothetical linear scenario P&L only; they do not recalculate full VaR or retroactively modify approved analysis.
- Eight hard structural input checks remain intact; duplicate labels and invalid rolling returns now fail explicitly instead of causing hard-to-diagnose downstream results.
- Publish CLI now blocks any user-provided CSV from being written **anywhere under public docs/** unless an explicit `--confirm-public-data` switch is given, including absolute or alternative paths. Never use the override for private holdings.

## Verification boundaries / release blockers

1. **Streamlit E2E:** No executable Streamlit installation was available in this handoff environment, so full `app.py` functionality, navigation, upload and approval mechanics still require a fresh browser run.
2. **Live data:** `yfinance` and real ETF ingestion are not revalidated in this handoff. Need market data licensing/terms check and independent adjusted-close/corporate-action consistency checks before representing the app as live.
3. **Hosted deployment:** No GitHub Pages URL or Streamlit Cloud deployment has been created or tested; do not claim one exists.
4. **AI:** A deterministic evidence-linked draft and an opt-in external LLM adapter exist, but no production-like external API, refusal, hostile input, or key-management E2E was verified in this handoff. Static demo commentary is **not AI-generated output**.
5. **Quant model constraints:** Daily constant-weight portfolio; illustrative static stress shocks; no trading costs, spread/slippage, liquidity horizons, tail dependence or regulatory market-risk capital assessment. VaR Kupiec/Christoffersen p-values have limited power in sparse-tail cases. ETF return-spread proxies are descriptive, in-sample, and not independently identified causal factors.
6. **Data privacy:** GitHub Pages `docs/index.html` is public. Only generate and deploy synthetic data. Keep `.env` and `.streamlit/secrets.toml` out of repository; store hosted secrets in approved app settings.

## Hardening changes in V7.1

- `risk_engine.validate_prices`: reject duplicate asset columns and duplicate weight labels (preserving exactly eight declared hard controls).
- `risk_engine.portfolio_returns` / `historical_var_es` / `rolling_var_backtest`: reject nonfinite results, invalid or unchronological direct backtest inputs, invalid windows and impossible loss returns.
- `publish_demo.py`: resolve output path and protect all public `docs/` descendants, not merely relative `docs/index.html`.
- `tests/test_release_hardening.py`: nine targeted regression tests for the above boundary conditions; the suite moves from 93 to 102 tests.
- `release_preflight.py`: one-command offline go/no-go gate (unit tests, demo CLI, published synthetic evidence, reproducible HTML checksum, public folder hygiene, obvious local credential file presence). Optional `--browser` for Playwright smoke.

## Next Codex tasks — prioritize by confidence gained per token

1. Run `python release_preflight.py --browser`, install `requirements.txt` in a clean Python 3.12 environment, then run `streamlit run app.py`. Fix reproducible E2E bugs, **not speculative rewrites**.
2. Run with market-data mode using completed sessions, compare selected vendor prices with an independent adjusted-price source and verify error handling (API outage, empty ticker, missing values, short sample, partial current day).
3. Add a Streamlit browser E2E test that checks risk metrics, factor view, CSV input failure, review status, analyst approval revocation and the date/source disclaimers.
4. Deploy **synthetic-only** static `docs/` to GitHub Pages, manually verify live URL, 390px mobile responsive layout and exports. Consider Streamlit Cloud after interactive Streamlit smoke passes.
5. Only after those gates, refine performance, accessibility and typed frontend components. A React/Next.js rewrite is an optional tradeoff, **not required** for a polished public research demo.

## Definition of done before linking on a resume

Working public demo URL; user can switch all pages and run a stress scenario; clear synthetic source badge; a documented model method and its limitations; no fabricated AI results or regulatory approval; confirmed version tag/reproducible build; publicly accessible GitHub README that explains assumptions, validation and reproducibility.

## Copy-ready Codex instructions

> Continue this repository **in place**. Read `PRE_CODEX_AUDIT.md`, `CODEX_HANDOFF.md`, `MODEL_VALIDATION_RESEARCH.md`, and `DESIGN_SYSTEM.md`. First run `python release_preflight.py --browser`; report only actual failures. Do not rewrite already tested risk modules or change the -13.045% synthetic baseline to match a resume claim. Next install the full app dependencies in Python 3.12, run `streamlit run app.py`, add a reproducible Streamlit E2E smoke test, test market-data outages and privacy, then prepare a synthetic-only public deployment. Preserve the existing UNAPPROVED and evidence-review workflow. For each change report affected files, test command/results, and remaining release blockers; avoid speculative large architectural rewrites.
