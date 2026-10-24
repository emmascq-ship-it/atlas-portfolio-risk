"""Archived synthetic assessment must not inherit a moving wall-clock age."""
import copy
import unittest
from unittest.mock import patch
from risk_engine import generate_synthetic_prices,DEFAULT_WEIGHTS,SCENARIOS
from research_packet import generate_packet
from static_dashboard import dashboard_payload,render_html

class SnapshotReproducibilityTests(unittest.TestCase):
    def test_report_age_changes_cannot_change_synthetic_html(self):
        prices=generate_synthetic_prices()
        packet=generate_packet(prices,DEFAULT_WEIGHTS,class_shocks=SCENARIOS['Equity selloff'])
        outputs=[]
        for age in (1,200):
            changed=copy.deepcopy(packet)
            changed['data_quality']['days_since_last_observation']=age
            changed['data_quality']['review_flags']=['Moving live freshness flag']
            with patch('static_dashboard.generate_packet',return_value=changed):
                payload=dashboard_payload(prices)
                outputs.append(render_html(payload))
            self.assertEqual(payload['quality']['assessment_as_of'],'2026-10-21')
            self.assertEqual(payload['quality']['days_since_last_observation'],0)
            self.assertNotIn('Moving live freshness flag',payload['quality']['review_flags'])
        self.assertEqual(outputs[0],outputs[1])
