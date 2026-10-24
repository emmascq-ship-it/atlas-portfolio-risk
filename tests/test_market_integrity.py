"""Fabricated integrity fixtures, not evidence of actual vendor agreement."""
import unittest
import numpy as np
import pandas as pd
from market_data import MARKET_TICKERS, adjusted_close_to_prices, audit_provider_adjustments
from market_integrity import compare_adjusted_prices, compare_corporate_actions

class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.dates = pd.bdate_range('2026-01-05', periods=4)
        self.prices = pd.DataFrame({a:[100.,101.,100.,102.] for a in MARKET_TICKERS}, index=self.dates)
        self.raw = pd.concat({field:pd.DataFrame(value, index=self.dates, columns=list(MARKET_TICKERS.values()))
            for field,value in [('Close',100.),('Adj Close',100.),('Dividends',0.),('Stock Splits',0.)]}, axis=1)

    def test_rebasing_allowed_return_corruption_fails(self):
        self.assertEqual(compare_adjusted_prices(self.prices,self.prices*.9,'Independent fixture')['sessions'],4)
        ref=self.prices.copy(); ref.iloc[2,0]*=1.01
        with self.assertRaisesRegex(ValueError,'mismatch'):
            compare_adjusted_prices(self.prices,ref,'Independent fixture')

    def test_missing_sessions_values_source_fail(self):
        with self.assertRaisesRegex(ValueError,'sessions differ'):
            compare_adjusted_prices(self.prices,self.prices.drop(self.dates[1]),'Independent fixture')
        ref=self.prices.copy(); ref.iloc[0,0]=np.nan
        with self.assertRaisesRegex(ValueError,'finite'):
            compare_adjusted_prices(self.prices,ref,'Independent fixture')
        with self.assertRaisesRegex(ValueError,'independent'):
            compare_adjusted_prices(self.prices,self.prices,'Yahoo Finance')

    def test_dividend_factor_checked(self):
        self.raw.loc[self.dates[:2],('Adj Close','SPY')]=99.
        self.raw.loc[self.dates[2],('Dividends','SPY')]=1.
        self.assertEqual(audit_provider_adjustments(self.raw,self.dates)['dividend_events_checked'],1)
        self.raw.loc[self.dates[2],('Dividends','SPY')]=2.
        with self.assertRaisesRegex(ValueError,'adjustment mismatch'):
            audit_provider_adjustments(self.raw,self.dates)

    def test_split_requires_review(self):
        self.raw.loc[self.dates[2],('Stock Splits','SPY')]=2.
        with self.assertRaisesRegex(ValueError,'Split event'):
            audit_provider_adjustments(self.raw,self.dates)

    def test_incomplete_sessions_excluded(self):
        prices,m=adjusted_close_to_prices(self.raw,asof_date=self.dates[2].date())
        self.assertEqual(len(prices),2)
        self.assertEqual(m['rows_excluded_pending_session'],2)

    def test_invalid_prices_dates_and_missing_ticker(self):
        for value in (0.,-1.,np.inf):
            raw=self.raw.copy(); raw.loc[self.dates[0],('Close','SPY')]=value
            with self.assertRaises(ValueError):
                adjusted_close_to_prices(raw,asof_date=pd.Timestamp('2026-01-20').date())
        raw=self.raw.copy(); raw.index=pd.DatetimeIndex([pd.NaT,*self.dates[1:]])
        with self.assertRaisesRegex(ValueError,'dates'): adjusted_close_to_prices(raw)
        with self.assertRaisesRegex(ValueError,'Missing ETF'): adjusted_close_to_prices(self.raw.drop(columns='SPY',level=1))

    def test_missing_observations_disclosed_or_rejected(self):
        raw=pd.concat([self.raw]*10,ignore_index=True); raw.index=pd.bdate_range('2026-01-01',periods=40)
        raw.iloc[0,raw.columns.get_loc(('Close','SPY'))]=np.nan
        _,m=adjusted_close_to_prices(raw,asof_date=pd.Timestamp('2026-05-01').date())
        self.assertEqual(m['rows_dropped_missing'],1)
        self.assertEqual(m['dates_dropped_missing'],['2026-01-01'])
        raw.iloc[:4,raw.columns.get_loc(('Close','SPY'))]=np.nan
        with self.assertRaisesRegex(ValueError,'complete prices'):
            adjusted_close_to_prices(raw,asof_date=pd.Timestamp('2026-05-01').date())

    def test_independent_events_and_missing_events(self):
        events=pd.DataFrame({'Date':['2026-01-07'],'Ticker':['SPY'],'Dividends':[1.],'Stock Splits':[0.]})
        args=('Independent fixture','2026-01-05','2026-01-08')
        self.assertEqual(compare_corporate_actions(events,events.copy(),*args)['events'],1)
        for column in ('Dividends','Stock Splits'):
            changed=events.copy(); changed[column]=2.
            with self.assertRaisesRegex(ValueError,'mismatch'): compare_corporate_actions(events,changed,*args)
        with self.assertRaisesRegex(ValueError,'mismatch'): compare_corporate_actions(events,events.iloc[:0],*args)

if __name__=='__main__': unittest.main()
