"""Evaluate shared conformance cases with the independent Python reference engine."""

from copy import deepcopy
from decimal import Decimal
import argparse
import json
from pathlib import Path

from kita_costs.engine import (ROOT, compare_municipalities, create_personal_profile, evaluate_city,
                               formula_price, load_cities, normalize_profile, round_money)
from kita_costs.registry import load_registry


def load_cases():
    return json.loads((ROOT / "tests/fixtures/comparison_cases.json").read_text())["cases"]


def evaluate_case(case):
    profile = json.loads((ROOT / "data/profiles" / (case.get("profile", "highest_band") + ".json")).read_text())
    cities = load_cities()
    registry = load_registry()
    if case.get("personal"):
        profile = create_personal_profile(profile)
    profile.update(deepcopy(case.get("profile_updates", {})))
    for field in case.get("remove_fields", []):
        profile.pop(field, None)
    if "child_updates" in case:
        profile["children"][profile["target_child"]].update(case["child_updates"])
    city = next((city for city in cities if city["id"] == case.get("municipality_id")), None)
    for update in case.get("catalog_updates", []):
        matches = [record for record in city[update["collection"]]
                   if update["id"] == "*" or record["id"] == update["id"]]
        if not matches:
            raise RuntimeError(f"Unknown fixture target: {update['id']}")
        for record in matches:
            record.update(deepcopy(update["values"]))
    for duplicate in case.get("duplicates", []):
        records = city[duplicate["collection"]]
        record = deepcopy(next(record for record in records if record["id"] == duplicate["id"]))
        record["id"] = duplicate["new_id"]
        records.append(record)
    operation = case.get("operation", "compare")
    if operation == "round_money":
        value = Decimal(case["numerator"]) / Decimal(case["denominator"])
        return round_money(value, case.get("rounding", "cent_half_up"))
    if operation == "normalize":
        return normalize_profile(profile)
    if operation == "personalize":
        return create_personal_profile(profile)
    if operation == "formula_price":
        offer = next(offer for offer in city["offers"] if offer["age_group"] == "u3" and offer["formula"])
        return list(formula_price(city, offer, normalize_profile(profile), case["family_count"], case["offered_minutes"]))
    if operation == "city":
        return evaluate_city(city, profile)
    return compare_municipalities(cities, profile, registry, case.get("municipality_id"))


def evaluate_cases():
    results = []
    for case in load_cases():
        try:
            results.append({"id": case["id"], "result": evaluate_case(case)})
        except ValueError:
            if case.get("expected_error") != "invalid_profile":
                raise
            results.append({"id": case["id"], "error": "invalid_profile"})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = evaluate_cases()
    output = json.dumps(results, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
        print(f"Evaluated {len(results)} Python reference scenarios.")
    else:
        print(output, end="")
