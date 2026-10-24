# ATLAS engineering guidance

Applies to this repository only. The parent AGENTS.md is an upstream Streamlit
monorepo reference; its uv, Make, directory, branch and frontend build rules do
not apply here. Do not change that parent file for ATLAS work.

- Read PRE_CODEX_AUDIT.md, CODEX_HANDOFF.md and DESIGN_SYSTEM.md before changes.
- Use Python 3.12 and an isolated virtual environment. Install requirements.txt
  (or requirements-test.txt for browser tests); requirements.lock constrains all
  runtime/test dependencies. Do not install unpinned upgrades during validation.
- Run `python release_preflight.py --browser` for the complete release gate.
  `python release_preflight.py` runs offline checks only. Report a blocked browser
  as blocked, never passed. CI must run both static and Streamlit browser suites.
- Preserve passing risk_engine.py, factor_engine.py, validation_extensions.py,
  model_benchmark.py and their assumptions. Fix demonstrated defects with focused
  regression coverage; do not rewrite financial models for UI or résumé claims.
- Default synthetic scenario is -13.045%. Historical loss claims require archived
  inputs and provenance. Do not tune weights or shocks to produce 12.5%.
- Preserve modern UI, synthetic disclosures, evidence IDs, unrounded input hashes,
  citation gates, explicit human approval and revocation on draft/input changes.
- AI generates prose only. Citation presence does not verify truth. Never send
  external AI requests in tests, persist API keys, or auto-approve a draft.
- Market-data failures stop analytics visibly. Never substitute synthetic prices
  in market mode. Distinguish provider self-consistency from independent checks.
- Edit templates/assets, then regenerate docs/index.html; never hand-edit generated
  HTML. Only synthetic data may enter public docs/. Keep private fixtures, holdings,
  keys and reference-vendor data out of docs/ and browser/CI artifacts.
- No public deployment, remote publishing or GitHub Actions dispatch is implied by
  this guide. Follow the user's explicit authorization. No public deployment now.
- Hard budget: $0. No paid subscriptions, trials, upgrades, billing details or
  paid API calls. Active briefing uses offline deterministic prose only. Tiingo
  is optional, explicitly invoked with an existing free Starter account; missing
  or insufficient free access means PENDING. No provider data redistribution.
  Do not run hosted CI where it can consume billable private-repository minutes.
- Use work/ for scratch files and preserve evidence of test commands and failures.
