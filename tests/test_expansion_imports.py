"""Source acceptance and isolation checks for the 33 normalized import catalogs."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("expansion_validation", ROOT / "scripts/validate_expansion_catalogs.py")
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


class ExpansionImportsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cities = {p.stem:json.loads(p.read_text()) for p in (ROOT / "data/expansion/municipalities").glob("*.json")}
        cls.research = json.loads((ROOT / "data/research/neighbor_expansion_2026-11-10.json").read_text())

    def test_schema_references_hashes_and_registry_isolation(self):
        self.assertEqual(validation.validate_imports(list(self.cities.values())), [])

    def test_manifest_matches_catalogs_and_inputs(self):
        manifest=json.loads((ROOT / "data/expansion/manifest.json").read_text())
        self.assertEqual(len(manifest["municipalities"]),33)
        self.assertEqual(manifest["research_sha256"],hashlib.sha256((ROOT / manifest["research_path"]).read_bytes()).hexdigest())
        for item in manifest["municipalities"]:
            self.assertEqual(item["sha256"],hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest())
        for field in ["production_registry_changed","calculation_engine_changed","website_activated"]:
            self.assertFalse(manifest[field])

    def test_existing_independent_research_control_cells_survive(self):
        for record in self.research["municipalities"]:
            with self.subTest(municipality=record["id"]):
                reference=record["reference_price"]
                city=self.cities[record["id"]]
                matched=any(p["amount_cents"]==reference["amount_cents"] and p["evidence"]["source_id"]==reference["source_id"] for p in city["prices"])
                if not matched:
                    matched=any(o.get("formula",{}).get("maximum_monthly_cents")==reference["amount_cents"] and o["evidence"]["source_id"]==reference["source_id"] for o in city["offers"] if o.get("formula"))
                self.assertTrue(matched,"Original control price disappeared during normalization")

    def test_all_ostfildern_cells_match_original_pdf_text(self):
        city=self.cities["ostfildern"]
        pages=(ROOT / "data/sources/af550fae0296/text.txt").read_text().split("\f")
        expected={}
        for index in range(9,17):
            rows=[re.findall(r"(\d+)\s*€",line) for line in pages[index].splitlines()]
            rows=[r for r in rows if len(r)==5]
            self.assertEqual(len(rows),48)
            age="o3" if index<13 else "u3"
            year=2026+(index-9)%4
            for row_index,row in enumerate(rows):
                for col,hours in enumerate([30,35,40,45,50]):
                    expected[age,year,hours,row_index//4+1,row_index%4+1]=int(row[col])*100
        offers={o["id"]:o for o in city["offers"]}
        bands={b["id"]:int(re.search(r"Stufe (\d+)",b["original_label"])[1]) for b in city["income_bands"]}
        actual={}
        for price in city["prices"]:
            offer=offers[price["offer_id"]]
            actual[offer["age_group"],int(offer["valid_from"][:4]),offer["weekly_minutes"]//60,bands[price["selectors"]["income_band_id"]],price["selectors"]["family_count"]]=price["amount_cents"]
        self.assertEqual(actual,expected)

    def test_meal_and_billing_decisions_are_preserved(self):
        freiberg=self.cities["freiberg"]
        self.assertEqual({o["payment_months"] for o in freiberg["offers"] if o["age_group"]=="u3"},{12})
        self.assertEqual({o["payment_months"] for o in freiberg["offers"] if o["age_group"]=="o3"},{11})
        aichwald=self.cities["aichwald"]
        row=next(p for p in aichwald["prices"] if p["amount_cents"]==75350)
        self.assertEqual(row["care_only_amount_cents"],70050)
        self.assertEqual(row["normalization"]["deduction_cents"],5300)
        waiblingen=self.cities["waiblingen"]
        included=[c for c in waiblingen["components"] if c.get("inclusion")=="included"]
        self.assertTrue(included)
        self.assertTrue(all(c["amount_cents"] is None and c["additional_charge"] is False for c in included))
        self.assertTrue(all(o["formula"]["income_cap_cents"]==12000000 for o in waiblingen["offers"]))

    def test_unresolved_schwieberdingen_cases_stay_unavailable(self):
        city=self.cities["schwieberdingen"]
        self.assertTrue(all(o["payment_months"]==11 and o["payment_evidence"]["provenance"]=="user_instruction" for o in city["offers"]))
        unavailable=city["coverage"]["unavailable_configurations"]
        self.assertEqual({r["result_status"] for r in unavailable},{"unavailable"})
        self.assertTrue(any(r["id"]=="o3_rank_changes_family_total" for r in unavailable))
        family_rule=next(r for r in city["rules"] if r["kind"]=="family_rules")
        self.assertEqual(family_rule["execution_status"],"documented_not_implemented")
        self.assertEqual(family_rule["parameters"]["u3"]["combination"],"sum_condition_shifts")

    def test_no_fictitious_schedules_or_silent_future_price_correction(self):
        benningen=self.cities["benningen"]
        self.assertTrue(all(o["weekday_minutes"] is None for o in benningen["offers"] if "VÖ" in o["original_label"]))
        self.assertTrue(all(o["weekly_minutes"]<=2100 for o in self.cities["baltmannsweiler"]["offers"] if o["age_group"]=="u3"))
        asperg=self.cities["asperg"]
        offer=next(o for o in asperg["offers"] if o["original_label"]=="GT9,5 an 3 Tagen" and o["valid_from"]=="2027-09-01")
        price=next(p for p in asperg["prices"] if p["offer_id"]==offer["id"] and p["selectors"]["family_count"]==4)
        self.assertEqual(price["amount_cents"],28450)

    def test_reproducible_import(self):
        result=subprocess.run([sys.executable,"scripts/normalize_expansion_tariffs.py","--check"],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == "__main__":
    unittest.main()
