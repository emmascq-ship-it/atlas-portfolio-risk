import json
import unittest
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from risk_engine import (
    ASSETS, ASSET_CLASS, DEFAULT_WEIGHTS, SCENARIOS, generate_synthetic_prices,
    scenario_impact, portfolio_returns, rolling_var_backtest,
)
from validation_extensions import (
    CLASSES, christoffersen_independence, combined_coverage_test,
    scenario_impact_custom,
)
from research_packet import inputs_fingerprint, generate_packet, packet_bytes
from briefing_workflow import (
    evidence_pack, evidence_digest, approve_brief, rules_based_draft, approval_is_current,
)
from risk_engine import summarize_risk, kupiec_unconditional_coverage
from factor_engine import factor_attribution


class IndependenceMathTests(unittest.TestCase):
    def test_transition_counts_are_exact(self):
        # F F T T F T => (n00=1, n01=2, n10=1, n11=1)
        b = pd.DataFrame({'Breach':[False,False,True,True,False,True]})
        r = christoffersen_independence(b)
        self.assertEqual((r.n00,r.n01,r.n10,r.n11),(1,2,1,1))
        self.assertEqual(r.n00+r.n01+r.n10+r.n11, len(b)-1)

    def test_all_zeroes_is_numerically_stable_but_warns(self):
        r = christoffersen_independence(pd.DataFrame({'Breach':[False]*300}))
        self.assertEqual(r.likelihood_ratio,0)
        self.assertEqual(r.p_value,1)
        self.assertIn('Fewer',r.warning)

    def test_all_ones_is_numerically_stable_but_warns_missing_group(self):
        r=christoffersen_independence(pd.DataFrame({'Breach':[True]*300}))
        self.assertEqual(r.likelihood_ratio,0)
        self.assertEqual(r.p_value,1)
        self.assertIn('absent',r.warning)

    def test_clumped_breaches_are_detected(self):
        flags=[False]*50 + [True]*30 + [False]*50 + [True]*30
        r=christoffersen_independence(pd.DataFrame({'Breach':flags}))
        self.assertLess(r.p_value,0.05)
        self.assertGreater(r.transition_rate_after_breach,r.transition_rate_after_no_breach)

    def test_combined_chisquare_reference(self):
        lr,p=combined_coverage_test(1.2,2.3)
        self.assertAlmostEqual(lr,3.5)
        self.assertAlmostEqual(p,np.exp(-3.5/2))
        with self.assertRaises(ValueError):
            combined_coverage_test(-1,2)

    def test_invalid_flags_fail(self):
        for flags in ([False,True,None], [0,1,0], [False,True]):
            with self.assertRaises(ValueError):
                christoffersen_independence(pd.DataFrame({'Breach':flags}))


class CustomScenarioTests(unittest.TestCase):
    def test_custom_matches_default_when_same_shocks(self):
        for name,shocks in SCENARIOS.items():
            old,old_contrib=scenario_impact(DEFAULT_WEIGHTS,name)
            new,new_contrib=scenario_impact_custom(DEFAULT_WEIGHTS,shocks)
            self.assertAlmostEqual(old,new)
            pd.testing.assert_series_equal(old_contrib,new_contrib)

    def test_shocks_by_class_not_weight_are_applied(self):
        shocks={c:0.0 for c in CLASSES}
        shocks['Equity']=-.25
        ret, components=scenario_impact_custom(DEFAULT_WEIGHTS,shocks)
        self.assertAlmostEqual(ret,-.25*(DEFAULT_WEIGHTS['US Equity']+DEFAULT_WEIGHTS['Global Equity']))
        self.assertAlmostEqual(components.sum(),ret)

    def test_rejects_invalid_inputs(self):
        valid={c:0.0 for c in CLASSES}
        with self.assertRaises(ValueError):scenario_impact_custom(DEFAULT_WEIGHTS,{'Equity':-.2})
        with self.assertRaises(ValueError):scenario_impact_custom(DEFAULT_WEIGHTS,{**valid,'Equity':float('nan')})
        with self.assertRaises(ValueError):scenario_impact_custom(DEFAULT_WEIGHTS,{**valid,'Equity':-1.01})
        with self.assertRaises(ValueError):scenario_impact_custom(DEFAULT_WEIGHTS*1.1,valid)


class AuditPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices=generate_synthetic_prices(n_days=550)
        cls.shocks=SCENARIOS['Equity selloff']
        cls.packet=generate_packet(cls.prices, DEFAULT_WEIGHTS, confidence=.95, window=250,
            notional=1e6, scenario_label='Equity selloff', class_shocks=cls.shocks,
            source_label='Synthetic demo')

    def test_no_claim_of_analyst_approval(self):
        self.assertEqual(self.packet['approval_status'],'UNAPPROVED_RESEARCH')
        self.assertIn('Synthetic demo',self.packet['source']['label'])
        self.assertEqual(len(self.packet['validation']),8)
        self.assertTrue(all(self.packet['validation'].values()))

    def test_loss_reconciles_with_asset_components(self):
        shock=self.packet['scenario']
        self.assertAlmostEqual(sum(shock['contribution_by_asset'].values()),shock['portfolio_return'])
        self.assertAlmostEqual(shock['estimated_pnl_usd'],shock['portfolio_return']*1e6)
        self.assertEqual(sum(self.packet['assumptions']['weights'].values()),1)

    def test_full_precision_input_fingerprint(self):
        common=(self.prices,DEFAULT_WEIGHTS,.95,250,1e6,'Equity selloff',self.shocks,'Synthetic demo')
        digest=inputs_fingerprint(*common)
        self.assertEqual(digest,self.packet['input_sha256'])
        self.assertEqual(len(digest),64)
        changed=self.prices.copy()
        changed.iloc[0,0]+=0.0000001
        self.assertNotEqual(digest,inputs_fingerprint(changed,*common[1:]))
        self.assertNotEqual(digest,inputs_fingerprint(self.prices,DEFAULT_WEIGHTS,.95,250,1e6,
                          'Equity selloff',{**self.shocks,'Equity':-.301},'Synthetic demo'))

    def test_packet_serialization_and_reproducibility(self):
        payload=packet_bytes(self.packet)
        self.assertTrue(payload.endswith(b'\n'))
        self.assertEqual(json.loads(payload)['input_sha256'],self.packet['input_sha256'])
        self.assertEqual(payload,packet_bytes(generate_packet(self.prices, DEFAULT_WEIGHTS,
            confidence=.95, window=250, notional=1e6, scenario_label='Equity selloff',
            class_shocks=self.shocks, source_label='Synthetic demo')))

    def test_rounding_cannot_preserve_stale_approval(self):
        r=portfolio_returns(self.prices, DEFAULT_WEIGHTS)
        risk=summarize_risk(r)
        coverage=kupiec_unconditional_coverage(rolling_var_backtest(r,250))
        factor=factor_attribution(self.prices,DEFAULT_WEIGHTS)
        scenario_return,_=scenario_impact(DEFAULT_WEIGHTS,'Equity selloff')
        args=(risk,coverage,factor,DEFAULT_WEIGHTS,'Equity selloff',scenario_return,
              1e6,.95,'Synthetic demo','2024-01-01','2026-10-21',250)
        original=evidence_pack(*args,input_digest=self.packet['input_sha256'])
        draft=rules_based_draft(original)
        record=approve_brief(draft,original,'Analyst',True,datetime(2026,10,22,tzinfo=timezone.utc))
        self.assertTrue(approval_is_current(record,draft,original))
        changed=evidence_pack(*args,input_digest='0'*64)
        self.assertEqual(changed['observations'],original['observations'])
        self.assertNotEqual(evidence_digest(changed),evidence_digest(original))
        self.assertFalse(approval_is_current(record,draft,changed))

    def test_raw_stock_data_not_in_packet(self):
        self.assertNotIn('prices',self.packet)
        self.assertNotIn('raw_returns',self.packet)
        self.assertNotIn('api_key',json.dumps(self.packet).lower())


if __name__=='__main__':
    unittest.main()
