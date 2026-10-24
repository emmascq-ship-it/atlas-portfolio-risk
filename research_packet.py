"""Portable, reproducible analysis exports: no API calls, no invented results."""
import hashlib
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from risk_engine import ASSETS, validate_prices, portfolio_returns, summarize_risk, rolling_var_backtest, kupiec_unconditional_coverage, component_volatility
from factor_engine import factor_attribution
from model_benchmark import compare_var_models
from data_quality import data_quality_diagnostics
from validation_extensions import christoffersen_independence, combined_coverage_test, scenario_impact_custom


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def inputs_fingerprint(prices: pd.DataFrame, weights: pd.Series, confidence: float,
                       window: int, notional: float, scenario_label: str,
                       class_shocks: dict, source_label: str) -> str:
    """Digest covers unrounded prices and *all* user-defined inputs, not just displayed KPIs."""
    header = {
        'schema': 'input-fingerprint-v1', 'confidence': float(confidence),
        'window': int(window), 'notional': float(notional), 'scenario': scenario_label,
        'source': source_label, 'weights': {a: float(weights[a]) for a in ASSETS},
        'class_shocks': {k: float(v) for k,v in sorted(class_shocks.items())},
    }
    h = hashlib.sha256(_canonical_json(header).encode('utf-8'))
    h.update(b'\nPRICES\n')
    # 17 significant digits preserve the underlying float64 input values.
    h.update(prices[ASSETS].to_csv(index_label='Date', float_format='%.17g').encode('utf-8'))
    return h.hexdigest()


def generate_packet(prices: pd.DataFrame, weights: pd.Series, *, confidence: float=.95,
                    window: int=250, notional: float=1_000_000,
                    scenario_label: str='Analyst scenario', class_shocks: dict,
                    source_label: str='Synthetic demo') -> dict:
    checks = validate_prices(prices, weights, min_history=max(window+1, 261))
    if not all(checks.values()):
        raise ValueError('Invalid input: '+ '; '.join(k for k,v in checks.items() if not v))
    if not 0 < confidence < 1 or window < 30 or not np.isfinite(notional) or notional <= 0:
        raise ValueError('Invalid analysis settings')
    daily = portfolio_returns(prices, weights)
    if len(daily) <= window:
        raise ValueError('Insufficient return history')
    risk = summarize_risk(daily, confidence)
    backtest = rolling_var_backtest(daily, window, confidence)
    uc = kupiec_unconditional_coverage(backtest, confidence)
    ind = christoffersen_independence(backtest)
    cc_lr, cc_p = combined_coverage_test(uc.likelihood_ratio, ind.likelihood_ratio)
    fit = factor_attribution(prices, weights)
    benchmark = compare_var_models(daily, window=window, confidence=confidence)
    stress, stress_components = scenario_impact_custom(weights, class_shocks)
    component = component_volatility(prices, weights)
    fingerprint = inputs_fingerprint(prices, weights, confidence, window, notional,
                                     scenario_label, class_shocks, source_label)
    return {
        'schema': 'portfolio-risk-research-packet-v1',
        'approval_status': 'UNAPPROVED_RESEARCH',
        'input_sha256': fingerprint,
        'source': {'label': source_label, 'first_date': prices.index.min().date().isoformat(),
                   'last_date': prices.index.max().date().isoformat(), 'price_rows': len(prices),
                   'return_rows': len(daily), 'adjusted_prices_required': True},
        'assumptions': {'currency': 'USD', 'notional_usd': float(notional),
                        'confidence': float(confidence), 'rolling_window': int(window),
                        'trading_days_per_year': 252, 'rebalancing': 'Daily constant weight',
                        'weights': {k:float(v) for k,v in weights[ASSETS].items()},
                        'stress_label': scenario_label,
                        'stress_class_shocks': {k:float(v) for k,v in sorted(class_shocks.items())}},
        'risk': {'historical_var_1d':risk.var, 'expected_shortfall_1d':risk.es,
                 'annualized_volatility':risk.annualized_vol, 'max_drawdown':risk.max_drawdown,
                 'historical_var_usd':risk.var*notional, 'expected_shortfall_usd':risk.es*notional,
                 'asset_volatility_contribution': {k:float(v) for k,v in component.items()}},
        'scenario': {'portfolio_return':stress, 'estimated_pnl_usd':stress*notional,
                     'contribution_by_asset': {k:float(v) for k,v in stress_components.items()}},
        'backtest': {'observations':uc.observations, 'breaches':uc.breaches,
                     'expected_breaches':uc.expected_breaches, 'kupiec_lr_uc':uc.likelihood_ratio,
                     'kupiec_p_approx':uc.p_value, 'christoffersen_lr_ind':ind.likelihood_ratio,
                     'christoffersen_p_approx':ind.p_value, 'lr_conditional_coverage':cc_lr,
                     'conditional_coverage_p_approx':cc_p,
                     'transition_counts':{'n00':ind.n00,'n01':ind.n01,'n10':ind.n10,'n11':ind.n11},
                     'caveat': ind.warning or 'Asymptotic p-values do not establish model validity'},
        'factors': {'definition':'Descriptive, in-sample ETF return spread proxies',
                    'r_squared':fit.r_squared,
                    'betas':{k:float(v) for k,v in fit.betas.items()},
                    'condition_number':fit.condition_number,
                    'annualized_fitted_vol':fit.fitted_annualized_vol,
                    'annualized_residual_vol':fit.residual_annualized_vol},
        'model_benchmark': {'methodology': benchmark['methodology'],
                            'models': benchmark['models']},
        'data_quality': data_quality_diagnostics(prices, source_label),
        'validation':checks,
        'limitations': [
            'Historical simulation is backward looking and sensitive to regime and sample',
            'Expected shortfall from a finite empirical tail is noisy',
            'Transaction costs, financing, slippage, taxes and intraday risk excluded',
            'Stress shocks are illustrative assumptions, not forecast probabilities',
            'Regressions reuse portfolio ETF proxies and are in-sample, not independently causal',
            'Kupiec and Christoffersen tests have fragile asymptotic inference with sparse breaches',
            'Third-party market data may be delayed, revised, incomplete or usage-restricted',
            'Gaussian comparator assumes normality; agreement between models does not certify tail adequacy',
        ],
    }


def packet_bytes(packet: dict) -> bytes:
    return (json.dumps(packet, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8')
