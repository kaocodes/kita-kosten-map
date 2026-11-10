"""Acceptance and rejection checks for the offline expansion compatibility review."""

import base64
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

from kita_costs.engine import evaluate_city, load_default_profile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("compatibility_review",ROOT/"scripts/review_expansion_compatibility.py")
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ExpansionCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review=audit.read(ROOT/"data/expansion/calculation_review.json")
        cls.policy=audit.read(ROOT/"data/reviews/expansion_compatibility_policy.json")
        cls.research={m["id"]:m for m in audit.read(ROOT/"data/research/neighbor_expansion_2026-11-10.json")["municipalities"]}
        cls.cities={p.stem:audit.read(p) for p in (ROOT/"data/expansion/municipalities").glob("*.json")}
        cls.default=audit.read(ROOT/"data/models/configuration.json")["default"]

    def test_review_is_bound_to_current_inputs_and_engines(self):
        for path,expected in self.review["input_sha256"].items():
            with self.subTest(path=path):self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),expected)
        for field in ["engine_changed","production_registry_changed","website_activated"]:
            self.assertFalse(self.review[field])
        self.assertTrue(self.review["publication_requires_enforcing_review_index"])

    def test_case_groups_partition_the_entire_reviewed_space(self):
        count=self.review["configuration_space"]["configurations_per_municipality"]
        self.assertEqual(count,2508)
        self.assertEqual(self.review["verification"]["family_probes"],33*count)
        self.assertEqual(self.review["verification"]["cross_engine_primitive_probes"],15840)
        self.assertEqual(self.review["verification"]["order_reversal_mismatches"],0)
        for city in self.review["municipalities"]:
            with self.subTest(city=city["id"]):
                mask=base64.b64decode(city["supported_scenarios_bitset_base64"],validate=True)
                allowed={i for i in range(count) if mask[i//8] & (1<<(i%8))}
                blocked=set()
                for group in city["unavailable_groups"]:
                    self.assertTrue(group["reasons"])
                    for low,high in group["scenario_index_ranges_inclusive"]:
                        indices=set(range(low,high+1))
                        self.assertFalse(indices & (allowed|blocked))
                        blocked|=indices
                self.assertEqual(allowed|blocked,set(range(count)))
                self.assertEqual(len(blocked),city["care_status_counts"].get("unavailable",0))

    def test_independent_acceptance_cases_have_matching_status(self):
        references=audit.read(ROOT/"data/reviews/expansion_calculation_cases.json")
        checked={r["id"]:r["status"] for r in self.review["verification"]["source_reference_results"]}
        for case in references["cases"]:
            household,income,*children=case["scenario_id"].split("|")
            selection={"household":household,"income_id":income,
                "children":[{"category":p.split(":")[0],"daily_minutes":int(p.split(":")[1])} for p in children]}
            result=audit.configuration_status(self.review,case["municipality_id"],selection)
            self.assertEqual(result["status"],case["expected"]["status"],case["id"])
            self.assertTrue(set(case["required_reasons"])<=set(result["reasons"]),case["id"])
            self.assertEqual(checked[case["id"]],"passed")

    def test_unavailable_defaults_never_become_zero_or_retain_old_prices(self):
        for city in self.review["municipalities"]:
            row=city["default_result"]
            if row["status"]=="unavailable":
                self.assertTrue(row["reasons"])
                for field in ["monthly_care_cents","annual_care_cents","monthly_equivalent_cents"]:
                    self.assertIsNone(row[field])
        for city_id in self.cities:
            selection={**self.default,"children":[{"category":"home","daily_minutes":360}]}
            self.assertEqual(audit.configuration_status(self.review,city_id,selection)["status"],"comparable")

    def test_unsupported_inputs_are_denied_and_order_does_not_change_status(self):
        outside=deepcopy(self.default)
        outside["children"]*=5
        self.assertEqual(audit.configuration_status(self.review,"aidlingen",outside)["status"],"unavailable")
        for selection in [{**self.default,"income_id":"unreviewed-income"},{**self.default,"pass_id":"city_pass"}]:
            self.assertEqual(audit.configuration_status(self.review,"aidlingen",selection)["status"],"unavailable")
        selection={**self.default,"children":[{"category":"nursery","daily_minutes":480},{"category":"kindergarten","daily_minutes":360},{"category":"home","daily_minutes":480}]}
        for city_id in self.cities:
            first=audit.configuration_status(self.review,city_id,selection)
            second=audit.configuration_status(self.review,city_id,{**selection,"children":list(reversed(selection["children"]))})
            self.assertEqual(first,second)

    def raw_single_child(self,city_id,selection):
        profile=load_default_profile()
        profile.update(as_of="2026-11-10",care_rank=1,weekday_minutes=[selection["children"][0]["daily_minutes"]]*5,
            single_parent=selection["household"]=="single",household={"parent_count":1 if selection["household"]=="single" else 2,"parents_living_together":selection["household"]!="single"})
        profile["children"]=[{"age_months":24,"resident":True,"child_benefit":True}]
        child=evaluate_city(self.cities[city_id],profile)
        raw={**audit.compact_result(child),"care_child_count":1,"children":[{"index":0,"category":"nursery","daily_minutes":selection["children"][0]["daily_minutes"],"in_care":True,"result":audit.compact_result(child)}]}
        case={"selection":selection,"profile":profile}
        return child,audit.review_result(self.cities[city_id],case,raw,self.policy["entries"].get(city_id,{}),self.research[city_id])

    def test_known_meal_amount_does_not_escape_as_care_only(self):
        native,reviewed=self.raw_single_child("aichwald",self.default)
        self.assertEqual(native["monthly_care_cents"],75350)
        self.assertEqual(reviewed["status"],"unavailable")
        self.assertIn("known_included_meal_not_separated",reviewed["reasons"])
        self.assertIsNone(reviewed["monthly_equivalent_cents"])

    def test_schwieberdingen_does_not_silently_ignore_single_parent_shift(self):
        native,ordinary=self.raw_single_child("schwieberdingen",self.default)
        self.assertEqual(native["monthly_care_cents"],55900)
        self.assertEqual(ordinary["status"],"comparable")
        native,reviewed=self.raw_single_child("schwieberdingen",{**self.default,"household":"single"})
        self.assertEqual(native["monthly_care_cents"],55900)
        self.assertEqual(reviewed["status"],"unavailable")
        self.assertIn("single_parent_band_shift_not_applied",reviewed["reasons"])

    def test_native_result_is_not_replaced_by_a_smaller_unverified_package(self):
        native,reviewed=self.raw_single_child("waldenbuch",self.default)
        self.assertEqual(native["monthly_care_cents"],76400)
        self.assertEqual(reviewed["status"],"unavailable")
        self.assertIn("smaller_offer_schedule_unverified",reviewed["reasons"])


if __name__=="__main__":unittest.main()
