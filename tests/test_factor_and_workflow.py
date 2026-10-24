import json
from datetime import datetime, timezone
import unittest
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

from risk_engine import (
    ASSETS, DEFAULT_WEIGHTS, generate_synthetic_prices, portfolio_returns,
    rolling_var_backtest, kupiec_unconditional_coverage, summarize_risk, scenario_impact,
)
from factor_engine import build_factor_proxies, factor_attribution, FACTOR_DESCRIPTIONS
from briefing_workflow import (
    evidence_pack, evidence_digest, rules_based_draft, approve_brief, approval_is_current,
    export_review_bundle, validate_draft_evidence, generate_llm_draft,
)


class FactorAndBriefingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices = generate_synthetic_prices()
        cls.returns = portfolio_returns(cls.prices, DEFAULT_WEIGHTS)
        cls.factor = factor_attribution(cls.prices, DEFAULT_WEIGHTS)
        cls.coverage = kupiec_unconditional_coverage(rolling_var_backtest(cls.returns))
        cls.risk = summarize_risk(cls.returns)
        cls.impact, _ = scenario_impact(DEFAULT_WEIGHTS, "Equity selloff")
        cls.evidence = evidence_pack(cls.risk, cls.coverage, cls.factor,
            DEFAULT_WEIGHTS, "Equity selloff", cls.impact, 1e6, .95,
            "Synthetic demonstration", "2023-01-01", "2026-10-21", 250)

    def test_five_proxy_factors(self):
        f = build_factor_proxies(self.prices)
        self.assertEqual(f.shape, (899, 5))
        self.assertEqual(set(f.columns), set(FACTOR_DESCRIPTIONS))

    def test_factor_proxy_spread_algebra(self):
        asset_rets = self.prices.pct_change().iloc[1]
        f = build_factor_proxies(self.prices).iloc[0]
        self.assertAlmostEqual(f["Equity market"], asset_rets["US Equity"] - asset_rets["Cash"])
        self.assertAlmostEqual(f["Credit spread"], asset_rets["Corp Bonds"] - asset_rets["Treasuries"])

    def test_regression_fitted_plus_residual_equals_portfolio(self):
        pd.testing.assert_series_equal(self.factor.fitted_returns + self.factor.residual_returns,
                                       self.returns, check_names=False, atol=1e-11)

    def test_ols_intercept_means_zero_residual(self):
        self.assertAlmostEqual(self.factor.residual_returns.mean(), 0., places=12)

    def test_factor_component_variances_add_up(self):
        self.assertAlmostEqual(self.factor.fitted_variance_contributions.sum(),
                               self.factor.fitted_annualized_vol ** 2, places=11)

    def test_regression_shape_and_quality(self):
        self.assertEqual(len(self.factor.betas), 5)
        self.assertEqual(self.factor.observations, len(self.returns))
        self.assertTrue(0 <= self.factor.r_squared <= 1)
        self.assertTrue(np.isfinite(self.factor.condition_number))

    def test_factor_attribution_insufficient_history(self):
        with self.assertRaisesRegex(ValueError, "at least 1000"):
            factor_attribution(self.prices, DEFAULT_WEIGHTS, min_observations=1000)

    def test_factor_regression_rejects_rank_deficiency(self):
        p = pd.DataFrame(np.tile(np.arange(300, 1200), (len(ASSETS), 1)).T.astype(float),
                         index=self.prices.index, columns=ASSETS)
        with self.assertRaisesRegex(ValueError, "rank deficient"):
            factor_attribution(p, DEFAULT_WEIGHTS)

    def test_evidence_pack_has_curated_observations(self):
        self.assertEqual(len(self.evidence["observations"]), 11)
        self.assertIn("Synthetic", self.evidence["observations"]["E01"])
        self.assertIn("Kupiec", self.evidence["observations"]["E08"])

    def test_rule_based_brief_cites_evidence(self):
        draft = rules_based_draft(self.evidence)
        self.assertEqual(validate_draft_evidence(draft, self.evidence), [])
        self.assertIn("Draft only", draft)

    def test_missing_citations_block_approval(self):
        draft = rules_based_draft(self.evidence).replace("[E08]", "[E99]")
        issues = validate_draft_evidence(draft, self.evidence)
        self.assertTrue(issues)
        with self.assertRaisesRegex(ValueError, "citation gate"):
            approve_brief(draft, self.evidence, "Analyst", True)

    def test_approval_requires_explicit_attestation(self):
        with self.assertRaisesRegex(ValueError, "Explicit"):
            approve_brief(rules_based_draft(self.evidence), self.evidence, "Analyst", False)
        with self.assertRaisesRegex(ValueError, "reviewer"):
            approve_brief(rules_based_draft(self.evidence), self.evidence, "", True)

    def test_approval_matches_only_exact_snapshot(self):
        draft = rules_based_draft(self.evidence)
        record = approve_brief(draft, self.evidence, "Emma", True,
                               datetime(2026, 10, 22, tzinfo=timezone.utc))
        self.assertTrue(approval_is_current(record, draft, self.evidence))
        self.assertFalse(approval_is_current(record, draft + " changed", self.evidence))
        changed = dict(self.evidence)
        changed["observations"] = {**changed["observations"], "E03": "new VaR"}
        self.assertFalse(approval_is_current(record, draft, changed))

    def test_bundle_marks_unapproved_or_approved_correctly(self):
        draft = rules_based_draft(self.evidence)
        raw = json.loads(export_review_bundle(draft, self.evidence, None))
        self.assertEqual(raw["status"], "UNAPPROVED_DRAFT")
        rec = approve_brief(draft, self.evidence, "Emma", True)
        exported = json.loads(export_review_bundle(draft, self.evidence, rec))
        self.assertEqual(exported["status"], "ANALYST_APPROVED")
        self.assertEqual(exported["review"]["evidence_sha256"], evidence_digest(self.evidence))
        with self.assertRaisesRegex(ValueError, "stale"):
            export_review_bundle(draft + " changed", self.evidence, rec)

    def test_ai_generation_is_opt_in(self):
        with self.assertRaisesRegex(ValueError, "user-provided"):
            generate_llm_draft(self.evidence, "")

    def test_unsupported_evidence_refs_reported(self):
        draft = rules_based_draft(self.evidence).replace("[E03]", "[E12]")
        issues = validate_draft_evidence(draft, self.evidence)
        self.assertTrue(any("E12" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
