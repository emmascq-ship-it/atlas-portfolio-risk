"""V7: independent formula checks, look-ahead safeguards, and product integrity."""
import math
import unittest
import numpy as np
import pandas as pd
from statistics import NormalDist

from risk_engine import DEFAULT_WEIGHTS, generate_synthetic_prices, portfolio_returns, summarize_risk
from model_benchmark import rolling_model_comparison, backtest_diagnostics, compare_var_models
from research_packet import generate_packet
from static_dashboard import dashboard_payload, render_html
from risk_engine import SCENARIOS


class TestV7Backtesting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices = generate_synthetic_prices()
        cls.returns = portfolio_returns(cls.prices, DEFAULT_WEIGHTS)
        cls.frame = rolling_model_comparison(cls.returns)
        cls.report = compare_var_models(cls.returns)

    def test_out_of_sample_forecast_start_and_length(self):
        self.assertEqual(self.frame.index[0], self.returns.index[250])
        self.assertEqual(len(self.frame), len(self.returns)-250)

    def test_gaussian_known_trailing_window(self):
        prev = self.returns.iloc[:250]
        target = max(0, NormalDist().inv_cdf(.95)*prev.std(ddof=1)-prev.mean())
        self.assertAlmostEqual(self.frame['Gaussian VaR'].iloc[0], target, 12)

    def test_future_observation_does_not_change_earlier_forecast(self):
        changed = self.returns.copy()
        changed.iloc[250] = -.5
        other = rolling_model_comparison(changed)
        for column in ('Historical VaR','Gaussian VaR'):
            self.assertAlmostEqual(self.frame[column].iloc[0], other[column].iloc[0], 12)
        self.assertNotEqual(self.frame['Actual loss'].iloc[0], other['Actual loss'].iloc[0])

    def test_two_models_expected_rate_and_exception_reconciliation(self):
        for m in self.report['models'].values():
            self.assertEqual(m['observations'], len(self.frame))
            self.assertAlmostEqual(m['expected_breaches'], .05*len(self.frame))
            self.assertEqual(m['max_consecutive_breaches'], 2)
        self.assertEqual(self.report['models']['historical']['breaches'], 31)
        self.assertEqual(self.report['models']['gaussian']['breaches'], 30)

    def test_false_breach_flag_rejected(self):
        manipulated = self.frame.copy()
        manipulated.iloc[0, manipulated.columns.get_loc('Historical breach')] = not bool(manipulated.iloc[0]['Historical breach'])
        with self.assertRaisesRegex(ValueError, 'reconcile'):
            backtest_diagnostics(manipulated,'Historical breach','Historical VaR',model='Historical')

    def test_nonfinite_returns_rejected(self):
        changed = self.returns.copy()
        changed.iloc[23] = np.nan
        with self.assertRaisesRegex(ValueError, 'finite'):
            rolling_model_comparison(changed)

    def test_breach_run_length_exact(self):
        f = self.frame.iloc[:10].copy()
        # all realized losses = 1%, forecasts = 0.5% only on days 2-4
        f['Actual loss']=.0
        f['Historical VaR']=.01
        f.loc[f.index[2:5],'Actual loss']=.02
        f['Historical breach']=f['Actual loss']>f['Historical VaR']
        m=backtest_diagnostics(f,'Historical breach','Historical VaR',model='Historical')
        self.assertEqual(m.max_consecutive_breaches,3)
        self.assertAlmostEqual(m.mean_breach_excess,.01)

    def test_initial_day_decline_is_max_drawdown(self):
        sample = pd.Series([-.2,.05],index=pd.bdate_range('2026-01-01',periods=2))
        self.assertAlmostEqual(summarize_risk(sample).max_drawdown,-.2)

    def test_invalid_dates_rejected(self):
        series=self.returns.copy();series.index=pd.Index(range(len(series)))
        with self.assertRaisesRegex(ValueError,'DatetimeIndex'):
            rolling_model_comparison(series)

    def test_packet_includes_methodology_and_model_warnings(self):
        p=generate_packet(self.prices,DEFAULT_WEIGHTS,source_label='Synthetic demo',class_shocks=SCENARIOS['Equity selloff'])
        self.assertTrue(p['model_benchmark']['methodology']['no_look_ahead'])
        self.assertEqual(p['model_benchmark']['models']['historical']['breaches'],31)
        self.assertEqual(p['approval_status'],'UNAPPROVED_RESEARCH')

    def test_browser_html_has_downloadable_model_comparison(self):
        payload=dashboard_payload(self.prices)
        html=render_html(payload)
        self.assertEqual(payload['schema'],'portfolio-risk-public-demo-v3')
        self.assertEqual(payload['benchmark']['models']['gaussian']['breaches'],30)
        for x in ('id="benchmark_chart"','id="benchmarkdownload"','id="benchmark_rows"'):
            self.assertIn(x,html)
        self.assertIn('No look-ahead',html)
        self.assertNotIn('<script src="http',html)


if __name__ == '__main__':unittest.main()

class TestV7DataLineage(unittest.TestCase):
    def test_non_datetime_index_rejected_by_core_checks(self):
        from risk_engine import validate_prices
        p=generate_synthetic_prices()
        p.index=pd.Index(range(len(p)))
        flags=validate_prices(p,DEFAULT_WEIGHTS)
        self.assertFalse(flags['1. Dates sorted ascending'])

    def test_true_false_prices_rejected(self):
        from risk_engine import validate_prices
        p=generate_synthetic_prices()
        p['Cash']=True
        flags=validate_prices(p,DEFAULT_WEIGHTS)
        self.assertFalse(flags['4. Prices numeric and finite'])

    def test_quality_heuristic_flags_big_weekday_gap(self):
        from data_quality import data_quality_diagnostics
        p=generate_synthetic_prices()
        p=p.drop(index=p.index[420:430])
        result=data_quality_diagnostics(p,'Synthetic demo',as_of=pd.Timestamp('2026-10-22').date())
        self.assertGreaterEqual(result['large_weekday_gap_count'],1)
        self.assertEqual(result['input_controls_passed'],8)
        self.assertTrue(any('Synthetic' in t for t in result['review_flags']))

    def test_snapshot_marks_all_unapproved(self):
        payload=dashboard_payload(generate_synthetic_prices())
        self.assertEqual(payload['quality']['input_controls_passed'],8)
        self.assertEqual(payload['review']['status'],'UNAPPROVED_DRAFT')
        self.assertIn('id="data_quality"',render_html(payload))

class TestV7RareEventCaveats(unittest.TestCase):
    def test_high_confidence_warns_about_weak_asymptotics(self):
        r=portfolio_returns(generate_synthetic_prices(),DEFAULT_WEIGHTS)
        summary=compare_var_models(r,confidence=.99)
        self.assertLess(summary['models']['historical']['expected_breaches'],10)
        self.assertTrue(any('chi-square' in t for t in summary['models']['historical']['warnings']))
        self.assertTrue(any('chi-square' in t for t in summary['models']['gaussian']['warnings']))
