# ATLAS V7.1 RC2 verification

## Confirmed local release gate

The exact final corrected synthetic HTML SHA-256 is
`8ea773df1ef3a98bc3d00dff13cb5b5399bd9f9c0a4ba4cf96d480497947edca`.
The saved owner-run normal-Mac-Terminal log contains this hash and confirms:

- PASSED: 134 Python tests and offline synthetic preflight.
- PASSED: V6 and V7 real Chromium suites, including charts, navigation, scenarios, diagnostics and downloads.
- PASSED: all five modules at 1440, 1024, 768 and 390px; chart surfaces/KPI text fit; no horizontal page overflow or global overflow masking.
- PASSED: full Streamlit browser E2E, explicit acknowledgment, approval hashes/revocation, exports, input failures, mobile and JavaScript checks.
- PASSED: two fresh pinned builds match the approved artifact; synthetic-only public artifact audit; frozen model/payload and export-code comparison.

Earlier RC2 horizontal-overflow failures and Codex-sandbox Chromium launch blocks are historical, superseded for local release gating by the exact final artifact's successful permitted-Terminal run. They were never recorded as passes before that run.

## Publication verification boundary

The owner authorized main /docs publication at the existing public repository/Pages URL. The README and release-status documentation were updated after local validation; application code and approved HTML were preserved byte-for-byte. Remote CI and hosted HTML/browser checks must be observed after the publication commit. Their current outcomes are available in [GitHub Actions](https://github.com/emmascq-ship-it/atlas-portfolio-risk/actions) and the post-publication verification report. A local test pass is not itself proof of a deployed pass.

No market-performance or independent live-data-validation claim is made. Public observations are synthetic; Tiingo remains optional/PENDING without suitable free access. No Streamlit hosting, paid services, external AI or authenticated governance platform is provided. All static exports remain unapproved.
