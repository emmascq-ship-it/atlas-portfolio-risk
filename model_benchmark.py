"""Independent Gaussian benchmark and operational VaR diagnostics.

These tools are descriptive and do not certify regulatory VaR compliance.
Forecasts use ONLY trailing returns, never the realized return being predicted.
"""
from dataclasses import asdict, dataclass
from math import isfinite
from statistics import NormalDist

import numpy as np
import pandas as pd

from risk_engine import historical_var_es, kupiec_unconditional_coverage
from validation_extensions import christoffersen_independence, combined_coverage_test


@dataclass(frozen=True)
class BacktestDiagnostics:
    model: str
    observations: int
    breaches: int
    expected_breaches: float
    observed_breach_rate: float
    kupiec_p_approx: float
    independence_p_approx: float
    conditional_p_approx: float
    max_consecutive_breaches: int
    mean_breach_excess: float
    worst_breach_excess: float
    warnings: tuple[str, ...]


def _check_returns(returns: pd.Series, window: int, confidence: float) -> pd.Series:
    if not isinstance(returns, pd.Series):
        raise ValueError('Returns must be a time-indexed pandas Series')
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise ValueError('Returns must have a DatetimeIndex')
    if not returns.index.is_unique or not returns.index.is_monotonic_increasing:
        raise ValueError('Returns must have unique chronological dates')
    if not isinstance(window, int) or isinstance(window, bool) or window < 30:
        raise ValueError('Window must be an integer of at least 30 sessions')
    if len(returns) <= window:
        raise ValueError('Not enough data for an out-of-sample forecast')
    if not 0 < confidence < 1:
        raise ValueError('Confidence must be strictly between 0 and 1')
    values = pd.to_numeric(returns, errors='coerce').to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= -1.0).any():
        raise ValueError('Returns must be finite and cannot lose 100% or more')
    return pd.Series(values, index=returns.index, name=returns.name)


def rolling_model_comparison(returns: pd.Series, *, window: int = 250,
                             confidence: float = .95) -> pd.DataFrame:
    """One-day rolling out-of-sample Historical vs Gaussian VaR.

    Gaussian forecast uses trailing sample mean and std(ddof=1), without
    volatility scaling or distribution fitting to the predicted day.
    """
    observed = _check_returns(returns, window, confidence)
    z = NormalDist().inv_cdf(confidence)
    data = []
    for i in range(window, len(observed)):
        history = observed.iloc[i-window:i]
        hist_var, _ = historical_var_es(history, confidence)
        gauss_var = max(0., z * float(history.std(ddof=1)) - float(history.mean()))
        loss = -float(observed.iloc[i])
        data.append((observed.index[i], loss, hist_var, gauss_var,
                     loss > hist_var, loss > gauss_var))
    return pd.DataFrame(data, columns=['Date','Actual loss',
                            'Historical VaR','Gaussian VaR',
                            'Historical breach','Gaussian breach']).set_index('Date')


def backtest_diagnostics(backtest: pd.DataFrame, breach_column: str,
                         forecast_column: str, *, confidence: float = .95,
                         model: str) -> BacktestDiagnostics:
    if backtest.empty or breach_column not in backtest or forecast_column not in backtest:
        raise ValueError('Nonempty model forecast and breach columns required')
    if 'Actual loss' not in backtest:
        raise ValueError('Actual loss column is required')
    flags = backtest[breach_column]
    if flags.isna().any() or not all(isinstance(v, (bool, np.bool_)) for v in flags):
        raise ValueError('Breaches must be explicitly true or false')
    forecasts = pd.to_numeric(backtest[forecast_column], errors='coerce').to_numpy(dtype=float)
    losses = pd.to_numeric(backtest['Actual loss'], errors='coerce').to_numpy(dtype=float)
    if not np.isfinite(forecasts).all() or not np.isfinite(losses).all() or (forecasts < 0).any():
        raise ValueError('Forecasts and losses must be finite; VaR must not be negative')
    hits = flags.to_numpy(dtype=bool)
    # Explicitly verify that breach indicators match the archived losses and forecasts.
    if not np.array_equal(hits, losses > forecasts):
        raise ValueError('Breach flags do not reconcile to the risk forecasts')
    counts = backtest[['Actual loss']].copy()
    counts['Breach'] = hits
    uc = kupiec_unconditional_coverage(counts, confidence)
    ind = christoffersen_independence(counts)
    _, cc_p = combined_coverage_test(uc.likelihood_ratio, ind.likelihood_ratio)
    max_run = run = 0
    for hit in hits:
        run = (run + 1) if hit else 0
        max_run = max(max_run, run)
    excess = losses[hits] - forecasts[hits]
    warnings = []
    if uc.expected_breaches < 10:
        warnings.append('Fewer than 10 expected exceptions; chi-square p-values may be fragile')
    if ind.warning:
        warnings.append(ind.warning)
    if np.std(losses, ddof=1) < 1e-12:
        warnings.append('Near-constant realized losses impair backtest interpretation')
    return BacktestDiagnostics(
        model=model, observations=uc.observations, breaches=uc.breaches,
        expected_breaches=uc.expected_breaches, observed_breach_rate=uc.observed_rate,
        kupiec_p_approx=uc.p_value, independence_p_approx=ind.p_value,
        conditional_p_approx=cc_p, max_consecutive_breaches=max_run,
        mean_breach_excess=float(excess.mean()) if len(excess) else 0.,
        worst_breach_excess=float(excess.max()) if len(excess) else 0.,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def compare_var_models(returns: pd.Series, *, window: int = 250,
                       confidence: float = .95) -> dict:
    frame = rolling_model_comparison(returns, window=window, confidence=confidence)
    models = {
        'historical': backtest_diagnostics(frame, 'Historical breach',
                                         'Historical VaR', confidence=confidence,
                                         model='Historical simulation'),
        'gaussian': backtest_diagnostics(frame, 'Gaussian breach',
                                        'Gaussian VaR', confidence=confidence,
                                        model='Gaussian mean / variance'),
    }
    return {
        'methodology': {
            'forecast_horizon': '1 trading session',
            'window': window, 'confidence': confidence,
            'backtest_start_date': frame.index.min().date().isoformat(),
            'backtest_end_date': frame.index.max().date().isoformat(),
            'no_look_ahead': True, 'loss_unit': 'fraction of portfolio value',
            'comparison': 'Historical empirical quantile vs mean-and-standard-deviation Gaussian VaR',
        },
        'models': {k: asdict(v) for k, v in models.items()},
        'backtest': frame,
    }
