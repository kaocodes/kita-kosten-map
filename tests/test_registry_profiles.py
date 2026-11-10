"""Acceptance checks for extensible geography and independent reference profiles."""

from copy import deepcopy
import json
import re
import subprocess
import sys
import unittest

from kita_costs.engine import (ROOT, compare_municipalities, evaluate_city, load_cities,
                               load_default_profile, load_highest_band_profile, validate_profile)
from kita_costs.registry import active_municipalities, load_registry, validate_registry
from kita_costs.validation import validate_dataset


class RegistryProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs = load_cities()
        cls.cities = {city["id"]: city for city in cls.catalogs}
        cls.model_review = json.loads((ROOT / "data/reviews/model_family_review.json").read_text())
        cls.highest_review = json.loads((ROOT / "data/reviews/highest_band_review.json").read_text())

    def setUp(self):
        self.registry = load_registry()
        self.profile = load_default_profile()

    def extra_municipality(self, tariff_id="test-municipality"):
        # Use a context feature only as test geography; no real fee data is added.
        reference = self.registry["geometry_reference"]
        features = json.loads((ROOT / reference["path"]).read_text())["features"]
        used = {entry["ags"] for entry in self.registry["municipalities"]}
        feature = next(f for f in features if f["properties"]["ags"] not in used)
        ags = feature["properties"]["ags"]
        entry = {"id": "test-municipality", "name": feature["properties"]["gen"], "ags": ags,
                 "active": True, "region_id": "test-region", "tariff_id": tariff_id,
                 "area_id": "municipality-" + ags}
        area = {"id": entry["area_id"], "kind": "municipality", "municipality_id": entry["id"],
                "parent_id": None, "tariff_id": tariff_id, "geometry_key": ags}
        self.registry["municipalities"].append(entry)
        self.registry["areas"].append(area)
        return entry

    def test_model_family_matches_all_independent_reference_cells(self):
        expected_rows = self.model_review["expected"]
        self.assertEqual(self.profile["id"], self.model_review["profile_id"])
        self.assertTrue(set(expected_rows) <= {entry["id"] for entry in active_municipalities(self.registry)})
        for row in compare_municipalities(self.catalogs, self.profile, self.registry):
            if row["municipality_id"] not in expected_rows:
                continue  # Expansion references have their own source acceptance suite.
            expected = expected_rows[row["municipality_id"]]
            with self.subTest(municipality=row["municipality_id"]):
                self.assertEqual(row["status"], "comparable", row["reasons"])
                self.assertEqual(row["monthly_care_cents"], expected["monthly_cents"])
                self.assertEqual(row["payment_months"], expected["payment_months"])
                self.assertEqual(row["booked_weekly_minutes"], expected["weekly_minutes"])
                self.assertEqual(row["monthly_equivalent_cents"], expected["equivalent_cents"])
                self.assertIn(expected["source_id"], {ref["source_id"] for ref in row["evidence"]})

    def test_model_reference_tokens_exist_in_archived_sources(self):
        normalize = lambda text: re.sub(r"\s+", "", text).replace(".", "")
        for city_id, expected in self.model_review["expected"].items():
            source = (ROOT / "data/sources" / expected["source_id"] / "text.txt").read_text()
            for token in expected["source_tokens"]:
                with self.subTest(municipality=city_id, token=token):
                    self.assertIn(normalize(token), normalize(source))

    def test_highest_band_profile_preserves_every_previous_reference(self):
        results = compare_municipalities(self.catalogs, load_highest_band_profile(), self.registry)
        for row in results:
            if row["municipality_id"] not in self.highest_review["expected"]:
                continue
            with self.subTest(municipality=row["municipality_id"]):
                self.assertEqual(row["monthly_equivalent_cents"],
                                 self.highest_review["expected"][row["municipality_id"]]["equivalent_cents"])

    def test_thirteenth_registered_municipality_needs_only_data(self):
        before = compare_municipalities(self.catalogs, self.profile, self.registry)
        entry = self.extra_municipality()
        city = deepcopy(self.cities["boeblingen"])
        city.update(id=entry["id"], name=entry["name"])
        catalogs = self.catalogs + [city]
        self.assertEqual(validate_dataset(catalogs, registry=self.registry), [])
        after = compare_municipalities(catalogs, self.profile, self.registry)
        self.assertEqual(after[:-1], before)
        self.assertEqual(after[-1]["municipality_id"], entry["id"])
        self.assertEqual(after[-1]["ags"], entry["ags"])
        self.assertEqual(after[-1]["monthly_care_cents"], 31000)

    def test_equal_record_count_does_not_hide_a_missing_municipality(self):
        cities = deepcopy(self.catalogs)
        cities[0]["id"] = "unregistered-municipality"
        errors = validate_dataset(cities, registry=self.registry)
        self.assertTrue(any("Missing tariff catalog" in error for error in errors))
        self.assertTrue(any("Unregistered tariff catalog" in error for error in errors))

    def test_inactive_municipality_is_not_compared_and_need_not_have_tariffs(self):
        entry = self.registry["municipalities"][0]
        entry["active"] = False
        catalogs = [city for city in self.catalogs if city["id"] != entry["tariff_id"]]
        self.assertEqual(validate_dataset(catalogs, registry=self.registry), [])
        results = compare_municipalities(catalogs, self.profile, self.registry)
        self.assertNotIn(entry["id"], {row["municipality_id"] for row in results})
        with self.assertRaisesRegex(ValueError, "inactive"):
            compare_municipalities(catalogs, self.profile, self.registry, entry["id"])

    def test_duplicate_ags_is_rejected(self):
        self.registry["municipalities"][1]["ags"] = self.registry["municipalities"][0]["ags"]
        errors = validate_registry(self.registry, self.catalogs)
        self.assertTrue(any("Duplicate municipal AGS" in error for error in errors))

    def test_ags_preserves_leading_zero_and_rejects_integer(self):
        entry = self.registry["municipalities"][0]
        self.assertTrue(entry["ags"].startswith("0"))
        entry["ags"] = int(entry["ags"])
        self.assertTrue(any("eight-digit string" in error for error in validate_registry(self.registry, self.catalogs)))

    def test_wrong_ags_name_assignment_is_rejected(self):
        # Swap two complete keys, preserving uniqueness and feature counts.
        first, second = self.registry["municipalities"][:2]
        first["ags"], second["ags"] = second["ags"], first["ags"]
        for entry in (first, second):
            area = next(area for area in self.registry["areas"] if area["id"] == entry["area_id"])
            area["geometry_key"] = entry["ags"]
        self.assertTrue(any("Official name differs" in error for error in validate_registry(self.registry, self.catalogs)))

    def test_changed_archived_geometry_hash_is_rejected(self):
        self.registry["geometry_reference"]["sha256"] = "0" * 64
        self.assertTrue(any("stored hash" in error for error in validate_registry(self.registry, self.catalogs)))

    def test_unknown_area_geometry_is_rejected(self):
        self.registry["areas"][0]["geometry_key"] = "00000000"
        self.assertTrue(any("exactly one archived feature" in error
                            for error in validate_registry(self.registry, self.catalogs)))

    def test_area_must_use_its_municipal_tariff(self):
        self.registry["areas"][0]["tariff_id"] = "unknown-tariff"
        self.assertTrue(any("Area tariff differs" in error for error in validate_registry(self.registry, self.catalogs)))

    def test_district_reuses_tariff_without_adding_a_catalog(self):
        entry = self.registry["municipalities"][0]
        # This synthetic area exercises references, not a real district boundary.
        self.registry["areas"].append({
            "id": "test-district", "kind": "district", "municipality_id": entry["id"],
            "parent_id": entry["area_id"], "tariff_id": entry["tariff_id"], "geometry_key": entry["ags"]})
        self.assertEqual(validate_registry(self.registry, self.catalogs), [])
        self.assertEqual(len(compare_municipalities(self.catalogs, self.profile, self.registry)),
                         len(active_municipalities(self.registry)))
        self.registry["areas"][-1]["parent_id"] = "unknown-area"
        self.assertTrue(any("District must reference" in error for error in validate_registry(self.registry, self.catalogs)))

    def test_shared_tariff_keeps_geographic_identity_and_local_inputs(self):
        entry = self.extra_municipality(tariff_id="stuttgart")
        self.assertEqual(validate_registry(self.registry, self.catalogs), [])
        self.profile["municipality_overrides"] = {
            entry["id"]: {"pass_id": "family_card", "eligibility": ["valid_family_card"]}}
        results = {row["municipality_id"]: row for row in
                   compare_municipalities(self.catalogs, self.profile, self.registry)}
        self.assertEqual(results[entry["id"]]["monthly_care_cents"], 14600)
        self.assertEqual(results["stuttgart"]["monthly_care_cents"], 24300)
        self.assertEqual(results[entry["id"]]["municipality"], entry["name"])
        self.assertEqual(results[entry["id"]]["tariff_id"], "stuttgart")

    def test_gross_or_taxable_edit_cannot_retain_model_income_assumptions(self):
        for basis in ("gross_income", "taxable_income", "esslingen_gross_income", "adjusted_taxable_income"):
            with self.subTest(basis=basis):
                profile = load_default_profile()
                next(income for income in profile["incomes"] if income["basis"] == basis)["amount_cents"] += 100
                with self.assertRaisesRegex(ValueError, "Model income assumptions have changed"):
                    evaluate_city(self.cities["ditzingen"], profile)

    def test_personal_gross_income_does_not_fill_local_or_taxable_inputs(self):
        profile = load_highest_band_profile()
        profile.update(income_mode="specified", incomes=[
            {"basis": "gross_income", "period": "year", "amount_cents": 8000000}])
        for city_id in ("ditzingen", "esslingen", "korntal-muenchingen"):
            with self.subTest(municipality=city_id):
                result = evaluate_city(self.cities[city_id], profile)
                self.assertIsNone(result["monthly_equivalent_cents"])
                self.assertIn("price_or_income_input_missing", result["reasons"])

    def test_local_income_cannot_keep_changed_model_conditions(self):
        self.profile["assumptions"]["no_letting_losses"] = False
        with self.assertRaisesRegex(ValueError, "Model income assumptions have changed"):
            validate_profile(self.profile)

    def test_explicit_local_income_replaces_only_that_municipalitys_model_inputs(self):
        self.profile["municipality_overrides"] = {"esslingen": {"incomes": [
            {"basis": "esslingen_gross_income", "period": "year", "amount_cents": 5000000}]}}
        results = {row["municipality_id"]: row for row in
                   compare_municipalities(self.catalogs, self.profile, self.registry)}
        self.assertEqual(results["esslingen"]["monthly_care_cents"], 36600)
        self.assertEqual(results["ditzingen"]["monthly_care_cents"], 57800)

    def test_conflicting_household_information_is_rejected(self):
        self.profile["single_parent"] = True
        with self.assertRaisesRegex(ValueError, "household composition"):
            validate_profile(self.profile)

    def test_comparison_does_not_mutate_registry_catalogs_or_profile(self):
        before = deepcopy((self.registry, self.catalogs, self.profile))
        first = compare_municipalities(self.catalogs, self.profile, self.registry)
        self.assertEqual(first, compare_municipalities(self.catalogs, self.profile, self.registry))
        self.assertEqual((self.registry, self.catalogs, self.profile), before)

    def test_cli_uses_model_default_and_can_select_highest_band(self):
        for arguments, expected in [([], 55100), (["--profile", "data/profiles/highest_band.json"], 117000)]:
            with self.subTest(arguments=arguments):
                completed = subprocess.run([sys.executable, "-m", "kita_costs", "compare", "--municipality",
                                            "esslingen", *arguments], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                rows = json.loads(completed.stdout)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["monthly_care_cents"], expected)
                self.assertEqual(rows[0]["ags"], "08116019")


if __name__ == "__main__":
    unittest.main()
