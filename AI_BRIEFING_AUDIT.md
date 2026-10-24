# Briefing workflow audit — $0 configuration

The active app uses deterministic offline evidence briefs. It has no external AI
mode, OpenAI key field or Generate AI button, and does not import the remote
adapter. Existing human review, editable drafts, evidence IDs and approval hashes
remain. No paid AI requests are permitted. No new AI framework was introduced.

## Implemented controls

- Risk, factor, scenario and backtest calculations run deterministically in Python
  before prose is assembled. Default text inserts eleven calculated observations.
- Fixed evidence IDs, methodology and the unrounded full-input SHA-256 bind the
  rendered evidence to analysis. Citation gates block unknown/missing required
  IDs and non-action bullets without citations.
- Exact draft/evidence hashes bind sign-off. Draft/input changes invalidate it;
  stale approved bundles are rejected. A reviewer identifier, attestation and
  explicit button press are required. Research packets stay UNAPPROVED regardless
  of separately exported in-session analyst review approval.

## Claims not implemented

- Citation IDs do not establish factual truth or entailment. Fabricated claims
  with existing IDs can pass; a regression demonstrates this boundary. No semantic
  fact checker, authenticated analyst identity, digital signature, reviewer
  separation, durable audit database or enterprise authorization is implemented.
- Approval timestamps are time dependent. Determinism applies to calculations and
  rule-based prose, not timestamps or historical external model wording.
- Static commentary is not AI-generated; no actual AI model performance was tested.

## Historical remote adapter audit

briefing_workflow.generate_llm_draft remains unchanged to preserve tested code,
with no path to it in the active app. requirements-ai.txt is a marked legacy file;
it is not part of the free runtime/CI installation. Do not install/use it as part
of this $0 project. The temporary optional SDK compatibility check occurred before
the $0 clarification and made no API calls or charges; it is not in active CI.

The legacy adapter would send eleven curated observations, methodology and input
digest, including notional, largest asset weight, metrics, scenario and source/date
labels. “No portfolio information is transmitted” would be false. It sends no raw
price history/full holdings table. Its 350-word limit and no-invention policy are
prompts, not semantic enforcement. External output is nondeterministic and was
never validated live. No production secrets vault/key-management guarantee exists.

## Tests

Mocked tests cover payload boundaries, empty response, refusal, timeout and gate
limitations without keys or network. Streamlit runtime tests assert that active
$0 mode exposes no remote generation control and never calls the historical
adapter. Existing tests preserve full-input binding, stale approval rejection and
draft/input revocation. The complete automated browser gate is still pending a
permitted Chromium runner; configured coverage is not a passing run.
