"""Fabricated Tiingo fixtures: no key, network or provider data."""
import json
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
import pandas as pd
from market_data import MARKET_TICKERS
from tiingo_reference import validate_tiingo_reference, normalize_history, fetch_history, ReferencePending

class TiingoReferenceTests(unittest.TestCase):
    def setUp(self):
        self.dates=pd.bdate_range('2026-01-05',periods=4)
        self.prices=pd.DataFrame({a:[100.,101.,100.,102.] for a in MARKET_TICKERS},index=self.dates)
        self.records=[{'date':d.isoformat()+'Z','adjClose':v,'close':v,'divCash':0.,'splitFactor':1.}
                      for d,v in zip(self.dates,[100.,101.,100.,102.])]
        self.fetch=Mock(side_effect=lambda *args:[dict(row) for row in self.records])

    def test_no_key_or_confirmation_pending_no_calls(self):
        for key,confirmed in [('',True),('TEST',False)]:
            result=validate_tiingo_reference(self.prices,{},key,confirm_free_starter=confirmed,fetcher=self.fetch)
            self.assertEqual(result['status'],'PENDING')
        self.fetch.assert_not_called()

    def test_seven_histories_match_without_raw_record_redistribution(self):
        result=validate_tiingo_reference(self.prices,{'corporate_actions':[]},'TEST',confirm_free_starter=True,fetcher=self.fetch)
        self.assertEqual(result['status'],'REFERENCE_CHECKS_PASSED')
        self.assertEqual(self.fetch.call_count,7)
        self.assertNotIn('adjClose',json.dumps(result));self.assertNotIn('TEST',json.dumps(result))

    def test_price_mismatch_fails(self):
        self.records[1]['adjClose']=105.
        result=validate_tiingo_reference(self.prices,{'corporate_actions':[]},'TEST',confirm_free_starter=True,fetcher=self.fetch)
        self.assertEqual(result['status'],'FAILED')

    def test_action_mismatch_fails(self):
        self.records[1]['divCash']=1.
        result=validate_tiingo_reference(self.prices,{'corporate_actions':[]},'TEST',confirm_free_starter=True,fetcher=self.fetch)
        self.assertEqual(result['status'],'FAILED')

    def test_insufficient_free_data_pending(self):
        self.records.pop(1)
        result=validate_tiingo_reference(self.prices,{'corporate_actions':[]},'TEST',confirm_free_starter=True,fetcher=self.fetch)
        self.assertEqual(result['status'],'PENDING')

    def test_quota_unavailable_pending_no_retry(self):
        self.fetch.side_effect=ReferencePending('Free quota unavailable')
        result=validate_tiingo_reference(self.prices,{},'TEST',confirm_free_starter=True,fetcher=self.fetch)
        self.assertEqual(result['status'],'PENDING');self.assertEqual(self.fetch.call_count,1)

    def test_token_header_only_quota_error_sanitized(self):
        opener=Mock();opener.open.side_effect=HTTPError('ignored',429,'token TEST-SECRET',{},None)
        with patch('tiingo_reference.build_opener',return_value=opener):
            with self.assertRaises(ReferencePending) as caught:fetch_history('SPY','2026-01-05','2026-01-08','TEST-SECRET')
        self.assertNotIn('TEST-SECRET',str(caught.exception))
        request=opener.open.call_args.args[0]
        self.assertNotIn('TEST-SECRET',request.full_url)
        self.assertEqual(request.get_header('Authorization'),'Token TEST-SECRET')
        self.assertEqual(opener.open.call_count,1)

    def test_split_normalization_and_incomplete_session_exclusion(self):
        self.records[1]['splitFactor']=2.
        prices,actions=normalize_history(self.records,'SPY',self.dates[2].date())
        self.assertEqual(len(prices),2);self.assertEqual(actions['Stock Splits'].tolist(),[2.])
        self.records[0].pop('adjClose')
        with self.assertRaises(ReferencePending):normalize_history(self.records,'SPY',self.dates[2].date())

if __name__=='__main__':unittest.main()
