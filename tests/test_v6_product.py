"""V6 analytics, provenance and standalone product regression coverage."""
import json
import unittest
from risk_engine import ASSETS, SCENARIOS, ASSET_CLASS, DEFAULT_WEIGHTS, generate_synthetic_prices
from static_dashboard import dashboard_payload, render_html


class TestV6ResearchProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = dashboard_payload(generate_synthetic_prices())
        cls.html = render_html(cls.payload)

    def test_schema_and_provenance(self):
        self.assertEqual(self.payload['schema'], 'portfolio-risk-public-demo-v3')
        self.assertTrue(self.payload['synthetic'])
        self.assertEqual(self.payload['review']['status'],'UNAPPROVED_DRAFT')
        self.assertEqual(len(self.payload['inputs']['saved_input_sha256']), 64)

    def test_drawdown_matches_reported_max_drawdown(self):
        dd=self.payload['drawdown']
        self.assertEqual(dd['dates'],self.payload['growth']['dates'])
        self.assertAlmostEqual(min(dd['values']),self.payload['kpis']['drawdown'],places=10)
        self.assertTrue(all(v <= 1e-12 for v in dd['values']))

    def test_correlation_diagonal_and_symmetry(self):
        c=self.payload['correlations']
        self.assertEqual(c['assets'], ASSETS)
        self.assertEqual(len(c['values']),len(ASSETS))
        for i in range(len(ASSETS)):
            self.assertAlmostEqual(c['values'][i][i],1.,places=8)
            for j in range(len(ASSETS)):
                self.assertAlmostEqual(c['values'][i][j],c['values'][j][i],places=8)
                self.assertLessEqual(abs(c['values'][i][j]),1+1e-8)

    def test_component_volatility_reconciles(self):
        self.assertAlmostEqual(sum(self.payload['asset_vol'].values()),self.payload['kpis']['volatility'],places=9)

    def test_three_scenario_presets_match_engine(self):
        self.assertEqual(self.payload['scenario_presets'],SCENARIOS)
        for scenario, shocks in self.payload['scenario_presets'].items():
            outcome=sum(float(DEFAULT_WEIGHTS[a])*shocks[ASSET_CLASS[a]] for a in ASSETS)
            self.assertLessEqual(outcome,1)
            if scenario=='Equity selloff':
                self.assertAlmostEqual(outcome,self.payload['kpis']['stress'],places=12)

    def test_html_navigation_and_controls_present(self):
        for name in ('Overview','Factor exposures','Scenario lab','Model validation','Review desk'):
            self.assertIn(name,self.html)
        for key in ('correlation','drawdown_chart','risk_contrib_chart','scenario_compare','scenarioexport','scenarioexportcsv'):
            self.assertIn('id="'+key+'"',self.html)

    def test_no_external_dependencies_embedded(self):
        self.assertIn('const DATA = ',self.html)
        self.assertNotIn('<script src="http',self.html)
        self.assertNotIn('<link href="http',self.html)
        self.assertIn('UNAPPROVED RESEARCH DEMO',self.html)
        self.assertGreater(len(self.html),1_000_000)

    def test_saved_evidence_does_not_change_with_scenario_controls(self):
        self.assertIn('baseline_input_sha256',self.html)
        self.assertIn('UNAPPROVED_HYPOTHETICAL',self.html)
        self.assertIn('Modified scenarios update the',self.html)

    def test_research_payload_has_no_unapproved_market_claim(self):
        self.assertIn('NOT market observations',self.payload['source'])
        self.assertNotIn('LIVE MARKET',self.html)

    def test_input_json_script_injection_is_escaped(self):
        altered=dict(self.payload,source='</script><img src=x onerror=alert(1)>')
        body=render_html(altered)
        self.assertNotIn('</script><img',body)
        self.assertIn('\\u003c/script\\u003e',body)


if __name__=='__main__':unittest.main()
