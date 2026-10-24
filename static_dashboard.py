"""Generate a shareable, fully offline HTML research dashboard.

This is a snapshot of one analysis. Scenario controls change ONLY linear scenario P&L
inside the browser; stored risk estimates, evidence, and approvals are never mutated.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
import pandas as pd
from plotly.offline.offline import get_plotlyjs

from briefing_workflow import evidence_pack, rules_based_draft
from model_benchmark import compare_var_models
from factor_engine import factor_attribution
from research_packet import generate_packet
from data_quality import data_quality_diagnostics
from risk_engine import (
    ASSETS, ASSET_CLASS, SCENARIOS, DEFAULT_WEIGHTS, component_volatility,
    kupiec_unconditional_coverage, portfolio_returns, rolling_var_backtest,
    summarize_risk,
)


CLASS_ORDER = list(dict.fromkeys(ASSET_CLASS.values()))


def dashboard_payload(prices: pd.DataFrame, weights: pd.Series = DEFAULT_WEIGHTS, *,
                      source_label: str = "Synthetic demo — NOT market observations",
                      confidence: float = .95, window: int = 250,
                      notional: float = 1_000_000,
                      scenario: str = "Equity selloff") -> dict:
    if scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    packet = generate_packet(
        prices, weights, confidence=confidence, window=window, notional=notional,
        scenario_label=scenario, class_shocks=SCENARIOS[scenario], source_label=source_label,
    )
    rets = portfolio_returns(prices, weights)
    risk = summarize_risk(rets, confidence)
    backtest = rolling_var_backtest(rets, window, confidence)
    coverage = kupiec_unconditional_coverage(backtest, confidence)
    benchmark = compare_var_models(rets, window=window, confidence=confidence)
    factors = factor_attribution(prices, weights)
    stressed = packet["scenario"]["portfolio_return"]
    evidence = evidence_pack(
        risk, coverage, factors, weights, scenario, stressed, notional, confidence,
        source_label, packet["source"]["first_date"], packet["source"]["last_date"],
        window, input_digest=packet["input_sha256"],
    )
    growth = (1 + rets).cumprod()
    drawdown_series = growth / growth.cummax().clip(lower=1.0) - 1.0
    aligned_daily = prices[ASSETS].pct_change().dropna()
    correlation = aligned_daily.corr()
    contribution = component_volatility(prices, weights)
    payload = {
        "schema": "portfolio-risk-public-demo-v3",
        "source": source_label,
        "synthetic": "synthetic" in source_label.lower(),
        "period": [packet["source"]["first_date"], packet["source"]["last_date"]],
        "inputs": {"notional": notional, "confidence": confidence, "window": window,
                   "scenario": scenario, "weights": {a: float(weights[a]) for a in ASSETS},
                   "asset_class": ASSET_CLASS.copy(), "classes": CLASS_ORDER,
                   "shocks": {k: float(v) for k, v in SCENARIOS[scenario].items()},
                   "saved_input_sha256": packet["input_sha256"]},
        "kpis": {"var": risk.var, "es": risk.es, "volatility": risk.annualized_vol,
                 "drawdown": risk.max_drawdown, "stress": stressed,
                 "breaches": coverage.breaches, "expected_breaches": coverage.expected_breaches,
                 "backtest_observations": coverage.observations,
                 "kupiec_p": coverage.p_value, "christoffersen_p": packet["backtest"]["christoffersen_p_approx"],
                 "conditional_p": packet["backtest"]["conditional_coverage_p_approx"],
                 "factor_r2": factors.r_squared},
        "growth": {"dates": growth.index.strftime('%Y-%m-%d').tolist(), "values": growth.tolist()},
        "drawdown": {"dates": drawdown_series.index.strftime('%Y-%m-%d').tolist(),
                     "values": drawdown_series.tolist()},
        "correlations": {"assets": ASSETS,
                         "values": correlation.to_numpy(dtype=float).round(10).tolist()},
        "scenario_presets": {name: {k: float(v) for k,v in shocks.items()}
                             for name, shocks in SCENARIOS.items()},
        "asset_vol": {a: float(contribution[a]) for a in ASSETS},
        "factors": {"beta": {k: float(v) for k,v in factors.betas.items()},
                    "variance": {k: float(v) for k,v in factors.fitted_variance_contributions.items()},
                    "r2": factors.r_squared, "condition": factors.condition_number},
        "benchmark": {
            "methodology": benchmark["methodology"],
            "models": benchmark["models"],
            "dates": benchmark["backtest"].index.strftime('%Y-%m-%d').tolist(),
            "historical": benchmark["backtest"]["Historical VaR"].tolist(),
            "gaussian": benchmark["backtest"]["Gaussian VaR"].tolist(),
            "realized": benchmark["backtest"]["Actual loss"].tolist(),
        },
        "backtest": {"dates": backtest.index.strftime('%Y-%m-%d').tolist(),
                     "actual": backtest["Actual loss"].tolist(),
                     "forecast": backtest["VaR forecast"].tolist(),
                     "breaches": backtest["Breach"].astype(bool).tolist()},
        "review": {"status": "UNAPPROVED_DRAFT", "draft": rules_based_draft(evidence),
                   "evidence": evidence["observations"]},
        "quality": packet["data_quality"],
        "limits": packet["limitations"],
    }
    if payload['synthetic']:
        # An archived synthetic snapshot must not change when the wall clock rolls.
        assessment_date = prices.index[-1].date()
        payload['quality'] = data_quality_diagnostics(prices, source_label, as_of=assessment_date)
        payload['quality']['assessment_as_of'] = assessment_date.isoformat()
        payload['quality']['synthetic_snapshot_assessment'] = True
    # Fail rather than emit a silent JavaScript NaN that disguises a broken analysis.
    json.dumps(payload, allow_nan=False)
    return payload


def render_html(payload: dict) -> str:
    """Embed Plotly locally; no CDNs, hosted APIs, tracking or credentials."""
    template = Path(__file__).parent / "templates" / "offline_dashboard.html"
    body = template.read_text(encoding="utf-8")
    # prevent literal closing script tags from arbitrary uploaded metadata
    safe_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    safe_json = safe_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    base_js = (Path(__file__).parent / "assets" / "v5_app.js").read_text(encoding="utf-8")
    v6_js = (Path(__file__).parent / "assets" / "v6_app.js").read_text(encoding="utf-8")
    return (body.replace("/*__EMBED_PLOTLY__*/", get_plotlyjs())
            .replace("/*__EMBED_DATA__*/", "const DATA = " + safe_json + ";")
            .replace("/*__APP_SCRIPT__*/", base_js)
            .replace("/*__V6_SCRIPT__*/", v6_js))


def write_dashboard(prices: pd.DataFrame, output: str | Path, **kwargs) -> dict:
    payload = dashboard_payload(prices, **kwargs)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_html(payload), encoding="utf-8")
    return payload
