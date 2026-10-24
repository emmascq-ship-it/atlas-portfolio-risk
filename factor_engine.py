"""Transparent OLS attribution against investable ETF-spread *proxy* factors.

This is a descriptive return-factor regression, not a causal factor model,
forward-looking risk forecast, or academically calibrated market/style model.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from risk_engine import ASSETS, portfolio_returns

FACTOR_DESCRIPTIONS = {
    "Equity market": "US equity minus short Treasury-bill proxy (SPY - BIL)",
    "Treasury duration": "Intermediate Treasury minus T-bill proxy (IEF - BIL)",
    "Credit spread": "Investment-grade corporate bond minus Treasury proxy (LQD - IEF)",
    "Gold / commodity": "Gold ETF minus T-bill proxy (GLD - BIL)",
    "Real estate relative": "REIT ETF minus US equity proxy (VNQ - SPY)",
}


@dataclass(frozen=True)
class FactorResult:
    factor_returns: pd.DataFrame
    betas: pd.Series
    intercept_daily: float
    r_squared: float
    fitted_returns: pd.Series
    residual_returns: pd.Series
    # Annualized contributions to *fitted factor variance*, not total portfolio variance.
    fitted_variance_contributions: pd.Series
    fitted_annualized_vol: float
    residual_annualized_vol: float
    condition_number: float
    observations: int


def build_factor_proxies(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily arithmetic ETF spread returns constructed from the same price source."""
    if not set(ASSETS).issubset(prices.columns):
        raise ValueError("Seven required price histories are needed for factor proxies")
    r = prices[ASSETS].pct_change().iloc[1:]
    if r.empty or not np.isfinite(r.to_numpy(dtype=float)).all():
        raise ValueError("Incomplete or nonfinite daily ETF returns")
    result = pd.DataFrame(index=r.index)
    result["Equity market"] = r["US Equity"] - r["Cash"]
    result["Treasury duration"] = r["Treasuries"] - r["Cash"]
    result["Credit spread"] = r["Corp Bonds"] - r["Treasuries"]
    result["Gold / commodity"] = r["Gold"] - r["Cash"]
    result["Real estate relative"] = r["REITs"] - r["US Equity"]
    return result


def factor_attribution(prices: pd.DataFrame, weights: pd.Series, min_observations: int = 260) -> FactorResult:
    """OLS with intercept, fitted-factor variance attribution, and diagnostics.

    All five factors use returns from the *same* source and trading dates.
    Factor contributions can be negative and sum to annualized fitted variance;
    this is different from contributions to annualized portfolio volatility.
    """
    y = portfolio_returns(prices, weights)
    factors = build_factor_proxies(prices)
    if len(y) < min_observations:
        raise ValueError(f"Need at least {min_observations} aligned returns for factor regression")
    if not y.index.equals(factors.index):
        raise ValueError("Portfolio and factor dates are misaligned")
    X = factors.to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(X)), X])
    # Detect multicollinearity instead of publishing unstable coefficients.
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError("Factor regressors are rank deficient")
    cond = float(np.linalg.cond(design))
    if not np.isfinite(cond) or cond > 1e8:
        raise ValueError("Factor regression is ill conditioned")
    parameters, *_ = np.linalg.lstsq(design, y.to_numpy(dtype=float), rcond=None)
    intercept, coefficients = float(parameters[0]), parameters[1:]
    betas = pd.Series(coefficients, index=factors.columns, name="Factor sensitivity (beta)")
    fitted = pd.Series(design @ parameters, index=y.index, name="Fitted daily return")
    residuals = pd.Series(y.to_numpy() - fitted.to_numpy(), index=y.index, name="Residual daily return")
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = (1 - float((residuals ** 2).sum()) / tss) if tss > 0 else float("nan")
    # Euler-like covariance decomposition of fitted *variance*: b_i * Cov(f_i, fitted_factor).
    cov = factors.cov().to_numpy(dtype=float)
    fitted_var_comp = pd.Series(coefficients * (cov @ coefficients) * 252,
                                index=factors.columns, name="Annualized fitted variance contribution")
    fitted_variance = max(0., float(coefficients @ cov @ coefficients))
    return FactorResult(
        factors, betas, intercept, r2, fitted, residuals, fitted_var_comp,
        float(np.sqrt(fitted_variance * 252)), float(residuals.std(ddof=1) * np.sqrt(252)),
        cond, len(y),
    )
