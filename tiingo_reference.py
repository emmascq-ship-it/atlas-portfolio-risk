"""Optional Tiingo Starter EOD reference. Standard library only; no paid endpoints.

No automatic calls, signup, billing, upgrade, retries, disk cache or redistribution.
Caller must explicitly confirm use of their $0 Starter account. A supplied token
cannot be introspected to prove its plan; ATLAS never changes billing settings.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

import numpy as np
import pandas as pd

from market_data import MARKET_TICKERS
from market_integrity import compare_adjusted_prices, compare_corporate_actions, checked_frame


class ReferencePending(RuntimeError):
    """Live independent validation cannot be completed; never means PASS."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Do not forward authorization to another URL.


def fetch_history(ticker, start, end, api_key):
    if ticker not in MARKET_TICKERS.values():
        raise ReferencePending('Only the seven configured ETF references are supported')
    query = urlencode({'startDate':start, 'endDate':end, 'resampleFreq':'daily', 'format':'json'})
    request = Request(f'https://api.tiingo.com/tiingo/daily/{ticker}/prices?{query}',
                      headers={'Authorization':'Token ' + api_key, 'Accept':'application/json'})
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            # Bound memory/bandwidth; never retry or request higher limits.
            body = response.read(8_000_001)
            if len(body) > 8_000_000:
                raise ReferencePending('Free reference response exceeds local size budget')
            return json.loads(body)
    except HTTPError as exc:
        raise ReferencePending(f'Tiingo free access unavailable (HTTP {exc.code}); no upgrade or retry attempted') from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise ReferencePending('Tiingo free reference unavailable or unreadable; no retry attempted') from None


def normalize_history(records, ticker, asof_date):
    if not isinstance(records, list) or not records:
        raise ReferencePending(f'Tiingo free history unavailable for {ticker}')
    frame = pd.DataFrame(records)
    required = {'date','adjClose','close','divCash','splitFactor'}
    if not required.issubset(frame.columns):
        raise ReferencePending(f'Tiingo free response lacks adjusted prices/actions for {ticker}')
    try:
        dates = pd.to_datetime(frame.pop('date'), utc=True, errors='raise').dt.tz_localize(None)
        if dates.isna().any() or not dates.equals(dates.dt.normalize()) or dates.duplicated().any():
            raise ValueError('Invalid dates')
        frame.index = pd.DatetimeIndex(dates)
        frame = frame.sort_index()
        frame = frame.loc[frame.index.date < asof_date]
        values = frame[['adjClose','close','divCash','splitFactor']].apply(pd.to_numeric, errors='raise')
        if (values.empty or not np.isfinite(values.to_numpy()).all() or
                (values[['adjClose','close','splitFactor']] <= 0).any().any() or
                (values['divCash'] < 0).any() or (values.index.dayofweek >= 5).any()):
            raise ValueError('Invalid price/action values')
    except (ValueError, TypeError, OverflowError):
        raise ReferencePending(f'Tiingo reference is malformed or insufficient for {ticker}') from None
    prices = values['adjClose'].rename(ticker)
    actions = pd.DataFrame({'Date':values.index, 'Ticker':ticker,
                           'Dividends':values['divCash'].to_numpy(),
                           'Stock Splits':values['splitFactor'].where(values['splitFactor'] != 1., 0.).to_numpy()})
    actions = actions.loc[(actions['Dividends'] != 0) | (actions['Stock Splits'] != 0)]
    return prices, actions


def validate_tiingo_reference(prices, metadata, api_key='', *, confirm_free_starter=False, fetcher=None):
    """Return PENDING, FAILED or matched-reference status; never changes prices.

    Exactly one request per seven hard-coded ETFs, only after explicit opt-in.
    No secret or raw provider rows are included in the returned summary.
    """
    if not api_key.strip() or not confirm_free_starter:
        return {'status':'PENDING', 'reason':'Optional Tiingo $0 Starter key and explicit free-tier confirmation required'}
    if len(api_key) > 200 or any(c.isspace() for c in api_key):
        return {'status':'PENDING', 'reason':'Invalid Tiingo token format'}
    checked_frame(prices, 'Primary feed')
    start, end = prices.index.min().date().isoformat(), prices.index.max().date().isoformat()
    asof_date = pd.Timestamp.now(tz='America/New_York').date()
    fetcher = fetcher or fetch_history
    adjusted, ledgers = [], []
    try:
        for asset, ticker in MARKET_TICKERS.items():
            series, ledger = normalize_history(fetcher(ticker, start, end, api_key), ticker, asof_date)
            adjusted.append(series.rename(asset)); ledgers.append(ledger)
        reference = pd.concat(adjusted, axis=1)
        if (reference.isna().any().any() or len(reference) < len(prices) or
                not prices.index.isin(reference.index).all()):
            raise ReferencePending('Tiingo free history has insufficient session/asset coverage')
        price_result = compare_adjusted_prices(prices, reference, 'Tiingo Starter EOD')
        primary_actions = pd.DataFrame(metadata.get('corporate_actions', []),
                                      columns=['Date','Ticker','Dividends','Stock Splits'])
        if 'corporate_actions' not in metadata:
            raise ReferencePending('Primary corporate-action ledger unavailable')
        nonempty = [ledger for ledger in ledgers if not ledger.empty]
        reference_actions = (pd.concat(nonempty, ignore_index=True) if nonempty else
                             pd.DataFrame(columns=['Date','Ticker','Dividends','Stock Splits']))
        action_result = compare_corporate_actions(primary_actions, reference_actions,
                                                'Tiingo Starter EOD', start, end)
    except ReferencePending as exc:
        return {'status':'PENDING', 'reason':str(exc)}
    except (TimeoutError, URLError, OSError):
        return {'status':'PENDING', 'reason':'Free reference connection unavailable; no retry attempted'}
    except (ValueError, TypeError, KeyError):
        return {'status':'FAILED', 'reason':'Independent reference mismatch or malformed data; inspect provider conventions and actions privately'}
    return {'status':'REFERENCE_CHECKS_PASSED', 'prices':price_result, 'actions':action_result,
            'scope':'Seven EOD ETF histories only; not a licensing, accuracy or production certification'}
