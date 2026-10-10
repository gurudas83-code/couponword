"""Cross-budget review must not silently become a fresh-price assertion."""
import unittest
from phase_e_gate3_api import check_budget_coverage


class BudgetCoverageAuditTests(unittest.TestCase):
    def run_row(self, budget, asin, score):
        return {'budget': budget, 'query': f'mobile under {budget}', 'payload': {
            'recommendations': [{'asin': asin, 'fit_percent': score, 'price': 9000}],
            'fit_diagnostics': []}}

    def test_missing_stronger_pick_requires_review_not_automatic_admission(self):
        rows = [self.run_row(10000, 'fixture-a', 62), self.run_row(20000, 'fixture-b', 51)]
        result = check_budget_coverage(rows)
        self.assertEqual(result['status'], 'REVIEW_REQUIRED')
        self.assertTrue(result['issues'][0]['current_price_and_identity_require_revalidation'])
        self.assertEqual(result['market_quality'], 'NOT_VERIFIED')

    def test_current_ineligibility_explains_omission(self):
        rows = [self.run_row(10000, 'fixture-a', 62), self.run_row(20000, 'fixture-b', 51)]
        rows[1]['payload']['fit_diagnostics'] = [{'profile_asin': 'fixture-a', 'eligible': False,
                                                'fit_percent': 62, 'hard_constraint_failures': ['stale price']}]
        self.assertEqual(check_budget_coverage(rows)['issues'], [])

    def test_evaluated_eligible_stronger_pick_is_selection_review(self):
        rows = [self.run_row(10000, 'fixture-a', 62), self.run_row(20000, 'fixture-b', 51)]
        rows[1]['payload']['fit_diagnostics'] = [{'profile_asin': 'fixture-a', 'eligible': True,
                                                'fit_percent': 62, 'hard_constraint_failures': []}]
        self.assertEqual(check_budget_coverage(rows)['issues'][0]['kind'], 'selection_review')

    def test_better_replacement_tie_and_brand_query_not_false_failures(self):
        for score in (62, 70):
            rows = [self.run_row(10000, 'fixture-a', 62), self.run_row(20000, 'fixture-b', score)]
            self.assertEqual(check_budget_coverage(rows)['issues'], [])
        rows[1]['query'] = 'Samsung phone under 20000'
        rows[1]['payload']['recommendations'][0]['fit_percent'] = 51
        self.assertEqual(check_budget_coverage(rows)['issues'], [])

    def test_lower_current_score_explains_replacement(self):
        rows = [self.run_row(10000, 'fixture-a', 62), self.run_row(20000, 'fixture-b', 51)]
        rows[1]['payload']['fit_diagnostics'] = [{'profile_asin': 'fixture-a', 'eligible': True,
                                                'fit_percent': 50, 'hard_constraint_failures': []}]
        self.assertEqual(check_budget_coverage(rows)['issues'], [])


if __name__ == '__main__':
    unittest.main()
