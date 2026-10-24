# ATLAS V7.1 RC1 — verification record

## Latest complete gate: PASSED (project-owner observed)

The project owner reports that the latest complete release_preflight.py --browser
run **passed in normal Mac Terminal**, after the assertion-timeout correction.
Recorded on 24 October 2026; raw Terminal logs/commit ID were not supplied. These
are owner-observed results, not a newly agent-executed complete browser run.

| Check | Status | Observation source |
|---|---|---|
| Python regressions | PASSED — 134 tests | Owner's full preflight; agent separately ran 134 tests |
| V6 Chromium suite | PASSED | Owner's normal Mac Terminal |
| V7 Chromium suite | PASSED | Owner's normal Mac Terminal |
| Full Streamlit E2E | PASSED — approval, revocation, exports, mobile and JavaScript checks | Owner's normal Mac Terminal |
| Offline synthetic demo generation/preflight | PASSED | Owner's full preflight; agent's offline checks |
| Final public directory audit | PASSED | Agent audit of exact synthetic payload and two-file allowlist |
| Financial/UI freeze | PASSED | RELEASE_FREEZE_SHA256.txt; no application changes in RC packaging |
| Free independent Tiingo comparison | PENDING — optional, not a synthetic-demo blocker | No usable free key configured |
| Hosted demo URL and remote CI | PENDING — not performed or authorized | No repository publishing/deployment |

## Resolved issues and boundaries

The Streamlit native checkbox requires its visible associated label as the pointer
target. Approval state arrives after a server rerun, so browser assertions now
share the test's bounded 60-second action budget instead of the separate 5-second
default. Both fixes retain all genuine-state assertions and safeguards.

No unresolved application failure is reported by the latest complete gate. The
agent sandbox still cannot launch subprocess Chromium (macOS MachPort permission
restriction). This environmental restriction does not supersede the owner's
successful permitted-Terminal result. Earlier reports marked BLOCKED describe
historical agent runs and are superseded for RC readiness by this record.

Synthetic baseline: 900 prices, 899 daily returns, 649 rolling forecasts, 31
Historical/30 Gaussian exceptions at 95% confidence; stress −13.045%. These are
illustrative fixtures, not realized performance or independent model validation.
Reference IDs and hashes prove traceability, not claim truth. No live-market or
production governance certification is implied.

The agent additionally reran the offline preflight during RC packaging: all 134
Python tests, CLI exports, reproducible HTML and public audit passed. No browser
suite was rerun or newly claimed by the agent in this documentation-only phase.

## Release evidence

RELEASE_FREEZE_SHA256.txt records the frozen source/config/demo/test files.
RELEASE_CANDIDATE.md records the public repository audit and staged scope.
Local delivery contains the release inventory and audit output. Historical agent
logs/screenshots remain outside the clean candidate. Retaining the owner's raw
successful preflight log with the eventual commit is recommended for provenance;
its absence does not reverse the explicitly reported pass.
