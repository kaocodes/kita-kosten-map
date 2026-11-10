"""Acceptance checks for promoting only the eight fully supported catalogs."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from kita_costs.engine import compare_municipalities, load_cities, load_default_profile, load_highest_band_profile
from kita_costs.registry import load_registry

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("expansion_activation", ROOT / "scripts/activate_expansion_catalogs.py")
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)


class ExpansionActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection = activation.read(ROOT, activation.SELECTION)
        cls.selected = set(cls.selection["municipality_ids"])
        cls.review = activation.read(ROOT, cls.selection["review_path"])
        cls.references = activation.read(ROOT, "data/reviews/expansion_calculation_cases.json")["cases"]

    def test_active_catalogs_are_exact_reviewed_copies(self):
        self.assertEqual(activation.activate(check=True), 8)
        registry = load_registry()
        active = {entry["id"] for entry in registry["municipalities"] if entry["active"]}
        original = set(activation.read(ROOT, "data/reviews/model_family_review.json")["expected"])
        self.assertEqual(active, original | self.selected)
        self.assertEqual(len(active), 20)
        self.assertEqual({city["id"] for city in load_cities()}, active)

    def test_every_active_default_has_an_independent_source_reference(self):
        original = activation.read(ROOT, "data/reviews/model_family_review.json")["expected"]
        references = {case["municipality_id"]: case for case in self.references
            if case["municipality_id"] in self.selected and case["id"].endswith("-default")}
        self.assertEqual(set(references), self.selected)
        self.assertEqual(set(original) | set(references), {city["id"] for city in load_cities()})
        for profile in [load_default_profile(), load_highest_band_profile()]:
            for result in compare_municipalities(load_cities(), profile, load_registry()):
                if result["municipality_id"] not in self.selected:
                    continue
                case = references[result["municipality_id"]]
                for field, expected in case["expected"].items():
                    self.assertEqual(result[field], expected, (case["id"], field))
                self.assertIn(case["evidence"]["source_id"], {ref["source_id"] for ref in result["evidence"]})

    def test_partially_supported_municipality_cannot_be_promoted(self):
        selection = deepcopy(self.selection)
        selection["municipality_ids"].append("schwieberdingen")
        with self.assertRaisesRegex(ValueError, "not fully supported"):
            activation.check_review(ROOT, selection)

    def test_future_or_unapproved_calculation_date_is_rejected(self):
        selection = deepcopy(self.selection)
        selection["supported_as_of_to"] = "2026-11-03"
        with self.assertRaisesRegex(ValueError, "outside the approved interval"):
            activation.check_review(ROOT, selection)

    def test_stale_input_or_modified_active_copy_is_rejected(self):
        paths = set(self.review["input_sha256"]) | {activation.SELECTION, self.selection["review_path"],
            "data/municipality_registry.json", "data/profiles/highest_band.json"}
        paths.update(f"data/municipalities/{city_id}.json" for city_id in self.selected)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in paths:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, target)
            target = root / "data/municipalities/aidlingen.json"
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "Active catalog differs"):
                activation.activate(root, check=True)
            target = root / "data/models/configuration.json"
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "Reviewed input has changed"):
                activation.activate(root, check=True)


if __name__ == "__main__":
    unittest.main()
