"""Mocked external AI contract: no credentials or network calls."""
import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from briefing_workflow import generate_llm_draft, rules_based_draft, validate_draft_evidence, approve_brief

class AiBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.evidence={'observations':{f'E{i:02}':f'Deterministic fact {i}' for i in range(1,12)},
                       'methodology':'Test fixture, not market evidence','unrounded_input_sha256':'a'*64}

    def test_payload_contains_only_curated_evidence_no_key_or_raw_series(self):
        constructor=MagicMock()
        constructor.return_value.responses.create.return_value=SimpleNamespace(output_text=rules_based_draft(self.evidence))
        with patch.dict(sys.modules,{'openai':SimpleNamespace(OpenAI=constructor)}):
            text=generate_llm_draft(self.evidence,'TEST-ONLY-KEY')
        constructor.assert_called_once_with(api_key='TEST-ONLY-KEY',timeout=25.,max_retries=0)
        call=constructor.return_value.responses.create.call_args.kwargs
        self.assertEqual(json.loads(call['input']),self.evidence)
        self.assertNotIn('TEST-ONLY-KEY',call['input'])
        self.assertEqual(validate_draft_evidence(text,self.evidence),[])

    def test_empty_refusal_and_provider_failure_never_create_approval(self):
        constructor=MagicMock()
        with patch.dict(sys.modules,{'openai':SimpleNamespace(OpenAI=constructor)}):
            constructor.return_value.responses.create.return_value=SimpleNamespace(output_text='  ')
            with self.assertRaisesRegex(ValueError,'empty'): generate_llm_draft(self.evidence,'TEST')
            constructor.return_value.responses.create.return_value=SimpleNamespace(output_text='I cannot provide this analysis.')
            refusal=generate_llm_draft(self.evidence,'TEST')
            with self.assertRaisesRegex(ValueError,'citation gate'): approve_brief(refusal,self.evidence,'Tester',True)
            constructor.return_value.responses.create.side_effect=TimeoutError('TEST timeout')
            with self.assertRaises(TimeoutError): generate_llm_draft(self.evidence,'TEST')

    def test_valid_citations_are_not_a_truth_checker(self):
        # Document the deliberate boundary: a fabricated claim with valid IDs can
        # pass the structural gate. Human claim review is mandatory.
        fabricated=rules_based_draft(self.evidence).replace('Deterministic fact 3','Guaranteed future return 999%')
        self.assertEqual(validate_draft_evidence(fabricated,self.evidence),[])
        with self.assertRaisesRegex(ValueError,'Explicit'):
            approve_brief(fabricated,self.evidence,'Tester',False)

if __name__=='__main__': unittest.main()
