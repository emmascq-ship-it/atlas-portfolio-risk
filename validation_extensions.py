"""Exception-clustering diagnostics and defensible scenario customization.

Christoffersen's independence test is asymptotic and descriptive. Sparse breach
counts undermine calibration; it is not a certificate of VaR model validity.
"""
from dataclasses import dataclass
from math import erfc, exp, isfinite, log, sqrt
from collections.abc import Mapping
import numpy as np
import pandas as pd

from risk_engine import ASSETS, ASSET_CLASS


@dataclass(frozen=True)
class IndependenceResult:
    n00: int
    n01: int
    n10: int
    n11: int
    likelihood_ratio: float
    p_value: float
    transition_rate_after_no_breach: float
    transition_rate_after_breach: float
    # p-values are approximate and not trustworthy with very few breaches.
    warning: str


def _bernoulli_log_likelihood(successes: int, trials: int, p: float) -> float:
    """Handle degenerate p=0/1 with mathematical 0*log(0)=0 convention."""
    if trials < 0 or successes < 0 or successes > trials or not 0 <= p <= 1:
        raise ValueError("Invalid Bernoulli parameters")
    if successes and p == 0:
        return float('-inf')
    if trials > successes and p == 1:
        return float('-inf')
    return ((successes * log(p) if successes else 0.0) +
            ((trials-successes) * log(1-p) if trials > successes else 0.0))


def christoffersen_independence(backtest: pd.DataFrame) -> IndependenceResult:
    """First-order Markov LRind test of breach independence, 1 dof χ² reference.

    Transition n_ij records previous breach=i and next breach=j; first
    exception has no incoming transition. A rare-event warning is mandatory.
    """
    if 'Breach' not in backtest.columns or len(backtest) < 3:
        raise ValueError("At least three breach flags are required")
    values = backtest['Breach']
    if values.isna().any() or not all(isinstance(v, (bool, np.bool_)) for v in values):
        raise ValueError("Breach flags must be nonmissing booleans")
    flags = values.to_numpy(dtype=bool)
    prior, nxt = flags[:-1], flags[1:]
    n00 = int(((~prior) & (~nxt)).sum())
    n01 = int(((~prior) & nxt).sum())
    n10 = int((prior & (~nxt)).sum())
    n11 = int((prior & nxt).sum())
    total = len(flags)-1
    p0 = n01/(n00+n01) if n00+n01 else 0.0
    p1 = n11/(n10+n11) if n10+n11 else 0.0
    pooled = (n01+n11)/total
    null_log = _bernoulli_log_likelihood(n01+n11, total, pooled)
    alt_log = (_bernoulli_log_likelihood(n01, n00+n01, p0) +
               _bernoulli_log_likelihood(n11, n10+n11, p1))
    lr = max(0.0, 2*(alt_log-null_log))
    pvalue = erfc(sqrt(lr/2))
    warnings = []
    if n01+n11 < 10:
        warnings.append('Fewer than ten transition exceptions: asymptotic test may be unreliable')
    if not (n00+n01) or not (n10+n11):
        warnings.append('One previous-state transition group is absent')
    return IndependenceResult(n00,n01,n10,n11,lr,pvalue,p0,p1,'; '.join(warnings))


def combined_coverage_test(unconditional_lr: float, independence_lr: float) -> tuple[float,float]:
    """Conditional coverage LRcc = LRuc + LRind; reference χ² with 2 dof."""
    if not all(isfinite(x) and x >= 0 for x in (unconditional_lr, independence_lr)):
        raise ValueError("LR statistics must be nonnegative and finite")
    lr = unconditional_lr+independence_lr
    return lr, exp(-lr/2)


CLASSES = tuple(dict.fromkeys(ASSET_CLASS.values()))


def scenario_impact_custom(weights: pd.Series, class_shocks: Mapping[str,float]) -> tuple[float,pd.Series]:
    """Transparent one-period linear repricing using user-defined class shocks."""
    if set(class_shocks) != set(CLASSES):
        raise ValueError("A shock for each of the five asset classes is required")
    try:
        values = {c: float(v) for c,v in class_shocks.items()}
    except (ValueError,TypeError) as exc:
        raise ValueError("Scenario shocks must be numbers") from exc
    if any(not isfinite(x) or not -1 <= x <= 2 for x in values.values()):
        raise ValueError("Scenario shock outside plausible UI range [-100%, +200%]")
    aligned = weights.reindex(ASSETS)
    if aligned.isna().any() or not np.isfinite(aligned.to_numpy(dtype=float)).all() or (aligned < 0).any() or not np.isclose(aligned.sum(),1):
        raise ValueError("Long-only weights must total 100%")
    contributions = aligned * pd.Series({asset: values[ASSET_CLASS[asset]] for asset in ASSETS})
    return float(contributions.sum()), contributions
