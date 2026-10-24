"""V5 offline, public-demo and provenance regression checks."""
import json
import tempfile
import unittest
from pathlib import Path

from risk_engine import generate_synthetic_prices, DEFAULT_WEIGHTS
from static_dashboard import dashboard_payload, render_html, write_dashboard
from publish_demo import main


class TestPublicDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices = generate_synthetic_prices()
        cls.payload = dashboard_payload(cls.prices)

    def test_unapproved_and_explicitly_synthetic(self):
        self.assertTrue(self.payload['synthetic'])
        self.assertEqual(self.payload['review']['status'], 'UNAPPROVED_DRAFT')
        self.assertIn('Synthetic', self.payload['source'])

    def test_default_scenario_is_calculated_not_resume_number(self):
        self.assertAlmostEqual(self.payload['kpis']['stress'], -.13045, places=8)
        self.assertNotAlmostEqual(self.payload['kpis']['stress'], -.125, places=3)

    def test_7_assets_5_classes(self):
        self.assertEqual(len(self.payload['inputs']['weights']), 7)
        self.assertEqual(len(self.payload['inputs']['classes']), 5)
        self.assertAlmostEqual(sum(self.payload['inputs']['weights'].values()), 1.)

    def test_risk_and_backtest_consistency(self):
        b=self.payload['backtest']
        self.assertEqual(len(b['dates']),len(b['forecast']))
        self.assertEqual(len(b['dates']),len(b['actual']))
        self.assertEqual(sum(b['breaches']),self.payload['kpis']['breaches'])
        self.assertEqual(len(b['dates']),self.payload['kpis']['backtest_observations'])

    def test_report_contains_human_review_gate(self):
        self.assertTrue(self.payload['review']['draft'].startswith('# Portfolio Risk Brief'))
        self.assertGreaterEqual(len(self.payload['review']['evidence']), 11)
        self.assertIn('No recommendation',self.payload['review']['draft'])

    def test_provenance_binds_full_inputs(self):
        self.assertEqual(len(self.payload['inputs']['saved_input_sha256']), 64)
        weights=DEFAULT_WEIGHTS.copy();weights['US Equity']+=.01;weights['Global Equity']-=.01
        modified=dashboard_payload(self.prices, weights)
        self.assertNotEqual(modified['inputs']['saved_input_sha256'],self.payload['inputs']['saved_input_sha256'])

    def test_static_html_is_offline_and_self_contained(self):
        body=render_html(self.payload)
        self.assertIn('Plotly',body)
        self.assertIn('UNAPPROVED RESEARCH DEMO',body)
        self.assertIn('const DATA = ',body)
        self.assertIn('Reset to baseline',body)
        self.assertNotIn('<script src="https://',body)
        self.assertNotIn('<script src="http://',body)

    def test_script_data_escaping(self):
        injected=dict(self.payload)
        injected['source']='</script><img src=x onerror=alert(1)>'
        body=render_html(injected)
        self.assertNotIn('</script><img',body)
        self.assertIn('\\u003c/script\\u003e',body)

    def test_write_to_temporary_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'public'/'index.html'
            output=write_dashboard(self.prices,path)
            self.assertEqual(output['schema'],'portfolio-risk-public-demo-v3')
            self.assertGreater(path.stat().st_size,1_000_000)

    def test_cli_refuses_accidental_publication_of_uploaded_csv(self):
        with self.assertRaises(SystemExit) as exc:
            main(['--input-csv','sensitive_positions.csv'])
        self.assertEqual(exc.exception.code,2)

    def test_cli_private_csv_output_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            prices=Path(temp)/'adjusted.csv';dest=Path(temp)/'report.html'
            self.prices.to_csv(prices,index_label='Date')
            self.assertEqual(main(['--input-csv',str(prices),'--output',str(dest)]),0)
            self.assertTrue(dest.is_file())


if __name__=='__main__':
    unittest.main()
