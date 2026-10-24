"""Independent arithmetic reconciliation; never tunes model assumptions."""
from decimal import Decimal
import unittest
from risk_engine import ASSET_CLASS, DEFAULT_WEIGHTS, SCENARIOS, scenario_impact

class StressReconciliationTests(unittest.TestCase):
    def test_documented_equity_selloff_and_resume_difference(self):
        contributions={asset:Decimal(str(weight))*Decimal(str(SCENARIOS['Equity selloff'][ASSET_CLASS[asset]]))
                       for asset,weight in DEFAULT_WEIGHTS.items()}
        self.assertEqual(sum(contributions.values()),Decimal('-0.13045'))
        actual,_=scenario_impact(DEFAULT_WEIGHTS,'Equity selloff')
        self.assertAlmostEqual(actual,float(sum(contributions.values())),places=14)
        self.assertEqual(abs(sum(contributions.values()))-Decimal('.125'),Decimal('.00545'))

if __name__=='__main__': unittest.main()
