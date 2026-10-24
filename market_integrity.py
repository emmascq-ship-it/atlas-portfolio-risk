"""Independent reference comparisons; no risk model and no synthetic fallback.

Reference providers must use the same currency, session dates and dividend/split
adjustment convention. Caller supplies licensed reference data and provenance.
"""
import numpy as np
import pandas as pd


def checked_frame(frame, label):
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.hasnans:
        raise ValueError(f'{label}: valid daily dates are required')
    if frame.index.tz is not None or not frame.index.equals(frame.index.normalize()):
        raise ValueError(f'{label}: use timezone-naive daily session dates')
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError(f'{label}: duplicate or unordered sessions')
    if frame.columns.has_duplicates or len(frame) < 2:
        raise ValueError(f'{label}: duplicate columns or insufficient observations')
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError(f'{label}: prices must be finite and positive with no missing observations')


def compare_adjusted_prices(prices, reference, source, tolerance_bps=5.0):
    """Compare daily adjusted returns, allowing a constant vendor rebasing.

    Entire analysis interval and every asset must be covered. This tests supplied
    data, not whether a self-declared reference provider is actually independent.
    """
    if not source.strip() or 'yahoo' in source.lower() or 'yfinance' in source.lower():
        raise ValueError('Name an independent reference source, not Yahoo/yfinance')
    if not np.isfinite(tolerance_bps) or not 0 <= tolerance_bps <= 10:
        raise ValueError('Reference tolerance must be between 0 and 10 basis points')
    checked_frame(prices, 'Primary feed')
    checked_frame(reference, 'Reference')
    if set(prices.columns) != set(reference.columns):
        raise ValueError('Reference asset columns must match the primary feed')
    reference = reference.loc[(reference.index >= prices.index.min()) &
                              (reference.index <= prices.index.max()), prices.columns]
    if not prices.index.equals(reference.index):
        raise ValueError('Reference sessions differ: missing or extra completed observations')
    discrepancies = (prices.pct_change(fill_method=None).iloc[1:] -
                     reference.pct_change(fill_method=None).iloc[1:]).abs() * 10000
    maximum = float(discrepancies.max().max())
    if maximum > tolerance_bps:
        date, asset = discrepancies.stack().idxmax()
        raise ValueError(f'Independent adjusted-return mismatch: {asset} {date.date()} '
                         f'{maximum:.3f} bps exceeds {tolerance_bps:.3f} bps')
    return {'status': 'REFERENCE_RETURNS_MATCH', 'reference_source': source.strip(),
            'sessions': len(prices), 'assets': len(prices.columns),
            'maximum_return_difference_bps': maximum, 'tolerance_bps': tolerance_bps,
            'scope': 'Supplied reference adjusted returns only; corporate actions checked separately'}


def compare_corporate_actions(primary, reference, source, first_date, last_date):
    """Compare complete event ledgers, including events missing from either side.

    Each ledger has Date, Ticker, Dividends and Stock Splits; zero means no event.
    Dividends must be in the same currency and share basis. Empty event sets are
    accepted only as an explicit statement by the reference supplier.
    """
    if not source.strip() or 'yahoo' in source.lower() or 'yfinance' in source.lower():
        raise ValueError('An independent action reference source is required')
    ledgers = []
    keys = ['Date', 'Ticker']
    for label, frame in (('Primary', primary), ('Reference', reference)):
        if set(frame.columns) != set(keys + ['Dividends', 'Stock Splits']):
            raise ValueError(f'{label}: expected Date,Ticker,Dividends,Stock Splits')
        frame = frame.copy()
        frame['Date'] = pd.to_datetime(frame['Date'], errors='raise')
        if frame['Date'].isna().any() or frame.duplicated(keys).any() or frame['Ticker'].isna().any():
            raise ValueError(f'{label}: invalid or duplicate corporate-action records')
        numeric = frame[['Dividends', 'Stock Splits']].apply(pd.to_numeric, errors='raise')
        if not np.isfinite(numeric.to_numpy(dtype=float)).all() or (numeric < 0).any().any():
            raise ValueError(f'{label}: invalid dividend or split values')
        frame[['Dividends', 'Stock Splits']] = numeric
        frame = frame.loc[frame['Date'].between(pd.Timestamp(first_date), pd.Timestamp(last_date))]
        frame = frame.loc[(frame['Dividends'] != 0) | (frame['Stock Splits'] != 0)]
        ledgers.append(frame.set_index(keys)[['Dividends', 'Stock Splits']].sort_index())
    a, b = ledgers
    if not a.index.equals(b.index) or not np.allclose(a.to_numpy(dtype=float), b.to_numpy(dtype=float), rtol=1e-6, atol=1e-6):
        raise ValueError('Independent corporate-action mismatch: event dates, symbols, dividends or split ratios differ')
    return {'status': 'REFERENCE_ACTIONS_MATCH', 'events': len(a), 'reference_source': source.strip()}
