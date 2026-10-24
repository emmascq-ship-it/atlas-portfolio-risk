"""Displayed values reconcile to report precision; no recalibration."""
import json
import importlib.util
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from risk_engine import generate_synthetic_prices,DEFAULT_WEIGHTS,SCENARIOS,portfolio_returns
from research_packet import generate_packet,packet_bytes
from static_dashboard import dashboard_payload
from model_benchmark import compare_var_models

class DisplayConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices=generate_synthetic_prices()
        cls.returns=portfolio_returns(cls.prices,DEFAULT_WEIGHTS)
        cls.packet=json.loads(packet_bytes(generate_packet(cls.prices,DEFAULT_WEIGHTS,
            class_shocks=SCENARIOS['Equity selloff'],scenario_label='Equity selloff')))
        cls.comparison=compare_var_models(cls.returns)

    def test_static_payload_reconciles_to_report(self):
        payload=dashboard_payload(self.prices)
        for ui,report in [('var','historical_var_1d'),('es','expected_shortfall_1d'),
                          ('volatility','annualized_volatility'),('drawdown','max_drawdown')]:
            self.assertAlmostEqual(payload['kpis'][ui],self.packet['risk'][report],places=14)
        self.assertEqual(payload['factors']['beta'],self.packet['factors']['betas'])
        self.assertAlmostEqual(payload['kpis']['stress'],self.packet['scenario']['portfolio_return'],places=14)
        self.assertEqual(json.loads(json.dumps(payload['benchmark']['models'])),self.packet['model_benchmark']['models'])

    @unittest.skipUnless(importlib.util.find_spec('streamlit'), 'requires Streamlit')
    def test_streamlit_values_match_export_calculations(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=60).run()
        self.assertFalse(app.exception)
        metrics={x.label:x.value for x in app.metric}
        for label,key in [('1-day Historical VaR','historical_var_1d'),('1-day Expected Shortfall','expected_shortfall_1d'),
                          ('Annualized Volatility','annualized_volatility'),('Maximum Drawdown','max_drawdown')]:
            self.assertEqual(metrics[label],f"{self.packet['risk'][key]:.2%}")
        self.assertEqual(metrics['Scenario P&L'],f"{self.packet['scenario']['portfolio_return']:+.3%}")
        latest=self.comparison['backtest'].iloc[-1]
        for label,column in [('Latest Historical VaR forecast','Historical VaR'),('Latest Gaussian VaR forecast','Gaussian VaR')]:
            self.assertEqual(metrics[label],f'{latest[column]:.3%}')
        table=next(x.value for x in app.dataframe if 'observed_breach_rate' in x.value.columns)
        self.assertEqual(table['breaches'].tolist(),[31,30])

    def test_csv_roundtrip_and_forecast_breaches_reconcile(self):
        import io
        prices=pd.read_csv(io.StringIO(self.prices.to_csv(index_label='Date')),index_col='Date',parse_dates=True)
        np.testing.assert_allclose(prices.to_numpy(),self.prices.to_numpy(),rtol=1e-14)
        frame=self.comparison['backtest']
        for name,column in [('historical','Historical VaR'),('gaussian','Gaussian VaR')]:
            self.assertEqual(int((frame['Actual loss']>frame[column]).sum()),self.packet['model_benchmark']['models'][name]['breaches'])
