# Codex handoff — ATLAS Portfolio Risk Intelligence V7.1

**Start here to save analysis tokens.** This is an already-built repo, not a blank-slate project.

## One-sentence objective
Finish a shareable, professionally designed portfolio risk analytics product while preserving research provenance, no-look-ahead VaR validation and human-approval controls.

## Do not rebuild
- `risk_engine.py` risk calculations, `factor_engine.py`, `validation_extensions.py`, `research_packet.py`, `briefing_workflow.py`
- `static_dashboard.py` serialized research snapshot, V7 HTML template, embedded Plotly
- `model_benchmark.py` matched-window Gaussian/Historical VaR diagnostics
- `data_quality.py` supplementary warning heuristics
- Five-section offline page, 3 scenario presets, CSV/JSON export and safeguards
- Existing tests (102 in V7.1)

## Critical files
- `app.py` — original Streamlit application (separate from static demo; requires browser smoke test)
- `templates/offline_dashboard.html` — all V7 page structure, CSS tokens
- `assets/v5_app.js` — original chart/event handlers
- `assets/v6_app.js` — expanded analytics, presets, export workflow, keyboard interaction
- `static_dashboard.py` — model to safe embedded research payload
- `publish_demo.py` — static HTML builder with data-publication safeguard
- `tests/browser_smoke_v7.py` — optional real-browser interaction test
- `docs/index.html` — **generated**. Edit source templates/JS instead of editing HTML manually.

## Quick commands
```bash
python -m pip install -r requirements-static.txt
python release_preflight.py --browser
python -m unittest discover -s tests -q
python publish_demo.py
python tests/browser_smoke_v7.py  # needs Chromium and playwright
python -m pip install -r requirements.txt
streamlit run app.py
```

## Immediate next Codex tasks (in priority order)

Read `PRE_CODEX_AUDIT.md` and `MODEL_VALIDATION_RESEARCH.md` first. Gaussian comparator exists in the research packet/static demo, but full Streamlit UI parity is still pending.
1. **Launch Streamlit**, test all tabs, market-data and CSV options, approval state, and errors; fix actual runtime problems. Do not claim tested until successful.
2. Bring Streamlit UI typography, labels, scenario handling and evidence controls closer to the V7 static design system. Preserve meaningful UX consistency, not exact HTML parity.
3. Add real market feed reliability tests (completed trading sessions, adjusted values, missing data, provider outages) and cross-check benchmark methods on real market histories. Do not present synthetic returns as market prices.
4. Set up GitHub repo and deploy *synthetic-only* `docs/index.html` to GitHub Pages; verify live URL and mobile interactions. Never publish own positions or user CSV in docs.
5. Only later add persistent governance and optional secure AI draft integration with human approval.

## Non-negotiable acceptance gates
- All Python tests pass; Playwright browser smoke passes where available.
- Default stress remains -13.045% under current documented baseline; do not alter to match the past résumé 12.5% claim.
- Scenario edits **only** update scenario outputs, label state MODIFIED, and export UNAPPROVED.
- No browser errors, no responsive horizontal overflow at 390 px, no external CDNs/analytics in offline HTML.
- Model methodology, source provenance, hypothetical notional and explicit limitations remain readable.
- Do not claim enterprise sign-off, true AI generated static commentary, real trading signals or live production deployment.

## Prompt for Codex
"Inspect `PRE_CODEX_AUDIT.md`, `CODEX_HANDOFF.md`, `DESIGN_SYSTEM.md`, then run existing tests. Continue the current V7 project; do not rewrite working components. Prioritize Streamlit runtime E2E verification and parity with the modern ATLAS static demo. Use test-first fixes and report precise evidence; preserve synthetic/market-source disclaimers and review gates."
