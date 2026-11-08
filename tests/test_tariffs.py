"""Source-backed acceptance cases and calculation boundaries."""

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import re
import csv
import subprocess
import sys
import tempfile
import unittest

from kita_costs.engine import (ROOT, band_matches, evaluate_city, family_count, formula_price,
                               income_value, load_cities, load_highest_band_profile, round_money)
from kita_costs.validation import validate_dataset


class TariffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cities = {c["id"]: c for c in load_cities()}
        cls.review = json.loads((ROOT / "data/reviews/highest_band_review.json").read_text())

    def setUp(self):
        self.profile = load_highest_band_profile()

    def result(self, city_id, **updates):
        self.profile.update(updates)
        return evaluate_city(self.cities[city_id], self.profile)

    def income(self, basis, amount, period="year"):
        self.profile.update(income_mode="specified", incomes=[{"basis": basis, "period": period,
                                                              "amount_cents": amount}])

    def test_all_highest_band_results_against_independent_source_review(self):
        self.assertEqual(set(self.review["expected"]), set(self.cities))
        for city_id, expected in self.review["expected"].items():
            with self.subTest(municipality=city_id):
                row = self.result(city_id)
                self.assertEqual(row["status"], "comparable", row["reasons"])
                self.assertEqual(row["monthly_care_cents"], expected["monthly_cents"])
                self.assertEqual(row["payment_months"], expected["payment_months"])
                self.assertEqual(row["booked_weekly_minutes"], expected["weekly_minutes"])
                self.assertEqual(row["monthly_equivalent_cents"], expected["equivalent_cents"])

    def test_reference_tokens_exist_in_archived_official_sources(self):
        normalize = lambda text: re.sub(r"\s+", "", text).replace(".", "")
        for city_id, expected in self.review["expected"].items():
            source = (ROOT / "data/sources" / expected["source_id"] / "text.txt").read_text()
            for token in expected["source_tokens"]:
                with self.subTest(municipality=city_id, token=token):
                    self.assertIn(normalize(token), normalize(source))

    def test_dataset_invariants_and_archived_hashes(self):
        self.assertEqual(validate_dataset(list(self.cities.values())), [])

    def test_all_800_esslingen_supplement_cells_match_official_pdf(self):
        pages = (ROOT / "data/sources/55d9e28a62d7/text.txt").read_text().split("\f")
        city = self.cities["esslingen"]
        checked = 0
        for page_index, age in [(1, "o3"), (2, "u3")]:
            matches = [re.search(r"([1-5]) Tage?\s+(.*)", line) for line in pages[page_index].splitlines()]
            matches = [m for m in matches if m]
            self.assertEqual(len(matches), 50)
            for row_index, match in enumerate(matches):
                amounts = [int(n) * 100 for n in re.findall(r"\d+", match[2])]
                self.assertEqual(len(amounts), 8)
                for column, amount in enumerate(amounts):
                    part = next(p for p in city["components"] if p["kind"] == "care_extension" and p["age_group"] == age
                                and p["selectors"]["income_band_id"] == f"gross-{row_index // 5}"
                                and p["days_per_week"] == int(match[1]) and p["extension_minutes"] == [30, 60][column // 4]
                                and p["selectors"]["family_count"] == column % 4 + 1)
                    self.assertEqual(part["amount_cents"], amount)
                    checked += 1
        self.assertEqual(checked, 800)

    def test_evaluation_does_not_mutate_source_data_or_profile(self):
        city = deepcopy(self.cities["esslingen"])
        before = deepcopy((city, self.profile))
        first = evaluate_city(city, self.profile)
        self.assertEqual(first, evaluate_city(city, self.profile))
        self.assertEqual((city, self.profile), before)

    def test_eleven_and_twelve_months_are_not_equal(self):
        self.assertEqual(self.result("stuttgart")["monthly_equivalent_cents"], 22275)
        self.assertEqual(self.result("gerlingen")["monthly_equivalent_cents"], 64000)
        self.assertEqual(round_money(Decimal(24300) * 11 / 12), 22275)

    def test_half_cent_rounding_is_decimal_half_up(self):
        self.assertEqual(round_money(Decimal("100.5")), 101)
        self.assertEqual(round_money(Decimal("250"), "whole_euro_half_up"), 300)

    def test_fellbach_friday_blocks_a_weekly_total_only_match(self):
        row = self.result("fellbach")
        self.assertEqual(row["booked_weekly_minutes"], 2700)
        self.assertEqual(row["monthly_care_cents"], 70200)
        item = next(o for o in self.cities["fellbach"]["offers"] if o["id"] == row["offer_id"])
        self.assertEqual(item["weekday_minutes"], [555, 555, 555, 555, 480])
        self.assertNotEqual(row["monthly_care_cents"], 62400)

    def test_packages_are_not_interpolated(self):
        row = self.result("leonberg")
        self.assertEqual(row["monthly_care_cents"], 53700)
        self.assertEqual(row["extra_weekly_minutes"], 150)
        row = self.result("ditzingen")
        self.assertEqual(row["monthly_care_cents"], 63600)
        self.assertEqual(row["extra_weekly_minutes"], 300)

    def test_weekly_formula_changes_rate_for_entire_package(self):
        city = self.cities["fellbach"]
        item = next(o for o in city["offers"] if o["age_group"] == "u3")
        low, _, _ = formula_price(city, item, self.profile, 1, 2100)
        high, _, _ = formula_price(city, item, self.profile, 1, 2160)
        self.assertEqual(low, 45500)
        self.assertEqual(high, 56200)

    def test_fellbach_sibling_discount_and_minimum(self):
        city = self.cities["fellbach"]
        item = next(o for o in city["offers"] if o["age_group"] == "u3")
        amount, _, _ = formula_price(city, item, self.profile, 2, 2700)
        self.assertEqual(amount, 56200)
        self.profile.update(income_mode="specified", approved_rules=["social_income_ratio"],
                            eligibility=["approved_social_reduction", "resident", "no_priority_benefit"])
        self.income("fellbach_gross_income", 10000, "month")
        amount, _, reason = formula_price(city, item, self.profile, 4, 2700)
        self.assertIsNone(reason)
        self.assertEqual(amount, 1000)

    def test_gross_cannot_be_substituted_for_taxable_income(self):
        self.income("gross_income", 8000000)
        row = self.result("ditzingen")
        self.assertIsNone(row["monthly_equivalent_cents"])
        self.assertIn("price_or_income_input_missing", row["reasons"])

    def test_period_conversion_keeps_income_definition(self):
        self.income("taxable_income", 500000, "month")
        self.assertEqual(income_value(self.profile, "taxable_income", "year"), 6000000)
        self.assertIsNone(income_value(self.profile, "gross_income", "year"))

    def test_esslingen_exact_income_boundary(self):
        self.income("esslingen_gross_income", 5000000)
        self.assertEqual(self.result("esslingen")["monthly_care_cents"], 36600)
        self.income("esslingen_gross_income", 5000001)
        self.assertEqual(self.result("esslingen")["monthly_care_cents"], 42500)

    def test_ditzingen_literal_income_gap_remains_unknown(self):
        self.income("taxable_income", 7000100)
        self.assertIsNone(self.result("ditzingen")["monthly_equivalent_cents"])
        self.income("taxable_income", 7000101)
        self.assertEqual(self.result("ditzingen")["monthly_care_cents"], 63600)

    def test_korntal_literal_cent_gap_is_not_filled(self):
        self.income("adjusted_taxable_income", 450050, "month")
        self.assertIsNone(self.result("korntal-muenchingen")["monthly_care_cents"])

    def test_korntal_single_parent_lower_band(self):
        self.income("adjusted_taxable_income", 250000, "month")
        self.assertEqual(self.result("korntal-muenchingen")["monthly_care_cents"], 23375)
        self.assertEqual(self.result("korntal-muenchingen", single_parent=True)["monthly_care_cents"], 19250)

    def test_all_korntal_income_cells_are_preserved(self):
        self.assertEqual(len(self.cities["korntal-muenchingen"]["prices"]), 9 * 4 * 7)

    def test_family_count_and_care_rank_are_distinct(self):
        self.profile["children"].append({"age_months": 48, "resident": True, "child_benefit": True})
        first = self.result("sindelfingen", care_rank=1)
        second = self.result("sindelfingen", care_rank=2)
        self.assertEqual(first["monthly_care_cents"], 28200)
        self.assertEqual(second["monthly_care_cents"], 21150)

    def test_adult_child_count_uses_local_definition(self):
        self.profile["children"].append({"age_months": 240, "resident": True, "child_benefit": True})
        self.assertEqual(family_count(self.cities["stuttgart"], self.profile), 1)
        self.assertEqual(family_count(self.cities["gerlingen"], self.profile), 2)
        self.assertEqual(family_count(self.cities["ludwigsburg"], self.profile), 1)
        self.assertEqual(family_count(self.cities["kornwestheim"], self.profile), 2)

    def test_fourth_or_later_child_is_explicitly_free(self):
        self.profile["children"] *= 5
        row = self.result("sindelfingen", care_rank=5)
        self.assertEqual(row["status"], "comparable")
        self.assertEqual(row["monthly_care_cents"], 0)
        self.assertNotEqual(row["components"][0]["amount_cents"], 0)

    def test_exact_four_child_column_does_not_imply_five(self):
        self.profile["children"] *= 5
        self.assertIsNone(self.result("kornwestheim")["monthly_care_cents"])

    def test_missing_care_rank_is_not_assumed_to_be_first(self):
        row = self.result("sindelfingen", care_rank=None)
        self.assertIsNone(row["monthly_care_cents"])

    def test_leinfelden_uses_published_pass_price(self):
        row = self.result("leinfelden-echterdingen", pass_id="city_pass_a",
                          eligibility=["valid_city_pass", "no_priority_benefit"])
        self.assertEqual(row["monthly_care_cents"], 23490)
        self.assertNotEqual(row["monthly_care_cents"], 23488)

    def test_pass_requires_eligibility_confirmation(self):
        row = self.result("stuttgart", pass_id="family_card")
        self.assertIn("pass_eligibility_not_confirmed", row["reasons"])
        row = self.result("stuttgart", eligibility=["valid_family_card"])
        self.assertEqual(row["monthly_care_cents"], 14600)

    def test_included_infant_surcharge_is_not_added_again(self):
        self.assertEqual(self.result("stuttgart")["monthly_care_cents"], 24300)
        price_id = self.result("stuttgart")["selected_price_id"]
        row = next(p for p in self.cities["stuttgart"]["prices"] if p["id"] == price_id)
        self.assertEqual(row["included_components"][0]["amount_cents"], 7800)

    def test_multiple_u3_card_children_need_surcharge_allocation(self):
        self.profile["children"] *= 2
        row = self.result("stuttgart", pass_id="family_card", eligibility=["valid_family_card"])
        self.assertIn("infant_surcharge_allocation_required", row["reasons"])

    def test_income_reduction_is_not_applied_automatically(self):
        self.income("gerlingen_household_income", 4000000)
        self.assertEqual(self.result("gerlingen")["monthly_care_cents"], 64000)
        row = self.result("gerlingen", approved_rules=["income_reduction"], eligibility=["priority_benefits_denied"])
        self.assertEqual(row["monthly_care_cents"], 51200)

    def test_extension_price_matches_selected_days(self):
        self.profile["weekday_minutes"] = [510, 510, 510, 480, 480]
        row = self.result("esslingen")
        self.assertEqual(row["monthly_care_cents"], 121400)
        self.assertEqual(row["booked_weekly_minutes"], 2490)

    def test_esslingen_regular_and_voe_have_been_transferred(self):
        row = self.result("esslingen", weekday_minutes=[360] * 5)
        self.assertEqual(row["monthly_care_cents"], 28400)
        self.assertEqual(row["offer_label"], "VÖ6")

    def test_meal_does_not_change_primary_metric(self):
        row = self.result("ditzingen")
        self.assertEqual(row["monthly_care_cents"], 63600)
        self.assertEqual(row["total_mandatory_monthly_equivalent_cents"], 72400)

    def test_site_meal_variants_remain_separate(self):
        row = self.result("kornwestheim")
        self.assertEqual({p["amount_cents"] for p in row["components"]}, {7600, 9000})
        self.assertIsNone(row["total_mandatory_monthly_equivalent_cents"])

    def test_unknown_meal_months_do_not_produce_a_total(self):
        row = self.result("korntal-muenchingen")
        self.assertIn(8500, [p["amount_cents"] for p in row["components"]])
        self.assertIsNone(row["total_mandatory_monthly_equivalent_cents"])

    def test_unknown_primary_payment_months_blocks_only_equivalent(self):
        city = deepcopy(self.cities["stuttgart"])
        for item in city["offers"]:
            item["payment_months"] = None
        row = evaluate_city(city, self.profile)
        self.assertEqual(row["monthly_care_cents"], 24300)
        self.assertIsNone(row["monthly_equivalent_cents"])
        self.assertIn("payment_months_unknown", row["reasons"])

    def test_missing_smallest_price_is_not_replaced_with_larger_package(self):
        city = deepcopy(self.cities["stuttgart"])
        selected = self.result("stuttgart")["selected_price_id"]
        price = next(p for p in city["prices"] if p["id"] == selected)
        price.update(amount_cents=None, value_status="not_published")
        row = evaluate_city(city, self.profile)
        self.assertIsNone(row["monthly_care_cents"])
        self.assertIn("tariff_not_published", row["reasons"])

    def test_unpriced_gt11_is_not_interpolated(self):
        row = self.result("ludwigsburg", weekday_minutes=[660] * 5)
        self.assertIsNone(row["monthly_care_cents"])
        self.assertIn("tariff_not_published", row["reasons"])

    def test_future_tariff_is_opt_in_and_separate(self):
        row = self.result("ditzingen", as_of="2027-01-01")
        self.assertIn("date_not_reviewed", row["reasons"])
        row = self.result("ditzingen", allow_published_future=True)
        self.assertEqual(row["monthly_care_cents"], 68200)
        self.assertIn("55caf2cb4eb8", [e["source_id"] for e in row["evidence"]])

    def test_future_missing_gt50_does_not_reuse_old_price(self):
        row = self.result("ditzingen", as_of="2027-01-01", allow_published_future=True, weekday_minutes=[600] * 5)
        self.assertIsNone(row["monthly_care_cents"])

    def test_age_transition_requires_birthday_month_when_relevant(self):
        self.profile["children"][0]["age_months"] = 36
        self.assertIn("birthday_month_required_for_age_transition", self.result("leinfelden-echterdingen")["reasons"])
        self.profile["children"][0]["birthday_in_reference_month"] = True
        self.assertEqual(self.result("leinfelden-echterdingen")["monthly_care_cents"], 58720)
        self.profile["children"][0]["birthday_in_reference_month"] = False
        self.assertEqual(self.result("leinfelden-echterdingen")["monthly_care_cents"], 25920)

    def test_local_overrides_do_not_change_other_cities(self):
        self.profile["municipality_overrides"] = {"stuttgart": {"pass_id": "family_card", "eligibility": ["valid_family_card"]}}
        self.assertEqual(self.result("stuttgart")["monthly_care_cents"], 14600)
        self.assertEqual(self.result("ditzingen")["monthly_care_cents"], 63600)

    def test_ambiguous_duplicate_price_is_not_silently_selected(self):
        city = deepcopy(self.cities["stuttgart"])
        selected = self.result("stuttgart")["selected_price_id"]
        row = deepcopy(next(p for p in city["prices"] if p["id"] == selected))
        row["id"] = "separate-unresolved-variant"
        city["prices"].append(row)
        result = evaluate_city(city, self.profile)
        self.assertEqual(result["status"], "ambiguous")

    def test_invalid_profile_is_rejected(self):
        self.profile["weekday_minutes"] = [480, 480]
        with self.assertRaises(ValueError):
            self.result("stuttgart")

    def test_boolean_duration_is_not_an_integer_duration(self):
        self.profile["weekday_minutes"][0] = True
        with self.assertRaises(ValueError):
            self.result("stuttgart")

    def test_conflicting_monthly_and_annual_income_is_rejected(self):
        self.income("taxable_income", 6000000)
        self.profile["incomes"].append({"basis": "taxable_income", "period": "month", "amount_cents": 100000})
        with self.assertRaises(ValueError):
            self.result("ditzingen")

    def test_personal_export_cannot_overwrite_the_default_report(self):
        completed = subprocess.run([sys.executable, "-m", "kita_costs", "export", "--municipality", "stuttgart"],
                                   cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("complete default catalog", completed.stderr)

    def test_csv_preserves_cents_and_nested_selectors(self):
        from kita_costs.__main__ import write_csv
        row = next(p for p in self.cities["korntal-muenchingen"]["prices"] if p["amount_cents"] == 39875)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tariffs.csv"
            write_csv(path, [row], ["id", "amount_cents", "selectors", "evidence"])
            with path.open(newline="") as stream:
                exported = next(csv.DictReader(stream))
            self.assertEqual(int(exported["amount_cents"]), 39875)
            self.assertEqual(json.loads(exported["selectors"]), row["selectors"])
            self.assertEqual(json.loads(exported["evidence"]), row["evidence"])


if __name__ == "__main__":
    unittest.main()
