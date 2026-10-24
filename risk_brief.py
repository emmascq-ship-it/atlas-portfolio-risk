"""Auditable portfolio-risk review narrative. No generative model is used."""

import pandas as pd

from risk_engine import CoverageResult, RiskResult


def make_risk_brief(
    risk: RiskResult,
    coverage: CoverageResult,
    weights: pd.Series,
    volatility_contributions: pd.Series,
    scenario_name: str,
    scenario_return: float,
    portfolio_value: float,
    confidence: float,
    source_label: str,
    history_start: str,
    history_end: str,
    backtest_window: int,
) -> str:
    """Summarize verified outputs, inputs, and limitations in reviewable prose."""
    if portfolio_value <= 0:
        raise ValueError("Portfolio value must be positive")
    max_contributor = volatility_contributions.idxmax()
    top_weight = weights.idxmax()
    coverage_assessment = (
        "The observed exception frequency differs significantly from the target "
        "under Kupiec's approximate 5% significance test."
        if coverage.p_value < .05 else
        "The test does not reject nominal unconditional coverage at the 5% level; "
        "this does not establish model validity."
    )
    if coverage.expected_breaches < 10:
        coverage_assessment += " **Caution:** fewer than 10 expected breaches make the asymptotic p-value less dependable."
    return "\n".join([
        "# Portfolio Risk Review",
        "",
        f"**Data:** {source_label} | {history_start} to {history_end}",
        f"**Model:** constant-weight daily rebalancing | {confidence:.1%} 1-day historical VaR | "
        f"{backtest_window}-observation rolling forecast window",
        f"**Illustrative portfolio notional:** ${portfolio_value:,.0f} USD",
        "",
        "## Exposure and downside",
        f"- Largest allocation: **{top_weight}** ({weights[top_weight]:.1%}); largest positive "
        f"volatility contributor: **{max_contributor}** "
        f"({volatility_contributions[max_contributor]:.2%} annualized volatility points).",
        f"- Historical 1-day VaR: **{risk.var:.2%}** "
        f"(~${risk.var * portfolio_value:,.0f} of notional); Expected Shortfall: "
        f"**{risk.es:.2%}** (~${risk.es * portfolio_value:,.0f}). "
        "These are model-based loss magnitudes, not guaranteed bounds.",
        f"- Annualized volatility: **{risk.annualized_vol:.2%}**; "
        f"maximum historical drawdown: **{risk.max_drawdown:.2%}**.",
        "",
        "## Scenario and validation",
        f"- Under the **illustrative {scenario_name}** shock, estimated portfolio return "
        f"is **{scenario_return:+.2%}** "
        f"(~${scenario_return * portfolio_value:+,.0f} of notional). "
        "This is a deterministic assumption, not an empirical forecast.",
        f"- VaR backtest: **{coverage.breaches}/{coverage.observations}** exceptions "
        f"({coverage.observed_rate:.2%} observed vs. {coverage.expected_rate:.2%} target); "
        f"Kupiec LRuc **{coverage.likelihood_ratio:.3f}**, "
        f"approximate p-value **{coverage.p_value:.3f}**. {coverage_assessment}",
        "",
        "## Review limitations",
        "- This analysis assumes fixed long-only weights rebalanced daily; it excludes "
        "trading costs, liquidity, portfolio drift, and model estimation uncertainty.",
        "- Kupiec tests breach frequency only, not clustering or loss severity. "
        "Historical data and proxy ETFs may not represent future risk.",
        "- Educational analytical output only; not investment advice or a trade recommendation.",
        "",
    ])
