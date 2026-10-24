"""Transparent, daily-frequency portfolio-risk calculations.

For educational analysis, not trading or investment advice.
"""

from dataclasses import dataclass
from math import erfc, log, sqrt
import numpy as np
import pandas as pd


ASSET_CLASS = {
    "US Equity": "Equity",
    "Global Equity": "Equity",
    "Treasuries": "Fixed Income",
    "Corp Bonds": "Fixed Income",
    "Gold": "Commodity",
    "REITs": "Real Estate",
    "Cash": "Cash",
}
ASSETS = list(ASSET_CLASS)
DEFAULT_WEIGHTS = pd.Series([0.26, 0.16, 0.20, 0.13, 0.10, 0.10, 0.05], index=ASSETS)
SCENARIOS = {
    "Equity selloff": {"Equity": -0.30, "Fixed Income": 0.035, "Commodity": 0.06, "Real Estate": -0.22, "Cash": 0.0},
    "Rates shock": {"Equity": -0.11, "Fixed Income": -0.09, "Commodity": 0.03, "Real Estate": -0.17, "Cash": 0.0},
    "Inflation shock": {"Equity": -0.14, "Fixed Income": -0.08, "Commodity": 0.16, "Real Estate": -0.11, "Cash": 0.0},
}


@dataclass
class RiskResult:
    var: float
    es: float
    annualized_vol: float
    max_drawdown: float
    returns: pd.Series


@dataclass
class CoverageResult:
    observations: int
    breaches: int
    expected_breaches: float
    observed_rate: float
    expected_rate: float
    likelihood_ratio: float
    p_value: float


def generate_synthetic_prices(n_days: int = 900, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic correlated returns with a deterministic seed."""
    if n_days < 300:
        raise ValueError("Generate at least 300 observations")
    rng = np.random.default_rng(seed)
    common = rng.normal(size=(n_days - 1, 3))
    noise = rng.normal(size=(n_days - 1, 7))
    loadings = np.array([
        [.010, -.001, .000], [.009, .002, .000], [-.001, .000, .003],
        [.002, .003, .002], [.001, .007, .000], [.007, .003, .001], [.000, .000, .000],
    ])
    idio = np.array([.008, .009, .003, .004, .010, .009, .00005])
    mu = np.array([.00032, .00027, .00012, .00017, .00015, .00025, .00007])
    daily = common @ loadings.T + noise * idio + mu
    daily = np.maximum(daily, -.95)
    prices = np.vstack([np.full(7, 100.0), 100 * np.cumprod(1 + daily, axis=0)])
    dates = pd.bdate_range(end=pd.Timestamp('2026-10-21'), periods=n_days)
    return pd.DataFrame(prices, index=dates, columns=ASSETS)


def validate_prices(prices: pd.DataFrame, weights: pd.Series, min_history: int = 252) -> dict[str, bool]:
    """Eight explicit, independent checks; callers can surface all failures."""
    values = prices.to_numpy() if not prices.empty else np.array([])
    numeric = prices.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float) if values.size else np.array([])
    finite_numeric = bool(numeric.size and np.isfinite(numeric).all())
    native_numeric = all(pd.api.types.is_numeric_dtype(t) and not pd.api.types.is_bool_dtype(t) for t in prices.dtypes)
    # Duplicate labels make column/weight selection ambiguous and may cause
    # pandas to return more than seven assets or raise during reindexing.
    unique_weight_labels = isinstance(weights, pd.Series) and weights.index.is_unique
    aligned = weights.reindex(ASSETS) if unique_weight_labels else pd.Series(np.nan, index=ASSETS)
    w = pd.to_numeric(aligned, errors="coerce").to_numpy(dtype=float)
    good_dates = (isinstance(prices.index, pd.DatetimeIndex)
                  and not prices.index.hasnans
                  and prices.index.is_monotonic_increasing
                  and (prices.index == prices.index.normalize()).all())
    return {
        "1. Dates sorted ascending": bool(good_dates),
        "2. Dates unique": bool(prices.index.is_unique),
        "3. Required assets present": bool(prices.columns.is_unique and set(ASSETS).issubset(prices.columns)),
        "4. Prices numeric and finite": bool(native_numeric and finite_numeric),
        "5. No missing price values": bool(not prices.isna().any().any()),
        "6. Prices strictly positive": bool(finite_numeric and (numeric > 0).all()),
        "7. Sufficient history for rolling test": len(prices) >= min_history + 1,
        "8. Long-only weights sum to 100%": bool(np.isfinite(w).all() and (w >= 0).all() and np.isclose(w.sum(), 1.0, atol=1e-8)),
    }


def portfolio_returns(prices: pd.DataFrame, weights: pd.Series) -> pd.Series:
    checks = validate_prices(prices, weights)
    if not all(checks.values()):
        raise ValueError("Input validation failed: " + "; ".join(k for k, ok in checks.items() if not ok))
    daily = prices[ASSETS].pct_change().dropna()
    # Constant-weight, daily-rebalanced portfolio for transparency.
    result = (daily @ weights.reindex(ASSETS)).rename("Portfolio return")
    if not np.isfinite(result.to_numpy(dtype=float)).all():
        raise ValueError("Price changes produce non-finite portfolio returns")
    return result


def historical_var_es(returns: pd.Series, confidence: float = .95) -> tuple[float, float]:
    if not 0 < confidence < 1:
        raise ValueError("Confidence must lie strictly between 0 and 1")
    clean = pd.to_numeric(returns.dropna(), errors="raise").astype(float)
    if clean.empty:
        raise ValueError("No returns")
    if not np.isfinite(clean.to_numpy()).all():
        raise ValueError("Returns must be finite")
    if (clean <= -1.0).any():
        raise ValueError("A daily portfolio return cannot be below or equal to -100%")
    cutoff = float(np.quantile(clean, 1 - confidence))
    tail = clean[clean <= cutoff]
    return max(0.0, -cutoff), max(0.0, -float(tail.mean()))


def summarize_risk(returns: pd.Series, confidence: float = .95) -> RiskResult:
    var, es = historical_var_es(returns, confidence)
    wealth = (1 + returns).cumprod()
    # The initial $1 of capital is a legitimate high-water mark.
    high_water = wealth.cummax().clip(lower=1.0)
    drawdown = wealth / high_water - 1
    return RiskResult(var, es, float(returns.std(ddof=1) * np.sqrt(252)), float(drawdown.min()), returns)


def rolling_var_backtest(returns: pd.Series, window: int = 250, confidence: float = .95) -> pd.DataFrame:
    """Out-of-sample test: day t forecast uses only days t-window ... t-1."""
    if not isinstance(returns, pd.Series) or not isinstance(returns.index, pd.DatetimeIndex):
        raise ValueError("Backtest requires a datetime-indexed pandas Series")
    if returns.index.hasnans or not returns.index.is_unique or not returns.index.is_monotonic_increasing:
        raise ValueError("Backtest dates must be unique, present and chronological")
    if not isinstance(window, int) or isinstance(window, bool) or window < 30:
        raise ValueError("Backtest window must be an integer of at least 30")
    if not 0 < confidence < 1:
        raise ValueError("Confidence must lie strictly between 0 and 1")
    if len(returns) <= window:
        raise ValueError("Insufficient observations for backtest")
    observed = pd.to_numeric(returns, errors="raise").astype(float)
    if not np.isfinite(observed.to_numpy()).all() or (observed <= -1).any():
        raise ValueError("Backtest returns must be finite and greater than -100%")
    forecasts = []
    for i in range(window, len(observed)):
        var, _ = historical_var_es(observed.iloc[i-window:i], confidence)
        actual_loss = -float(observed.iloc[i])
        forecasts.append((observed.index[i], var, actual_loss, actual_loss > var))
    return pd.DataFrame(forecasts, columns=["Date", "VaR forecast", "Actual loss", "Breach"]).set_index("Date")


def kupiec_unconditional_coverage(backtest: pd.DataFrame, confidence: float = .95) -> CoverageResult:
    """Kupiec LRuc; two-sided χ²(1) asymptotic p-value.

    Tests the *frequency* of VaR exceptions, not their independence or severity.
    Low expected exception counts make the asymptotic approximation unreliable.
    """
    if not 0 < confidence < 1:
        raise ValueError("Confidence must lie strictly between 0 and 1")
    if "Breach" not in backtest.columns or backtest.empty:
        raise ValueError("Backtest must have a nonempty Breach column")
    if backtest["Breach"].isna().any():
        raise ValueError("Backtest breach flags must not be missing")
    observed_flags = backtest["Breach"]
    if not observed_flags.isin([True, False]).all():
        raise ValueError("Backtest breach flags must be boolean")

    n = len(backtest)
    x = int(observed_flags.sum())
    p0 = 1.0 - confidence
    phat = x / n
    log_null = (n - x) * log(1 - p0) + x * log(p0)
    # Convention: 0 * log(0) = 0, including all/no exceptions.
    log_alternative = (
        (n - x) * log(1 - phat) if x < n else 0.0
    ) + (
        x * log(phat) if x > 0 else 0.0
    )
    lr = max(0.0, 2 * (log_alternative - log_null))
    return CoverageResult(
        n, x, n * p0, phat, p0, lr,
        erfc(sqrt(lr / 2)),
    )


def scenario_impact(weights: pd.Series, scenario: str) -> tuple[float, pd.Series]:
    if scenario not in SCENARIOS:
        raise KeyError(scenario)
    shocks = pd.Series({a: SCENARIOS[scenario][ASSET_CLASS[a]] for a in ASSETS})
    contributions = weights.reindex(ASSETS) * shocks
    return float(contributions.sum()), contributions


def component_volatility(prices: pd.DataFrame, weights: pd.Series) -> pd.Series:
    r = prices[ASSETS].pct_change().dropna()
    cov = r.cov().to_numpy()
    w = weights.reindex(ASSETS).to_numpy()
    total = np.sqrt(w @ cov @ w)
    if total <= 0:
        return pd.Series(0.0, index=ASSETS)
    return pd.Series(w * (cov @ w) / total * np.sqrt(252), index=ASSETS)
