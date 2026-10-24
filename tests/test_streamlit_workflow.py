"""Streamlit runtime regressions; install requirements.txt to enable."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'requires Streamlit')
class StreamlitWorkflowTests(unittest.TestCase):
    def app(self):
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'),
                                 default_timeout=45).run()

    def test_approval_requires_review_and_revokes_on_edit_and_inputs(self):
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.tabs), 5)
        self.assertTrue(app.button[0].disabled)
        self.assertEqual(len(app.text_area), 0)
        app.text_input[0].set_value('AUTOMATED SYNTHETIC TEST')
        app.checkbox[0].check().run()
        app.button[0].click().run()
        self.assertTrue(any('ANALYST APPROVED' in x.value for x in app.success))
        original_draft = app.session_state.brief_snapshot['draft']
        original_approval = app.session_state.brief_snapshot['approval']
        next(x for x in app.radio if x.label == 'Report mode').set_value('Edit Draft').run()
        self.assertEqual(app.text_area[0].value, original_draft)
        self.assertEqual(app.session_state.brief_snapshot['approval'], original_approval)
        app.text_area[0].set_value(app.text_area[0].value + '\nTest editorial note.').run()
        self.assertFalse(any('ANALYST APPROVED' in x.value for x in app.success))
        edited = app.session_state.brief_snapshot['draft']
        next(x for x in app.radio if x.label == 'Report mode').set_value('Preview').run()
        self.assertEqual(len(app.text_area), 0)
        self.assertEqual(app.session_state.brief_snapshot['draft'], edited)
        app.button[0].click().run()
        self.assertTrue(any('ANALYST APPROVED' in x.value for x in app.success))
        next(x for x in app.radio if x.label == 'Report mode').set_value('Edit Draft').run()
        self.assertEqual(app.text_area[0].value, edited)
        self.assertTrue(any('ANALYST APPROVED' in x.value for x in app.success))
        app.number_input[0].set_value(1100000).run()
        self.assertFalse(app.exception)
        self.assertFalse(any('ANALYST APPROVED' in x.value for x in app.success))
        self.assertTrue(any('$1,100,000 USD' in x.value for x in app.text))

    def test_preview_approval_gates_after_separate_reviewer_and_ack_events(self):
        app = self.app()
        approve = lambda: next(x for x in app.button
                               if x.label == 'Approve current evidence-linked draft')
        self.assertTrue(approve().disabled)
        self.assertEqual(len(app.text_area), 0)  # Preview is the default.
        app.text_input[0].set_value('SYNTHETIC REVIEWER').run()
        self.assertTrue(approve().disabled)  # A name alone cannot approve.
        app.checkbox[0].check().run()
        self.assertFalse(approve().disabled)
        self.assertIsNone(app.session_state.brief_snapshot['approval'])
        app.checkbox[0].uncheck().run()
        self.assertTrue(approve().disabled)
        app.text_input[0].set_value('   ').run()
        app.checkbox[0].check().run()
        self.assertTrue(approve().disabled)  # Acknowledgment alone is insufficient.
        app.text_input[0].set_value('SYNTHETIC REVIEWER').run()
        self.assertFalse(approve().disabled)
        approve().click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any('ANALYST APPROVED' in x.value for x in app.success))

    def test_invalid_weights_and_empty_upload_stop_analytics(self):
        app = self.app()
        app.number_input[1].set_value(0.0).run()
        self.assertTrue(any('resolve validation errors' in x.value for x in app.error))
        self.assertEqual(len(app.metric), 0)
        app = self.app()
        next(x for x in app.radio if x.label == 'Data source').set_value('Upload CSV').run()
        self.assertTrue(any('Upload a CSV' in x.value for x in app.info))
        self.assertEqual(len(app.metric), 0)

    def test_provider_outage_is_actionable_and_never_synthetic(self):
        app = self.app()
        with patch('market_data.download_etf_prices', side_effect=RuntimeError('TEST provider outage')):
            next(x for x in app.radio if x.label == 'Data source').set_value('Market ETF proxies').run()
        self.assertFalse(app.exception)
        self.assertTrue(any('ETF data unavailable' in x.value for x in app.error))
        self.assertEqual(len(app.metric), 0)

    def test_overview_exposures_reconcile_and_follow_notional(self):
        app = self.app()
        self.assertFalse(app.exception)
        def positions():
            return next(x.value for x in app.dataframe
                        if 'Hypothetical exposure (USD)' in x.value.columns)
        table = positions()
        self.assertEqual(len(table), 7)
        self.assertAlmostEqual(table['Target weight (%)'].sum(), 100.0)
        self.assertAlmostEqual(table['Hypothetical exposure (USD)'].sum(), 1000000.0)
        volatility = float(app.metric[2].value.rstrip('%'))
        self.assertAlmostEqual(table['Volatility contribution (pp)'].sum(), volatility, delta=.005)
        original_metrics = [x.value for x in app.metric[:4]]
        app.number_input[0].set_value(1100000).run()
        self.assertFalse(app.exception)
        self.assertAlmostEqual(positions()['Hypothetical exposure (USD)'].sum(), 1100000.0)
        self.assertEqual([x.value for x in app.metric[:4]], original_metrics)

    def test_zero_cost_mode_has_no_external_ai_controls_or_calls(self):
        with patch('briefing_workflow.generate_llm_draft') as remote:
            app = self.app()
        remote.assert_not_called()
        self.assertFalse(app.exception)
        self.assertFalse(any('API key' in x.label or 'OpenAI' in x.label for x in app.text_input))
        self.assertFalse(any('Generate AI' in x.label for x in app.button))
        self.assertTrue(any('External AI API requests are disabled' in x.value for x in app.info))


if __name__ == '__main__':
    unittest.main()
