import unittest
import numpy as np
import pandas as pd
from risk_engine import (
    ASSETS, DEFAULT_WEIGHTS, generate_synthetic_prices, historical_var_es,
    portfolio_returns, rolling_var_backtest, scenario_impact, summarize_risk,
    validate_prices, component_volatility, kupiec_unconditional_coverage,
)
from market_data import MARKET_TICKERS, adjusted_close_to_prices
from risk_brief import make_risk_brief


class PortfolioRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices = generate_synthetic_prices()
        cls.returns = portfolio_returns(cls.prices, DEFAULT_WEIGHTS)

    def test_synthetic_data_is_reproducible(self):
        pd.testing.assert_frame_equal(self.prices, generate_synthetic_prices())

    def test_seven_assets_five_classes_and_valid_inputs(self):
        self.assertEqual(len(ASSETS), 7)
        self.assertEqual(len(validate_prices(self.prices, DEFAULT_WEIGHTS)), 8)
        self.assertTrue(all(validate_prices(self.prices, DEFAULT_WEIGHTS).values()))

    def test_invalid_weights_rejected(self):
        w = DEFAULT_WEIGHTS.copy()
        w.iloc[0] += .1
        self.assertFalse(validate_prices(self.prices, w)["8. Long-only weights sum to 100%"])
        with self.assertRaises(ValueError):
            portfolio_returns(self.prices, w)

    def test_missing_prices_rejected(self):
        p = self.prices.copy()
        p.iloc[7, 1] = np.nan
        self.assertFalse(validate_prices(p, DEFAULT_WEIGHTS)["5. No missing price values"])

    def test_nonnumeric_price_rejected_without_crashing(self):
        p = self.prices.astype(object)
        p.iloc[7, 1] = "not a price"
        checks = validate_prices(p, DEFAULT_WEIGHTS)
        self.assertFalse(checks["4. Prices numeric and finite"])
        self.assertFalse(checks["6. Prices strictly positive"])

    def test_negative_price_rejected(self):
        p = self.prices.copy()
        p.iloc[7, 1] = -2
        self.assertFalse(validate_prices(p, DEFAULT_WEIGHTS)["6. Prices strictly positive"])

    def test_var_expected_shortfall_tail(self):
        v, es = historical_var_es(pd.Series([-0.10, -0.08, -0.01, 0.00, .03]), .80)
        self.assertGreaterEqual(es, v)

    def test_confidence_rejected(self):
        with self.assertRaises(ValueError):
            historical_var_es(self.returns, 1.0)

    def test_weights_and_returns(self):
        day = self.prices.pct_change().iloc[1]
        self.assertAlmostEqual(self.returns.iloc[0], float(day @ DEFAULT_WEIGHTS))

    def test_backtest_out_of_sample_and_window(self):
        backtest = rolling_var_backtest(self.returns, 250)
        self.assertEqual(len(backtest), len(self.returns) - 250)
        self.assertEqual(backtest.index[0], self.returns.index[250])
        v, _ = historical_var_es(self.returns.iloc[:250], .95)
        self.assertAlmostEqual(backtest.iloc[0]["VaR forecast"], v)

    def test_backtest_does_not_look_ahead(self):
        altered = self.returns.copy()
        altered.iloc[250] = -0.70
        original = rolling_var_backtest(self.returns, 250)
        modified = rolling_var_backtest(altered, 250)
        self.assertAlmostEqual(original.iloc[0]["VaR forecast"], modified.iloc[0]["VaR forecast"])

    def test_scenario_contributions_sum(self):
        loss, components = scenario_impact(DEFAULT_WEIGHTS, "Equity selloff")
        self.assertAlmostEqual(loss, components.sum())

    def test_volatility_decomposition(self):
        comp = component_volatility(self.prices, DEFAULT_WEIGHTS)
        self.assertAlmostEqual(comp.sum(), summarize_risk(self.returns).annualized_vol, places=8)

    def test_risk_metrics_reasonable(self):
        r = summarize_risk(self.returns)
        self.assertGreaterEqual(r.es, r.var)
        self.assertGreater(r.annualized_vol, 0)
        self.assertLessEqual(r.max_drawdown, 0)

    def test_short_history_fails(self):
        with self.assertRaises(ValueError):
            rolling_var_backtest(self.returns.iloc[:250], 250)

    def test_kupiec_perfect_frequency_has_p_one(self):
        flags = [True] * 5 + [False] * 95
        summary = kupiec_unconditional_coverage(pd.DataFrame({"Breach": flags}), .95)
        self.assertEqual(summary.breaches, 5)
        self.assertAlmostEqual(summary.expected_breaches, 5)
        self.assertAlmostEqual(summary.likelihood_ratio, 0, places=8)
        self.assertAlmostEqual(summary.p_value, 1, places=8)

    def test_kupiec_no_exceptions_is_finite(self):
        summary = kupiec_unconditional_coverage(pd.DataFrame({"Breach": [False] * 250}), .95)
        self.assertEqual(summary.breaches, 0)
        self.assertTrue(np.isfinite(summary.likelihood_ratio))
        self.assertLess(summary.p_value, .05)

    def test_kupiec_all_exceptions_is_finite(self):
        summary = kupiec_unconditional_coverage(pd.DataFrame({"Breach": [True] * 20}), .95)
        self.assertEqual(summary.breaches, 20)
        self.assertTrue(np.isfinite(summary.p_value))

    def test_kupiec_rejects_missing_exception_flags(self):
        with self.assertRaises(ValueError):
            kupiec_unconditional_coverage(pd.DataFrame({"Breach": [True, None]}))

    def test_market_data_adapter_maps_adjusted_prices(self):
        dates = pd.bdate_range('2024-01-01', periods=300)
        tickers = list(MARKET_TICKERS.values())
        columns = pd.MultiIndex.from_product([["Close", "Open"], tickers])
        raw = pd.DataFrame(100.0, index=dates, columns=columns)
        raw.loc[dates[0], ("Close", tickers[0])] = np.nan
        prices, metadata = adjusted_close_to_prices(raw, asof_date=pd.Timestamp('2030-01-01').date())
        self.assertEqual(list(prices.columns), ASSETS)
        self.assertEqual(len(prices), 299)
        self.assertEqual(metadata["rows_dropped_missing"], 1)
        self.assertTrue((prices == 100.0).all().all())

    def test_market_data_adapter_rejects_large_data_gaps(self):
        dates = pd.bdate_range('2024-01-01', periods=300)
        tickers = list(MARKET_TICKERS.values())
        columns = pd.MultiIndex.from_product([["Close"], tickers])
        raw = pd.DataFrame(100.0, index=dates, columns=columns)
        raw.loc[dates[:20], ("Close", tickers[0])] = np.nan
        with self.assertRaisesRegex(ValueError, "complete prices"):
            adjusted_close_to_prices(raw, asof_date=pd.Timestamp('2030-01-01').date())

    def test_market_data_adapter_supports_reverse_multiindex(self):
        dates = pd.bdate_range('2024-01-01', periods=300)
        tickers = list(MARKET_TICKERS.values())
        columns = pd.MultiIndex.from_product([tickers, ["Close"]])
        raw = pd.DataFrame(42.0, index=dates, columns=columns)
        prices, _ = adjusted_close_to_prices(raw, asof_date=pd.Timestamp('2030-01-01').date())
        self.assertEqual(list(prices.columns), ASSETS)

    def test_market_data_excludes_current_session(self):
        dates = pd.bdate_range('2024-01-01', periods=300)
        columns = pd.MultiIndex.from_product([["Close"], list(MARKET_TICKERS.values())])
        raw = pd.DataFrame(100.0, index=dates, columns=columns)
        asof_date = dates[-1].date()
        prices, meta = adjusted_close_to_prices(raw, asof_date=asof_date)
        self.assertNotIn(dates[-1], prices.index)
        self.assertEqual(meta["rows_excluded_pending_session"], 1)

    def test_analyst_review_contains_auditable_values(self):
        backtest = rolling_var_backtest(self.returns, 250, .95)
        coverage = kupiec_unconditional_coverage(backtest, .95)
        risk = summarize_risk(self.returns)
        stress, _ = scenario_impact(DEFAULT_WEIGHTS, "Equity selloff")
        component = component_volatility(self.prices, DEFAULT_WEIGHTS)
        brief = make_risk_brief(risk, coverage, DEFAULT_WEIGHTS, component,
                                "Equity selloff", stress, 1000000, .95,
                                "Synthetic test", "2022-01-01", "2026-10-21", 250)
        self.assertIn(f"{risk.var:.2%}", brief)
        self.assertIn(f"{coverage.breaches}/{coverage.observations}", brief)
        self.assertIn(f"{stress:+.2%}", brief)
        self.assertIn("Synthetic test", brief)

    def test_analyst_review_rejects_invalid_notional(self):
        with self.assertRaises(ValueError):
            make_risk_brief(summarize_risk(self.returns),
                            kupiec_unconditional_coverage(rolling_var_backtest(self.returns)),
                            DEFAULT_WEIGHTS, component_volatility(self.prices, DEFAULT_WEIGHTS),
                            "Equity selloff", -.1, 0, .95, "Synthetic", "2020-01-01", "2026-01-01", 250)


if __name__ == "__main__":
    unittest.main()
