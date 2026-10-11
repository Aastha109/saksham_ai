"""
Unit and integration tests for Saksham_AI backend modules.
"""

import unittest
import os
import sys

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.tokenizer import count_tokens
from backend.cost_engine import calculate_cost, compare_all_models
from backend.efficiency_scorer import score_prompt
from backend.rewriter import heuristic_rewrite, generate_rewrite_report
from backend.model_recommender import classify_task_complexity, recommend_model
from backend.impact_estimator import estimate_environmental_impact
from backend.database import init_db, log_prompt_event, get_kpis, get_trend_data


class TestSakshamAIBackend(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_token_counting(self):
        text = "Extract the customer invoice number and date from this receipt."
        stats = count_tokens(text, "gpt-4o")
        self.assertGreater(stats["token_count"], 5)
        self.assertEqual(stats["word_count"], 10)
        self.assertTrue(stats["tokens_per_word"] > 0)

    def test_cost_calculation(self):
        cost_4o = calculate_cost(input_tokens=1000, model_key="gpt-4o", expected_output_tokens=500)
        cost_mini = calculate_cost(input_tokens=1000, model_key="gpt-4o-mini", expected_output_tokens=500)
        
        # GPT-4o input: $2.50/M, output: $10.00/M -> 1000*2.5e-6 + 500*10e-6 = 0.0025 + 0.0050 = 0.0075
        self.assertAlmostEqual(cost_4o["total_cost_estimate_usd"], 0.0075, places=5)
        # GPT-4o-mini should be significantly cheaper
        self.assertLess(cost_mini["total_cost_estimate_usd"], cost_4o["total_cost_estimate_usd"])

    def test_efficiency_scorer_penalizes_fillers(self):
        bad_prompt = "Hello please kindly can you help me write something good thank you so much in advance"
        good_prompt = "Extract the top 5 customer complaints from the attached reviews. Format as a markdown table with columns: ID, Complaint, Severity."
        
        bad_eval = score_prompt(bad_prompt)
        good_eval = score_prompt(good_prompt)

        self.assertLess(bad_eval["score"], 60)
        self.assertGreater(good_eval["score"], 80)
        # Verify filler issue was flagged
        codes = [i["code"] for i in bad_eval["issues"]]
        self.assertIn("FILLER_PHRASES", codes)

    def test_heuristic_rewriter(self):
        bloated = "Please kindly help me extract the dates from this document and make sure you return JSON thank you."
        report = generate_rewrite_report(bloated, "gpt-4o")
        
        self.assertLess(report["tokens_rewritten"], report["tokens_original"])
        self.assertGreater(report["pct_token_reduction"], 15.0)
        self.assertGreater(len(report["diff_stream"]), 0)

    def test_model_recommender(self):
        simple_task = "Extract JSON keys from this text: { 'id': 101 }"
        rec = recommend_model(simple_task, current_model="gpt-4o", input_tokens=30)
        
        self.assertEqual(rec["task_complexity"], "simple")
        self.assertEqual(rec["recommended_model"], "gpt-4o-mini")
        self.assertTrue(rec["is_downgrade_recommended"])
        self.assertGreater(rec["pct_cost_saved"], 80.0)

    def test_impact_estimator(self):
        impact = estimate_environmental_impact(total_tokens=5000, model_tier="flagship")
        self.assertGreater(impact["energy_consumption_wh"]["estimate"], 0)
        self.assertGreater(impact["carbon_footprint_g"]["estimate"], 0)
        self.assertGreater(len(impact["citations"]), 1)

    def test_database_logging_and_kpis(self):
        log_id = log_prompt_event(
            prompt="Test automated prompt verification",
            rewritten_prompt="Test automated verification",
            model_used="gpt-4o",
            recommended_model="gpt-4o-mini",
            task_category="simple",
            input_tokens=10,
            output_tokens=20,
            cost_usd=0.0002,
            savings_usd=0.00018,
            efficiency_score=92,
            carbon_g=0.04
        )
        self.assertGreater(log_id, 0)
        
        kpis = get_kpis()
        self.assertGreater(kpis["total_prompts"], 0)
        self.assertGreater(kpis["avg_efficiency_score"], 0)


if __name__ == "__main__":
    unittest.main()
