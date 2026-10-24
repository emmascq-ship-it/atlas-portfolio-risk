"""Optional, inspectable market-data adapter for a USD ETF proxy portfolio.

Yahoo Finance prices are fetched through yfinance, a third-party research
convenience library.  This adapter does not promise licensed or live quotes.
"""

import numpy as np
import pandas as pd

from risk_engine import ASSETS


# Liquid USD-traded proxies. BIL is a short-term Treasury ETF, not literal cash.
MARKET_TICKERS = {
    "US Equity": "SPY",
    "Global Equity": "VEU",
    "Treasuries": "IEF",
    "Corp Bonds": "LQD",
    "Gold": "GLD",
    "REITs": "VNQ",
    "Cash": "BIL",
}


def adjusted_close_to_prices(downloaded: pd.DataFrame, asof_date=None) -> tuple[pd.DataFrame, dict]:
    """Normalize yfinance's multi-level download shape without filling gaps.

    Only dates with complete prices across all seven ETFs are retained.
    Summarize dropped dates so alignment remains visible to the analyst.
    """
    if downloaded.empty:
        raise ValueError("The market-data provider returned no historical prices")
    if not isinstance(downloaded.columns, pd.MultiIndex):
        raise ValueError("Expected a multi-ticker download with price/ticker columns")

    tickers = list(MARKET_TICKERS.values())
    if "Close" in downloaded.columns.get_level_values(0):
        close = downloaded["Close"].copy()
    elif "Close" in downloaded.columns.get_level_values(1):
        close = downloaded.xs("Close", axis=1, level=1).copy()
    else:
        raise ValueError("Downloaded data have no adjusted Close field")

    if any(t not in close.columns for t in tickers):
        missing = [t for t in tickers if t not in close.columns]
        raise ValueError("Missing ETF histories: " + ", ".join(missing))
    close = close[tickers].apply(pd.to_numeric, errors="coerce")
    close = close.rename(columns={symbol: asset for asset, symbol in MARKET_TICKERS.items()})
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    if close.index.hasnans or (close.index.dayofweek >= 5).any():
        raise ValueError("Invalid or non-trading session dates in market-data response")
    close = close.sort_index()
    if close.index.has_duplicates:
        raise ValueError("Duplicate dates in market-data response")

    raw_dates_received = len(close)
    # Conservative daily risk cut: today's close can still be provisional.
    if asof_date is None:
        asof_date = pd.Timestamp.now(tz="America/New_York").date()
    pending_session = close.index.date >= asof_date
    excluded_sessions = int(pending_session.sum())
    close = close.loc[~pending_session]
    if close.empty:
        raise ValueError("No completed trading sessions are available")

    unavailable = close.isna().any(axis=1)
    rows_before = len(close)
    close = close.loc[~unavailable, ASSETS]
    if not np.isfinite(close.to_numpy()).all() or (close <= 0).any().any():
        raise ValueError("Market prices must be finite and positive")
    if close.empty:
        raise ValueError("No dates have a complete set of ETF prices")
    # Excessive missing-data loss is a source-quality failure, not a silent fill.
    if len(close) / rows_before < .95:
        raise ValueError(
            f"Only {len(close)} of {rows_before} trading dates have complete prices; "
            "check ETF history or select a shorter range"
        )
    details = {
        "source": "Yahoo Finance via yfinance (daily dividend/split adjusted ETF prices)",
        "symbols": MARKET_TICKERS.copy(),
        "rows_received": raw_dates_received,
        "rows_excluded_pending_session": excluded_sessions,
        "rows_dropped_missing": int(unavailable.sum()),
        "dates_dropped_missing": [d.date().isoformat() for d in unavailable.index[unavailable]],
        "rows_used": len(close),
        "first_date": close.index.min().date().isoformat(),
        "last_date": close.index.max().date().isoformat(),
    }
    return close, details


def download_etf_prices(period: str = "5y") -> tuple[pd.DataFrame, dict]:
    """Fetch daily, adjusted historical ETF prices; network is opt-in in UI."""
    if period not in ("3y", "5y", "10y"):
        raise ValueError("Period must be 3y, 5y, or 10y")
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("Install project dependencies to enable market prices") from exc

    # Retain raw close and action fields for inspection, select Adj Close explicitly.
    date_options = (
        {"start": (pd.Timestamp.today().normalize() - pd.DateOffset(years=3)).date().isoformat()}
        if period == "3y" else {"period": period}
    )
    raw = yf.download(
        list(MARKET_TICKERS.values()), **date_options, interval="1d",
        auto_adjust=False, actions=True, keepna=True, group_by="column", threads=False,
        progress=False, multi_level_index=True, timeout=20,
    )
    if raw is None or raw.empty:
        raise ValueError("The market-data provider returned no historical prices")
    for field in ('Adj Close', 'Close', 'Dividends', 'Stock Splits'):
        if field not in raw.columns.get_level_values(0):
            raise ValueError(f"Market response lacks auditable {field} field")
        if set(MARKET_TICKERS.values()) - set(raw[field].columns):
            raise ValueError(f"Market response lacks ETF histories for {field}")
    adjusted = raw['Adj Close'].copy()
    normalized = pd.concat({'Close': adjusted}, axis=1)
    prices, details = adjusted_close_to_prices(normalized)
    if (pd.Timestamp.now(tz='America/New_York').date() - prices.index[-1].date()).days > 7:
        raise ValueError('Market history is over seven calendar days stale; inspect the provider before use')
    audit = audit_provider_adjustments(raw, prices.index)
    details.update(audit)
    details['independent_verification'] = 'NOT VERIFIED against an independent vendor'
    details['corporate_actions'] = [
        {'Date': str(pd.Timestamp(date).date()), 'Ticker': ticker,
         'Dividends': float(raw['Dividends'].at[date, ticker]),
         'Stock Splits': float(raw['Stock Splits'].at[date, ticker])}
        for date in raw.index for ticker in MARKET_TICKERS.values()
        if pd.Timestamp(date).tz_localize(None).normalize() in prices.index
        and (raw['Dividends'].at[date, ticker] != 0 or raw['Stock Splits'].at[date, ticker] != 0)
    ]
    return prices, details


def audit_provider_adjustments(raw, completed_dates):
    """Check Yahoo's own adjustment factors against its dividend/action ledger.

    This is same-provider consistency, never independent price verification.
    Yahoo Close is already split adjusted; do not apply split ratios a second time.
    Split events require an independent audit rather than an inferred correction.
    """
    if len(completed_dates) < 2:
        raise ValueError('Insufficient completed sessions for corporate-action audit')
    frames = {}
    for field in ('Close', 'Adj Close', 'Dividends', 'Stock Splits'):
        frame = raw[field][list(MARKET_TICKERS.values())].copy()
        frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
        frames[field] = frame.loc[completed_dates].apply(pd.to_numeric, errors='raise')
        if not np.isfinite(frames[field].to_numpy()).all():
            raise ValueError(f'Missing/nonfinite {field} in corporate-action audit')
    close, adjusted = frames['Close'], frames['Adj Close']
    dividends, splits = frames['Dividends'], frames['Stock Splits']
    if (close <= 0).any().any() or (adjusted <= 0).any().any() or (dividends < 0).any().any() or (splits < 0).any().any():
        raise ValueError('Invalid prices or corporate actions')
    if (splits > 0).any().any():
        raise ValueError('Split event requires independent corporate-action review; no automatic price correction')
    ratio = adjusted / close
    # Dividend back-adjustment: factor[t-1]/factor[t] = 1-dividend[t]/close[t-1].
    errors = (ratio.shift(1) / ratio - (1 - dividends / close.shift(1))).iloc[1:].abs()
    # Gaps are disclosed; do not infer intervening actions across missing sessions.
    max_error = float(errors.max().max())
    if max_error > 5e-4:
        raise ValueError(f'Provider dividend adjustment mismatch ({max_error * 10000:.3f} bps)')
    return {'provider_adjustment_check': 'PASS (same-provider consistency only)',
            'dividend_events_checked': int((dividends > 0).sum().sum()),
            'split_events_checked': 0,
            'maximum_adjustment_factor_error_bps': max_error * 10000}
