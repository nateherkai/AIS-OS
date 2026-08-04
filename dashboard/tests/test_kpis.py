import os
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("BRIDGE_TOKEN", "test-token")
os.environ.setdefault("EXPO_PUBLIC_SUPABASE_URL", "https://example.invalid")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import server


class KpiCalculationTests(unittest.TestCase):
    def test_explicit_curated_zero_does_not_fall_back_to_expense_rows(self):
        self.assertEqual(
            server.curated_monthly_burn({
                "monthly_charges_curated": 0,
                "expenses": [{"amount": 1781.48}],
            }),
            0,
        )

    def test_kpis_use_curated_burn_for_net(self):
        schools = [
            {"name": "Elite", "subscription_status": "active", "subscription_tier": "enterprise"},
            {"name": "Trial", "subscription_status": "trialing", "subscription_tier": None},
        ]
        summary = {
            "paid_count": 1,
            "trial_count": 1,
            "paid": schools[:1],
            "trials": schools[1:],
            "school_goal": 50,
            "goal_date": "August 2026",
        }
        with patch.object(server, "get_schools", return_value=schools), \
             patch.object(server, "get_pipeline_summary", return_value=summary):
            result = server.kpis()

        self.assertEqual(result["monthly_burn"], 373.39)
        self.assertEqual(result["net"], round(result["monthly_revenue"] - 373.39, 2))


if __name__ == "__main__":
    unittest.main()
