"""Evidence-linked, explicitly analyst-approved briefing artifacts.

Optional external AI generation is user-triggered; no AI is called by default.
Approval never happens automatically. No market or portfolio raw series sent to AI.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re

import pandas as pd

from factor_engine import FactorResult
from risk_engine import CoverageResult, RiskResult

EVIDENCE_IDS = ("E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11")
CITATION_PATTERN = re.compile(r"\[(E\d{2})\]")


def evidence_pack(
    risk: RiskResult, coverage: CoverageResult, factor: FactorResult,
    weights: pd.Series, scenario: str, scenario_return: float, portfolio_value: float,
    confidence: float, data_source: str, first_date: str, last_date: str, window: int,
    input_digest: str | None = None,
) -> dict:
    """Curated, rounded, fixed-key evidence; no holdings or raw time series leaked."""
    if not 0 < confidence < 1 or portfolio_value <= 0:
        raise ValueError("Invalid briefing assumptions")
    values = {
        "E01": f"Source: {data_source}; completed sessions {first_date} through {last_date}.",
        "E02": f"Daily-rebalanced long-only portfolio, 1-day historical simulation at {confidence:.1%} confidence; ${portfolio_value:,.0f} hypothetical notional.",
        "E03": f"1-day historical VaR {risk.var:.2%}, equivalent to ${risk.var * portfolio_value:,.0f} hypothetical loss magnitude.",
        "E04": f"1-day Expected Shortfall {risk.es:.2%}, equivalent to ${risk.es * portfolio_value:,.0f} hypothetical loss magnitude.",
        "E05": f"Annualized volatility {risk.annualized_vol:.2%}; max historical drawdown {risk.max_drawdown:.2%}.",
        "E06": f"Stress: {scenario}, assumed shock return {scenario_return:+.2%}; hypothetical P&L ${scenario_return * portfolio_value:+,.0f}.",
        "E07": f"{window}-day rolling historical VaR backtest: {coverage.breaches}/{coverage.observations} breaches; expected {coverage.expected_breaches:.1f}; observed {coverage.observed_rate:.2%}.",
        "E08": f"Kupiec unconditional coverage LRuc {coverage.likelihood_ratio:.3f}, asymptotic p-value {coverage.p_value:.3f}; evaluates rate, not independence/severity.",
        "E09": f"OLS ETF-spread factor fit R² {factor.r_squared:.1%}; factor fitted vol {factor.fitted_annualized_vol:.2%}; residual vol {factor.residual_annualized_vol:.2%}.",
        "E10": f"Largest absolute factor beta: {factor.betas.abs().idxmax()} at {factor.betas.loc[factor.betas.abs().idxmax()]:+.3f}; exposures are descriptive ETF-spread proxies.",
        "E11": f"Highest asset weight {weights.idxmax()} at {weights.max():.1%}; ETF proxies, daily rebalancing and historical assumptions limit extrapolation.",
    }
    if tuple(values.keys()) != EVIDENCE_IDS:
        raise AssertionError("Evidence inventory is inconsistent")
    result = {"schema": "portfolio-risk-evidence-v1", "observations": values,
              "methodology": "Historical VaR; sample tail mean ES; OLS ETF-spread proxy factors; out-of-sample rolling backtest; illustrative instantaneous stress assumptions."}
    if input_digest is not None:
        if not re.fullmatch(r"[0-9a-f]{64}", input_digest):
            raise ValueError("Input digest must be SHA-256 hex")
        # Unrounded *full* inputs bind the approval even if displayed values round identically.
        result["unrounded_input_sha256"] = input_digest
    return result


def evidence_digest(evidence: dict) -> str:
    return hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def rules_based_draft(evidence: dict) -> str:
    """Always-available deterministic narrative; explicitly NOT represented as AI."""
    e = evidence["observations"]
    return "\n".join([
        "# Portfolio Risk Brief — draft for analyst review", "",
        "## Scope", f"- {e['E01']} [E01]", f"- {e['E02']} [E02]", "",
        "## Downside and concentration", f"- {e['E03']} [E03]", f"- {e['E04']} [E04]",
        f"- {e['E05']} [E05]", f"- {e['E11']} [E11]", "",
        "## Stress and model diagnostics", f"- {e['E06']} [E06]", f"- {e['E07']} [E07]",
        f"- {e['E08']} [E08]", f"- {e['E09']} [E09]", f"- {e['E10']} [E10]", "",
        "## Analyst judgment required", "- Assess whether the stress assumptions fit the current investment thesis.",
        "- Check whether recent market conditions undermine historical calibration.",
        "- Review whether VaR breaches cluster and whether liquidity risks are understated.", "",
        "*Draft only. No recommendation or investment approval is implied.*",
    ])


def validate_draft_evidence(draft: str, evidence: dict) -> list[str]:
    """Surface unsupported IDs, unreferenced claims and missing core evidence.

    An ID-only check does NOT substantiate prose; a human must review all claims.
    """
    issues = []
    ids = set(CITATION_PATTERN.findall(draft))
    unknown = ids - set(evidence["observations"])
    if unknown:
        issues.append("Unknown evidence references: " + ", ".join(sorted(unknown)))
    if not {"E01", "E03", "E04", "E06", "E07", "E08"}.issubset(ids):
        issues.append("Missing references to the source, VaR, ES, stress, or backtest evidence")
    # Every substantive bullet needs a cited evidence item, or a clear action item.
    for line in draft.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and not CITATION_PATTERN.search(stripped):
            if not any(stripped.lower().startswith("- " + action) for action in (
                "assess", "check", "review", "investigate", "confirm", "discuss"
            )):
                issues.append("Uncited factual bullet: " + stripped[:75])
    return issues


@dataclass(frozen=True)
class ApprovalRecord:
    reviewer: str
    timestamp_utc: str
    draft_sha256: str
    evidence_sha256: str
    status: str = "ANALYST_APPROVED"


def approve_brief(draft: str, evidence: dict, reviewer: str, review_confirmed: bool,
                  now: datetime | None = None) -> ApprovalRecord:
    """Create approval only via explicit reviewer action; never implicit/automatic."""
    if not review_confirmed:
        raise ValueError("Explicit analyst review confirmation is required")
    if not reviewer.strip() or len(reviewer.strip()) < 2:
        raise ValueError("A reviewer name or identifier is required")
    issues = validate_draft_evidence(draft, evidence)
    if issues:
        raise ValueError("Brief citation gate failed: " + "; ".join(issues))
    timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    return ApprovalRecord(reviewer.strip(), timestamp,
                          hashlib.sha256(draft.encode()).hexdigest(), evidence_digest(evidence))


def approval_is_current(record: ApprovalRecord, draft: str, evidence: dict) -> bool:
    return (record.draft_sha256 == hashlib.sha256(draft.encode()).hexdigest()
            and record.evidence_sha256 == evidence_digest(evidence))


def export_review_bundle(draft: str, evidence: dict, record: ApprovalRecord | None) -> bytes:
    if record is not None and not approval_is_current(record, draft, evidence):
        raise ValueError("Approval is stale: draft or evidence changed")
    return json.dumps({"status": record.status if record else "UNAPPROVED_DRAFT",
                       "review": vars(record) if record else None, "evidence": evidence,
                       "draft_markdown": draft}, indent=2, ensure_ascii=False).encode()


def generate_llm_draft(evidence: dict, api_key: str, model: str = "gpt-4.1-mini") -> str:
    """Opt-in OpenAI Responses API; ONLY passes curated evidence, not price histories.

    Caller must present preview and manual approval; no automatic transmission.
    """
    if not api_key or not api_key.strip():
        raise ValueError("A user-provided API key is required")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install optional AI dependency: pip install -r requirements-ai.txt") from exc
    client = OpenAI(api_key=api_key, timeout=25., max_retries=0)
    policy = (
        "You draft institutional-style RISK ANALYST NOTES, not trades. "
        "Only use provided evidence facts. Every factual bullet must end with one or more "
        "matching [E01] evidence markers. Include ALL source, VaR, ES, stress, backtest, "
        "and Kupiec evidence [E01], [E03], [E04], [E06], [E07], [E08]. "
        "Do not invent metrics, links, data providers, or claims of AI verification. "
        "No more than 350 words. Organize Scope, Downside, Stress, Validation, "
        "Limits & questions; analytic questions may be uncited if clearly questions. "
        "Do not call the brief approved. Respond in Markdown only."
    )
    response = client.responses.create(model=model, instructions=policy,
        input=json.dumps(evidence, ensure_ascii=False))
    result = response.output_text.strip()
    if not result:
        raise ValueError("AI provider returned an empty response")
    return result
