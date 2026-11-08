"""Shared input scenarios have independent acceptance assertions in both runtimes."""

from copy import deepcopy
import unittest

from kita_costs.engine import create_personal_profile, load_default_profile, normalize_profile
from scripts.evaluate_reference_cases import evaluate_cases, load_cases


class ReferenceCaseTests(unittest.TestCase):
    def test_shared_cases_meet_declared_expectations(self):
        results = {result["id"]: result for result in evaluate_cases()}
        for case in load_cases():
            with self.subTest(case=case["id"]):
                record = results[case["id"]]
                if "expected_error" in case:
                    self.assertEqual(record.get("error"), case["expected_error"])
                    continue
                self.assertNotIn("error", record)
                result = record["result"]
                if "expected_value" in case:
                    self.assertEqual(result, case["expected_value"])
                if "expected_amount" in case:
                    self.assertEqual(result[0], case["expected_amount"])
                if "expected" in case:
                    row = result[0] if case.get("operation", "compare") == "compare" else result
                    for key, value in case["expected"].items():
                        if key == "reasons_include":
                            self.assertTrue(set(value).issubset(row["reasons"]), row["reasons"])
                        else:
                            self.assertEqual(row[key], value, key)

    def test_personal_profile_keeps_family_but_removes_all_model_income(self):
        model = load_default_profile()
        before = deepcopy(model)
        personal = create_personal_profile(model)
        self.assertEqual(model, before)
        self.assertEqual(personal["children"], model["children"])
        self.assertEqual(personal["weekday_minutes"], model["weekday_minutes"])
        self.assertEqual(personal["incomes"], [])
        self.assertEqual(personal["income_mode"], "specified")
        self.assertNotIn("model_income_snapshot", personal)
        self.assertNotIn("municipality_overrides", personal)

    def test_normalization_returns_independent_state(self):
        model = load_default_profile()
        normalized = normalize_profile(model)
        normalized["children"][0]["age_months"] = 48
        self.assertEqual(model["children"][0]["age_months"], 24)


if __name__ == "__main__":
    unittest.main()
