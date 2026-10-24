"""Supplementary *descriptive* checks, distinct from eight hard input controls.

A missing business day is NOT necessarily a missing trading day (holidays exist).
The report is for analyst investigation, not an exchange-calendar validation.
"""
from datetime import date
import numpy as np
import pandas as pd
from risk_engine import ASSETS, validate_prices, DEFAULT_WEIGHTS


def data_quality_diagnostics(prices: pd.DataFrame, source: str,
                             *, as_of: date | None = None) -> dict:
    checks=validate_prices(prices, DEFAULT_WEIGHTS)
    if not all(checks.values()):
        raise ValueError('Cannot report data quality on structurally invalid prices')
    dates=prices.index
    rets=prices[ASSETS].pct_change().iloc[1:]
    # A heuristic only: weekdays need not be trading days, especially holidays.
    business_gaps=[]
    for prev,nxt in zip(dates[:-1],dates[1:]):
        gap=max(0,len(pd.bdate_range(prev,nxt))-2)
        if gap>=4:
            business_gaps.append({'from':prev.date().isoformat(),'to':nxt.date().isoformat(),
                                  'missing_weekdays':gap})
    if as_of is None:
        as_of=pd.Timestamp.now(tz='America/New_York').date()
    days_since=(as_of-dates[-1].date()).days
    flags=[]
    if days_since>10:
        flags.append('Snapshot is more than ten calendar days old; not a current risk estimate')
    if business_gaps:
        flags.append(f'{len(business_gaps)} large weekday gaps; inspect trading calendars and source history')
    if 'synthetic' in source.lower():
        flags.append('Synthetic observations cannot validate live risk forecast performance')
    else:
        flags.append('Provider coverage, corporate actions and quote licensing not independently verified')
    return {
        'records':len(prices),
        'assets':len(ASSETS),
        'first_date':dates[0].date().isoformat(),
        'last_date':dates[-1].date().isoformat(),
        'days_since_last_observation':days_since,
        'large_weekday_gap_count':len(business_gaps),
        'large_weekday_gaps':business_gaps[:5],
        'largest_absolute_daily_asset_return':float(rets.abs().max().max()),
        'input_controls_passed':int(sum(checks.values())),
        'input_controls_total':len(checks),
        'review_flags':flags,
    }
