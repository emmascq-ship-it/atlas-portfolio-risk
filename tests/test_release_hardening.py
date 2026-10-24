"""Regression checks for edge cases discovered in pre-Codex audit."""
import unittest
import contextlib
import io

import numpy as np
import pandas as pd

from risk_engine import (
    ASSETS, DEFAULT_WEIGHTS, generate_synthetic_prices, historical_var_es,
    portfolio_returns, rolling_var_backtest, validate_prices,
)


class InputHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices = generate_synthetic_prices()
        cls.returns = portfolio_returns(cls.prices, DEFAULT_WEIGHTS)

    def test_duplicate_asset_column_rejected_before_matrix_multiply(self):
        dirty = pd.concat([self.prices, self.prices[[ASSETS[0]]]], axis=1)
        self.assertFalse(validate_prices(dirty, DEFAULT_WEIGHTS)['3. Required assets present'])
        with self.assertRaisesRegex(ValueError, 'Required assets present'):
            portfolio_returns(dirty, DEFAULT_WEIGHTS)

    def test_duplicate_weight_labels_gracefully_rejected(self):
        weights = pd.concat([DEFAULT_WEIGHTS, DEFAULT_WEIGHTS.iloc[:1]])
        self.assertFalse(validate_prices(self.prices, weights)['8. Long-only weights sum to 100%'])
        with self.assertRaisesRegex(ValueError, 'weights sum'):
            portfolio_returns(self.prices, weights)

    def test_nonfinite_returns_never_emit_var(self):
        for value in [float('inf'), float('-inf')]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'finite'):
                    historical_var_es(pd.Series([-.01, .02, value, .03]))

    def test_invalid_less_than_minus_one_return_rejected(self):
        with self.assertRaisesRegex(ValueError, '100%'):
            historical_var_es(pd.Series([-.01, -1.01, .02]))

    def test_shuffled_dates_rejected_in_direct_backtest(self):
        shuffled = self.returns.iloc[::-1]
        with self.assertRaisesRegex(ValueError, 'chronological'):
            rolling_var_backtest(shuffled)

    def test_duplicate_dates_rejected_in_direct_backtest(self):
        duplicated = self.returns.copy()
        ix = list(duplicated.index)
        ix[300] = ix[299]
        duplicated.index = pd.DatetimeIndex(ix)
        with self.assertRaisesRegex(ValueError, 'unique'):
            rolling_var_backtest(duplicated)

    def test_invalid_backtest_return_rejected(self):
        dirty = self.returns.copy()
        dirty.iloc[270] = np.inf
        with self.assertRaisesRegex(ValueError, 'finite'):
            rolling_var_backtest(dirty)

    def test_invalid_backtest_window_rejected(self):
        for bad in [True, 0, -1, 20, 250.0]:
            with self.subTest(window=bad), self.assertRaisesRegex(ValueError, 'window'):
                rolling_var_backtest(self.returns, window=bad)


if __name__ == '__main__':
    unittest.main()

class PublicExportProtectionTests(unittest.TestCase):
    def test_csv_is_not_publishable_via_alternate_paths(self):
        """A user CSV must not silently land anywhere under GitHub Pages docs/."""
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from publish_demo import main
        root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            csv_file = Path(tmp)/'private.csv'
            generate_synthetic_prices().rename_axis('Date').to_csv(csv_file)
            destinations = [str(root/'docs'/'index.html'),
                            str(root/'docs'/'private-report.html'),
                            'docs/reports/portfolio.html']
            for target in destinations:
                with self.subTest(target=target), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    main(['--input-csv', str(csv_file), '--output', target])
                self.assertEqual(raised.exception.code, 2)
